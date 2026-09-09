# ASCENT-R1: Evidence-gated research record protocol

Project draft, version 0.1.0. This is not an ISO, NIST, OpenAI or third-party standard.

1. A run MUST bind a purpose, task family, parent policy, candidate grammar and budgets.
2. Candidate inputs MUST be data-only and reject unknown fields.
3. A candidate MUST NOT modify the evaluator, policy or authority.
4. At least two declared development and audit worlds MUST be retained.
5. An audit candidate MUST be frozen before its audit observations are acquired.
6. The local controller MUST consume an audit slot before evaluating it and MUST NOT refund the slot after a failed audit.
7. The evaluator MUST recompute outcome loss; self-reported scores or explanations MUST NOT determine it.
8. An apparent improvement MUST be compared with both its incumbent and a stronger fixed reference. Beating the incumbent MUST NOT be represented as state of the art.
9. The audit MUST include non-regression and uncertainty information; uncertainty intervals MUST be labeled descriptive unless supported otherwise.
10. Search costs and assurance costs MUST have separate budgets and MUST NOT be described as measured joules.
11. A research record MUST retain failed candidates and an explicit limitation scope.
12. Local activation MUST require an unexpired one-use ticket bound to the run, source fingerprint, incumbent and control epoch.
13. A stop MUST prevent new controlled work and increment the epoch; resumption MUST NOT validate old tickets.
14. A rollback MUST preserve both the retired version and the reason.
15. Imported external records MUST remain untrusted until validated by the appropriate trusted controller.
16. Observational records MUST NOT silently claim hidden chain-of-thought, legal identity, subjective experience or general intelligence.
17. A policy version MUST NOT inherit permission from an ancestor artifact.
18. ASI status MUST NOT be automatically assigned from task scores.
19. The trust boundary and host-compromise limitations MUST be disclosed.
20. The public browser lab MUST be distinguished from the authenticated controller workflow.

## What is implemented

All twenty requirements have local reference mechanisms or explicit reporting fields. The declared threat model excludes a malicious same-OS-user process or host administrator. Local enforcement is not production isolation, external certification, independent holdout secrecy or bank/legal authority.

## Message types

- `ascent.run/1`: complete immutable content-digested experiment record.
- `LOCAL_POLICY_PROMOTION`: one-use local-controller approval envelope.
- `DatasetScope`: input hashes, counts, synthetic/custom flag and declared worlds.
- `ObservedResiduals`, `EmpiricalCandidate`, `NonCompensableControls`, `ResearchPurpose`: inspectable DIKWP argument records, not private chain of thought.

## Replication note

New independent evaluators should retain source fingerprints and publish all comparisons. Public repeatability and independent hidden testing are different goals; the reference supplies the former and a software API boundary for the latter, not secrecy from source owners.
