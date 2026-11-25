# ROS2SmolVLA — 把 SmolVLA 接到工业轻量机器人的 ROS 2 接口

- **类型**：一手论文（Procedia Computer Science 2026 校样，10 页全文）+
  5 个 Apache-2.0 仓库的静态源码审计。
- **访问日期**：2026-11-25
- **阅读范围**：论文全文 10 页（§1–§5、图 1–2、表 1–3）；代码
  `ros2smolvla_interface_lerobot` @ `470be64b38b5` 与
  `ros2smolvla_interface_camera` @ `6da3f71b0c4f` 已 `git clone --depth 1`
  静态阅读；**未构建、未运行**。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/06_ROS2SmolVLA.pdf`
  （10 页，2,764,225 字节）。**未入库**：第三方出版物 + 5 MB 门禁。
- **许可**：论文文本 **CC BY-NC-ND 4.0**（不可商用、不可演绎）；代码
  **Apache-2.0**（可商用）。两者许可分层，引用时不要混用。

## 来源

- Mandischer, N.; Böckmann, N.; Holl, L.; Mikelsons, L. *ROS2SmolVLA:
  Enabling Small Vision-Language-Action Models for Integration into
  Industrial-Grade Lightweight Robots*. **Procedia Computer Science** 2026
  （校样，卷期页未定；8th International Conference on Industry of the Future
  and Smart Manufacturing）。arXiv:2608.23320v1, 2026-08-24.
  <https://arxiv.org/abs/2608.23320>
- 项目入口：<https://una-auxme.github.io/en/projects/ros2smolvla/>
- 代码（均 Apache-2.0，HTTP 200，2026-11-25）：
  - <https://github.com/una-auxme/ros2smolvla_docker> @ `92d3d1c43bf5`
  - <https://github.com/una-auxme/ros2smolvla_ur10e_real>
  - <https://github.com/una-auxme/ros2smolvla_ur10e_sim>
  - <https://github.com/una-auxme/ros2smolvla_interface_lerobot> @ `470be64b38b5`
  - <https://github.com/una-auxme/ros2smolvla_interface_camera> @ `6da3f71b0c4f`
- 模型/数据：Hugging Face `una-auxme/ROS2SmolVLA_ur10e_no_joints_crop_pick_place`
  （450,046,176 参数）、训练集 349 episodes / 325,838 帧 / 30 fps、
  评估集 244 episodes。
- 论文未给出版方 DOI；Crossref 截至访问日无命中。代码仓库 README 明写
  **Ubuntu 24.04 + ROS 2 Jazzy**，不是 Humble。

## 论文声称的核心结果（作者报告值，未独立复现）

- 真实 UR10e + Robotiq Hand-E，349 条遥操作示教，9 组场景 T1–T9。
- 聚合成功率：**pick 77.72%、place 63.59%、place-after-pick 81.69%**；
  ID（T1/T3/T4）pick 78.33%、place 72.50%；OOD（T2/T5/T8/T9）pick 76.56%、
  place 46.88%。
- 作者结论：**“success rates are currently too low for real-world
  deployment”**（§5）。
- 训练：SmolVLA 450M，200,000 steps，batch 64，单种子 1000，bf16；
  最终在 **NVIDIA L40S** 上训练约 **25 h**；推理在 **RTX 4080 16 GB** 工作站。
- 边缘侧：Jetson AGX Orin 只做三路相机流汇聚/拼接，10 GbE 交换机。
- 颜色/纹理偏置：黄/橙 pick 低于灰；双色无序时 75% 选绿；提示 gray 时仅
  20–30% 遵从；作者自述颜色区分能力“negligible”。放置由“蓝色”触发：
  橙箱 found 100% 但 place 17%。

## 方法要点

- **输入**：3 路 RGB（2× Azure Kinect 俯视/前视 + 1 个腕部 webcam），
  裁剪到 256×256；本体状态为末端笛卡尔位姿（发布数据集为 7 维
  `pose.xyz + quat`，不含关节角）。
- **输出**：7 维笛卡尔增量（6 维速度 + 夹爪），以 `TwistStamped` 发布，
  经 Cartesian Operator → FZI `cartesian_motion_controller` 跟踪；也支持
  关节轨迹、MoveIt Servo 等通路。
- **SmolVLA**：SmolVLM-2 主干、每帧 64 visual tokens、Action Expert
  层跳过、Flow Matching 生成动作；`chunk_size=50`、`n_action_steps=50`、
  flow 采样 10 步（HF 配置）。
- 30 fps 下 50 步 chunk ≈ **1.67 s 开环**；论文未报告推理频率/端到端延迟。

## 代码审计（静态，A 级）

- **动作空间硬编码 6-DoF + 夹爪**：
  `lerobot_robot_ros/config.py:46-55` 默认 `joint_1..joint_6`；
  `:58-67` 的 `action_features` 固定 6 维速度 + `gripper.pos`；
  `:68-71` 关节模式固定 6 个 `*.pos`。5-DoF 臂不能直接套用。
- **直接发布控制器话题，绕过运动权威**：
  `ros_interface.py:82-114` 创建 `/arm_controller/joint_trajectory`、
  `/gripper_controller/joint_trajectory`、`TwistStamped` 发布器；
  `robot.py:128-190` 的 `send_action()` 直接 publish，只有
  `max_relative_target` 幅度裁剪，**没有 lease、deadman、stop latch、
  工作空间/姿态限制**。在 JCHENG 中这等于绕过 `ExecuteMotion`，不可接受。
- **ROS 2 Jazzy**：仓库 README 明写 “tested on Ubuntu 24.04 with ROS2 Jazzy”；
  Dockerfile `ARG ROS_DISTRO=jazzy`。机器人侧是 Humble，需降级验证。
- **依赖**：`lerobot-ros` fork、`ros2_control`/MoveIt Servo、Azure Kinect
  驱动（已停产）、Robotiq Hand-E 驱动。许可 Apache-2.0，但上游 `lerobot`
  与相机驱动需逐一复核。

## 批判性评估

- **无 baseline**：没有经典流水线、ACT/Octo/π0.5、同模型不同输入的对照。
  在 5×5 网格、固定相机、固定光照的立方体入箱任务上，经典“固定抓取位姿 +
  颜色阈值/ArUco + 预设放置点”很可能接近 100%。77.72/63.59 只能证明
  “能跑通”，不能证明“VLA 值得用”。
- **“ID”是训练集内插**：T1/T3/T4 的格点就是训练网格点（5×5 每点 5 次），
  78.33% 不能读作泛化。
- **样本量小且未声明**：T1–T7 的百分比都是 10% 的整数倍，T8/T9 是 1/6 的
  整数倍；反算每格 n=10 或 6，合计 **184 次真实试验**（本评审推断，四点
  精确吻合）。n=10 的 Wilson 95% 区间宽约 ±25–30 pp，“90%”与“50%”在统计上
  不可分。
- **发布物与论文不一致**：论文 §4.1 称数据含“three camera views, the joint
  states, and the Cartesian end effector position”；实际数据集/模型名是
  `no_joints`，`observation.state` 只有 7 维位姿，而 `train_config.json`
  又声明 9 维。三处不一致，说明发布权重与训练集可能不是同一版本。
- **评估集 244 episodes，论文只评分 184 次**；约 60 条已录制回合未进入任何
  表格，原因未说明。
- **“工业级”缺安全论证**：没有速度/力/碰撞限制量化，没有急停、安全 PLC、
  协作速度监控、风险评估。用“industrial-grade”形容 UR10e 硬件可以，形容
  整条链路过度。
- **延迟/显存/控制频率全部缺失**：论文只说 “low latencies”；无法判断
  50 步开环是否满足节拍，也无法判断 3060 6 GB 是否够用。
- **负面结果被转写成正面叙事**：黑箱/纸箱 place 17% 被写成“可利用的颜色
  编码设计”，这是工程洞察，但不能计入性能。

## 代码与数据

- **代码、权重、训练/评估数据确实公开且可克隆**（`git ls-remote` 验证），
  这是本批次中可复现性最好的一篇。
- 但可复现 ≠ 可迁移：需要 UR10e + Hand-E、Azure Kinect（停产）、Jazzy/
  Ubuntu 24.04、RTX 4080 级推理；且动作空间/控制通路与 JCHENG 不兼容。
- 复现风险：中（代码在，但硬件与维度不匹配）。

## 与 JCHENG / ArmPi Ultra 的适配

- **自由度硬阻断**：6 维笛卡尔 delta 在 5-DoF 上不可实现；必须降维
  （如 xyz + yaw）或退回关节空间，二者都要重新采数/重训，“跨本体”卖点
  消失。
- **软件栈**：Jazzy vs Humble；`ros2_control`/MoveIt Servo 依赖在 Humble
  上需降级验证。
- **安全边界**：`TwistStamped`/`JointTrajectory` 直接进控制器，绕过
  `ExecuteMotion` 的 lease/deadman/stop latch。可行形态是 VLA 只发布
  短意图，由 system 层切片、限速、逐条下发；50 步开环需切成 ≤5 步。
- **算力**：450M bf16 权重约 0.9 GB，3×256×256、batch 1 在 6 GB 上
  “理论可行”，但 KV cache、50 步 chunk、CUDA graph 开销未测。**未验证**，
  必须做显存/延迟 MVE。
- **正面可借鉴**：边缘汇聚/工作站推理的解耦、容器化、训练集/评估集分开
  发布、`TwistStamped` 作为能力层→系统层的意图接口形态。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | 450M SmolVLA 的代码/权重/数据公开可克隆 | A（GitHub/HF 核实） | **采纳**为 VLA 沙箱候选 |
| 2 | 作者自述成功率不足以真实部署（77.72 pick/63.59 place） | A（论文） | **采纳**为负面结论 |
| 3 | 颜色/纹理偏置严重，语言条件在非主导颜色上失效 | B（T7 真实数据，n=10） | **采纳**为强制验收项 |
| 4 | 动作空间 6-DoF、直接 publish 控制器、Jazzy | A（源码/README） | **不采纳**运行时；需重写适配层 |
| 5 | 无 baseline、ID 是训练内插、n≈184 | A（论文/反算） | **不采纳**其性能主张 |
| 6 | 边缘汇聚/工作站推理、容器化、数据分开发布 | B（工程实践） | **仅借鉴** |
| 7 | 6 GB 上可推理 | D（未实测） | **待验证**，先做 MVE-3 |

## 核验片段

1. “a highly lightweight 450M-parameter foundation model” — §2.1, p.3
2. “The VLA is computed on a workstation with consumer-grade hardware (Nvidia RTX 4080, 16GB VRAM, 32GB RAM).” — §4.1, p.6
3. “The dataset with a total of 349 episodes is available via Hugging Face” — §4.1, p.6
4. “Training on the server took about 25 hours.” — §4.1, p.6
5. “In the ID cases (T1, T3, T4), the success rates were [78.33%, 72.50%, 92.47%].” — §4.2, p.8
6. “Among all test cases the success rates were [77.72%, 63.59%, 81.69%].” — §4.2, p.8
7. “The system effectively ignored the condition and defaults to its inherent bias for the green cube.” — §4.3, p.8
8. “the validation showed that the model uses blue as a primary trigger for place actions” — §4.4, p.9
9. “the success rates are currently too low for real-world deployment” — §5, p.9
10. “depth information is currently not supported by the LeRobot dataset format” — §5, p.9
11. “tested on Ubuntu 24.04 with ROS2 Jazzy” — `ros2smolvla_docker/readme.md`（非论文，2026-11-25）
12. `config.py:46-55`（6 个关节名）、`robot.py:128-190`（直接 publish）、
    `ros_interface.py:82-114`（控制器话题）— 本仓库克隆 @ `470be64b38b5`

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)
与 MVE-3（SmolVLA 6 GB 回环）。结论：**不直接接入机器人**；可作为离线
VLA 沙箱，验证显存/延迟后再讨论 5-DoF 动作重映射。
