# Piper X — 官方与社区仓库 / 资产审计

- **类型**：仓库与资产审计（GitHub API、raw 文件、浅克隆/稀疏克隆；静态阅读，
  未运行任何 ROS、Gazebo、MuJoCo、Isaac Sim 或机器人代码）
- **访问日期**：2026-11-26
- **目标**：为“围绕松灵 PiPER X 设计仿真”建立可追溯的数据源清单，区分可再分发、
  仅可参考和不可混用的模型，并给出各仓库的落位建议。
- **阅读范围**：`agx_arm_urdf` 的 Piper X URDF/xacro 全文、`agx_arm_ros` 的
  Piper X 相关参数/话题/MoveIt/SRDF/ros2_control/TCP 文档、`pyAgxArm` 的
  `ArmModel.PIPER_X` 与 Piper X demo、`piper_sdk` README 与目录树、
  `agx_arm_sim` 与 `piper_isaac_sim` 的目录树和 README、社区仓库的 README 与
  LICENSE。**未**逐行审计 USD、MuJoCo XML、Gazebo world，也**未**构建或运行它们。
- **本地资产**：`~/.local/share/jcheng/assets/piper_x/`（仓外；618 个上游文件，
  38,673,663 字节；`SHA256SUMS` 与 `PROVENANCE.json` 见该目录）。

## 1. 型号事实

Piper X 的公开规格（厂商页面/公开资料，**B** 级）：6 DoF、球形腕、最大负载
1.5 kg、工作半径 669 mm、重复定位精度 ±0.1 mm、本体质量约 4.5 kg、DC 24 V、
CAN 1 Mbps；J4/J5 ±90°，J6 ±165°。这些数字用于选型，不用于安全限位；安全限位
以机器人实际固件和实测为准。

MIT 的 `agx_arm_urdf@680fa925` 给出的关节表（**A** 级，直接源码）：

| Joint | Parent → child | Axis | Lower (rad) | Upper (rad) | Velocity | Effort |
|---|---|---|---|---|---|---|
| `joint1` | `base_link` → `link1` | `0 0 1` | -2.6179938 | 2.6179938 | 5 | 100 |
| `joint2` | `link1` → `link2` | `0 0 1` | 0 | 3.1415926 | 5 | 100 |
| `joint3` | `link2` → `link3` | `0 0 1` | -2.9670597 | 0 | 5 | 100 |
| `joint4` | `link3` → `link4` | `0 0 1` | -1.553343 | 1.553343 | 5 | 100 |
| `joint5` | `link4` → `link5` | `0 0 1` | -1.553343 | 1.553343 | 5 | 100 |
| `joint6` | `link5` → `link6` | `0 0 1` | -2.9670597 | 2.9670597 | 5 | 100 |

`effort="100"` 与 `velocity="5"` 是 URDF 声明值，不能当作实测能力；J6 的
±2.967 rad（±170°）与公开规格的 ±165° 不一致，见 §4.2。

**独立交叉验证（A）**：`pyAgxArm@d90e234` 的
`pyAgxArm/api/constants.py:67-74` 给出 `piper_x` 的关节限位预设，与上表逐项一致
（J1 ±2.617994、J2 0…3.141593、J3 -2.967060…0、J4/J5 ±1.553344、J6 ±2.967060）；
同文件 `:151-158` 的 MDH 预设也与 URDF 关节原点一致（J1 d=0.123、J3 a=0.28503、
J4 a=0.27364、J5 a=0.07466、J6 d=0.03526）。因此 **MIT URDF 与官方 SDK 在运动学
和限位上互相印证**；公开规格的 J6 ±165° 是少数派，仍需固件/总线读确认。

夹爪（`piper_x_with_gripper_description.xacro`，**A**）：

- `gripper`：prismatic，0…0.1 m，effort 10，velocity 3；这是 MoveIt/控制器使用的
  主关节。
- `gripper_joint1`：0…0.05 m，`mimic joint="gripper" multiplier="0.5"`。
- `gripper_joint2`：-0.05…0 m，`mimic joint="gripper" multiplier="-0.5"`。
- 夹爪基座通过 `flange_link` 挂在 `link6`，`gripper_base_joint` 的 origin 为
  `0 0 0.0045`、yaw `1.5707963`。

## 2. 官方仓库

| 仓库 | 分支/提交 | 许可 | 与 Piper X 的关系 | 阅读范围 |
|---|---|---|---|---|
| `agilexrobotics/agx_arm_urdf` | `main` / `680fa925cd00db7e2628563d2edc5540963045de` | MIT（Copyright 2026 aalicecc） | **Piper X 几何/惯性/限位主源**：`piper_x/` 与 `agx_gripper/` | URDF、夹爪 xacro、目录树、提交历史 |
| `agilexrobotics/agx_arm_ros` | `ros2` / `747d0722074d4cebc095d8d44f3ef68d2023ba6f` | MIT（同上） | ROS 2 驱动、MoveIt2/SRDF/ros2_control、CAN/TCP 文档；`arm_type:=piper_x` | README、节点参数/话题/服务、MoveIt 配置、TCP 文档 |
| `agilexrobotics/pyAgxArm` | `master` / `d90e234ba8e408cfa964b38aa9120b3131fc9f85` | **LGPL-3.0** | 当前 Python SDK；显式 `ArmModel.PIPER_X` 与 `demos/piper_x/test1.py` | README、API 入口、Piper X demo |
| `agilexrobotics/piper_sdk` | `master` / `b847e5393a7ce6ff8508d713eca7bdd3a42421b4` | MIT（Copyright 2024 Agilex Robotics） | 遗留 Python CAN SDK；README 指向 pyAgxArm，未声明 Piper X | README、目录树、版本枚举 |

### 2.1 驱动接口（`agx_arm_ros`，A 级）

- 启动参数：`can_port`、`arm_type`（`nero`/`piper`/`piper_h`/`piper_l`/`piper_x`）、
  `effector_type`（`none`/`agx_gripper`/`revo2`/`revo2_pro`/`revo2_touch`）、
  `auto_enable`、`fast_mode`、`speed_percent`、`pub_rate`（默认 200 Hz）、
  `tcp_offset`（6 维）。
- 发布：`feedback/joint_states`、`feedback/tcp_pose`、`feedback/arm_status`、
  `feedback/leader_joint_states`、`feedback/gripper_status`、`feedback/motor_status`。
- 订阅：`control/joint_states`、`control/move_j`、`control/move_p`、`control/move_l`、
  `control/move_c`、`control/move_js`、`control/move_cpv`、`control/move_mit`、
  `control/hand`、`control/hand_position_time`。
- 服务：`enable_agx_arm`、`control_enable`、`move_home`、`emergency_stop`、
  `exit_teach_mode`。
- CAN 配置：`can_activate.sh can0 1000000`；驱动依赖 `python-can`、`scipy`、`numpy`
  和 `pyAgxArm`（`agx_arm_ctrl` 的 `package.xml` 没有声明 pyAgxArm，需 pip 安装）。
- 重要边界：这些是**厂商话题/服务**，不是 JCHENG 契约；`emergency_stop` 是软件
  停止，不是急停。不能把该驱动直接接入 domain 41/42，也不能绕过 `ExecuteMotion`。

### 2.2 MoveIt / URDF 结构（A 级）

- `agx_arm.urdf.xacro` 通过 `arm_type` include `piper_x_with_gripper_description.xacro`；
  `tcp_link` 是固定的工具坐标系，`tcp_offset_xyz`/`tcp_offset_rpy` 默认全 0。
- `agx_arm.srdf.xacro`：`arm` 组为 `base_link` → `tcp_link` 的 chain；`gripper` 组只含
  `gripper`，`gripper_joint1/2` 标为 passive；`gripper_open/half/close` 为 0.1/0.05/0.0。
- `joint_limits.yaml` 只给速度/加速度（6 个臂关节 5.0/5.0，`gripper` 1.0/1.0），
  **不给位置限位**；位置限位来自 URDF/robot profile。
- TCP 文档示例：标准 Piper + 夹爪的 TCP 在 `link6` 前 0.1425 m
  （`tcp_offset:='[0.0, 0.0, 0.1425, 0.0, 0.0, 0.0]'`）。这是 **Piper** 的示例，
  不是 Piper X 的实测值；Piper X + 夹爪的 TCP 必须实测或由 CAD 导出后复核。

## 3. 仿真资产仓库

| 仓库 | 提交 | 许可 | 内容 | 结论 |
|---|---|---|---|---|
| `agilexrobotics/agx_arm_sim` | `f8cd8b147c75` | **无 LICENSE**；README 写 “MIT License” | `Moveit2/piper_x_gripper_moveit_config/`、`piper_x.world`、`gazebo_ros2_control`、`agx_arm_description/urdf/USD/piper_x_gripper_d435`、MuJoCo（仅 `agilex_piper`，无 X） | **不可再分发/搬运**，直到仓库补 LICENSE；可参考其目录结构和 Gazebo 配置项 |
| `agilexrobotics/piper_isaac_sim` | `8e1f88fdb7af` | **无 LICENSE** | `piper_x_description/`（8 关节 URDF：J1–J6 + J7/J8 夹爪指）、`USD/piper_x_v1.usd`、D435 模型、`PIPER-XURDF.csv` | **不可再分发**；模型比 MIT 主源旧，质量和关节原点不同，不能混用 |
| `google-deepmind/mujoco_menagerie` | `eea4c7431b63` | MIT（`agilex_piper/LICENSE`，Copyright 2024 RosenYin） | `agilex_piper/` MuJoCo 模型 | 许可干净，但这是**标准 Piper**，不是 Piper X |
| `AB-pixel-pixel/piper-X` | `master` | **无 LICENSE** | MuJoCo 流水线：下载 `agx_arm_ros` → 复制 URDF/mesh → 转 MJCF → 加 actuator；`minimal_piper_x_demo.py` | 方法可复用（从 MIT URDF 自行生成），文件不可搬运 |
| `Mamengyiyi/PiperX-ToolKit` | `main` | **无 LICENSE** | 双 PiperX 拖动示教/主从遥操作、三路 RGB、LeRobot 数据转换 | 与本项目数据采集最相关，但许可阻塞；仅记录 |
| `justagist/piper_cpp` | `main` | MIT（LICENSE 明示；GitHub API 为 NOASSERTION） | C++ SDK + ROS 2/MoveIt，部分派生自 `piper_sdk` | 可作为非 LGPL 桥接候选；**未验证 Piper X** |
| `Reimagine-Robotics/piper_ros` | `main` | MIT | 基于 `piper_control` 的 ROS 2 驱动 | 标准 Piper；**未验证 Piper X** |
| `xdongmiao/pico-piper-teleop` | `main` | Apache-2.0 | Pico VR 遥操作 + LeRobot 采集，双 PiPER | 标准 PiPER，不是 X；遥操作/采集参考 |

## 4. 关键差异与矛盾

### 4.1 两个“官方”Piper X 模型不一致

| 项 | MIT `agx_arm_urdf@680fa925` | 无许可 `piper_isaac_sim@8e1f88fd` |
|---|---|---|
| 关节数 | 6 revolute + 夹爪主关节 + 2 mimic | 8（J1–J6 + J7/J8 夹爪指） |
| 质量合计 | 4.3166 kg（base 1.02、link1 0.71、link2 1.16、link3 0.67、link4 0.39、link5 0.35、link6 0.01655） | 1.5500 kg（base 0.47421、Link1 0.16975、…、Link8 0.02648） |
| J4 origin | `0.27364 0 0` | `0.27264 0 0` |
| J5 origin | `0.07466 0 0`, rpy `-π/2 π/2 0` | `0.076857 0.00062395 0`, rpy `-π/2 0 0` |
| J6 origin | `0 -0.035 0`, rpy `π/2 0 0` | `0.035 0 0`, rpy `π/2 0 π/2` |
| J6 限位 | ±2.9670597 rad（±170°） | ±3.14 rad（±180°） |
| 夹爪 | 主关节 `gripper` 0…0.1 m + mimic | 两个独立指关节 J7/J8，各 0.05 m |

结论：**以 MIT `agx_arm_urdf@680fa925` 为准**。它在 2026-10-13 修正 J6 限位到
±170°，2026-10-15 修正 link6 惯性参数；`piper_isaac_sim` 的模型更旧、无许可、
且是 8 关节生成方式，不能与 6 关节 + mimic 的 MoveIt 配置混用。`PIPER-XURDF.csv`
的质量合计约 1.55 kg，与 8 关节 URDF 一致，更像 CAD 构件质量而非含电机的整臂质量；
不应作为动力学唯一来源。

### 4.2 规格与代码源的 J6 限位

公开规格 J6 ±165°（2.880 rad），MIT URDF 与 `pyAgxArm` 的
`ROBOT_JOINT_LIMIT_PRESET_RAD["piper_x"]` 都是 ±170°（2.967 rad）。两份官方代码源
一致，规格表是少数派；差异可能来自固件/批次/规格口径。仿真可用 URDF，但安全限位
必须按实际固件和实测重新确认；在未确认前，建议仿真用更保守的 ±165° 作为软限位，
并在报告中标注。

### 4.3 TCP 未实测

`agx_arm_ros` 只提供标准 Piper + 夹爪的 0.1425 m 示例；Piper X 的 `link6` →
夹爪指尖距离未在官方文档中给出。仿真/规划可以先用 0，但抓取实验前必须测量；
不能把标准 Piper 的值直接套到 X。

## 5. 许可矩阵

| 资产 | 许可 | 可提交到本生态仓库？ | 可放仓外资产库？ | 备注 |
|---|---|---|---|---|
| `agx_arm_urdf`（URDF/mesh） | MIT | 否（simulation gate 禁止 mesh；且生态无资产层） | 是，保留 LICENSE | 需在清单中署名 |
| `agx_arm_ros`（驱动/MoveIt） | MIT | 否（厂商代码，不复制） | 是，保留 LICENSE | 依赖 pyAgxArm LGPL |
| `piper_sdk` | MIT | 否 | 是 | 遗留 SDK |
| `pyAgxArm` | LGPL-3.0 | 否 | 是（作为依赖/参考） | 修改或静态嵌入需评估 LGPL |
| `agx_arm_sim` | 无 LICENSE（README 称 MIT） | 否 | 否，直到补 LICENSE | 不能仅凭 README 主张 MIT |
| `piper_isaac_sim` | 无 LICENSE | 否 | 否 | 仅记录 |
| Menagerie `agilex_piper` | MIT | 否 | 可选 | 标准 Piper，不是 X |
| 社区 Piper X 工具 | 多数无 LICENSE | 否 | 否 | 仅记录；方法可自行实现 |

## 6. 与 JCHENG 的落位

| 数据类别 | 落位 | 形式 | 状态 |
|---|---|---|---|
| 来源/许可/提交审计 | `jcheng-research/references/manipulation/piper-x-assets.md` | 本记录 | 已写 |
| 决策与比较 | `jcheng-research/reports/20261126-piper-x-simulation-data-map.md` | 13 节报告 | 已写 |
| URDF/网格/驱动/MoveIt/SDK | `~/.local/share/jcheng/assets/piper_x/` | 仓外资产库 + `SHA256SUMS` + `PROVENANCE.json` | 已物化并校验 |
| 资产清单、关节表、抓取脚本 | `jcheng-simulation/docs/robots/piper_x/`、`scripts/fetch_piper_x_assets.sh` | 文本清单 + 脚本，不含二进制 | 已写 |
| CAN 臂的 profile 契约 | `jcheng-interfaces/docs/proposals/piper-x-robot-profile.md` | 提案，不改 v0.1 IDL/schema | 已写 |
| CAN 硬件桥接 | `jcheng-system/docs/robots/piper-x.md` | 上游指针 + 桥接前置条件，不含实现 | 指针已写；桥未实现 |

## 7. 已执行 vs 推断

- **已执行**：GitHub API/raw 读取、`agx_arm_urdf` 稀疏克隆、三个仓库浅克隆、
  614+ 文件校验、URDF/xacro XML 解析、网格路径存在性检查、SHA-256 清单。
- **静态**：上表所有提交、许可、关节/质量/TCP 数值均来自对应提交的文件。
- **推断**：J6 5° 差异的原因、CSV 质量口径、`agx_arm_sim` 的 MIT 意图、社区仓库
  是否支持 X——均未获厂商确认，按 C/D 级处理。

## 8. 相关

- 报告：[Piper X 仿真数据地图](../../reports/20261126-piper-x-simulation-data-map.md)
- 仿真清单：`jcheng-simulation/docs/robots/piper_x/README.md`
- 契约提案：`jcheng-interfaces/docs/proposals/piper-x-robot-profile.md`
- 系统侧指针：`jcheng-system/docs/robots/piper-x.md`
- 仓外资产：`~/.local/share/jcheng/assets/piper_x/`（`PROVENANCE.json`、`SHA256SUMS`）
