"""Real experiments over safe numerical DSLs and a single frozen audit candidate."""
from __future__ import annotations
import hashlib
import platform
import statistics
import time
from dataclasses import asdict
from pathlib import Path
from .canonical import digest, Invalid, integer
from .policy import CONTROL, CONTROL_DIGEST, Meter, Limits
from .problems import make_split, validate_custom, TASKS
from .search import evolve
from .evaluator import audit_pair, evaluation


def source_fingerprint():
    import importlib.resources as resources
    root = resources.files("dikwp_ascent")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(root.iterdir(), key=lambda x:x.name) if p.name.endswith(".py")}
    assets = root.joinpath("resources")
    if assets.is_dir():
        for p in sorted(assets.iterdir(), key=lambda x:x.name):
            if p.is_file(): hashes["resources/" + p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return digest(hashes)


def knowledge_packet(task, result, scope):
    """Typed argument graph, not fabricated hidden thoughts or a truth certificate."""
    data_id=digest(scope)
    return {
        "D":{"id":data_id,"type":"DatasetScope","scope":scope},
        "I":{"type":"ObservedResiduals","development_trials":result["evaluated_count"],"source":data_id},
        "K":{"type":"EmpiricalCandidate","program":result["champion"]["program"],"scope":"Only the declared task distribution; no universal law claim"},
        "W":{"type":"NonCompensableControls","policy_digest":CONTROL_DIGEST,"principle":"Objective improvement cannot grant permission or overwrite failed evidence"},
        "P":{"type":"ResearchPurpose","task":task,"outcome":"Find a lower-loss bounded policy without self-modifying the verifier"},
        "routes":[{"from":"D","to":"I","loss":"Finite noisy observations"},{"from":"I","to":"K","loss":"Model-class and distribution limits"},{"from":"W","to":"P","loss":"Normative rules are not physical laws"},{"from":"P","to":"D","loss":"Next experiment requires fresh observations"}],
    }


def research(task="quadratic",seed=17,limits=None,custom=None,proposals=None,incumbent=None,parent_version=None,stop_check=None,audit_register=None,incumbent_model=None):
    if task not in TASKS and task!="custom_regression":raise Invalid("Unknown experiment")
    integer(seed,0,2**31-1,"seed")
    if proposals is not None and (not isinstance(proposals,list) or len(proposals)>32):raise Invalid("At most 32 data-only external proposals")
    limits=limits or Limits()
    meter=Meter(limits,stop_check)
    meter.check()
    started=time.monotonic()
    fingerprint=source_fingerprint()
    if custom is not None:
        custom=validate_custom(custom)
        if task!="custom_regression":raise Invalid("Custom data requires custom_regression task")
        train=custom["train"];dev=custom["development"]
    else:
        if task=="custom_regression":raise Invalid("Custom data missing")
        train=make_split(task,seed,"train")["in_distribution"]
        dev=make_split(task,seed,"development")
    result=evolve(task,train,dev,meter,seed,proposals,incumbent,incumbent_model)
    # Frozen model is hashed BEFORE audit data are acquired or evaluated.
    frozen=digest(result["champion"]["model"])
    meter.check()
    audit=custom["audit"] if custom is not None else make_split(task,seed,"audit")
    audit_key=digest({w:sorted(digest({k:float(v) for k,v in row.items()}) if task!="scheduling" else digest(row) for row in rs) for w,rs in audit.items()})
    audit_claim=audit_register(audit_key) if audit_register else None
    assurance=Meter(Limits(proposals=4,work_units=limits.audit_work_units,seconds=limits.seconds),stop_check)
    report=audit_pair(result["baseline"],result["champion"]["model"],audit,seed+91000,meter=assurance)
    meter.check()
    if digest(result["champion"]["model"])!=frozen or source_fingerprint()!=fingerprint:
        raise Invalid("Model or evaluator changed during audit")
    strong=evaluation(result["strong_comparator"],audit,meter=assurance)
    numerical_tolerance = 1e-9
    comparator_gaps = {name: row["candidate"] - strong["world_losses"][name] for name, row in report["worlds"].items()}
    strong_pass = all(gap <= numerical_tolerance for gap in comparator_gaps.values())
    reasons = []
    if not report["eligible"]: reasons.append("INCUMBENT_AUDIT_NOT_PASSED")
    if not strong_pass: reasons.append("STRONG_REFERENCE_NONREGRESSION_FAILED")
    adoption = {"eligible": report["eligible"] and strong_pass,
                "strong_reference_nonregression": strong_pass,
                "absolute_tolerance": numerical_tolerance,
                "candidate_minus_reference_by_world": comparator_gaps,
                "blocking_reasons": reasons,
                "scope": "Predeclared gate; not significance against reference and not state-of-the-art certification"}
    # A second analyst interprets the same frozen observations; not a second independent dataset.
    worlds=[
        {"id":"transferable_improvement","prediction":"The frozen candidate lowers loss on each declared audit world","supported":report["eligible"],"falsifier":"Independent shifted data reverse the improvement or reveal a constraint failure"},
        {"id":"selection_or_benchmark_artifact","prediction":"Gain disappears beyond the built-in model family or disclosed generator","status":"UNRESOLVED","next_test":"Independent data owner, new distributions, stronger baselines and equal-budget replication"},
        {"id":"control_plane_failure","prediction":"Apparent gain requires changing evaluator, authority, audit or limits","status":"CHECKED_ONLY_WITHIN_DATA_DSL_BOUNDARY","next_test":"Independent deployment and sandbox assessment before any native-code or network extension"},
    ]
    scope={"task":task,"seed":seed,"train_rows":len(train),"development_rows":{w:len(rs) for w,rs in dev.items()},"audit_rows":{w:len(rs) for w,rs in audit.items()},
           "train_digest":digest(train),"development_digest":digest(dev),"audit_digest":digest(audit),"synthetic":custom is None}
    body={
        "schema":"ascent.run/2","task":task,"seed":seed,"parent_version":parent_version,"limits":asdict(limits),
        "source_fingerprint":fingerprint,"control_digest":CONTROL_DIGEST,"status":"REVIEWABLE" if adoption["eligible"] else "NOT_PROMOTABLE",
        "candidate_digest":frozen,"search":result,"audit":report,"adoption":adoption,"fixed_generalist_audit":strong,
        "assurance_work_units":assurance.work_units,"audit_key":audit_key,"audit_claim":audit_claim,"scope":scope,"interpretations":worlds,"dikwp":knowledge_packet(task,result,scope),
        "authority":CONTROL,"actual_model_api_calls":0,"foundation_weights_updated":False,"asi_established":False,
        "limitations":["Finite synthetic or operator-provided domains, not ASI evidence","Search operators are algorithms, not independent conscious agents","No external model API was invoked","Audit withheld by interface, not protected against a hostile host","Paired bootstrap interval is descriptive; repeated holdout reuse causes contamination","No physical energy measurement","No autonomous production deployment"],
    }
    body["run_id"]="run-"+digest(body)[:24]
    body["record_digest"]=digest(body)
    return {"record":body,"telemetry":{"wall_seconds":time.monotonic()-started,"python":platform.python_version(),"work_units":meter.work_units,"work_unit_kind":"deterministic_accounting_units_not_joules"}}


def verify_record(record):
    r=dict(record);expected=r.pop("record_digest",None)
    if not expected or digest(r)!=expected:raise Invalid("Run record digest mismatch")
    if record["candidate_digest"]!=digest(record["search"]["champion"]["model"]):raise Invalid("Candidate digest mismatch")
    if record["control_digest"]!=CONTROL_DIGEST:raise Invalid("Control policy mismatch")
    if record.get("schema") != "ascent.run/2":raise Invalid("Unsupported run schema; old records require a fresh workspace")
    tol=1e-9
    comparison={w:v["candidate"]-record["fixed_generalist_audit"]["world_losses"][w] for w,v in record["audit"]["worlds"].items()}
    expected=bool(record["audit"]["eligible"]) and all(x<=tol for x in comparison.values())
    if record["adoption"]["eligible"] != expected or record["adoption"]["candidate_minus_reference_by_world"]!=comparison:raise Invalid("Inconsistent adoption evidence")
    if record["status"]!=("REVIEWABLE" if expected else "NOT_PROMOTABLE"):raise Invalid("Inconsistent adoption status")
    return True
