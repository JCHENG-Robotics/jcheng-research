# RLinf 真机数据采集评估：AgileX Piper/Piper X 与 PICO VR

> Report status: **draft**. Date: 2026-11-26.
> Author: ZCode（研究代理），for J. Cheng. Reviewer: pending.
> Decision this informs: whether RLinf is a viable PICO VR teleoperation /
> data-collection path for the AgileX Piper X, and what must be built and
> verified before any hardware session.
> Research boundary: static review of RLinf at commit
> `ed0e1b836d11ec50eef4e5133e6b42ebd370cab9` (2026-11-26), the vendor SDK pinned
> by RLinf (`pyAgxArm@4b0f0658`), official docs, GitHub metadata and issue/PR
> search. **No RLinf install, no CAN, no PICO headset, no camera, no robot
> motion, no hardware verification.** All motion-related statements are
> design constraints, not measured results.

**证据等级**：**S** 在本机复现 · **A** 一手源码/官方文档 · **B** 可信二手资料 ·
**C** 基于现有证据的推断 · **D** 未验证假设。

---

## 01. Executive Summary

**结论：截至 2026-11-26，RLinf 不能直接对 AgileX Piper/Piper X 做 PICO VR
数据采集。** RLinf 的 PICO 数采链路是完整实现的，但它只接在 Franka、ARX5、
YAM、R2 等机器人上；Piper 只有“单臂硬件自检 + 关节 reach 任务”（后者可
在真机/仿真跑，但只是 bring-up 级的关节目标保持），没有
teleop、没有分集控制、没有 Piper 的数采配置。**这不是改一个 YAML 就能打开的
开关**：`PiperEnv` 在代码层拒绝所有 teleop 设备，且缺少 Pico 关节映射所需的
运动学事实。

三个支撑事实：

1. **官方能力矩阵明确把 Piper 的 Teleop / Data Collection 标为 `—`**，Piper
   专页原文：“RLinf does not ship a training task for AgileX Piper yet.”
   `rlinf/envs/real/piper/base.py:112` 的 `TELEOP = ()` 与
   `examples/embodiment/config/env/piper_reach.yaml:13-14` 的 `teleop: none`
   是代码级证据：Piper 环境当前**拒绝**任何设备，而不只是“未测试”。（A）
2. **PICO 链路本身可用，但有三条不同动作语义**：Franka 用
   `PicoDelta`（笛卡尔增量）、ARX5 用 `PicoTcp`（绝对位姿 + rot6d）、YAM/R2
   用 `PicoJoint`（经环境 IK 解成关节）。`PicoJoint.for_env()` 强制要求环境
   提供 `arm_kinematics` 与 `joint_step_limits`；`PiperEnv` 两者都没有。（A）
3. **Piper 驱动层反而比较完整**：RLinf 的 `PiperArm` 已接受
   `model: piper_x`、自动探测固件、AgxGripper、`move_j` 与关节/TCP 反馈；
   `pyAgxArm@4b0f0658` 支持 `piper_x`、离线 `fk()`、`move_p()`（控制器内部
   IK）和 TCP/法兰互转。缺的是 **Piper 的笛卡尔环境/动作/分集适配**，不是
   底层 CAN 驱动。（A）

**推荐**：

- 若目标是把 PICO 数采接到 **Piper X** 并保留 RLinf 的数据/训练管线：**不要
  走 `PicoJoint`**；仿照 ARX5 写一个 `PiperCartesianEnv`（`CARTESIAN_POSE` +
  `PicoTcp` + `PiperArm.move_p()` + `PicoEpisodeControlWrapper`），先做
  read-only 的 MVE-1，再做低速单臂 MVE-2。预估原型 3–5 天、可验证版本
  2–3 周（C，见 §09）。
- 若目标只是**尽快在 Piper X 上采演示数据**：先看
  `zcaklchgdm/piperx-pico-data-collector`（Apache-2.0，0.1.1 **source-only
  alpha**）——这是目前唯一按 **单臂 PiperX + PICO 4 Ultra + 双 RGB +
  LeRobot 转换** 验证过的公开实现：Ubuntu 22.04 x86-64、Python 3.11、
  SocketCAN 1 Mbit、60 Hz 遥操 / 30 Hz 训练行、7D 关节+夹爪；但它不是
  turnkey，必须配合同版本的 patched `pyAgxArm` 源码包并完成标定。另一个
  独立 ZMQ→`move_p`→LeRobot 采集器更小、更可控；RLinf 的完整栈
  （torch/Ray/训练）对纯数采是负担。（C）
- 若需要**双臂 + ROS 2 + LeRobot**：`xdongmiao/pico-piper-teleop`（Apache-2.0，
  双臂 PiPER + Pico + ROS 2 Humble + LeRobot 0.5.1）功能面最完整，但只有
  3 stars、固定 `/projects` 路径、无 Docker；其 launch 支持 `piper_x`，IK
  节点却硬编码标准 `piper` URDF，单臂/Piper X 都要改，必须先审计（C）。
- **仅参考、不建议直接采用**：
  - `ZhengYihong-cell/ACT`（PICO 4 Ultra + PiPER X + 原生 LeRobot v3 +
    ACT）功能最贴近，但**没有 LICENSE**，只能读思路；
  - `Arborseek/PiperXR`（PICO 4 Ultra + XRoboToolkit + placo IK + MuJoCo/真机）
    是 **non-commercial** 许可且不含 LeRobot；
  - `swaaniida/pico-piper-teleop`、`p-stop/PICO_teleop_Agilex_piper`、
    `Curry-ZHR/piper_teleoperation` 均无许可证；
  - `tomakeIT/PiperPilot` 是 MIT、明确支持 Piper-X + LeRobot v2.0，但 VR 是
    **Quest 3 / SpaceMouse**，不是 PICO。
- **不推荐**：把 RLinf 当运行时运动源、在 `jcheng-system`/ArmPi 上直接跑、
  依赖无许可证的 `pico_software`、或把厂商 IK 换成手写数值 IK 只为复用
  `PicoJoint`。

**主要风险**：RLinf 的 **Piper 路径**没有 e-stop、lease 或 stop latch
（ARX5/YAM 只有各自的软件 emergency hold，Piper 连这个都没有），且
`move_p`/`move_j` 会立即下发运动；Piper 平台本身无 e-stop（生态根
`AGENTS.md`）。`move_p`
要求**法兰**位姿，而 RLinf 观测的是 **TCP**，Piper X 的 TCP 偏移未实测；
默认 10 Hz 对 PICO 80 Hz 的流和 CAN 跟踪是否足够未验证；`pico_software`
无许可证；相机在 Pi 5/aarch64 上不能走 RLinf 的 `pyrealsense2` 依赖路径
（该 extra 只装 x86_64），且与现有
perception 进程存在设备所有权冲突。

---

## 02. Research Questions

**主问题**：RLinf（`RLinf/RLinf`）能否用 PICO VR 在松灵 AgileX Piper/Piper X
上采集真机演示数据？如果不能，最小、最安全的改造是什么，是否值得相对替代
方案投入？

**子问题**：

1. 在该 commit 上，RLinf 的 PICO 数采实际支持哪些机器人？Piper 处于什么
   状态？
2. Piper 路径实际实现了什么：驱动、环境、动作空间、teleop、分集、数据格式？
3. 要把 PICO→Piper 接通，缺哪些代码/配置/运动学事实？每条的最小实现是什么？
4. PICO 外部软件栈（头显、XRoboToolkit、publisher、SDK）要求什么硬件/系统/
   许可？有哪些供应链与维护风险？
5. 最小可行实验（MVE）如何设计，验收/失败判据是什么，哪些步骤必须获得
   单独的实机运动授权？

**约束**：

- 生态安全边界：真机运动只经 `jcheng-system` 的 `ExecuteMotion`；每次实机
  运动需单独的、明确的、按会话的操作者授权；平台无 e-stop、无抱闸、无编码器、
  无自碰撞模型（根 `AGENTS.md` §7）。
- 研究仓库无硬件访问；本报告不得把任何未运行的实验写成已完成。
- 目标臂是 **Piper X**（6 revolute + 夹爪），不是 ArmPi Ultra 的 5-DoF 总线
  舵机臂；两者不能混用驱动/安全假设。
- 交付物：一份带证据等级的调研报告、一份来源记录、一份预注册 MVE 设计。

---

## 03. Current System Analysis

### 3.1 生态里的“机械臂”有两条完全不同的路径

- **ArmPi Ultra**：Pi 5 + 厂商 ROS 2 Humble + 5-DoF 总线舵机 + 夹爪。运动
  只能经 `jcheng-system` 的 `jcheng_motion.ExecuteMotion`；`/joint_states`
  是命令缓存而非测量，完成/位姿真相来自 `GetBusServoState`；平台无 e-stop
  （根 `AGENTS.md` §7）。
- **AgileX Piper X**：独立的 6-DoF CAN 臂 + AgxGripper。已有调研确认：
  MIT 许可的 `agx_arm_urdf@680fa925` 是几何/惯性主源（6 revolute + 夹爪主
  关节 + 2 mimic 指），J1–J6 限位 ±150°/0…180°/-170°…0/±89°/±89°/±170°；
  `pyAgxArm`（LGPL-3.0）是官方 Python 驱动；`agx_arm_ros`（MIT）是 ROS 2
  驱动/MoveIt 参考；**TCP 偏移未实测**；`jcheng-interfaces` 的
  `robot-profile.v1` 以 `servo_id`/脉冲为中心，不能表达 CAN 臂。详见
  [Piper X 仿真数据地图](20261126-piper-x-simulation-data-map.md) 与
  [piper-x-assets](../references/manipulation/piper-x-assets.md)。

**对本报告的含义**：RLinf 的 Piper 路径只能跑在 **Piper X 这条独立 CAN 臂**
上；它不是 ArmPi 的运行时组件，也不能作为 `jcheng-system` 的运动源。任何
Piper X 数据采集都是**台架/离线活动**，不是生态运行时的一部分。

### 3.2 生态里没有 Piper X 的运行时集成

- `jcheng-system` 的硬件桥接面向总线舵机；没有 CAN 臂的 profile/lease/
  stop latch 路径。
- `jcheng-learning` 是 v0.1.0 离线数据集/训练脚手架，没有运行时节点，也没有
  数据格式承诺。
- `jcheng-teleop` 是 admission-only 脚手架，保留的 `TeleopCommand` 流未发布，
  没有输入适配器/设备/运动。
- `jcheng-studio`/`jcheng-applications` 只走 HTTP/WS；不接触 DDS/设备。

因此，PICO→Piper 的数采只能作为**生态外的研究工具**存在；其数据若要进入
`jcheng-learning`，应通过离线数据集导入，而不是让 RLinf 成为运动入口。

### 3.3 现有 Piper X 证据的缺口

- 没有 Piper X 的 TCP 实测、夹爪行程实测、关节跟踪误差、CAN 延迟或长时间
  稳定性数据。
- 没有 PICO 头显、XRoboToolkit、Piper X 三者同机的实测记录。
- 没有“Piper X + 任何 VR 遥操”在本工作区的证据。

本报告因此把“RLinf 的 Piper 驱动可用”与“PICO 数采可用”严格分开：前者有
源码/文档证据（A），后者没有（D，直到 MVE 运行）。

---

## 04. Research Methodology

**检索策略**：

- 以 `RLinf/RLinf` 为主对象，先读 README/能力矩阵/真机索引，再按
  `piper`、`pico`、`teleop`、`data collection` 在 `docs/`、`examples/`、
  `rlinf/`、`toolkits/`、`tests/` 中做全仓 grep。
- 对命中文件做全文阅读（清单见
  [来源记录](../references/manipulation/rlinf-piper-pico.md)），而不是只看
  README。
- 对 `pyAgxArm` 固定 commit 读 API 文档与 demo；对 `XRoboToolkit` 各仓库读
  README 与 GitHub 元数据；对社区 Piper/Pico 仓库只读 README/元数据。
- 用 GitHub Search API 查 `piper`/`pico`/`data collection` 的 issue/PR，判断
  上游是否已有计划或社区需求。
- 用 arXiv landing page 读 RLinf 技术报告摘要，确认它是否覆盖真机 teleop。

**纳入标准**：与 Piper/Piper X、PICO、真机 teleop、分集、LeRobot 导出、
CAN/驱动、许可/维护直接相关。

**排除标准**：RL 算法（PPO/GRPO/SAC）、仿真 benchmark、IsaacLab/RoboTwin
训练细节——它们不影响“能否采数”的结论；只在说明 Piper 的仿真任务时引用。

**实际阅读范围**：RLinf 源码/文档在固定 SHA 上全文或相关节；`pyAgxArm`
API 文档相关节；社区仓库仅 README/元数据，未审计源码。**未执行**：RLinf
安装、`collect_real_data.py`、`test_pico_data.py`、CAN、任何运动。研究与
结论的边界见 §12。

---

## 05. Literature Review

**RLinf 技术报告**：arXiv:2509.15965，*RLinf: Flexible and Efficient
Large-scale Reinforcement Learning via Macro-to-Micro Flow Transformation*
（29 作者；v1 2025-09-19，v2 2025-12-29）。landing page/摘要显示它讲的是
RL 训练系统的 macro-to-micro flow、弹性流水线与调度，报告 1.07×–2.43× 加速；
**没有**真机 teleop、数据采集或 AgileX Piper 的内容。全文未读；对本决策
不构成证据。（A，阅读范围=摘要页）

**PICO + Piper 数采的学术证据**：检索未发现同行评审论文专门评估
“PICO VR 遥操 AgileX Piper 采演示数据”。现有公开材料是仓库文档、厂商手册和
社区项目；它们不是受控实验，不能提供成功率、延迟、数据质量的统计结论。
（A/B）

**含义**：本问题不能靠论文结论回答，必须回到源码与最小实验。§06 因此是
本报告的主要证据来源；§11 给出可执行的验证设计。（C）

---

## 06. Repository Investigation

### 6.1 快照与总体结构

- 仓库：`RLinf/RLinf`，commit
  `ed0e1b836d11ec50eef4e5133e6b42ebd370cab9`（2026-11-26），
  `pyproject.toml` 版本 `0.4.0`，Python `>=3.10`，Apache-2.0。
- 真机相关分层：
  - `rlinf/envs/real/`：每机器人一个环境（`piper/`、`franka/`、`arx5/`、
    `yam/`、`r2/`…），声明动作空间、teleop 白名单、分集包装器。
  - `rlinf/robotics/parts/arms/`：每臂一个驱动（`piper.py` 走 `pyAgxArm`）。
  - `rlinf/robotics/parts/teleop/`：设备（`pico.py`、`spacemouse.py`、
    `gello*.py`…）。
  - `rlinf/robotics/parts/transports/`：PICO 的 ZMQ 订阅（`pico.py`）。
  - `rlinf/envs/real/wrappers/`：teleop 干预、键盘/Pico 分集、观测变换。
  - `examples/embodiment/`：`collect_data.sh`、`collect_real_data.py` 与
    Hydra 配置。
- 数据路径：`collect_real_data.py` 构建 `RealWorldEnv`，可挂
  `CollectEpisode`，导出 `replay_buffer` / `lerobot_dataset` /
  `pickle_episode`；LeRobot 分片写到
  `lerobot_dataset/rank_*/id_*/`，`robot_type` 默认 `panda`，`fps` 默认 10。
  `collect_real_data.py` 顶部 `import torch`，所以纯数采也需要 torch 环境
  （不一定要 GPU）。（A）

### 6.2 Piper 路径：驱动完整，环境只到“关节 reach”

**驱动**（`rlinf/robotics/parts/arms/piper.py`）：

- `PiperArm` 注册名 `pyagxarm`，`DOF=6`；构造参数覆盖 `can0`/`socketcan`/
  `1 Mbit`、`model`（含 `piper_x`）、固件自动探测、`speed_percent=30`、
  `gripper_force`、`gripper_max_width`、`with_gripper`。
- `_open()` 顺序：`AgxArmFactory.create_arm` → `init_effector(AGX_GRIPPER)` →
  `connect()` → 采纳该变体的 `joint_limits` → `enable()`（5 s 超时，每 10 ms
  轮询）→ `set_speed_percent()` → 等待首帧关节反馈（2 s 超时）。
- 固件探测：先用 `default` 配置连接、`get_firmware()`，再
  `resolve_firmware_profile(model, version)`；拿不到版本就报错，不静默用旧
  协议。
- 读：`tcp_pose`（SDK 的 `[x,y,z,r,p,y]` 按 `Rz·Ry·Rx` 转四元数）、6 关节
  （rad）、夹爪开口（宽度/行程，0…1）。
- 写：只有 `move_joints()` → `robot.move_j()` 与 `move_gripper()` →
  `gripper.move_gripper_m()`。**没有 `move_p`/`move_l`/笛卡尔接口。**
- 释放：`disconnect()`，不 `disable()`/`reset()`——源码注释说明两者会切断
  电机电源、让抬起的臂掉落。（A）

**环境**（`rlinf/envs/real/piper/base.py`）：

- 动作：6 关节绝对位置（rad）+ 可选 1 维夹爪（0…1）；
  `ActionKind.JOINT_POSITION`；`step()` 直接 `robot.send_action({"arm":
  {"joint_position": ...}})`。
- 观测：`state.arm_joint_position`（6）、`state.tcp_pose`（7）、
  `state.gripper_position`（1），以及最多若干 `wrist_*` 相机帧。
- `TELEOP = ()`，`TELEOP_DEFAULT = "none"`；注释：“No registered
  teleoperation device produces this joint layout.”
- 没有 `arm_kinematics()`、没有 `joint_step_limits`/
  `teleop_max_joint_lead`、没有 `episode_wrappers()`。
- `PiperEnvConfig.step_frequency=10.0`；`target_joint_qpos` 奖励是关节距离，
  `reward_threshold=0.05 rad`；这是“reach 一个关节配置”的任务，不是通用
  操作任务。
- `PiperReachEnv` 只是加随机初始扰动；CI 用 fake SDK 跑 SAC reach
  （`tests/e2e_tests/embodied/piper_mock_sac_mlp_reach.yaml`）。（A）

**配置与文档**：

- `examples/embodiment/config/env/piper_reach.yaml:13-14`：
  `# No registered leader device produces the Piper's joint layout.` +
  `teleop: none`。
- `docs/.../embodied/piper.rst:15`：只承诺硬件 setup 与 `test_piper_controller`
  检查，“RLinf does not ship a training task for AgileX Piper yet.”
- 没有 `realworld_piper_collect_data_pico.yaml`；唯一的单臂 Pico 数采配置是
  `realworld_collect_data_pico.yaml`，但它的 `cluster.node_groups` 写的是
  `hardware.type: Franka` + `robot_ip` + RealSense 序列号，默认任务是
  `env/realworld_peg_insertion@env.eval`，与 Piper 无关。（A）

**工具**：

- `toolkits/realworld_check/test_piper_controller.py`：`--model` 明确支持
  `piper_x`；`--read-only` 只读反馈（仍会 `connect()`，厂商文档警告连接会
  使能电机），不带 `--read-only` 才做 2° 关节步进/夹爪测试。
- `toolkits/realworld_check/test_pico_data.py`：独立订阅 PICO JSON 流，
  不需要 Franka/ Ray；打印 `recv_rate`、头显/手柄位姿、`grip`/`trigger`、
  按键。（A）

### 6.3 PICO 路径：传输/设备/分集都齐全，但只接在别的臂上

**传输**（`rlinf/robotics/parts/transports/pico.py`）：

- docstring 明确：“The PICO service and publisher still live outside RLinf.
  This module only subscribes to the existing JSON/ZeroMQ stream.”
- ZMQ SUB，默认 `ipc:///tmp/vr_data.ipc`；跨机 `tcp://<publisher_ip>:<port>`；
  高水位 10、`max_stale_s=0.25`、`timestamp_ns` 去重、按钮上升沿缓存、
  触发/握把模拟量、头显 yaw 校准。
- 字段与 `pico_software/vr_message.py` 对得上：`headset_pose`、左右
  `controller`（position/orientation/trigger/grip/axis）、`buttons`
  （A/B/X/Y/menu/axis click）。（A）

**设备**（`rlinf/robotics/parts/teleop/pico.py`）：

| 变体 | 动作语义 | 典型机器人 | 关键要求 |
|---|---|---|---|
| `PicoDelta` | `CARTESIAN_DELTA`（6 维增量 + 夹爪） | Franka 单/双臂 | 环境有 `tcp_pose`、`action_scale` |
| `PicoTcp` | `CARTESIAN_POSE`（位置 3 + rot6d 6 + 夹爪） | ARX5 双臂 | 动作空间裁剪；松手保持测得位姿 |
| `PicoJoint` | `JOINT_POSITION`（经环境 IK） | YAM / R2 等关节臂 | `arm_kinematics`、`joint_step_limits`、`max_joint_lead` 可选 |

- `PicoJoint.for_env()`（`pico.py:609-627`）在环境缺 `arm_kinematics` 或
  `joint_step_limits` 时直接 `ValueError`，错误文本点名这两个事实。
- 三个变体共用 `PicoExpert` 传输、校准、失联/无效位姿锁存、夹爪按钮逻辑；
  `PicoJoint` 额外有 IK 回溯、每 tick 关节步长上限、故障后“松手再握”重挂。
- `PicoEpisodeControlWrapper`（`wrappers/episode/pico_control.py`）：
  **B 开始**、**X 成功保存**、**A 失败丢弃**；ARX5 在启用 teleop 时把它挂进
  `episode_wrappers()`（`arx5/dual_base.py:693-704`）。（A）

**支持矩阵**（`docs/.../real_world_index.rst` §Robot Capability Matrix）：

| 机器人 | Setup | Teleop | Data Collection | SFT/Deploy | Online RL |
|---|---|---|---|---|---|
| AgileX Piper | ✓ | — | — | — | — |
| ARX X5 | ✓ | ✓ | ✓ | — | — |
| YAM | ✓ | ✓ | ✓ | — | — |
| Franka（单/双） | ✓ | ✓ | ✓ | ✓ | ✓ |
| Robbyant R2 | ✓ | ✓ | ✓ | — | Env only |
| SO-101 | ✓ | ✓ | ✓ | ✓ | — |

README 对 `—` 的说明是“untested, not necessarily unsupported”；但对 Piper
而言，`TELEOP=()` 是代码级的“拒绝”，所以它不是“只是没测”。（A）

### 6.4 外部 PICO 软件栈：能跑，但许可与硬件门槛要注意

RLinf 文档（`franka_vr.rst`）要求：

1. PICO 头显 + 手柄；`XRoboToolkit-Unity-Client` APK。
2. PC 侧 `XRoboToolkit-PC-Service`（Ubuntu 22.04/24.04）。
3. `pico_software`（包装 `XRoboToolkit-Teleop-Sample-Python`），
   `vr_data_publisher` 以 80 Hz 发 JSON。
4. 同机 IPC 或跨机 TCP；先 `test_pico_data` 验证，再采集。

许可/维护事实：

- `tiny-xie/pico_software`：GitHub API `license=None`，1 star，最后 push
  2026-07-05；仓库根没有 README/LICENSE；`vr_data_publisher.py` 依赖
  `xrobotoolkit_sdk`。**RLinf 文档直接让用户 clone 这个仓库**，这是一个
  可见的供应链/许可风险。（A）
- `XRoboToolkit-PC-Service`：Apache-2.0，支持 Windows x86 / Linux x86 /
  Linux aarch64。
- `XRoboToolkit-PC-Service-Pybind`：MIT，Linux x86_64/aarch64、Windows x64、
  Python >=3.10；`pip install xrobotoolkit-sdk`。
- `XRoboToolkit-Unity-Client`：`NOASSERTION`（未识别标准许可证）；README
  以 **Pico 4 Ultra** 为目标，提到企业版 SN、全身 tracker、远程立体视觉；
  相机数据采集需 PICO 企业服务审批。
- `XRoboToolkit-Teleop-Sample-Python`：MIT。

**含义**：如果要在 Piper X 上做 PICO 数采，最小许可干净的栈是
XRoboToolkit PC Service + Pybind SDK（MIT）+ 自写 publisher；不要依赖
`pico_software` 的无许可代码。头显方面，Pico 4 Ultra 是文档明确的目标；
其他 Pico 型号未验证。（A/C）

### 6.5 上游 issue/PR：没有 Piper teleop/数采计划

GitHub Search API（2026-11-26）：

- `is:issue piper`：4 条，全部是 RoboTwin 仿真/训练问题，没有 Piper 真机
  teleop/数采请求。
- `is:pr piper`：19 条命中，含 UR5/UR5e、Kuavo、ARX5 SFT 等新硬件 PR；
  未见 Piper teleop/Pico 数采 PR。
- `is:issue pico`：1 条（R2 测试偶发超时），与 Piper 无关。

这支持“上游短期不会自动补上 Piper 数采”的判断（C），但不排除未来版本；
fork 需要持续跟进上游。（A/C）

### 6.6 数据格式与分集：可复用，但需要 Piper 的任务语义

- 三种格式：`replay_buffer`（RLPD，成功轨迹 `.pt`）、`lerobot_dataset`
  （OpenPI SFT / HG-DAgger 等读）、`pickle_episode`（奖励模型预处理）。
- LeRobot 列：`image`、`extra_view_image*`、`state`/`actions`、`timestamp`/
  `frame_index`、`episode_index`/`index`/`task_index`、`done`/`is_success`；
  `streaming: true` 时每帧立即写 PNG，内存恒定。
- 采集入口：`bash examples/embodiment/collect_data.sh <config>`；退出条件是
  `runner.num_data_episodes` 个成功 episode。
- 对 Piper 的含义：数据管线可复用；但 **分集从哪来** 需要决定——Piper reach
  的关节目标不适合自由操作任务；ARX5 的 B/X/A 按钮分集是更合适的模板。
  `robot_type` 要显式写 `piper_x`（默认 `panda` 会误导下游）。（A）

### 6.7 许可与依赖

- RLinf：Apache-2.0；`pyAgxArm`：LGPL-3.0；`pico_software`：无许可证；
  XRoboToolkit 组件：Apache-2.0 / MIT / NOASSERTION；社区仓库：Apache-2.0、
  MIT 或无许可证。
- `piper.txt` 的 `pyrealsense2` 只在 Linux x86_64 安装；Pi 5（aarch64）上
  RLinf 的默认依赖不会装它，需要自建 librealsense/pyrealsense2 或改走
  `uvc`/`v4l2`。相机注册表还支持 `uvc`/`v4l2`，但
  `PiperConfig.camera_type` 文档没有列它们；是否可用未验证。（A/C）
- `collect_real_data.py` 导入 torch；纯数采也要一个含 torch 的 venv，但不必
  有 GPU（Piper 文档明确“no GPU or model checkpoint is required”）。（A/C）

### 6.8 社区里的直接实现（Piper X + PICO + LeRobot）

上一版比较漏掉了几个直接实现；补查后最匹配的是：

**`zcaklchgdm/piperx-pico-data-collector`（Apache-2.0，0.1.1）**

- 仓库自述：PiperX 单臂、双相机 VR 数据采集 + Pi0.5/OpenPI 策略执行的
  **source-only alpha reference**；包含运行时、episode 审核和 LeRobot 转换。
- `docs/TESTED_BASELINE.md` 的已实机验证栈：Ubuntu 22.04 x86-64、Python 3.11
  venv、单台 PiperX、SocketCAN **1,000,000 bit/s**、PICO 4 Ultra +
  XRoboToolkit PC 服务/SDK、两路 RGB **640×480@30 Hz**（头/第三视角 +
  腕/手部，软件时间戳配对，非硬件同步）、**60 Hz 遥操/CPV**、**30 Hz 训练
  行**、7D（6 关节 rad + 夹爪 m）、绝对关节位置 + 16 行 horizon。
- PICO 数采路径（`vr-live`/`vr-record`/`operator-console`）**不需要 OpenPI**；
  只有 `shadow`/`live`/RTC 才需要另行获取修改版 OpenPI。LeRobot 转换需要
  兼容的 LeRobot 安装，但不需要策略服务。
- 依赖：`pyAgxArm` 的**修改版源码包**（上游 base `cc498c0`，功能头
  `e00df19`，发布头 `7dcf423`，LGPL-3.0）必须随源码包提供并最后安装；
  不要用 PyPI 上的普通 `pyAgxArm` 替代。XRoboToolkit APK/DEB/SDK 由厂商
  渠道另行安装。
- 质量：作者的 270 项行为基线 + 6 项发布检查，期望 `276 passed`；这是
  软件回归门，不是硬件认证。仓库不包含 APK/SDK/固件/权重/采集数据。
- 结论：**单臂 PiperX + PICO 4 Ultra + LeRobot 的最直接起点**；但 alpha、
  source-only、需要标定和重复 preflight，不能当 turnkey（A）。

**`ZhengYihong-cell/ACT`（无 LICENSE，0 stars）**

- README 自述：PICO 4 Ultra 遥操 PiPER X，独立 USB Gloria-M 夹爪，双相机
  录制**原生 LeRobot v3** 示教数据，含 PyBullet 仿真、手动分条、数据校验和
  ACT 训练参考。
- 平台：Ubuntu 22.04 x86_64、Python 3.12、Conda、CPU 版 PyTorch；经典 CAN
  1 Mbit/s；最终相机 D435i（全局）+ D405（腕部），640×480@30 FPS，深度关闭；
  示教采样 20 Hz，按主机时间软件对齐（非硬件曝光同步）。
- 许可证：GitHub 未识别、仓库根无 LICENSE；只能作为思路参考，不能复制/
  再分发。README 很详细，但 0 stars、无第三方审计（A/C）。

**`Arborseek/PiperXR`（non-commercial，3 stars）**

- Ubuntu 22.04 + conda Python 3.10；PICO 4 Ultra + XRoboToolkit；placo IK；
  MuJoCo 仿真与真机 `piper_sdk` over CAN 的统一管线；**不含 LeRobot**。
- LICENSE 是自定义 **PiperXR Non-Commercial License**，禁止商业用途；
  只适合作为遥操/坐标映射/IK 的参考，不适合作为数采栈（A）。

**Quest 3 替代（不是 PICO）**

- `tomakeIT/PiperPilot`：MIT，明确支持 **Piper / Piper-X**、AgxGripper、
  LeRobot **v2.0**、Ubuntu 22.04、Python 3.10–3.11、1–3 路 RealSense、
  Quest 3 原生 OpenXR（90–92 Hz）或 SpaceMouse。若手头是 Quest 3 而不是
  Pico，这是许可最干净的 Piper-X + LeRobot 选择。
- `BdttK/vr_teleop`：Quest 3 WebXR、双臂 Piper、LeRobot **v2.1**、3×D435、
  120 Hz 遥操/30 Hz 录制；**无 LICENSE**，仅参考。

**结论**：直接实现存在，但分三类——(1) `zcaklchgdm`：Apache-2.0、单臂
PiperX、PICO、LeRobot 转换，alpha；(2) `ZhengYihong`/`Arborseek`/`swaaniida`/
`p-stop`/`Curry`：功能贴近但无许可证或非商业，不能直接采用；(3)
`PiperPilot`：MIT 但 VR 是 Quest 3。没有“Pico + Piper X + 原生 LeRobot +
宽松许可 + 生产级”的四全仓库。（A）

---

## 07. Comparative Analysis

| 方案 | 与 Piper/Piper X 的匹配 | PICO | 数采格式 | 许可 | 成熟度/证据 | 结论 |
|---|---|---|---|---|---|---|
| `zcaklchgdm/piperx-pico-data-collector` | **单臂 PiperX**；Ubuntu 22.04 x86-64；SocketCAN 1 Mbit；60 Hz 遥操 / 30 Hz 训练行；双 RGB 640×480 | **PICO 4 Ultra** + XRoboToolkit | 自有运行时 + **LeRobot 转换**；可选 OpenPI | Apache-2.0（核心） | 0.1.1 source-only alpha；3 stars；README/TESTED_BASELINE 明确实机栈；无第三方审计 | **单臂最直接起点**；需配套 patched pyAgxArm + 标定 |
| `ZhengYihong-cell/ACT` | **单臂 PiPER X**；Ubuntu 22.04；Python 3.12；CAN 1 Mbit；D435i+D405；20 Hz | **PICO 4 Ultra** + XRoboToolkit | **原生 LeRobot v3** + ACT 训练 | **无 LICENSE** | 0 stars；README 很详细；无第三方审计 | 只读参考；不可复制/再分发 |
| `Arborseek/PiperXR` | AgileX PiPER 6-DOF；Ubuntu 22.04；conda Python 3.10；placo IK；MuJoCo + 真机 | **PICO 4 Ultra** + XRoboToolkit | **无 LeRobot** | **Non-Commercial** | 3 stars；README；无实机证据 | 遥操/IK 参考；商业不可用 |
| `tomakeIT/PiperPilot` | **Piper / Piper-X**；Ubuntu 22.04；Python 3.10–3.11；CAN 1 Mbit；1–3×RealSense | **Quest 3** / SpaceMouse（非 PICO） | **LeRobot v2.0** | **MIT** | 2 stars；README；Quest 90–92 Hz | 若用 Quest 3，许可最干净的 Piper-X 方案 |
| `xdongmiao/pico-piper-teleop` | **双臂** PiPER；Ubuntu x86_64 + ROS 2 Humble；固定 `/projects`；3×V4L2；30 Hz | **PICO 4 Ultra** + XRoboToolkit | LeRobot 0.5.1 + Streamlit | Apache-2.0 | 3 stars；README/INSTALL；launch 支持 `piper_x`，IK 硬编码标准 piper URDF | 双臂 ROS 2 方案；Piper X/单臂需改 IK |
| `swaaniida/pico-piper-teleop` | 单臂 PiPER + Tracer Mini；Ubuntu 22.04；Python 3.10；ROS 2 Humble；piper_sdk 0.6.1 | **PICO 4 Ultra** | 非 LeRobot（README 未列） | **无 LICENSE** | 1 star；README | 只读参考 |
| `p-stop/PICO_teleop_Agilex_piper` | 双臂 PiPER；LeRobot 插件 | 是 | LeRobot frame | **无 LICENSE** | 0 stars；README | 拒绝（许可） |
| `jokeru8/piper_lerobot` | Piper leader→follower | 否 | LeRobot v3 | Apache-2.0 | 118 stars；README | 不用 PICO 时的备选 |
| `innovator-zero/piper-aio` | Piper/PiperX 主从 + DAgger | 否 | LeRobot 转换 | MIT | 59 stars；README | 不用 PICO 时的备选 |
| RLinf，Piper 现状 | 驱动支持 `piper_x`、固件探测、夹爪 | **无** | LeRobot/replay/pickle（通用） | Apache-2.0 + LGPL-3.0 依赖 | 驱动 A；teleop/数采 A（缺失） | 不能直接用；需改造 |
| RLinf，ARX5 式改造 | 需新写 `PiperCartesianEnv` + `move_p` | `PicoTcp` | 同上 | 同上 | 设计 C；未实现 | 若坚持 RLinf 的路线 |
| 自写最小采集器 | 完全按 Piper X 定制 | 是 | 自定/LeRobot | 自有 | 未实现 | 纯数采的最小方案 |

**可比性说明**：这些方案的目标臂、动作空间（关节/笛卡尔）、控制率
（10/30 Hz）、相机数量和分集语义都不同，不能用一个“成功率”横比；上表只做
适配性与证据强度比较，不做主观排名。社区仓库的 stars 不代表在 Piper X 上
可用；RLinf 的 ARX5 路径也不能直接平移到 Piper，因为 ARX5 用绝对位姿 +
自己的控制器，而 Piper 的 `move_p` 是法兰位姿 + 控制器 IK。

**为什么 `PicoJoint` 不是首选**：它要求环境提供 `arm_kinematics` 的
`fk`/`solve` 接口。Piper 的 SDK 提供离线 `fk()`，但**不提供离线 IK**；
`get_ik_joint_angles()` 只在 `move_p()` 之后有反馈，不是通用求解器。要复用
`PicoJoint`，就得自己写数值 IK（scipy/URDF），这会重复厂商控制器已做的
IK，并引入肘部构型跳变、限位、连续性等风险。相反，ARX5 式
`CARTESIAN_POSE` + `move_p` 直接把笛卡尔目标交给厂商控制器，代码更少、
风险更低；代价是动作是绝对位姿（rot6d）而不是关节角，且 `move_p` 的
TCP/法兰帧要处理正确。（A/C）

---

## 08. Critical Findings

1. **“RLinf 支持 AgileX Piper”与“RLinf 能用 Pico 在 Piper 上数采”是两件事。**
   README 的真机表把 Piper 列为 ✅，但能力矩阵的 Teleop/Data Collection 是
   `—`，Piper 专页明确说没有训练任务；`TELEOP=()` 是代码级拒绝。把 README
   的 ✅ 当成“Pico 数采可用”会直接踩空。（A）

2. **`PicoJoint` 在 Piper 上无法实例化，且不是配置问题。**
   `for_env()` 要求 `arm_kinematics` + `joint_step_limits`；`PiperEnv` 两者
   都没有。加一个 `pico:` 配置块不会改变这一点。（A）

3. **`move_p` 的帧约定是隐藏坑。** SDK 文档说 `move_p` 接收**法兰**位姿，
   `get_tcp_pose()` 返回 **TCP**；`get_tcp2flange_pose()`/`get_flange2tcp_pose()`
   负责互转。Piper X 的 TCP 偏移未实测；直接把 RLinf 的 `tcp_pose`
   喂给 `move_p` 会在有 TCP 偏移时产生系统性位置误差。（A/B）

4. **控制率与跟踪未验证。** `PiperEnv` 默认 10 Hz；PICO publisher 80 Hz；
   ARX5/YAM 的采集配置用 30 Hz。Piper 的 `move_j`/`move_p` 是位置-速度
   模式，底层会平滑，但 10 Hz 的离散目标在快速操作下是否足够、CAN 1 Mbit
   是否跟得上，均未测量。低控制率会直接降低演示质量并增加操作者负担。
   （A 配置 / D 实测）

5. **安全边界不匹配。** Piper 路径没有 lease、没有 stop latch、没有 e-stop
   （ARX5/YAM 只有各自的 software emergency hold/`check_stop_requested`，
   Piper 连这个都没有）；`PiperArm._release()` 只断开 CAN、电机继续抱位；
   `move_p`/`move_j` 会立即下发。Piper 平台本身无 e-stop。把 RLinf 接入
   生态运行时，等于绕开
   `ExecuteMotion` 的全部安全机制。（A，根 `AGENTS.md` §7）

6. **`pico_software` 是无许可证的个人仓库，却是 RLinf 文档指定的 publisher。**
   这不是“能不能跑”的问题，而是再分发/合规问题；同时只有 1 star、最后
   push 2026-07-05，维护风险高。最小干净栈是 XRoboToolkit PC Service +
   MIT Pybind SDK + 自写 publisher。（A）

7. **Pi 5/aarch64 的默认相机路径不通。** `piper.txt` 的 `pyrealsense2` 只在
   Linux x86_64 安装；相机注册表虽有 `uvc`/`v4l2`，但 `PiperConfig` 文档
   未列，且现有 perception ingress 独占相机（ADR 0004）。在 ArmPi 上
   同时跑 RLinf 相机采集与 perception 会冲突；应把采集放在笔记本/独立
   主机，或明确停掉 perception。（A/C）

8. **上游没有 Piper teleop/数采的 issue/PR。** 社区需求集中在 RoboTwin 仿真；
   fork 后要自己维护，且 RLinf 迭代快（886 commits、v0.4、文档频繁变动）。
   （A/C）

9. **直接实现存在，但没有“四全”仓库。** `zcaklchgdm` 是唯一同时做到
   单臂 PiperX + PICO 4 Ultra + LeRobot 转换 + Apache-2.0 的公开实现，但仍
   是 0.1.1 source-only alpha；`ZhengYihong` 有原生 LeRobot v3 但无许可证；
   `Arborseek` 是 non-commercial 且不含 LeRobot；`PiperPilot` 是 MIT 但 VR
   是 Quest 3；`xdongmiao` 是 Apache-2.0 但双臂/ROS 2、IK 硬编码标准 Piper。
   因此推荐从“用 RLinf 改造”改为“先审计 `zcaklchgdm`，不满足再自写”。（A/C）

10. **什么会改变结论**：
   - `zcaklchgdm` 的审计/复现通过（276 tests + 本机 PiperX 预检），则单臂
     PICO 数采不必改 RLinf；
   - 上游 RLinf 在 `PiperEnv` 增加 `TELEOP=("pico",)`、`arm_kinematics` 或
     Cartesian 环境，并提供 `realworld_piper_collect_data_pico.yaml`；
   - 或者 `xdongmiao/pico-piper-teleop` 在 Piper X 上有可复现的实机证据；
   - 或者用户只需要 leader-arm/spacemouse 数采（此时 RLinf 的 Piper 仍不
     支持，但 `jokeru8/piper_lerobot` / `piper-aio` 更直接）。

---

## 09. Engineering Applicability

### 9.1 与现有架构的兼容性

- **运行时**：不兼容。RLinf 直接持有 CAN、直接下发运动，绕开
  `jcheng-system` 的 `ExecuteMotion`、lease、deadman、stop latch；不能成为
  生态的运动源。
- **台架/离线**：兼容。Piper X 是独立 6-DoF 臂；RLinf 可在研究主机上以
  独立 venv/进程运行，数据离线导入 `jcheng-learning`。
- **数据**：LeRobot 分片与生态的离线学习方向一致；`robot_type` 需写
  `piper_x`，`fps` 需与实测控制率一致。

### 9.2 改造路线与成本（C）

| 路线 | 改动 | 原型 | 可验证版本 | 主要风险 |
|---|---|---|---|---|
| A0. 审计/复现 `zcaklchgdm` | 装 patched `pyAgxArm` + 校验 276 tests + CAN/相机/夹爪标定 + preflight | 1–2 天 | 1–2 周 | alpha、单臂、仅作者机验证、厂商 SDK 需另装 |
| A. ARX5 式 `PiperCartesianEnv` | 新增环境 + `PiperArm.move_pose()` + 配置 + 分集 | 3–5 天 | 2–3 周 | `move_p` 帧/限位、10 Hz 跟踪、工作空间 |
| B. `PicoJoint` + 数值 IK | 新增 `PiperKinematics`（`fk`/`solve`）+ `joint_step_limits` | 5–8 天 | 3–4 周 | 肘部跳变、IK 失败、与厂商 IK 不一致 |
| C. 独立最小采集器 | ZMQ→`move_p`→LeRobot，自己实现分集/停止 | 2–4 天 | 1–2 周 | 重复 RLinf 的包装器/数据校验 |
| D. 审计 `xdongmiao/pico-piper-teleop` | 读源码、去固定路径、改 IK URDF、验证 Piper X/单臂 | 3–5 天 | 2–3 周 | 低成熟度、ROS 2 Humble、双臂假设 |

以上是**单臂、无力反馈、无相机标定、无策略训练**的估计；不含 PICO 头显/
PC 的采购与系统安装。实际成本取决于 CAN 适配器、固件、TCP 偏移和操作者
熟练度。

### 9.3 硬件与算力

- Piper X + USB-to-CAN（SocketCAN，1 Mbit）；CAN 接口必须先 `ip link` 起来，
  SDK 不配置。
- PICO 4 Ultra（文档目标）+ XRoboToolkit PC Service（Ubuntu 22.04/24.04）
  + publisher 主机；同机 IPC 或跨机 TCP。
- 采集主机：x86_64 Linux 最稳（RealSense + Pybind 轮子）；aarch64 可用
  Pybind SDK，但 RealSense 轮子不可用，需 UVC/V4L2 或外接采集机。
- GPU：数采不需要模型；`collect_real_data.py` 导入 torch，但可在 CPU 运行
  （未验证）。后续 SFT/RL 才需要 3060/Orin 级算力；6 GB 显存对 OpenPI/π0
  训练仍是约束，不属于本报告范围。

### 9.4 安全与可靠性

- 物理急停/断电开关必须在操作者伸手可及处；RLinf 的“关脚本”不是急停。
- 首次运动限速（`speed_percent` 10–30）、限制工作空间、清空桌面、单人到场。
- PICO 失联/无效位姿时 `PicoJoint`/`PicoTcp` 有锁存/保持逻辑，但这不是
  全局 stop；需要额外的看门狗/断电策略。
- CAN 总线同一时间只允许一个 owner；RLinf 的 `DeviceClaim` 防同进程双开，
  但不防另一个进程（如厂商工具）抢总线。
- 记录启动时间、PID、CAN 状态、命令计数；异常先停进程、再断 CAN、再断电。

### 9.5 回退

- 独立 venv/分支，不改产品仓库；数据写 `logs/`，不入 git。
- 失败即 `ip link set can0 down`、杀进程、断电重启；不反复重连。
- 任何“实机已验证”结论必须能指向 `jcheng-*/evidence/` 的具体文件与日期；
  本报告不产生这样的结论。

---

## 10. Recommended Approach

### 推荐（若决定用 RLinf）

**A. 仿 ARX5 的 `PiperCartesianEnv`，不要用 `PicoJoint`。**

1. `rlinf/robotics/parts/arms/piper.py`：新增 `move_pose()`，把目标 TCP 位姿
   经 `get_tcp2flange_pose()` 转成法兰位姿后调用 `robot.move_p()`；保留
   `move_j` 给策略/复位。注意 SDK 的 Euler 约定是 `Rz·Ry·Rx`（extrinsic
   xyz），与 `PiperArm._tcp_pose()` 的转换一致。
2. 新增 `rlinf/envs/real/piper/cartesian.py`：单臂 `PiperCartesianEnv`，
   动作 `CARTESIAN_POSE`（位置 3 + rot6d 6）+ 夹爪 1；观测复用
   `PiperEnv` 的 `tcp_pose`/关节/相机；加工作空间盒、每步位移/旋转上限、
   `step_frequency` 10–30；`TELEOP=("pico",)`；`episode_wrappers()` 返回
   `PicoEpisodeControlWrapper`。
3. 新增 `examples/embodiment/config/env/piper_collect.yaml` 与
   `realworld_piper_collect_data_pico.yaml`：`hardware.type: Piper`、
   `can_channel`、`model: piper_x`、`camera_serials`、`teleop: pico`、
   `pico.zmq_addr`、`data_collection.robot_type: piper_x`、`fps`。
4. 测试：先用 `tests/robot_mocks` 的 fake SDK 写单测（动作空间、帧转换、
   限位、失联锁存），再跑 `test_piper_controller --read-only` 与
   `test_pico_data`，最后才上实机。
5. 分阶段 MVE 见 §11；MVE-2/3 的每次运动都需要单独的会话授权。

**理由**：复用厂商 `move_p` 的 IK/平滑，代码量最小；`PicoTcp` 在 ARX5 上
已有绝对位姿 + 分集的成熟模式；避免手写 IK 的构型风险。**代价**：动作是
绝对 EE 位姿而不是关节角；`move_p` 的 TCP/法兰帧必须正确；10 Hz 跟踪需实测。

### 替代

**B. 审计 `zcaklchgdm/piperx-pico-data-collector`（单臂 PiperX + PICO +
LeRobot）**：Apache-2.0，0.1.1 source-only alpha；已按 Ubuntu 22.04 x86-64 +
单臂 PiperX + SocketCAN 1 Mbit + PICO 4 Ultra + 双 RGB + 60/30 Hz +
LeRobot 转换验证。若目标就是单臂 Piper X 数采，这是**最直接的起点**，
比从 RLinf 改造或自写采集器更省。代价：alpha、需要配套 patched
`pyAgxArm` 源码包、必须重新标定/预检；先审计其 276 项测试和硬件假设，
再决定是否采用（C）。

**C. 独立最小采集器**（只数采、不要 RLinf 的训练栈）：ZMQ SUB 接收
`xrobotoolkit_sdk` 的 JSON，映射为 `move_p` 目标，按 B/X/A 分集，写 LeRobot
或 HDF5。优点是代码可控、依赖少、许可干净；缺点是要自己实现分集/停止/
数据校验，未来接 RLinf 训练需做格式转换。

**D. 审计 `xdongmiao/pico-piper-teleop`（双臂 + ROS 2）**：Apache-2.0，
双臂 PiPER + Pico + ROS 2 Humble + LeRobot 0.5.1 + Streamlit，功能面最完整；
但 3 stars、固定 `/projects`、无 Docker；launch 支持 `piper_x`，IK 节点却
硬编码标准 `piper` URDF/`joint6`，单臂或 Piper X 都要改。适合双臂方案或
作为**参考实现**，不建议直接生产；采用前先做代码审计（IK、时序、许可头、
安全）和单臂裁剪。

**E. `ZhengYihong-cell/ACT`（仅参考）**：PICO 4 Ultra + PiPER X + 原生
LeRobot v3 + ACT，平台是 Ubuntu 22.04 / Python 3.12 / CPU torch / CAN
1 Mbit / D435i+D405 / 20 Hz；功能最贴近“Pico + Piper X + LeRobot”，但
**没有 LICENSE**，不能复制或再分发；只读其数据合同、时间对齐和 ACT
训练思路。

**F. `tomakeIT/PiperPilot`（若用 Quest 3）**：MIT，明确支持 Piper/Piper-X、
AgxGripper、LeRobot v2.0、Ubuntu 22.04、Python 3.10–3.11、1–3 路 RealSense、
Quest 3 原生 OpenXR（90–92 Hz）或 SpaceMouse。若手头是 Quest 3 而不是
Pico，这是许可最干净的 Piper-X + LeRobot 选择。

### 不推荐

- **只改 YAML 打开 `teleop: pico`**：`TELEOP=()` 会在包装器构建时拒绝。
- **给 `PicoJoint` 套一个手写数值 IK**：重复厂商 IK、增加肘部跳变/限位
  风险；除非必须得到关节角动作。
- **依赖 `pico_software`**：无许可证；用 XRoboToolkit PC Service + MIT
  Pybind SDK + 自写 publisher。
- **在 ArmPi/`jcheng-system` 上跑 RLinf**：绕开 `ExecuteMotion`/lease/
  stop latch，违反生态安全边界。
- **使用无许可证的社区仓库**（`ZhengYihong-cell/ACT`、
  `swaaniida/pico-piper-teleop`、`p-stop/PICO_teleop_Agilex_piper`、
  `Curry-ZHR/piper_teleoperation`、`WeGo-Robotics/lerobot_robot_piper`）：
  不采用、不复制；只能读思路。
- **商业使用 `Arborseek/PiperXR`**：其 LICENSE 是 Non-Commercial，且不含
  LeRobot。

---

## 11. Experimental Design

预注册设计见
[`experiments/20261126-rlinf-piper-pico-mve/design.md`](../experiments/20261126-rlinf-piper-pico-mve/design.md)。
**尚未运行**；以下只是计划。

- **MVE-0（离线，0.5–1 天）**：在独立 venv 安装 RLinf 的 Piper 依赖；用
  fake ZMQ publisher 向 `test_pico_data` 发 80 Hz JSON；解析
  `piper_x` 配置；不接硬件、不发运动。验收：消息率/字段正确，配置可解析，
  单测通过；失败：导入/依赖/字段不匹配。
- **MVE-1（只读硬件，0.5 天）**：CAN 1 Mbit up；`test_piper_controller
  --read-only --model piper_x` 读 6 关节/TCP/夹爪/固件；PICO publisher +
  `test_pico_data` 读头显/手柄/按键；**不下发任何运动**。验收：反馈稳定、
  固件可解析、Pico 流 ≥ 60 Hz 且 stale 可控；失败：无帧、固件不识别、
  控制权冲突。需要操作者到场与单独授权（连接即可能使能电机）。
- **MVE-2（低速单臂遥操，3–5 天实现）**：`PiperCartesianEnv` + `PicoTcp`
  + `move_p`，`speed_percent=10`，小工作空间，单臂，无相机；测命令延迟、
  跟踪误差、失联保持、停止行为。验收（暂定，需 MVE-1 校准）：p95 命令
  延迟 ≤ 150 ms、稳态位置误差 ≤ 10 mm/2°、无未命令运动、stale > 0.25 s
  保持；失败：超限、抖动、IK/限位报错、无法停止。**每次运动单独授权。**
- **MVE-3（演示采集，2–3 天）**：20 个成功 episode，LeRobot 导出，
  `robot_type: piper_x`，`fps` 与实测控制率一致；回放检查图像/状态/动作/
  时间戳。验收：20/20 可读、时间戳单调、动作在限位内、丢帧 < 5%、成功
  标签正确；失败：分片损坏、图像/动作错位、不可复现。**每次运动单独授权。**

---

## 12. Limitations & Uncertainties

- **纯静态**：没有安装 RLinf、没有 CAN、没有 PICO、没有相机、没有运动；
  所有“会怎样”的判断都是源码/文档推断（A/C），不是实测（S）。
- **快照会变**：RLinf 迭代快；commit `ed0e1b8` 的结论不保证适用于后续版本。
  上游若新增 Piper teleop，本报告的“需改造”结论会被推翻。
- **固件/TCP**：Piper X 的实际固件、TCP 偏移、夹爪行程、关节跟踪未测；
  `pyAgxArm` 文档的 `move_p`/`fk` 行为只在 SDK 层，未在本机复现。
- **PICO 硬件**：Pico 4 Ultra 之外的头显、XRoboToolkit 版本匹配、80 Hz 流的
  实际延迟/丢包未测；`pico_software` 未运行。
- **社区仓库**：只读 README/元数据，未审计源码、未验证实机；stars 不是
  证据。
- **成本估计**：路线 A–D 的天数是 C 级推断，依赖单人、单臂、无相机标定、
  无策略训练；实际可能翻倍。
- **未回答**：PICO 数采的演示质量（成功率、平滑度、操作者负荷）是否足以
  训练 VLA；这需要 MVE-3 的数据和下游训练实验，不在本报告范围。

**需要的访问/数据**：Piper X + USB-CAN + 物理断电开关；Pico 4 Ultra +
XRoboToolkit PC Service + publisher 主机；操作者与逐次运动授权；Piper X
的 TCP/夹爪实测；RLinf 安装与 MVE-0/1 的运行记录。

---

## 13. References

- RLinf 仓库：<https://github.com/RLinf/RLinf>，commit
  `ed0e1b836d11ec50eef4e5133e6b42ebd370cab9`（2026-11-26），Apache-2.0，
  v0.4.0。关键文件：`rlinf/envs/real/piper/base.py`、
  `rlinf/robotics/parts/arms/piper.py`、`rlinf/robotics/parts/teleop/pico.py`、
  `rlinf/robotics/parts/transports/pico.py`、
  `rlinf/envs/real/wrappers/episode/pico_control.py`、
  `docs/source-en/rst_source/examples/embodied/piper.rst`、
  `docs/source-en/rst_source/examples/real_world_index.rst`、
  `docs/source-en/rst_source/examples/embodied/franka_vr.rst`、
  `examples/embodiment/config/realworld_collect_data_pico.yaml`、
  `examples/embodiment/config/collect_data_dual_arx5.yaml`。
- RLinf 技术报告：C. Yu et al., *RLinf: Flexible and Efficient Large-scale
  Reinforcement Learning via Macro-to-Micro Flow Transformation*,
  arXiv:2509.15965（v1 2025-09-19；v2 2025-12-29）；
  <https://arxiv.org/abs/2509.15965>（只读 landing page/摘要）。
- `pyAgxArm`：<https://github.com/agilexrobotics/pyAgxArm>，commit
  `4b0f06585db3324222616999afeda9037df2e8bd`，LGPL-3.0；
  `docs/piper/piper_api.md`（`move_j`/`move_p`/`fk`/TCP 偏移/夹爪）、
  `pyAgxArm/api/agx_arm_factory.py`、`pyAgxArm/demos/piper_x/test1.py`。
- `pico_software`：<https://github.com/tiny-xie/pico_software>（GitHub
  `license=None`，1 star，最后 push 2026-07-05；`vr_data_publisher.py`
  80 Hz；仓库根无 LICENSE）。
- XRoboToolkit：
  - <https://github.com/XR-Robotics/XRoboToolkit-PC-Service>（Apache-2.0）
  - <https://github.com/XR-Robotics/XRoboToolkit-PC-Service-Pybind>（MIT；
    Linux x86_64/aarch64、Windows x64、Python >=3.10）
  - <https://github.com/XR-Robotics/XRoboToolkit-Unity-Client>
    （`NOASSERTION`；README 以 Pico 4 Ultra 为目标）
  - <https://github.com/XR-Robotics/XRoboToolkit-Teleop-Sample-Python>（MIT）
- 对照仓库（仅 README/元数据）：
  - <https://github.com/zcaklchgdm/piperx-pico-data-collector>（Apache-2.0，
    0.1.1 source-only alpha；单臂 PiperX + PICO 4 Ultra + 双 RGB +
    LeRobot 转换；Ubuntu 22.04 / Python 3.11 / CAN 1 Mbit / 60 Hz 遥操 /
    30 Hz 训练行）
  - <https://github.com/ZhengYihong-cell/ACT>（无 LICENSE，0 stars；
    PICO 4 Ultra + PiPER X + 原生 LeRobot v3 + ACT；Ubuntu 22.04 /
    Python 3.12 / D435i+D405 / 20 Hz）
  - <https://github.com/Arborseek/PiperXR>（自定义 Non-Commercial，
    3 stars；PICO 4 Ultra + XRoboToolkit + placo IK + MuJoCo/真机；
    不含 LeRobot）
  - <https://github.com/tomakeIT/PiperPilot>（MIT，2 stars；Piper/Piper-X +
    Quest 3/SpaceMouse + LeRobot v2.0；非 PICO）
  - <https://github.com/xdongmiao/pico-piper-teleop>（Apache-2.0，3 stars，
    ROS 2 Humble + LeRobot 0.5.1；双臂）
  - <https://github.com/swaaniida/pico-piper-teleop>（无 LICENSE，1 star；
    单臂 PiPER + Tracer Mini；Ubuntu 22.04 / ROS 2 Humble /
    piper_sdk 0.6.1）
  - <https://github.com/Curry-ZHR/piper_teleoperation>（无 LICENSE，1 star；
    idata PICO 控制 Piper）
  - <https://github.com/BdttK/vr_teleop>（无 LICENSE；Quest 3 WebXR +
    双臂 Piper + LeRobot v2.1）
  - <https://github.com/jokeru8/piper_lerobot>（Apache-2.0，118 stars，
    leader→follower）
  - <https://github.com/lykycy123/lerobot-piper>（Apache-2.0，58 stars）
  - <https://github.com/innovator-zero/piper-aio>（MIT，59 stars，
    Piper/PiperX 主从）
  - <https://github.com/p-stop/PICO_teleop_Agilex_piper>（无许可证）
  - <https://github.com/WeGo-Robotics/lerobot_robot_piper>（无许可证）
- 生态内基线：
  [Piper X 仿真数据地图](20261126-piper-x-simulation-data-map.md)、
  [piper-x-assets](../references/manipulation/piper-x-assets.md)、
  [Piper X Gazebo plant 实验](../experiments/20261126-piper-x-gazebo-plant/result.md)。

来源记录（阅读范围、许可、未验证事项）：
[`references/manipulation/rlinf-piper-pico.md`](../references/manipulation/rlinf-piper-pico.md)。

---

*证据等级：S 在本机复现；A 一手源码/官方文档；B 可信二手资料；C 基于现有
证据的推断；D 未验证假设。本报告没有 S 级结论。*
