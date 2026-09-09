# ASCENT 0.2.0 — Engineering and Operator Guide

Release date: 2026-09-08. Apache-2.0.

This release supplies an actual bounded research runtime, not a foundation model or demonstrated ASI. The live operator console is distinct from the static offline results viewer.



---

# DIKWP ASCENT Research Kernel 0.2.0

**Research that must earn its next version.** A local, bounded numerical research
system with frozen-model inference, strong-reference adoption gates, review,
revocation, monitoring and rollback. **Not a demonstrated ASI or a foundation model.**

Apache-2.0 · Python 3.10+ · no third-party runtime dependency · no candidate native
code execution · no external model calls · no autonomous deployment.

## Start the real operator console

From the extracted source directory:

```sh
# Linux/macOS
./START_ASCENT.sh
# Or on any platform, from this directory:
PYTHONPATH=src python -m dikwp_ascent serve workspace --port 8765
```

On Windows, double-click `START_ASCENT_WINDOWS.bat`, or use PowerShell:

```powershell
$env:PYTHONPATH="$PWD\src"
py -3 -m dikwp_ascent serve workspace --port 8765
```

Open `http://127.0.0.1:8765` in a browser. A standard Python installation is required;
no GPU is required for the bundled small numerical experiments. This release was
executed on Linux with Python 3.13.5. Windows/macOS launchers are provided but were
not executed here. An organization may block local browser servers.

With the downloadable PYZ:

```sh
python DIKWP_ASCENT_v0.2.0.pyz doctor
python DIKWP_ASCENT_v0.2.0.pyz serve workspace --port 8765
```

The console actually calls the Python controller. It can run experiments, inspect
results, approve a specific record, activate its policy, compute predictions,
stop, resume and roll back. Approval and activation are separate explicit actions.
Closing the server with Ctrl+C stops the controller; restarting does not silently
resume a previously stopped workspace. Never expose the server to a network.
`http.server` is research infrastructure, not a production gateway.

## Reproduce the complete lifecycle

```sh
PYTHONPATH=src python -m dikwp_ascent walkthrough --output fresh-walkthrough
```

This creates a NEW synthetic workspace, evaluates all four tasks, blocks three
seed-17 candidates at the strong-reference gate, synthetically approves and
activates the periodic policy, runs inference, rejects a replayed ticket,
detects synthetic drift, stops inference, rolls back and verifies the ledger.
It is an automated test scenario, **not evidence of a real human approval**.
Output must be new or empty. Existing research is never silently reset.

## What changed from 0.1.0

1. An active model is compared using its frozen deployed coefficients, not refitted
   before each new experiment.
2. A candidate must pass both the incumbent audit and per-world non-regression
   against the predeclared stronger reference before approval is available.
3. Adopted policies can be used for typed inference and labeled-data monitoring.
4. Finite predeclared campaigns preserve completed, blocked, failed and not-run trials.
5. A loopback console operates the real controller, with local session token,
   Host/Origin checks, bounded JSON and one concurrent research job.
6. Explicit CSV split intake and a file-only model-proposal handoff are included.

## Four tasks, not universal intelligence

`quadratic`, `periodic`, `sensor_shift`: one-dimensional basis regression in a finite
feature language. `scheduling`: bounded priority/local-swap policies, evaluated
against an exact integer-knapsack oracle. `custom_regression` accepts a declared
train/development/audit dataset with at least two evaluation worlds.

Candidates are JSON data, never Python, shell, paths or tool calls. The system
fits small numerical coefficients; it does not train a foundation model.

## Actual seed-17 results

Lower is better. Regression MSE and scheduling regret are different units.

| Task | Incumbent worst | Candidate worst | Fixed reference worst | Adoption |
|---|---:|---:|---:|---|
| Quadratic | 27.611113 | 0.003419 | 0.002834 | NOT_PROMOTABLE |
| Periodic | 9.172172 | 0.004294 | 0.188747 | REVIEWABLE |
| Sensor shift | 15.695588 | 0.003923 | 0.002883 | NOT_PROMOTABLE |
| Scheduling | 0.193899 | 0.008158 | 0.006953 | NOT_PROMOTABLE |

`REVIEWABLE` means the local reference gates passed, not SOTA, safety certification,
human-level generality, or a recommendation to deploy. All synthetic results and
adverse comparisons are in `validation/`. Campaign: 12 declared/completed trials,
8 reviewable, 4 not promotable, zero automatic adoptions.

## Manual controlled sequence

After installation of the Wheel (`python -m pip install ./dikwp_ascent-0.2.0-py3-none-any.whl`):

```sh
ascent init workspace
ascent run workspace --task periodic --seed 17 --output run.json
ascent report run.json --output experiment.md
ascent status workspace
# Replace RUN_ID below by the printed actual run identifier.
ascent approve workspace RUN_ID --operator local-reviewer --ttl 300 --output approval.json
ascent promote workspace approval.json
ascent infer workspace --task periodic --input examples/predict-periodic.json --output predictions.json
ascent canary workspace --task periodic --data examples/monitor-drift.json --threshold 0.1 --output monitor.json
ascent export-policy workspace --task periodic --output active-policy.json
ascent stop workspace --reason "Review requested"
ascent rollback workspace --task periodic --reason "Restore prior local policy"
ascent audit workspace
```

Use a fresh directory for version 0.2.0. Version 0.1 records remain historical data;
there is no automatic authority or database migration.

## Tests

```sh
python -m pip install -r requirements-dev.txt
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python scripts/validate_release.py
```

See `docs/ENGINEERING_GUIDE_EN.md`, `docs/QUICKSTART_CN_EN.md`, `docs/SECURITY.md`,
`docs/PROPOSER_INTERFACE.md`, and `protocol/ASCENT-R2.md`. The static offline results
viewer in `web/index.html` is distinct from the live controller console.

## Trust boundary

The OS user, Python installation, source, controller key and SQLite state are
trusted. HMAC authenticates local records, not civil identity, input truth or a
hostile-host environment. A candidate module boundary is not an OS sandbox.
Public synthetic data are not secret independent holdouts. No API, network peer,
provider, financial transaction, remote publish, self-copy or authority expansion
is implemented. Independent real-world experiments remain necessary.


---

# File-only external-model proposal interface

```sh
ascent proposer-request --task periodic --seed 17 --output request.json
```

The request contains training/development examples, grammar and task. It excludes
the audit set. Human-reviewed manual sharing may still disclose private training
information. No external API is invoked, no provider is required, and no actual
GPT or other model performance is claimed.

An external model may return ONLY an array of at most 32 typed programs:

```json
[
  {"kind":"basis","features":["sin","x","x2"],"ridge":0.001},
  {"kind":"basis","features":["x","x2"],"ridge":0.01}
]
```

Use:

```sh
ascent run workspace --task periodic --seed 17 --candidate-file candidates.json --output run.json
```

Rejected content includes source code, commands, paths, tools, evaluator changes,
self-scores, identity assertions and unknown fields. Coefficients are fitted by the
trusted engine; a proposer does not control the verifier or the approval process.

CSV data must explicitly use `split,world,x,y,proxy`. Valid split names are `train`,
`development`, `audit`; train world is `in_distribution`. Evaluation worlds must
match between development and audit, with at least two and at most six worlds.
Each split/world needs 8 to 4096 rows. Identical record overlap is rejected; this
cannot establish causal independence or eliminate semantically similar leakage.

```sh
ascent csv-import examples/custom-dataset.csv --output custom-data.json
ascent proposer-request --task custom_regression --data custom-data.json --output request.json
ascent run workspace --task custom_regression --data custom-data.json --candidate-file candidates.json --output run.json
```

A custom task rejected by the fixed-reference gate is a result, not a bug. Keep the
failed record and use an independently justified new evaluation design; do not keep
trying on disclosed audit data until a desired result appears.


---

# ASCENT 0.2.0 threat model

## In scope

Untrusted data-only candidates, unknown/oversized/malformed JSON, nonfinite numbers,
invalid feature names, wrong family, deceptive self-scores, reused audit content,
expired/replayed approval, parent/source mismatch, stop/resume races, and accidental
local cross-origin API use. Full source/control authority remains with the operator.

The live server binds exactly 127.0.0.1. It validates Host, rejects other Origins,
requires the server-session token on API calls, accepts bounded JSON, and permits
one research worker at a time. There is no arbitrary file path, shell, proxy,
provider credential, tool, payment or remote-publish endpoint. The root page is
available to the local user. Tokens are anti-CSRF controls, NOT identity certificates.

The registry serializes authority transitions with SQLite transactions. Audits use
a consistent read transaction. Run approval checks the source fingerprint; activation
checks record, incumbent, epoch, expiry and unused ticket in one transaction. Stop
advances the epoch. Resume never revalidates an earlier epoch's approval.

## Outside scope

A malicious same-OS-user process, host administrator, compromised interpreter or
source, stolen controller key, replacement of the entire database plus trusted
history, filesystem rollback, hardware failure, network-deployed multi-user access,
and civil identity or legal authorization. An HMAC cannot solve those problems.

Module separation is not process/container isolation. Candidates cannot supply
native code; expanding the grammar to native code is a new security design requiring
separate review. Resource checks are cooperative and bounded-built-in accounting,
not a scheduler for hostile machine code or proof of measured energy consumption.

`http.server` is not a production server. Do not forward this service through a
public tunnel, shared host, reverse proxy or a non-loopback address. Use an isolated
research OS account; protect and back up key/state together. A forced process kill
cannot guarantee a final stop event was written. After abnormal termination inspect
the audit and stopped state before reuse.

## Evidence limits

Public generators do not constitute secret holdouts. One-use audit registration
limits local repeated tuning; it does not defeat reconstructed synthetic data,
semantically duplicated observations or resetting the whole trusted controller.
The strong reference is fixed, not the best known scientific solution. Bootstrap
intervals are descriptive and do not correct unrestricted adaptive multiple testing.

## Model APIs

No network model provider is implemented or called. The proposer-request export
contains training and development data only. Before manually sending it to any
external provider, establish authorization and privacy terms. Never send controller
keys, approval tickets, private audit data or raw internal chains of thought.

## Sources

Python server warning: https://docs.python.org/3/library/http.server.html
SQLite isolation: https://www.sqlite.org/isolation.html


---

# ASCENT-R2: local research-to-operation protocol

Project specification v0.2.0; not a formal standards-body or third-party certification.

1. A run binds task, purpose, dataset scope, source fingerprint, parent and finite budgets.
2. Candidate inputs are data-only and validated against the explicit bounded grammar.
3. Candidate self-reports never determine task loss or permission.
4. Search receives training/development data, not audit observations.
5. Freeze the candidate before acquiring audit observations at the trusted boundary.
6. Consume the local audit content slot before evaluation; failure never refunds it.
7. Record separate search and assurance budgets; units are not physical joules.
8. Retain every evaluated failure and all declared interpretations.
9. Compare active incumbents using frozen deployed coefficients, not retraining.
10. Require incumbent audit and per-world strong-reference non-regression for REVIEWABLE.
11. Keep fixed-reference comparisons visible even when favorable to the candidate.
12. Do not treat numerical reference tolerance as statistical significance or SOTA proof.
13. Approval requires inspected evidence, local operator label, expiry and source match.
14. Activation atomically validates parent, control epoch and one-use ticket.
15. Inference uses only an active frozen model and records input/model/output digests.
16. Monitoring labels user observations as monitoring, not independent hidden testing.
17. Drift triggers a review suggestion, not an autonomous replacement decision.
18. Stop advances the control epoch; resumption does not revive prior tickets.
19. Rollback preserves evidence and the retirement reason.
20. Campaigns declare the finite grid before execution and preserve failed/not-run trials.
21. The browser evidence viewer is not the authenticated controller console.
22. Loopback API access requires local session validation and bounded messages.
23. Model export transfers parameters, not authority, credentials or approval history.
24. Explain trusted-host, secret-test, statistical and deployment limitations.
25. General intelligence, consciousness, legal identity and universal safety are not
    inferred from local task performance.

Implemented reference messages: ascent.run/2, ascent.campaign/1,
ascent.proposer-request/1, ascent.inference/1, ascent.monitor/1,
ascent.policy-export/1 and LOCAL_POLICY_PROMOTION.

This specification describes the current reference, not a claim of compliance with
ISO, NIST, OpenAI, DeepMind or any external standard. The old ASCENT-R1 record remains
historical; use a fresh workspace for this version.


---

# Evidence-driven expansion roadmap

Stage 1: reproduce the bundled finite tasks, negative controls, actual inference,
monitoring and revocation. Publish adverse comparisons, not only large improvements.

Stage 2: an independent data owner prepares a new task and previously unseen audit
set, with equal-budget strong baselines. An external model may propose JSON programs
through manual file intake. Record actual calls separately if a future connector is
built; this release makes none.

Stage 3: extend the candidate grammar for a specific scientific problem only after
adding a trustworthy verifier and meaningful distribution-shift tests. Task-specific
regression results do not transfer automatically to medicine, finance or legal work.

Stage 4: any native-code, remote-tool or real experimental actuator requires OS-level
isolation, outbound-network policy, credentials separated from proposers, independent
monitoring, incident response, rights review and explicit operator authority. Merely
adding a prompt is not an adequate security control.

Stage 5: generalized intelligence claims require unknown tasks, diverse fields, strong
human-team comparators, resource accounting, long-horizon reliability and independent
replication. ASI status is not computed from this project's numerical benchmark.

Model/API performance, foundation-weight training, physical experiments, universal
alignment, real-world delegated identity and remote GitHub deployment are not delivered.


## Reproduction evidence

Baseline 0.1.0 passed its original 54 tests before modification. Version 0.2.0 passed 93 tests. The public seed-17 demonstration has one reviewable task and three blocked by the stronger-reference gate. The twelve-trial campaign retained all outcomes: eight reviewable, four not promotable, no automatic adoption.

The complete walkthrough rejected ticket replay, computed actual frozen-model predictions, requested review on deliberately shifted labels, blocked inference after stop and rolled back to no active policy. The final local audit had 15 events and was valid. These are synthetic operator scenarios, not a human endorsement or independent scientific validation.

The finite model explores 47 abstract states and 63 transitions with four deliberately unsafe variants rejected. It is a bounded independent control model, not TLC or a proof of the full implementation.

Real loopback HTTP endpoints were tested with an HTTP client. The managed browser blocked direct loopback navigation. UI tests used the same server page with only the fetch function bridged to the real HTTP backend. This tests UI transitions with real computation, not direct-navigation or CSP enforcement in the managed browser. Windows/macOS launchers were not executed.

See validation/ for the full records and the delivery distribution receipt for fresh-source, Wheel, PYZ and Git Bundle replay. No private controller keys or databases are shipped.
