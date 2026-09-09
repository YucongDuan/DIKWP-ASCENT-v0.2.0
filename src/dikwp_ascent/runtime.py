"""Operational research, finite campaigns, and inference with frozen active models.

No provider calls, code execution, autonomous activation, or external effects.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .canonical import Invalid, Stopped, BudgetExceeded, digest, exact_keys, finite, integer, save_json
from .dsl import predict, schedule, validate_model
from .engine import research, source_fingerprint
from .evaluator import evaluation
from .policy import Limits
from .problems import TASKS
from .registry import Registry


def run_controlled(workspace: str | Path, task: str = "periodic", seed: int = 17,
                   limits: Limits | None = None, custom=None, proposals=None, deadline: float | None = None) -> dict:
    """A local controlled experiment, preserving the deployed incumbent's parameters."""
    reg = Registry(workspace)
    try:
        reg.verify()
        if reg.stopped():
            raise Stopped("Operator stop is active")
        epoch = reg.meta("epoch")
        old = reg.current(task)
        def stop_check():
            if deadline is not None and time.monotonic() >= deadline:
                raise BudgetExceeded("Campaign deadline exceeded")
            return reg.stopped() or reg.meta("epoch") != epoch
        result = research(task, seed, limits or Limits(), custom=custom, proposals=proposals,
                          incumbent_model=old["model"] if old else None,
                          parent_version=old["version"] if old else None,
                          stop_check=stop_check, audit_register=reg.claim_audit)
        reg.store_run(result["record"])
        return result
    finally:
        reg.close()


def campaign(workspace: str | Path, output: str | Path, tasks: list[str], seeds: list[int],
             limits: Limits | None = None, max_seconds: int = 300) -> dict:
    """Run a predeclared finite grid. Every trial including failures appears in the report."""
    if not isinstance(tasks, list) or not tasks or len(set(tasks)) != len(tasks) or any(t not in TASKS for t in tasks):
        raise Invalid("Choose distinct built-in task names")
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds):
        raise Invalid("Choose distinct seeds")
    for seed in seeds:
        integer(seed, 0, 2**31-1, "seed")
    if len(tasks) * len(seeds) > 32:
        raise Invalid("Campaign limited to 32 trials")
    integer(max_seconds, 1, 600, "campaign seconds")
    root = Path(output)
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise Invalid("Campaign output must be a new or empty directory")
    root.mkdir(parents=True, exist_ok=True)
    spec = {"tasks": tasks, "seeds": seeds, "source_fingerprint": source_fingerprint(),
            "max_seconds": max_seconds, "limits": vars(limits or Limits()),
            "synthetic": True, "automatic_adoption": False}
    save_json(root / "campaign-spec.json", spec)
    reg = Registry(workspace)
    try:
        reg.observe("campaign_started", {"spec_digest": digest(spec), "trials": len(tasks)*len(seeds)})
    finally:
        reg.close()
    started = time.monotonic()
    trials = []
    halted = False
    for task in tasks:
        for seed in seeds:
            if halted or time.monotonic() - started >= max_seconds:
                trials.append({"task": task, "seed": seed, "status": "NOT_RUN", "reason": "Campaign stopped or wall budget exhausted"})
                continue
            try:
                remaining = max(1, int(max_seconds - (time.monotonic() - started)))
                lim = limits or Limits()
                bounded = Limits(**{**vars(lim), "seconds": min(lim.seconds, remaining)})
                result = run_controlled(workspace, task, seed, bounded, deadline=started+max_seconds)
                save_json(root / f"{task}-{seed}.json", result)
                r = result["record"]
                trials.append({"task": task, "seed": seed, "run_id": r["run_id"], "status": r["status"],
                               "incumbent_pass": r["audit"]["eligible"], "strong_reference_pass": r["adoption"]["strong_reference_nonregression"],
                               "incumbent_worst": r["audit"]["worst_baseline"], "candidate_worst": r["audit"]["worst_candidate"],
                               "strong_reference_worst": r["fixed_generalist_audit"]["worst_loss"],
                               "blocking_reasons": r["adoption"]["blocking_reasons"]})
            except (Invalid, BudgetExceeded, Stopped) as exc:
                row = {"task": task, "seed": seed, "status": "FAILED", "error_type": type(exc).__name__, "reason": str(exc)}
                trials.append(row)
                halted = isinstance(exc, Stopped)
                if not halted:
                    reg = Registry(workspace)
                    try:
                        reg.observe("campaign_trial_failed", row)
                    finally:
                        reg.close()
            save_json(root / "campaign-progress.json", {"spec": spec, "trials": trials})
    result = {"schema": "ascent.campaign/1", "spec": spec, "trials": trials,
              "summary": {"declared": len(tasks)*len(seeds), "completed": sum("run_id" in x for x in trials),
                          "reviewable": sum(x["status"] == "REVIEWABLE" for x in trials),
                          "not_promotable": sum(x["status"] == "NOT_PROMOTABLE" for x in trials),
                          "failed": sum(x["status"] == "FAILED" for x in trials),
                          "not_run": sum(x["status"] == "NOT_RUN" for x in trials)},
              "automatic_adoptions": 0, "asi_established": False,
              "interpretation": "Public synthetic repeated trials, not independent real-world validation; all declared trials retained"}
    result["digest"] = digest(result)
    save_json(root / "campaign.json", result)
    reg = Registry(workspace)
    try:
        if not reg.stopped():
            reg.observe("campaign_finished", {"digest": result["digest"], "summary": result["summary"]})
    finally:
        reg.close()
    return result


def validate_schedule_cases(cases: Any) -> list[dict]:
    if not isinstance(cases, list) or not 1 <= len(cases) <= 128:
        raise Invalid("Provide 1 to 128 scheduling cases")
    for case in cases:
        exact_keys(case, {"jobs", "capacity"})
        integer(case["capacity"], 1, 10000, "capacity")
        if not isinstance(case["jobs"], list) or not 1 <= len(case["jobs"]) <= 128:
            raise Invalid("Provide 1 to 128 jobs per case")
        for job in case["jobs"]:
            exact_keys(job, {"cost", "value"})
            integer(job["cost"], 1, 10000, "cost")
            integer(job["value"], 0, 1000000, "value")
    return cases


def infer(workspace: str | Path, task: str, payload: dict) -> dict:
    """Execute only an active frozen DSL policy. Stop applies to inference as well."""
    reg = Registry(workspace)
    try:
        if reg.stopped():
            raise Stopped("Operator stop is active")
        old = reg.current(task)
        if old is None:
            raise Invalid("No active policy: inspect, approve and promote a reviewable run first")
        epoch = reg.meta("epoch")
        model = validate_model(old["model"])
        if model["program"]["kind"] == "basis":
            exact_keys(payload, {"rows"})
            if not isinstance(payload["rows"], list) or not 1 <= len(payload["rows"]) <= 4096:
                raise Invalid("Inference requires 1 to 4096 rows")
            for row in payload["rows"]:
                exact_keys(row, {"x"}, {"proxy"})
                finite(row["x"], -10, 10, "x")
                finite(row.get("proxy", 0), -1000, 1000, "proxy")
            values = [predict(model, row) for row in payload["rows"]]
        else:
            exact_keys(payload, {"cases"})
            cases = validate_schedule_cases(payload["cases"])
            values = []
            for case in cases:
                selected = schedule(model["program"], case)
                values.append({"selected": selected, "cost": sum(case["jobs"][i]["cost"] for i in selected),
                               "value": sum(case["jobs"][i]["value"] for i in selected)})
        result = {"schema": "ascent.inference/1", "task": task, "version": old["version"],
                  "model_digest": digest(model), "input_digest": digest(payload), "outputs": values,
                  "external_actions": 0, "note": "Frozen bounded policy; inference is not proof of correctness on new data"}
        result["digest"] = digest(result)
        with reg.transaction():
            if reg.meta("epoch") != epoch or reg.current(task) != old:
                raise Stopped("Policy or authority changed during inference")
            reg._append("inference_recorded", {k: result[k] for k in ("task", "version", "model_digest", "input_digest", "digest")})
        return result
    finally:
        reg.close()


def canary(workspace: str | Path, task: str, worlds: dict, threshold: float) -> dict:
    """Measure an immutable deployed policy on new labeled observations; never auto-rollback."""
    finite(threshold, 0, 1e12, "loss threshold")
    if not isinstance(worlds, dict) or not 1 <= len(worlds) <= 6:
        raise Invalid("Provide 1 to 6 observation worlds")
    reg = Registry(workspace)
    try:
        if reg.stopped():
            raise Stopped("Operator stop is active")
        old = reg.current(task)
        if old is None:
            raise Invalid("No active policy")
        epoch = reg.meta("epoch")
        model = validate_model(old["model"])
        for name, rows in worlds.items():
            if not isinstance(name, str) or not name.isidentifier() or len(name) > 48:
                raise Invalid("Invalid observation world")
            if model["program"]["kind"] == "scheduler":
                # Monitoring budget is tighter than inference because of the exact oracle.
                validate_schedule_cases(rows)
                if len(rows) > 32 or any(r["capacity"] > 1000 or len(r["jobs"]) > 32 for r in rows):
                    raise Invalid("Scheduling monitor exceeds bounded oracle budget")
            else:
                if not isinstance(rows, list) or not 1 <= len(rows) <= 4096:
                    raise Invalid("Invalid monitoring rows")
                for row in rows:
                    exact_keys(row, {"x", "y"}, {"proxy"})
                    finite(row["x"], -10, 10, "x")
                    finite(row["y"], -10000, 10000, "y")
                    finite(row.get("proxy", 0), -1000, 1000, "proxy")
        result = {"schema": "ascent.monitor/1", "task": task, "version": old["version"],
                  "model_digest": digest(model), "data_digest": digest(worlds),
                  "evaluation": evaluation(model, worlds), "threshold": threshold,
                  "data_status": "USER_SUPPLIED_MONITORING_NOT_INDEPENDENT_HOLDOUT", "automatic_rollback": False}
        result["review_recommended"] = result["evaluation"]["worst_loss"] > threshold
        result["digest"] = digest(result)
        with reg.transaction():
            if reg.meta("epoch") != epoch or reg.current(task) != old:
                raise Stopped("Policy or authority changed during canary evaluation")
            reg._append("canary_recorded", result)
        return result
    finally:
        reg.close()


def walkthrough(output: str | Path) -> dict:
    """Fresh synthetic operator demonstration; never reuses an existing workspace."""
    root = Path(output)
    if root.exists() and any(root.iterdir()):
        raise Invalid("Walkthrough requires a new or empty directory")
    root.mkdir(parents=True, exist_ok=True)
    reg = Registry(root / "workspace", create=True)
    reg.close()
    from .reporting import run_markdown, export_policy
    from .problems import make_split
    results = {}
    for task in TASKS:
        result = run_controlled(root / "workspace", task, 17)
        save_json(root / f"{task}.json", result)
        (root / f"{task}.md").write_text(run_markdown(result), encoding="utf-8")
        results[task] = result["record"]
    # This approval is exclusively for the synthetic walkthrough, clearly recorded.
    reg = Registry(root / "workspace")
    try:
        r = results["periodic"]
        ticket = reg.approve(r["run_id"], "SYNTHETIC_WALKTHROUGH_OPERATOR")
        activated = reg.promote(ticket)
        replay_rejected = False
        try:
            reg.promote(ticket)
        except Invalid:
            replay_rejected = True
    finally:
        reg.close()
    prediction = infer(root / "workspace", "periodic", {"rows": [{"x": x} for x in (-1, 0, 1, 2)]})
    save_json(root / "prediction.json", prediction)
    save_json(root / "active-policy.json", export_policy(root / "workspace", "periodic"))
    # Different seed, deliberately shifted response for a monitoring failure, not a claim of natural data.
    observations = make_split("periodic", 201, "development")
    for rows in observations.values():
        for row in rows:
            row["y"] += 5
    monitoring = canary(root / "workspace", "periodic", observations, threshold=0.1)
    save_json(root / "canary-shift.json", monitoring)
    reg = Registry(root / "workspace")
    try:
        reg.stop("Synthetic stop following canary review signal")
    finally:
        reg.close()
    stop_enforced = False
    try:
        infer(root / "workspace", "periodic", {"rows": [{"x": 0}]})
    except Stopped:
        stop_enforced = True
    reg = Registry(root / "workspace")
    try:
        rollback = reg.rollback("periodic", "Synthetic reviewer restores pre-adoption state")
        audit = reg.verify()
        state = reg.snapshot()
    finally:
        reg.close()
    summary = {"version": "0.2.0", "synthetic": True, "asi_established": False,
               "runs": [{"task": t, "status": r["status"], "baseline_worst": r["audit"]["worst_baseline"],
                         "candidate_worst": r["audit"]["worst_candidate"], "strong_worst": r["fixed_generalist_audit"]["worst_loss"],
                         "blocking_reasons": r["adoption"]["blocking_reasons"]} for t, r in results.items()],
               "activation": activated, "ticket_replay_rejected": replay_rejected,
               "predictions": prediction["outputs"], "canary_review_recommended": monitoring["review_recommended"],
               "stop_enforced_for_inference": stop_enforced, "rollback": rollback,
               "final_stopped": state["stopped"], "final_active": state["active"], "audit": audit,
               "external_actions": 0, "model_api_calls": 0}
    save_json(root / "walkthrough.json", summary)
    return summary
