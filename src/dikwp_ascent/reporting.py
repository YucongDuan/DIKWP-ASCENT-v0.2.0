"""Human-readable, evidence-bound reports and local policy exports."""
from __future__ import annotations

import json
from pathlib import Path
from .canonical import Invalid, digest
from .engine import verify_record
from .registry import Registry


def run_markdown(result: dict) -> str:
    r = result.get("record", result)
    verify_record(r)
    lines = [f"# ASCENT experiment: {r['task']}", "", f"Run: `{r['run_id']}`", "",
             f"**Decision: {r['status']}**. ASI established: **false**.", "",
             "## Three distinct comparisons", "",
             "| World | Frozen incumbent / initial baseline | Candidate | Strong fixed reference |",
             "|---|---:|---:|---:|"]
    for name, row in r["audit"]["worlds"].items():
        strong = r["fixed_generalist_audit"]["world_losses"][name]
        lines.append(f"| {name} | {row['baseline']:.9g} | {row['candidate']:.9g} | {strong:.9g} |")
    lines += ["", "Losses are task-specific. Regression MSE and scheduling regret must not be averaged as one intelligence score.", "",
              "## Adoption gates", "", f"Incumbent audit passed: {r['audit']['eligible']}", "",
              f"Strong-reference per-world nonregression: {r['adoption']['strong_reference_nonregression']}", "",
              "Blocking reasons: " + (", ".join(r["adoption"]["blocking_reasons"]) or "none; operator review still required"), "",
              "Strong-reference comparison uses an absolute numerical tolerance of 1e-9, not a significance claim.", "",
              "## Frozen candidate", "", "```json", json.dumps(r["search"]["champion"]["model"], indent=2), "```", "",
              "## Scope and lineage", "", f"Incumbent evaluation: `{r['search']['incumbent_evaluation_mode']}`.", "",
              f"Parent version: `{r['parent_version']}`.", "",
              f"Candidate digest: `{r['candidate_digest']}`.", "",
              f"Source fingerprint: `{r['source_fingerprint']}`.", "",
              f"Record digest: `{r['record_digest']}`.", "",
              f"Candidates evaluated: {r['search']['evaluated_count']}.", "",
              f"Search status: `{r['search']['search_status']}`.", "",
              "## What remains unproved", ""]
    lines += ["- " + x for x in r["limitations"]]
    lines += ["- The fixed reference is not a comprehensive state-of-the-art benchmark.",
              "- A frozen policy may behave poorly on data outside its declared domain.",
              "- No foundation model was called or trained in this experiment.", ""]
    return "\n".join(lines)


def export_policy(workspace: str | Path, task: str) -> dict:
    reg = Registry(workspace)
    try:
        old = reg.current(task)
        if old is None:
            raise Invalid("No active policy to export")
        result = {"schema": "ascent.policy-export/1", "task": task, **old,
                  "authority_transferred": False, "note": "Portable numerical parameters, not an approval ticket or external authority"}
        result["digest"] = digest(result)
        return result
    finally:
        reg.close()
