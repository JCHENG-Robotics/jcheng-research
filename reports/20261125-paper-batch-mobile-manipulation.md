# ArmPi Ultra 论文批次评估：10 篇 2026 年工业视觉、移动抓取与轻量 VLA 文献的可迁移性

> 报告状态：**reviewed（self-review only；独立评审 pending）**。日期：2026-11-25。
> 作者：ZCode（研究代理），for J. Cheng。评审：自查（附录 A）；独立评审未做。
> 本报告影响的决策：这批论文中哪些方法/组件值得在 JCHENG 生态内做最小验证，
> 哪些应明确不做；近期是否为 VLA、6D 位姿或分割模型投入工程时间与 GPU 预算。
> 研究主题：2026 年 10 篇论文（工业视觉分拣、6D 位姿/装箱、移动抓取、轻量 VLA）
> 对 ArmPi Ultra（Pi 5 + 5-DoF 臂 + D435i/Aurora + RTX 3060 Laptop 6 GB）的
> 技术可迁移性评估。
> 研究边界：10 篇 PDF 全文已读（页数与图表范围见各来源记录）；**未执行任何论文
> 代码，未连接机器人，未做硬件实验**；02/05/12 三篇未能获取（见 §12）；部分
> arXiv 论文的附录/补充材料未单独获取；所有“实机有效”均为作者报告，非本机复现。

**证据等级**：**S** 在本机复现 · **A** 一手论文、源码或官方文档 · **B** 可信
二手证据 · **C** 基于现有证据的推断 · **D** 未验证假设。本报告没有任何 S 级
论文结论；唯一的 S 级内容是本仓库的桌面核验（文件存在性、链接可达性、源码
静态检查）。

---

## 01. Executive Summary（执行摘要）

**结论：这 10 篇论文中没有一篇可以直接部署到 ArmPi Ultra；现在不应引入任何
端到端系统。** 可采纳的是三类“低风险资产”：评测/失败分类协议、可离线复现的
小模型组件、以及一个受控的 VLA 沙箱实验。具体建议：

1. **立即做（桌面，0 硬件）**：把 Cracking（07）的三类失败诊断框架和
   Visibility-Aware（09）的可见性约束，改写成 JCHENG 现有失败日志的标注表；
   先回答“我们的失败到底卡在规划、基座定位还是局部操作”，再决定买什么。
2. **先做离线 MVE（笔记本 GPU，不动机器人）**：用现有 D435i/Aurora 数据比较
   YOLO11-seg / GLD-YOLO 模块与当前 YOLOv8s 检测的掩码、3D 质心与时序抖动；
   用 5 个已知物体比较 SAM-6D + 多视角 pose buffer 与现有 PnP/AprilTag 的
   6D 位姿噪声；用 SmolVLA 450M 在 6 GB 上做纯回环延迟/显存测试。
3. **明确不做（本阶段）**：不移植 PanoVLA（双 6-DoF 臂 + 全景 + 4×A100 训练）、
   不移植 Visibility-Aware 的 ROS 1/Fetch 整机、不把 ROS2SmolVLA 的
   `TwistStamped`/`JointTrajectory` 直接接到厂商控制器、不做煤矸石残差 RL
   （6-DoF + 无代码 + 仿真增益在噪声内）、不做依赖编码器的输送带动态定位。

支撑结论的四条硬事实：

1. **平台不匹配是系统性的，不是个别参数问题。** 10 篇中 0 篇提到 ArmPi 或
   5-DoF；01/10 是 6-DoF，08 是双 6-DoF 臂 + 全景，09 是 Fetch 7-DoF，
   06 是 UR10e 6-DoF，11 是 UR16e 6-DoF。凡需要任意 6D 姿态修正或 6 关节
   动作空间的方法，都必须先解决 5-DoF 可达流形/动作屏蔽，论文均未提供。
2. **可复现性很差。** 10 篇中只有 06（Apache-2.0，5 个 ROS 2 仓库）和 09
   （MIT，ROS 1 Noetic）有可审计代码；07 的仓库只有 PDF/图片（README 明写
   “Code coming soon”），08 的仓库为空，04 明写代码保密，10 无代码/CAD，
   01/03/11/13 无代码。**“论文声称 + 无代码”不能作为工程采纳依据。**
3. **头条数字多数不是本平台可复现的实机数字。** 09 的 70.4%/57.9% 是 400 个
   仿真场景；实机只测了完整系统（65.0% 静态 / 55.0% 动态），无 baseline。
   08 的 73.4% 是 4 个任务 × 15 trials。11 的 92% 是 5 类 × 5 trials（Wilson
   95% CI 75.1–97.8%）。06 的作者自己写“success rates are currently too low
   for real-world deployment”。01 的仿真增益 0.5 pp（10/2000）在统计上不可
   区分于零。
4. **算力/软件栈不匹配。** 06 在 RTX 4080 16 GB 上推理、L40S 上训练 25 h；
   08 用 4×A100 训练、RTX 4090 推理；本机是 RTX 3060 Laptop **6 GB**、
   ROS 2 Jazzy 主机 + Humble 机器人。SmolVLA 450M 的**推理**有可能放进 6 GB，
   但这是 D 级假设，必须先做显存/延迟实测；训练与 PanoVLA 级别模型不在本机
   能力范围内。

**主要风险**：把“论文里的仿真提升”误当成“我们平台上的工程收益”；把
`/joint_states` 或厂商控制器当作可信状态/安全通道；在没有 lease、deadman、
stop latch 的情况下让学习策略直接发布动作。任何实机运动仍需逐次操作员授权，
且只能经 `jcheng-system` 的 `ExecuteMotion`。

---

## 02. Research Questions（研究问题）

### 2.1 任务书补全（用户模板）

| 模板字段 | 本批次填写 |
|---|---|
| **研究主题** | 2026 年工业视觉分拣、6D 位姿/装箱、移动抓取与轻量 VLA 论文批次（10 篇）对 JCHENG ArmPi Ultra 的技术可迁移性评估 |
| **项目背景** | JCHENG 多仓库生态：L2 `jcheng-system`（唯一运动入口 `ExecuteMotion`，lease/deadman/stop latch）、L3 `jcheng-perception`（Pi 5 采集 + 笔记本 GPU YOLO + 双视角融合）、L3 `jcheng-mobile`（ICP 激光里程计/SLAM/Nav2，无编码器）、OPS `jcheng-ops`（健康探针/看门狗）、冻结基线 `jcheng-manipulation v1.0.0`（5-DoF 视觉抓取，24/24，RSS 13.33 mm） |
| **核心研究问题** | 这 10 篇论文分别解决什么问题、证据强度如何？哪些方法/组件与 ArmPi Ultra 的 5-DoF、Pi 5 8 GB、D435i/Aurora、RTX 3060 6 GB、ROS 2 Humble、无编码器/无 e-stop 约束兼容？哪些开源代码可审计/复用，哪些只是声明？近期应做哪些最小实验、明确不做哪些？ |
| **约束条件** | 硬件：Pi 5 8 GB、5-DoF 总线舵机臂 + 平行夹爪、D435i + Aurora 930、LSLIDAR M10 未接入、RTX 3060 Laptop 6 GB；软件：机器人 ROS 2 Humble、主机 Jazzy、CycloneDDS、DDS 域 0/41/42/43；安全：运动仅经 `ExecuteMotion`、lease + 500 ms deadman + stop latch、无 e-stop/抱闸/编码器/自碰撞模型；数据：无演示数据集、无模型权重入库；时间/成本：本批次不做实机实验，只做离线 MVE |
| **交付物** | 10 份逐篇来源记录（`references/`）+ 本 13 节报告 + 4 个未执行的最小实验设计（MVE-0…3）+ 分类与采纳/不采纳清单 |

### 2.2 可回答的子问题

- **RQ1（证据）**：每篇论文的研究问题、方法、数据集、baseline、样本量、统计
  可靠性、作者自述局限分别是什么？哪些结论是作者报告值，哪些是推断？
- **RQ2（平台）**：把每篇的动作空间、传感器、状态观测、控制频率、算力需求
  与 ArmPi Ultra 对照，硬阻断项是什么？哪些可以通过适配层/降级解决？
- **RQ3（复现）**：哪些论文有可克隆、可读、许可允许的代码？代码是否覆盖论文
  的核心贡献，还是只有 Docker/接口外壳？仓库的 commit、许可、ROS 版本是什么？
- **RQ4（决策）**：哪些方法值得做离线 MVE，验收/失败判据是什么？哪些应明确
  拒绝或推迟？拒绝的理由是证据不足、平台不匹配，还是工程成本过高？
- **RQ5（空白）**：这批论文共同遗漏了什么（5-DoF、无编码器、安全边界、
  小样本统计、真实部署）？下一步应补哪些自有数据/实验？

### 2.3 不在本报告范围内

- 不评价论文作者的学术声誉或期刊影响因子；只评价方法与证据。
- 不比较不同任务的绝对成功率（数据集/判据/硬件不同，不可直接横比）。
- 不做实机运动、不连接 DDS、不训练/微调任何模型；所有 MVE 均为未执行设计。
- 不覆盖 02/05/12 三篇未能获取的论文（见 §12）。

---

## 03. Current System Analysis（当前系统分析）

### 3.1 分层与事实源

| 层 | 仓库 / 版本 | 当前能力（有证据的部分） | 与本批次相关的硬约束 |
|---|---|---|---|
| L2 | `jcheng-system` v0.3.0-dev，`52fa293` | `ExecuteMotion` action、lease、arbiter、stop latch；M5.2 单关节/夹爪厂商桥接；M6 MoveIt plan-only；未做安全认证 | 任何学习策略只能发布 intent；不得直接写 `/servo_controller` 或厂商控制器 |
| L3 感知 | `jcheng-perception` v0.1.0，`b401767` | Pi 5 采集/深度/TF 环、反投影、双视角融合、30 Hz 输出；笔记本 GPU YOLO；时间戳不重写 | 多姿态精度、对齐深度、运动集成**未验证**；无 6D 位姿/实例分割管线 |
| L3 移动 | `jcheng-mobile`，`6b3a7e1` | ICP 激光里程计、SLAM、Nav2、`/cmd_vel` intent；无驱动/设备 | M10 未接入；无轮式编码器；Nav2/RTAB-Map 未在实机验证 |
| 操作基线 | `jcheng-manipulation` v1.0.0，`a08b8b6` | 5-DoF 模型/TF、手眼标定、MoveIt/Pilz、24/24 抓取、RSS 13.33 mm | 冻结基线；无 e-stop/抱闸/编码器；`/joint_states` 是命令缓存 |
| OPS | `jcheng-ops` v0.1.0，`144d89d` | 15 s 硬件看门狗、30 s 健康检查、systemd 自愈；HTTP only | 看门狗未在真实 wedge 中触发过；不参与 DDS |
| 契约 | `jcheng-interfaces` v0.1.0 | 契约哈希 `sha256:0b8d72…f24b42` | 跨仓库契约只在此处改；本报告不改契约 |

### 3.2 硬件与算力（本报告所有迁移判断的基线）

- **机器人**：ArmPi Ultra，Raspberry Pi 5 8 GB，ROS 2 Humble；5-DoF 总线舵机
  臂 + 两指夹爪；腕部 Aurora 930 RGB-D、机身前 D435i；LSLIDAR M10 未接入；
  麦轮底盘无编码器。
- **操作笔记本**：RTX 3060 Laptop **6 GB**（`nvidia-smi` 6144 MiB，见 GloVLA
  报告），ROS 2 Jazzy；YOLO 稳态 9.0 ms FP32 / 7.4 ms FP16（640，单图），
  ROS 节点平均 54.3 ms/帧。
- **安全边界**：无 e-stop、无抱闸、无关节编码器、无自碰撞模型；软件 stop 不是
  e-stop；总线舵机读无安全超时；`/joint_states` 是命令缓存，完成/位姿真值来自
  `GetBusServoState`。
- **DDS**：域 0 厂商、41 特权、42 能力、43 仿真；能力仓库只能加入 42；感知在
  实践中跑域 0（CycloneDDS）；一个图一个 RMW。

### 3.3 这意味着什么

1. **动作空间**：5-DoF 不能执行任意 6D 位姿修正；任何输出 6D delta 的策略都
   需要投影/屏蔽/重定向层，且投影后的可行性未经论文验证。
2. **状态观测**：论文常用的关节角/角速度、末端 6D 位姿、基座里程计，在本平台
   分别受“命令缓存”“无编码器”“M10 未接入”限制；用这些输入训练/推理前必须
   先定义可信替代或明确降级。
3. **算力**：6 GB 是本批次最硬的筛选器；能加载 450M VLA 不等于能训练/微调，
   更不等于能满足控制周期。
4. **安全**：论文里的“ bounded residual”“collision checking”“watchdog”都是
   方法层概念，不能替代 `ExecuteMotion` 的 lease/deadman/stop latch；任何
   直接发布 `TwistStamped`/`JointTrajectory` 的代码都是安全边界外的。

---

## 04. Research Methodology（研究方法）

### 4.1 材料与检索

- **输入**：用户提供的 10 篇 PDF（目录 `/home/jerichocheng/文档/JCHENG_Robotics_Papers/`），
  以及 `download_report.txt` 记录的 02/05/12 获取失败。
- **全文获取**：`pdftotext -layout` 提取全文；对双栏/公式错位页用
  `pdftotext -f N -l N` 回读原页；逐篇核对标题、作者、卷期、DOI、日期、许可。
- **外部核验**：DOI 解析（doi.org/Crossref）、arXiv abs 页、GitHub REST API
  （仓库元数据、tree、HEAD SHA、license）、项目页 HTTP 状态。访问日期均为
  2026-11-25。
- **代码审计**：对 06 的 `ros2smolvla_interface_lerobot`、`interface_camera`
  做 `git clone --depth 1` 静态阅读（未执行）；对 09 只读 README/tree；对 07
  读 tree 与 README；对 08 读空 tree。所有源码结论标 A，未运行标“静态分析”。

### 4.2 纳入/排除标准

**纳入**：2026 年发表/预印；主题属于工业视觉分拣、6D 位姿/装箱、移动抓取、
轻量 VLA/移动操作；能获得全文；与 ArmPi Ultra 的感知/操作/移动至少一个层
相关。

**排除**：仅摘要可读、无法核对实验的论文；与生态无关的纯算法论文；无法获取
全文的 02/05/12。排除不改变“批次”的边界，但在 §12 明确记录。

### 4.3 阅读与证据规则

- 每篇至少读：摘要、引言、方法、实验设置、主结果表、消融、结论、数据/代码
  可用性声明；不以摘要代替正文。
- 区分四类陈述：**【报告值】**（论文明确数字）、**【作者解释】**（作者因果
  解释）、**【推断】**（本评审推理）、**【未报告】**。
- 关键数字必须能回到页码/表号/图号；每份来源记录附 8–12 条英文原文片段。
- 证据等级按 §9 的 S–D 规则；论文作者的自评不升级为客观事实。
- 统计复核：对二项成功率做独立比例检验时明确标注“本评审计算”，并说明
  试次独立性假设；不把 p 值当作因果证据。

### 4.4 方法限制

- 未获取补充材料/附录（07 的附录在同一 PDF 内已读；08/09 的附录未单独获取）。
- 未复现任何论文代码；06 的代码只做静态阅读；09 的 ROS 1 代码未构建。
- 未做系统检索（本批次是用户给定选集，不是 PRISMA 式全覆盖）；因此不能
  据此声称“某方向没有更好工作”。
- 未访问机器人；所有平台适配判断基于仓库文档与实测证据，不基于本批次实验。

---

## 05. Literature Review（论文分析）

> 逐篇的完整元数据、表格、原文核验片段见 `references/` 下的 10 份来源记录。
> 本节只保留与决策有关的问题、方法、关键数字、批判与迁移判断；不重复整篇
> 论文的摘要。

### 5.1 01 — 煤矸石抓取的有界残差精化（Sensors 2026）

- **问题/方法**：GraspNet 给 6-DoF 标称抓取，PPO 在 ±20 mm/±15°、最多 5 次
  决策内学残差；PointNet++ + 12 维关节状态，InfoNCE 对齐点云与物理状态。
- **证据**：MuJoCo 2000 次/方法，Full 98.0%（1960）vs Baseline PPO 97.5%
  （1950）；CR5 真机 200 次/方法，86% vs 70%，末端 0.031 vs 0.046 m。
- **批判**：仿真 +0.5 pp 只差 10/2000，作者自己不做显著性声明；缺“GraspNet
  零残差”最强对照；真机 +16 pp 与仿真 +0.5 pp 相差 32 倍且无域适配解释；
  残差单独使用反而低于 baseline（1944<1950）；§3.2.4 的“6D pose”与 §4.1 的
  12 维 q/q̇ 矛盾；无代码/数据。
- **迁移**：CR5 6-DoF + q/q̇ 输入与 ArmPi 5-DoF/无编码器硬冲突；只采纳
  “有界残差 + 零修正回退 + 单次界≠累计界”的设计语义。
- **来源记录**：[coal-gangue-residual-grasp.md](../references/manipulation/coal-gangue-residual-grasp.md)

### 5.2 03 — 输送带煤矸石动态视觉定位（Scientific Reports 2026）

- **问题/方法**：eye-in-hand 跟踪 + SiamCSF（SiamDW + ECA + 多尺度）；
  APCE 置信度门控，低置信时用编码器位移沿输送方向短期补偿。
- **证据**：312 条序列/34,860 帧/52 目标；带速 0.7–1.0 m/s、70 cm 下
  1.8/1.7 mm、约 58 FPS；补偿把 Pr 82→85%、Cr 96→98.4%。
- **批判**：引言声称解决带速波动/打滑/跑偏/振动，实验只有恒定带速/距离；
  补偿依赖编码器（JCHENG 没有）；1.7 mm 的 GT、时间同步、标定残差均未报告，
  1 m/s 下 1 帧时间误差就是约 17 mm；摘要的 1.7/1.8 mm 来自补偿子集，
  主表是 1.8/1.7；Pr≈85% 与 Cr>98% 指标口径自相矛盾；无代码/数据。
- **迁移**：不引入运行时；只借鉴“置信度门控 + 短期外推”的结构，且必须由
  system 层限幅/停止。
- **来源记录**：[dynamic-localization-coal-sorting.md](../references/perception/dynamic-localization-coal-sorting.md)

### 5.3 04 — 井下矿块实例分割 GLD-YOLO（Machines 2026）

- **问题/方法**：YOLO11-seg 上加入 C3k2_GBC、C2PSA_LRSA、PAFPN_DDFE
  （EDLKC+WTConv+双向注意力）与 Focaler-Shape-IoU。
- **证据**：自建 2100 张/21,420 实例，随机 8:1:1；mAP50 98.1、mAP50-95 82.3
  vs YOLO11n 93.7/77.2（+4.4/+5.1）；90 FPS（RTX 5070，batch=1）。
- **批判**：单一场景/单类别/固定相机光照，98.1% 是同分布内插；1900 张来自
  连续破碎实验，随机帧划分有泄漏风险；跨表单模块数值有 0.3–1.1 pp 不一致；
  MineralImage5k 原始定位是零样本分类/描述、分割子集约 100 张，论文却称
  5341 张/3 万实例并报 mask AP；代码保密；Ultralytics AGPL-3.0。
- **纠正**：Table 3 的四模块全开行是 98.1/82.3，与 Table 2 一致；**不存在**
  “全模块 96.7 vs 主表 98.1”的矛盾（96.7 是三模块行，无 Focaler）。
- **迁移**：不引入运行时；只把 Focaler-IoU、P2/P3 注入列为可选 A/B，
  先过许可评审。
- **来源记录**：[gld-yolo-ore-segmentation.md](../references/perception/gld-yolo-ore-segmentation.md)

### 5.4 13 — 3D 视觉无序箱拣综述（Applied Sciences 2026）

- **内容**：130 篇叙事综述；成像原理/系统组成/识别与位姿/抓取/应用五层。
- **批判**：自述 narrative，却用 PRISMA 式流程图与 “systematically” 措辞；
  无 PRISMA 清单、无双人筛选、无偏倚评估、无定量综合；21/130（16.2%）为
  写作/修回期补录；未引 SAM-6D/FoundationPose，并称基础模型“只能离线”，
  被本批次 Pickalo 的 SAM-6D 在线 600 PPH 直接否证；遗漏 BOP/XYZ-IBD/
  ROBI 与激光三角测量。
- **迁移**：只作术语表/选型地图；不作为技术依据。
- **来源记录**：[3d-bin-picking-review.md](../references/manipulation/3d-bin-picking-review.md)

### 5.5 10 — Pickalo 工业箱拣（Robotics 2026）

- **问题/方法**：腕载 D435i + BridgeDepth 深度增强 + Mask R-CNN 分割 +
  SAM-6D 零样本 6D 位姿 + pose buffer + 离线抓取候选库/效用排序。
- **证据**：UR5e，三类高反光件；Table 1 报 577.85–615.89 MPPH、96.12–98.84%
  SR；30 min 消融 BridgeDepth 96.3% vs RealSense 88.5%；pose buffer
  96.3% vs 84.2%。
- **批判**：Table 1 的 B 行与 Table 2/3 的 5 min 行三个指标逐位相同，高度
  可能复用同一次 5 min 试验（615.89 MPPH × 5 min ≈ 51 抓，而非 1000
  iterations）；每个消融条件 n=1、无种子/方差/显著性；无工业相机对照；
  无卡抓/掉件/双抓率；D435i 红外投影器状态未报告；无代码/CAD；SAM-6D
  仓库无 LICENSE（默认保留所有权利）；3060 6 GB 预计 3–6 s/迭代。
- **迁移**：不引入运行时；pose buffer、位姿-深度几何拒绝、候选排序可离线
  借鉴；MVE-2 只在有 CAD、许可解决后做。
- **来源记录**：[pickalo-bin-picking.md](../references/manipulation/pickalo-bin-picking.md)

### 5.6 11 — 轻量视觉移动机械臂杂货拣选（Sensors 2026）

- **问题/方法**：UR16e + MiR100 + ZED 2i + Jetson Orin Nano；RGB-only 前端，
  YOLOv11-Nano 检测 + FastSAM-s 分割 + PCA 抓取点，单像素深度查询。
- **证据**：Level-3 五类、每类 5 次、共 25 次，23/25=92%（Wilson 75.1–97.8%）；
  sweet bag 3/5=60%；平均 7.5 s；模型 30.9 MB。
- **批判**：n=5/类，四类满分项的 Wilson 下限只有 56.6%；无 baseline、无消融、
  无 mAP/precision/抓取点误差；“Grocery Pick-and-Pack Benchmark”是作者团队
  2025 年自订分级，不是社区 benchmark；7.5 s 的 “edge device” 从未点名，
  Jetson 只测 CPU 路径（0.59 FPS）；能耗口径不一致（GPU 单轨 vs SoC 全轨），
  Table 8/9 的 GPU 每帧能量差 2.4 倍；30.9 MB < GraspNet 7.2 MB 的表述
  按字面错误；无代码/数据。
- **迁移**：不引入运行时；RGB-only + 单像素深度 + PCA + Wilson 区间可借鉴。
- **来源记录**：[lightweight-grocery-mobile-manipulator.md](../references/manipulation/lightweight-grocery-mobile-manipulator.md)

### 5.7 06 — ROS2SmolVLA（Procedia Computer Science 2026）

- **问题/方法**：把 SmolVLA 450M 接到 UR10e；3 路 RGB、末端笛卡尔位姿、
  7 维笛卡尔 delta；ROS 2 Jazzy + LeRobot；代码/权重/数据公开。
- **证据**：349 episodes；9 组场景；聚合 pick 77.72%、place 63.59%；
  作者自述 “too low for real-world deployment”；训练 L40S 25 h，
  推理 RTX 4080 16 GB。
- **批判**：无 baseline；ID 是训练网格内插；每格 n=10/6，合计约 184 次；
  颜色/纹理偏置严重，gray 提示遵从率 20–30%；代码硬编码 6-DoF，直接
  publish `/arm_controller/joint_trajectory` 与 `TwistStamped`，无
  lease/deadman/stop latch；Jazzy vs Humble；发布物 7 维状态 vs 论文
  12 维关节说法不一致；延迟/显存未报告。
- **迁移**：**不直接接机器人**；作为离线 VLA 沙箱（MVE-3），先验证 6 GB
  显存/延迟，再讨论 5-DoF 动作重映射。
- **来源记录**：[ros2smolvla.md](../references/manipulation/ros2smolvla.md)

### 5.8 07 — Cracking Mobile Manipulation（arXiv 2026）

- **问题/方法**：诊断长程移动操作的失败（规划/导航-底盘/局部操作），在冻结
  子任务 VLA 外加持能卡、视觉记忆、可达性底盘调整、末端调整。
- **证据**：RoboCasa365 19→47%（dev）/18→49%（held-out）；BEHAVIOR-1K
  14→37%；真机 5/20→13/20；最强端到端 Xiaomi Robotics 1 44/45%。
- **批判**：47/49 分母不同却并置成递进；按作者自己的 0.8^H 参考，20 任务
  平均应有 41.0%，全系统 47.0% 只高 6 pp；最强端到端仅差 3–4 pp，摘要未提；
  单训练种子；只有 base adjustment 稳定显著（p=0.004/0.013），memory/EEF/
  demo 的 p=0.057–0.344；规划器依赖 Kimi K3/Gemini/Qwen3-VL，成本/延迟未报；
  代码仓库只有 PDF/图片，README 全 “Coming soon”。
- **迁移**：不引入 agentic 运行时；采纳失败诊断协议、可达性门控、配对
  McNemar + 分层 bootstrap。
- **来源记录**：[cracking-mobile-manipulation.md](../references/manipulation/cracking-mobile-manipulation.md)

### 5.9 08 — PanoVLA（arXiv 2026）

- **问题/方法**：轮式双臂 6-DoF + 顶部 360° 相机；VR 全身遥操作采 800 条/
  5.5 h；π0.5 双专家 + 100M 全景专家 + MTPano 编码器。
- **证据**：4 任务 × 15 trials，SCR 91.3%、SR 73.4% vs π0.5 58.6/30.0；
  π0.5 w/ Pano 80.8/56.7；4×A100 训练，RTX 4090 推理。
- **批判**：容量/预训练与“全景几何”混淆（无容量匹配对照）；4 个任务各自
  微调，不是通才；baseline 只限 π0.5 家族；n=15/任务，对最强 baseline 的
  汇总 p≈0.056；消融只在已打平的 Move Pen；无导航/安全指标；全景相机规格
  缺失；仓库 `puffyyy/panovla` 为空；无数据/权重。
- **迁移**：不引入运行时；只作“专用全景编码器/数据预算/SR+SCR 协议”的
  设计参考。
- **来源记录**：[panovla.md](../references/manipulation/panovla.md)

### 5.10 09 — Visibility-Aware Mobile Grasping（arXiv 2026）

- **问题/方法**：Fetch 11-DoF 全身；碰撞可见性 + 物体可见性；速度感知
  gaze、分层 subgoal 行为树、VAMP 滚动时域全身规划。
- **证据**：400 场景 ×5 runs；静态 70.3±1.1%、动态 57.9±1.5% vs
  Nav 54.0/48.6；真机 20+20 次，65.0%/55.0%，只跑完整系统。
- **批判**：代码核验发现仿真/真机都加载 **canonical static map + 预建家具
  碰撞模型**，与 “unknown static/previously unseen layouts” 的表述冲突；
  动态碰撞率 13.9% **高于** Nav 7.5%，摘要却称 “significantly reducing
  collisions”；真机 40 次无 CI/无 baseline，“strong generalization”过度；
  仿真 `dynamic_costmap: True` vs 真机 `False`；核心可见性约束没有直接
  测量；SG-VLA baseline 是未调好的重实现。
- **迁移**：不引入运行时；采纳三层行为树回退、可见性 pre-grasp 采样、
  碰撞按尝试归一化、先验披露要求。
- **来源记录**：[visibility-aware-mobile-grasping.md](../references/manipulation/visibility-aware-mobile-grasping.md)

### 5.11 横向小结

- **平台**：0/10 提到 ArmPi 或 5-DoF；6-DoF/7-DoF/双 6-DoF/11-DoF 全身是
  常态。任何需要任意 6D 姿态修正或 6 关节动作空间的方法，都必须先解决
  5-DoF 可达流形/动作屏蔽。
- **证据**：只有 06/09 有可审计代码；07 仓库只有 PDF/图片；08 仓库为空；
  04 代码保密；01/03/10/11/13 无代码。**0/10 同时具备代码 + 5-DoF 验证。**
- **数字**：头条成功率多数来自仿真或小样本；09 的 70.4/57.9 是 400 个仿真
  场景，真机只测完整系统；08 是 15 trials/任务；11 是 5 trials/类；06 的
  作者自己说不足以部署；01 的仿真增益在噪声内。**不能把这些数字当作
  JCHENG 的预期收益。**

---

## 06. Repository Investigation（开源仓库调查）

### 6.1 代码可用性总表

| # | 论文 | 代码 | 仓库 / 许可 | 覆盖论文核心贡献？ | ROS/环境 | 结论 |
|---|---|---|---|---|---|---|
| 01 | Coal gangue residual | 无 | — | — | — | 不可复现 |
| 03 | Dynamic localization | 无 | — | — | — | 不可复现 |
| 04 | GLD-YOLO | 无（保密） | — | — | — | 不可复现；上游 YOLO11 AGPL-3.0 |
| 06 | ROS2SmolVLA | **有** | 5 个仓库，Apache-2.0 | 是（接口/训练/数据/权重） | Ubuntu 24.04 + **Jazzy** | 可克隆；6-DoF，直发控制器 |
| 07 | Cracking | 占位 | `PKU-VaLuE-Lab/Cracking-Mobile-Manipulation`，Apache-2.0 | **否**（只有 PDF/图片） | — | 不可复现 |
| 08 | PanoVLA | 空仓库 | `puffyyy/panovla`，Apache-2.0，0 files | 否 | — | 不可复现 |
| 09 | Visibility-Aware | **有** | `AdaCompNUS/Visibility-Awared-Mobile-Grasping`，MIT | 是（仿真/真机/baseline） | Ubuntu 20.04 + **ROS 1 Noetic** | 可克隆；Fetch 专用 |
| 10 | Pickalo | 无 | — | — | — | 不可复现；SAM-6D 无 LICENSE |
| 11 | Grocery pick-and-pack | 无 | — | — | — | 不可复现 |
| 13 | Bin-picking review | 无 | — | — | — | 不可复现（综述） |

**统计**：10 篇中 **2 篇**有可克隆、覆盖核心贡献的代码（06、09）；1 篇有
占位仓库（07）；1 篇空仓库（08）；6 篇无代码/保密。**0 篇**同时满足
“代码可用 + 5-DoF + ROS 2 Humble”。

### 6.2 06 — ROS2SmolVLA（唯一可直接克隆的 VLA 栈）

- **仓库结构**：`ros2smolvla_interface_lerobot`（LeRobot→ROS 2 桥）、
  `interface_camera`（ROS 图像→LeRobot）、`ur10e_real`/`ur10e_sim`
  （bringup）、`docker`（容器）。均为 Apache-2.0；`interface_lerobot`
  HEAD `470be64b38b5`，`interface_camera` HEAD `6da3f71b0c4f`（2026-11-25）。
- **动作空间**：`config.py:46-55` 默认 `joint_1..joint_6`；`:58-67`
  固定 6 维速度 + `gripper.pos`；`:68-71` 关节模式固定 6 个 `*.pos`。
  5-DoF 不能直接套用。
- **控制通路**：`ros_interface.py:82-114` 直接创建
  `/arm_controller/joint_trajectory`、`/gripper_controller/joint_trajectory`、
  `TwistStamped` 发布器；`robot.py:128-190` 直接 publish，只有
  `max_relative_target` 幅度裁剪，**没有 lease/deadman/stop latch**。
  在 JCHENG 中这是绕过 `ExecuteMotion` 的安全边界外行为。
- **环境**：README 明写 “tested on Ubuntu 24.04 with ROS2 Jazzy”，
  Dockerfile `ARG ROS_DISTRO=jazzy`；机器人侧 Humble 需降级验证。
- **可复现性**：代码/权重/训练集/评估集都公开；但需 UR10e + Hand-E、
  Azure Kinect（停产）、RTX 4080 级推理；论文的 184 次试验无法从发布物
  直接重放。
- **结论**：可作为**离线沙箱**（MVE-3），不能作为机器人运行时。

### 6.3 09 — Visibility-Aware（唯一可审计的全身移动抓取栈）

- **仓库结构**：ManiSkill3 仿真、Gazebo/真机脚本、RL/VLA baseline、
  `resources/grasp_benchmark.json`（20×20=400）。MIT；HEAD `c37eb1638f66`。
- **环境**：Ubuntu 20.04 + ROS 1 Noetic + CUDA 12.4 + Python 3.11 + pixi；
  VAMP/pytracik/ikfast 本地编译。与 ROS 2 Humble 不兼容。
- **关键代码事实**：`run_maniskill_benchmark.py:156-171` 把
  `canonical_map_path` 作为 `static_pcd_paths` 传入 `Fetch`；
  `observation/scene.py:13` 明确 `static_map (S): canonical world PCD,
  considered immutable`，belief 是 `E(t)=S∪M(t)`；`real_fetch.yaml:6`
  加载 `resources/mp_collision_models/`。**“unknown static” 不是完全未知。**
- **配置差异**：仿真 `dynamic_costmap: True`，真机 `False`；sim-to-real
  对比混入配置差异。
- **可复现性**：仿真 benchmark 与代码齐全，理论上可重跑 400×5；但预计算
  资源需从 Dropbox 下载（未验证）、依赖 GPU/服务、真机 Fetch 不易获得；
  真机 40 次记录未公开。
- **结论**：可审计，但**不能移植**；只借鉴行为树/可见性约束/评测协议。

### 6.4 其他仓库与许可风险

- **07 Cracking**：仓库公开、Apache-2.0，但 tree 只有
  `Cracking_Mobile_Manipulation__...pdf`、`README.md`、`LICENSE`、3 张图；
  README 的 Release 清单全部未勾选。**“论文称将发布” ≠ “已发布”。**
- **08 PanoVLA**：`puffyyy/panovla` 创建于 2026-11-24，tree 为空；
  `panovla.github.io` 只是项目页仓库。无代码/数据/权重。
- **10 Pickalo**：无代码/CAD。依赖 **SAM-6D**（GitHub `license=None`，
  无 LICENSE 文件 → 默认保留所有权利；商用/再分发需作者书面许可）、
  **BridgeDepth**（MIT）；BlenderProc2/Mask R-CNN/SAM 主干未逐一核验。
- **04 GLD-YOLO**：代码保密；方法基于 **Ultralytics YOLO11-seg（AGPL-3.0）**；
  JCHENG 多数仓库无 LICENSE（许可评审未结），复用前必须做许可评审。
- **01/03/11/13**：无代码、无公开数据；数据声明分别为“应要求提供”
  （01/03）、“包含在文中”（11/13）。

### 6.5 代码调查的边界

- 06/09 只做**静态阅读**（`git clone --depth 1` / raw 文件），**未构建、
  未运行、未连接机器人**；所有源码结论为 A 级“代码存在/逻辑如此”，
  不是“运行通过”。
- 07/08 只读 tree/README；10/04 只读论文与项目页；01/03/11/13 只读论文。
- 未审计依赖树的完整许可兼容性；只标注了最直接的 AGPL/无许可风险。

---

## 07. Comparative Analysis（横向比较）

### 7.1 分类矩阵

| 组 | # | 论文 | 任务 | 平台/DoF | 主要证据（作者报告） | 代码 | 迁移成本 | 处置 |
|---|---|---|---|---|---|---|---|---|
| A 工业视觉/分拣 | 01 | Coal gangue residual | 6D 抓取精化 | CR5 6-DoF + RGB-D | 仿真 98.0 vs 97.5；真机 86 vs 70%（200/方法） | 无 | 高（6-DoF/q̇） | 仅设计语义 |
| A | 03 | Dynamic localization | 输送带跟踪 | 龙门架 + 工业臂 | 1.8/1.7 mm、58 FPS（312 序列） | 无 | 不可行（无编码器/皮带） | 不采纳 |
| A | 04 | GLD-YOLO | 矿块实例分割 | 单目工业相机 | 98.1/82.3 mAP、90 FPS（RTX 5070） | 保密 | 中（单场景/AGPL） | 仅 Focaler/P2-P3 |
| A | 13 | 3D bin-picking review | 综述 | — | 130 篇叙事综述 | 无 | 低（背景） | 仅术语表 |
| B 工业抓取/装箱 | 10 | Pickalo | 箱拣 | UR5e 6-DoF + D435i | 600 MPPH、96–99% SR | 无/CAD 无 | 高（SAM-6D/6-DoF） | 仅 pose buffer |
| B | 11 | Grocery pick-and-pack | 移动拣选装袋 | UR16e 6-DoF + MiR100 + ZED | 23/25=92%、7.5 s、30.9 MB | 无 | 中（RGB-only 可借） | 仅前端/统计 |
| C 移动操作/VLA | 06 | ROS2SmolVLA | 桌面 pick-place | UR10e 6-DoF + 3 相机 | pick 77.72/place 63.59% | **有**（Apache） | 中高（Jazzy/6-DoF/直发） | 离线沙箱 |
| C | 07 | Cracking | 长程移动操作 | Astribot-S1 双臂 + 底盘 | 19→47/49%；真机 13/20 | 占位 | 高（云端规划器） | 仅协议 |
| C | 08 | PanoVLA | 移动双臂 VLA | 2×6-DoF + 全景 + 底盘 | 91.3 SCR/73.4 SR；15 trials/任务 | 空 | 不可行（双臂/全景/A100） | 不采纳 |
| C | 09 | Visibility-Aware | 动态移动抓取 | Fetch 11-DoF 全身 | 70.3/57.9%（400 场景×5）；真机 65/55% | **有**（MIT） | 不可行（ROS 1/Fetch） | 仅行为树/约束 |

### 7.2 哪些结果可以直接比较？

**几乎都不能。** 这批论文的任务、数据集、硬件、成功判据、样本量都不同：

- **任务不同**：矿块分割（04）、输送带跟踪（03）、箱拣（10）、货架拣选
  （11）、桌面 pick-place（06）、长程移动操作（07/08/09）。成功率不是同一
  分母。
- **平台不同**：5-DoF 桌面臂、6-DoF 工业臂、7-DoF Fetch、11-DoF 全身、
  双 6-DoF 移动双臂。同一“成功率”背后的可达空间、碰撞风险、控制频率不同。
- **判据不同**：01 抬升 10 cm/2 s；06 pick/place 分开；09 抬升 10 cm/2 s +
  稳定夹持；10 取出并放入目标箱；11 四条全满足 + 人工目视。
- **样本量不同**：01 仿真 2000/方法、真机 200/方法；06 约 184 次；
  08 15/任务；09 仿真 400×5、真机 40；10 每条件 1 次 5/10/30 min；
  11 5/类；03 2,158 帧；04 210 张测试图。
- **仿真 vs 真机**：01/07/08/09 的头条数字含仿真；09 真机只测完整系统，
  01 真机 +16 pp 与仿真 +0.5 pp 相差 32 倍；08 全真机但 n=15；06 全真机但
  无 baseline。

因此本报告**不做跨论文成功率排名**；只比较“证据结构、代码可用性、平台
距离、迁移成本”。

### 7.3 相互矛盾/互证的证据

- **矛盾：13 vs 10。** 13 的 Table 4 称基础模型“Only feasible for offline
  inspection stations currently”；10 用 SAM-6D 在线跑箱拣并报告 600 MPPH。
  两者不能同时为真；更可能是 13 未纳入 2024–2026 的零样本 6D 位姿文献。
- **矛盾：09 的 “unknown static” vs 代码。** 论文称未知静态环境；代码把
  canonical world PCD 作为不可变 `S` 注入 belief，真机加载预建家具碰撞
  模型。按字面理解会高估其未知环境能力。
- **互证：10 vs 13（多视角/合成数据）。** 13 引 [103] 的腕载多视角 RGB-D
  对反光件 <2 mm；10 的 eye-in-hand 半球多视角 + pose buffer + BlenderProc
  合成训练属同一技术家族。两条独立来源支持“多视角 + 合成数据”对反光件
  有效。
- **互证：06 vs 07（小 VLA 的局限）。** 06 的颜色偏置/低成功率与 07 的
  “子任务 VLA 强、长程组合弱”一致：VLA 的瓶颈不只在模型大小，也在数据
  覆盖、状态表示与系统集成。

### 7.4 成熟度与更简单的替代

- **成熟度**：06/09 有可运行代码但平台不匹配；07 是占位；08 为空；
  10/04 无代码；01/03/11/13 无代码。**没有一篇达到“可在我方平台复现”的
  成熟度。**
- **更简单的替代**：JCHENG 现有“YOLO 检测 + 深度反投影 + PnP/AprilTag +
  脚本化抓取 + `ExecuteMotion`”在 24/24 方块任务上已经工作。这批论文没有
  证明“换成分割/6D 位姿/VLA”会带来超过其集成成本与安全风险的收益。
  近期更合理的路径是**改进现有管线的可观测性与失败恢复**，而不是换栈。
- **何时值得换**：当 MVE-1 证明分割使 3D 质心误差/时序抖动显著下降，
  或 MVE-3 证明 450M VLA 在 6 GB 上满足延迟且 5-DoF 重映射可行时，才讨论
  局部替换；不是现在。

---

## 08. Critical Findings（关键发现）

### 8.1 可复现性缺口是系统性的

- 10 篇中只有 **2 篇**（06、09）有覆盖核心贡献的可克隆代码；07 的仓库只有
  PDF/图片，08 的仓库为空，04 明写代码保密，10 无代码/CAD，01/03/11/13
  无代码 [A]。
- **0 篇**同时满足“代码可用 + 5-DoF + ROS 2 Humble”。这不是“再找一篇”的
  问题，而是当前文献与 ArmPi Ultra 的平台差距决定的。
- 因此本批次没有任何 S 级（本机复现）证据；所有“有效”都是作者报告值
  [A/C]。

### 8.2 头条数字的语境被压缩

- **09**：70.4%/57.9% 是 **400 个仿真场景 ×5 runs**；真机只测完整系统
  （65.0%/55.0%，20+20 次，无 baseline、无 CI）。摘要把两者并列，
  读者容易误读为“真机 70%” [A]。
- **08**：91.3%/73.4% 是 **4 任务 ×15 trials**，且 4 个任务各自微调；
  对最强 baseline 的汇总 p≈0.056（本评审计算）[A/C]。
- **11**：92% 是 **23/25**，每类 n=5；四类满分项的 Wilson 下限只有 56.6%
  [A]。
- **06**：作者自己写 “success rates are currently too low for real-world
  deployment”；place 63.59% [A]。
- **01**：仿真 98.0 vs 97.5 只差 10/2000，作者明确不做显著性声明；
  真机 86 vs 70% 是 200/方法，但试次独立性未证明 [A]。
- **07**：19→47（dev）与 18→49（held-out）分母不同，摘要并置成递进；
  按作者自己的 0.8^H 参考，全系统只比“零件组合”高 6 pp [A/C]。

### 8.3 统计脆弱性是常态，不是例外

| # | 重复/种子 | 方差/CI | 显著性 | 主要问题 |
|---|---|---|---|---|
| 01 | 评测 5 seeds；训练种子未报 | 仅奖励有 ± | 作者明确不做 | 仿真增益在噪声内 |
| 03 | 未报 | 无 | 无 | 单次点估计；FPS 64>63 暴露计时噪声 |
| 04 | 未报 | 无 | 无 | 每配置单结果；跨表 0.3–1.1 pp 不一致 |
| 06 | 单种子 1000 | 无 | 无 | n≈184，无 baseline |
| 07 | 单种子 42 | 配对 CI | McNemar | 只有 base adjustment 稳定显著 |
| 08 | 未报 | 无 | 无 | n=15/任务；消融只在 Move Pen |
| 09 | 5 runs | 95% CI（仿真） | 仅 observation stage | 真机 40 次无 CI；动态碰撞反例 |
| 10 | 每条件 1 次 | 无 | 无 | Table 1/2 疑似复用同一 5 min run |
| 11 | 每类 5 次 | Wilson | 无 | n=5；无 baseline/消融 |
| 13 | 不适用 | 不适用 | 不适用 | 叙事综述，无定量综合 |

**含义**：这批论文的“提升”多数没有跨训练种子/跨场景的方差支撑；把它们
当作工程收益预期，会把单次运行的波动误当成方法效应。

### 8.4 仿真到真机的跳跃没有被解释

- **01**：仿真 +0.5 pp、真机 +16 pp，相差 32 倍；无系统辨识、无域随机化、
  无真机微调。真机提升的替代解释（试次不独立、baseline 更脆弱、重试次数
  不同）作者未排除 [A/C]。
- **09**：真机 65/55% vs 仿真 70.4/57.9%，作者称 “comparable”；但真机
  无 baseline、无 CI，且仿真/真机的 `dynamic_costmap` 配置不同 [A]。
- **10**：30 min 时 BridgeDepth 96.3% vs RealSense 88.5%，但 5 min 时
  RealSense 吞吐更高；作者用“模型推理延迟”解释，10 min 的反转又无法用
  同一解释说明 [A/C]。
- **06**：训练/评测同一工作台、同一三相机、同一光照；“ID”格点就是训练
  网格点，78.33% 是内插而非泛化 [A/C]。

### 8.5 隐藏先验与自订 benchmark

- **09**：代码把 canonical world PCD 作为不可变 `S` 注入 belief，真机加载
  预建家具碰撞模型；论文却称 “unknown static / previously unseen layouts”
  [A]。这不是小瑕疵：它直接改变“未知环境能力”的解释。
- **11**：“Grocery Pick-and-Pack Benchmark”是作者团队 2025 年自订分级，
  不是社区 benchmark；没有独立规范页/排行榜 [A]。
- **04**：自建 2100 张单场景数据、随机 8:1:1；MineralImage5k 原始分割子集
  约 100 张，论文却称 5341 张/3 万实例并报 mask AP；掩码来源/训练协议
  未报告 [A/B]。
- **10**：Table 1 的 B 行与 Table 2/3 的 5 min 行三个指标逐位相同，高度
  可能复用同一次 5 min 试验；“1000 iterations”与 5 min ≈51 抓不一致 [A/B]。

### 8.6 代码层面的安全边界冲突

- **06**：`ros_interface.py:82-114` 直接发布 `/arm_controller/joint_trajectory`
  与 `TwistStamped`；`robot.py:128-190` 只有 `max_relative_target` 裁剪，
  没有 lease/deadman/stop latch。直接接入就是绕过 `ExecuteMotion` [A]。
- **09**：ROS 1 Noetic + Fetch 11-DoF 全身；whole-body VAMP/非完整底盘/
  pan-tilt gaze 在 ArmPi 上没有对应物 [A]。
- **10**：UR5e 开环执行 + 轨迹验证阶段放松体素碰撞 + 允许轻触邻件；在无
  e-stop/无编码器的平台不可接受 [A]。
- **01/07/08/11**：都让学习策略或规划器直接输出关节/末端/底盘动作，
  没有 JCHENG 的 lease/deadman/stop latch 语义 [A/C]。

### 8.7 算力是硬筛选器，不是软约束

- 本机 RTX 3060 Laptop **6 GB**；06 推理在 **4080 16 GB**、训练在 L40S；
  08 训练 **4×A100**、推理 4090；04 的 90 FPS 是 **RTX 5070** 桌面卡；
  10 的 SAM-6D 在 3060 上预计 **3–6 s/迭代** [A/C]。
- 450M SmolVLA 的**推理**有可能放进 6 GB，但这是 D 级假设；训练/微调
  不在本机能力范围内。任何“先微调再部署”的计划都要先解决算力。

### 8.8 相互矛盾与需要追问作者的点

- 13 的“基础模型只能离线” vs 10 的 SAM-6D 在线 600 PPH [A]。
- 09 的“unknown static” vs 代码 canonical map [A]。
- 09 的“significantly reducing collisions” vs 动态碰撞 13.9% > Nav 7.5%
  [A]。
- 11 的 Table 8（0.66 J/帧）vs Table 9（23.18 FPS、6.45 W → 0.278 J/帧）
  [A]。
- 11 的 sweet bag Wilson CI（23.1–88.2%）与 3/5 的标准 Wilson（约 31–80%）
  不一致 [A/C]。
- 04 的 Table 3/4/5/6/7 单模块数值互不一致（0.3–1.1 pp）[A]。
- 06 的论文“12 维关节状态” vs 发布数据 7 维位姿 vs 配置 9 维 [A/B]。

### 8.9 什么会改变本报告的结论

- 06 或 09 发布 **5-DoF/Humble** 分支，并在 ArmPi 级硬件上给出可复现的
  安全闭环数据；
- 任一批次论文发布**代码 + 数据 + 5-DoF 适配**，且统计报告含多种子/CI；
- JCHENG 自建 MVE 显示分割/6D 位姿/VLA 的收益超过集成成本与安全风险；
- 出现一篇在 5-DoF、无编码器、无 e-stop 平台上做真实抓取的独立论文。
在这些发生之前，**“不引入端到端系统、只做离线 MVE”** 是证据支持的决策。

---

## 09. Engineering Applicability（工程适配性）

### 9.1 分层映射

| 层 | 可借鉴的论文/组件 | 适配方式 | 主要障碍 | 建议 |
|---|---|---|---|---|
| L3 感知 | 04 的 Focaler-IoU/P2-P3 注入；11 的 RGB-only + 单像素深度；10 的位姿-深度几何拒绝/pose buffer | 在 `jcheng-perception` 的 GPU 节点做离线 A/B；不新建相机所有权 | 04 无代码/AGPL；10 无代码/SAM-6D 许可；6 GB | 先 MVE-1；MVE-2 条件执行 |
| L2/L3 操作 | 01 的有界残差语义；06 的 SmolVLA 沙箱；07 的失败分类/可达性门控；09 的行为树/可见性 pre-grasp | 只做设计/协议；运行时必须经 `ExecuteMotion` | 5-DoF/无 q̇；06 直发控制器；09 ROS1/Fetch | MVE-0 + MVE-3；不接机器人 |
| L3 移动 | 07 的底盘可达性门控；09 的碰撞按尝试归一化 | 作为 Nav2/`/cmd_vel` intent 的上层检查 | M10 未接入；无编码器 | 只写入验收协议，不改移动栈 |
| L2 系统 | 01 的“单次界≠累计界”；06 的直接 publish 反例；09 的先验披露 | 写入 `SAFETY.md`/评审清单 | 无 e-stop；bus 读无超时 | 不改代码，只加设计约束 |
| OPS | 11/09 的失败分类与 CI 报告 | 写入健康/证据格式 | 无 | 低优先级 |

### 9.2 候选组件的成本/风险

| 组件 | 来源 | 预计工作量 | 算力 | 许可 | 安全风险 | 回退 |
|---|---|---|---|---|---|---|
| 分割/抓取点 A/B | 04/11 | 1–2 周（标注 200–300 帧 + 训练/评测） | 3060 6 GB | 04 上游 AGPL；11 无代码 | 低（纯感知） | 保留当前 YOLOv8s |
| pose buffer/几何拒绝 | 10 | 2–4 周（重实现 + 5 物体 CAD + GT） | 3060 6 GB | SAM-6D 无许可 | 中（位姿错误→抓空） | 单帧 PnP/AprilTag |
| SmolVLA 沙箱 | 06 | 1–2 周（Docker/依赖/回环） | 6 GB 未验证 | Apache-2.0 | 低（不接机器人） | 不部署 |
| 失败分类协议 | 07/09 | 2–3 天（桌面） | 无 | 无 | 无 | 不适用 |
| 5-DoF 动作重映射 | 06 | 2–4 周（改 config/动作空间 + 仿真） | 6 GB | Apache-2.0 | 高（若接机器人） | 仅仿真 |
| 全景/双臂/全身栈 | 08/09 | 数月 + 新硬件 | A100/4090 | 08 无代码 | 极高 | 不做 |

### 9.3 与现有架构的兼容性

- **契约**：本批次不要求改 `jcheng-interfaces`；所有建议在现有
  `ExecuteMotion`/lease/stop latch 语义内。
- **DDS**：所有离线 MVE 使用域 77（合成）或独立域，不加入 0/41/42；
  06 的 ROS 2 Jazzy 节点不得与机器人 Humble 图混跑。
- **相机所有权**：10/11 都假设单一相机；JCHENG 的 D435i 由感知进程独占
  （ADR-0004），任何新模型只能消费已发布的图像/检测，不能另开设备。
- **状态真值**：01/06/09 都依赖关节/末端状态；JCHENG 必须用总线读回
  （`GetBusServoState`）或明确标注“命令缓存”，不能把 `/joint_states`
  当测量。

### 9.4 失败后的回退

- 所有感知/模型实验以**旁路**方式接入：新模型输出与现有 YOLO/PnP 并行，
  用 feature flag 选择；失败即切回现有管线。
- 任何 VLA/6D 位姿结果在进入 `ExecuteMotion` 前必须经过：工作空间盒、
  5-DoF IK 可行性、速度/加速度限幅、lease、deadman、stop latch。
- 实机运动仍需**逐次操作员授权**；MVE-1/2/3 都不产生运动。

---

## 10. Recommended Approach（推荐方案）

### 10.1 推荐：现在做（不动机器人）

1. **MVE-0 失败分类（桌面，2–3 天）**：用 07 的三类失败框架 + 09 的
   执行/系统/规划分类，标注 JCHENG 现有失败日志（manipulation 24-pair、
   perception fixed-point、ops incident）。产出“我们的首要瓶颈”排序。
   这是所有后续投入的前置条件。
2. **MVE-1 分割/抓取点 A/B（离线，1–2 周）**：在现有 D435i/Aurora 数据上
   比较当前 YOLOv8s + 深度反投影 vs YOLO11-seg（或 04 的 Focaler/P2-P3
   重实现）。指标：mask mAP、3D 质心误差、时序抖动、p95 延迟、显存。
3. **MVE-3 SmolVLA 6 GB 沙箱（离线，1–2 周）**：用 06 的 Apache-2.0 栈
   在笔记本 Jazzy/域 77 上做纯回环，测峰值显存、p50/p95 延迟、10 min
   稳定性；**不接机器人、不接 DDS 0/41/42**。
4. **采纳为协议（零成本）**：
   - 小样本报告必须给 n、Wilson/配对 CI、仿真/真机分开（11/09）；
   - 失败分类 + 碰撞按尝试次数归一化（07/09）；
   - 任何“未知环境”主张必须披露静态先验（09 的 canonical map 教训）；
   - VLA 上线前必须做颜色/纹理反事实测试（06）。

### 10.2 条件执行：只有前置通过才做

- **MVE-2 6D 位姿 + pose buffer（2–4 周）**：仅当 MVE-1 通过、目标物体有
  CAD、且 SAM-6D 许可解决（或换 FoundationPose/自研）时做。先在 5 个已知
  物体、D435i、离线数据上测 ADD(-S)/旋转误差/时序抖动/单帧耗时；不接
  机器人。若 3060 上 >5 s/迭代或 OOM，直接停止。
- **5-DoF VLA 动作重映射（2–4 周）**：仅当 MVE-3 通过且 06 的 6-DoF
  动作空间能在仿真中降维（如 xyz+yaw+gripper）时做；仍只在仿真，不接
  机器人。
- **感知层集成**：仅当 MVE-1 的收益（≥5% mAP 或 −20% 质心误差）稳定、
  且不超过 50 ms p95 时，才以旁路 feature flag 接入 `jcheng-perception`。

### 10.3 不推荐/推迟（附理由）

| 方案 | 理由 | 证据 |
|---|---|---|
| 直接接入 06 的 ROS2SmolVLA | 6-DoF 动作空间、Jazzy、直接 publish 控制器，绕过 `ExecuteMotion` | A（源码/README） |
| 移植 09 的 Visibility-Aware 运行时 | ROS 1 Noetic + Fetch 11-DoF 全身；ArmPi 无底盘/躯干/pan-tilt | A（仓库/论文） |
| 采用 08 PanoVLA | 双 6-DoF 臂 + 全景 + 4×A100；仓库为空；6 GB 不足 | A/C |
| 采用 01 的残差 RL 运行时 | 6-DoF + 12 维 q/q̇；无编码器平台无法提供状态；仿真增益在噪声内 | A |
| 采用 03 的动态定位 | 依赖编码器/输送带；ArmPi 无编码器、无皮带 | A |
| 采用 10 的 600 PPH/96–99% 作为指标 | UR5e 6-DoF 开环 + 放松碰撞；Table 1/2 疑似复用；无代码/CAD | A/B |
| 采用 11 的 92%/能效排名 | n=5/类、无 baseline、自订 benchmark、能耗口径不一致 | A |
| 把 13 当技术依据 | 叙事综述、无定量综合、关键文献缺失、结论被 10 推翻 | A |
| 现在训练/微调 VLA | 6 GB 不足；无演示数据；无 5-DoF 动作空间；无安全闭环 | A/C |

### 10.4 工程实施路径（建议顺序）

```text
Phase 0（2–3 天，桌面）
  └─ MVE-0 失败分类 + 评测模板（n/CI/仿真-真机分开）

Phase 1（2–3 周，离线，不动机器人）
  ├─ MVE-1 分割/抓取点 A/B（3060 6 GB）
  └─ MVE-3 SmolVLA 沙箱（Jazzy/域 77，纯回环）

Phase 2（条件触发，2–4 周）
  ├─ 若 MVE-1 通过：感知旁路集成（feature flag）
  ├─ 若 MVE-3 通过：5-DoF 动作重映射（仅仿真）
  └─ 若 MVE-1 + CAD + 许可：MVE-2 6D 位姿（离线）

Phase 3（实机，逐次授权）
  └─ 只在 Phase 2 全部通过、且 system 层完成 lease/deadman/限幅/stop
     latch 评审后，才讨论实机；本批次不授权任何运动。
```

### 10.5 与现有路线的关系

- **不换栈**：继续用现有 YOLO + 深度 + PnP/AprilTag + 脚本化抓取；
  这批论文没有证明换栈的收益超过集成成本。
- **先补可观测性**：失败分类、时间同步、标定残差、总线读回，比换模型
  更能解释当前 24/24 之外的失败。
- **VLA 只做沙箱**：06 是唯一可克隆的 VLA 栈，但它的价值是“验证 450M
  在 6 GB 上的可行性”，不是“马上上机器人”。
- **安全边界不变**：所有运动仍只经 `jcheng-system` 的 `ExecuteMotion`；
  本报告不建议任何绕过 lease/deadman/stop latch 的形态。

---

## 11. Experimental Design（实验设计）

> **状态：全部未执行。** 以下是预注册式设计，不是已完成的实验；没有任何
> 机器人运动授权。MVE-0/1/2 为离线/桌面，MVE-3 为纯回环沙箱。

### 11.1 MVE-0 — 失败分类与瓶颈排序（桌面）

| 项 | 内容 |
|---|---|
| **假设** | 现有失败日志中 ≥80% 可归入 07 的“规划/导航-底盘/局部操作”三类与 09 的“执行/系统/规划”三类；首要瓶颈可转成一个可测假设。 |
| **Baseline** | 当前无统一分类（按会话/现象零散记录）。 |
| **自变量/控制变量** | 分类框架（07/09 合并）；控制：同一批日志、同一标注人两次间隔 ≥24 h。 |
| **环境** | 桌面；现有 `jcheng-manipulation` 24-pair 记录、`jcheng-perception` fixed-point 记录、`jcheng-ops` incident 记录；不接机器人。 |
| **指标** | 分类覆盖率；两次标注的 Cohen's κ；top-3 瓶颈的频次与可测试性。 |
| **验收** | 覆盖率 ≥80%，κ≥0.6，top-1 瓶颈能写出一个 MVE-1/2/3 式假设。 |
| **失败判据** | >30% 无法分类，或 κ<0.4；停止，先补日志字段。 |
| **记录** | CSV：episode_id、阶段、症状、主类/子类、置信度、证据路径、备注。 |
| **回退** | 无（不改变系统）。 |

### 11.2 MVE-1 — 分割/抓取点稳定性 A/B（离线，3060）

| 项 | 内容 |
|---|---|
| **假设** | 实例分割（YOLO11-seg，可选 Focaler/P2-P3）相对当前 YOLOv8s 检测，在同批 D435i/Aurora 帧上把 3D 质心误差或时序抖动降低 ≥20%，且 p95 ≤50 ms、峰值显存 ≤5 GB。 |
| **Baseline** | 当前 `jcheng-perception` 的 YOLOv8s 检测 + 深度反投影；同一批帧、同一深度、同一标定。 |
| **自变量/控制变量** | 模型（当前 vs YOLO11-seg vs 可选 Focaler/P2-P3）；控制：帧、物体、距离、光照、标注、评测脚本。 |
| **环境** | 离线；200–300 帧，10 个桌面物体，3 个距离（0.3/0.5/0.8 m），2 种光照；D435i 与 Aurora 各半；不动机器人。 |
| **指标** | mask mAP50-95；3D 质心误差（mm，按深度 GT）；时序抖动（mm/frame）；p50/p95 延迟；峰值显存；当前类别回归。 |
| **验收** | mAP +5% 或质心误差 −20%；p95 ≤50 ms；峰值 ≤5 GB；当前类别不下降 >1%。 |
| **失败判据** | 增益 <2%，或 p95 >80 ms，或 OOM；保留当前管线。 |
| **记录** | 每帧 CSV（模型、帧 id、物体、距离、光照、mask IoU、质心误差、延迟、显存）；模型/配置哈希。 |
| **回退** | 旁路 feature flag；失败即切回 YOLOv8s。 |

### 11.3 MVE-2 — 6D 位姿 + pose buffer（离线，条件执行）

| 项 | 内容 |
|---|---|
| **假设** | 在 5 个已知物体上，SAM-6D + 多视角 pose buffer 相对单帧 PnP/AprilTag 把 ADD(-S) 降到 ≤5 mm、时序抖动降低 ≥30%，单次迭代 ≤2 s。 |
| **Baseline** | 当前 PnP/AprilTag 单帧位姿；同一批图像/深度/标定。 |
| **自变量/控制变量** | 位姿估计器（SAM-6D vs 当前）；buffer 开/关；视角数；控制：物体、光照、箱型、GT。 |
| **环境** | 离线；5 个有 CAD 的物体 × 20 视角 × 3 种摆放；D435i；GT 用 AprilTag/卡尺；不动机器人。 |
| **指标** | ADD(-S)（mm）、旋转误差（°）、时序抖动、单次迭代耗时、峰值显存、pose buffer 接受/拒绝率。 |
| **验收** | ADD(-S) ≤5 mm、抖动 −30%、≤2 s/迭代、≤5.5 GB；SAM-6D 许可已解决。 |
| **失败判据** | ADD(-S) >10 mm，或 >5 s/迭代，或 OOM，或许可未解决；停止，不集成。 |
| **记录** | 每视角位姿、buffer 关联/拒绝原因、GT、耗时、显存；代码 commit。 |
| **回退** | 不接入；保留当前 PnP/AprilTag。 |

### 11.4 MVE-3 — SmolVLA 6 GB 回环沙箱（离线，不接机器人）

| 项 | 内容 |
|---|---|
| **假设** | SmolVLA 450M 在 RTX 3060 Laptop 6 GB 上可加载并稳定运行 ≥10 min，p95 ≤150 ms/chunk；6-DoF 动作空间可通过屏蔽一维得到合法的 5-DoF 目标。 |
| **Baseline** | 无策略；只测“能否加载/延迟/显存”，不与论文成功率比较。 |
| **自变量/控制变量** | 精度（bf16/fp16）、chunk size、相机路数（1/3）、输入分辨率；控制：容器、驱动、功耗模式。 |
| **环境** | 笔记本 ROS 2 Jazzy + Docker；DDS 域 **77**（合成）；回放/模拟图像；**不连机器人、不连域 0/41/42、不发运动**。 |
| **指标** | 峰值显存；p50/p95 延迟；chunk 速率；10 min 稳定性；5-DoF 重映射后的目标是否通过 IK/限位检查（仿真）。 |
| **验收** | 峰值 ≤5.5 GB；p95 ≤150 ms；10 min 无 OOM；重映射在仿真中产生合法目标。 |
| **失败判据** | OOM，或 p95 >300 ms，或 10 min 内崩溃；停止，不进入 Phase 2。 |
| **记录** | `nvidia-smi` 采样、时间戳、容器 digest、配置、失败日志。 |
| **回退** | 不部署；沙箱可随时删除。 |

### 11.5 共同约束

- 所有 MVE 都不产生机器人运动；Phase 3 的实机实验需要**逐次操作员授权**，
  且只能经 `ExecuteMotion`。
- 所有 MVE 的报告必须含：n、均值/CI、失败判据、原始日志路径、代码/模型
  哈希；不得把仿真/回环结果写成硬件验证。
- MVE-1/2 的数据若来自现有证据，必须记录采集日期、相机、标定版本；
  不得混用不同标定。

---

## 12. Limitations & Uncertainties（局限与不确定性）

### 12.1 批次不完整

- 用户目录中有 13 个编号，实际可读 **10 篇**；**02、05、12 未获取**：
  - 02：DOI `10.1002/rob.70324` 返回 403；
  - 05：期刊页要求手动下载（`cjournal.hep.com.cn`，DOI 10.3799/dqkx.2026.057）；
  - 12：ScienceDirect 手动下载（`S0921889026002988`）。
  本报告不对这三篇做任何判断；批次结论只适用于 10 篇。
- 11、13 未在用户消息内联附件中出现，但在同一目录且下载报告标记成功；
  本报告按“批次文件”处理，并在来源记录中注明。若用户只想覆盖 8 篇，
  11/13 的结论可单独剔除，不影响“0/8 可部署”的主结论。

### 12.2 阅读范围

- 10 篇 PDF 全文已读；但**补充材料/附录**未单独获取（07 的附录 A–L 在同一
  PDF 内已读；08/09 的附录未单独获取；04/10/11 无补充材料）。
- 部分图表数字是**读图**获得（10 的 Figure 8/9、11 的 Figure 9），已在来源
  记录中标“≈/读图”，不作为精确报告值。
- 未做系统检索（本批次是用户给定选集），因此不能声称“某方向没有更好
  工作”；只可以说“这 10 篇中没有”。

### 12.3 未执行的验证

- **未运行任何论文代码**；06/09 只做静态阅读，未构建、未训练、未推理。
- **未连接机器人**；没有 S 级证据；所有“实机有效”都是作者报告。
- 未独立复现任何统计（除本报告明确标注的二项/Wilson/Fisher 复算）。
- 未做硬件在环、DDS 跨域、时间同步、功耗/热测试。

### 12.4 推断与不确定项

- 04 的“相邻帧泄漏”、10 的“Table 1 复用 5 min run”、08 的“容量/预训练
  混淆”、11 的“Jetson 只测 CPU”均为**推断**，已在正文标 B/C；它们需要
  作者数据或代码才能证实。
- 09 的 canonical map 是**代码事实**（A），但“论文是否故意隐瞒”是推断；
  本报告只陈述“正文未披露”，不评价动机。
- 06 的 184 次试验是由百分比反算（10/6 的整数倍），不是论文明确数字；
  标 C，尽管四点精确吻合。
- 算力估算（10 的 3–6 s/迭代、08 的 6–8 GB 权重、04 的 3060 FPS）都是
  C 级推断，未实测。

### 12.5 证据边界

- 07/08/09 是 arXiv 预印本，未同行评审；06 是 Procedia 校样（卷期页未定）；
  01/03/04/10/11/13 是期刊论文，但 MDPI 的审稿深度/统计要求不一。
- 未评估引用数、独立复现、撤稿/更正记录；Web 检索受 2026 年文献可检索性
  限制。
- 未评估论文作者的长期维护承诺；06 的仓库最后推送 2026-11-17，09 为
  2026-09-28，07/08 基本停滞。
- “代码不存在”不等于“方法无效”；“论文数字不可复现”不等于“方法在别的
  平台上无效”。本报告的拒绝建议是**工程决策**，不是对论文科学价值的
  终审。

### 12.6 需要什么才能关闭这些缺口

- 02/05/12 的全文；
- 06 在 5-DoF/Humble 上的适配与 6 GB 实测；
- 09 在非 Fetch、非 ROS 1 平台上的移植数据；
- 10 的代码/CAD 与 30 次 run 原始数据；
- 11 的逐 trial 日志与 Jetson GPU 数据；
- 01/03/04 的代码、数据与训练配置；
- 07/08 的代码、checkpoint、prompt 与 episode seed；
- 任何一篇在 ArmPi Ultra 级硬件上的独立复现。

---

## 13. References（参考）

> 访问日期均为 2026-11-25。论文全文来自本地 PDF；DOI/arXiv 与仓库元数据
> 已用 doi.org/Crossref、arXiv abs、GitHub REST API 核对。本地 PDF **未纳入
> git**（第三方版权 + 本仓库 5 MB 门禁）。

### 13.1 论文

1. Wang, H.; Wu, G.; Yang, Q.; Yang, J. *Sensor-Guided Intelligent Strategy
   Optimization for Robot-Assisted Grasping in Complex Coal Gangue
   Environments*. **Sensors** 2026, 26(22), 7230.
   <https://doi.org/10.3390/s26227230>
2. Ye, Z.; Bohao, C.; Peng, W.; Yuanhao, Z.; Kexiang, M.; Hongwei, M.;
   Xudong, W.; Jiahui, L. *A dynamic visual localization method for intelligent
   coal gangue sorting robots*. **Scientific Reports** 2026, 16, 38110.
   <https://doi.org/10.1038/s41598-026-71502-5>
3. Chen, M.; Liu, Y.; Si, L.; Wang, X.; Gu, J. *GLD-YOLO: An Ore Instance
   Segmentation Algorithm for Underground Crushing Scenes*. **Machines** 2026,
   14(7), 731. <https://doi.org/10.3390/machines14070731>
4. Mandischer, N.; Böckmann, N.; Holl, L.; Mikelsons, L. *ROS2SmolVLA:
   Enabling Small Vision-Language-Action Models for Integration into
   Industrial-Grade Lightweight Robots*. **Procedia Computer Science** 2026
   （校样；8th International Conference on Industry of the Future and Smart
   Manufacturing）. arXiv:2608.23320v1.
   <https://arxiv.org/abs/2608.23320>
5. Wang, Z.; Li, J.-N.; Tang, Y.; Yu, Y.; Wu, B.; Fang, M.; Li, X.; Zhong, Y.
   *Cracking Mobile Manipulation: From Failure Diagnosis to Agentic Robot
   System*. arXiv:2610.19600v1 [cs.RO], 2026-10-14.
   <https://arxiv.org/abs/2610.19600>
6. Yang, D.; Chen, H.; Chen, X.; Liu, L.; Li, M.; Tu, C.; Xu, K.; Ma, X.;
   Liu, S. *Learning Panorama-Aware VLA for Mobile Manipulation with
   Whole-Body Teleoperation*. arXiv:2608.02257v1 [cs.RO], 2026-08-03.
   <https://arxiv.org/abs/2608.02257>
7. Hu, T.; Xiao, A.; Hsu, D.; Zhang, H. *Visibility-Aware Mobile Grasping in
   Dynamic Environments*. arXiv:2605.02487v5 [cs.RO], 2026-10-26.
   <https://arxiv.org/abs/2605.02487>
8. Tarsi, A.; Mastrogiuseppe, M.; Taliani, S.; Cortinovis, S.; Pattacini, U.
   *Pickalo: Leveraging 6D Pose Estimation and Deep Stereo Matching for
   Industrial Bin Picking*. **Robotics** 2026, 15(10), 197.
   <https://doi.org/10.3390/robotics15100197>；预印本
   <https://arxiv.org/abs/2604.04690>
9. Mansakul, T.; Tang, G.; Webb, P.; Rice, J.; Oakley, D.; Fowler, J.
   *A Complete Grocery Pick-and-Pack Application Using a Computationally
   Lightweight Vision-Based Mobile Manipulator*. **Sensors** 2026, 26(9), 2860.
   <https://doi.org/10.3390/s26092860>；前作/自订 benchmark：
   **Sensors** 2025, 25(17), 5309. <https://doi.org/10.3390/s25175309>
10. Han, Y.; Zhang, F. *Review of Research on 3D Vision-Based Robotic System
    for Unstructured Bin-Picking*. **Applied Sciences** 2026, 16(22), 11254.
    <https://doi.org/10.3390/app162211254>

### 13.2 代码、项目页与数据

- **06 ROS2SmolVLA**（Apache-2.0）：
  - <https://github.com/una-auxme/ros2smolvla_docker> @ `92d3d1c43bf5`
  - <https://github.com/una-auxme/ros2smolvla_interface_lerobot> @ `470be64b38b5`
  - <https://github.com/una-auxme/ros2smolvla_interface_camera> @ `6da3f71b0c4f`
  - <https://github.com/una-auxme/ros2smolvla_ur10e_real>
  - <https://github.com/una-auxme/ros2smolvla_ur10e_sim>
  - 项目页：<https://una-auxme.github.io/en/projects/ros2smolvla/>
  - 模型/数据：Hugging Face `una-auxme/ROS2SmolVLA_ur10e_no_joints_crop_pick_place`、
    `una-auxme/eval_ROS2SmolVLA`
- **09 Visibility-Aware**（MIT）：
  <https://github.com/AdaCompNUS/Visibility-Awared-Mobile-Grasping> @
  `c37eb1638f66`；项目页
  <https://visibility-aware-mobile-grasping.github.io/>。
- **07 Cracking**（Apache-2.0，占位）：
  <https://github.com/PKU-VaLuE-Lab/Cracking-Mobile-Manipulation> @
  `2702ab119840`。
- **08 PanoVLA**（Apache-2.0，空仓库）：
  <https://github.com/puffyyy/panovla> @ `e160ea0607d6`。
- **10 Pickalo**：项目页 <https://mesh-iit.github.io/project-jl2-camozzi/>；
  依赖 **SAM-6D** <https://github.com/JiehongLin/SAM-6D>（无 LICENSE）、
  **BridgeDepth** <https://github.com/aeolusguan/BridgeDepth>（MIT）。
- **04 GLD-YOLO**：无代码；上游 **Ultralytics YOLO11**
  <https://github.com/ultralytics/ultralytics>（AGPL-3.0）。
- **01/03/11/13**：无代码/项目页；数据声明见各来源记录。

### 13.3 本地 PDF（未入库）

| 文件 | 页数 | 字节 |
|---|---|---|
| `01_Coal_Gangue_Grasping.pdf` | 25 | 11,861,337 |
| `03_Dynamic_Visual_Localization.pdf` | 13 | 3,423,072 |
| `04_GLD_YOLO.pdf` | 23 | 6,095,034 |
| `06_ROS2SmolVLA.pdf` | 10 | 2,764,225 |
| `07_Cracking_Mobile_Manipulation.pdf` | 30 | 9,495,096 |
| `08_PanoVLA.pdf` | 8 | 8,142,289 |
| `09_Visibility_Aware_Mobile_Grasping.pdf` | 8 | 56,242,903 |
| `10_Pickalo.pdf` | 15 | 7,565,042 |
| `11_Lightweight_Mobile_Manipulator.pdf` | 35 | 27,688,328 |
| `13_3D_Bin_Picking_Review.pdf` | 29 | 14,200,842 |

目录：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/`。未获取：02、05、12
（见 §12.1）。

---

## Appendix A — 提交前自审（critical self-review）

> 本节记录本报告在提交前发现并修正的问题，以及仍然存在的偏差。自审只代表
> 同一研究代理的二次检查，不等于独立评审。

### A.1 已修正的问题

1. **04 的“消融表全模块行矛盾”是误读，已删除。** 初稿代理把 Table 3 的
   三模块行（C3k2+C2PSA+PAFPN，96.7/80.8）当成“四模块全开”，并据此指控
   “全模块 96.7 vs 主表 98.1”。渲染原页 p.16 后确认：四模块全开行是
   98.1/82.3，与 Table 2 一致；96.7 行没有 Focaler。最终记录只保留**真实**
   的跨表单模块差异（0.3–1.1 pp），不保留错误指控。
2. **08 的“无代码仓库”已修正为“仓库存在但为空”。** GitHub 检索到
   `puffyyy/panovla`（Apache-2.0，created 2026-11-24，tree 0 files）；
   这比“未找到”更精确，也避免把“空仓库”误写成“没有仓库”。
3. **07 的“Kimi K3 2.8T 参数/价格”已删除。** 该数字来自外部二手来源，
   论文未写；最终记录只保留“Kimi K3/Gemini 3.5 Flash/Qwen3.8-27B，
   token/延迟/费用未报告”，避免把未验证的外部信息混入论文事实。
4. **11 的 CI/能效指控已分级。** 92% 的 Wilson 区间 [75.1,97.8] 复算正确；
   sweet bag 的 [23.1,88.2] 与 3/5 的标准 Wilson（约 31–80）不一致，标为
   “表格异常（推断）”；Table 8/9 的 GPU 每帧能量 0.66 vs 0.278 J 是**原表
   可直接复核的矛盾**，保留为 A 级；能耗口径不一致保留为 A/B。
5. **01 的 GitHub 检索对象修正。** 初稿在 01 记录里误写搜索 “GLD-YOLO”；
   最终记录只写 `coal gangue grasp`，并删除无关检索。
6. **09 的 canonical map 指控已从“推断”升级为“代码事实”。** 直接读取
   `run_maniskill_benchmark.py:156-171`、`scene.py:13/161-162`、
   `real_fetch.yaml:6` 后确认；报告只陈述“正文未披露”，不评价作者动机。
7. **10 的 Table 1/2 复用保留为 B 级。** 三个指标逐位相同是事实，但“同一
   次 5 min run”是推断；报告用“高度可能/疑似”，不写成已证实。
8. **11 的“30.9 MB 小于 GraspNet”按字面纠正。** GraspNet 模型 7.2 MB，
   总内存 425 MB；论文的表述只有在“总内存”语境下成立。

### A.2 仍然存在的偏差

- **选择偏差**：本批次是用户给定选集，不是系统检索；我们可能漏掉更适合
  5-DoF/无编码器平台的论文。报告已把“0/10”限定为“这 10 篇中”，没有
  推广为“文献中没有”。
- **负面证据权重较高**：报告重点审查可复现性/统计/平台匹配，可能相对
  低估论文的工程启发价值。我们在 §10 仍保留了 10 的 pose buffer、11 的
  RGB-only 前端、06 的沙箱等可借鉴项，以平衡。
- **MDPI  venue 偏见检查**：没有因 MDPI 直接降级；04/11 的问题都落在
  具体方法/数据/报表，而不是“因为是 MDPI”。01 的自我限定反而被肯定。
- **代码审计深度不均**：06/09 读了源码；07/08 只读 tree/README；10/04
  只读论文/项目页。报告已标“静态分析/未运行”，没有把 README 当实现。
- **图读数字**：10 的 Figure 8/9、11 的 Figure 9 是读图，已标“≈/读图”；
  不用作精确结论。
- **未做独立评审**：本自审不能替代他人评审；报告状态标
  “reviewed (self-review only); independent review pending”。

### A.3 自审清单（对应 AGENTS.md §12）

| 检查项 | 结论 |
|---|---|
| 是否存在确认偏误？ | 有风险（负面证据权重高）；已用“可借鉴项”与“什么会改变结论”平衡。 |
| 是否遗漏明显替代方案？ | 已列“继续现有 YOLO+PnP+脚本抓取”作为更简单替代；未发现第 11 篇可直接替代的 5-DoF 论文。 |
| 是否混淆相关性与因果？ | 09 的 canonical map 与性能只陈述“先验被隐藏”，不声称因果；01 的真机提升保留替代解释。 |
| 是否存在未经验证的技术假设？ | 6 GB 可跑 SmolVLA、3060 上 SAM-6D 3–6 s、08 权重 6–8 GB 均标 C/D；未写成事实。 |
| 是否过度解读论文结果？ | 所有头条数字都附 n/平台/仿真或真机语境；没有跨论文排名。 |
| 是否把 README 当实现？ | 06/09 读了源码；07 明确“README 说 Coming soon，实际无代码”；08 空 tree。 |
| 是否存在虚构引用/链接/结果？ | DOI/arXiv/GitHub 均已核对；没有编造数字；未获取的 02/05/12 明确标注。 |
| 推荐是否真正适合当前项目？ | 只推荐离线 MVE + 协议；没有推荐任何端到端运行时；所有运动仍经 `ExecuteMotion`。 |
| 结论是否足以指导下一步？ | 是：MVE-0/1/3 有假设、baseline、指标、验收/失败判据、记录与回退。 |

### A.4 自审结论

报告从“draft”升级为 **reviewed（self-review only）**；独立评审仍未做。
在上述偏差与未获取材料的范围内，结论“**现在不引入端到端系统；先做
MVE-0/1/3，MVE-2 条件执行**”有可追溯证据支撑，且不依赖任何单篇论文的
作者自评。
