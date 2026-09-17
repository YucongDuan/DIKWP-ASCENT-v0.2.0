# ASCENT 0.2 · Numerical research — practical guide / 使用导读

[Project README](README.md) · [Detailed project record](https://github.com/YucongDuan/YucongDuan/blob/main/projects/1362110634.md) · [Research portfolio](https://github.com/YucongDuan)

Study numerical experiments, stronger-reference comparisons, explicit adoption, inference, monitoring and rollback.

研究数值实验、强参考比较、明确采用、推断、监测与回退。

## First result / 第一个结果

Use Python 3.10+ and a fresh workspace. Start with the documented walkthrough before the local operator console.

使用Python 3.10+和新的工作目录，先运行文档中的完整示例，再进入本地操作控制台。

[Inspect the entry file / 查看入口文件](docs/QUICKSTART_CN_EN.md)

```bash
PYTHONPATH=src python -m dikwp_ascent walkthrough --output fresh-walkthrough
```

Run from the project root after downloading and extracting the source. For a ZIP-distributed project, enter the inner project directory first. Commands using `PYTHONPATH=src` use POSIX shell syntax; PowerShell users can set `$env:PYTHONPATH='src'` before the Python command.

下载解压后在项目根目录运行；以ZIP分发的项目先进入包内项目目录。含`PYTHONPATH=src`的命令使用POSIX语法，PowerShell可先设置`$env:PYTHONPATH='src'`。

## Inspect what changed / 检查变化

Keep one input and its assumptions, run the documented example, then change one condition and compare the actual output. Preserve both successful and unsuccessful results. Use the README's dependency and test instructions for full verification.

保留输入及其假设，运行文档示例，再改变一个条件并比较实际输出。成功与失败结果都应保留；完整验证按README中的依赖和测试说明执行。

## Next contribution / 下一步贡献

Compare a declared custom regression split against a fixed stronger reference. / 将明确划分的自定义回归数据与固定强参考比较。

A useful public report includes the exact revision, environment, command, minimal input, expected result and observed result. Keep private data out of public examples.

公开报告应包含确切版本、环境、命令、最小输入、预期结果与实际结果。公开示例应去除私人数据。

## Research and collaboration / 研究与合作

[Written collaboration guide](https://github.com/YucongDuan/YucongDuan/blob/main/COLLABORATE.md) · [Citation guide](https://github.com/YucongDuan/YucongDuan/blob/main/CITING.md)

Choose a question, a data scope, a source revision, responsible people, a license and an inspectable deliverable. The project's original implementation scope, author notices and component licenses remain in its README and source.

合作请明确问题、数据范围、源码版本、责任人、许可与可审阅的交付物。项目实现范围、作者声明和组件许可见原README与源码。

Research basis: Yucong Duan (段玉聪). Guide updated 17 September 2026.
