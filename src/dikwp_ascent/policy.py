"""Frozen control policy. Candidate programs cannot write these fields."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import time
from .canonical import Invalid, BudgetExceeded, Stopped, integer, digest

CONTROL = {
    "version": "ASCENT-CP-2",
    "candidate_format": "data-only-allowlisted-dsl",
    "network": False,
    "shell": False,
    "arbitrary_code": False,
    "external_payment": False,
    "self_granted_permission": False,
    "self_promotion": False,
    "self_restart": False,
    "holdout_feedback_during_search": False,
    "candidate_can_change_verifier": False,
    "human_claim_certification": False,
    "promotion_scope": "local-policy-version-only",
    "strong_reference_gate": "per-world-nonregression-absolute-1e-9",
    "deployed_incumbent": "frozen-parameters-not-refitted",
}
CONTROL_DIGEST = digest(CONTROL)

@dataclass(frozen=True)
class Limits:
    proposals: int = 96
    generations: int = 6
    work_units: int = 8_000_000
    seconds: int = 30
    audit_work_units: int = 8_000_000

    def __post_init__(self):
        integer(self.proposals, 4, 256, "proposals")
        integer(self.generations, 1, 16, "generations")
        integer(self.work_units, 10_000, 100_000_000, "work_units")
        integer(self.seconds, 1, 120, "seconds")
        integer(self.audit_work_units, 10_000, 100_000_000, "audit_work_units")

class Meter:
    """A work budget for fixed built-ins, not a sandbox for untrusted native code."""
    def __init__(self, limits: Limits, stop_check=None):
        self.limits = limits
        self.work_units = 0
        self.proposals = 0
        self.start = time.monotonic()
        self.stop_check = stop_check or (lambda: False)

    def check(self):
        if self.stop_check():
            raise Stopped("Operator stop is active")
        if time.monotonic() - self.start > self.limits.seconds:
            raise BudgetExceeded("Wall-clock budget exceeded")

    def charge(self, units: int):
        self.check()
        integer(units, 0, 100_000_000, "work charge")
        if self.work_units + units > self.limits.work_units:
            raise BudgetExceeded("Deterministic work budget exceeded")
        self.work_units += units

    def proposal(self):
        self.check()
        if self.proposals >= self.limits.proposals:
            raise BudgetExceeded("Proposal budget exceeded")
        self.proposals += 1
