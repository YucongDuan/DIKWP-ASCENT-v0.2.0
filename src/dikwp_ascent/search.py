"""Budgeted evolution of allowlisted policies, not recursive foundation-model training."""
from __future__ import annotations
import itertools
import random
from .canonical import digest, BudgetExceeded, Invalid
from .dsl import FEATURES, RIDGES, validate_program, fit, validate_model
from .evaluator import evaluation

def baseline_program(task):
    return {"kind":"scheduler","cost_power":0.0,"swap_passes":0} if task=="scheduling" else {"kind":"basis","features":["x"],"ridge":0.001}

def strong_program(task):
    return {"kind":"scheduler","cost_power":1.0,"swap_passes":2} if task=="scheduling" else {"kind":"basis","features":["x","x2","x3","sin","cos"],"ridge":0.001}

def neighbors(p):
    if p["kind"]=="scheduler":
        for power in (0,0.5,0.75,1,1.25,1.5,2):
            for swaps in range(4):
                yield {"kind":"scheduler","cost_power":power,"swap_passes":swaps}
    else:
        for f in FEATURES:
            fs=set(p["features"])
            if f in fs:fs.remove(f)
            else:fs.add(f)
            yield {"kind":"basis","features":sorted(fs),"ridge":p["ridge"]}
        for r in RIDGES:
            yield {**p,"ridge":r}

def evolve(task,train,development,meter,seed=17,proposals=None,incumbent=None,incumbent_model=None):
    """The search interface receives no audit rows, labels, audit score or promotion key."""
    rng=random.Random(seed)
    if incumbent is not None and incumbent_model is not None:
        raise Invalid("Choose a program baseline or a frozen deployed model, not both")
    baseline = validate_model(incumbent_model) if incumbent_model is not None else fit(incumbent or baseline_program(task),train)
    expected = "scheduler" if task == "scheduling" else "basis"
    if baseline["program"]["kind"] != expected:
        raise Invalid("Frozen incumbent belongs to another task family")
    records=[];seen=set();best=None
    queue=[(baseline["program"],None,"incumbent"),(strong_program(task),None,"fixed_generalist")]
    for p in proposals or []:
        p=validate_program(p)
        if p["kind"]!=baseline["program"]["kind"]:raise Invalid("Candidate family mismatch")
        queue.append((p,None,"external_data_proposal"))
    status="SEARCH_COMPLETE"
    for generation in range(meter.limits.generations):
        try:
            for p,parent,origin in queue:
                p=validate_program(p);pid=digest(p)
                if pid in seen:continue
                meter.proposal()
                meter.charge(len(train)*(len(p.get("features",[]))+1)**2)
                model=fit(p,train)
                ev=evaluation(model,development,meter)
                item={"id":pid,"program":p,"model":model,"generation":generation,"parent":parent,"operator":origin,**ev}
                records.append(item);seen.add(pid)
                if best is None or (ev["selection_score"],ev["complexity"],pid)<(best["selection_score"],best["complexity"],best["id"]):best=item
            ranked=sorted(records,key=lambda x:(x["selection_score"],x["complexity"],x["id"]))[:4]
            queue=[]
            for r in ranked:
                queue.extend((p,r["id"],"one_edit_mutation") for p in neighbors(r["program"]) if digest(validate_program(p)) not in seen)
            rng.shuffle(queue)
            if not queue:break
        except BudgetExceeded as e:
            status="SEARCH_BUDGET_STOP"
            break
    if best is None:raise BudgetExceeded("No completed candidate evaluation")
    return {"baseline":baseline,"champion":best,"history":records,"search_status":status,
            "proposal_count":meter.proposals,"evaluated_count":len(records),"work_units":meter.work_units,
            "strong_comparator":fit(strong_program(task),train),"holdout_seen_by_search":False,
            "incumbent_evaluation_mode":"FROZEN_DEPLOYED_PARAMETERS" if incumbent_model is not None else "FITTED_REFERENCE_PROGRAM"}
