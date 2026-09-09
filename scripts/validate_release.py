"""Reproduce real experiments and a separately written finite controller abstraction."""
from __future__ import annotations
import ast
import json
import tempfile
from collections import deque
from pathlib import Path
from dikwp_ascent.canonical import save_json
from dikwp_ascent.runtime import walkthrough,campaign
from dikwp_ascent.registry import Registry
from dikwp_ascent.dsl import fit
from dikwp_ascent.problems import make_split
from dikwp_ascent.evaluator import audit_pair

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation'


def bounded_check():
    # stop, incumbent pass, reference pass, holdout used, ticket, epoch,
    # ticket epoch, ticket consumed, active. One run, epochs 0..2.
    initial=(False,False,False,False,False,0,-1,False,False)
    todo=deque([initial]);seen={initial};edges=0;violations=[]
    while todo:
        s=todo.popleft();stop,b,r,used,ticket,epoch,te,spent,active=s
        nxt=[]
        if not stop and not used:
            for bp,rp in ((False,False),(False,True),(True,False),(True,True)):
                nxt.append(('audit',(stop,bp,rp,True,ticket,epoch,te,spent,active)))
        if not stop and used and b and r and not ticket:
            nxt.append(('approve',(stop,b,r,used,True,epoch,epoch,False,active)))
        if not stop and ticket and not spent and b and r and epoch==te:
            nxt.append(('activate',(stop,b,r,used,ticket,epoch,te,True,True)))
        if epoch<2:nxt.append(('stop',(True,b,r,used,ticket,epoch+1,te,spent,active)))
        if stop:nxt.append(('resume',(False,b,r,used,ticket,epoch,te,spent,active)))
        if active and epoch<2:nxt.append(('rollback',(stop,b,r,used,ticket,epoch+1,te,spent,False)))
        for action,n in nxt:
            if n==s:continue
            edges+=1
            if action=='activate' and (stop or not b or not r or not ticket or spent or te!=epoch):violations.append([s,action,n])
            if action=='audit' and used:violations.append([s,action,n])
            if n not in seen:seen.add(n);todo.append(n)
    negatives={
        'ignore_stop':(True,True,True,True,True,0,0,False,False),
        'ignore_reference':(False,True,False,True,True,0,0,False,False),
        'reuse_ticket':(False,True,True,True,True,0,0,True,False),
        'ignore_revocation':(False,True,True,True,True,1,0,False,False),
    }
    def legal(s):
        stop,b,r,used,ticket,epoch,te,spent,active=s
        return not stop and b and r and used and ticket and not spent and epoch==te
    return {'states':len(seen),'transitions':edges,'violations':violations,
            'negative_controls_rejected':{k:not legal(v) for k,v in negatives.items()},
            'scope':'Independent one-run/ticket finite abstraction, two epoch increments; not TLC, not a proof of code or universal AI safety'}


def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        temp=Path(tmp)
        summary=walkthrough(temp/'walk')
        for p in (temp/'walk').glob('*.json'):
            save_json(OUT/p.name,json.loads(p.read_text()))
        # Registry and private key remain in the temporary directory and are never copied.
        r=Registry(temp/'campaign-workspace',create=True);r.close()
        repeat=campaign(temp/'campaign-workspace',temp/'campaign',['quadratic','periodic','sensor_shift','scheduling'],[17,23,31])
        save_json(OUT/'campaign.json',repeat)
    train=make_split('sensor_shift',17,'train')['in_distribution']
    simple=fit({'kind':'basis','features':['x'],'ridge':.001},train)
    shortcut=fit({'kind':'basis','features':['proxy'],'ridge':.001},train)
    rejected=audit_pair(simple,shortcut,make_split('sensor_shift',17,'audit'))
    save_json(OUT/'rejected_shortcut.json',{'synthetic':True,'candidate':shortcut,'audit':rejected})
    findings=[]
    for p in (ROOT/'src/dikwp_ascent').glob('*.py'):
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {'eval','exec','compile'}:
                findings.append({'file':p.name,'line':node.lineno,'call':node.func.id})
            if isinstance(node,ast.Import):
                for n in node.names:
                    if n.name.split('.')[0] in {'subprocess','pickle','requests'}:
                        findings.append({'file':p.name,'line':node.lineno,'import':n.name})
    bounded=bounded_check();save_json(OUT/'bounded_check.json',bounded)
    summary['campaign_summary']=repeat['summary']
    summary['shortcut_rejected']=not rejected['eligible']
    summary['bounded_model']=bounded
    summary['static_scan']={'findings':findings,'scope':'Narrow AST check; loopback HTTP server intentionally allowed, no arbitrary candidate-code execution'}
    save_json(OUT/'summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
