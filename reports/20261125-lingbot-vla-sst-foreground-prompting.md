# LingBot-VLA 2.0 / SST 前景提示配方评估：是否引入 JCHENG？

> 报告状态：**draft**（draft | reviewed | superseded）。日期：2026-11-25。
> 作者：ZCode（研究代理），for J. Cheng。评审：pending。
> 本报告影响的决策：是否、以及以何种形式，把 LingBot-VLA 2.0 / SST 的 RoboTwin 后训练配方纳入 JCHENG 技术路线。
> 研究主题：LingBot-VLA 2.0 / SST 的 RoboTwin 后训练配方（前景视觉提示、分模块学习率、数据修复）及其对 JCHENG 的可迁移性。
> 研究边界：无机器人访问；无 GPU 训练/评测（SST checkpoints 未发布）；代码审计为静态分析，pin 在 `8797aa31`；文献以公开摘要/HTML 为主，部分论文未读全文；赛事规则读到的是论坛摘要而非规则原文；统计部分是对已发布计数的桌面复算（S），不是实机或 checkpoint 复现。

**证据等级**：**S** 在本机复现（本报告仅指桌面统计复算）· **A** 一手论文/源码/官方文档 · **B** 可信二手证据 · **C** 基于现有证据的推断 · **D** 未验证假设。

---

## 01. Executive Summary（执行摘要）

**推荐：现在不引入运行时 VLA，也不把 SST 的前景掩码管线放进 JCHENG。吸收三件事——数据完整性门禁、评测协议、预训练模型的分模块学习率；如果未来真的上学习型操作策略，先做小的 3D/BC 策略（DP3/ACT 量级），不要从 6B VLA 起步。**

支撑这个结论的三条事实：

1. **头条增益是真的，但只在“只准用 clean 数据”的约束下有解释力。** SST 的 random 成功率从 36.20% 提到 58.22%，其中最大的一步（前景替换）是 +11.64 pp，z≈9.63，远超噪声 [S/A]；但同一基准上，官方用 clean+randomized 数据（randomized 池清单命名为 `_500-1000`，至少 500 条/任务）训练得到 **92.80%** random [A]，而 SST 只被允许用 2,500 条 clean 演示 [A/B]。这不是“SST 方法不如官方”，而是**两条不同约束下的曲线**：一条是把 clean-only 的泛化缺口补上一部分，另一条是用数据直接覆盖这个缺口。对不受赛事规则约束的 JCHENG，后者的性价比高得多 [C：这是基于成本结构的推断，不是 JCHENG 实测]。
2. **中间阶段的 +2–3 pp 大多没有统计显著性。** 用 SST 自己发布的 success/total 复算：N2→N3（raw teacher）p=0.107，N3→N4（module LR）p=0.112；只有 N0→N1 和 30k 等步数的数据修复（+3.98 pp，p=0.001）站得住 [S]。报告的叙事“每一阶段加几个点”比数据本身更强。
3. **方法不是“Qwen 自动提词 + SAM3 分割”的通用配方。** 实际交付物是一份 **73 行手工词表**：按 RoboTwin-OD 的物体类别（147 类中的任务相关子集）逐类写短语、颜色备份和 `MISSED` 词规避；评测时还要常驻 SAM3 服务 + Qwen3.8-27B judge [A]。换一套物体/相机/指令，这份词表要重做，失败模式也要重新标定 [A：词表内容；C：迁移判断]。

**主要风险**：把 27B Qwen + SAM3 放进感知到运动的链路，会把一个“检测/分割错误”变成策略输入的分布外扰动；ArmPi 是 5-DoF、无编码器、无 e-stop、`/joint_states` 只是命令缓存，连可靠的动作标签都还没有。现在引入 VLA，风险不在模型大小，而在**数据、标签和安全边界**。

**一句话**：这是一份质量高于平均水平的**受限赛道工程报告**，值得学它的数据治理和评测纪律；它不是可以直接搬进产品的方案。

---

## 02. Research Questions（研究问题）

**主问题**：JCHENG 是否应该、以及以什么形式，采用 LingBot-VLA 2.0 / SST 的 RoboTwin 后训练配方？

拆成可回答的子问题：

| # | 子问题 | 本报告的回答位置 |
|---|---|---|
| Q1 | SST 到底改了什么？哪些改动是因果、哪些只是相关？ | §05、§06、§08 |
| Q2 | 这套配方能否在 RoboTwin 之外复现/泛化？ | §05、§08、§12 |
| Q3 | 有哪些替代路线（更多数据、3D 策略、分割骨干、经典位姿）？ | §05.6、§07 |
| Q4 | 哪些部分与 JCHENG 的架构、硬件、安全边界兼容？成本多少？ | §03、§09 |
| Q5 | 若未来上学习策略，最小可行实验是什么？验收/失败判据？ | §11、[design.md](../experiments/20261125-lingbot-sst-reanalysis/design.md) |
| Q6 | 哪些结论仍缺证据？缺什么才能关闭？ | §12 |

**约束条件**：

| 类别 | 约束 |
|---|---|
| 硬件 | ArmPi Ultra：Pi 5 8 GB + 5-DoF 总线舵机臂 + 夹爪；D435i；LSLIDAR M10 未接入；操作笔记本 RTX 3060（显存未在工作区记录） |
| 软件 | 机器人侧 ROS 2 **Humble**（厂商栈）；本机仅 Jazzy；Python 3.12；无 `gh` CLI |
| 安全 | 运动只能经 `jcheng_motion.ExecuteMotion`；lease/deadman/limits/stop latch；无 e-stop、无抱闸、无编码器、无自碰撞模型；每次实机运动需单独授权 |
| 数据 | 无演示数据集；无可靠动作标签（`/joint_states` 是命令缓存）；感知只给 advisory target |
| 算力 | 无 6B 级训练/推理资源；SST 训练用 16–32×H200，评测 8 GPU × 4 slot |
| 法务 | SST 自有代码**无根 LICENSE**；上游 LingBot-VLA 2.0 为 Apache-2.0；RoboTwin/SAM3 各自保留许可证 |
| 时间 | 本次调研为桌面研究；未申请 GPU/机器人时段 |

**交付物**：本报告 + 来源记录（`references/`）+ 可复算的统计实验（`experiments/20261125-lingbot-sst-reanalysis/`）+ 未来实验设计（未执行）。

---

## 03. Current System Analysis（当前系统分析）

### 3.1 生态现状（按仓库）

| 仓库 | 层 | 当前实际能力 | 与 VLA 的关系 |
|---|---|---|---|
| `jcheng-system` | L2 | 安全状态机、lease、arbiter、硬件桥、网关、只读遥测、MoveIt plan-only；**唯一运动入口 `ExecuteMotion`** | VLA 只能作为 L4 意图源，不能绕过 lease/stop latch |
| `jcheng-perception` | L3 | Pi 5 边缘采集、深度/TF 时间戳环、反投影、双视角融合、Kalman；笔记本 YOLO；**advisory targets only** | 没有“把策略输出变成运动”的闭环；跨视角标定仍有残差 |
| `jcheng-mobile` | L3 | ICP 激光里程计、SLAM、Nav2、`/cmd_vel` 意图；无驱动、无设备 | 与机械臂操作正交 |
| `jcheng-ops` | OPS | HTTP 健康探针、看门狗、systemd 自愈；不加入 DDS | 与 VLA 无关 |
| `jcheng-manipulation` | L3 frozen | v1.0.0 基线、ArmPi Debug Studio、证据归档；冻结 | 参考基线，不可改写其证据 |

### 3.2 与本次决策直接相关的五个事实

1. **没有学习型操作策略，也没有演示数据集。** 现有操作路径是经典感知 + MoveIt plan-only + 系统层执行；没有任何策略网络被训练或部署 [A: 工作区 `AGENTS.md`]。
2. **动作标签不可靠。** 厂商 `/joint_states` 是**命令缓存**，不是测量；完成与位姿真值来自总线读 `GetBusServoState`，而总线读没有安全超时 [A: 工作区 `AGENTS.md` §7]。这意味着：即使现在开始采演示，动作标签的质量也是未解问题。
3. **5-DoF、无编码器、无 e-stop、无抱闸。** 平台没有力/位真值闭环，软件 stop 不是 e-stop [A: 工作区 `AGENTS.md` §7]。任何“预测 50 步、开环执行”的策略都缺少底层保护。
4. **算力不匹配。** 6B 参数仅 FP16 权重就约 12 GB，3060 级笔记本无法加载；SST 的评测还要 27B mask-Qwen + SAM3 + 策略服务，其评测记录是 8 GPU × 4 slot [A: SST `base.json` 与 evidence 头；C: 12 GB 是算术]。
5. **没有 VLA 的“插槽”。** 现有 L4 是空的；引入 VLA 不是“接一个节点”，而是新开一条策略训练、数据采集、评测、部署的路线 [C]。

**结论**：JCHENG 当前的问题不是“用哪个 VLA”，而是“要不要开始一条学习型操作策略路线”。在这个问题回答之前，SST 配方的可迁移部分只剩工程实践，而不是模型。

---

## 04. Research Methodology（研究方法）

### 4.1 检索策略

关键词组合（中英并用）：`LingBot-VLA 2.0`、`Robbyant`、`RoboTwin 2.0`、`demo_clean`、`demo_randomized`、`SAM 3 promptable concept segmentation`、`VLA robustness`、`LIBERO-Plus`、`real-time chunking`、`SAM2Act`、`3D diffusion policy`、`layer-wise learning rate decay`、`LLM-as-a-judge bias`、`LeRobot v3.0 frame alignment`、`Robbyant 具身智能挑战赛 规则`。

检索顺序：先读 SST 报告与源码 → 追到 LingBot-VLA 2.0 官方仓库/论文 → 追到 RoboTwin 2.0 基准与规则 → 用 SAM3、LIBERO-Plus、RTC、SAM2Act、DP3、ULMFiT、judge-bias、LeRobot issues 做反例与替代路线。

### 4.2 来源与阅读深度

| 来源 | 版本/日期 | 实际读到什么 | 等级 |
|---|---|---|---|
| SST 报告页 | 访问 2026-11-25 | 发布版全文（HTML），含 per-task 交互数据 | A（作者主张） |
| SST 代码 | commit `8797aa31` | README、配置、入口脚本、核心源码、测试、`base.json`；**未执行** | A（静态） |
| SST 数据 | HF revision `7111c72` | 数据集卡片、文件清单、`validation_summary.json`；未下载 8.33 GiB | A（元数据） |
| LingBot-VLA 2.0 论文 | arXiv 2607.06403 | 摘要 + HTML 正文；正文不含 RoboTwin 数字 | A（部分） |
| LingBot-VLA 2.0 仓库 | `main`，访问 2026-11-25 | README、`robotwin.yaml`、`robotwin.txt` 数据清单 | A |
| RoboTwin 2.0 | arXiv 2506.18088 | 摘要 + HTML 正文（协议/局限）+ 项目页；**未读全文 PDF** | A（协议/局限） |
| SAM 3 | arXiv 2511.16719 | HTML 正文，含 Limitations 与延迟数据 | A |
| LIBERO-Plus | arXiv 2510.13626 | 摘要/检索摘要 | B |
| RTC | arXiv 2506.07339 | 摘要/检索摘要 | B |
| SAM2Act | arXiv 2501.18564 | 摘要/检索摘要 | B |
| DP3 | arXiv 2403.03954 | 摘要 | B |
| π0 | arXiv 2410.24164 | 摘要 | B |
| ULMFiT | arXiv 1801.06146 | PDF 相关章节（`pdftotext` 抽取） | A（该节） |
| LLM judge bias | 2305.17926 / 2306.05685 | 摘要/检索摘要 | B |
| LeRobot issues | #5039/#5187/#5051 | 检索摘要；未逐条打开 | B |
| 赛事规则 | 天池论坛 post 1081761 | 页面正文不可取（JS），仅有检索摘要 | B/C |

### 4.3 纳入/排除标准

- **纳入**：一手论文、官方仓库、官方数据卡、issue tracker、可复算的公开计数。
- **排除**：博客/营销/二手总结作为关键结论的唯一来源；SST `page` 分支的 `blog.md` 草稿（与发布页数字不一致，明确不作为数字来源）；未发布的 checkpoint 相关推测。
- **统计方法**：Wilson 95% CI；两比例 z 检验（不配对，忽略 task 聚类，因此 p 值是**乐观上界**）；逐任务描述统计。没有做 McNemar，因为没有 per-episode/seed 级配对数据。
- **停止条件**：核心问题有答案；主要替代路线已比较；关键结论有可追溯来源；继续检索的边际收益下降（新增来源不再改变结论）。

---

## 05. Literature Review（文献综述）

### 5.1 LingBot-VLA 2.0：架构与官方 RoboTwin 协议

**问题**：把 VLA 从实验室推到多本体、长时序、真实部署。**架构**：Qwen3-VL-4B 主干 + 稀疏 MoE 动作专家（流匹配）+ 双查询蒸馏（LingBot-Depth 几何、DINO-Video 时序）；55 维统一动作空间；约 60,000 小时预训练数据（50,000 小时机器人 / 20 本体 + 10,000 小时人类视频）[A: 论文摘要/HTML；README]。

**官方 RoboTwin 后训练**：README 原文 "trained with clean and randomized data together"；数据清单每个任务一条 `*_randomized_500-1000` 加一条 `*_clean_50-50`，即 **500–1,000 条 randomized + 50 条 clean 演示/任务**（至少 10× clean）；Muon 结果为 **93.52 clean / 92.80 randomized** [A: 官方 README 与数据清单]。评测用 **FP32**；README 明确警告 BF16 可能"materially different" [A]。

**局限（作者自述）**：任务间 progress/success 差距大；本体差异（运动学、相机视角、动作空间对齐）仍难；OOD 退化 [A: 论文 HTML]。

**对 SST 的含义**：SST 的 77.1/36.2 基线和 81.9/58.2 终版，是**clean-only** 约束下的另一条曲线。把 58.2 与 92.8 直接比是错的；但把 92.8 当作“如果有数据，天花板在哪里”的参照是合理的 [C]。

**SST 的主线（clean-only；括号内为发布计数）**：

| 阶段 | 改动 | Clean | Random |
|---|---|---:|---:|
| N0 15k | absolute joint 基线 | 77.14 (3857/5000) | 36.20 (1810/5000) |
| N1 15k | Qwen+SAM3 前景替换 | 78.04 (1951/2500) | 47.84 (1196/2500) |
| N2 15k | 掩码复核 + 背景×0.1 + 2px 白边 | 75.96 (1899/2500) | 50.84 (1271/2500) |
| N3 15k | 教师读原图 + 前景加权 | 76.52 (1913/2500) | 53.12 (1328/2500) |
| N4 15k | 分模块学习率 | 78.20 (1955/2500) | 55.36 (1384/2500) |
| N5 30k | padding mask + 帧对齐修复（并训练到 30k） | 81.86 (4093/5000) | 58.22 (2911/5000) |

注：N0/N5 为 100 episodes/task，N1–N4 为 50；不要跨行直接比较置信区间。

### 5.2 RoboTwin 2.0：基准与强域随机化

50 个双臂任务、5 种本体、SAPIEN；RoboTwin-OD 731 实例/147 类；5 条域随机化轴（杂物、光照、背景、桌面高度、语言指令）；>100,000 条随机化专家轨迹；评测 100 rollouts/task（Easy/Hard），训练 50 条 clean 演示/任务；论文报告 RDT/Pi0 从 clean 到 randomized 下降 20.8/30.1 个百分点 [A: 论文 HTML]。

**对 SST 的含义**：`demo_randomized` 是**为外观鲁棒性专门设计的强偏移**，对象集封闭、指令来自 seen pool。SST 的 +22 pp random 提升是在这个封闭分布内测的；它不能证明真实相机/新物体/新指令下的鲁棒性 [C]。

### 5.3 SAM 3：能力与边界

PCS 支持名词短语/图像 exemplar，返回所有匹配实例的 mask + identity；图像 30 ms/H200（100+ 物体），视频跟踪成本随物体数线性增长，约 5 个物体近实时，64 个物体 30 FPS 需 8×H200；15 帧确认延迟约 0.5 s [A: 论文 HTML]。

**作者自述局限**：只支持简单名词短语；细粒度 OOD 概念（航空器型号、医学、热成像）弱；歧义（多义、主观描述、不可落地短语、遮挡/模糊）；跟踪漂移（mask 传播、误检、拥挤场景 IoU 匹配）；无共享物体级上下文 [A]。

**对 SST 的含义**：SST 的 73 行词表正是在补 SAM3 的词表缺口（hammer、pad、mat、skillet、bin、rack、stamp、seal、switch、scanner、sign 等被标为 `MISSED`）。这说明“提词”不是一行 prompt，而是**按物体类别的工程**；换物体集要重做 [A]。

### 5.4 LIBERO-Plus：VLA 的脆弱性

10,030 个任务、7 个扰动维度（布局、视角、初始状态、指令、光照、背景、传感器噪声）；报告 >95% 的模型在温和扰动下跌到 <30%；视角与初始状态最敏感；模型大量忽略语言；存在轨迹记忆 [B]。

**对 SST 的含义**：外观偏移确实是真问题，值得做输入侧干预；但也提醒：benchmark 高分可能脆弱，SST 的 58.2 不能外推为“真实场景 58%” [C]。另一个可检验的假设是：SST 的增益可能来自**把指令条件注入像素**，而不是“前景”本身（见 §08 F3、§11 MVE-1）。

### 5.5 动作块执行：RTC

把实时执行建模为 inpainting：冻结将在推理期间执行的 prefix，inpaint 其余；soft masking；异步执行；**无需重训** [B: 摘要]。

**对 SST 的含义**：SST 的“每个任务有最佳执行长度，但只能选一个全局值（50）”是静态折中。RTC 是标准替代，能在不重训的情况下处理延迟与块边界；SST 没有测它，尽管赛事允许推理策略 [B/C]。

### 5.6 替代路线

| 路线 | 关键证据 | 对 JCHENG 的含义 |
|---|---|---|
| 更多/更杂的数据（clean+randomized、DR） | 官方 93.52/92.80（500–1,000 random/task）[A]；Tobin et al. 域随机化 [B] | 若能采/生成数据，这是主导杠杆；比测试时掩码简单 |
| 3D/点云策略（DP3） | 10 条演示可学多数任务；40 条真实演示 85%；跨视角/外观/实例泛化 [B]；但 RoboTwin 论文指出其强结果部分来自仿真完美点云/干净背景分割 [A] | 与 D435i 匹配；比 6B VLA 现实；真实点云噪声/缺失会打折；仍需演示与动作标签 |
| 分割骨干策略（SAM2Act） | SAM2 encoder + memory；RLBench 86.8%；扰动下 4.3% 差距 [B] | 把分割放在训练期表征，而不是测试期预处理；无 27B judge |
| 经典位姿 + MoveIt | 现有 JCHENG 路径 [A/S] | 已知物体、受控场景下最稳；不需要学习 |
| 光度增强 | DR 文献正面 [B]；SST 腕部颜色增强负面 [A] | 范围依赖；SST 的负面结果只覆盖腕部颜色，不是对 DR 的反驳 |
| 深度第四视角 | SST 负面（48.2 random）[A]；DP3 用点云正面 [B] | SST 否的是“伪彩色深度图 + 独立 connector”，不是深度/点云本身 |

### 5.7 微调策略与 judge 偏差

- **ULMFiT**：不同层用不同学习率（discriminative fine-tuning），目的是保留预训练知识、避免灾难性遗忘 [A: PDF §3.2]。SST 的 `module_lr_mult`（ViT 0.3×、merger/LLM 0.5×、embed 冻结、action/align 1.0×）是同一思路的粗粒度版本 [A: 代码]。
- **LLM-as-a-judge**：位置偏差可翻转排名；还有 verbosity/self-enhancement 偏差 [B: 2305.17926, 2306.05685]。SST 的 judge 不是 pairwise，位置偏差不直接适用；但它是**单次 yes/no、阈值 0.5、无人工校准集、无错误率报告**，而且只能否决 SAM3 提出的对象，不能补回漏掉的对象 [A/C]。

---

## 06. Repository Investigation（仓库调查）

### 6.1 交付物

| 部分 | 内容 | 质量判断 |
|---|---|---|
| `Lingbot-vla-challenge/` | 上游训练框架 + SST patch（3 份配方 yaml、module LR、raw teacher、padding mask、多机 launcher） | 代码结构与上游一致，patch 有注释和测试 |
| `auto_mask/` | Qwen 提词 → SAM3 跟踪 → Qwen judge → 渲染（`pipeline_lerobot.py` 62 KB） | 工程完整；强依赖服务与 GPU |
| `inference/` | 评测期在线掩码 + 策略包装 | 与训练样式对齐；有 fallback 默认值 |
| `data_inputs/` | 2,500 episode 映射、原始 instruction、`preparation_report.json`（1.4 MB） | 溯源非常完整 |
| `RoboTwin/`、`sam3/` | 上游全量 vendored | 各自保留许可证 |
| `tools/` | 数据重建、修复、校验、服务、配置 | 校验逻辑扎实；路径绑定本机 |

### 6.2 调用链

```text
process_data.sh --stage raw      -> tools/rebuild_robotwin_v30_from_v21.py
process_data.sh --stage masks    -> auto_mask/pipeline_lerobot.py
                                    -> Qwen 提词（vLLM）
                                    -> SAM3 服务（跟踪）
                                    -> Qwen judge（yes/no logprob）
                                    -> mask_style.py（dim / outline）
process_data.sh --stage assemble -> 成对 raw + SAM 数据集
train.sh                         -> Lingbot-vla-challenge/train_multinode.sh
                                    -> tasks/vla/train_lingbotvla.py + 配方 yaml
eval.sh                          -> script_sam.sh
                                    -> inference/cam_high_masker.py（在线掩码）
                                    -> 策略服务 + RoboTwin 环境
```

### 6.3 关键实现（文件 + 符号 + 行号，commit `8797aa31`）

| 机制 | 位置 | 审查意见 |
|---|---|---|
| Padding 不计入 loss 的分子/分母 | `Lingbot-vla-challenge/lingbotvla/models/vla/lingbot_vla/action_loss.py:6-45` | 正确；fp16/bf16 下用 fp32 累加；只掩监督，不改 transformer 输入 |
| `mask_action_pad` 开关 | `.../modeling_lingbot_vla_v2.py:1297` | 与配置一致 |
| 分模块 LR | `.../optim/module_lr.py:29-125` | 7 个模块；未知 key 报错；0 直接冻结；有单测 |
| 教师读原图 | `.../data/vla_data/base_dataset.py:101-131`；`.../data/dataset.py:94` | 从 `sam_info.json["source"]` 取原图；episode 数不一致会在启动时报错 |
| 评测样式回读 | `tools/evaluation_config.py:41-44` | 从 checkpoint 的 `sam_info.json` 读 `outside_scale/edge_width`，train/eval 一致 |
| 提词词表 | `vllm_space/sam3_prompt.py`（73 行） | 逐类短语 + 颜色备份 + `MISSED` 规避；不是通用提词 |
| Judge | `sam3/tools/sam3_mask_judge.py:37-45,109`；`auto_mask/pipeline_lerobot.py:1174,1194` | 两图 + 任务 + 短语的 yes/no；logprob 比值；阈值 0.5；`regrow` 复判 |
| 数据修复 | `tools/rebuild_robotwin_v30_from_v21.py:119,145-155,326` | PTS 严格等于 `i/fps`；SHA-256/内容哈希；写 `repair_report.json` |
| 数据溯源 | `data_inputs/preparation_report.json` | 2,500 episodes / 548,893 frames / 250,000 slots；状态动作 float32 字节级一致 |

### 6.4 数据修复：本仓库最可迁移的部分

SST 发现两个问题：（1）episode 末尾不足 50 步时，复制最后动作填满 chunk，原实现把这些 padding 也算进 loss，导致 click 类任务学不会“完成”；（2）官方 RoboTwin LeRobot v3.0 的部分 episode 末尾帧会读到下一个 episode 的帧 [A: 报告 + 代码]。修复方式是：padding 从 loss 分子和分母同时剔除；用 v2.1 的视频重建 v3.0 的帧序列，同时保留 v3.0 的 episode ID 与状态/动作数值 [A]。

**外部佐证**：LeRobot issue #5039（28/31 个视频缺最后一个 episode，`from_timestamp` 超出视频末尾）、#5187（12 个数据集同类问题，根因指向 converter commit `59d108a80`）、#5051（加载时检查）[B]。这说明 SST 说的不是孤例，而是 LeRobot v3.0 的一类真实缺陷。

### 6.5 测试、CI、许可证、维护

- **测试**：`Lingbot-vla-challenge/tests/` 10 个文件、根 `tests/` 3 个、`auto_mask/` 3 个；以 CPU 数据完整性/单元测试为主，没有 GPU 端到端、没有实机 [A]。
- **CI**：无 `.github` 目录，无 CI [A]。
- **许可证**：根目录**没有 LICENSE**，GitHub API `license: null`；`Lingbot-vla-challenge/` 是 Apache-2.0，`RoboTwin/`、`sam3/` 各自保留 [A]。**SST 自有的 `auto_mask/`、`tools/`、`inference/` 没有授权**，不能直接复制进 JCHENG。
- **Checkpoints**：未发布（README badge "Coming soon"）[A]。因此无法复现 81.86/58.22，也无法做配对重评。
- **可移植性**：`base.json` 里有 `/home/pc/miniconda3/...`、`/usr/local/cuda-13.0`、`/data1/szh/...` 等本机路径；4 套 conda 环境；vLLM 需从源码编译（v0.20.2，`bc150f5`）；模型+输入约 103 GB [A]。
- **文档漂移**：`page` 分支 `blog.md` 是过期草稿（§7 重复、数字与发布页不一致）；以 `index.html` + `data/results.csv` 为准 [A]。

### 6.6 静态分析 vs 执行

本报告**没有运行 SST 的任何代码**，没有下载权重，没有 GPU。所有代码结论都是静态阅读；唯一的计算是对其公开计数的统计复算（`experiments/20261125-lingbot-sst-reanalysis/`）。

---

## 07. Comparative Analysis（横向比较）

比较对象：在“外观偏移下让操作策略更稳”这个问题上，JCHENG 可选的路线。

| 路线 | 证据强度 | 数据/算力成本 | 与 JCHENG 的适配 | 主要风险 |
|---|---|---|---|---|
| SST：clean-only + 前景掩码 + 6B VLA | RoboTwin 上 A；真实迁移 C | 2,500 demos；16–32×H200 训练；评测 8 GPU × 4 slot + mask-Qwen/SAM3 服务 | 低：无数据、无算力、无 VLA 插槽 | 测试时检测/分割错误；词表需重做；judge 未校准 |
| 官方 clean+randomized | RoboTwin 上 A（92.80） | 500–1,000 random demos/task；训练算力未核实（SST 报告用 16–32×H200） | 低：数据成本更高 | 赛事不允许；真实世界仍需采集 |
| 小 3D/BC 策略（DP3/ACT） | B（DP3：10–40 demos） | 1 张消费级 GPU；几十条 demos | 中：D435i 有深度；需动作标签 | 5-DoF/无编码器；标签质量 |
| 分割骨干（SAM2Act） | B（RLBench 86.8%） | 多 GPU 训练；无测试时 judge | 低–中：研究路线 | 仍需演示与训练基础设施 |
| 经典位姿 + MoveIt | 现有系统 S | 无学习成本 | 高：已在用 | 只适合已知物体/受控场景 |
| 光度增强/DR | B（DR 文献）；SST 腕部负面 A | 低 | 中：可作为数据侧的廉价补充 | 范围依赖；SST 的负面结果不覆盖全部 |
| 深度第四视角 | SST 负面 A；DP3 正面 B | 中 | 中 | SST 否的是特定编码方式，不是深度本身 |

**可比性**：

- SST 的 N0→N5 是同一基准、同一评测器、同一数据约束下的**内部比较**，可比；但 50 vs 100 episodes/task 混用，且没有 per-episode 配对。
- SST 58.22 vs 官方 92.80 **不可比**：训练数据不同（clean-only vs clean+randomized），且后者用 500–1,000 random/task。
- SST 的 50 步执行长度 vs RTC 的异步执行**不可比**：前者是静态配置，后者是推理算法；SST 没有测 RTC。

**矛盾证据**：

- SST 的腕部颜色增强负面 vs DR 文献的正面：不矛盾，范围不同（腕部颜色 vs 渲染/外观全轴；单一数据集 vs 多任务）。
- SST 的深度第四视角负面 vs DP3 的点云正面：不矛盾，表示不同（伪彩色图 + 独立 connector vs 点云 + 点编码器）。
- SST 的 judge 看起来比朴素 yes/no 更严谨（两图、任务、短语、regrow），但**没有校准集/错误率**；这与 LLM judge 偏差文献的警告并不冲突，只是没有被量化。

**更简单的替代**：如果目标是“减少外观偏移”，在数据侧加多样性（DR/更多演示）比在测试时加一个 27B judge 更简单、更可维护；如果目标是“让策略看见任务物体”，3D/点云表示比 2D 掩码更直接地去掉外观。SST 的路线是在**不能加数据**的约束下的最优折中之一，不是无约束下的最优。

---

## 08. Critical Findings（关键发现）

### F1. 头条增益稳健，但适用范围窄 [S/A]

前景替换（N0→N1）random +11.64 pp，z≈9.63，p<1e-4；这是前景/蒸馏/优化这几个阶段中唯一一个在 50 episodes/task 的噪声水平上仍然稳固的增益。数据修复的 +3.98 pp 在 30k 等步数下也显著（p=0.001），但那是另一类改动。它证明“输入侧干预”在 RoboTwin 的 clean→randomized 偏移下有效，不证明真实相机/新物体下有效。

### F2. 中间阶段大多不显著 [S]

| 比较 | Δ random | p（不配对，乐观） | 判断 |
|---|---:|---:|---|
| N0→N1 前景替换 | +11.64 pp | <0.0001 | 成立 |
| N1→N2 复核 + 0.1 渲染 | +3.00 pp | 0.034 | 边缘 |
| N2→N3 raw teacher + 前景加权 | +2.28 pp | 0.107 | 未成立 |
| N3→N4 分模块 LR | +2.24 pp | 0.112 | 未成立 |
| N4@30k→N5 数据修复 | +3.98 pp | 0.001 | 成立 |

N3→N4 在 25k 复现了同样的 +2.24 pp（53.00→55.24，p≈0.11）；两个 checkpoint 同方向同幅度是**提示性**证据（若独立，Stouffer Z≈2.25，p≈0.02），但不是配对检验。报告把“分模块 LR”写成确定收益，证据强度不够。

### F3. Clean 的提升集中在两个 click 任务 [S]

N0→N5 clean：均值 +4.72 pp，但中位数只有 +1.0 pp；29 个任务变好、16 个变差、5 个不变。`click_bell` 5→98、`click_alarmclock` 34→96，两个任务贡献了 236 个新增成功中的 **155 个（66%）**。这恰好验证了 padding/frame 修复的机制，但也说明：**clean 81.86 不是全面变好，而是修好了一个特定病理**。Random 的提升是广谱的（46/50 变好，中位数 +19 pp），两者机制不同。

### F4. 方法的核心资产是词表，不是模型 [A]

`vllm_space/sam3_prompt.py` 73 行，逐类写短语、颜色备份、`MISSED` 词规避，并明确要求输出 `robot, robot arm`。这意味着：

- 换物体集/相机/指令分布，词表要重做；
- SAM3 的词表缺口（hammer、pad、mat、skillet、bin、rack、stamp、seal、switch、scanner、sign…）是方法的一部分；
- 报告里“Qwen 根据指令识别物体”的叙述，弱化了这份手工工程。

### F5. 测试时依赖与 judge 未校准 [A/C]

评测时 SAM3 逐帧跟踪，Qwen judge 逐对象判断（首次出现 + regrow 复判，27B），样式从 checkpoint 的 `sam_info.json` 回读。Judge 的设计比朴素 yes/no 好（两图、任务、短语、regrow 复判），但：

- 单次判断、阈值 0.5、无人工校准集、无错误率；
- 只能否决候选，不能补回 SAM3 漏掉的对象；
- 掩码错误会直接进入策略输入，没有 fallback/置信度门控。

SST 没有量化“掩码错时策略会怎样”，这是最大的未测风险。

### F6. 有一个缺失的关键消融：指令条件 vs 前景本身 [C/D]

`single`（每 episode 一个 mask，配一条指令）→ `multi`（每 episode 100 个 mask，配 100 条指令）带来 +2.7 pp。这既可能是“更多 mask 数据增强”，也可能是“掩码把指令条件注入了像素”。SST 没有做“同一 mask 配不同指令”或“随机物体 mask”的对照。如果增益在指令无关的 mask 下仍然存在，那它就不是“指令 grounding”，而是外观增强；这会改变方法的解释和迁移方式。

### F7. 官方 c+r 是一个被规则挡住的更强基线 [A/B]

官方 93.52/92.80 用 500–1,000 random demos/task（清单命名 `_500-1000`）；赛事规则禁止 randomized 训练 [B]。所以 SST 不测 c+r 是合规的，不是疏忽。但对 JCHENG（不受该规则约束），**在投入前景掩码工程之前，先问“能不能采/生成更多样的数据”**；如果能，c+r/DR 的预期收益远高于掩码。

### F8. 真实机器人证据缺失 [A]

仓库里的全部实验都是 RoboTwin 仿真；决赛的真机方案不在仓库里。报告页面的“grand finals”叙述与仿真实验是两件事。任何“真实场景有效”的推断都是 C/D。

### F9. 复现性与法务 [A]

- Checkpoints 未发布 → 无法复现 81.86/58.22，无法做配对重评。
- `base.json` 绑本机路径、4 套环境、vLLM 源码编译、103 GB 下载 → 复现成本高。
- 根目录无 LICENSE → SST 自有代码不能直接复用；上游 LingBot-VLA 是 Apache-2.0，可用。
- 无 CI；测试以 CPU 数据完整性为主。

### F10. 数据修复是可信且可迁移的 [A/B]

LeRobot v3.0 的帧错位有独立 issue 佐证；SST 的修复保留 v3.0 ID 和 float32 状态/动作字节，写了 `repair_report.json`。这是本仓库最值得学的一块：**先验证数据，再谈模型**。

### 什么会改变结论

1. SST 发布 checkpoints，并在相同 seeds 下做 100 episodes/task 的配对重评（McNemar），证明 N2–N4 的 +2–3 pp 真实；
2. 有真实机器人上的前景掩码迁移实验（不是仿真）；
3. JCHENG 决定启动学习型操作策略路线，并解决动作标签问题；
4. 官方/社区给出 clean-only 约束下的更强方法（例如 RTC + 更好的数据增强），使掩码工程的边际收益下降。

---

## 09. Engineering Applicability（工程适配）

### 9.1 适配矩阵

| 维度 | 评估 | 依据 |
|---|---|---|
| 架构兼容 | **低**：没有 L4 策略插槽；VLA 只能作为意图源经 `ExecuteMotion` | [A] 工作区 `AGENTS.md` |
| 数据 | **无**：没有演示集；动作标签不可靠（`/joint_states` 命令缓存；总线读无安全超时） | [A] |
| 算力 | **不匹配**：6B FP16 ≈12 GB 权重；27B judge + SAM3 服务无法在 3060/Pi 上常驻；整体评测 8 GPU × 4 slot | [A/C] |
| 安全 | **高风险**：5-DoF、无编码器、无 e-stop/抱闸；50 步开环 chunk 降低反应性 | [A] |
| 维护 | **高**：4 套环境、vendor fork、词表、judge、在线服务 | [A] |
| 预期收益（当前路线） | **无**：M6/M7 是移动/系统里程碑，不是操作策略 | [A] |
| 回退 | 现在不引入，无需回退；若未来引入，保留经典路径为 fallback | [C] |

### 9.2 算力算术（为什么不是“优化一下就能跑”）

- 6B 参数 × 2 bytes（FP16）≈ 12 GB，仅权重；加上激活、KV cache、视觉编码器，单卡需求更高。3060 级笔记本（显存未记录，通常 6–8 GB 级）连权重都放不下 [C]。
- SST 的评测记录是 8 GPU × 4 个常驻推理 slot；还叠加单卡 27B mask-Qwen 服务与 SAM3 服务（数据生成阶段的 Qwen 服务用 4 卡张量并行）[A]。
- SST 的训练是 16–32×H200，global batch 1024，micro 32 [A]。这不是“租一张 4090 周末跑跑”的量级。

### 9.3 数据与标签（最容易被忽略的成本）

SST 的动作标签来自仿真器的绝对关节目标；JCHENG 的 `/joint_states` 是命令缓存，真值要靠总线读，而总线读没有安全超时 [A]。在采演示之前，必须先解决：

1. 动作标签的时间对齐（命令 vs 总线读 vs 相机帧）；
2. episode 边界与 padding 的定义；
3. 失败演示的标注（成功/失败/中断）；
4. 5-DoF 动作空间与夹爪的归一化。

没有这四样，任何 BC/VLA 训练都是在噪声标签上拟合。

### 9.4 现在就可以采纳的三件事

| 实践 | 成本 | 证据 | 风险 |
|---|---|---|---|
| 数据完整性门禁（帧数=行数、PTS 单调、首尾帧解码、padding mask） | 1–2 人日，CPU | A（SST 修复 + LeRobot issues） | 低 |
| 评测协议（固定 seeds、≥100 trials、原始计数、CI、配对检验、预注册） | 流程成本 | A/B（RoboTwin 协议 + 统计常识） | 低 |
| 预训练模型的分模块/分层 LR（冻结 backbone、低 LR 早期层、高 LR 头） | 低 | A（ULMFiT；SST 消融但统计弱） | 低 |

---

## 10. Recommended Approach（推荐方案）

### 推荐（现在）

**不引入 VLA / 前景掩码运行时；保持经典操作路径。** 采纳 §9.4 的三项工程实践，尤其是数据完整性门禁和评测协议。它们不依赖 GPU，不改变安全边界，直接提升未来任何学习型路线的可信度。

### 替代（如果决定上学习型策略）

**先小后大**：用 D435i 深度 + 1–2 个固定任务 + 40–100 条演示，训练 DP3/ACT 量级的小策略（DP3 的点云优势在真实深度上会打折，先在受控台面验证）；在仿真或受控台面上做 100 trials/任务的配对评测。只有当小策略饱和、且数据规模确实成为瓶颈时，才考虑 VLA。若一定要用 VLA，优先用上游 Apache-2.0 的 LingBot-VLA 2.0，而不是 SST 的未授权 patch。

### 不推荐

| 选项 | 理由 |
|---|---|
| 在 ArmPi 上部署 SST 管线 | 算力不匹配；27B+SAM3 测试时依赖；5-DoF/无编码器/无 e-stop；无数据 |
| 把 SAM 掩码放进安全/运动链 | 掩码错误会变成运动输入；安全层不能依赖学习组件 |
| 直接复制 SST 自有代码 | 根目录无 LICENSE；只能用上游 Apache-2.0 |
| 用 RoboTwin 数据训练真实 ArmPi 任务 | 本体/动作空间/相机/任务全不匹配；sim-to-real 无证据 |
| 以“58.2 vs 92.8”评判 SST | 约束不同，不可比；正确比较是 SST vs 它自己的 clean-only 基线 |

### 重新开启 VLA 问题的触发条件

1. JCHENG 路线图正式加入“学习型操作策略”里程碑；
2. 有 ≥1 个任务的 100+ 条高质量演示，动作标签经总线真值校验；
3. 有 ≥1 张 24 GB 级 GPU 或可租用多卡；
4. 小策略（DP3/ACT）在该任务上达到平台期；
5. 安全层完成“策略输出 → 限幅/停止”的失效分析。

---

## 11. Experimental Design（实验设计）

完整设计见 [design.md](../experiments/20261125-lingbot-sst-reanalysis/design.md)。这里给出结论级摘要。

### MVE-0 — 已执行（桌面复算，不是机器人实验）

- **假设**：50 episodes/task 下，SST 中间阶段的 +2–3 pp 在噪声内。
- **方法**：Wilson CI + 两比例 z 检验 + 逐任务描述统计；输入是 SST 公开计数。
- **结果**：N0→N1 与 N4@30k→N5 成立；N2→N3、N3→N4 不成立；clean 增益 66% 来自两个 click 任务。
- **状态**：**已运行**（`python3 -I analysis.py`，日志 `logs/analysis.txt`）。这是本报告唯一的 S 级结果，且仅指统计复算。

### MVE-1 — 未执行（如果上学习策略）

- **假设**：在 2 个 RoboTwin 任务上，小 BC 策略 + 指令条件前景变暗，random 成功率优于 raw，且不劣于光度 DR。
- **对照**：raw；光度 DR；关键消融：指令无关 mask、随机物体 mask。
- **变量**：输入管线；控制：策略、数据、seeds、步数、评测协议。
- **环境**：RoboTwin 2.0，2 任务，50 clean demos/task，100 trials/task，固定 seeds；ACT/DP3 量级。
- **指标**：成功率、配对 McNemar、clean 回退、在线掩码延迟。
- **验收**：random ≥ +5 pp 且 p<0.05；clean 回退 ≤2 pp。
- **失败**：无增益，或 clean 回退 >2 pp，或增益在指令无关 mask 下消失。
- **记录**：per-episode CSV、原始 stats、配置哈希。
- **回退**：保留 raw 策略，不引入掩码服务。
- **状态**：**未执行**。

### MVE-2 — 未执行（现在就能做）

- **假设**：未来任何 LeRobot 风格演示集，10 episode 抽样可发现帧/行错位、PTS 违规、解码失败、padding 未掩。
- **验收**：零 mismatch；所有 padding 在 loader 中被掩。
- **失败**：任一 mismatch → 不训练，先修数据。
- **状态**：**未执行**；建议作为下一个数据集的准入门禁。

### MVE-3 — 阻塞

SST checkpoints 未发布；若发布，用相同 seeds、100 episodes/task 对 N4/N5 做配对 McNemar。**未执行**。

---

## 12. Limitations & Uncertainties（局限与不确定性）

| 不确定性 | 影响 | 关闭方式 |
|---|---|---|
| SST checkpoints 未发布 | 无法复现 81.86/58.22；无法配对重评 | 等发布，或向作者索取 |
| 赛事规则只读到论坛摘要 | “clean-only 约束”是 B 级；若规则允许 randomized，SST 的约束叙事要改写 | 取规则原文/官方 PDF |
| 部分论文只读摘要（RTC、SAM2Act、DP3、LIBERO-Plus）；RoboTwin 只读了 HTML 的协议/局限 | 机制/数字是作者主张，未独立核验 | 读全文/附录 |
| 统计检验不配对、忽略 task 聚类 | p 值是乐观上界；真实显著性更低 | 需要 per-episode/seed 数据 + McNemar/混合效应模型 |
| 未做真实机器人实验 | 所有迁移结论是 C/D | 受控台面实验 |
| 3060 显存未记录 | 算力结论是算术推断 | 查 `nvidia-smi` |
| SST 自有代码无 LICENSE | 不能直接复用 | 法务/作者授权；或只用上游 Apache-2.0 |
| 报告的“决赛”叙述与仿真实验混在一起 | 容易误读为真机验证 | 以代码/数据为准；真机方案未公开 |
| 未审 LoRA/冻结 backbone 等更便宜的 VLA 微调路线 | 可能遗漏更低成本的替代 | 后续专项调研 |

---

## 13. References（参考文献）

### 论文

1. Wu et al. *From Foundation to Application: Improving VLA Models in Practice* (LingBot-VLA 2.0). arXiv:2607.06403. <https://arxiv.org/abs/2607.06403>
2. Chen et al. *RoboTwin 2.0*. arXiv:2506.18088. <https://arxiv.org/abs/2506.18088>
3. Carion et al. *SAM 3: Segment Anything with Concepts*. arXiv:2511.16719. <https://arxiv.org/abs/2511.16719>
4. Fei et al. *LIBERO-Plus*. arXiv:2510.13626. <https://arxiv.org/abs/2510.13626>
5. Black et al. *Real-Time Execution of Action Chunking Flow Policies*. arXiv:2506.07339. <https://arxiv.org/abs/2506.07339>
6. Fang et al. *SAM2Act*. arXiv:2501.18564. <https://arxiv.org/abs/2501.18564>
7. Ze et al. *3D Diffusion Policy*. arXiv:2403.03954. <https://arxiv.org/abs/2403.03954>
8. Black et al. *π0*. arXiv:2410.24164. <https://arxiv.org/abs/2410.24164>
9. Howard & Ruder. *ULMFiT*. arXiv:1801.06146. <https://arxiv.org/abs/1801.06146>
10. Tobin et al. *Domain Randomization*. arXiv:1703.06907. <https://arxiv.org/abs/1703.06907>
11. Wang et al. *Large Language Models are not Fair Evaluators*. arXiv:2305.17926. <https://arxiv.org/abs/2305.17926>
12. Zheng et al. *Judging LLM-as-a-Judge*. arXiv:2306.05685. <https://arxiv.org/abs/2306.05685>

### 仓库与数据

13. LingBot-VLA 2.0: <https://github.com/Robbyant/lingbot-vla-v2>（Apache-2.0；README/`robotwin.yaml`/`robotwin.txt`，访问 2026-11-25）
14. SST: <https://github.com/YzmYalier/Lingbot-Challenge-SST>（commit `8797aa31dd9798a6e931d57857f32cd5de372b6c`）
15. SST 报告: <https://yzmyalier.github.io/Lingbot-Challenge-SST/>
16. SST 数据: <https://huggingface.co/datasets/yydsyangsdyy/Lingbot-Challenge-SST>（revision `7111c726e5f45e045e5ead62816a1d175a826a9e`）
17. RoboTwin: <https://github.com/RoboTwin-Platform/RoboTwin>；<https://robotwin-platform.github.io/>
18. SAM 3: <https://github.com/facebookresearch/sam3>
19. LeRobot issues: <https://github.com/huggingface/lerobot/issues/5039>, <https://github.com/huggingface/lerobot/issues/5187>, <https://github.com/huggingface/lerobot/issues/5051>
20. 赛事规则（论坛摘要）: <https://tianchi.aliyun.com/forum/post/1081761>

### 本仓库的来源记录与实验

- [LingBot-VLA 2.0 来源记录](../references/manipulation/lingbot-vla-v2.md)
- [RoboTwin 2.0 来源记录](../references/datasets-benchmarks/robotwin-2.md)
- [SAM 3 来源记录](../references/perception/sam3.md)
- [VLA 鲁棒性与替代路线](../references/manipulation/vla-robustness-and-alternatives.md)
- [微调策略与 judge 偏差](../references/manipulation/fine-tuning-and-judge-bias.md)
- [LeRobot v3.0 数据完整性](../references/datasets-benchmarks/lerobot-v3-data-integrity.md)
- [SST 仓库审计](../references/manipulation/sst-repo-audit.md)
- [赛事规则来源](../references/datasets-benchmarks/competition-rules.md)
- [复算实验设计](../experiments/20261125-lingbot-sst-reanalysis/design.md)
- [复算结果](../experiments/20261125-lingbot-sst-reanalysis/result.md)
- [复算脚本](../experiments/20261125-lingbot-sst-reanalysis/analysis.py)

---

## 附录 A. 自审（按 AGENTS.md §12）

### A.1 检查清单

| 问题 | 自查结果 |
|---|---|
| 是否存在确认偏误？ | 初稿倾向于“这套方法很有用”；复算后改为“头条有效、中间阶段不显著”，并补了官方 c+r 反例。 |
| 是否遗漏明显的替代方案？ | 补了 DR/c+r、DP3、SAM2Act、RTC、经典位姿；没有深审 LoRA/冻结 backbone，已列为限制。 |
| 是否混淆相关性和因果？ | 明确标注 N5 是合并改动、未拆分；N3/N4 未达显著；没有把“提升”写成“因果”。 |
| 是否存在未经验证的技术假设？ | 6B FP16≈12 GB 是算术（C）；3060 显存未记录；赛事规则是 B；均已标注。 |
| 是否过度解读论文？ | RoboTwin/RTC/SAM2Act/DP3/LIBERO-Plus 只读摘要，已标注 B；SAM3 与 ULMFiT 读了正文/PDF 相关节。 |
| 是否把 README 当实现？ | 代码结论都给了 `file:symbol:line`；README 的 93.52/92.80 明确标为官方 README，不是论文。 |
| 是否有虚构引用/链接/结果？ | 所有链接访问过；统计结果由 `analysis.py` 复算并留日志；未运行的实验明确标“未执行”。 |
| 推荐是否适合当前项目？ | 推荐“不引入 VLA + 采纳三项工程实践”，与无数据/无算力/安全边界一致。 |
| 是否足以指导下一步？ | 是：MVE-2 可立即做；MVE-1 有验收/失败判据；VLA 重启有触发条件。 |

### A.2 本报告修正过的问题

1. **初稿把官方 93.52/92.80 当作同条件基线**。修正：官方用 clean+randomized（500–1,000 random/task），赛事禁止 randomized；两者不可直接比。
2. **初稿把“Qwen 自动提词”当作通用能力**。修正：源码是 73 行手工词表 + `MISSED` 规避，泛化性下调。
3. **初稿把 module LR 的 +2.2 pp 当作确定收益**。修正：15k/25k 各自 p≈0.11；只能算提示性证据。
4. **初稿把 clean 81.86 当作全面提升**。修正：66% 的 clean 增益来自两个 click 任务，中位数仅 +1 pp。
5. **初稿以为评测用预计算 mask**。修正：评测在线跑 SAM3 + Qwen judge，样式从 checkpoint 回读。
6. **初稿把 0.2 当作最终背景系数**。修正：最终是 0.1 + 2 px 白边；0.2 是 judge 图/默认 fallback。
7. **初稿把 SST 仓库当作 Apache-2.0**。修正：根目录无 LICENSE；只有 vendored 上游是 Apache-2.0。
8. **初稿引用 `page` 分支 `blog.md` 的数字**。修正：该文件是过期草稿；以发布页 + `results.csv` 为准。
9. **初稿把 50 episodes/task 当作官方协议**。修正：RoboTwin 官方是 100；SST 的消融用 50，基线和终版用 100。
10. **初稿把 SAM3 的 30 ms/image 当作评测成本**。修正：那是 H200 图像 PCS；视频跟踪随物体数线性增长，SST 是服务化在线推理。

### A.3 残余偏差与未做的事

- 本报告对统计显著性的要求较严，可能低估了“工程上仍然值得做”的改动；作者在 50 episodes/task 的预算下做消融是合理的。
- 没有读 RoboTwin/RTC/SAM2Act/DP3/LIBERO-Plus 的全文，机制细节可能有误；已标 B。
- 没有运行任何 SST 代码、没有下载权重、没有实机；所有“会不会在 ArmPi 上工作”的结论都是 C/D。
- 没有审 LoRA、冻结 backbone、视觉 prompt 的其他形式（SoM、RoboPoint）等更便宜的替代；这是下一轮调研的候选。
