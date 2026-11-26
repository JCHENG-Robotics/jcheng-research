# Piper X 仿真数据地图：GitHub 资产、许可与落位

> 报告状态：**draft**。日期：2026-11-26。
> 作者：ZCode（研究代理），for J. Cheng。评审：pending。
> 本报告影响的决策：是否以 `agx_arm_urdf@680fa925` 作为 Piper X 的唯一几何/惯性
> 主源、把仿真资产放在仓外资产库，并按 `jcheng-interfaces` 的 CAN 臂差异开新
> profile 契约；是否在 `jcheng-system` 启动 CAN 桥接工作。
> 研究边界：GitHub API/raw 读取、`agx_arm_urdf` 稀疏克隆、三个仓库浅克隆、URDF/
> xacro XML 解析与 SHA-256 校验。**未**构建或运行 ROS 2、Gazebo、MuJoCo、Isaac
> Sim；**未**连接机器人；**未**获得运动授权；**未**实测质量、惯量、TCP 或 J6 限位。
>
> **后续（2026-11-26）**：MVE-1 已在本机 Gazebo Harmonic 运行，结果见
> [`experiments/20261126-piper-x-gazebo-plant/result.md`](../experiments/20261126-piper-x-gazebo-plant/result.md)。
> 本报告 §12 的“未构建/未运行”边界描述的是数据地图阶段，不覆盖该实验。

**证据等级**：**S** 在本机复现（本报告仅指资产物化/解析）· **A** 一手源码或官方
文档 · **B** 可信二手/规格资料 · **C** 基于现有证据的推断 · **D** 未验证假设。

---

## 01. Executive Summary

**推荐**：以 MIT 许可的 `agilexrobotics/agx_arm_urdf@680fa925` 作为 Piper X 的
唯一几何、网格、惯性和关节限位主源；以 MIT 的 `agilexrobotics/agx_arm_ros@747d0722`
作为驱动/MoveIt 参考；把二进制资产放在**仓外资产库**（`~/.local/share/jcheng/assets/piper_x/`），
仓库只保留来源清单、校验和、关节表和抓取脚本。Gazebo/MuJoCo/USD 模型从这份 MIT
URDF **自行生成**，不复制无许可证的 `agx_arm_sim`、`piper_isaac_sim` 或社区模型。

三个支撑事实（A/S）：

1. MIT URDF 是 6 revolute + 1 个夹爪主关节（`gripper`，0…0.1 m）+ 2 个 mimic
   指关节；质量合计 4.3166 kg，J1–J6 限位为 ±150°、0…180°、-170°…0、±89°、
   ±89°、±170°。它已在 2026-10-13/15 修正 J6 限位和 link6 惯性。
2. 资产已在本机物化并校验：618 个上游文件、38,673,663 字节、`sha256sum -c`
   全部通过、0 个缺失网格（S，仅限“可获取且可解析”）。
3. 官方 ROS 2 驱动 `agx_arm_ros@747d0722`（MIT）通过 `pyAgxArm@d90e234`
   （**LGPL-3.0**）控制 Piper X；`pyAgxArm` 明确有 `ArmModel.PIPER_X` 和
   `demos/piper_x/test1.py`。

**主要风险**：Piper X 的 TCP 没有实测值（官方文档只给标准 Piper + 夹爪 0.1425 m
的示例）；J6 规格 ±165° 与 URDF ±170° 相差 5°；`agx_arm_sim` README 声称 MIT
但没有 LICENSE 文件；`jcheng-interfaces` 的 `robot-profile.v1` 要求 `servo_id`/
脉冲，CAN 臂不适用。

## 02. Research Questions

主问题：围绕 Piper X 的仿真工作，应该从 GitHub 取哪些数据、以哪一份为准、按什么
许可使用、分别放在 JCHENG 生态的哪个仓库/区域？

子问题：

1. 官方与社区仓库中，哪些明确支持 Piper X（而不是标准 Piper）？
2. 各仓库的许可证是否允许再分发网格、URDF、USD、MJCF、驱动代码？
3. 官方来源之间是否一致；不一致时哪一份是当前主源？
4. 现有 `jcheng-simulation`（禁止 mesh、单一 plant）、`jcheng-interfaces`
   （总线舵机 profile）、`jcheng-system`（pulse/bus-servo 桥）能否直接承接？
5. 哪些数据只能“参考/自行生成”，不能复制？

约束：仿真仓库 gate 禁止 `*.stl/*.dae/*.obj`；生态 license review 未关闭，仓库根
不得出现 `LICENSE`；不复制厂商代码；运动只经 `ExecuteMotion`；没有 Piper X 实机
和运动授权。交付物是**可追溯的数据地图 + 仓外资产 + 文本清单**，不是可运行的
Piper X plant。

## 03. Current System Analysis

- **`jcheng-simulation`**：tracked v0.1 是固定基座 5-DoF ArmPi 模型，primitive
  geometry；`docs/SIMULATION_MODEL.md:8-15` 明确“不是 ArmPi Ultra 的几何/动力学
  复刻”，“没有 vendor mesh/URDF/source”。Gate `scripts/check_repo_gate.sh:104-110`
  在整棵树里禁止 `*.stl/*.dae/*.obj`；`:43-46` 要求固定的
  `urdf/jcheng_armpi_sim.urdf.xacro`；`:83-91` 在包内禁止 `socketcan`、`can0` 等
  硬件 token。当前 tracked 仓库**没有** Piper/AgileX 引用。
- **`jcheng-interfaces`**：`schemas/robot-profile.v1.schema.json:28` 要求每个关节
  有 `servo_id`，`:43` 要求夹爪有 `servo_id` 和 `measured_open_pulses`/
  `measured_closed_pulses`；这是总线舵机模型。`JointTrajectory`/`MotionCommand`/
  `RobotState` 只携带 `string[] joint_names`，没有 DoF 常量。
- **`jcheng-system`**：`jcheng_vendor/jcheng_vendor/executor.py:40` 的
  `HardwareBridge` 语义是 `send_step`/`send_gripper`/`hold`/`read_bus`/
  `pulse_snapshot`，即脉冲/总线舵机；没有 CAN 臂适配器。运动仍只经
  `ExecuteMotion`。
- **`jcheng-research`**：已有 manipulation 主题和 13 节模板；本报告与
  `references/manipulation/piper-x-assets.md` 是本次新增来源记录。
- **资产层**：生态 taxonomy 没有 robot-description/asset 层；唯一先例是冻结的
  `jcheng-manipulation/ros2_ws/src/armpi_ultra_description`（mesh + 
  `THIRD_PARTY_NOTICES.md`），不能作为新资产的落位。

## 04. Research Methodology

- **检索**：GitHub 组织搜索 `org:agilexrobotics piper`、`org:agilexrobotics agx_arm`；
  仓库搜索 `piper_x`、`piper ros2 agilex`；对每个候选读取 `repos`、`git/trees?
  recursive=1`、`commits`、`license` 和 raw 文件。
- **纳入**：明确出现 `piper_x`/`Piper X`，或直接服务 Piper X 的末端/驱动/仿真资产。
- **排除**：只支持标准 Piper 且不能复用的仓库；但保留为“备选/参考”并标注。
- **阅读深度**：全文读 URDF、夹爪 xacro、SRDF、`joint_limits.yaml`、TCP 文档、
  驱动节点参数/话题/服务、`pyAgxArm` 的 `ArmModel.PIPER_X` demo、`piper_sdk`
  README；只读目录树/README 的是 `agx_arm_sim`、`piper_isaac_sim` 的 USD/MuJoCo/
  Gazebo 资产和社区仓库。
- **复现**：稀疏克隆 `agx_arm_urdf` 到临时目录，复制 `piper_x`、`agx_gripper`、
  LICENSE/README；浅克隆 `agx_arm_ros`、`piper_sdk`、`pyAgxArm`；生成 SHA-256；
  用 Python 标准库 `xml.etree` 解析 URDF/xacro 并检查 mesh 路径。
- **未做**：没有运行 `colcon build`、Gazebo、MuJoCo、Isaac Sim；没有构建 USD/MJCF；
  没有连机器人。

## 05. Literature Review

本问题没有论文主语料；可核对的“文献”是厂商规格与仓库文档。公开规格（**B**）：

| 项 | 值 |
|---|---|
| DoF | 6，球形腕 |
| 负载 | 1.5 kg |
| 工作半径 | 669 mm |
| 重复定位精度 | ±0.1 mm |
| 本体质量 | 约 4.5 kg |
| 供电/通信 | DC 24 V / CAN 1 Mbps |
| J4/J5/J6 | ±90° / ±90° / ±165° |

规格与 MIT URDF 的差异：J6 规格 ±165° vs URDF ±170°；本体质量 4.5 kg vs URDF
各连杆质量合计 4.3166 kg（不含夹爪/线缆，接近但不等于整机质量）。`pyAgxArm@d90e234`
的 `ROBOT_JOINT_LIMIT_PRESET_RAD["piper_x"]` 与 URDF 一致（J6 ±2.967060），
`ROBOT_MDH_PRESET["piper_x"]` 也与 URDF 关节原点一致（J1 d=0.123、J3 a=0.28503、
J4 a=0.27364、J5 a=0.07466、J6 d=0.03526）。因此 **两份官方代码源在 J6 ±170° 上
一致，公开规格是少数派**；但安全限位仍应以固件/总线读为准。规格表、URDF 与实机
称重是三个不同口径，不能互相替代。

## 06. Repository Investigation

| 仓库 | 提交 | 许可 | Piper X 相关性 | 关键内容 | 阅读 |
|---|---|---|---|---|---|
| `agilexrobotics/agx_arm_urdf` | `680fa925cd00db7e2628563d2edc5540963045de` | MIT | **主源** | `piper_x/urdf/piper_x_description.urdf`、`piper_x_with_gripper_description.xacro`、`piper_x/meshes/{stl,dae}`、`agx_gripper/` | 全文 URDF/xacro；提交历史 |
| `agilexrobotics/agx_arm_ros` | `747d0722074d4cebc095d8d44f3ef68d2023ba6f` | MIT | **官方驱动** | `src/agx_arm_ctrl`（`arm_type:=piper_x`、`pyAgxArm`）、`src/agx_arm_moveit`（SRDF/limits/ros2_control/TCP）、`docs/tcp_offset` | 参数/话题/服务、MoveIt 配置、TCP 文档 |
| `agilexrobotics/pyAgxArm` | `d90e234ba8e408cfa964b38aa9120b3131fc9f85` | **LGPL-3.0** | **官方 SDK** | `ArmModel.PIPER_X`、`demos/piper_x/test1.py`、CAN 协议驱动、`constants.py` 的关节限位/MDH 表 | README、API 入口、demo、常量表 |
| `agilexrobotics/piper_sdk` | `b847e5393a7ce6ff8508d713eca7bdd3a42421b4` | MIT | 遗留 SDK | V2/V3 协议、CAN 工具、`piper_msgs` | README、目录树、版本 |
| `agilexrobotics/agx_arm_sim` | `f8cd8b147c75d59e14f90fb0646770eefa268ed0` | **无 LICENSE**（README 称 MIT） | 有 X 资产 | `Moveit2/piper_x_gripper_moveit_config`、`piper_x.world`、USD/D435、MuJoCo（仅标准 Piper） | 目录树/README |
| `agilexrobotics/piper_isaac_sim` | `8e1f88fdb7afca49c40e9a0c1c01cc588e86f0d2` | **无 LICENSE** | 旧 X 资产 | 8 关节 `piper_x_description.urdf`、`USD/piper_x_v1.usd`、D435、`PIPER-XURDF.csv` | 全文 URDF 对比 |
| `google-deepmind/mujoco_menagerie` | `eea4c7431b63da8278b0ff31638e0b0e941cec0e` | MIT（模型内 LICENSE） | 否（标准 Piper） | `agilex_piper/` MJCF + meshes | 目录/许可 |
| `AB-pixel-pixel/piper-X` | `ea390f5bd4dc31865f23bed68f54c68bddcf79f6` | **无 LICENSE** | 社区 X MuJoCo | 下载 `agx_arm_ros` → 转 MJCF → 加 actuator；`minimal_piper_x_demo.py` | README |
| `Mamengyiyi/PiperX-ToolKit` | `e2d47da231ed461a5f7f82d406e73995848d5576` | **无 LICENSE** | 社区 X 数据采集 | 双 PiperX 拖动示教/主从、三路 RGB、LeRobot 转换 | README |
| `justagist/piper_cpp` | `01e1616e076fd0324f79ca6cee2ae0d7b23ba370` | MIT（LICENSE 明示） | 未验证 X | C++ SDK + ROS 2/MoveIt，部分派生自 `piper_sdk` | LICENSE/README |
| `Reimagine-Robotics/piper_ros` | `011be5fbc5a968cc06f044339ae6ee25f0cdbd7b` | MIT | 未验证 X | 基于 `piper_control` 的 ROS 2 驱动 | README |
| `xdongmiao/pico-piper-teleop` | `658acf7f91eb4ab628d6c8b2e17723743dc19261` | Apache-2.0 | 否（标准 PiPER） | Pico VR 遥操作 + LeRobot 采集，双 PiPER | 目录树/README |

### 6.1 驱动调用链（A）

`agx_arm_ros/src/agx_arm_ctrl/agx_arm_ctrl/agx_arm_ctrl_single_node.py`：
`main()` → `AgxArmFactory`/`pyAgxArm` → 200 Hz `feedback/joint_states`；
订阅 `control/joint_states`、`control/move_j`、`control/move_p`、`control/move_l`、
`control/move_c`、`control/move_js`、`control/move_cpv`、`control/move_mit`；
服务 `enable_agx_arm`、`control_enable`、`move_home`、`emergency_stop`。
`arm_type` 参数把 `piper_x` 传给 SDK；`effector_type:=agx_gripper` 路由夹爪。
这些都是**厂商接口**，不是 JCHENG 契约。

### 6.2 MoveIt 结构（A）

`agx_arm.urdf.xacro` 通过 `arm_type` include `piper_x_with_gripper_description.xacro`，
并加 `tcp_link`/`tcp_joint`；`agx_arm.srdf.xacro` 的 `arm` 组是 `base_link` →
`tcp_link` 的 chain，`gripper` 组只含 `gripper`，`gripper_joint1/2` 为 passive。
`joint_limits.yaml` 只有速度/加速度（6 臂 5.0，夹爪 1.0），没有位置限位；位置
限位来自 URDF。

## 07. Comparative Analysis

### 7.1 模型来源

| 候选 | 许可 | 关节 | 质量口径 | 结论 |
|---|---|---|---|---|
| `agx_arm_urdf@680fa925` | MIT | 6 + 夹爪主关节 + 2 mimic | 4.3166 kg | **采用** |
| `piper_isaac_sim@8e1f88fd` | 无 | 8（J1–J6 + J7/J8） | 1.5500 kg | 不采用；旧、无许可、不可混用 |
| `PIPER-XURDF.csv`（同上仓库） | 无 | 8 | 约 1.55 kg | 仅作质量属性对照；不作主源 |
| Menagerie `agilex_piper` | MIT | 标准 Piper | — | 可作 MuJoCo 结构参考；不是 X |

### 7.2 仿真后端

| 后端 | 官方 X 资产 | 许可 | 可行路径 |
|---|---|---|---|
| Gazebo | `agx_arm_sim` 有 `piper_x.world`/ros2_control | 无 LICENSE | 用 MIT URDF 自行生成 SDF/ros2_control；参考其配置项 |
| MuJoCo | 无官方 X；社区 `AB-pixel-pixel/piper-X` 有流水线 | 无 | 用 MIT URDF → MJCF（自行转换/加 actuator） |
| Isaac Sim | `agx_arm_sim`/`piper_isaac_sim` 有 USD | 无 | 用 MIT URDF 走 Isaac URDF importer 自行生成 USD |
| RViz/MoveIt | `agx_arm_ros` 配置（MIT） | MIT | 可直接参考/在资产库中使用 |

### 7.3 SDK/驱动

| 候选 | 许可 | X 支持 | 结论 |
|---|---|---|---|
| `agx_arm_ros` + `pyAgxArm` | MIT + LGPL-3.0 | 明确 `ArmModel.PIPER_X` | 官方路径；LGPL 需评审 |
| `piper_sdk` | MIT | 未声明 X | 遗留；不能假定支持 |
| `justagist/piper_cpp` | MIT | 未验证 | 非 LGPL 备选；需先验证 X |
| `Reimagine-Robotics/piper_ros` | MIT | 未验证 | 备选；标准 Piper |
| 社区 `PiperX-ToolKit` | 无 | 是（双 X） | 仅参考，不可复制 |

## 08. Critical Findings

1. **没有许可干净、开箱即用的 Piper X MuJoCo/USD/Gazebo 资产**（A）。官方仿真仓库
   `agx_arm_sim` 和 `piper_isaac_sim` 都没有 LICENSE；有 X 的社区 MuJoCo 仓库也没有
   LICENSE。唯一许可干净的是 MIT URDF/网格，因此必须**自行生成**仿真格式。
2. **两个“官方”模型不一致，且旧模型仍在传播**（A）。`piper_isaac_sim` 的 8 关节
   模型质量合计 1.55 kg，MIT 新模型 4.3166 kg；J4/J5/J6 原点、J6 限位、夹爪关节
   都不同。混用会导致 MoveIt/控制器关节数不匹配或动力学错误。
3. **`agx_arm_sim` 的 MIT 只写在 README 里**（A）。GitHub API 返回 `license: none`，
   仓库根没有 LICENSE；不能仅凭 README 主张再分发权。需要厂商书面确认或补 LICENSE。
4. **J6 限位有 5° 口径差**（A/B）。公开规格 ±165°，MIT URDF 与 `pyAgxArm`
   的 `ROBOT_JOINT_LIMIT_PRESET_RAD` 都是 ±170°。两份官方代码源一致，规格表是
   少数派；但安全限位仍必须由固件/总线读确认。在确认前，仿真软限位取更保守的
   ±165°（2.880 rad）。
5. **TCP 未实测**（A）。`docs/tcp_offset` 的 0.1425 m 是标准 Piper + 夹爪示例，
   不是 Piper X；`tcp_link` 默认 0。抓取前必须测量 `link6` → 夹爪指尖。
6. **`robot-profile.v1` 不适用于 CAN 臂**（A）。它要求 `servo_id` 和脉冲数组；
   Piper X 是 CAN 关节索引，没有舵机 ID/脉冲。直接复用会伪造字段或阻塞 profile。
7. **`HardwareBridge` 是 pulse/bus-servo 语义**（A）。CAN 臂需要新的 bridge；
   不能把厂商 `emergency_stop` 当作急停，也不能绕过 `ExecuteMotion`。
8. **驱动依赖 LGPL-3.0 的 `pyAgxArm`**（A）。`agx_arm_ros` 自身 MIT，但
   `agx_arm_ctrl` 运行时 import `pyAgxArm`；分发/修改前要做 LGPL 评审。
9. **数据采集工具存在但许可阻塞**（A）。`PiperX-ToolKit` 是最贴近双 X 拖动示教/
   LeRobot 的社区工具，但没有 LICENSE；`pico-piper-teleop` 是 Apache-2.0，但针对
   标准 PiPER。两者都不能直接作为 X 的数据管线。

## 09. Engineering Applicability

| 仓库 | 可承接 | 需要的工作 | 风险/成本 |
|---|---|---|---|
| `jcheng-simulation` | 资产清单、抓取脚本、关节表、未来 plant | 加第二 plant 需改 gate（单 plant、mesh 禁令、`can0` token）、ADR、测试；本次**不**改 plant | 中；gate 是许可/安全边界，不应擅自放宽 |
| `jcheng-interfaces` | CAN 臂 profile 提案 | v0.2 schema：`joints[].index`/可选 `servo_id`、prismatic gripper、`tcp_offset`；新 tag + manifest + locks | 高；契约变更需审计/签字 |
| `jcheng-system` | 未来 `HardwareBridge` 实现 | CAN 适配器、domain 41、状态真值（总线读）、软件停止语义、安全评审；指针见 `jcheng-system/docs/robots/piper-x.md` | 高；无 e-stop、无编码器，不能夸大 |
| `jcheng-perception` | D435 安装参考 | 外参实测；`piper_isaac_sim`/`agx_arm_sim` 的 D435 模型无许可，不可复制 | 中 |
| `jcheng-learning` | 数据采集/遥操作参考 | 先解决工具许可；Piper X 数据集不在 GitHub（HF 上的 `lerobot_piper` 是标准 Piper） | 中 |

## 10. Recommended Approach

**采用**：

1. 单一几何/惯性主源：`agx_arm_urdf@680fa925`（MIT），保留 LICENSE 与 commit。
2. 仓外资产库：`~/.local/share/jcheng/assets/piper_x/`，618 文件、38,673,663 字节、
   `SHA256SUMS` + `PROVENANCE.json`；仓库只放清单/脚本/关节表。
3. 仿真格式自行生成：Gazebo SDF/ros2_control、MuJoCo MJCF、Isaac USD 都从 MIT
   URDF 转换；转换脚本和版本记录进实验，不把生成物提交进 simulation 树。
4. 契约：在 `jcheng-interfaces` 提 v0.2 CAN 臂 profile（提案），不直接改 v0.1。
5. 硬件桥接：等实机/授权/安全评审后再做；优先评估官方 `agx_arm_ros` +
   `pyAgxArm`（LGPL）或许可更宽松的 `piper_cpp`（需先验证 X）。
6. 数据采集：先解决 `PiperX-ToolKit` 许可，或基于 Apache-2.0 的标准 PiPER 工具
   自行改造；不要把无许可代码复制进生态。

**不推荐**：

- 复制 `agx_arm_sim`/`piper_isaac_sim` 的 USD/MJCF/Gazebo 文件（无 LICENSE 或
  README-only MIT）。
- 使用 `piper_isaac_sim` 的 8 关节 URDF 或 `PIPER-XURDF.csv` 作为动力学主源。
- 把 `piper_sdk` 当作 Piper X 官方 SDK（README 已指向 `pyAgxArm`，且未声明 X）。
- 把 mesh 放进 `jcheng-simulation`（gate 会失败），或把 CAN token 写进仿真包。
- 把厂商 `emergency_stop` 描述为急停。

## 11. Experimental Design

**MVE-0（已运行，S）— 资产物化与解析**

- 假设：固定 MIT 提交可在本机复现，URDF/xacro 可解析，网格路径完整。
- 方法：稀疏克隆 `agx_arm_urdf@680fa925`，复制 `piper_x`/`agx_gripper`；浅克隆
  `agx_arm_ros@747d0722`、`piper_sdk@b847e539`、`pyAgxArm@d90e234`；生成 SHA-256；
  Python `xml.etree` 解析 URDF/xacro；检查 mesh 路径。
- 结果：618 个上游文件、38,673,663 字节；`sha256sum -c` 618/618 通过；
  6 个 revolute 关节；0 个缺失网格。
- 结论：**仅**证明“资产可获取、可校验、可解析”；不证明模型准确、可仿真或可上机。

**MVE-1（已运行 2026-11-26，S）— Gazebo plant**

- 假设：MIT URDF 可在 Gazebo Harmonic + `gz_ros2_control` 中加载，6 关节 + 夹爪
  可被 `joint_trajectory_controller` 驱动。
- 验收：URDF 无 mesh 错误；关节名/限位与 `joint_map.yaml` 一致；domain 43；
  `/sim/*` 真值源；不加入 0/41/42。
- 结果：上述验收项全部通过（13 links / 12 joints / 9 movable、22 mesh 全解析、
  限位与 `joint_map.yaml` 一致、3 控制器 active、domain 43 隔离；plant 使用
  `/sim/piper_x` 以避开 domain 43 上的其它 plant）。**实验追加的 A6 位置跟踪
  失败**：`joint2`/`joint3` 不响应位置命令，直接速度命令可移动；mimic 结构保留
  但动力学未实现。详见
  [result.md](../experiments/20261126-piper-x-gazebo-plant/result.md)。
- 失败条件：关节数/限位不一致、mesh 路径失败、控制器不激活。

**MVE-2（未运行）— 关节空间一致性**

- 假设：mock plant 与 Gazebo plant 对同一 joint trajectory 的终态误差在 1e-3 rad
  内（位置），且都遵守 `joint_map.yaml`。
- 验收：6 关节逐点误差、夹爪行程 0…0.1 m、mimic 关系 0.5/-0.5。
- 失败条件：任一关节超差或 mimic 关系错误。

**MVE-3（未运行）— 夹爪/TCP 实测**

- 假设：`link6` → 夹爪指尖的 TCP 可由 CAD 或卡尺测量，重复 10 次标准差 < 1 mm。
- 验收：记录 `tcp_offset` 6 维、测量方法、日期；与官方 0.1425 m 示例对比。
- 失败条件：无法稳定测量或与 CAD 差 > 2 mm。

**MVE-4（未运行）— CAN 桥接台架**

- 仅在获得实机与运动授权后；先只读总线，不运动；验证 `feedback/joint_states`
  是否是总线读还是命令缓存；再评估 `ExecuteMotion` 适配。
- 验收：只读状态与总线读一致；软件停止语义明确；无运动命令。
- 失败条件：需要运动才能验证、或无法区分命令缓存与测量。

## 12. Limitations & Uncertainties

- **无实机**：没有 Piper X、没有 CAN 适配器、没有运动授权；所有动力学/安全结论
  都是静态或推断。
- **无实测 TCP/质量/惯量**：URDF 质量 4.3166 kg 与规格 4.5 kg 不等；J6 限位
  5° 差异未解释；TCP 未测。
- **未构建/未运行**：没有 `colcon build`、Gazebo、MuJoCo、Isaac Sim；没有验证
  MIT URDF 在 Humble/Jazzy、Gazebo Harmonic、Isaac 版本下的兼容性。（数据地图
  阶段的边界；MVE-1 已于 2026-11-26 单独运行，见
  [`result.md`](../experiments/20261126-piper-x-gazebo-plant/result.md)。）
- **许可未闭环**：`agx_arm_sim` 的 MIT 只有 README；`piper_isaac_sim` 和社区 X
  工具无 LICENSE；LGPL 的 `pyAgxArm` 分发义务未评审。
- **社区仓库未逐行审计**：只读 README/目录树；`piper_cpp`、`Reimagine` 是否支持
  X 未验证。
- **数据**：HF 上的 `lerobot_piper*` 是标准 Piper，不是 X；本次未纳入。

## 13. References

官方仓库（访问日期 2026-11-26）：

- `agx_arm_urdf`, commit `680fa925cd00db7e2628563d2edc5540963045de`：
  <https://github.com/agilexrobotics/agx_arm_urdf>
- `agx_arm_ros`, branch `ros2`, commit `747d0722074d4cebc095d8d44f3ef68d2023ba6f`：
  <https://github.com/agilexrobotics/agx_arm_ros>
- `pyAgxArm`, commit `d90e234ba8e408cfa964b38aa9120b3131fc9f85`：
  <https://github.com/agilexrobotics/pyAgxArm>
- `piper_sdk`, commit `b847e5393a7ce6ff8508d713eca7bdd3a42421b4`：
  <https://github.com/agilexrobotics/piper_sdk>
- `agx_arm_sim`, commit `f8cd8b147c75d59e14f90fb0646770eefa268ed0`：
  <https://github.com/agilexrobotics/agx_arm_sim>
- `piper_isaac_sim`, commit `8e1f88fdb7afca49c40e9a0c1c01cc588e86f0d2`：
  <https://github.com/agilexrobotics/piper_isaac_sim>

第三方/社区：

- `mujoco_menagerie`, commit `eea4c7431b63da8278b0ff31638e0b0e941cec0e`：
  <https://github.com/google-deepmind/mujoco_menagerie>
- `AB-pixel-pixel/piper-X`, commit `ea390f5bd4dc31865f23bed68f54c68bddcf79f6`：
  <https://github.com/AB-pixel-pixel/piper-X>
- `Mamengyiyi/PiperX-ToolKit`, commit `e2d47da231ed461a5f7f82d406e73995848d5576`：
  <https://github.com/mamengyiyi/PiperX-ToolKit>
- `justagist/piper_cpp`, commit `01e1616e076fd0324f79ca6cee2ae0d7b23ba370`：
  <https://github.com/justagist/piper_cpp>
- `Reimagine-Robotics/piper_ros`, commit `011be5fbc5a968cc06f044339ae6ee25f0cdbd7b`：
  <https://github.com/Reimagine-Robotics/piper_ros>
- `xdongmiao/pico-piper-teleop`, commit `658acf7f91eb4ab628d6c8b2e17723743dc19261`：
  <https://github.com/xdongmiao/pico-piper-teleop>

本地记录与资产：

- 来源记录：[piper-x-assets.md](../references/manipulation/piper-x-assets.md)
- 仿真清单：`jcheng-simulation/docs/robots/piper_x/README.md`
- 契约提案：`jcheng-interfaces/docs/proposals/piper-x-robot-profile.md`
- 系统侧指针：`jcheng-system/docs/robots/piper-x.md`
- 仓外资产：`~/.local/share/jcheng/assets/piper_x/`（`PROVENANCE.json`、`SHA256SUMS`、
  `README.md`）

---

证据等级：**S** 在本机复现 · **A** 一手源码/官方文档 · **B** 可信二手/规格 ·
**C** 推断 · **D** 未验证假设。
