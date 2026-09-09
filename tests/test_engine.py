import copy
import inspect
import pytest
from dikwp_ascent.engine import research,verify_record,source_fingerprint
from dikwp_ascent.policy import Limits,Meter,CONTROL_DIGEST
from dikwp_ascent.search import evolve
from dikwp_ascent.canonical import Invalid,Stopped,BudgetExceeded
from dikwp_ascent.problems import TASKS

@pytest.mark.parametrize("task",TASKS)
def test_research_is_measured(task):
    r=research(task,17)["record"]
    assert verify_record(r)
    assert r["search"]["evaluated_count"]>=2
    assert r["audit"]["eligible"]
    assert r["audit"]["worst_candidate"]<r["audit"]["worst_baseline"]
    assert not r["search"]["holdout_seen_by_search"]
    assert not r["foundation_weights_updated"]
    assert not r["asi_established"]
    assert r["fixed_generalist_audit"]
    assert r["control_digest"]==CONTROL_DIGEST

def test_search_has_no_audit_parameter():
    assert "audit" not in inspect.signature(evolve).parameters

def test_deterministic_record():
    assert research("quadratic",5)["record"]==research("quadratic",5)["record"]

def test_record_mutation_detected():
    r=research("quadratic",5)["record"];r["audit"]["eligible"]=False
    with pytest.raises(Invalid):verify_record(r)

def test_stop_before_work():
    with pytest.raises(Stopped):research("quadratic",3,stop_check=lambda:True)

def test_small_budget_never_runs_forever():
    try:
        r=research("quadratic",3,Limits(proposals=4,work_units=10000))["record"]
        assert r["search"]["proposal_count"]<=4
        assert r["search"]["work_units"]<=10000
    except BudgetExceeded:
        pass

def test_negative_budget_rejected():
    with pytest.raises(Invalid):Limits(proposals=-1)

def test_meter_limits():
    m=Meter(Limits(proposals=4,work_units=10000));m.charge(10000)
    with pytest.raises(BudgetExceeded):m.charge(1)
    assert m.work_units==10000

def test_self_score_not_accepted():
    with pytest.raises(Invalid):research("quadratic",17,proposals=[{"kind":"basis","features":["x"],"ridge":.001,"score":0}])

def test_custom_missing_rejected():
    with pytest.raises(Invalid):research("custom_regression",17)

def test_fingerprint_length():assert len(source_fingerprint())==64

def test_assurance_budget_separate_and_fail_closed():
    with pytest.raises(BudgetExceeded):research("quadratic",17,Limits(audit_work_units=10000))

def test_custom_external_programs_bounded():
    with pytest.raises(Invalid):research("quadratic",17,proposals=[{}]*33)

def test_bad_seed_rejected():
    with pytest.raises(Invalid):research("quadratic",True)
