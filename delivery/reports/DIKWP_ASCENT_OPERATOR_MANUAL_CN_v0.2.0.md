# ASCENT 0.2.0 研究执行系统

证据约束型ASI研究、冻结模型推理与可撤销演化内核

交付日期：2026年9月8日｜许可证：Apache-2.0｜版本：0.2.0

## 交付定位

这是一套已经运行的有限研究系统：提出数据型候选、拟合或执行策略、检验多个数据世界、比较更强参考、保存失败、经本地审核采用版本，再执行预测、监测、停止和回退。它不包含基础模型权重，也没有证明达到人工超级智能。

## 这一版具体新增

真实本地控制台；旧模型冻结参数比较；强参考逐世界采用门；采用后的直接推理；新观测漂移检查；预声明批量实验；明确分割的CSV导入；外部模型的文件候选接口。

## 三条阅读路径

立即使用：第2—3页。理解如何研究与采用：第4—8页。接入数据、批量复现、排查和安全部署：第9—16页。

参考结果为公开合成数据上的实际计算，不是现实科研成果、真人批准、独立盲测、监管认证或远端GitHub发布。报告只把已执行的检查记为完成。

```text
Research → Verify → Inspect → Approve → Activate
                     ↓
           Infer → Monitor → Stop / Roll back
```

# 01 / 交付目录与安装

最直接的运行方式是PYZ：它是一个Python可执行压缩包，不需要先安装本项目。请先安装Python 3.10或以上版本。内置数值实验只使用CPU，无需GPU、API密钥和云账号。

```text
python DIKWP_ASCENT_v0.2.0.pyz doctor
python DIKWP_ASCENT_v0.2.0.pyz serve workspace --port 8765
```

浏览器打开 http://127.0.0.1:8765。doctor应显示版本0.2.0、console_resource_present=true和空的runtime_dependencies。服务保持在前台；按Ctrl+C结束时会尝试停止控制器。

| 文件或目录 | 作用 |
| --- | --- |
| DIKWP_ASCENT_v0.2.0.pyz | 独立Python入口；所有CLI功能可用 |
| dikwp_ascent-0.2.0-py3-none-any.whl | 标准Python安装包，安装后命令名ascent |
| SOURCE.zip / Git Bundle | 可检查源码、测试、协议与真实版本历史 |
| RESULTS_v0.2.0.html | 离线结果查看器；不是有权限的控制台 |
| validation/ | 实验、失败、监测、复现及浏览器检查记录 |

## 源码启动

Windows可双击START_ASCENT_WINDOWS.bat；Linux/macOS在源码目录执行./START_ASCENT.sh。脚本仅设置本项目路径并启动Python，不修改系统设置。

```text
# 安装Wheel后的等价启动
python -m pip install ./dikwp_ascent-0.2.0-py3-none-any.whl
ascent serve workspace --port 8765
```

本次实机环境为Linux、Python 3.13.5和Chromium。Windows/macOS启动器已提供，但未在这两个系统上实机执行。组织策略阻止回环地址时请使用CLI或由管理员审核，不应通过暴露公共端口绕过策略。

# 02 / 第一小时操作

## 先做一次完整、独立演示

```text
python DIKWP_ASCENT_v0.2.0.pyz walkthrough --output fresh-demo
```

fresh-demo必须不存在或为空。程序会建立新的合成控制器，执行四类任务，以明确标注的synthetic reviewer完成一次审批演示，再运行预测、重复票据拒绝、漂移提示、停止和回退。不能把这个测试审核者当成现实人员已经批准。

## 然后使用自己的控制台

选择periodic，种子17，候选上限96，每阶段时间预算30秒。点击Run后，后台实际执行研究，界面显示本地任务状态和记录，不只是播放预存动画。

结果出现后点击Inspect。先看每个世界的候选损失、当前模型损失、固定参考损失，以及不可采用理由。只有REVIEWABLE记录才提供Approve；批准后仍需单独点击Activate。

在“Use the active policy”输入x值，点击Infer。此时执行的是刚采用的冻结参数，不重新搜索、不重新拟合、不请求大模型。随后测试STOP；新推理和研究应被拒绝。

| 状态 | 应该如何理解 |
| --- | --- |
| REVIEWABLE | 采用门通过，进入审阅；不是自动推荐采用 |
| NOT_PROMOTABLE | 结果保留，但当前采用条件未满足 |
| STOPPED | 控制器已停止；恢复是明确的人类操作 |
| 无活动策略 | 没有被采用的模型；不能执行受控推理 |

下一次实验不得反复使用已披露的同一验收数据。换一个合成种子可测试工作流，但仍不是独立真实世界验证。当前版本与0.1的控制策略不同，使用新的workspace，不自动迁移旧授权。

# 03 / 架构：研究与控制分离

附件区分了“是否执行目标”与“目标模糊或遇到压力时是否坚持价值底线”。本系统把这一问题转成可以测试的结构：提高任务性能的代码，不拥有修改评估器和授权机制的接口。[F1]

```text
数据/候选JSON
    ↓
输入检查 → 搜索器 → 冻结候选 → 验收器
                                     ↓
                             强参考逐世界门
                                     ↓
                          不可采用 / 可审阅记录
                                     ↓
                  本地批准票据 → 原子采用 → 冻结推理
                                     ↓
                            监测、停止、回退
```

| 模块 | 实际职责 |
| --- | --- |
| dsl.py / problems.py | 候选语法、可信执行器、数据生成及检查 |
| search.py / evaluator.py | 候选产生、开发集选择、损失与区间计算 |
| engine.py / policy.py | 研究顺序、冻结摘要、预算和采用门 |
| registry.py | 一次性验收、本地票据、版本、停止和账本 |
| runtime.py / intake.py | 批量实验、推理、监测、CSV及模型候选接口 |
| server.py / console.html | 真实回环API和交互控制台 |
| reporting.py / cli.py | 报告、参数导出及全部命令入口 |

候选只是数据对象。研究器、评估器和控制器是同一可信软件中的不同模块，并非独立操作系统安全域。对同一OS用户或宿主管理员的恶意控制，本版不提供隔离保证。

# 04 / 当前能力具体到什么程度

| 任务 | 研究对象 | 独立计算的目标 |
| --- | --- | --- |
| quadratic | 噪声中的二次响应 | 各世界均方误差 |
| periodic | 线性趋势与周期项 | 分布外预测误差 |
| sensor_shift | 训练中好用、变化后失效的代理 | 代理失效时损失 |
| scheduling | 容量受限的收益选择 | 相对动态规划最优值的遗憾 |

回归语法允许x、x²、x³、sin(x)、cos(x)和proxy。候选选择特征组合与正则化系数，可信实现拟合少量实数系数。调度候选选择收益/成本排序指数和至多三轮局部交换。

默认训练集为72条记录；开发集和验收集各有三个世界，每世界分别48和128条记录。世界名为in_distribution、shifted_inputs和proxy_failure。自定义任务只支持同样的一维回归格式，不是任意维度数据科学平台。

## 候选的准确形态

```text
{"kind":"basis",
 "features":["sin","x","x2"],
 "ridge":0.001}
```

这不是Python表达式，也没有可调用的文件、进程、网络或账户。未知字段、自报分数、非有限数字、超范围参数及错误任务族会被拒绝。

## 没有交付的能力

没有基础大模型、通用聊天推理、自动浏览、任意编程、物理实验器械控制、基础权重训练或模型API接入。把任务标题改成某个未解科学问题，不会扩展候选语言或产生相应研究能力。扩大能力需要新增任务语义、验证器、数据和独立评估。

# 05 / 搜索与验收数学

回归损失为每个世界的均方误差；调度损失为(最优收益−候选收益)/max(1,最优收益)。最优收益由独立动态规划例程计算，不采信候选对自己输出的评价。

```text
J_dev(θ) = max_w L_w(θ) + 10⁻⁵ × complexity(θ)
θ* = 在预算内选出的最低开发集评分候选
```

搜索是有限候选语言中的算法搜索，不承诺连续参数空间或全部程序空间的全局最优。默认上限为96个候选、6代、8,000,000记账工作单位；验收保留独立8,000,000单位预算。时间限制每阶段最多120秒。

## 当前模型门

候选须在各验收世界不显著数值退化，最差世界损失必须下降，配对Bootstrap改进区间的下界也必须超过阈值。默认600次重采样，区间标注为描述性95%区间，不对无限试验和任意自适应选择提供统计保证。

## 新增强参考门

```text
对每个验收世界w：
L_w(candidate) − L_w(reference) ≤ 10⁻⁹

REVIEWABLE = 当前模型验收通过 AND 强参考逐世界门通过
```

1e−9只是数值非退化容差，不是相对参考模型的统计显著性证明。固定参考也不是全世界最优模型。本版故意采用严格门：宁可保留一个有趣但不可采用的结果，也不把“比简单基线好”自动当成研究进步。

AlphaEvolve采用候选生成、评价和演化选择的研究结构，可作为架构参照；本项目没有复现它的系统或成果，也没有进行同任务同预算比较。[P1]

# 06 / 实际结果与反例

以下为本次运行种子17所得结果。前三行单位是MSE，最后一行是调度遗憾比例。均为合成数据，不能跨任务比较绝对数值，也不能换算成通用智能等级。[R1]

| 任务 | 当前/候选/参考：最差损失 | 采用状态 |
| --- | --- | --- |
| 二次响应 | 27.611113 / 0.003419 / 0.002834 | 不可采用 |
| 周期响应 | 9.172172 / 0.004294 / 0.188747 | 可审阅 |
| 代理失效 | 15.695588 / 0.003923 / 0.002883 | 不可采用 |
| 资源调度 | 0.193899 / 0.008158 / 0.006953 | 不可采用 |

四项都比简单基线好，但三项在至少一个验收世界不如固定参考。它们被标为NOT_PROMOTABLE，而不是从报告中删除。周期任务在三个验收世界都满足强参考门，可进入本地审阅。

## 采用的周期模型

```text
y = 0.397302031
  + 2.022909449 sin(x)
  + 0.685216587 x
  + 0.004592292 x²
```

这是真实拟合参数，不是人工填入的标准答案。使用冻结模型预测x=−1、0、1、2，得到−1.985541871、0.397302031、2.789330516、3.625530729。

## 必须失败的案例

只使用proxy的候选可能在训练中表现很好，却在代理变量失效的世界失败。validation/rejected_shortcut.json保存了这一反例。验证者不因候选叙述合理、自称有信心或训练分数优秀而放宽结果检查。

# 07 / 本地采用、冻结与回退

0.1.0持续研究会按旧特征重新拟合基线。这不等于比较真正部署中的旧参数。0.2.0改为读取活动版本的完整冻结模型，保持其系数不变；候选仍在新训练集拟合。记录公开incumbent_evaluation_mode。

```text
ascent init workspace
ascent run workspace --task periodic --seed 17 --output run.json
ascent report run.json --output experiment.md
ascent status workspace
```

把下列RUN_ID替换为本次打印的真实运行标识。请实际查看结果后执行，不能复制别人的运行ID或历史票据。

```text
ascent approve workspace RUN_ID --operator local-reviewer --ttl 300 --output approval.json
ascent promote workspace approval.json
```

票据绑定运行摘要、源码指纹、父版本、控制代次、范围、期限和唯一ID。签名为本地HMAC；它证明这个安装实例的秘密持有，不证明local-reviewer是某位真实身份人士。

采用在事务中检查全部条件并消费票据。旧父版本、修改过的源码、到期票据和重复票据都不能继续使用。共享导出的模型参数不会附带批准权。SQLite事务用于本地状态原子转换，不构成外部部署保障。[P3]

```text
ascent stop workspace --reason "Review required"
ascent rollback workspace --task periodic --reason "Return to prior policy"
ascent audit workspace
ascent resume workspace --operator local-reviewer
```

停止提高授权代次，研究和推理都会被拒绝；恢复不会复活旧票据。回退保留原版本和原因。若没有上一活动版本，回退结果是没有活动模型，而不是虚构一个替代模型。

# 08 / 自己的数据如何进入

本版支持自定义一维回归数据。你需要先确定目标y、特征x、可选proxy，以及为什么数据分布会变化。先设计验收，再选择候选；不要随机混合后宣称解决真实分布外问题。

```text
split,world,x,y,proxy
train,in_distribution,-1.0,2.1,0
development,normal,0.2,1.3,0
development,shifted,2.0,5.1,0
audit,normal,0.3,1.5,0
audit,shifted,2.2,5.9,0
```

上面只有格式示意，不足以运行。完整示例在examples/custom-dataset.csv。train需8—4096条；development和audit各需2—6个同名世界，每世界8—4096条。x范围−10到10；y范围−10000到10000；proxy范围−1000到1000。

```text
ascent csv-import examples/custom-dataset.csv --output custom-data.json
ascent run workspace --task custom_regression --data custom-data.json --output custom-run.json
```

CSV限制2MB，列名必须完全一致。JSON顶层仅允许train、development和audit。相同记录在不同分割或世界间重叠会被拒绝，但语义相似、同一主体重复测量、时间泄漏和共同来源不一定能自动识别。

## 验收资料的真正隔离

可信协调模块会接触完整文件以做结构校验；搜索函数不接收audit。源代码持有者仍可查看文件或重建公开合成生成器。真正独立的盲验收应由另一数据负责人持有新观测并运行独立验证环境，本版并未替你完成这种组织隔离。

# 09 / 与强模型协作的接口

本版不捆绑某家模型，不虚构GPT或其他API调用。它提供的是文件级候选接口：导出经过选择的训练和开发数据，允许你在完成数据授权审查后，手动交给外部模型。

```text
ascent proposer-request --task periodic --seed 17 --output proposer-request.json
```

模型应只返回不超过32个JSON候选，不能返回自报成绩、文件路径、命令、评估器修改或新权限。你可以修改提问文字，但不能用模型生成的自我说明代替实验。

```text
[
  {"kind":"basis", "features":["sin","x","x2"], "ridge":0.001},
  {"kind":"basis", "features":["x","x2"], "ridge":0.01}
]
```

```text
ascent run workspace --task periodic --seed 17 --candidate-file candidates.json --output model-proposal-run.json
```

候选经语法校验后，与内置算法生成的候选共同参与有限搜索。系数由可信数值程序拟合；真实损失由验收器重算。外部模型没有controller.key、停止开关、评分规则或自动激活接口。

## 该接口没有证明什么

它没有证明模型提出了新理论，没有证明模型优于没有模型的搜索，也没有证明外部提供商保密性。正式试验应保留无模型对照、等预算参考、实际调用收据、完整失败集和独立验收数据。不要在模型请求中加入私人验收标签、控制密钥或批准票据。

# 10 / 批量研究与资源预算

```text
ascent init campaign-workspace
ascent campaign campaign-workspace --tasks quadratic periodic sensor_shift scheduling --seeds 17 23 31 --output new-campaign --seconds 300 --proposals 96
```

这个命令预先声明4个任务×3个种子，写入campaign-spec.json，然后执行研究。候选上限、工作量、整批时间和源码指纹均可复查。最多32项试验，整批最多600秒，单阶段最多120秒。

| 结果文件 | 用途 |
| --- | --- |
| campaign-spec.json | 执行前的研究网格和资源限制 |
| 任务名-种子.json | 每个完成试验的完整记录 |
| campaign-progress.json | 执行中的已记录进度 |
| campaign.json | 全部已声明项，包括失败与未运行项 |

本次12项试验全部完成：8项可审阅，4项不可采用，0项执行失败，0项未运行。这个比例是公开合成任务上预先声明采用门的通过率，不是ASI成功率、真实世界泛化率或模型产品排名。

验收失败和采用失败不是同一状态。旧验收数据已经被消费、预算耗尽、用户停止或输入错误会留下失败或未运行信息。系统不会只输出最好的种子，也不会自动采用批量研究中的任何候选。

## 重跑与恢复

输出目录必须新建或为空，已有目录不会被清空。一个控制器内相同验收内容只可使用一次；失败也消耗该资格。研究数据换种子不能自动成为独立证据。进程异常中断后检查原有记录，再为新的、正当的数据设计新实验。

# 11 / 推理、漂移监测与现实接触

## 直接使用采用后的模型

```text
ascent infer workspace --task periodic --input examples/predict-periodic.json --output predictions.json
```

回归输入格式为{"rows":[{"x":−1},{"x":0}]}，可选proxy。每次最多4096行。输出记录使用的版本、模型摘要、输入摘要和输出摘要。不是复制一次实验得分，而是以固定参数计算新输入。

## 监测不是再训练

```text
ascent canary workspace --task periodic --data examples/monitor-drift.json --threshold 0.1 --output canary.json
```

监测文件按世界保存新x、y及可选proxy。本次演示对新合成观测的标签加5，最差MSE为25.012717，超过0.1，review_recommended=true。该人造漂移用来验证管道，不证明能发现全部现实漂移。

监测不会修改模型，不自动采用候选，也不自动回退。原模型继续存在，操作者决定停止、调查、回退或设计新实验。监测数据标注为USER_SUPPLIED_MONITORING_NOT_INDEPENDENT_HOLDOUT。

## 导出与携带

```text
ascent export-policy workspace --task periodic --output active-policy.json
```

导出只包括任务、参数、版本和摘要，明确authority_transferred=false。另一个实例读取模型文件，不因此取得原工作区的身份、授权、批准或验收资格。

调度推理最多128个案例、每例128个job；漂移监测因使用精确最优解而限得更紧。不要将这个小调度例程接入支付、医疗、生产控制或劳动分配并宣称经过生产验证。

# 12 / 本地控制台与API

服务只绑定127.0.0.1，不接受远端接口。页面使用每次服务器会话生成的令牌调用API，同时检查Host和Origin。所有输入为有界JSON；没有任意路径、代理请求、系统Shell或动态插件接口。

| 接口 | 用途 |
| --- | --- |
| GET /api/status、/api/jobs | 本地状态和任务进度 |
| GET /api/run?id=…、/api/model?task=… | 查看记录和当前模型 |
| POST /api/run、/api/infer | 实际实验和冻结模型推理 |
| POST /api/approve、/api/promote | 明确分开的审核与采用 |
| POST /api/stop、/api/resume、/api/rollback | 停止、恢复和回退 |

所有API需要X-ASCENT-Token；根页面对本机用户可访问。本机制主要减少意外跨站调用，不是多用户身份认证。每次只允许一个研究worker；状态读取使用一致事务，避免轮询看到不一致的账本视图。

## 浏览器验证的准确范围

真实HTTP客户端完成了本地服务、令牌、Host/Origin、任务和停止测试。受管Chromium阻止直接本地地址导航，界面测试改为把实际服务HTML放入DOM，只替换fetch封装为通向真实HTTP后端的测试桥。因此已验证界面状态及真实后端协作，但未证明直接导航与CSP在该环境中的完整行为。

桌面和390px移动布局均检查，没有水平溢出或页面错误。Windows、macOS、Safari和所有组织浏览器策略不在本次实测范围。Python官方明确指出http.server不适合生产部署。[P2]

# 13 / 验证、安全边界和保管

| 本次检查 | 结果或范围 |
| --- | --- |
| 原版回归测试 | 0.1.0原有54项测试先实际通过 |
| 升级版自动化测试 | 93项通过，0失败 |
| 独立有限控制模型 | 47状态、63转移，未发现声明属性违反 |
| 负向控制 | 忽略停止/参考、重复票据、忽略撤销均被识别 |
| 完整工作流 | 推理、漂移提示、重复票据拒绝、停止、回退通过 |
| 合成实验 | 四任务与十二项预声明campaign保留所有结果 |

有限模型不是TLC，也不是对实际代码所有并发路径的形式证明。静态扫描只覆盖指定的危险执行入口，不等于渗透测试。全部测试通过也不能证明科学正确性、价值对齐、意识或ASI。

## 必须保密的文件

```text
workspace/controller.key
workspace/registry.sqlite
```

这些文件包含本地权限与研究状态，数据库未加密。备份时保管密钥与状态的一致版本，不要把工作区提交到开源仓库。删除或替换整个工作区会破坏本地历史连续性；本系统没有外部不可回滚时间戳。

权限保护假设本机OS用户、解释器、软件源码和控制器状态可信。不防御盗取密钥的同用户进程、宿主管理员、完整历史重写或恶意更新。把候选改成原生代码，或把回环服务暴露上网，都超出本版已测试边界。

# 14 / 常见失败不是都该绕过

| 现象 | 含义与正确处理 |
| --- | --- |
| NOT_PROMOTABLE | 读blocking_reasons；强参考更好时不要强行采用 |
| No active policy | 尚未Approve/Activate，或已回退为空 |
| Operator stop is active | 先审计停止原因；需要时显式resume |
| Audit already claimed | 同一验收内容用过；不要删除库骗取新资格 |
| BudgetExceeded | 缩小任务或预先增加合法预算；保留失败 |
| Run/source mismatch | 源码改变；旧审核不能自动适用于新实现 |
| CSV/JSON validation error | 列名、字段、数字范围、世界或样本数不符 |
| 端口8765占用 | 选择另一个本地端口，如--port 8877 |
| 组织禁止回环地址 | 使用CLI或请管理员审核，不绕过安全策略 |
| 输出目录非空 | 换新目录，不能以reset删除已有研究 |

## 安全更新版本

0.2.0改变采用策略和记录格式，旧数据留作历史，不继承旧批准。新版本先在新的工作区重跑独立数据和负向测试。不要为了使报表更好看而修改默认损失、隐藏参考模型或只保留最好种子。

## 故障后恢复

停服务，保存密钥与数据库的完整备份，运行audit。完整性失败时不要继续生成票据。若需重新建库，应把它明确记录为新的控制器实例，不冒充旧历史没有中断。异常强制杀进程可能无法追加最后一条停止记录，重启前必须核查。

# 15 / 如何向更强系统推进

| 下一阶段 | 必须新增的实证 |
| --- | --- |
| 独立新数据复现 | 另一数据负责人、未公开验收、同成本强参考 |
| 模型候选生成 | 真实调用记录、无模型对照、完整失败与费用 |
| 真实限定科研 | 专业目标、授权数据、专家审阅与实际结果 |
| 代码或实验执行器 | OS级隔离、出网治理、独立监控与恢复 |
| 广域ASI评估 | 未知跨领域任务、强人类团队、资源归一和长时可靠性 |

能力、泛化、可控性、价值对齐、资源效率和现实收益分配是不同轴。不能用其中一个成绩替代其他轴，也不能从四个数值任务推导人工超级智能。NIST AI RMF可为治理、映射、测量和管理提供框架参照，不构成产品认证。[P4]

## 来源与论证边界

[F1] 用户附件《OpenAI首席科学家：我们已造出异星心智，全人类都要刹车了》，2026-09-07。本文使用其“目标对齐/价值对齐”及评估风险作为设计问题，不把标题或RSI结论当作本项目实证。

[P1] Google DeepMind, AlphaEvolve (2025-05-14). Architecture reference; no reproduction or superiority claim.
https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/

[P2] Python, http.server documentation.
https://docs.python.org/3/library/http.server.html
[P3] SQLite, Isolation.
https://www.sqlite.org/isolation.html
[P4] NIST, AI Risk Management Framework.
https://www.nist.gov/itl/ai-risk-management-framework

[R1] 本次真实计算：validation/summary.json、四项运行记录、campaign.json、browser.json及分发一致性记录。在线资料核对日为2026-09-08。项目没有调用外部模型、提交远端GitHub、获得第三方认证或取得基础模型权重。
