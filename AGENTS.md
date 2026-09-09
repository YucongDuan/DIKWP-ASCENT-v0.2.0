# Repository agent instructions

This repository is a bounded numerical research kernel, not a demonstrated ASI.
Run `PYTHONPATH=src python -m pytest -q`. Keep candidates data-only. Do not add shell,
provider calls, outbound networking, arbitrary code execution, automatic promotion,
or authority inheritance. A source change invalidates existing local approvals.

Do not edit expected metrics to hide failed experiments. Regenerate validation with
`scripts/validate_release.py` and retain the adverse fixed-reference comparisons.
Public synthetic repeatability is not an independent blind test. Protect any local
controller.key and registry.sqlite. Do not add live workspaces to version control.
