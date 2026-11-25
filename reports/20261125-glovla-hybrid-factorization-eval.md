# GloVLA 评估：几何搬运 + 局部 VLA 的分解能否迁移到 JCHENG ArmPi Ultra？

> 报告状态：**reviewed（self-review only；独立评审 pending）**。日期：2026-11-25。
> 作者：ZCode（研究代理），for J. Cheng。评审：自查（附录 A）；独立评审未做。
> 本报告影响的决策：是否、以及以何种形式，把 GloVLA 的“几何搬运 + 局部 VLA”
> 分解纳入 JCHENG 技术路线；是否为它准备演示数据与 GPU 算力。
> 研究主题：GloVLA（Geometry + Local VLA）的混合操作框架，及其在 JCHENG
> ArmPi Ultra 生态中的技术评估与迁移可行性。
> 研究边界：GloVLA 全文（9 页，含表/图）已读；**无公开代码、无数据集、无
> LIBERO-Challenge 场景**；本机 GPU 为 RTX 3060 Laptop **6 GB**，无法加载论文的
> 四个 backbone；无机器人访问与运动授权，未执行任何策略或实机评测；外部文献
> 以 arXiv 摘要/官方 README 为主，部分只读摘要。MVE-0 是桌面复算（S），不是
> 机器人实验，也不是 checkpoint 复现。
> 排版文档：[DOCX](20261125-glovla-hybrid-factorization-eval.zh-CN.docx)（中文；
> 可追溯版本以本 Markdown 为准）。

**证据等级**：**S** 在本机复现（本报告仅指桌面几何/算术复算）· **A** 一手论文、
源码或官方文档 · **B** 可信二手证据 · **C** 基于现有证据的推断 · **D** 未验证假设。

---

## 01. Executive Summary（执行摘要）

**推荐：现在不引入 GloVLA 运行时。** 保留 JCHENG 现有的“几何/标定 + 模型化
抓取”管线；把论文的三项资产作为可立即采纳的工程输入：

1. **handoff 误差预算**（Eq. 12）：`ε + η + ||δ||₂ ≤ r`，作为任何未来
   “几何搬运 → 学习型局部策略”交接的设计门禁；
2. **分级扰动评测协议**：clean + 单扰动 + 2–3 组合 + 4–5 组合，固定官方成功
   判据，报告逐场景成功率与区间；
3. **演示数据的阶段标注 schema**：抓取/放置片段、物体与容器中心、夹爪指令与
   观测状态、时间戳与标定版本。

如果目标从“39.4 mm 方块”扩展到“多物体/语言条件”，先在仿真里用 **ACT/DP3
量级的小策略**做 MVE-1，不要从 π0/GR00T 起步。**不要在本机 6 GB 上尝试论文的
四个 backbone；不要在没有任何演示数据前搭 VLA 栈。**

支撑这个结论的三条硬事实：

1. **算力硬约束。** 本机 `nvidia-smi` 实测 **6144 MiB**；openpi 官方要求 π0/π0.5
   推理 **>8 GB**、LoRA 微调 **>22.5 GB**、全量微调 **>70 GB**；GR00T 主
   README（N1.7）要求推理 **16 GB+**、微调 **40 GB+**，N1.6 为 **3B** 参数
   （N1.6 branch 未单列 VRAM）。论文的仿真评测在 **RTX 5090 32 GB** 上完成；
   真实机器人表 VI 的 **28.2 s** 未注明统计单位与推理硬件（本报告按 episode
   总推理时间理解，C 级）。按官方要求，本机 6 GB 无法加载这些 backbone；
   官方文档未给出 4-bit/量化路径 [A/C]。
2. **动作空间/运动学硬约束。** 论文的接口是 LIBERO 的 **7D OSC pose delta**
   （6 维位姿增量 + 1 维夹爪），transport controller 只调位置、保持进入模式时的
   姿态。ArmPi 是 **5-DoF + 夹爪**，不能到达任意 6D 位姿；`PTP` 可用，固定姿态的
   直线 `LIN` 会 `NO_IK_SOLUTION`。因此“不改变 action space”在 ArmPi 上不成立，
   必须改动作空间或加重定向层 [A]。
3. **数据硬约束。** 论文的“no additional demonstrations”是指**复用原始 full-task
   演示**，不是零演示；仿真每任务 10–50 条，训练用 **8×A100 80 GB**，局部策略还是
   **两个独立训练的网络**（πg、πp）。JCHENG 当前**没有演示数据集、没有动作标签、
   没有 VLA 运行时**；现有证据来自脚本化/模型化管线 [A]。

**反方证据也必须记录**：论文在真实 UR10e 上把总成功率从 **35.6% 提到 90.0%**，
推理时间从 **60.1 s 降到 28.2 s**（2.13×）；在四个 backbone 上 clean LIBERO 不降
反升。这说明“把可重复的 free-space transport 从学习策略里拿掉”是一个**真实且
方向正确**的工程 insight。它首先是对 JCHENG 现有“几何 + 模型化局部交互”架构的
**支持证据**，而不是替换现有架构的理由 [A]。

**主要风险**：把论文的 88.5%/90.0% 当作 JCHENG 的预期；在没有数据、算力和
5-DoF 动作空间适配的情况下先搭 VLA 栈，最后得到一个无法验证、也无法安全上机的
演示。**本报告的核心否定结论（现在不可部署）是 A 级（π0 官方 >8 GB + 本机
实测；GR00T N1.6 的 VRAM 未官方给出，按 C 级保守处理）；对论文因果归因的
怀疑是 C 级；对 JCHENG 任务成功率的任何预测都是 D 级。**

---

## 02. Research Questions（研究问题）

### 2.1 任务书（按用户模板填写）

**研究主题**：GloVLA——用几何 transport controller 把末端送到 interaction-centric
handoff 区域，再用局部 VLA 策略完成抓取/放置的混合操作框架——在 JCHENG
ArmPi Ultra 上的技术评估与迁移可行性。

**项目背景**：`~/jcheng` 是多仓库生态（非单一 git 仓库）。L2 `jcheng-system`
是唯一运动入口（`ExecuteMotion`、lease、deadman、stop latch、只读遥测、MoveIt
plan-only）；L3 `jcheng-perception` 在 Pi 5 上做采集/深度/TF/融合，在笔记本
RTX 3060 上跑 YOLO；`jcheng-manipulation` 是冻结的 `v1.0.0` 基线（5-DoF 标定、
手眼、MoveIt/Pilz PTP、S-curve、总线实测完成、24/24 方块抓取）；L1
`jcheng-interfaces` 定义跨仓库契约。硬件是 ArmPi Ultra：Pi 5 8 GB、5-DoF
总线舵机臂 + 两指夹爪、腕部 Aurora 930 RGB-D + 底盘前 D435i、无编码器/IMU/
e-stop/抱闸；机器人 ROS 2 Humble，主机 Jazzy；DDS 域 0/41/42/43。

**核心研究问题**：在 5-DoF、6 GB 笔记本 GPU、零演示数据、`ExecuteMotion` 安全
边界的约束下，GloVLA 的分解能否兑现论文声称的鲁棒性/效率收益？哪些组件可以
迁移，哪些不能？需要什么最小证据才能采纳？

**约束条件**：
- 计算：本机 RTX 3060 Laptop **6 GB**；Pi 5 无 CUDA；无 A100/H100 集群。
- 运动学：5-DoF + 夹爪；不能任意 6D；`PTP` 可用、`LIN` 常失败；无力矩传感。
- 数据：无演示集、无动作标签、无语言指令集；只有脚本化/Studio 运行记录。
- 架构：运动只能经 `ExecuteMotion`；能力模块不得直发厂商话题、不得打开设备；
  MoveIt 只规划；域 0 厂商、41 特权、42 能力、43 仿真。
- 安全：无 e-stop/抱闸/独立编码器/自碰撞模型；每次实机运动需单独授权；软件
  停止不是急停；`/joint_states` 是命令缓存，完成判定靠总线读。
- 交付：报告、实验设计、可追溯来源；不产出可被机器人加载的代码。

**调研要求**：自主制定计划、动态调整检索；读论文正文与仓库核心源码；主动找
反例/失败案例/替代路线；不预设结论；优先真实工程环境；不限制轮数，以证据充分
性和边际收益为停止依据；关键结论可追溯；未验证内容明确标注；给出选型建议、
实施路径与实验验证方案；提交前做批判性自审。

### 2.2 子问题

- **RQ1**：论文的分解在受控基准上是否真实优于 full VLA？证据强度、统计可靠性、
  混淆因素是什么？
- **RQ2**：在 JCHENG 的 5-DoF/6 GB/零演示约束下，哪些组件可迁移？哪些不可？
- **RQ3**：如果要做最小验证，最便宜、最能证伪的实验是什么？
- **RQ4**：安全与架构边界是什么？哪些路径绝对不能走？

### 2.3 交付物与范围外

交付物：本报告 + `experiments/20261125-glovla-handoff-budget/` 的 MVE-0 桌面
复算 + MVE-1/2/3 设计。范围外：不实现 GloVLA、不训练策略、不调用机器人、
不修改任何产品仓库、不复制厂商代码/权重。

---

## 03. Current System Analysis（当前系统分析）

### 3.1 仓库与版本

| 仓库 | 当前 SHA / 标签 | 角色 | 与本决策直接相关的事实 |
|---|---|---|---|
| `jcheng-system` | `36027d2`（`deploy/armpi-ultra-20261125`） | L2 特权运行时 | 唯一运动入口 `ExecuteMotion`；lease/deadman/stop latch；状态新鲜度 0.5 s；MoveIt plan-only |
| `jcheng-perception` | `b401767`（`docs/d435i-depth-recovery`） | L3 感知 | D435i + Aurora；YOLO 在 3060 上 9.0 ms/图（FP32）；融合目标 30 Hz；跨视图 1.55–10.03 mm |
| `jcheng-manipulation` | `a08b8b6`；基线 `v1.0.0` = `b3411e4` | 冻结基线 + Studio | 5-DoF 标定；PTP/S-curve；24/24 方块；放置均值 3.08 mm；误差预算 RSS 13.33 mm 未过 6 mm 门 |
| `jcheng-interfaces` | `3c55dd6` | L1 契约 | `MotionCommand` 支持 `JOINT_TRAJECTORY/JOINT_STEP/POSE/HOME/BASE_PULSE/GRIPPER`；`ExecuteMotion` 为唯一 action |
| `jcheng-research` | `10b6cbc` | 研究 | 本报告与 MVE-0；无运行时依赖 |
| `jcheng-mobile` / `jcheng-ops` | `6b3a7e1` / `144d89d` | L3/ OPS | 与本决策无直接关系；不纳入比较 |

> `jcheng-design` 与 `jcheng-manipulation` 是同一 remote 的两个 checkout；本报告
> 只读引用 `jcheng-manipulation` 的基线事实，不修改其标签、证据或实验历史。

### 3.2 运动路径：不是 7D OSC 流

- `jcheng-interfaces/ros2_ws/src/jcheng_interfaces/msg/MotionCommand.msg:9-30`
  定义 `kind` 与 `target_pose/trajectory`；`ExecuteMotion.action` 只有
  goal/result/feedback，没有逐 step 的 delta 接口。
- `jcheng-system/ros2_ws/src/jcheng_system_core/jcheng_system_core/safety.py:26-33`
  列出允许的 kind/profile 组合；`:36-40` 的 `state_timeout_s = 0.5`；
  `:311-326` 对 `POSE` 做工作空间与桌面间隙检查。
- `jcheng-system/docs/SAFETY.md` §1–§6：运动只经 `ExecuteMotion`；能力模块只
  提交意图；禁止原始总线 `set_position`、`SetBusServoState`、直接
  `/arm_controller/follow_joint_trajectory`、`/move_action` 执行。
- `jcheng-system/docs/M6-SCOPE.md` §6.2：MoveIt 只构建/校验 plan-only goal；
  真正 move_group 的 plan-only 调用尚未在实机验证；任何 MoveIt 执行路径必须
  关闭或无硬件发布权限。

**含义**：GloVLA 的 transport controller 是**每个 timestep 计算 7D OSC delta**
的闭环；JCHENG 的运动路径是**按命令/轨迹校验并执行**的离散接口。两者不是同一
控制层。把 VLA chunk 塞进 `ExecuteMotion` 是可行的工程改造，但它把闭环从
“每 step”变成“每 chunk”，不是论文的原样执行。

### 3.3 感知：有目标，但没有“容器中心”与学习管线

- `jcheng-perception/docs/TOPICS.md:92-115`：`/perception/targets` 为
  `FusedTargetArray`，best effort，30 Hz；每个目标有 `base_link` 下的位置 +
  方向、6×6 协方差、`confidence`、`phase`、`status`、`weight_external/wrist`、
  `occluded`；规划器必须检查 stamp 与自身时钟差（建议 >200 ms 视为过期）。
- `jcheng-perception/README.md:195`：RTX 3060 上 Ultralytics 稳态 **9.0 ms
  (FP32) / 7.4 ms (FP16)** 每图；ROS 节点 **54.3 ms/frame** 平均；跨机真实
  YOLO 2.06 fps / 55 ms（`README.md:219`）。
- `jcheng-perception/evidence/README.md:14`：2026-11-24 split-edge 静态 60 s，
  external 134 + wrist 226 条，**跨视图 1.55 mm**，fusion max 2.14 / p95 1.64 /
  final 1.96 mm；`docs/EVIDENCE.md:398` 的 run 9 为跨视图 **3.37 mm**、融合
  max **10.03 mm**、p95 3.78 mm、final 1.19 mm（12.4 mm 视图切换瞬态）。
- **没有** basket/容器的 3D 中心估计；没有物体中心真值；没有演示数据管线。

### 3.4 操作基线：已经是“几何 + 模型化局部交互”

- `jcheng-manipulation/docs/phase0/ARMPI_5DOF_CONSTRAINTS.md:8-30`：5-DoF +
  1 个夹爪关节；`joint1` 基座 yaw、`joint2` 肩 pitch、`joint3` 肘 pitch、
  `joint4` 腕 pitch、`joint5` 工具 roll；不能到达任意 6D 位姿；工具姿态由
  `joint1…joint5` 完全决定。
- 同文件 `:100-120`：`PTP` 是端点约束 5-DoF 目标的可用 primitive；`LIN` 在
  固定姿态直线离开可达集时返回 `NO_IK_SOLUTION`；OMPL goal sampler 在 KDL
  5-DoF 模型上不可用，但 `/compute_ik` 可从随机种子成功。
- `jcheng-manipulation/README.md:43-47`：ArmPi Ultra 5-DoF、两指夹爪、Pi 5、
  腕部 Aurora 930 RGB-D、底盘前 D435i；抓取+放回 24/24（McNemar
  p=0.00049），随机放置 24-pair 9/24 → 24/24（p=6.1×10⁻⁵）。
- 同文件 `:196-201`：抓取执行 20 次，命令 vs 总线 **4.220 mm / 1.069° mean**，
  **5.386 mm / 1.495° max**；放置 20 次，landing − pre-grasp **3.080 mm mean、
  RMS 4.082 mm、max 11.514 mm**；抓取工作半径 205–210 mm。
- 同文件 `:640-690`：误差预算 translation RSS **13.325 mm**、rotation worst
  **3.322°**，均超过 6 mm / 2° 门；经验放置均值 3.080 mm 在门内；单一平台、
  单一物体、单次 session；无 e-stop/抱闸/力矩传感；contact-rich 与自主恢复
  明确 out of scope。

**含义**：JCHENG 不是“还没做几何”的空平台；它已经有一个**几何 transport +
模型化局部抓取/放置**的系统。GloVLA 的分解与它同构，差别在“局部交互”由
VLA 而不是标定/抓取搜索完成。论文的真实价值是**为这个架构提供外部证据**，
而不是提出一个 JCHENG 尚未拥有的架构。

### 3.5 算力与数据

- 本机 `nvidia-smi`：`NVIDIA GeForce RTX 3060 Laptop GPU, 6144 MiB`，
  driver 595.99.02（2026-11-25）。
- Pi 5 无 CUDA；感知 GPU 节点在笔记本上；机器人容器内是 Humble，主机是 Jazzy。
- **没有**演示数据集、动作标签、语言指令集、VLA checkpoint 或训练脚本。
  `jcheng-perception/README.md:259` 提到的 `lerobot_piper_local` 是一个本地
  copy 的 acquisition/camera patch，不是可用演示集。

### 3.6 决定问题的五个事实

1. 运动是 joint/pose 命令，不是 7D OSC delta 流。
2. 5-DoF 不能任意 6D；固定姿态直线常不可行。
3. 6 GB 不能加载 π0/π0.5/GR00T N1.6/N1.7 中任何一个。
4. 零演示数据；论文需要 full-task 演示 + 8×A100 训练。
5. 现有管线已经实现几何 + 模型化局部交互，且有实测精度与失败边界。

---

## 04. Research Methodology（研究方法）

### 4.1 检索策略

关键词与同义组合：`GloVLA`、`geometry-aware VLA`、`hybrid VLA motion planning`、
`VLA classical planner`、`VLA robustness`、`LIBERO-Plus`、`LIBERO-PRO`、
`LIBERO saturation`、`SkipVLA`、`GeomVLA`、`GR00T N1.6`、`openpi pi0`、
`ACT action chunking`、`DP3 3D diffusion policy`、`SAM 3`、`TAMP`、
`phase segmentation demonstrations`、`handoff region`。

检索轮次：先以论文为中心（GloVLA → 其引用的 LIBERO/π0/GR00T/SAM3/TAMP），
再向外找**同期替代**（SkipVLA、GeomVLA）与**反例**（LIBERO-Plus/PRO 的鲁棒性
崩溃），最后回到项目约束做算力/动作空间/数据核算。没有以“找到第一个可行方案”
为停止条件；停止依据是核心问题已回答、主要候选已比较、边际收益下降。

### 4.2 来源与阅读深度

| 来源 | 类型 | 阅读深度 | 用途 |
|---|---|---|---|
| GloVLA arXiv:2609.06256v1 | 论文 | **全文 9 页**，含 Table I–VI、Fig. 2/3/5/6/7 | 方法、数字、消融、局限 |
| GloVLA 项目页 | 官方页面 | 全文 | 代码/数据/视频核实 |
| arXiv abs 页 | 元数据 | 全文 | 投稿状态、注释、代码链接 |
| GitHub API 搜索 | 仓库 | 查询结果 | 是否存在官方代码 |
| LIBERO arXiv:2306.03310 | 论文 | 摘要 | 基准背景 |
| LIBERO-Plus arXiv:2510.13626 + repo | 论文/仓库 | 摘要 + README | 鲁棒性反例、评测协议 |
| LIBERO-PRO arXiv:2510.03827 + repo | 论文/仓库 | 摘要 + 元数据 | 记忆化反例、MIT 代码 |
| SkipVLA arXiv:2609.20648 | 论文 | 摘要 | 同期替代、速度声明 |
| GeomVLA arXiv:2609.13812 | 论文 | 摘要 | 3D 几何路线替代 |
| GR00T 官方 repo（N1.6 branch / main） | 仓库 | README | N1.6 3B/37 ms@5090；N1.7 16 GB+/40 GB+ |
| openpi 官方 repo | 仓库 | README | >8 GB / >22.5 GB / >70 GB |
| ACT 官方 repo | 仓库 | README | MIT、50 episodes、chunk 100 |
| SAM 3 arXiv:2511.16719 + 本仓库 `references/sam3.md` | 论文/来源记录 | 已有全文记录 | 边缘部署限制 |
| JCHENG 内部文档/代码 | 一手 | 相关章节 + 行号 | 当前系统事实 |

### 4.3 纳入/排除

纳入：一手论文、官方仓库、官方文档、可核实的项目页、内部代码/证据。排除：
搜索引擎摘要、第三方博客、营销材料、无法核实的 2026 arXiv 编号、只凭 README
推断的实现结论。对 GloVLA 不以摘要判断；对替代方案只读摘要的，明确标注并降低
置信度。

### 4.4 研究边界

- 无 GloVLA 代码（不存在），无法做源码审计或复现。
- 无 ≥8 GB GPU，无法加载论文 backbone；无 8×A100，无法训练。
- 无机器人授权，未执行任何运动；MVE-0 只是桌面几何复算。
- LIBERO-Challenge 未发布，无法独立重评 88.5%。
- 论文是 RA-L 投稿（2026-09-05），未显示接收；项目页为匿名 "Under review"。

---

## 05. Literature Review（文献综述）

### 5.1 GloVLA：问题、机制、证据

**问题**：单一端到端 VLA 同时承担“长程 free-space transport”和“短程
contact-rich interaction”。前者视觉多样但几何等价，后者需要语义/接触推理。
一个动作分布学两件事，导致数据低效、推理步数多、误差累积；视觉偏移、遮挡、
杂乱、初始夹爪姿态不利会把策略推出训练分布。

**贡献**：
1. 把 object-centric pick-and-place 显式分解为几何 transport + 局部 VLA；
2. 用固定、确定性的 handoff 边界，不需要学习 handoff 选择器；
3. 提出 sphere-conditioned demonstration extraction：只用原始 full-task 演示，
   不收集新的阶段演示；
4. 提出 LIBERO-Challenge（50 个评测场景，5 类扰动，3 个难度）；
5. 在 4 个 backbone（π0、π0.5、GR00T N1.6、N1.7）和真实 UR10e 上验证。

**机制**（以论文 §III 为准）：

- 动作：`a_t = (Δx, Δy, Δz, Δϕ, Δθ, Δψ, g) ∈ R^7`，前 6 维是末端位姿增量，
  `g ∈ [0,1]` 是夹爪指令（1=开）。策略输出 chunk `A_t = (a_t,…,a_{t+H−1})`，
  执行前 `n_act ≤ H` 个动作后重查。
- 提取区域：`R_j^clip = {p : ||p − c_j||₂ ≤ r_j}`，`j ∈ {o,b}`；`r_o=0.12 m`，
  `r_b=0.18 m`（Fig. 2）。
- 抓取片段：`t0g` = 首次进入物体球且指令/观测夹爪都开；`tcg` = 之后首次闭合
  指令；`t1g` = 首次离开物体球 +1；片段含退出步。
- 放置片段：`t0p` = 抓取片段之后、进入篮子球且“指令闭合或观测闭合”；`trp` =
  首次释放指令；`t1p = trp + 9`（释放步 + 后 8 步）。
- transport controller：`p_hj = ĉ_j + δ_j`；`δ_o=(ρ_o,z_g)`，
  `ρ_o=(0.04,0)`、`z_g=0.08`；`δ_b=(ρ_b,z_p)`，`ρ_b=(0.005,0.005)`、
  `z_p=0.12`；`a_xyz = clip(S^{-1} K_p (p_hj − p_ee), −1, 1)`；旋转增量置零，
  姿态保持在进入模式时的值；夹爪在 approach 开、transport 闭；抓取/释放只由
  局部策略执行。
- handoff 集合：`H_j = {p : ||p − p_hj||₂ ≤ ε_j}`；进入 `H_j` 或预算耗尽就
  切换模式；四模式 `app → grasp → trans → place → end`；预算耗尽**不终止**
  episode，而是把控制交给下一模式（超时的 transport 会把次优起点交给局部策略）。
- 包含条件：若 `||ĉ_j − c_j||₂ ≤ η_j`，且 handoff 时 `p_ee ∈ H_j`，则
  `||p_ee − c_j||₂ ≤ ε_j + η_j + ||δ_j||₂`；当
  `ε_j + η_j + ||δ_j||₂ ≤ r_j` 时，handoff 位置落在提取区域内。论文明确：
  这只是**位置包含**，不保证 orientation、gripper state、visual context 的
  in-distribution。

**假设**：
- 物体/容器中心可靠：仿真用环境真值；真实机器人用 SAM 3 分割。
- 固定 offset 足以覆盖局部策略分布；不需要学习 handoff 选择或碰撞感知。
- 原始 full-task 演示可得；动作接口是 7D OSC；机器人能执行 6D 位姿。
- 成功判据不变；不需要新演示。

**实验设计与结果**：
- 标准 LIBERO Object：10 任务 × 50 episodes，5 个独立 run × 10；4 个 backbone。
  策略训练用 8×A100 80 GB（论文 §IV-A）；仿真评测在 RTX 5090 32 GB。
  π0 87.4→98.6，π0.5 97.8→99.6，GR00T N1.6 88.8→98.4，N1.7 96.4→99.6。
- LIBERO-Challenge：50 场景（30 easy/10 medium/10 hard），每场景 50 episodes；
  GR00T N1.6 full 20.8±10.0 → GloVLA 88.5±9.4（+67.6）；easy 31.4→93.8；
  medium 8.3→86.5；hard 1.5→74.9。
- LIBERO-Plus：GloVLA 88.2 加权平均，6/7 轴领先或持平，noise 竞争。
- 数据效率：Table V 仅 Alphabet Soup；10 demos clean 100% vs FullVLA 86.0%；
  50 demos 非结构化平均 99.9% vs 48.5%。
- 真实 UR10e：90 trials（clean 20 + 7 条件 ×10）；总体 35.6%→90.0%；
  inference 60.1±19.6 s→28.2±2.0 s（2.13×；表 VI 未注明统计单位/推理硬件，
  按 episode 总时间理解，C）；clean 90→95，clutter 30→90，obstruction
  40→100，illumination 0→80，visual shift 40→100，distraction 20→100，
  medium 10→80，hard 0→70。
- 消融：提取半径 `(r_o,r_b)` 在测试范围内 success >80%；`ρ_b,z_g,z_p` 在 ±8λ
  内近满分；`ρ_o` 最紧：±2λ（±10 mm）保持，−4λ（−20 mm）降到 40–80%，
  −8λ（−40 mm）崩溃；`ρ_b` +16λ、`z_p` −16λ 崩溃。

**主张与证据强度**：

| 主张 | 论文证据 | 本报告评级 | 理由 |
|---|---|---|---|
| Challenge 88.5% vs 20.8% | Table II，2,500 episodes/方法 | A（报告）/C（独立） | 无代码/场景，未独立复现 |
| 真实 UR10e 90.0% vs 35.6% | Table VI，90 trials | A（报告）/B（迁移） | 无演示数量/训练协议；5-DoF 不同 |
| 推理 2.13× | Table VI，60.1→28.2 s | A（报告）/C（单位） | 未注明统计单位/硬件 |
| 10 demos clean 100% | Table V，单任务 | B | 只测 Alphabet Soup |
| 4 backbone 一致 | Table I | A | 都是大型 VLA，无小策略 |
| 分解导致增益 | 消融只变 handoff 参数 | C | 真值中心/双策略/固定语言混淆 |
| 物理 obstruction 鲁棒 | Table II/VI | C | 控制器无碰撞检查；语义不明 |

**优点**：
- 方法简单、可解释；handoff 是确定性的，没有额外学习组件。
- 真实机器人提升大，推理成本减半；四个 backbone 一致，说明不是单一架构的
  偶然。
- 论文自己给出包含条件，并明确它不是 in-distribution 的充分条件；也承认
  “完全隔离归因需要 decoupled ablations”。这种自我限制提高了可信度。
- 使用公开 LIBERO/Plus 与官方成功判据；LIBERO-Challenge 保持官方初始状态
  分布与 predicate。

**关键弱点/混淆**（详见 §08）：
1. 仿真里 GloVLA 用**真值**物体/容器中心，FullVLA 只有 RGB + proprioception，
   没有真值中心；不是感知公平的对比。
2. GloVLA 训练**两个独立局部策略**（πg、πp），FullVLA 是一个策略；不是
   参数量/容量匹配的对比。
3. 局部策略的指令是固定短语 `ℓg`/`ℓp`；语言 grounding 被外置到 SAM3/真值，
   没有“VLA backbone 是否必要”的消融（vs 小型 vision-only policy）。
4. transport controller 不做碰撞检查/轨迹优化；“obstruction”是物理占道还是
   视觉遮挡未说明；不能把结果外推为物理避障。
5. 没有代码/数据/Challenge 发布；RA-L 在审；没有独立复现。
6. 统计：50 episodes/scene、5×10 runs、无 CI/显著性检验；真实机器人 10–20
   trials/条件；Table V 与消融只用一个任务；摘要 20.9 与 Table II 20.8 不一致。

**可复现性**：**不可复现**。没有代码、没有 LIBERO-Challenge 场景、没有真实
机器人演示/训练协议；只有项目页视频。arXiv v1 的 9 页没有附录，ε、K_p、S、
真实机器人演示数量、SAM3 定位误差均未报告。

**迁移成本**：高。需要 (a) 与论文同量级的 GPU 训练；(b) 6D/7D 动作空间或
5-DoF 适配；(c) 原始 full-task 演示与阶段标注；(d) SAM3 或等效的开放词表
定位；(e) 与 `ExecuteMotion` 的安全适配。对 JCHENG 当前任务，收益未证明。

### 5.2 LIBERO-Plus / LIBERO-PRO：高分不等于鲁棒

- **LIBERO-Plus**（arXiv:2510.13626）：7 个扰动轴（物体布局、相机视角、机器人
  初始状态、语言指令、光照、背景纹理、传感器噪声），10,030 个任务；官方 repo
  `sylvestf/LIBERO-plus` 把 `num_trials_per_task` 从 50 改为 **1**；报告
  “95% → <30%”，相机视角/初始状态最致命，模型大量忽略语言。代码/资产公开，
  但 repo 未声明 license。
- **LIBERO-PRO**（arXiv:2510.03827）：4 个轴（物体、初始状态、指令、环境）；
  报告 >90% 模型在 generalized setting 跌到 **0.0%**；行为包括抓无关物体、
  对无意义指令不变；repo `Zxy-MLlab/LIBERO-PRO`，MIT，365 stars（2026-11-25）。
- **含义**：GloVLA 的 clean LIBERO 98% 不能当作部署证据；它自己的 Challenge/
  Plus 结果更接近真实分布偏移，但仍是作者自评、未独立复现。对 JCHENG，任何
  评测都应包含分级扰动与固定 predicate，而不是只看 clean。

### 5.3 SkipVLA：同期的“经典规划 + VLA 接触技能”

- arXiv:2609.20648（2026-09-17）：经典运动规划器负责 free-space，VLA 只在
  contact-rich 技能被查询；用冻结 VLA backbone 预测目标位姿；13 个 LIBERO
  任务 + 物理 6-DoF YAM 臂；声称 **2.5×** 任务完成加速、同等成功率、显著更低
  能耗；**无代码**。
- **含义**：GloVLA 的“分解”不是孤例，2026 年出现收敛；两篇都缺代码，无法
  独立比较。SkipVLA 用 collision-aware planner，若 JCHENG 要走这条路，它比
  GloVLA 的 P-controller 更接近 MoveIt 的工程现实；但仍需要 VLA backbone 与
  数据。

### 5.4 GeomVLA：把几何放进 VLA，而不是外置

- arXiv:2609.13812（CoRL 2026）：把 VLM 特征用深度/标定提升到 3D scene
  tokens，学习 3D scene trajectory denoiser，再用 geometry-aware attention
  条件化 3D flow action denoiser；CALVIN SOTA，LIBERO/RoboTwin2.0 有竞争力；
  真实机器人无需 robot-action pretraining；**无代码**。
- **含义**：加几何有两条路：显式分解（GloVLA/SkipVLA）或隐式 3D 表示
  （GeomVLA）。JCHENG 已有深度/标定，显式路线更自然；但 GeomVLA 说明
  “VLA 内部也能学几何”，不能把“分解”当成唯一解。

### 5.5 TAMP / 经典几何：分解不是新思想

- 任务与运动规划（TAMP）长期把几何规划与符号/学习技能结合（Garrett et al.,
  Annual Review of Control, Robotics, and Autonomous Systems, 2021；GloVLA
  引用 [19]）。GloVLA 的新意是**固定 handoff + sphere-conditioned clip
  extraction + Challenge benchmark**，不是“几何 + 学习”本身。
- **含义**：JCHENG 的现有管线属于 TAMP 家族；论文是支持证据，不是范式转换。

### 5.6 小策略替代：ACT / DP3

- **ACT**（arXiv:2304.13705；repo `tonyzhaozh/act`，MIT）：Action Chunking
  with Transformers；chunk 100；仿真 50 episodes/任务；README 没有 VRAM 数字，
  只给 `--batch_size 8`、`hidden_dim 512`；真实数据建议训练到 loss plateau 后
  3–4 倍时长。**6 GB 是否够训练未验证**；推理量级上比 3B VLA 现实得多。
- **DP3**（arXiv:2403.03954；本仓库 `references/vla-robustness-and-alternatives.md`
  已记录）：稀疏点云 + 点编码器 + 扩散策略；仿真多数任务 10 条演示；真实 4 任务
  40 条/任务、85%；对空间/视角/外观/实例泛化。警告：仿真优势部分来自完美点云
  与干净背景分割；真实 D435i 点云有空洞/噪声。
- **含义**：如果 JCHENG 要做“局部学习”，ACT/DP3 量级比 π0/GR00T 更匹配 6 GB
  与数据条件；但它们仍需要演示与动作标签，且没有证据表明能超过现有模型化
  抓取（24/24 方块）。

### 5.7 SAM 3：GloVLA 真实机器人的定位依赖

- SAM 3（arXiv:2511.16719）：Promptable Concept Segmentation；名词短语/
  exemplar；H200 上 100+ 物体单图 30 ms；视频成本随物体数线性增长；约 5 个
  并发物体近实时；64 物体 30 FPS 需要 8×H200；15 帧确认延迟约 0.5 s。
- 论文自述限制：简单名词短语、歧义、遮挡、跟踪漂移；词表/提示是方法的一部分。
- **含义**：按 SAM3 论文的 H200 数字与模型规模，它不适合 Pi 5/6 GB 边缘
  部署（未在 6 GB 上实测，C 级）；GloVLA 真实机器人用 SAM3 提供物体/容器
  中心，但论文没有报告 SAM3 的 η，Eq. 12 无法闭合。JCHENG 现有 YOLO + 深度 +
  融合更轻，但只支持已知类别；要做开放词表，需另算成本。

### 5.8 综合：什么是真的新，什么是缺的

**真的新**：
- 固定、确定性的 handoff 边界，不需要学习 handoff 选择器；
- sphere-conditioned clip extraction，把 full-task 演示自动切成 grasp/place
  片段，不需要新演示；
- LIBERO-Challenge 的分级扰动组合与官方 predicate 保持；
- 在 4 个 backbone + 真实 UR10e 上的一致增益与 2.13× 推理降低。

**不新**：
- 几何 transport + 学习型局部技能（TAMP、hybrid planning 长期存在）；
- 用视觉 backbone 做局部 visuomotor 控制；
- 用扰动基准评估鲁棒性（LIBERO-Plus/PRO 已做）。

**缺的**：
- 代码、数据、Challenge 场景、真实机器人协议；
- 感知公平的 full VLA 基线（GloVLA 用真值中心）；
- 容量/策略数匹配的基线（两个局部策略 vs 一个 full policy）；
- 小型 vision-only 局部策略的消融（VLA backbone 是否必要）；
- 物理 obstruction / 碰撞检查的验证；
- 5-DoF 动作空间适配；
- 独立复现。

---

## 06. Repository Investigation（仓库调查）

### 6.1 GloVLA：没有代码

- arXiv abs 页（2026-11-25 访问）：标题、8 位作者、2026-09-05 提交、9 页/7 图、
  投稿 RA-L；Comments 只给项目页 `https://glovla-project.github.io/`。
- 项目页：只有视频、BibTeX（"Under review", "Anonymous Authors"）、Nerfies
  模板与 CC BY-SA 4.0；**没有 code/dataset 链接**。
- GitHub API 搜索 `GloVLA`：3 个结果，分别是 `glovla/glovla`（profile 配置）、
  `Eric-nguyen1402/glovla.github.io`（网页）、`glovla-project/glovla-project.github.io`
  （项目页）；**没有方法代码**。
- 结论：截至 2026-11-25，GloVLA **不可源码审计、不可复现、不可独立评测**。
  这是本报告最强的可复现性限制 [A]。

### 6.2 LIBERO-Plus / LIBERO-PRO：可用的评测资产，但不是 JCHENG 基准

- `sylvestf/LIBERO-plus`：官方实现；drop-in 替换 LIBERO；10,030 任务；
  7 轴扰动；`num_trials_per_task` 从 50 改为 1；资产在 Hugging Face；
  评估模型包括 OpenVLA/OFT、π0/π0-fast、Nora、WorldVLA、UniVLA、RIPT-VLA；
  README 明确“models largely ignore language instructions”；**未声明 license**。
- `Zxy-MLlab/LIBERO-PRO`：MIT；365 stars；pushed 2026-07-17；4 轴扰动；
  报告 >90% → 0.0%。
- **可用性**：作为“分级扰动 + 固定 predicate + 逐任务记录”的评测模板；
  不能直接用于 ArmPi（LIBERO 是 6/7-DoF 仿真、不同动作空间、不同成功判据）。

### 6.3 GR00T / openpi：6 GB 的硬墙

| 项目 | 模型 | 官方要求 | 6 GB 可行性 |
|---|---|---|---|
| GR00T N1.6 | 3B | N1.6 branch：37 ms/5090；未给 VRAM；main/N1.7：推理 16 GB+、微调 40 GB+ | **不适合**（N1.6 VRAM 未官方给出；6 GB 无余量，C） |
| π0 / π0.5 (openpi) | 未给参数 | 推理 >8 GB；LoRA >22.5 GB；full >70 GB；Ubuntu 22.04 | **不可**（差 ≥2 GB；微调差更多） |

- 官方 README 还说明：GR00T 推荐 1×H100/L40 微调；A6000 可但更慢；openpi
  的 `fsdp_devices` 可多卡分摊，但本机只有一张 6 GB。**截至 2026-11-25，
  官方文档未给出 4-bit/量化推理路径**；社区量化未在论文/官方文档验证，按 D
  级处理。

### 6.4 ACT / DP3：量级上更现实，但仍不是“即插即用”

- ACT：MIT；chunk 100；仿真 50 episodes；真实数据训练建议很长；README 无
  VRAM；`batch_size 8` 是唯一内存旋钮。**6 GB 训练未验证**；按模型量级，
  推理可行性高于 3B VLA，但未在 ArmPi/6 GB 上实测 [C]。
- DP3：点云 + 扩散；10 条仿真演示；真实 40 条/任务；对深度质量敏感；现有
  参考记录警告仿真点云过于完美。**未在 ArmPi 上验证**。

### 6.5 JCHENG 内部：当前系统的代码/证据位置

- 运动契约：`jcheng-interfaces@3c55dd6`，
  `ros2_ws/src/jcheng_interfaces/msg/MotionCommand.msg:9-30`；
  `action/ExecuteMotion.action`。
- 安全：`jcheng-system@36027d2`，
  `ros2_ws/src/jcheng_system_core/jcheng_system_core/safety.py:26-40,311-326`；
  `docs/SAFETY.md` §1–§6；`docs/M6-SCOPE.md` §6.2。
- 感知：`jcheng-perception@b401767`，`docs/TOPICS.md:92-115`；
  `README.md:195,219`；`evidence/README.md:14`；`docs/EVIDENCE.md:398`。
- 操作基线：`jcheng-manipulation@a08b8b6`，基线 `v1.0.0=b3411e4`；
  `docs/phase0/ARMPI_5DOF_CONSTRAINTS.md:8-30,100-120`；
  `README.md:43-47,196-201,640-690`。
- 数据：没有演示集/动作标签/VLA 运行时；`jcheng-perception/README.md:259`
  的 `lerobot_piper_local` 不是演示数据。

### 6.6 静态分析 vs 执行 vs 推断

- **静态分析**：内部代码/文档的行号、外部 README 的要求、论文的数字。
- **执行**：MVE-0 桌面复算（本机 Python，无 GPU/机器人）。
- **推断**：6 GB 不能跑 3B VLA（官方要求 + 硬件事实 → A/C）；5-DoF 适配
  困难（运动学文档 + 论文动作空间 → A/C）；小策略可行性（未测 → C/D）。
- 没有把任何 README 描述当成“已实现”；没有把论文数字当成“已复现”。

---

## 07. Comparative Analysis（横向比较）

### 7.1 候选方案

| 方案 | 计算 | 数据 | 5-DoF 适配 | 集成/安全 | 预期收益 | 证据 | 结论 |
|---|---|---|---|---|---|---|---|
| **当前模型管线** | Pi 5 + 6 GB | 无演示；标定/脚本 | 原生 | `ExecuteMotion`/lease/stop latch；PTP | 24/24 方块；3.08 mm 放置 | A/S | **基线** |
| **GloVLA（π0/GR00T）** | >8/16 GB；8×A100 训练 | full-task 演示 | 7D OSC，需改 | 无代码；需 chunk 适配 | 论文 88.5/90.0%；2.13× | A（报告）/C（迁移） | **现在不** |
| **GloVLA + 小策略** | 6 GB 可能 | 演示 + 阶段标签 | 需 5-DoF 动作空间 | 需 chunk 适配 | 未知；可能不如模型管线 | C/D | **仅仿真 MVE** |
| **SkipVLA** | VLA backbone | 演示 | 6-DoF YAM | 经典规划器 | 2.5× 声明 | B | 不现在 |
| **Full VLA** | >8/16 GB | 大量演示 | 7D OSC | 高 | 论文 clean 高、扰动崩 | A/C | 不推荐 |
| **TAMP/模型化** | CPU | 无需学习 | 原生 | 成熟 | 当前水平 | A | 基线 |
| **GeomVLA** | 大 | 演示 | 6-DoF | 研究 | CALVIN SOTA | B | 研究观察 |

> GloVLA 行的 16 GB 是 N1.7/main README；N1.6 未单列 VRAM（见 §6.3）。

### 7.2 哪些结果可直接比较？

- **不能**把 GloVLA 的 LIBERO/UR10e 成功率与 JCHENG 的 24/24 方块直接比较：
  任务、物体、夹爪、臂、动作空间、成功判据、相机、算力都不同。
- **不能**把 GloVLA 的 28.2 s/episode 与 JCHENG 的 25 Hz 总线读直接比较：
  前者是表 VI 的 episode 级推理时间（硬件未注明），后者是关节读回率。
- **可以**比较的是：几何误差预算（Eq. 12）、推理显存/延迟的算术、动作空间
  约束、数据前置条件。这些是“是否可行”的门，不是“效果”的比较。
- **不能**把论文的 “obstruction” 与 JCHENG 的物理杂乱等同：论文未说明是
  物理占道还是视觉遮挡，控制器无碰撞检查。

### 7.3 矛盾证据

- LIBERO clean 98% vs LIBERO-Plus/PRO 的 95→<30 / >90→0：说明 clean 分数
  不是鲁棒性；GloVLA 的 Challenge 结果与后者方向一致，但仍作者自评。
- GloVLA 的分解增益 vs 三个混淆（真值中心、两个策略、固定语言）：增益方向
  可信，幅度/归因不闭合。
- SkipVLA 2.5× vs GloVLA 2.13×：基线/硬件/任务不同，不能直接比较；两者都
  无代码。
- 论文说“no additional demonstrations”，但需要原始 full-task 演示；这不是
  矛盾，是**相对**声明，容易被误读为“零数据”。

### 7.4 成熟度与隐藏成本

- **成熟**：模型化几何/标定/抓取搜索（JCHENG 已有证据）；TAMP。
- **研究阶段**：GloVLA/SkipVLA/GeomVLA（无代码或未复现）；小策略（ACT/DP3
  有代码，但未在 ArmPi 验证）。
- **隐藏成本**：演示采集与阶段标注；GPU 租用/训练；chunk→`ExecuteMotion`
  适配；安全验证；SAM3/开放词表服务；模型/数据版本管理；热/功耗；维护。
- **更简单的替代**：改进现有标定/感知/扰动评测；用深度/点云做几何；不引入
  学习。对当前方块任务，这是性价比最高的路径。

---

## 08. Critical Findings（关键发现）

### F1. 论文的分解与 JCHENG 现有架构同构，它首先是“支持证据” [A]

JCHENG 已经是“几何 transport（标定 + PTP）+ 模型化局部抓取/放置”。GloVLA
把局部交互换成 VLA，不是提出 JCHENG 没有的架构。论文的真实机器人 35.6→90.0
说明“把 free-space transport 从学习策略里拿掉”是有效的；这与 JCHENG 的选择
一致，但不能推导出“JCHENG 应换成 VLA”。

### F2. “model-agnostic / 不改 action space”在 5-DoF ArmPi 上不成立 [A]

论文的 action 是 7D OSC（6 位姿增量 + 夹爪），transport 只调位置、保持姿态；
ArmPi 是 5-DoF + 夹爪，不能任意 6D；`PTP` 可用，固定姿态 `LIN` 会
`NO_IK_SOLUTION`。要迁移，必须改动作空间（5-DoF 关节/位姿）或加重定向层，
这已经违反论文的核心卖点之一。

### F3. 四个 backbone 都不适合 6 GB；官方未给量化路径 [A/C]

本机 6144 MiB；openpi >8 GB 推理、>22.5 GB LoRA、>70 GB full；GR00T
N1.6 为 3B（N1.6 branch 未单列 VRAM），N1.7/main README 要求 16 GB+ 推理、
40 GB+ 微调。论文的仿真评测在 5090 32 GB 上完成；真实机器人 28.2 s/episode
的推理硬件未注明。按官方要求，6 GB 不适合加载任一 backbone；社区 4-bit 不是
官方支持，按 D 级处理。

### F4. “no additional demonstrations” ≠ 零演示 [A/C]

论文复用原始 full-task 演示；仿真每任务 10–50 条；真实机器人演示数量未报告；
训练 8×A100 80 GB；局部策略是两个独立网络（πg、πp）。JCHENG 没有演示集/
动作标签；现有脚本化运行是“模型管线自己的轨迹”，用它训练只会模仿现有管线，
不增加新信息（除非做人类遥操作/扰动演示）。

### F5. 仿真对比不是感知公平的 [A/C]

仿真里 `ĉ_j = c_j`（真值）；FullVLA 只有 RGB + proprioception，没有真值
中心。GloVLA 的 88.5%（仿真）包含了“免费”的物体/容器中心；FullVLA 没有。
真实机器人用 SAM3，但论文没有报告 SAM3 的定位误差 η，Eq. 12 无法闭合。这个混淆足以解释一部分（不是全部）差距。

### F6. 两个局部策略 vs 一个 full policy：容量/专门化混淆 [A/C]

论文明确“两个独立训练、共享 backbone 架构但不共享参数”的局部策略；推理时
只激活当前阶段的一个，训练时是两个。FullVLA 是一个策略。GloVLA 的增益可能
来自“阶段专门化 + 更多训练容量”，而不只是几何分解；论文没有做策略数/容量
匹配的消融。

### F7. 固定阶段指令把语言 grounding 基本外置 [A/C]

局部策略的指令是固定的 `ℓg`（"pick up the target object"）和 `ℓp`
（"place it in the basket"）；目标选择由真值/SAM3 完成，语言 grounding 基本
被外置。论文没有比较“小型 vision-only 局部策略”与 VLA backbone；因此无法
证明 3B VLA 是必要的。
对 JCHENG，这意味着 ACT/DP3 量级可能足够，前提是数据和动作空间适配。

### F8. 无碰撞检查 + “obstruction”语义不明 [A/C]

transport controller “performs no collision checking or trajectory
optimization”；`obstruction` 只写“end-effector approach corridor”，没有说明
是物理占道还是视觉遮挡。若是物理占道，96.2% 的 obstruction 成功率难以由该
控制器解释；若是视觉遮挡，则不能外推为物理避障；论文没有给出区分二者的
信息。JCHENG 有真实桌面/杂乱/无自碰撞模型，不能把论文结果当作
collision-aware transport 的证据。

### F9. 统计精度不足以支撑逐任务/幅度声明 [A]

- 标准 LIBERO：每任务 50 episodes，5 个 run ×10；没有 CI/显著性检验。
- Challenge：每场景 50 episodes；没有逐场景 CI；摘要 20.9 vs Table II 20.8。
- 真实机器人：每条件 10–20 trials，总体 90；没有 CI。
- Table V 数据效率与 §IV-G 消融只用 Alphabet Soup 一个任务。
- 结论：**方向可信**（差距大），但精确幅度、逐任务排序、数据效率的
  “10 demos 100%”不能当作普适结论。

### F10. 无代码/数据/Challenge，RA-L 在审，无独立复现 [A]

GitHub 搜索无方法代码；项目页无 code/dataset；论文 9 页无附录；真实机器人
演示数量、训练协议、SAM3 η、ε/K_p/S 均缺失。88.5%/90.0% 是**作者报告值**，
不是独立验证值。任何 JCHENG 决策都不能把它当 S/A 级复现证据。

### F11. handoff 几何：抓取只剩 30.56 mm 余量 [S/A]

MVE-0 复算：`||δ_o||=0.0894 m`，`r_o=0.12 m` → `ε+η ≤ 30.56 mm`；
`||δ_b||=0.1202 m`，`r_b=0.18 m` → `ε+η ≤ 59.79 mm`。用 JCHENG 实测
1.55/3.37/10.03 mm 代入，只要 ε ≤ 17–29 mm 就满足；30 mm 物体中心误差
基本失效（只剩 0.6 mm ε）。论文没报告 ε，所以不能判定其实际部署满足条件。
这与论文消融
“ρo 在 ±10 mm 保持、−20 mm 降到 40–80%、−40 mm 崩溃”一致。

### F12. 最可迁移的是“门禁/评测/数据 schema”，不是运行时 [A/C]

- Eq. 12 可作为任何“几何 → 学习”交接的设计检查；
- 分级扰动 + 固定 predicate + 逐场景记录可作为现有管线的评测协议；
- 阶段标注 schema 可作为未来演示数据的采集规范。
这三项不依赖 VLA backbone，也不违反 `ExecuteMotion`/安全边界。

### 什么会改变结论

1. GloVLA 发布代码、Challenge 场景与真实机器人协议，并被独立复现；
2. JCHENG 获得 ≥16 GB GPU 与可用的遥操作演示集；
3. 出现一个当前模型管线明显失败、而局部学习有优势的任务族；
4. 论文/独立工作证明 5-DoF + 小策略也能获得同样增益；
5. 论文的 obstruction 被证明是物理占道且控制器有碰撞检查（当前没有）；
6. 现有管线的分级扰动评测显示其在目标场景大面积失败。

---

## 09. Engineering Applicability（工程适配）

### 9.1 适配矩阵

| 维度 | 当前 | GloVLA | 差距/动作 |
|---|---|---|---|
| 臂 | 5-DoF + 夹爪 | 6-DoF UR10e / LIBERO 7D OSC | 动作空间重设计；5-DoF IK/姿态约束 |
| 控制 | 离散 `ExecuteMotion`，0.5 s 状态新鲜度 | 每 step 7D delta 闭环 | chunk 适配器；闭环降频；安全校验 |
| 算力 | 6 GB 笔记本；Pi 5 无 CUDA | 仿真 5090 32 GB；8×A100 训练 | 不可本地训练/推理 |
| 感知 | YOLO + 深度 + 融合；30 Hz target | 真值中心（sim）/ SAM3（real） | 需容器中心/物体中心；SAM3 边缘不适合（C） |
| 数据 | 0 演示；脚本/Studio 记录 | full-task 演示；10–50/任务 | 需遥操作/演示采集与阶段标注 |
| 安全 | lease/deadman/stop latch；无 e-stop | 无碰撞检查；学习策略 | 需碰撞/工作空间/监控；不得绕过 |
| 评测 | 24/24 方块；3.08 mm | LIBERO/Plus/Challenge | 不可直接比较；需自有扰动协议 |

### 9.2 算力算术

- **显存**：6 GB vs π0 >8 GB（差 ≥2 GB）；GR00T N1.6 为 3B、N1.6 branch
  未单列 VRAM，N1.7/main README 为 16 GB+（6 GB 无余量）。LoRA/full 微调
  差距更大（22.5/70 GB、40 GB+）。按官方要求，6 GB 不是“优化一下”能补的；
  官方文档未给出 6 GB/4-bit 路径。
- **延迟**：论文真实机器人表 VI 为 28.2 s/episode（硬件/单位未注明，C 级）；
  若局部阶段约 200 步、`n_act=8`，约 25 次查询 → 约 1.1 s/query（从 episode
  总量反推，论文未给 per-query 数字，C 级）。ArmPi 5 关节总线读 39 ms
  （25 Hz）；若控制 20 Hz，chunk 8 是 0.4 s 运动 + 约 0.6 s 等待；接触阶段
  会出现明显停顿（C 级）。
- **训练**：8×A100 80 GB；论文未报训练 wall-clock/成本；无法做预算（D）。
  6 GB 本机不能复现任何 backbone 的微调。

### 9.3 动作空间与控制路径

- 论文 transport 是 Cartesian P-control，姿态保持；JCHENG 的可用 primitive
  是 `PTP`（joint-space，端点 IK），固定姿态 `LIN` 常失败。把 P-control 换成
  PTP 会改变 handoff 动力学与误差特性，需要重新验证。
- `MotionCommand` 有 `POSE`，但 MoveIt 只规划、执行路径是 `JOINT_TRAJECTORY`
  / `JOINT_STEP`/`GRIPPER`；没有逐 step delta 接口。
- 可行改造：把 VLA chunk 转成短 joint trajectory，作为**一个** `ExecuteMotion`
  执行；闭环在 chunk 边界，不是每 step。这需要：
  (a) 5-DoF IK/姿态约束；(b) 轨迹时间参数化与 S-curve；(c) 安全校验
  （工作空间/桌面/限位/速度）；(d) 停止时中止在飞动作；(e) 总线实测完成判定。
- **不能**为了低延迟绕过 `ExecuteMotion`、lease、stop latch 或直接发厂商
  `/servo_controller`；这违反 `SAFETY.md` §1–§6。

### 9.4 数据与标签

- 需要：原始 RGB/深度、关节/夹爪指令与总线实测、物体/容器中心、阶段边界、
  成功/失败、时间戳、标定版本、相机内外参。
- JCHENG 现有 Studio G7 可做逐步位姿 takeover，但不是连续遥操作；用它采集
  的演示会带有“逐步命令”分布，不等于人类连续演示。
- 用现有模型管线脚本生成演示，只能蒸馏现有策略；没有新信息，除非加入人类
  纠正、扰动恢复或新物体 [C]。
- 成本：采集时间、标注、存储、训练 GPU；未估算，不能假装低。

### 9.5 安全与可靠性

- 无 e-stop/抱闸/力矩/自碰撞模型；contact-rich 学习策略会增加不可预测接触。
- 现有安全层能拒绝越界/超速/无 lease/stop latch，但不能检测“策略输出语义
  错误”（例如抓空、推入障碍、姿态奇异）。
- 需要：策略输出限幅、工作空间收缩、碰撞检查（MoveIt plan-only 可用于
  离线检查，但真正的 plan-only 调用尚未在实机验证，C 级）、看门狗、人工
  监督、失败即停不重试。
- 论文的 transport 无碰撞检查；JCHENG 不能照搬。

### 9.6 如果 adoption：分阶段路径

| 阶段 | 内容 | 门禁 | 是否已执行 |
|---|---|---|---|
| P0 | 数据/评测 instrumentation：记录阶段、中心、夹爪、时间戳 | 不改变运动；只读 | 未 |
| P1 | 离线片段提取 + 小策略训练（仿真） | 5-DoF 动作空间；≥16 GB GPU | 未 |
| P2 | 仿真扰动评测（MVE-1） | 成功率/CI/延迟达标 | 未 |
| P3 | 影子模式：策略输出与现有管线对比，不执行 | 无运动；差异可解释 | 未 |
| P4 | 实机监督 trial（MVE-3） | 单独授权；`ExecuteMotion`；stop latch | 未 |

### 9.7 回退

- 保留现有模型管线为默认；学习策略仅 advisory/feature flag；
- 不修改 `jcheng-manipulation v1.0.0` 的标签/证据；
- 任何新路径失败，回到现有管线；不自动重试 `UNKNOWN`；
- 代码/数据/权重不进入 `jcheng-research`；实验记录留在对应仓库。

---

## 10. Recommended Approach（推荐方案）

### 推荐（现在）

**不引入 GloVLA 运行时；保留现有管线。** 立即采纳三项：

1. **Eq. 12 作为设计门禁**：任何“几何 → 学习”交接，先算
   `ε + η + ||δ||₂ ≤ r`；用 JCHENG 的实测 η/ε，不通过就不进入训练。
2. **分级扰动评测**：clean + 单扰动 + 2–3 组合 + 4–5 组合；固定 predicate；
   每条件 ≥24 trials（实机）或 ≥50 episodes（仿真）；报告 Wilson CI 与逐
   场景失败模式。
3. **阶段标注 schema**：为未来演示数据定义抓取/放置片段、中心、夹爪、时间戳、
   标定版本；先记录，不训练。

### 替代（如果决定上学习型局部策略）

在仿真里做 **MVE-1**：5-DoF 动作空间、几何 transport + ACT/DP3 量级小策略，
与现有模型管线、full policy 对比；每任务 10/30/50 条演示；≥50 episodes/场景；
配对 McNemar；先证明“局部学习有增益”，再谈 VLA backbone。**不要**从
π0/GR00T 起步。

### 不推荐

- 在本机 6 GB 上尝试 π0/π0.5/GR00T N1.6/N1.7；
- 在 Pi 5 或 6 GB 笔记本上部署 SAM3 服务；
- 为了低延迟绕过 `ExecuteMotion`/lease/stop latch，或直接发厂商 servo；
- 用论文的 88.5%/90.0% 作为 JCHENG 的验收标准；
- 在没有演示数据/动作标签前搭 VLA 栈；
- 把“no additional demonstrations”理解为“零数据”。

### 重新开启 VLA 问题的触发条件

- 有 ≥16 GB GPU（本地或稳定租用）且能覆盖训练/推理；
- 有 ≥50 条/任务的遥操作演示与阶段标注；
- 现有管线在目标物体/扰动下出现可复现的失败，且局部学习有明确假设；
- GloVLA 或同类工作发布代码并被独立复现；
- 任务从“单一方块 pick-place”扩展到多物体/语言条件，模型化管线维护成本
  超过学习管线。

---

## 11. Experimental Design（实验设计）

> **状态**：MVE-0 **已运行**（桌面复算，不是机器人实验）；MVE-1/2/3 **未运行**。
> 未执行的实验不描述为已完成；合成/仿真结果不当作硬件验证。

### MVE-0 — handoff 几何误差预算（已运行）

- **假设**：论文抓取 handoff 只剩约 30.6 mm 给 `ε+η`；JCHENG 实测跨视图
  误差可落入，但 30 mm 物体中心误差会失效。
- **基线**：Eq. 12；不使用成功率。
- **变量**：阶段、η、ε；控制：论文 Fig. 2 的半径/偏移。
- **环境**：CPU/Python 3.12；无 GPU/机器人。
- **指标**：`slack = r − ||δ|| − ε − η`；允许的最大 ε。
- **验收**：复算与手算一致（grasp 30.56 mm，place 59.79 mm）。
- **失败判据**：输出与手算不一致，或把跨视图差异误当 η 不加说明。
- **记录**：`experiments/20261125-glovla-handoff-budget/`。
- **回退**：不需要（只读）。
- **结果**：grasp 余量 30.56 mm；place 59.79 mm；JCHENG 1.55–10.03 mm 在
  ε ≤17–29 mm 下通过；30 mm 误差失败。详见
  [`result.md`](../experiments/20261125-glovla-handoff-budget/result.md)。

### MVE-1 — 5-DoF 小策略 + 几何 transport（未运行）

- **假设**：在 5-DoF 动作空间下，几何 transport + 局部小策略（ACT/DP3 量级）
  在扰动场景优于 full policy，且不劣于现有模型管线。
- **基线**：现有模型管线；第二对照：full policy。
- **变量**：策略结构（几何 + 局部 / full）；控制：数据、seeds、训练步数、
  评测场景、成功判据。
- **环境**：LIBERO 或 MuJoCo 的 5-DoF 改编；每任务 10/30/50 条演示；
  ≥50 episodes/场景；单张 ≥16 GB GPU 更稳妥（本机 6 GB 未验证，C）。
- **指标**：成功率、Wilson 95% CI、配对 McNemar、推理延迟、handoff 定位误差。
- **验收**：扰动场景提升 ≥10 pp 且 p<0.05；clean 回退 ≤2 pp；延迟满足控制周期。
- **失败判据**：无显著提升；或提升只在 clean；或 5-DoF 下无法满足 Eq. 12。
- **记录**：固定 seeds、逐 episode CSV、配置哈希、模型/数据版本。
- **回退**：保留现有管线；不引入 VLA 运行时。

### MVE-2 — 现有管线的分级扰动评测（未运行）

- **假设**：现有管线在 LIBERO-Challenge 式扰动下出现可测量退化，退化主要
  来自定位/遮挡而非抓取策略。
- **基线**：clean 台面；现有管线。
- **变量**：clutter/distractor/illumination/visual shift/obstruction 的组合。
- **环境**：ArmPi Ultra 实机；**需要单独的操作员授权**；不得由 CI/脚本自动
  触发运动。
- **指标**：成功率、定位误差、抓取失败模式、人工接管次数。
- **验收**：预注册 ≥24 trials/条件；Wilson CI；失败模式可归因。
- **失败判据**：无法区分定位与抓取失败；或出现安全锁存/总线 `UNKNOWN`。
- **记录**：`jcheng-manipulation` 证据目录；原始数据不进入 `jcheng-research`。
- **回退**：停止实验；保持现有管线；不自动重试。

### MVE-3 — 实机局部策略（阻塞）

需要 (a) 遥操作/演示数据；(b) ≥16 GB GPU 或经验证的量化推理路径；
(c) 通过 `ExecuteMotion` 的 chunk 适配器与安全校验；(d) 单独授权。在上述
条件满足前不启动。

---

## 12. Limitations & Uncertainties（局限与不确定性）

1. **无代码/数据/Challenge**：GloVLA 不可源码审计、不可复现；所有论文数字
   是作者报告值 [A]。本报告只读到 arXiv v1 的 9 页；RA-L 终版/补充材料可能
   有更多实现细节（ε、演示数量、SAM3 η），但截至 2026-11-25 不可得。
2. **无独立复现**：没有第三方在 LIBERO-Challenge 或 UR10e 上复现 88.5%/
   90.0%；RA-L 在审 [A]。
3. **无大 GPU**：本机 6 GB；无法验证 4-bit/量化/offload 的可行性；任何
   “也许能跑”的说法都是 D 级。
4. **无机器人授权**：MVE-2/3 未执行；不能对 JCHENG 实机成功率作任何断言。
5. **无演示数据**：无法评估“小策略 + 几何”在 JCHENG 上的真实上限；ACT/DP3
   的 6 GB 训练可行性未测。
6. **η 的语义**：1.55/3.37/10.03 mm 是跨视图/融合差异，不是物体中心真值
   误差；13.33 mm 是平移误差预算 RSS；MVE-0 是上界近似，不是标定。
7. **ε 缺失**：论文没有报告 ε、K_p、S；无法判定其实际部署是否满足 Eq. 12。
8. **obstruction 歧义**：物理占道 vs 视觉遮挡未说明；控制器无碰撞检查。
9. **统计**：50 episodes/scene、5×10、无 CI；真实 10–20/条件；Table V/消融
   单任务；20.9 vs 20.8；幅度/逐任务结论不确定。
10. **5-DoF 适配未测试**：没有 5-DoF 的 GloVLA 实现；动作空间/IK/姿态约束
    的改造难度是 A/C 推断，不是实测。
11. **现有误差预算未过门**：translation RSS 13.325 mm > 6 mm；经验均值
    3.080 mm 在门内；不能把“经验均值”写成“bound 通过”。
12. **报告自身偏差**：作者（研究代理）可能倾向维护现有架构；本报告通过
    纳入论文真实机器人强结果、SkipVLA/GeomVLA 替代、以及“什么会改变结论”
    来对冲，但仍不是独立评审。

**需要什么才能关闭**：GloVLA 代码/Challenge 发布；≥16 GB GPU；遥操作演示；
SAM3 η 标定；5-DoF 仿真；实机授权与预注册评测；独立评审。

---

## 13. References（参考文献）

### 论文

- Nguyen, T. T., Nguyen, H. H., Nguyen, H. A., Dinh, B. K., Vien, N. A.,
  Nguyen Ho Minh, D., Vu, M. N., Le, N. *GloVLA: Let Geometry Move and Local
  VLA Interact for Robust Object-Centric Manipulation in Unstructured
  Environments*. arXiv:2609.06256v1, 2026-09-05; submitted to IEEE RA-L.
  <https://arxiv.org/abs/2609.06256>（全文 9 页已读；2026-11-25 访问）。
  本地副本：[`references/papers/20261125-glovla.pdf`](../references/papers/20261125-glovla.pdf)
  （CC BY-NC-SA 4.0；Ghostscript `/ebook` 压缩版，文本未变、图分辨率降低）。
- Liu, B., Zhu, Y., Gao, C., Feng, Y., Liu, Q., Zhu, Y., Stone, P.
  *LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning*.
  NeurIPS 2023. arXiv:2306.03310. <https://arxiv.org/abs/2306.03310>
  （摘要；基准 130 任务、四 suite）
- Fei, S., Wang, S., Shi, J., Dai, Z., Cai, J., Qian, P., Ji, L., He, X.,
  Zhang, S., Fei, Z., Fu, J., Gong, J., Qiu, X. *LIBERO-Plus: In-depth
  Robustness Analysis of Vision-Language-Action Models*. arXiv:2510.13626,
  2025（v3 2025-12-26）. <https://arxiv.org/abs/2510.13626>（摘要 + repo
  README；7 轴、10,030 任务、1 trial/task）
- Zhou, X., Xu, Y., Tie, G., Chen, Y., Zhang, G., Chu, D., Zhou, P., Sun, L.
  *LIBERO-PRO: Towards Robust and Fair Evaluation of Vision-Language-Action
  Models Beyond Memorization*. arXiv:2510.03827, 2025（v2 2026-05-25）.
  <https://arxiv.org/abs/2510.03827>（摘要；>90%→0.0%）
- Agrawal, K., Rahman, M. A., Yeh, R. A., Kingston, Z. *SkipVLA: Skipping VLA
  Steps with Classical Planning for Fast Robot Manipulation*.
  arXiv:2609.20648, 2026-09-17. <https://arxiv.org/abs/2609.20648>（摘要；
  2.5×、13 LIBERO、YAM、无代码）
- Xiong, Z., Gkanatsios, N., Reuss, M., Fragkiadaki, K. *GeomVLA: Unifying
  Scene, Motion, and Action in 3D*. arXiv:2609.13812, CoRL 2026.
  <https://arxiv.org/abs/2609.13812>（摘要）
- Black, K., Brown, N., Driess, D., et al. *π0: A Vision-Language-Action Flow
  Model for General Robot Control*. arXiv:2410.24164, 2024.
  <https://arxiv.org/abs/2410.24164>（背景；未逐节读）
- Bjorck, J., Castañeda, F., et al. *GR00T N1: An Open Foundation Model for
  Generalist Humanoid Robots*. arXiv:2503.14734, 2025.
  <https://arxiv.org/abs/2503.14734>（背景）
- Zhao, T. Z., Kumar, V., Levine, S., Finn, C. *Learning Fine-Grained
  Bimanual Manipulation with Low-Cost Hardware*. arXiv:2304.13705, RSS 2023.
  <https://arxiv.org/abs/2304.13705>（ACT；摘要/README）
- Ze, Y., Zhang, G., Zhang, K., Hu, C., Wang, M., Xu, H. *3D Diffusion Policy:
  Generalizable Visuomotor Policy Learning via Simple 3D Representations*.
  arXiv:2403.03954, 2024. <https://arxiv.org/abs/2403.03954>（见本仓库
  `references/vla-robustness-and-alternatives.md`）
- Carion, N., Gustafson, L., Hu, et al. *SAM 3: Segment Anything with
  Concepts*. arXiv:2511.16719, 2025. <https://arxiv.org/abs/2511.16719>
  （见本仓库 `references/sam3.md`）
- Garrett, C. R., Chitnis, R., Holladay, R., Kim, B., Silver, T., Kaelbling,
  L. P., Lozano-Pérez, T. *Integrated Task and Motion Planning*. Annual
  Review of Control, Robotics, and Autonomous Systems, 4:265–293, 2021.
  （TAMP 背景；经 GloVLA 引用 [19]，未独立读全文）

### 仓库与项目页

- GloVLA 项目页：<https://glovla-project.github.io/>（视频；无 code/dataset；
  2026-11-25 访问）
- GloVLA 网页 repo：<https://github.com/glovla-project/glovla-project.github.io>
- LIBERO-Plus：<https://github.com/sylvestf/LIBERO-plus>（10,030 任务；
  1 trial/task；无 license 声明）
- LIBERO-PRO：<https://github.com/Zxy-MLlab/LIBERO-PRO>（MIT；365 stars；
  pushed 2026-07-17）
- NVIDIA Isaac-GR00T：<https://github.com/NVIDIA/Isaac-GR00T>；N1.6 branch
  <https://github.com/NVIDIA/Isaac-GR00T/tree/n1d6>（3B；37 ms/5090；
  main/N1.7：16 GB+ 推理、40 GB+ 微调）
- Physical Intelligence openpi：<https://github.com/Physical-Intelligence/openpi>
  （>8 GB 推理、>22.5 GB LoRA、>70 GB full；Ubuntu 22.04）
- ACT：<https://github.com/tonyzhaozh/act>（MIT；chunk 100；50 episodes 仿真）
- SAM 3 官方 repo（经 `references/sam3.md`）：<https://github.com/facebookresearch/sam3>

### 本仓库来源记录与实验

- `references/glovla.md`（论文来源记录与本地副本说明；2026-11-25）
- `references/vla-robustness-and-alternatives.md`（2026-11-25）
- `references/sam3.md`（2026-11-25）
- `experiments/20261125-glovla-handoff-budget/design.md`
- `experiments/20261125-glovla-handoff-budget/result.md`
- `experiments/20261125-glovla-handoff-budget/analysis.py`
- `experiments/20261125-glovla-handoff-budget/logs/handoff_budget.txt`

### 内部文档（只读引用；不作为外部来源）

- `jcheng-system@36027d2`：`docs/SAFETY.md`、`docs/M6-SCOPE.md`、
  `ros2_ws/src/jcheng_system_core/jcheng_system_core/safety.py`
- `jcheng-perception@b401767`：`docs/TOPICS.md`、`README.md`、
  `evidence/README.md`、`docs/EVIDENCE.md`
- `jcheng-manipulation@a08b8b6`，基线 `v1.0.0=b3411e4`：
  `docs/phase0/ARMPI_5DOF_CONSTRAINTS.md`、`README.md`
- `jcheng-interfaces@3c55dd6`：`msg/MotionCommand.msg`、`action/ExecuteMotion.action`
- `jcheng-research@10b6cbc`：本报告与 MVE-0

---

## 附录 A. 自审（按 AGENTS.md §12）

### A.1 检查清单

| 检查 | 结果 | 说明 |
|---|---|---|
| 确认偏误？ | 部分缓解 | 报告纳入了论文真实机器人强结果、SkipVLA/GeomVLA 替代、以及“什么会改变结论”；但仍可能偏向现有架构 |
| 遗漏明显替代？ | 否（在范围内） | 比较了当前管线、GloVLA、SkipVLA、GeomVLA、full VLA、ACT/DP3、TAMP；未展开 RL/遥操作 |
| 混淆相关与因果？ | 已标注 | 论文的分解增益与真值中心、两个策略、固定语言混淆；归因为 C 级 |
| 未验证假设？ | 已标注 | 6 GB 量化、5-DoF 适配、小策略可行性均标 C/D |
| 过度解读论文？ | 已修正 | 88.5/90.0 标为作者报告值；不称为复现；统计幅度标不确定 |
| README 当实现？ | 已避免 | 外部仓库只读 README/官方要求；内部代码给路径/行号；无代码的 GloVLA 明确标注 |
| 虚构引用/链接？ | 已核查 | 所有 arXiv 编号/仓库均经 abs 页或 API 核实；未使用无法核实的二手 2026 编号 |
| 推荐适合当前项目？ | 是（条件式） | 现在不引入运行时；采纳门禁/评测/schema；小策略仅仿真 MVE |
| 足以指导下一步？ | 是 | 给出 MVE-0 已运行、MVE-1/2/3 未运行及触发条件 |

### A.2 自审中发现并修正的问题

1. **最初把“GloVLA 不可部署”写得太绝对**。修正为“四个 backbone 在 6 GB
   上不可部署；分解与小策略仍可测试”。前者是硬件事实，后者是研究假设。
2. **最初把 “obstruction” 当成物理避障**。修正为“论文未说明物理占道还是
   视觉遮挡；控制器无碰撞检查；不能外推为物理避障”。
3. **最初考虑引用二手博客的 LIBERO 饱和数字**。删除了无法核实的 MINERVA/
   MetaFine/审计数字；只保留 LIBERO-Plus/PRO 的一手摘要与 repo。
4. **最初把 88.5% 写成“验证”**。修正为“作者报告值；A 级来源，但不是独立
   复现；迁移判断 C 级”。
5. **最初漏掉“两个局部策略 vs 一个 full policy”的容量混淆**。补入 F6；
   这是论文自己写明的事实，直接影响因果归因。
6. **最初漏掉“固定阶段指令”**。补入 F7；语言 grounding 被外置到 SAM3/真值，
   VLA backbone 的必要性未被消融。
7. **最初把 `v1.0.0` 的 tag object SHA 当作 commit**。修正为 annotated tag
   `v1.0.0` 指向的 commit `b3411e4`；tag object 是 `6436e2b`，不用于引用。
8. **最初把 28.2 s 当作 per-query 延迟**。修正为“per-episode 总推理时间；
   per-query 是从步数反推的 C 级估计”。
9. **最初漏掉“现有误差预算 bound 未过 6 mm”**。补入 §03/§12；经验均值
   3.080 mm 不等于 bound 通过。
10. **最初把 “no additional demonstrations” 读成“零数据”**。修正为
    “复用原始 full-task 演示；仍需演示与训练”。

### A.3 剩余不确定性（不掩饰）

- 论文的真实机器人演示数量、训练协议、SAM3 η、ε/K_p/S 均缺失；无法判断
  90.0% 的可复现性。
- 6 GB 上的量化/offload 未测试；不能排除“某种工程 hack 能跑”，但官方不支持，
  按 D 级处理。
- 5-DoF 适配没有实现；动作空间改造的难度是推断，不是实测。
- 现有管线的分级扰动评测未做；不能断言它在 clutter/obstruction 下的真实
  成功率。
- 本报告不是独立评审；结论应视为“可执行的决策建议”，不是“最终科学定论”。

---

**一句话**：GloVLA 的分解是对的，论文的真实机器人结果也值得认真对待；但在
5-DoF、6 GB、零演示、`ExecuteMotion` 安全边界的 JCHENG 上，它现在是一个
**值得借鉴其门禁与评测、但不值得直接部署的运行时**。先做 MVE-2（现有管线的
扰动评测）和 MVE-1（仿真小策略），再决定是否碰 VLA。
