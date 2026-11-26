# RLinf 真机遥操作/数据采集与 AgileX Piper、PICO VR — 来源记录

- **类型**：开源仓库源码 + 官方文档 + 厂商 SDK 文档 + GitHub 元数据（一个来源组）
- **访问日期**：2026-11-26
- **相关报告**：[`reports/20261126-rlinf-piper-pico-data-collection.md`](../../reports/20261126-rlinf-piper-pico-data-collection.md)
- **相关实验**：[`experiments/20261126-rlinf-piper-pico-mve/design.md`](../../experiments/20261126-rlinf-piper-pico-mve/design.md)
  （预注册，未运行）
- **本地副本**：无。RLinf 与 pyAgxArm 只做浅克隆/raw 读取，未复制进本仓库；
  第三方源码、二进制、模型权重均未入库。

## 阅读范围

**完整阅读的源码/文档（RLinf，commit
`ed0e1b836d11ec50eef4e5133e6b42ebd370cab9`，2026-11-26）**：

- `rlinf/envs/real/piper/base.py`（Piper 环境，432 行，全文）
- `rlinf/robotics/parts/arms/piper.py`（Piper 臂驱动，457 行，全文）
- `rlinf/robotics/parts/teleop/pico.py`（Pico 设备与 `PicoDelta`/`PicoTcp`/
  `PicoJoint`，969 行，全文）
- `rlinf/robotics/parts/transports/pico.py`（ZMQ 订阅，655 行，全文）
- `rlinf/envs/real/wrappers/teleop/facts.py`（teleop facts，全文）
- `rlinf/envs/real/wrappers/teleop/intervention.py`（干预包装器，全文）
- `rlinf/envs/real/wrappers/episode/pico_control.py`（Pico 按键分集，全文）
- `rlinf/envs/real/wrappers/__init__.py`（包装器栈与分集选择，全文）
- `rlinf/robotics/robots/piper.py`（Piper 机器人树与 `PiperConfig`，全文）
- `rlinf/robotics/actions.py`（`ActionKind` 定义，全文）
- `rlinf/envs/real/piper/reach.py`（Piper reach 任务，全文）
- `examples/embodiment/collect_real_data.py`（采集入口，前 120 行）
- `examples/embodiment/collect_data.sh`（全文）
- `examples/embodiment/config/realworld_collect_data_pico.yaml`（全文）
- `examples/embodiment/config/env/piper_reach.yaml`（全文）
- `examples/embodiment/config/collect_data_dual_arx5.yaml`（Pico 段与采集段）
- `examples/embodiment/config/realworld_dual_yam_collect_data_pico.yaml`（Pico 段）
- `requirements/install.sh`（Piper 安装函数、环境清单，相关段）
- `requirements/embodied/envs/piper.txt`（全文）
- `toolkits/realworld_check/test_piper_controller.py`（参数与 read-only 路径）
- `toolkits/realworld_check/test_pico_data.py`（全文）
- `docs/source-en/rst_source/examples/embodied/piper.rst`（全文）
- `docs/source-en/rst_source/examples/real_world_index.rst`（能力矩阵段）
- `docs/source-en/rst_source/examples/embodied/franka_vr.rst`（PICO 软件栈段）
- `docs/source-en/rst_source/guides/data_collection.rst`（全文）
- `docs/source-en/rst_source/guides/teleoperation.rst`（全文）
- `pyproject.toml`（版本、Python 要求）
- `README.md` / `README.zh-CN.md`（真机支持表、更新日志）

**对照阅读的厂商资料（pyAgxArm，commit
`4b0f06585db3324222616999afeda9037df2e8bd`，RLinf 固定版本）**：

- `docs/piper/piper_api.md`：`move_j` / `move_p` / `move_l` / `get_ik_joint_angles`
  / `fk` / TCP 偏移 / 夹爪接口（相关节全文）
- `docs/effector/agx_gripper/agx_gripper_api.md`：`move_gripper_m`、状态反馈
- `pyAgxArm/api/agx_arm_factory.py`：`piper_x` 注册表与配置
- `pyAgxArm/api/arm_options.py`：`ArmModel.PIPER_X`
- `pyAgxArm/api/firmware.py`：`resolve_firmware_profile`
- `pyAgxArm/demos/piper_x/test1.py`：Piper X 的 SocketCAN 配置与夹爪初始化
- `LICENSE`：LGPL-3.0

**只看元数据/README 的对照仓库**（未做代码审计）：

- `tiny-xie/pico_software`（RLinf 文档指定的 VR publisher）
- `XR-Robotics/XRoboToolkit-PC-Service`
- `XR-Robotics/XRoboToolkit-PC-Service-Pybind`
- `XR-Robotics/XRoboToolkit-Unity-Client`
- `XR-Robotics/XRoboToolkit-Teleop-Sample-Python`
- `zcaklchgdm/piperx-pico-data-collector`（README、README_CN、
  `docs/TESTED_BASELINE.md`、`docs/INSTALLATION.md`、`SOURCE_LOCKS.md`、
  `configs/piperx_pi05.example.toml`）
- `ZhengYihong-cell/ACT`（README；无 LICENSE）
- `Arborseek/PiperXR`（README、LICENSE）
- `tomakeIT/PiperPilot`（README）
- `swaaniida/pico-piper-teleop`（README）
- `Curry-ZHR/piper_teleoperation`（README 缺失/空）
- `BdttK/vr_teleop`（README）
- `xdongmiao/pico-piper-teleop`
- `p-stop/PICO_teleop_Agilex_piper`
- `jokeru8/piper_lerobot`
- `lykycy123/lerobot-piper`
- `innovator-zero/piper-aio`
- `WeGo-Robotics/lerobot_robot_piper`

**检索**：GitHub Search API（`repo:RLinf/RLinf is:issue piper`、
`is:pr piper`、`is:issue pico`、`is:issue data collection`；
仓库搜索 `piper pico teleop`、`piper lerobot`、`piper vr teleop`、
`agilex piper data collection`），访问日期 2026-11-26。

**未读**：RLinf 技术报告 arXiv:2509.15965 全文（只读 landing page/摘要）；
`XRoboToolkit` 各仓库源码；社区仓库源码与 issue；RLinf 的 RL 训练/仿真文档
（与本次数据采集问题无关）。

## 来源与事实

### 1. RLinf 仓库快照

- URL：<https://github.com/RLinf/RLinf>
- Commit：`ed0e1b836d11ec50eef4e5133e6b42ebd370cab9`（2026-11-26
  10:47:12 +0800，`docs(supermimic): tighten docs harness and guides (#1950)`）
- `pyproject.toml`：`version = "0.4.0"`，`requires-python = ">=3.10"`
- `LICENSE`：Apache-2.0
- README 自述：面向 Embodied / Agentic AI 的 RL 基础设施；真机支持表列出
  Single-Arm Franka、Dual-Arm Franka、ARX X5、XSquare Turtle2、DOS-W1、
  GimArm、**AgileX Piper**、SO101、Robbyant R2、LeKiwi。
- 真机能力矩阵（`docs/source-en/rst_source/examples/real_world_index.rst`
  §Robot Capability Matrix）：AgileX Piper 的 Setup 为 ✓，Teleop、Data
  Collection、SFT/Deploy、Online RL 四列均为 `—`；ARX X5、YAM、Franka、
  R2、DOS-W1、SO-101 等有 Teleop/Data Collection 的 ✓。
- Piper 专页（`docs/source-en/rst_source/examples/embodied/piper.rst:15`）：
  “No GPU or model checkpoint is required; RLinf does not ship a training task
  for AgileX Piper yet.”
- 该页只覆盖 SocketCAN bring-up、`candump`、`test_piper_controller` 的
  read-only 与低速关节/夹爪检查；没有 Pico、没有数据采集。

### 2. RLinf 的 Piper 实现

- `rlinf/robotics/parts/arms/piper.py`
  - `PiperArm` 注册名 `pyagxarm`，通过 `pyAgxArm` 走 CAN；`DOF=6`。
  - 构造参数含 `channel`、`interface`（`socketcan` / `slcan` / `agx_cando`）、
    `bitrate=1000000`、`model`（`piper` / `piper_h` / `piper_l` / `piper_x`）、
    `firmware`（`None` 自动探测；`default` / `v183` / `v188` / `v189`）、
    `speed_percent=30`、`gripper_force`、`gripper_max_width=0.07`、
    `with_gripper`。
  - `_open()`：`AgxArmFactory.create_arm` → `init_effector(AGX_GRIPPER)` →
    `connect()` → 采纳变体关节限位 → `enable()` → `set_speed_percent()` →
    等待首帧关节反馈。
  - `_detect_firmware()`：先用 `PROBE_FIRMWARE="default"` 连接并
    `get_firmware()`，再 `resolve_firmware_profile(model, version)`；失败即报错，
    不静默回落。
  - `get_state()`：`tcp_pose`（SDK 的 `[x,y,z,r,p,y]` 转四元数）、
    `arm_joint_position`、`gripper_position`（宽度/行程，0…1）。
  - 动作只有 `move_joints()` → `robot.move_j([...])` 与
    `move_gripper()` → `gripper.move_gripper_m(value, force)`；**没有**
    `move_p` / `move_l` / 笛卡尔接口。
  - `_release()` 只 `disconnect()`，注释明确“不 disable、不 reset：两者都会
    切断电机电源并让抬起的臂掉落”。
- `rlinf/envs/real/piper/base.py`
  - `PiperEnvConfig`：`step_frequency=10.0`、`reset_joint_qpos`、
    `max_num_steps`、`target_joint_qpos`、`reward_threshold=0.05`、
    `success_hold_steps`、`gripper_penalty`。
  - 动作空间：6 个关节（rad）+ 可选的 1 维夹爪（0…1），
    `ActionKind.JOINT_POSITION`；`step()` 直接 `robot.send_action({"arm":
    {"joint_position": ...}})`。
  - `TELEOP = ()`，注释：“No registered teleoperation device produces this
    joint layout.”；`TELEOP_DEFAULT = "none"`。
  - **没有** `arm_kinematics()`、**没有** `joint_step_limits`/
    `teleop_max_joint_lead` 配置、**没有** `episode_wrappers()`。
  - 相机默认 `realsense`；`PiperConfig.camera_type` 文档列
    `realsense` / `zed` / `lumos` / `orbbec`；相机注册表实际还注册了
    `uvc` 与 `v4l2`。
- `rlinf/robotics/robots/piper.py`：`PiperConfig` 字段与上面一致；
  `PiperRobot.ROBOT_TYPE="Piper"`，`BACKEND="pyagxarm"`；夹爪挂在 `arm`
  之下。
- `examples/embodiment/config/env/piper_reach.yaml:13-14`：
  “No registered leader device produces the Piper's joint layout.” +
  `teleop: none`。
- `tests/e2e_tests/embodied/piper_mock_sac_mlp_reach.yaml`：CI 用 fake SDK
  跑 Piper SAC reach，动作 7 维、观测 14 维；不涉及 Pico。
- `toolkits/realworld_check/test_piper_controller.py`：`--model` 明确支持
  `piper` / `piper_h` / `piper_l` / **`piper_x`**；`--read-only` 只读反馈，
  不带 `--read-only` 才做小关节步进/夹爪测试。

### 3. RLinf 的 Pico 链路

- `rlinf/robotics/parts/transports/pico.py:15-20`：模块 docstring 明确
  “The PICO service and publisher still live outside RLinf. This module only
  subscribes to the existing JSON/ZeroMQ stream.”
- 默认地址 `ipc:///tmp/vr_data.ipc`（同机）；跨机用
  `tcp://<publisher_ip>:<port>`；`PicoExpert` 是 ZMQ SUB，`RCVTIMEO`、
  高水位 10、`max_stale_s=0.25`、校准按钮、按钮上升沿缓存。
- JSON 字段（`transports/pico.py` 与 `pico_software/vr_message.py` 对照）：
  `timestamp_ns`、`headset_pose`（7 维）、`left_controller` /
  `right_controller`（`position` 3、`orientation` 4、`trigger`、`grip`、
  `axis` 2）、`buttons`（`A`/`B`/`X`/`Y`/`left_menu_button`/
  `right_menu_button`/`left_axis_click`/`right_axis_click`）。
- `rlinf/robotics/parts/teleop/pico.py` 的三个变体：
  - `PicoDelta`：`ActionKind.CARTESIAN_DELTA`，6 维笛卡尔增量 + 夹爪；
    Franka 单臂/双臂用。
  - `PicoTcp`：`ActionKind.CARTESIAN_POSE`，绝对位姿（位置 3 + rot6d 6）+
    夹爪；ARX5 双臂用；`CLIPS_TO_ACTION_SPACE=True`，松手后保持测得位姿。
  - `PicoJoint`：`ActionKind.JOINT_POSITION`，用环境提供的 `arm_kinematics`
    把笛卡尔目标解成关节；`joint_step_limits` 限制每 tick 步长；
    `ik_backtrack_attempts`、`max_tick_s`、`max_joint_lead` 等。
  - `PicoJoint.for_env()`（`pico.py:609-627`）：环境没有
    `arm_kinematics` 时报 “This env's arm takes joint positions but the env
    offers no arm_kinematics…”，没有 `joint_step_limits` 时报
    “A PICO controller driving joints needs the env's joint_step_limits…”；
    因此 `PiperEnv` 以现状无法实例化 `PicoJoint`。
- `rlinf/envs/real/arx5/dual_base.py:693-704`：ARX5 在启用 teleop 时挂
  `PicoEpisodeControlWrapper`；该 wrapper（`episode/pico_control.py`）用
  **B 开始**、**X 成功保存**、**A 失败丢弃** 控制分集。
- `rlinf/envs/real/franka/base.py:436-445`：Franka 的 `action_parts` 是
  `CARTESIAN_DELTA`（6）+ `GRIPPER`（1）。
- `rlinf/envs/real/arx5/dual_base.py:325-331`：ARX5 的 `action_parts` 是
  `CARTESIAN_POSE`（9）+ `GRIPPER`（1）。
- 数据入口：`examples/embodiment/collect_data.sh` +
  `collect_real_data.py`；`data_collection.export_format` 支持
  `replay_buffer`、`lerobot_dataset`、`pickle_episode`；LeRobot 写出
  `lerobot_dataset/rank_*/id_*/` 分片，`robot_type` 默认 `panda`，
  `fps` 默认 10；`only_success`、`streaming`、`resume` 可选。
- 文档：`guides/data_collection.rst` 说明三种格式、目录结构、LeRobot 列、
  streaming 与 merge；`guides/teleoperation.rst` 说明设备表、`pico` 需
  `pico:` 配置块、`drives` 分支、`teleop_direct_stream`、设备归属。

### 4. RLinf 文档指定的 PICO 外部软件栈

- `docs/source-en/rst_source/examples/embodied/franka_vr.rst`：
  - 三角色：GPU server（node 0）、Franka controller node（env worker +
    Pico subscriber）、VR/PICO PC（XRoboToolkit PC Service + publisher）。
  - 需要 PICO 头显与手柄、`XRoboToolkit-Unity-Client` APK、
    `XRoboToolkit-PC-Service`（Ubuntu 22.04/24.04）、`pico_software`
    （包装 `XRoboToolkit-Teleop-Sample-Python`）。
  - 同机 `ipc:///tmp/vr_data.ipc`，跨机 `tcp://<publisher_ip>:<port>`；
    publisher 绑定 `tcp://0.0.0.0:<port>`，consumer 不得填 `0.0.0.0`。
  - 先 `test_pico_data` 验证，再 `collect_data.sh
    realworld_collect_data_pico`。
- `tiny-xie/pico_software`：
  - GitHub API：`license=None`、1 star、最后 push 2026-07-05；仓库根没有
    README（404），没有 LICENSE 文件；`vr_data_publisher.py` 以 80 Hz 发布
    JSON，依赖 `xrobotoolkit_sdk`。
  - 该仓库是 RLinf 文档指定的 publisher；被引用的 `pico_software` 本身
    没有可见许可证。
- `XR-Robotics/XRoboToolkit-PC-Service`：Apache-2.0，96 stars，最后 push
  2025-10-23；支持 Windows x86、Linux x86、Linux aarch64。
- `XR-Robotics/XRoboToolkit-PC-Service-Pybind`：MIT，30 stars，最后 push
  2026-10-14；Linux x86_64/aarch64、Windows x64、Python >=3.10；
  `pip install xrobotoolkit-sdk` 或源码构建。
- `XR-Robotics/XRoboToolkit-Unity-Client`：GitHub 识别为 `NOASSERTION`
  （未识别为标准许可证），88 stars，最后 push 2026-11-16；README 以
  **Pico 4 Ultra** 为目标设备，提到企业版 SN、全身 tracker、远程立体视觉
  等能力；相机数据采集需 PICO 企业服务审批。
- `XR-Robotics/XRoboToolkit-Teleop-Sample-Python`：MIT，182 stars，最后
  push 2026-01-01。

### 5. pyAgxArm（RLinf 固定的厂商 SDK）

- RLinf `requirements/install.sh:4251-4257`：
  `pyAgxArm @ git+https://github.com/agilexrobotics/pyAgxArm.git@4b0f06585db3324222616999afeda9037df2e8bd`；
  `requirements/embodied/envs/piper.txt` 另有 numpy、scipy、gymnasium、
  opencv-python、python-can>=3.3.4、`pyrealsense2`（仅 Linux x86_64）、
  imageio[ffmpeg]。
- `pyAgxArm` LICENSE：**LGPL-3.0**。
- `ArmModel.PIPER_X = "piper_x"`；`create_agx_arm_config` 接受
  `piper` / `piper_h` / `piper_l` / `piper_x` / `nero`；
  `AgxArmFactory` 为 `piper_x` 注册 `default` / `v183` / `v188` / `v189`
  四个驱动。
- `demos/piper_x/test1.py`：Linux 用 `interface="socketcan", channel="can0"`；
  `init_effector(AGX_GRIPPER)`。
- `docs/piper/piper_api.md`：
  - `move_j(joint_angles)`：关节运动；`move_p(pose)`：目标**法兰**位姿
    `[x,y,z,roll,pitch,yaw]`，控制器内部做 IK；`move_l` 直线；`move_c` 圆弧。
  - `get_ik_joint_angles()`：仅在 `move_p()` 之后有反馈，固件
    `PiperFW.V188+`（≥ S-V1.8-8）；不是离线 IK 求解器。
  - `fk(joint_angles)`：离线正解，返回**法兰**位姿
    `[x,y,z,roll,pitch,yaw]`，ZYX RPY。
  - `get_tcp2flange_pose()` / `get_flange2tcp_pose()`：TCP 与法兰互转；
    `set_tcp_offset()` 保存偏移。
  - 夹爪：`move_gripper_m(value, force)`，`value` 米、`force` 0…3 N；
    状态 `mode` 为 `width` / `angle`。
- `piper_x` 的关节限位由 `create_agx_arm_config` 返回的 `joint_limits`
  决定；RLinf 在 `_adopt_joint_limits()` 中采纳。

### 6. GitHub issue / PR 检索

- `repo:RLinf/RLinf is:issue piper`：4 条，均为 RoboTwin 仿真/训练问题
  （#634、#711、#712、#1217），没有 Piper 真机 teleop/数采请求。
- `is:pr piper`：19 条命中，含 UR5/UR5e、Kuavo、ARX5 SFT 等新硬件 PR；
  未见 Piper teleop/Pico 数采 PR。
- `is:issue pico`：1 条（R2 测试偶发超时），与 Piper 无关。
- 结论仅覆盖 GitHub Search API 在 2026-11-26 的可见结果，不排除被删除/
  未索引的内容。

### 7. 对照的社区实现（仅元数据/README）

| 仓库 | 许可 | stars | 最后 push | 与 Pico+Piper 的关系 |
|---|---|---|---|---|
| `zcaklchgdm/piperx-pico-data-collector` | Apache-2.0 | 3 | 2026-09-04 | **单臂 PiperX + PICO 4 Ultra + 双 RGB + LeRobot 转换**；Ubuntu 22.04 / Python 3.11 / CAN 1 Mbit / 60 Hz 遥操 / 30 Hz 训练行；0.1.1 source-only alpha |
| `ZhengYihong-cell/ACT` | **无** | 0 | 2026-11-07 | 单臂 PiPER X + PICO 4 Ultra + **原生 LeRobot v3** + ACT；Ubuntu 22.04 / Python 3.12 / D435i+D405 / 20 Hz；无 LICENSE |
| `Arborseek/PiperXR` | **Non-Commercial**（`NOASSERTION`） | 3 | 2026-07-20 | PICO 4 Ultra + XRoboToolkit + placo IK；MuJoCo 仿真 + 真机 `piper_sdk`；**不含 LeRobot** |
| `tomakeIT/PiperPilot` | MIT | 2 | 2026-08-31 | Piper/Piper-X + **Quest 3 / SpaceMouse** + LeRobot v2.0；**非 PICO**；Ubuntu 22.04 / Python 3.10–3.11 |
| `swaaniida/pico-piper-teleop` | **无** | 1 | 2026-10-27 | 单臂 PiPER + Tracer Mini + PICO；Ubuntu 22.04 / Python 3.10 / ROS 2 Humble / `piper_sdk 0.6.1`；README 未列 LeRobot |
| `Curry-ZHR/piper_teleoperation` | **无** | 1 | 2026-07-21 | `idata_pico_control_piper`；README 为空/缺失 |
| `BdttK/vr_teleop` | **无** | 0 | 2026-11-23 | **Quest 3 WebXR** + 双臂 Piper + LeRobot v2.1；非 PICO |
| `xdongmiao/pico-piper-teleop` | Apache-2.0 | 3 | 2026-10-21 | 双臂 PiPER + Pico + ROS 2 Humble + LeRobot 0.5.1 + Streamlit；固定 `/projects` 路径；源码分发，不含 Docker/模型/录制 |
| `p-stop/PICO_teleop_Agilex_piper` | 无 | 0 | 2026-11-09 | 双臂 Pico + Piper + LeRobot frame；无许可证 |
| `jokeru8/piper_lerobot` | Apache-2.0 | 118 | 2026-08-27 | Piper leader → follower 主从遥操 + LeRobot Dataset v3；非 Pico |
| `lykycy123/lerobot-piper` | Apache-2.0 | 58 | 2025-09-10 | LeRobot 采集/训练/推理；非 Pico；较旧 |
| `innovator-zero/piper-aio` | MIT | 59 | 2026-10-25 | Piper/PiperX 主从 + DAgger + LeRobot 转换；非 Pico |
| `WeGo-Robotics/lerobot_robot_piper` | 无 | 17 | 2026-09-04 | 多臂遥操 LeRobot 插件；无许可证 |

**`zcaklchgdm` 的已实机验证栈**（`docs/TESTED_BASELINE.md`）：Ubuntu 22.04
x86-64、Python 3.11、单台 PiperX、SocketCAN 1,000,000 bit/s、PICO 4 Ultra +
XRoboToolkit PC 服务/SDK、两路 RGB 640×480@30 Hz（头/第三视角 + 腕/手部，
软件时间戳配对）、60 Hz 遥操/CPV、30 Hz 训练行、7D（6 关节 rad + 夹爪 m）、
绝对关节位置 + 16 行 horizon。PICO 数采路径（`vr-live`/`vr-record`/
`operator-console`）不需要 OpenPI；LeRobot 转换需要兼容 LeRobot，不需要策略
服务。依赖随源码包提供的 patched `pyAgxArm`（上游 base `cc498c0`、功能头
`e00df19`、发布头 `7dcf423`，LGPL-3.0），不要用 PyPI 普通版本替代。
作者的 270 项行为基线 + 6 项发布检查期望 `276 passed`；这是软件回归门，
不是硬件认证；仓库不分发 APK/DEB/SDK/固件/权重/采集数据。

## 许可与再分发

- RLinf：Apache-2.0，可引用/派生；但其依赖 `pyAgxArm` 为 **LGPL-3.0**，
  动态使用可以，静态链接/ vendoring 需按 LGPL 处理；本仓库不复制其源码。
- `pico_software`：GitHub 未识别许可证、仓库根无 LICENSE；按“无许可证”
  处理，不复制、不再分发；研究记录只引用 URL 与行为。
- XRoboToolkit PC Service：Apache-2.0；Pybind SDK：MIT；Unity Client：
  `NOASSERTION`（未识别），其 APK/资产再分发需单独确认；Teleop Sample：
  MIT。
- 社区仓库：Apache-2.0 / MIT 的可在许可范围内参考；无许可证的
  (`ZhengYihong-cell/ACT`、`swaaniida/...`、`p-stop/...`、`Curry-ZHR/...`、
  `BdttK/...`、`WeGo-Robotics/...`) 不采用、不复制。
- `zcaklchgdm/piperx-pico-data-collector`：本仓库代码 Apache-2.0；配套
  patched `pyAgxArm` 为 LGPL-3.0（源码包形式提供），部署时按其 LGPL 条款
  处理；不分发 XRoboToolkit APK/DEB/SDK。
- `Arborseek/PiperXR`：自定义 PiperXR Non-Commercial License，禁止商业用途；
  只可作非商业参考。
- `tomakeIT/PiperPilot`：MIT；但其 VR 是 Quest 3，不是 PICO。
- 本记录不包含第三方源码、二进制、固件、模型权重或录制数据。

## 未验证事项

- 未安装 RLinf、未运行 `collect_real_data.py`、未构建 Pico publisher。
- 未连接 Piper X、未上 CAN、未做任何运动；`piper_x` 的实际固件版本、
  TCP 偏移、夹爪行程、关节跟踪性能均未测量。
- 未使用 PICO 头显；Pico 4 Ultra 之外的头显兼容性、XRoboToolkit 版本
  匹配、80 Hz 流的实际延迟/丢包均未测量。
- 社区仓库只读 README/元数据/文档，未审计其 IK、时序、许可头与实机证据；
  `zcaklchgdm` 的 276 项测试未运行，其 “已实机验证栈” 是作者文档自述，
  未在本机复现；`ZhengYihong-cell/ACT` 无许可证，未审计；`Arborseek/PiperXR`
  为非商业许可，未测试。
- RLinf 技术报告只读 landing page/摘要，未读全文；其结论不覆盖真机
  teleop/数采。
