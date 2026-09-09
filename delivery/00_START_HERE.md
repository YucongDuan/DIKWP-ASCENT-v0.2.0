# ASCENT 0.2.0 — Start here / 先读这里

This is an ASI-oriented bounded research execution system, NOT a demonstrated ASI.
这是面向ASI研究的可执行系统，不包含基础模型权重，也没有证明达到ASI。

## Fast path / 最快启动

Unzip this package. With Python 3.10+ installed, open a terminal in the `program` folder:
解压后，在program目录打开终端：

    python DIKWP_ASCENT_v0.2.0.pyz doctor
    python DIKWP_ASCENT_v0.2.0.pyz serve workspace --port 8765

Open http://127.0.0.1:8765. Select periodic, seed 17. Inspect before approving;
approval and activation are distinct. Stop blocks further research and inference.

## Source / 源码

The full directly runnable repository is `ascent/`. Windows: double-click
START_ASCENT_WINDOWS.bat. Linux/macOS: ./START_ASCENT.sh. The SOURCE.zip and
Git Bundle in source-distributions are optional alternate distributions.
Windows/macOS launchers were not executed in this Linux validation environment.

## Evidence / 证据

`program/DIKWP_ASCENT_RESULTS_v0.2.0.html` is an OFFLINE evidence viewer and
fixed-model numerical example, not the authenticated live controller.

`reports/` contains the 16-page Chinese manual, editable Word, English engineering
guide and protocol. `evidence/` contains measured validation, manifests and hashes.
All numerical examples are synthetic. No live customer, model API or remote publish
is asserted. HMAC is local installation authentication, not a human identity proof.

## Reproduce / 复现

    python DIKWP_ASCENT_v0.2.0.pyz walkthrough --output new-demo

Use a new or empty output directory. This command uses an explicitly synthetic
reviewer, ends stopped after rollback, and cannot be treated as real human approval.
Never publish workspace/controller.key or workspace/registry.sqlite.
