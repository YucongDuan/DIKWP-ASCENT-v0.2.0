# DIKWP ASCENT Research Kernel 0.2.0

Created by Yucong Duan (段玉聪). Licensed under Apache-2.0.

[中文与英文快速开始](docs/QUICKSTART_CN_EN.md) · [Complete original delivery](release/DIKWP_ASCENT_v0.2.0_FULL_DELIVERY.zip) · [Publication record](PUBLICATION.md)

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
