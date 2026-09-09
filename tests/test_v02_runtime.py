import copy
import csv
import json
from pathlib import Path

import pytest

from dikwp_ascent.canonical import Invalid, Stopped, BudgetExceeded, digest
from dikwp_ascent.dsl import fit, validate_model
from dikwp_ascent.engine import research, verify_record
from dikwp_ascent.intake import csv_dataset, proposer_packet, validate_proposals
from dikwp_ascent.policy import Limits
from dikwp_ascent.problems import make_split
from dikwp_ascent.registry import Registry
from dikwp_ascent.reporting import export_policy, run_markdown
from dikwp_ascent.runtime import run_controlled, campaign, infer, canary, walkthrough


@pytest.fixture
def active(tmp_path):
    path = tmp_path / 'workspace'
    r = Registry(path, create=True); r.close()
    run = run_controlled(path, 'periodic', 17)
    r = Registry(path)
    r.promote(r.approve(run['record']['run_id'], 'TEST_OPERATOR'))
    r.close()
    return path


def test_strong_reference_gate_rejects_old_weak_winner(tmp_path):
    r = Registry(tmp_path, create=True)
    result = research('quadratic', 17, audit_register=r.claim_audit)['record']
    assert result['audit']['eligible']
    assert not result['adoption']['eligible']
    assert result['status'] == 'NOT_PROMOTABLE'
    r.store_run(result)
    with pytest.raises(Invalid): r.approve(result['run_id'], 'reviewer')
    r.close()


def test_periodic_passes_predeclared_reference_gate():
    r = research('periodic', 17)['record']
    assert r['status'] == 'REVIEWABLE'
    assert all(v <= 1e-9 for v in r['adoption']['candidate_minus_reference_by_world'].values())


def test_frozen_incumbent_preserved_not_refitted(active):
    r = Registry(active); old = r.current('periodic'); r.close()
    result = run_controlled(active, 'periodic', 23)['record']
    assert result['search']['baseline'] == old['model']
    assert result['search']['incumbent_evaluation_mode'] == 'FROZEN_DEPLOYED_PARAMETERS'
    assert result['parent_version'] == old['version']
    newly_fitted = fit(old['model']['program'], make_split('periodic', 23, 'train')['in_distribution'])
    assert newly_fitted['coefficients'] != result['search']['baseline']['coefficients']


def test_no_dual_incumbent_configuration():
    model = fit({'kind':'basis','features':['x'],'ridge':.001}, make_split('periodic',17,'train')['in_distribution'])
    with pytest.raises(Invalid): research('periodic',17,incumbent=model['program'],incumbent_model=model)


def test_wrong_incumbent_family():
    with pytest.raises(Invalid): research('periodic',17,incumbent_model={'program':{'kind':'scheduler','cost_power':1,'swap_passes':1}})


def test_adoption_flags_cannot_override_comparator():
    r=research('quadratic',17)['record']
    r['adoption']['eligible']=True;r['status']='REVIEWABLE'
    r.pop('record_digest');r['record_digest']=digest(r)
    with pytest.raises(Invalid,match='Inconsistent'):verify_record(r)


@pytest.mark.parametrize('model',[
    {},
    {'program':{'kind':'basis','features':['x'],'ridge':.001},'coefficients':[1]},
    {'program':{'kind':'basis','features':['x'],'ridge':.001},'coefficients':[float('nan'),1]},
    {'program':{'kind':'scheduler','cost_power':1,'swap_passes':1},'authority':True},
])
def test_invalid_frozen_model(model):
    with pytest.raises(Invalid):validate_model(model)


def test_inference_is_real_and_version_bound(active):
    result=infer(active,'periodic',{'rows':[{'x':0},{'x':1}]})
    assert result['outputs'] == pytest.approx([.3973020311961158,2.7893305164978877])
    assert result['version'].startswith('v-')
    assert result['external_actions']==0
    r=Registry(active);assert r.verify()['valid'];r.close()


def test_stop_blocks_inference(active):
    r=Registry(active);r.stop('test');r.close()
    with pytest.raises(Stopped):infer(active,'periodic',{'rows':[{'x':0}]})


def test_inference_without_approved_policy(tmp_path):
    r=Registry(tmp_path,create=True);r.close()
    with pytest.raises(Invalid,match='No active policy'):infer(tmp_path,'periodic',{'rows':[{'x':0}]})


@pytest.mark.parametrize('payload',[
    {'rows':[]}, {'rows':[{'x':float('inf')}]},
    {'rows':[{'x':0,'y':1}]}, {'rows':[{'x':11}]},
    {'rows':[{'x':1}],'tool':'shell'},
])
def test_inference_rejects_invalid_data(active,payload):
    with pytest.raises(Invalid):infer(active,'periodic',payload)


def test_canary_detects_shift_does_not_mutate(active):
    before=export_policy(active,'periodic')
    w=make_split('periodic',73,'development')
    for rs in w.values():
        for row in rs:row['y']+=5
    result=canary(active,'periodic',w,.1)
    assert result['review_recommended']
    assert not result['automatic_rollback']
    assert export_policy(active,'periodic') == before


def test_policy_export_does_not_export_authority(active):
    p=export_policy(active,'periodic')
    assert not p['authority_transferred']
    assert 'controller.key' not in json.dumps(p)


def test_campaign_all_declared_trials_retained(tmp_path):
    path=tmp_path/'w';r=Registry(path,create=True);r.close()
    c=campaign(path,tmp_path/'out',['quadratic','periodic'],[17])
    assert c['summary']=={'declared':2,'completed':2,'reviewable':1,'not_promotable':1,'failed':0,'not_run':0}
    assert c['automatic_adoptions']==0
    r=Registry(path);assert r.snapshot()['active']==[];r.close()


def test_campaign_failed_reuse_retained(tmp_path):
    p=tmp_path/'w';r=Registry(p,create=True);r.close()
    run_controlled(p,'periodic',17)
    c=campaign(p,tmp_path/'out',['periodic'],[17])
    assert c['summary']['failed']==1
    assert 'Holdout already consumed' in c['trials'][0]['reason']


def test_campaign_bound_and_overwrite(tmp_path):
    with pytest.raises(Invalid):campaign(tmp_path,tmp_path/'out',['periodic'],list(range(33)))
    out=tmp_path/'out';out.mkdir();(out/'private').write_text('keep')
    with pytest.raises(Invalid):campaign(tmp_path,out,['periodic'],[17])
    assert (out/'private').read_text()=='keep'


def test_proposer_packet_has_no_audit_rows():
    p=proposer_packet('periodic',17)
    assert 'train' in p and 'development' in p
    assert 'audit' not in p and 'seed' not in p
    assert not p['network_authorized'] and not p['tools_authorized']


def test_proposer_self_score_and_source_are_not_accepted():
    for p in [{'kind':'basis','features':['x'],'ridge':.001,'score':1}, {'python':'print(1)'}]:
        with pytest.raises(Invalid):validate_proposals([p])


def test_csv_explicit_splits_roundtrip(tmp_path):
    from dikwp_ascent.problems import validate_custom
    data={'train':make_split('periodic',19,'train')['in_distribution'], 'development':make_split('periodic',19,'development'),'audit':make_split('periodic',19,'audit')}
    p=tmp_path/'d.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['split','world','x','y','proxy']);w.writeheader()
        for split in ['train','development','audit']:
            groups={'in_distribution':data['train']} if split=='train' else data[split]
            for world,rows in groups.items():
                for row in rows:w.writerow({'split':split,'world':world,**row})
    assert csv_dataset(p)==data


def test_csv_wrong_header(tmp_path):
    p=tmp_path/'x.csv';p.write_text('x,y\n1,2\n')
    with pytest.raises(Invalid):csv_dataset(p)


def test_report_contains_adverse_comparison():
    text=run_markdown(research('quadratic',17))
    assert 'NOT_PROMOTABLE' in text and 'STRONG_REFERENCE_NONREGRESSION_FAILED' in text
    assert 'not demonstrated' in text.lower() or 'asi established: **false**' in text.lower()


def test_full_walkthrough(tmp_path):
    s=walkthrough(tmp_path/'walk')
    assert len(s['runs'])==4
    assert s['ticket_replay_rejected'] and s['stop_enforced_for_inference']
    assert s['canary_review_recommended'] and s['final_active']==[]
    assert s['audit']['valid'] and s['external_actions']==0


def test_frozen_order_not_silently_permuted():
    with pytest.raises(Invalid,match='ordering'):
        validate_model({'program':{'kind':'basis','features':['x','sin'],'ridge':.001},'coefficients':[1,2,3]})


def test_campaign_deadline_reaches_search(tmp_path):
    import time
    p=tmp_path/'w';r=Registry(p,create=True);r.close()
    with pytest.raises(BudgetExceeded,match='deadline'):
        run_controlled(p,'periodic',17,deadline=time.monotonic()-1)
