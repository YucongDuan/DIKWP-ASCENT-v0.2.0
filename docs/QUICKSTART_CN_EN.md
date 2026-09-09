# ASCENT 0.2.0 / 具体使用路径

This is a runnable research execution system, not a demonstrated ASI.
这是可运行的研究执行系统，不是已经证明达到ASI的基础模型。

## 最短路径：无需安装软件包

安装Python 3.10或以上后，在PYZ所在目录运行：

```sh
python DIKWP_ASCENT_v0.2.0.pyz doctor
python DIKWP_ASCENT_v0.2.0.pyz serve workspace --port 8765
```

打开 `http://127.0.0.1:8765`。选择 `periodic`、种子17、候选预算96，点击Run。
刷新后的记录为REVIEWABLE时，先Inspect检查每个世界的结果与局限，再依次
Approve和Activate。Infer会使用已冻结的参数直接计算。STOP会阻止后续推理和
受控研究。ROLLBACK恢复之前的本地策略；没有历史版本时恢复为没有活动策略。

## 完整验收演示

```sh
python DIKWP_ASCENT_v0.2.0.pyz walkthrough --output new-walkthrough
```

该命令只能使用新或空目录，并会明确以synthetic reviewer演示审批，不是伪造真人审核。
运行结束应看到 `ticket_replay_rejected=true`、`stop_enforced_for_inference=true`、
`canary_review_recommended=true`、`audit.valid=true`。最终控制器已停止，活动策略为空。

## 源码运行

Windows双击 `START_ASCENT_WINDOWS.bat`；Linux/macOS执行 `./START_ASCENT.sh`。
若启动脚本受策略限制，可手动设置PYTHONPATH后运行 `python -m dikwp_ascent`。
源码包与PYZ均不带基础模型权重；数值演示不需要GPU、API Key或网络服务。
Windows和macOS脚本未在本次环境实机测试。浏览器如被组织策略禁止访问回环地址，
请使用CLI或请本机管理员审核，不建议暴露服务或绕过组织安全策略。

## 不要泄漏工作区

`workspace/controller.key`和`workspace/registry.sqlite`应保密。停止不是删除数据。
共享结果优先使用导出的JSON和Markdown；它们可能含有输入数据摘要和研究信息，
导出前仍需审阅。私有工作区不是加密数据库，不抵御宿主机或同一OS账户恶意程序。
