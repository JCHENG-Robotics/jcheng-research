# 结果 — Piper X Gazebo Harmonic plant（MVE-1，2026-11-26 运行）

- **状态**：已运行。设计见 [`design.md`](design.md)；本文件是运行结果与证据记录。
- **证据等级**：**S** 仅指“在本机 Gazebo Harmonic 8.15.0 上复现”；不是硬件验证，也不是
  动力学准确性验证。
- **范围**：离线仿真。无机器人、无 CAN 设备、无运动授权、无实机测量。
- **相关报告**：[`20261126-piper-x-simulation-data-map.md`](../../reports/20261126-piper-x-simulation-data-map.md)

## 1. 结论

| 项目 | 结果 |
|---|---|
| MIT URDF 在 Gazebo Harmonic 加载 | **通过**：13 links、12 joints、9 movable，`gz sdf -p` 无警告 |
| 网格路径 | **通过**：22 个 mesh 引用全部解析到仓外 MIT 资产，0 个 `package://` 残留，运行日志 0 个 mesh 错误 |
| 关节名/限位与 `joint_map.yaml` | **通过**：9 个 movable 关节的名称/类型/限位全部一致（abs tol 1e-9） |
| mimic 结构 | **通过**：URDF 与转换后 SDF 都保留 `gripper_joint1 +0.5`、`gripper_joint2 -0.5` |
| 控制器激活 | **通过**：`joint_state_broadcaster`、`arm_controller`、`gripper_controller` 全部 active |
| domain 43 / 域隔离 | **通过**：0/41/42 上没有 `/sim/piper_x/*`；43 上可见 |
| **6 关节位置跟踪（实验追加 A6）** | **失败**：`joint2`、`joint3` 不动；`joint1/4/5/6` 与夹爪主关节精确跟踪 |
| **mimic 动力学** | **未实现**：物理引擎不支持 SDF mimic；`gripper_joint1` 被 gz_ros2_control 驱动到 +0.04，`gripper_joint2` 保持 0 |

**判定**：报告 §11 的 MVE-1 验收条件（URDF 无 mesh 错误、关节名/限位一致、domain 43、
不加入 0/41/42、控制器激活）**通过**；实验追加的 A6（位置跟踪）**失败**。因此该 plant
可以用于“加载/激活/限位/域隔离”验证，但**尚不能**作为 MVE-2 的位置控制 plant，直到
`joint2`/`joint3` 问题解决。

## 2. 环境与输入

| 项 | 值 |
|---|---|
| 主机 | 操作者主机（非机器人），ROS 2 Jazzy，Python 3.12 |
| Gazebo | Harmonic **8.15.0**（`ros-jazzy-gz-sim-vendor`） |
| ros2_control | `ros2_control` 4.48.1，`ros2_controllers` 4.42.1，`gz_ros2_control` 1.2.20 |
| 资产 | `~/.local/share/jcheng/assets/piper_x/agx_arm_urdf-680fa925/` |
| 源提交 | `agx_arm_urdf@680fa925cd00db7e2628563d2edc5540963045de`（MIT） |
| 源哈希 | `piper_x_description.urdf` `93eb2a84…`；`piper_x_with_gripper_description.xacro` `88561fe4…`（均与 `joint_map.yaml` 一致） |
| 生成 URDF SHA-256 | `f42b4fae580fb27041a1ec74b05cd347e7e00da90e100deab6c5dcb3366f22e2` |
| 控制器 | 100 Hz；位置命令（6 臂 + 主夹爪）；mimic 指关节仅状态 |
| Gazebo 分区 | `GZ_PARTITION=jcheng-sim`；ROS domain **43** |

**共享 domain 43**：运行期间 domain 43 上还有其它会话的 ArmPi mock plant 和迁移后的
gate2 2-DoF arm plant，二者占用裸 `/sim` 名称（`/sim/controller_manager`、
`/sim/joint_states`、全局 `/robot_description`）。第一次运行因此与另一个 controller
manager 串线，数据作废。按 [`design.md`](design.md) 的 Amendment 1，所有 plant 名称
移到 `/sim/piper_x/*`，仍只在 domain 43；A5/A7 按 `/sim/piper_x/*` 判定。

## 3. 交付物

- 生成器：[`plant/piper_x_plant.py`](plant/piper_x_plant.py)（从 MIT URDF/xacro 组合，
  按 `joint_map.yaml` 覆写限位，把 `package://` 改写为 `file://`，注入
  `gz_ros2_control` 与 `<ros2_control>`）。
- 控制器：[`plant/config/piper_x_controllers.yaml`](plant/config/piper_x_controllers.yaml)。
- 世界：[`plant/worlds/piper_x_lab.sdf`](plant/worlds/piper_x_lab.sdf)（自包含，无 Fuel/网络）。
- 启动：[`plant/launch/piper_x_gazebo.launch.py`](plant/launch/piper_x_gazebo.launch.py)
  （domain 43 守卫、`/sim/piper_x`、分阶段启动、60 s 每阶段超时）。
- 静态检查：[`scripts/check_static.py`](scripts/check_static.py)。
- 轨迹探针：[`scripts/trajectory_probe.py`](scripts/trajectory_probe.py)。
- 编排：[`scripts/run_mve1.sh`](scripts/run_mve1.sh)。

plant 适配（全部记录在 `data/plant_report.json` 的 `adaptations`）：

1. `gripper_link` 的 **simulation-only 占位惯性**（0.05 kg）。MIT xacro 的该 link
   没有 `<inertial>`；`urdf2sdf` 会丢弃它和父关节 `gripper`，并连带破坏 mimic 引用。
   这不是实测值。
2. mesh URI 改写为仓外 `file://`；不改网格内容。
3. `/sim/piper_x` 命名空间；`robot_description` 同时做绝对/相对 remap（gz_ros2_control
   实际订阅绝对 `/robot_description`，相对 remap 不生效）。
4. 限位按 `joint_map.yaml` 写入；源值与合同值差为 0。

## 4. 验收结果（运行前固定）

| ID | 验收项 | 结果 | 证据 |
|---|---|---|---|
| A1 | 源哈希与 URDF 组合 | **pass** | `data/static_checks.json` A1.1–A1.2 |
| A2 | 9 个 movable 关节名称/类型/限位 | **pass** | A2.1–A2.4；最大源-合同差 0（abs tol 1e-9） |
| A3 | 网格路径与 `gz sdf -p` | **pass** | A3.1–A3.3；22 引用、0 缺失、0 `package://`、转换 exit 0、stderr 空 |
| A4 | SDF 结构与 mimic | **pass** | A4.1–A4.3；9 movable、mimic 在 `<axis>` 内、+0.5/-0.5 |
| A5 | 3 控制器 active / 9 关节 | **pass** | `logs/controllers_startup.txt`；`/sim/piper_x/joint_states` 含 9 关节 |
| A6 | 6 关节 ≤0.02 rad；夹爪 ≤0.002 m | **fail** | 见 §5.1：joint2 = −0.6 rad，joint3 = +0.5 rad；其余 0；夹爪 0.08 m 精确 |
| A7 | 域隔离 | **pass** | `logs/domain_isolation.txt`：0/41/42 无 `/sim/piper_x`；43 有 `/sim/piper_x/joint_states` |

运行时间：从 launch 到 3 控制器 active 约 **13 s**（本机负载下；含 3 s spawn 延迟）。
两个 action 都返回 `status=4`、`error_code=0`，但 **JTC 没有配置 tolerances，SUCCEEDED
不等于跟踪成功**；A6 以 `/sim/piper_x/joint_states` 的终态为准。

## 5. 关键发现

### 5.1 `joint2`/`joint3` 不响应位置命令（A6 失败）

- `arm_controller` 的 reference 正常爬升；`controller_state` 的 feedback 对 joint2/3
  保持 0；action 仍报告 SUCCEEDED。
- 单关节 `joint2` JTC 的输出与硬件命令接口都到 **0.4975**，但关节位置保持 0。
- 单关节 `joint4` JTC 正常跟踪（feedback 到 0.475），说明不是“单关节 JTC 路径”问题。
- **直接速度命令可以移动 joint2/3**（`ForwardCommandController`，±0.5 rad/s，两个方向
  都移动），说明轴、限位、物理约束和 `JointVelocityCmd` 路径都正常。
- 结论：命令到达硬件接口，但 `gz_ros2_control` 的 **POSITION 控制分支**没有对
  joint2/joint3 生效；`hold_joints` 回退把它们按 0 保持。根因未定位，见 §6 的排除表。
- 这**阻断 MVE-2**（mock vs Gazebo 的关节空间一致性），直到该缺陷解决。

### 5.2 mimic：结构保留，动力学未实现

- URDF 和 SDF 都保留 `gripper_joint1`（+0.5）/`gripper_joint2`（−0.5），SDF 位置正确
  （`<axis><mimic>`，`reference=0`）。
- 物理引擎日志明确：`Attempting to create a mimic constraint ... but the chosen physics
  engine does not support mimic constraints`。DART 与 bullet-featherstone 都是如此；
  bullet-featherstone 的插件包含 `SetMimicConstraintFeature` 符号但运行时不实现。
- `gz_ros2_control` 自己实现了 mimic 的**速度环**（`velocity_sp = -error * update_rate`）：
  `gripper_joint1` 被驱动到 **+0.04 m**（精确），`gripper_joint2` 保持 **0.0**。因此
  mimic 关系只被部分实现，不能写成“动力学已验证”。
- 结构 mimic 的验收（A4.2）通过；动力学行为是**已知限制**，不是通过项。

### 5.3 `joint_map.yaml` 的夹爪轴与固定源不一致

`joint_map.yaml` 记录的轴与 MIT xacro 的实际 `<axis>` 不同：

| 关节 | `joint_map.yaml` | 固定源 xacro |
|---|---|---|
| `gripper` | `[1, 0, 0]` | `[0, 0, 1]` |
| `gripper_joint1` | `[1, 0, 0]` | `[0, 0, 1]` |
| `gripper_joint2` | `[1, 0, 0]` | `[0, 0, -1]` |

限位、名称、origin 都一致；只有 axis 列不一致。plant 以 MIT 源为几何权威，保留 xacro
的轴，并在 `data/static_checks.json` 的 `joint_map_axis_mismatch` 中记录。建议修正
`joint_map.yaml` 的 axis 列或明确其坐标系（当前没有帧标注）。

### 5.4 其它记录到的事实

- `gripper_link` 在源 xacro 中没有 `<inertial>`；不加占位惯性时 `urdf2sdf` 直接
  exit 255（`link[gripper_link] is not modeled`、`parent joint[gripper] ignored`），
  这是 plant 适配 #1 的直接原因。
- `gz_ros2_control` 日志：`Enforcing command limits is disabled. Command limits from
  URDF will be ignored.` 因此 URDF 的 `effort/velocity` 不是运行时的命令限幅；plant
  的软限位必须由控制器/上层保证。
- 生成的 plant 总质量 **4.906554081 kg** = MIT 臂 4.316554081 + flange 0.04 +
  gripper_base 0.45 + 两指 0.05 + 占位 0.05；这是 URDF 声明值加占位值，不是称重。
- 模型通过 URDF 根关节 `world_to_base_link`（parent `world`）锚定；post-run
  `base_link` 位姿为 `(0, 0, 0)`，没有掉落。
- 服务器只跑 `-s`（无渲染、无传感器）；日志中 0 个 mesh 错误。**视觉 DAE 的运行时
  加载没有被渲染器执行**；DAE 文件本身 11/11 XML 可解析且无纹理依赖，但“可视化
  正确”不在本实验结论内。

## 6. 排除表（joint2/3 位置缺陷）

| 试验 | 结果 | 排除 |
|---|---|---|
| 全臂 6 关节 JTC | joint2/3 = 0；joint1/4/5/6 精确 | 不是“所有关节”问题 |
| 单关节 JTC joint2 | output/命令接口 0.4975，关节 0 | 不是 JTC 输出或接口未写 |
| 单关节 JTC joint4 | 跟踪到 0.475 | 不是单关节 JTC 路径 |
| 直接速度命令 joint2/3/4 | 三个关节都按 ±0.5 rad/s 移动 | 轴/限位/物理/速度路径正常 |
| `<ros2_control>` 关节顺序交换 | 失败跟随**关节名**，不跟随索引 | 不是接口索引错位 |
| 移除 mimic 状态接口 | 不变 | 不是 mimic 接口触发 |
| 位置增益 0.02（target_vel≈1.2 rad/s） | 不变 | 不是速度命令饱和/增益 |
| 移除 command interface min/max | 不变 | 不是命令限幅参数 |
| 移除 velocity command interfaces | 不变 | 不是 position/velocity 分支抢占 |
| DART vs bullet-featherstone | 两个引擎结果相同 | 不是单一引擎实现 |
| JTC 无 tolerances | 误差 0.6 rad 仍 SUCCEEDED | JTC 成功不能作为跟踪证据 |

未完成/不确定：控制器 deactivate/reactivate 后探针未能在超时内重新连上 action server，
该试验**无结论**，未用于排除。

## 7. 限制与不声称

- 没有机器人、没有 CAN、没有运动授权；所有结论仅限本机仿真。
- 不声称动力学准确性：`gripper_link` 占位质量、URDF 惯性声明、未实测质量/TCP。
- 不声称 mimic 动力学通过；只声称“结构保留 + 部分插件驱动”。
- 不声称 6 关节位置控制可用；A6 明确失败。
- 不声称 TF/时间同步正确：`/clock` 在 domain 43 是全局名称，若同时有第二个 Gazebo
  server，RSP 的 sim-time 时间戳可能来自不同 server；本实验没有验证 TF。
- 不声称视觉网格在渲染器中的外观；服务器模式不加载渲染。
- `joint_map.yaml` 的 J6 ±170° 与公开规格 ±165° 的差异未解决；plant 按合同用
  ±2.9670597 rad，未额外加保守软限位。
- 第一次运行的数据因共享 domain 43/裸 `/sim` 名称冲突而作废，未作为证据；只有
  Amendment 1 之后的 `/sim/piper_x` 运行被采用。

## 8. 下一步

1. **joint2/3 位置缺陷**：向 `gz_ros2_control` 提 issue，最小复现是“单关节 JTC
   joint2，output/命令接口 0.4975，关节不动；同一关节的速度接口正常；joint4 正常”。
   备选工作绕过方案（未验证）：用速度接口 JTC/外部 P 环；或换用 patched 插件。
2. **MVE-2 暂停**，直到 A6 通过；mock plant 的关节空间对照可以先行，但不能替代
   Gazebo 侧。
3. **mimic**：若 MVE-2 需要指关节运动，需自定义 Gazebo system plugin（按 master
   写 follower 位置）或接受“指关节静态”；不要把结构保留写成动力学实现。
4. **MVE-3**：测 `link6` → 夹爪指尖 TCP，填 `tcp_offset`；不要用 0.1425 m 示例。
5. **数据修正**：修正 `joint_map.yaml` 的夹爪 axis 列，或在 schema 中标注轴所在帧。

## 9. 复现

```bash
# 资产（一次）：默认 ~/.local/share/jcheng/assets/piper_x
bash ../../../jcheng-simulation/scripts/fetch_piper_x_assets.sh

cd experiments/20261126-piper-x-gazebo-plant
python3 scripts/check_static.py          # A1-A4；应 0 hard failure
bash scripts/run_mve1.sh                 # 完整 MVE-1；A6 失败时退出码 1
```

`run_mve1.sh` 的退出码 1 是**预期**的：静态 A1–A4、运行时 A5/A7 通过，A6 因 joint2/3
失败。证据在 `data/` 与 `logs/`；诊断试验的日志在 `logs/diagnostics/`，诊断 JSON 在
`data/diagnostics/`。

## 10. 证据索引

- 设计：[`design.md`](design.md)（含 Amendment 1）
- 静态：`data/static_checks.json`、`logs/static_checks.log`
- 生成器报告：`data/plant_report.json`（源哈希、关节表、mesh、适配、质量）
- 运行时：`data/runtime_probe.json`、`logs/trajectory_probe.log`
- 启动/控制器：`logs/mve1_launch.log`、`logs/controllers_startup.txt`、
  `logs/controllers_after.txt`
- 域隔离：`logs/domain_isolation.txt`、`logs/shared_domain_before.txt`
- 基座位姿：`data/base_pose.json`
- 日志分析：`data/log_findings.json`
- 诊断：`logs/diagnostics/`、`data/diagnostics/`
- 合同：`jcheng-simulation/docs/robots/piper_x/joint_map.yaml`、
  `jcheng-simulation/docs/robots/piper_x/SOURCES.yaml`
