# 研究任务书与预注册设计 — VP-VLA 视觉提示接口在 ArmPi Ultra 上的可迁移性

> **文档性质**：研究任务书 / 预注册设计（pre-registration），**不是调研报告**。它定义问题、边界、证据标准和实验，不给出技术选型结论。
>
> **状态**：待执行（draft task book）。**日期**：2026-11-25。
> **作者**：ZCode（研究代理），for J. Cheng。**评审**：pending。
>
> **面向决策**：M6/M7 是否、以及以何种形式，把 VP-VLA 式学习型操作策略引入 JCHENG；具体是整栈微调 System 1、只复用“视觉提示接口”，还是继续现有解析管线。
>
> **研究边界**：桌面研究 + 只读代码审计 + 允许的离线/仿真实验；不默认获得 GPU 训练资源或实机运动授权。**未运行 VP-VLA 代码、未访问机器人。**
>
> **一手材料**：[论文 PDF](../../references/papers/20261125-vp-vla.pdf) · [来源记录](../../references/vp-vla.md) · [arXiv](https://arxiv.org/abs/2603.22003) · [代码仓库](https://github.com/JIA-Lab-research/VP-VLA)
>
> **相关报告**：[LingBot-VLA 2.0 / SST 前景提示配方评估](../../reports/20261125-lingbot-vla-sst-foreground-prompting.md)

## 任务摘要

- **要回答什么**：视觉提示接口是否比现有解析管线更好；如果更好，整栈微调还是只复用接口层。
- **三条主路线**：A 解析基线；B 接口层复用（VLM + SAM3 + 深度/TF + 现有执行）；C 整栈 VP-VLA（5-DoF 微调 System 1）。
- **最大未知**：5-DoF 动作空间迁移、3060 显存/延迟、事件触发信号、演示数据与训练成本。
- **交付**：13 节报告 + 来源记录 + MVP 实验设计/结果；未运行的部分明确标注。

---

## 1. 研究主题

**VP-VLA 的“视觉提示接口”能否在 ArmPi Ultra（5-DoF、无编码器、Pi 5 + RTX 3060、ROS 2 Humble）上落地：整栈迁移、接口层复用与解析基线三条路线的精度、延迟、数据与安全成本对比。**

- 对象论文：Wang, Chen, Liu, Ye, Chen, Lu, Liu, Yu, Jia。*VP-VLA: Visual Prompting as an Interface for Vision-Language-Action Models*。arXiv:2603.22003v3，2026-05-09，25 页，preprint，**CC BY 4.0**。
- 对象代码：`JIA-Lab-research/VP-VLA` @ `5d92396e96ef3a20eacfeecb4771db6b1016b93f`，**MIT**（Copyright StarVLA Team），代码 2026-04-12 发布；权重链接见 README 的 HF collection `Vincent2311/vp-vla`（模型卡许可待核）。
- 术语澄清：论文的 “visual prompt” 是叠加在 RGB 上的 crosshair/bbox，不是给 VLM 的文本提示（不是 SoM 意义上的 visual prompting）。
- 不研究：VP-VLA 在原始 Franka/RoboCasa 设置上的算法改进；不复现论文 headline；不评估与 ArmPi 无关的人形/双手机器人结果。

---

## 2. 项目背景

### 2.1 仓库与分层

| 仓库 | 层 | 与本任务的关系 |
|---|---|---|
| `jcheng-system/` | L2 | 安全状态机、租约、仲裁器、硬件桥；唯一运动入口 `ExecuteMotion`；MoveIt 仅 plan-only |
| `jcheng-perception/` | L3 | D435i 外部 + Aurora 930 腕部；深度/TF 时间戳环、反投影、双视图融合、Kalman；只输出 advisory targets |
| `jcheng-mobile/` | L3 | 底盘/导航；本任务仅在“移动操作”扩展时相关 |
| `jcheng-interfaces/` | L1 | `MotionCommand`/`ExecuteMotion` 契约；本任务不得改契约 |
| `jcheng-manipulation/` | 冻结 | v1.0.0 基线 + ArmPi Debug Studio；潜在遥操作/数据采集入口 |
| `jcheng-ops/` | OPS | 健康探针/看门狗；不在本任务范围 |
| `jcheng-research/` | Research | 本任务书、报告与实验记录所在仓库 |

### 2.2 当前技术架构（与本任务相关的部分）

- **感知**：`jcheng-perception` 在 Pi 5 边缘做采集/时间戳环，在笔记本 GPU 上跑 YOLO；外部 D435i 负责 `SEARCH/COARSE/DROP_RECHECK`，腕部 Aurora 930 负责 `FINE`（640×400，RGB ~6.7 Hz，depth 3.1–6.4 Hz，0.10–0.90 m）。腕部 TF 由**总线实测关节 + URDF FK** 发布为 `camera_optical_measured`（10 Hz），明确不用厂商 `/joint_states` 命令缓存。
- **运动**：能力层只能提交意图；`MotionCommand` 支持 `JOINT_TRAJECTORY / JOINT_STEP / POSE / HOME / BASE_PULSE / GRIPPER`，带 `lease_id`、`idempotency_key`、`verify_bus`、`require_measured_state`。仲裁器负责租约、deadman、限位、停止闩锁；`jcheng-system` 是唯一运动来源。
- **安全**：无 e-stop、无抱闸、无编码器、无 IMU、无力传感、无自碰撞模型；软件停止不是急停；每次实机运动需单独、显式授权；`/joint_states` 不能作为测量真值，完成/位姿真值来自 `GetBusServoState`。
- **数据**：没有遥操作演示数据集；Studio 可手动控制但未形成训练集；现有证据以静态标定/静态双视图为主。
- **契约**：`jcheng-interfaces` 钉在 v0.1.0，contract hash `sha256:0b8d72ced7f54d444d6851d8b99a51a78e2bed3f687324f51a15f76557f24b42`；本任务不得改契约。

### 2.3 硬件环境

| 项 | 事实 | 对本任务的含义 |
|---|---|---|
| 机械臂 | ArmPi Ultra，5-DoF 总线舵机臂 + 平行夹爪 | 论文验证平台是 7-DoF Franka、6-DoF WidowX、人形 GR1；**没有 5-DoF 证据** |
| 计算（机器人） | Pi 5 8 GB，ROS 2 Humble | 不可能本地托管 4B VLM + SAM3 + 4B policy |
| 计算（操作员） | 笔记本 RTX 3060，显存未在工作区记录 | 论文推理用 1×4090 24 GB；3060 的 6 GB/12 GB 版本决定可行性 |
| 相机 | 外部 D435i（0.15–2.0 m）+ 腕部 Aurora 930（0.10–0.90 m，640×400） | 论文提示叠在“overhead/third-person”视图；我们的外部相机是底盘前置，不是俯视，遮挡/视角不同 |
| 传感 | 无编码器、无 IMU、无力/力矩、无 e-stop | 事件触发、动作标签、安全校验都缺硬件真值 |
| 网络 | 机器人侧互联网访问未确认 | 论文延迟测试用 OpenRouter 云端 8B；若机器人无网，云端 planner 不可用 |

### 2.4 已有证据与已知限制

- **静态精度**：AprilTag 定义点双视图 3.77 mm；split-ingress 静态 60 s 跨视图 1.55 mm；定点 5 mm 门限下 3.67 mm（depth）/ 3.07 mm（PnP）。来源：`jcheng-perception/evidence/README.md`。
- **腕部多姿态**：历史运行 ≤4 mm PASS；但**动态/运动中的 TF 滞后未验证**，不能把 1.55 mm 当作全场景保证。
- **未验证项**：移动中的多姿态精度、TF 时间同步、5-DoF 笛卡尔 IK 的成功率、总线夹爪读取速率/超时行为。
- **先前 VLA 结论**：`reports/20261125-lingbot-vla-sst-foreground-prompting.md` 的结论是“现在不引入运行时 VLA，先做小的 3D/BC 策略（DP3/ACT 量级）”；本任务要检验 VP-VLA 的解耦设计是否改变该结论的**边界条件**，而不是直接沿用或推翻。

### 2.5 为什么现在评估 VP-VLA

VP-VLA 把 System 2（Qwen3-VL-4B 规划 + SAM3 分割）与 System 1（QwenOFT/Qwen3-VL-4B 控制器）解耦，接口是 RGB 上的 crosshair/bbox。理论上，这意味着**可以不训练 System 1，只复用接口层**：VLM 选目标、SAM3 出掩码、深度/TF 反投影到 3D，再走现有 `ExecuteMotion`/IK。这与“整栈 VLA”是两种完全不同的成本结构，必须分开评估。论文的验证平台、算力和数据规模都与 ArmPi 差距很大，因此需要一次可迁移性调研，而不是直接选型。

---

## 3. 核心研究问题

**主问题**：在 ArmPi Ultra 的真实约束下，VP-VLA 的视觉提示接口是否比现有解析管线带来可测量的精度/鲁棒性增益；如果带来，应该整栈微调 System 1，还是只把接口层作为 `perception → system` 的中间表示？

### 3.1 子问题

| # | 子问题 | 判定标准 / 可能的反例 |
|---|---|---|
| Q1 | **接口层**：VLM + SAM3 产生的 crosshair/bbox，相比现有 YOLO + 深度 + TF 的 target，是否让下游在 mm 误差、成功率、OOD 上更好？ | 增益需超过标定噪声；若接口层自身 3D 误差 > 现有基线 + 3 mm，则收益不成立；反例：论文只报 success rate，不报 mm；bbox 无深度；SAM3 在透明/反光/小物体上失败未量化 |
| Q2 | **具身迁移**：7-DoF/6-DoF 的 action chunk 迁移到 5-DoF + 平行夹爪，需要动作空间投影、重训还是数据增广？ | 论文/代码是否有任何 5-DoF 或跨具身证据；反例：5-DoF 不能任意定向，直接投影会丢姿态/不可达 |
| Q3 | **事件驱动**：论文用夹爪开合（或 z 轴抬升）作为子任务切换；ArmPi 的 `/joint_states` 是命令缓存、总线读无安全超时。哪些替代信号可靠？ | 误触发/漏触发率、最坏延迟、抓取失败（物体滑落）后的恢复；反例：夹爪命令缓存导致事件永远不触发或提前触发 |
| Q4 | **计算与延迟**：4B planner + SAM3 + 4B policy 三服务在 RTX 3060/Pi 5 上的可行配置与端到端延迟？ | 显存峰值、首动作延迟、chunk 频率、最坏延迟；反例：论文 0.78 s 是 8B API、0.36 s 是 4090 上的 SAM3，不是 4B 本地 + 3060 |
| Q5 | **数据、成本与许可**：复现/微调需要多少演示、GPU 小时、多少钱？许可是否允许？ | 论文：8×H200 140 GB 约 46 h 全量训练；真实任务 50 演示/物体、200 演示（4 色蛋）、10k steps、8 GPU、batch 256；反例：真实数据未发布，5-DoF 数据需自采；SAM3 是自定义许可 |
| Q6 | **安全与架构**：如何把 VLA 提议嵌入 `ExecuteMotion`/租约/限位/停止闩锁，而不破坏“唯一运动入口”？VLM/SAM 错误如何被独立校验？ | 独立几何一致性、工作空间、双视图一致性、置信度检查；反例：论文无安全层、无碰撞模型，端到端策略可能输出不可达/碰撞动作 |
| Q7 | **证据质量**：论文的 +5.0/+8.3 是否统计显著？消融是否支持“视觉提示接口”本身？ | 论文未报告置信区间/显著性检验；分项有胜有负（RoboCasa Tray 46.0 vs 49.2、Plate 53.5 vs 61.0）；消融 “w/o decomposition” 57.3 vs 58.3；真实机器人每条件 10/5 trials |

### 3.2 待检验假设（不是结论）

- **H1**：接口层可以独立复用；不训练 System 1，仅用 VLM + SAM3 + 深度 + IK 就能获得大部分定位/OOD 收益。
- **H2**：整栈迁移到 5-DoF 的主要障碍是动作空间与数据，而不是视觉提示本身。
- **H3**：3060 无法在论文延迟内串行跑三服务，但异步/分机（planner 在笔记本、policy 在边缘/云）可行。
- **H4**：夹爪状态在 ArmPi 上不可直接作为事件信号，必须换成总线实测位置/腕部 TF 运动/视觉变化。

### 3.3 什么会改变结论

- 若 5-DoF 动作投影可行且只需少量演示 → 整栈路线复活。
- 若接口层单独复用即可达到 4 mm/成功率目标 → 不需要训练 System 1。
- 若 3060 只能跑量化模型且延迟不可接受，但分机可行 → 架构改为“笔记本 planner + 边缘 policy”。
- 若 SAM3 在透明/反光物体上失败率高 → 接口层的鲁棒性收益不成立。
- 若论文增益在复算后不显著 → 整栈路线的优先级下降，接口层仍需独立评估。

---

## 4. 约束条件

| 类别 | 硬约束 | 影响 |
|---|---|---|
| 计算 | Pi 5 8 GB ARM64；笔记本 RTX 3060（显存未记录）；无 8×H200 | 训练/评测必须在云端或降级；推理可能需量化/分机 |
| 软件 | 机器人侧 Humble；本机 Jazzy；Python 3.10/3.12；CycloneDDS；一个图一个 RMW | 不能直接复用论文的 Python 3.10 + starVLA 环境到机器人侧 |
| 契约 | `jcheng-interfaces` v0.1.0、contract hash 固定；能力层只提交意图 | 不改 `ExecuteMotion`；VLA 不能直连舵机/总线 |
| 硬件 | 5-DoF + 平行夹爪；无编码器/IMU/力传感/e-stop；总线读无安全超时 | 动作空间、事件触发、安全校验都要重新设计 |
| 数据 | 无遥操作数据集；无可靠动作标签；感知只给 advisory target | 不能假设有论文规模的演示数据 |
| 安全 | 运动只经 `ExecuteMotion`；每次实机运动单独授权；无 e-stop | 任何闭环实验必须先离线/影子，不能无人值守 |
| 合规 | 权重不入 git（`/opt/jcheng/models/`）；无 LICENSE 的 repo 不得添加 LICENSE；SAM3 自定义许可 | 需逐条核对 Qwen3-VL（Apache-2.0）、SAM3、VP-VLA 权重、starVLA 的许可 |
| 时间/成本 | 单操作员；单条外部命令 ≤90 s；连续工作 40 min 提醒；3 次失败停止 | 研究计划按 4–5 个工作日估算，不承诺 8-GPU 复现 |

### 4.1 非目标 / 硬边界

- 不在未授权情况下让机器人运动；不重启厂商容器；不修改只读的 `~/ArmPiUltra/`。
- 不把 VLA 直接接进舵机/总线；不绕过仲裁器/租约/限位。
- 不提交模型权重、录制数据、厂商源码或私有计划。
- 不在 90 s 命令上限外无限等待；不重复启动进程/重复跑已完成的测试。
- 不要求复现 24 tasks × 50 trials 的完整 RoboCasa 评测；不把仿真/回放结果写成硬件验证。

---

## 5. 调研要求

### 5.1 证据标准

1. **全文精读**论文正文 + 附录 A–H，逐条核对数字；不以 abstract 或项目页判断。
2. **代码 pin 在 SHA**：`5d92396`；每个代码主张给出文件路径 + 符号 + 行号；区分静态分析、实际执行、推断。
3. 每条关键结论标 **S/A/B/C/D**：S 本机复现；A 一手论文/源码/官方文档；B 可信二手；C 推断；D 未验证假设。
4. 未运行的内容必须写“未执行”；仿真/回放结果不得写成硬件验证。
5. 主动找反例：失败案例、负面结果、许可证限制、论文未报告的量（mm 误差、置信区间、SAM3 失败率、真实机器人消融）。

### 5.2 必读来源

- **论文**：正文 §3（方法）、§4（实验）、§4.5（消融）、附录 A（局限）、B（算力）、C（延迟）、D（工具使用）、F（扩展消融）、G（planner prompt）。
- **代码**：`data_preparation/`（VLM 子任务 + SAM3 掩码）、`examples/*/train_files/`（grounding loss、`feed_both_images`）、`deployment/model_server/`、`examples/*/visual_prompt_utility/sam3_server.py`、eval wrappers。
- **上游**：starVLA、Qwen3-VL-4B-Instruct、SAM3、OpenVLA-OFT、QwenOFT。
- **对比论文**：π0.5、GR00T N1.6、OpenVLA-OFT、Hi Robot、CoT-VLA、TraceVLA、Point-VLA、RoboGround、DexGraspVLA。
- **鲁棒性/失败案例**：LIBERO-PRO/PLUS、SAM3 的透明/反光/小物体/遮挡失败、VLM 空间 grounding 误差、双系统延迟。
- **许可**：VP-VLA（MIT）、Qwen3-VL（Apache-2.0）、SAM3（NOASSERTION/Other，需读条款）、starVLA（NOASSERTION，需读条款）、HF 权重卡。

### 5.3 代码与复现边界

- 先做**静态审计**：确认哪些代码/权重真正发布，训练脚本是否能在非 8-GPU 环境启动，`feed_both_images`、grounding loss、event trigger 的实现是否与论文一致。
- 若 3060 可跑通 **inference-only**：记录显存峰值、首动作延迟、chunk 频率、量化设置；跑不通就明确写“未执行”，不猜。
- 仿真复现**不要求** 24 tasks × 50 trials；最低配置是 1 个 SimplerEnv 任务、固定 seed、N=20，记录失败分类。
- 真实机器人只做**离线回放/影子模式**（相机流 + 三服务，不接执行）；如要闭环运动，单独申请授权，按 `.github/docs/hardware-workflow.md` 执行。

### 5.4 对比路线与统一指标

| 路线 | 描述 | 关键问题 |
|---|---|---|
| A 解析基线 | 现有 YOLO + 对齐深度 + TF + IK/MoveIt | 当前 4 mm/成功率的上限在哪 |
| B 接口层复用 | VLM planner + SAM3/GroundingDINO + 深度/TF + 现有执行 | 不训练 policy 能拿到多少收益 |
| C 整栈 VP-VLA | 论文 System 2 + 在 5-DoF 数据上微调 System 1 | 5-DoF 迁移、数据量、GPU 成本 |
| D 小规模 BC/ACT/DP3 | 5-DoF 原生、无 VLM | 更简单的学习基线是否足够 |
| E 经典视觉伺服/IBVS | 图像空间闭环，无学习策略 | 精度/鲁棒性是否被低估 |
| F 其他基础模型微调 | π0.5/GR00T，如权重/许可允许 | 跨具身证据是否更强 |

**统一指标**：3D 定位误差（mm）、prompt 像素误差、跨视图一致性、抓取/放置成功率、OOD 成功率、首动作延迟、chunk 频率、最坏延迟、显存/CPU、演示数、标注小时、GPU 小时、云成本、许可、集成工作量、回滚成本。

### 5.5 最小可行实验（MVP）

| 编号 | 内容 | 是否运动 | 通过判据 | 失败判据 |
|---|---|---|---|---|
| E0 | 离线：用现有录制的双视图数据，比较 VLM + SAM3 prompt vs 人工标注 vs 现有 YOLO 的像素/3D 误差 | 否 | 接口层 3D 误差 ≤ 现有基线 + 1 mm，且 OOD 不更差 | 误差 > 基线 + 3 mm，或透明/反光物体失败率 > 30% |
| E1 | 影子：真实相机流跑三服务，记录延迟/失败/显存 | 否 | 首动作延迟 ≤ 1.5 s，chunk ≥ 2 Hz，连续 10 min 无崩溃 | 延迟 > 3 s，或服务崩溃/显存溢出 |
| E2 | 单任务闭环：授权下 5-DoF 做 1 个 pick-place，A/B/C 各 N=20 | 是 | C 或 B 的成功率 ≥ A + 10 pp，且无安全拒绝 | 成功率不高于 A，或出现不可达/碰撞/超限 |
| E3 | 扩展：3 任务 + OOD，N=20/任务 | 是 | 复现 E2 方向且 OOD 不崩 | OOD 下降 > 20 pp，或维护成本超预算 |

E0/E1 可立即做；E2/E3 必须单独授权，且先通过 `jcheng-system` 的限位/工作空间校验。

### 5.6 交付物

1. `reports/20261125-vp-vla-armpi.md`：13 节报告，含推荐/备选/拒绝理由。
2. `references/vp-vla.md`：论文/代码/权重/许可的来源记录（本任务书已附）。
3. `experiments/20261125-vp-vla-armpi/design.md` + `data/` + `logs/` + `result.md`（未运行则写“未执行”）。
4. 一页决策摘要：推荐路线、三条支撑事实、主要风险、下一步。

### 5.7 研究计划与停止条件

| 阶段 | 内容 | 建议时间 |
|---|---|---|
| P0 | 确认 3060 显存、SAM3 条款、HF 权重许可、机器人网络/授权 | 0.5 天 |
| P1 | 论文 + 代码审计，建立“主张—证据”表 | 1 天 |
| P2 | 替代路线 + 反例，填对比矩阵 | 1 天 |
| P3 | E0/E1 离线/影子实验 | 1 天 |
| P4 | 报告 + 批判性自审 | 0.5–1 天 |

**停止条件**：关键主张有 3 个独立来源；或已找到决定性约束（如无 5-DoF 证据 + 算力/数据成本超预算）；或下一轮检索的边际收益低于成本。工具连续失败 3 次即停止重试，转文档记录。

### 5.8 提交前的批判性审查

- 是否把作者主张写成已验证事实？
- 是否把 7-DoF/6-DoF 结果当成 5-DoF 证据？
- 是否把 8B API 延迟当成 4B 本地延迟？把 4090 当成 3060？
- 是否把仿真/回放结果写成硬件验证？
- 是否混淆 success rate 与 mm 精度？
- 是否只引用支持 VP-VLA 的材料，漏掉反例/替代路线？
- 是否核对了 SAM3/Qwen3-VL/权重许可？
- 是否明确写出“未执行”的部分？

修正后再提交。

---

## 6. 附 A：已核实的一手事实

| 事实 | 值 | 来源 |
|---|---|---|
| 论文版本 | arXiv:2603.22003v3，2026-05-09，25 页，preprint | PDF 首页 |
| 论文许可 | CC BY 4.0 | PDF XMP `dc:rights` |
| 代码 | `JIA-Lab-research/VP-VLA` @ `5d92396`，MIT（StarVLA Team），2026-04-12 发布 | GitHub API / README |
| 架构 | System 2：Qwen3-VL-4B + SAM3；System 1：QwenOFT（Qwen3-VL-4B），真实实验 chunk 16 | 论文 §3、§4.1、§4.4 |
| 训练算力 | 8×H200 140 GB，全量约 46 h | 附录 B |
| 推理算力 | 单卡 4090 24 GB | 附录 B |
| 延迟 | VLM 0.78 s（8B，OpenRouter）、SAM3 0.36 s、action chunk 0.108 s | 附录 C |
| RoboCasa | 53.8% vs QwenOFT 48.8%（+5.0） | 表 1 |
| SimplerEnv | 58.3% vs QwenOFT 50.0%（+8.3） | 表 2 |
| 真实垃圾分类 | ID 87.5% / OOD 85.0% vs 80.0% / 63.3% | §4.4、Fig. 5 |
| 真实彩蛋抓取 | ID 77.1% / OOD-color 75.0% / OOD-pos 75.0% vs 58.3% / 29.2% / 54.2% | §4.4、Fig. 5 |
| 真实蛋盒放置 | ID 91.25% / OOD 68.75% vs 70.63% / 55% | §4.4、Fig. 5 |
| 消融 | full 53.8；w/o grounding 49.4；all-frame 49.5；point 47.3；direct overlay 50.8 | 表 3 |
| 分解消融 | 57.3（w/o decomposition）vs 58.3（full），SimplerEnv | 表 6 |
| 真实机器人 | Franka Research 3 7-DoF，第三人称 + 腕部 RGB，224×224；50 演示/物体；10k steps；8 GPU，batch 256 | §4.4 |
| 局限 | 仅 2D bbox/crosshair；复杂任务需 3DGS/接触热力图 | 附录 A |
| Qwen3-VL 许可 | Apache-2.0 | HF API |
| SAM3 许可 | NOASSERTION / Other（自定义，条款未读） | GitHub API |
| starVLA 许可 | NOASSERTION（上游，需读条款） | GitHub API |

## 7. 附 B：待确认项

- RTX 3060 的显存（6 GB 笔记本版 vs 12 GB 桌面版）——工作区未记录。
- SAM3 自定义许可的具体条款（商用/再分发/模型输出）。
- VP-VLA HF 权重的模型卡许可。
- 5-DoF 笛卡尔 IK 是否可用、成功率、关节限位下的可达工作空间。
- 总线夹爪位置读取速率、超时行为、能否作为事件信号。
- 机器人侧是否能访问云端 VLM API（历史记录为无互联网，需复核）。
- Studio 遥操作的演示采集吞吐（条/小时）。
- 腕部相机作为 prompt 视图的可行性（论文用 overhead/third-person）。
- 动态/运动中的 TF 滞后与多姿态精度（现有证据为静态）。
- 历史定点运行中 10–14 mm 跨视图偏移的原始数据与结论（外参怀疑）。

## 8. 附 C：任务书自检

- **已修正**：不把“3060 跑不动”写成结论，改为 H3 待验证；不把“5-DoF 不可迁移”写成结论，改为 Q2；不把论文的 +5.0/+8.3 当作对 ArmPi 的增益；不把 0.78 s 当成 4B 本地延迟。
- **仍未验证**：3060 显存、SAM3 条款、HF 权重许可、5-DoF IK、总线夹爪读取、机器人网络。
- **边界声明**：本任务书基于论文全文与仓库 README/代码清单核对；**未运行代码、未访问机器人、未读 SAM3 许可全文**。因此上述项目均列为待验证，而不是既定事实。
- **偏见检查**：任务书同时保留 A（解析基线）、B（接口层）、C（整栈）、D（小规模 BC）、E（IBVS）五条路线，不预设 VP-VLA 优或劣；任何“不可行”必须由证据支撑。

## 9. 来源与版本

| 来源 | 版本 / commit | 许可 | 读取范围 |
|---|---|---|---|
| VP-VLA 论文 | arXiv:2603.22003v3，2026-05-09 | CC BY 4.0 | 全文 25 页，含附录 A–H；表格 1–12 |
| VP-VLA 代码 | `5d92396e96ef3a20eacfeecb4771db6b1016b93f` | MIT | README、文件树、训练/评测入口；未逐行审计 |
| Qwen3-VL-4B-Instruct | HF 模型卡 | Apache-2.0 | 仅许可元数据 |
| SAM3 | GitHub `facebookresearch/sam3` | NOASSERTION / Other | 仅许可元数据；条款未读 |
| starVLA | GitHub `starVLA/starVLA` | NOASSERTION | 仅许可元数据；条款未读 |
| 项目文档 | 本工作区 | — | `AGENTS.md`、`jcheng-perception/evidence/README.md`、`jcheng-interfaces` 契约 |

论文 PDF 的本地副本在 [`references/papers/20261125-vp-vla.pdf`](../../references/papers/20261125-vp-vla.pdf)（ghostscript 压缩，原始 9.6 MB，压缩后 1.1 MB；页数与文字可读性已核对）。
