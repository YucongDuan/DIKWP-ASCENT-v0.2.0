"""Verifier recomputes outcomes. No candidate self-score, rationale or CoT is trusted."""
from __future__ import annotations
import math
import random
import statistics
from .dsl import predict, schedule
from .canonical import Invalid

def optimum(case):
    """Exact integer knapsack oracle, independent of candidate priority policy."""
    dp = [0]*(case["capacity"]+1)
    for job in case["jobs"]:
        for b in range(case["capacity"], job["cost"]-1, -1):
            dp[b] = max(dp[b],dp[b-job["cost"]]+job["value"])
    return max(dp)

def losses(model, data):
    if model["program"]["kind"] == "basis":
        return [(predict(model,r)-r["y"])**2 for r in data]
    out = []
    for case in data:
        chosen = schedule(model["program"],case)
        if len(chosen) != len(set(chosen)) or any(type(i) is not int or i<0 or i>=len(case["jobs"]) for i in chosen):
            raise Invalid("Invalid schedule indices")
        used = sum(case["jobs"][i]["cost"] for i in chosen)
        if used>case["capacity"]:
            raise Invalid("Resource capacity violation")
        value = sum(case["jobs"][i]["value"] for i in chosen)
        out.append((optimum(case)-value)/max(1,optimum(case)))
    return out

def evaluation(model, worlds, meter=None):
    loss = {}
    for name, data in worlds.items():
        if meter:
            width = len(model["program"].get("features",[]))+1
            units = len(data)*width*width if model["program"]["kind"]=="basis" else len(data)*2000
            meter.charge(units)
        ls = losses(model,data)
        loss[name] = statistics.fmean(ls)
    complexity = len(model["program"].get("features",[])) if model["program"]["kind"]=="basis" else model["program"]["swap_passes"]+1
    return {"world_losses":loss,"worst_loss":max(loss.values()),"mean_loss":statistics.fmean(loss.values()),"complexity":complexity,
            "selection_score":max(loss.values())+1e-5*complexity}

def paired_interval(baseline_losses, candidate_losses, seed=7301, samples=600, meter=None):
    """Descriptive paired bootstrap; not a certificate of generalization or alignment."""
    ds = [b-c for b,c in zip(baseline_losses,candidate_losses)]
    if not ds or len(baseline_losses)!=len(candidate_losses):
        raise Invalid("Paired observations required")
    if meter:meter.charge(samples*len(ds))
    rng = random.Random(seed)
    means = sorted(sum(ds[rng.randrange(len(ds))] for _ in ds)/len(ds) for _ in range(samples))
    return {"mean_improvement":statistics.fmean(ds),"low":means[int(samples*.025)],"high":means[min(samples-1,int(samples*.975))],
            "method":"paired_percentile_bootstrap_descriptive_95pct","resamples":samples}

def audit_pair(baseline, candidate, worlds, seed=7301, meter=None):
    per = {}
    all_b, all_c = [], []
    for j,(name,data) in enumerate(worlds.items()):
        if meter:meter.charge(len(data)*(2000 if candidate["program"]["kind"]=="scheduler" else 50)*2)
        b,c = losses(baseline,data),losses(candidate,data)
        per[name] = {"baseline":statistics.fmean(b),"candidate":statistics.fmean(c),"interval":paired_interval(b,c,seed+j,meter=meter)}
        all_b.extend(b);all_c.extend(c)
    paired = paired_interval(all_b,all_c,seed+10,meter=meter)
    worst_b=max(x["baseline"] for x in per.values());worst_c=max(x["candidate"] for x in per.values())
    tolerance=0.002 if candidate["program"]["kind"]=="basis" else 0.01
    nonregression=all(x["candidate"]<=x["baseline"]+tolerance for x in per.values())
    improvement=paired["low"]>0.00001 and worst_c < worst_b-0.00001
    return {"worlds":per,"paired":paired,"worst_baseline":worst_b,"worst_candidate":worst_c,
            "nonregression":nonregression,"improvement":improvement,"eligible":nonregression and improvement,
            "nonregression_tolerance":tolerance,"audit_scope":"One frozen candidate; public synthetic generator or operator-provided data; not independent certification"}
