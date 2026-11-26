# 实验设计 — Piper X Gazebo Harmonic plant（MVE-1）

- **日期**：2026-11-26（运行前冻结）
- **状态**：设计已冻结；运行结果见 [`result.md`](result.md)
- **负责人**：J. Cheng（决策），ZCode（实现与运行）
- **相关报告**：[`20261126-piper-x-simulation-data-map.md`](../../reports/20261126-piper-x-simulation-data-map.md)
- **上游资产清单**：`jcheng-simulation/docs/robots/piper_x/SOURCES.yaml`、
  `jcheng-simulation/docs/robots/piper_x/joint_map.yaml`
- **边界**：离线仿真，无机器人、无 CAN 设备、无运动授权、无实机测量。证据等级
  **S** 仅指“在本机 Gazebo Harmonic 上复现”。

## 1. 假设

1. 固定提交 `agilexrobotics/agx_arm_urdf@680fa925cd00db7e2628563d2edc5540963045de`
   的 MIT URDF/xacro 可以在 **Gazebo Harmonic 8.15 + gz_ros2_control 1.2.20**
   中加载为单个 plant：6 个 revolute 关节 + 1 个夹爪主关节 + 2 个 mimic 指关节。
2. `joint_trajectory_controller` 可以驱动 6 个臂关节和夹爪主关节；关节名与位置
   限位与 `joint_map.yaml` 一致。
3. 把 `package://` 网格 URI 改写为仓外资产库的 `file://` 路径后，Gazebo 不报
   网格缺失。
4. plant 只存在于 **ROS domain 43** 和 `GZ_PARTITION=jcheng-sim`，不进入
   0/41/42。

## 2. 基线

- 已迁移的 2-DoF `jcheng_simulation_arm` plant（`../../..` 的
  `jcheng-simulation`，2026-11-26 迁移）证明同一套 `gz_ros2_control` + `/sim`
  命名空间 + 分阶段启动链在本机可用。本实验复用其启动模式，但**不修改**该包
  或仓库 gate。
- 几何/惯性基线是 MIT URDF 本身；`joint_map.yaml` 是限位与关节名的合同。

## 3. 变量

| 类别 | 取值 |
|---|---|
| 自变量 | 资产根（`JCHENG_ASSET_ROOT`）、夹爪是否包含、控制器位置增益 |
| 控制变量 | 固定 commit 与 SHA-256、`ROS_DOMAIN_ID=43`、`GZ_PARTITION=jcheng-sim`、Gazebo Harmonic 8.15.0、`ros2_control` 4.48.1、100 Hz 控制、DART 物理引擎 |
| 因变量 | 关节数/类型/限位、mesh 解析结果、mimic 结构、控制器状态、轨迹终态误差 |

## 4. 环境

- 操作者主机（非机器人）：Ubuntu，ROS 2 Jazzy（`/opt/ros/jazzy`），Python 3.12，
  Gazebo Harmonic **8.15.0**（`ros-jazzy-gz-sim-vendor`），`gz_ros2_control`
  1.2.20，`ros2_control` 4.48.1，`ros2_controllers` 4.42.1。
- 资产：`~/.local/share/jcheng/assets/piper_x/agx_arm_urdf-680fa925/`（仓外）。
- 只读：`joint_map.yaml`、MIT URDF/xacro、网格；本实验只生成到 `generated/`。
- 无 GPU 依赖、无传感器插件、无网络/Fuel 下载；Gazebo 只跑 server
  （`-s --headless-rendering`）。

## 5. 指标

- 关节集合：12 个 joint（3 fixed + 9 movable）；9 个 movable = 6 revolute +
  3 prismatic（`gripper`、`gripper_joint1`、`gripper_joint2`）。
- 每个 movable 关节的 `lower/upper/effort/velocity` 与 `joint_map.yaml` 的
  数值差（SI）。
- 网格：URI 数、去重数、存在数、字节数；`gz sdf -p` 的 stderr 行数。
- mimic：`gripper_joint1 → gripper` 乘数 `+0.5`、`gripper_joint2 → gripper`
  乘数 `-0.5`；URDF 与转换后 SDF 都必须保留。
- 控制器：`joint_state_broadcaster`、`arm_controller`、`gripper_controller`
  的 active 状态；6 关节轨迹终态最大绝对误差（rad）；夹爪终态误差（m）。
- 域隔离：domain 0/41/42 上不出现 `*/sim/*` 话题；domain 43 上出现
  `/sim/joint_states` 与 `/sim/controller_manager`。

## 6. 验收（运行前固定）

| ID | 验收项 | 通过条件 |
|---|---|---|
| A1 | URDF 组合 | 固定提交的两个源文件 SHA-256 与 `joint_map.yaml` 一致；生成 URDF 良构 |
| A2 | 关节与限位 | 9 个 movable 关节的名称/类型/限位与 `joint_map.yaml` 完全一致（abs tol 1e-9） |
| A3 | 网格路径 | 所有 mesh URI 为 `file://` 且文件存在；0 个 `package://` 残留；`gz sdf -p` 无 mesh/URDF 警告 |
| A4 | SDF 结构 | 转换成功；mimic 位于 `<axis>` 内，乘数 +0.5/-0.5，`reference=0` |
| A5 | 控制器激活 | 3 个控制器在 90 s 内全部 active；`/sim/joint_states` 含 9 个关节 |
| A6 | 轨迹跟踪 | 6 关节终态误差 ≤ 0.02 rad；夹爪主关节 ≤ 0.002 m；action `error_code=0` |
| A7 | 域隔离 | 43 上有 plant；0/41/42 上无 `/sim/*`；Gazebo partition 为 `jcheng-sim` |

**mimic 动态行为（观察项，不计入 A1–A7）**：如果所选物理引擎支持 SDF 1.11
mimic，则指关节应满足 `q1=0.5*q_master`、`q2=-0.5*q_master`（tol 1e-3 m）；
如果不支持，记录引擎日志与实际关节值，作为 plant 的已知限制。不得把
“结构保留”写成“动力学已实现”。

## 7. 失败判据

- 任一源文件哈希不符，或 `joint_map.yaml` 与 URDF 的关节名/限位不一致 →
  停止，不“修正”源数据来迁就实验。
- `gz sdf -p` 失败，或出现 `link[...] is not modeled` / `parent joint[...] ignored`
  / 网格找不到 → 失败；允许的修复仅限于明确的 plant 适配（见下），且必须记录。
- 任一控制器在 90 s 内未 active → 失败，收集完整 launch 日志。
- 6 关节终态超差 → 先记录；允许调整 `position_proportional_gain` 重测一次，
  两次结果都写入 `result.md`。

## 8. 记录

- 设计（本文件）、结果 [`result.md`](result.md)。
- 脚本：`plant/piper_x_plant.py`（生成器）、`scripts/check_static.py`、
  `scripts/trajectory_probe.py`、`scripts/run_mve1.sh`。
- 数据：`data/static_checks.json`、`data/runtime_probe.json`、
  `data/log_findings.json`、`data/plant_report.json`。
- 日志：`logs/mve1_launch.log`、`logs/static_checks.log`、
  `logs/trajectory_probe.log`、`logs/controllers_*.txt`、
  `logs/domain_isolation.txt`。
- 生成物：`generated/piper_x_gazebo.urdf`（含本机绝对资产路径，不提交）。

## 9. 已知的 plant 适配（允许且必须记录）

1. **`gripper_link` 占位惯性**：MIT xacro 的 `gripper_link` 没有 `<inertial>`；
   `urdf2sdf` 会丢弃该 link 及其父关节 `gripper`（已在探测中复现）。plant 给该
   虚拟 link 加一个 **simulation-only** 小质量/惯量，不代表实测值。
2. **mesh URI 改写**：`package://agx_arm_description/agx_arm_urdf/...` →
   `file://<asset_root>/agx_arm_urdf-680fa925/...`；不改网格内容。
3. **`/sim` 命名空间 + `robot_description` remap**：沿用已迁移 plant 的模式，
   避免在 43 上出现未命名空间的 `/joint_states`。
4. **关节限位**：以 `joint_map.yaml` 为准写入 URDF；J6 的 ±170°（2.967 rad）
   与公开规格 ±165°（2.880 rad）的差异不在本实验解决，只记录。

## 10. 回退

- 实验只写 `experiments/20261126-piper-x-gazebo-plant/` 与仓外资产库的**读**；
  不修改 `jcheng-simulation`、`jcheng-interfaces` 或任何运行时仓库。
- 若 Gazebo 无法在本机稳定运行：保留静态检查结果（A1–A4）并把 A5–A7 标为
  **未验证**，不把静态结果写成运行验证。
- 生成的 URDF 与日志可删除；`design.md` 与 `result.md` 保留。

## Amendment 1 — namespace isolation on shared domain 43（2026-11-26，Accepted run 之前）

第一次运行期间发现：domain 43 同时被其它会话的 **ArmPi mock plant**（5 关节 +
`r_joint`）和迁移后的 **gate2 2-DoF arm plant** 使用；两者都占用裸 `/sim` 名称，
包括 `/sim/controller_manager`、`/sim/joint_states` 和全局
`/robot_description`。结果是 controller spawner 会连接到另一个 plant 的
controller manager（日志中出现 `gate2_arm/config/arm_controllers.yaml`），
JTC 的 reference 与实际状态来自不同实例；第一次运行数据因此作废，不作为证据。

修正（在 accepted run 之前）：

- plant 仍然只在 **domain 43**，但所有 ROS 名称移到 **`/sim/piper_x`**：
  `/sim/piper_x/controller_manager`、`/sim/piper_x/{arm,gripper}_controller`、
  `/sim/piper_x/joint_states`、`/sim/piper_x/robot_description`、
  `/sim/piper_x/tf`。
- A5 的“`/sim/joint_states` 含 9 个关节”改读 `/sim/piper_x/joint_states`；
  A7 的域隔离检查改查 `/sim/piper_x/*`。A1–A4 不变。
- `/clock` 仍是 domain 全局名称；如果同时运行第二个 Gazebo server，RSP 的
  sim-time 时间戳可能来自不同 server。MVE-1 不验证 TF/时间戳，这一点记入
  `result.md` 的限制。
- 运行前 preflight 必须确认没有残留的 `piper_x_lab.sdf` 进程，也没有其它
  `/sim/piper_x/*` 发布者；运行后按唯一 world 路径清理 Gazebo 子进程。
