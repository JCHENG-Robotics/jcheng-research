# 实验设计 — RLinf PICO→Piper X 最小可行实验（MVE-0…3）

- **日期**：2026-11-26（运行前冻结）
- **状态**：**预注册，未运行**。没有任何一步在 Piper X、PICO 或 RLinf 上
  执行过；本文件不是实验结果。
- **负责人**：J. Cheng（决策与实机授权），ZCode（设计与离线检查）
- **相关报告**：
  [`reports/20261126-rlinf-piper-pico-data-collection.md`](../../reports/20261126-rlinf-piper-pico-data-collection.md)
- **来源记录**：
  [`references/manipulation/rlinf-piper-pico.md`](../../references/manipulation/rlinf-piper-pico.md)
- **边界**：MVE-0 无硬件；MVE-1 只读；MVE-2/3 涉及真实运动，**每一次**
  都需要操作者单独的、明确的、按会话的授权，且操作者在场、物理断电开关
  伸手可及。不得由 CI、脚本或无人值守运行触发运动。

## 1. 假设

1. RLinf 的 `PiperArm`（`pyAgxArm@4b0f0658`）能在 Piper X 上完成只读反馈：
   6 关节、TCP、夹爪、固件版本可读，`model: piper_x` 配置可解析。
2. RLinf 的 PICO 订阅（`PicoExpert`）能接收外部 publisher 的 80 Hz JSON，
   字段/按键/校准与 `test_pico_data` 一致；失联 > 0.25 s 时进入 stale。
3. 用 ARX5 式 `CARTESIAN_POSE` + `PicoTcp` + `PiperArm.move_pose()`
   （`move_p`，TCP→法兰转换）可以在低速下把操作者位姿映射为 Piper X 的
   笛卡尔目标，且不触发限位/故障。
4. LeRobot 导出能把 Piper X 的分集写成可回放的分片（`robot_type:
   piper_x`，`fps` 与实测控制率一致）。
5. 以上可以在不修改任何产品仓库、不接入 `jcheng-system`、不绕过
   `ExecuteMotion` 的前提下，作为**生态外台架实验**完成。

## 2. 基线

- **无 PICO 基线**：`test_piper_controller --read-only` 的关节/TCP/夹爪
  读数；`--speed-percent 10` 下的 2° 关节步进与夹爪 0.5 行程（需要单独的
  运动授权）。
- **无 Piper 基线**：`test_pico_data` 接收 publisher 的 JSON，打印
  `recv_rate`、头显/手柄位姿、`grip`/`trigger`、按键。
- **数据基线**：本工作区没有 Piper X 的 PICO 演示数据；没有可比的
  成功率/延迟基线。MVE-3 的验收因此以“数据完整/可回放/时间戳一致”为主，
  不以操作成功率为唯一指标。

## 3. 变量

| 类别 | 取值 |
|---|---|
| 自变量 | 控制模式（只读/关节/笛卡尔）、`speed_percent`（10/30）、`step_frequency`（10/30 Hz）、Pico `position_scale`/`rotation_scale`、有无相机 |
| 控制变量 | Piper X 固件、CAN 适配器与 1 Mbit、TCP 偏移、夹爪行程、PICO 头显/固件、XRoboToolkit 版本、publisher 80 Hz、同一操作者、同一工位 |
| 因变量 | 反馈完整性、命令延迟、跟踪误差、stale 行为、停止时间、分集数量/可读性、丢帧率、时间戳抖动、动作饱和/裁剪 |

## 4. 环境

- **臂**：AgileX Piper X（6 revolute + AgxGripper），USB-to-CAN，
  SocketCAN `can0`，1 Mbit；物理断电开关/急停在操作者伸手可及处。
- **PICO**：Pico 4 Ultra（XRoboToolkit-Unity-Client README 的目标设备）+
  手柄；PC 侧 Ubuntu 22.04/24.04 + XRoboToolkit PC Service +
  `xrobotoolkit-sdk`（MIT Pybind）+ 自写 publisher（80 Hz JSON）。
  **不使用**无许可证的 `pico_software` 作为依赖；若仅为快速验证，可在
  隔离环境临时运行并记录其许可风险，但不入库、不再分发。
- **主机**：x86_64 Linux（推荐，RealSense/Pybind 轮子齐全）；若用 Pi 5/
  aarch64，相机走 UVC/V4L2 或外接采集机，且不得与现有 perception ingress
  同时占用相机。
- **软件**：独立 venv；RLinf commit `ed0e1b8`；`bash requirements/install.sh
  embodied --env piper`；`pyzmq`；`pytest`；不修改产品仓库。
- **网络**：PICO PC 与采集主机同网；同机用 `ipc:///tmp/vr_data.ipc`，跨机
  用 `tcp://<publisher_ip>:<port>`；publisher 绑定 `0.0.0.0`，consumer 填
  具体 IP，绝不填 `0.0.0.0`。

## 5. MVE-0 — 离线一致性（无硬件）

**目的**：在接任何硬件前，确认环境、配置、PICO JSON schema 和 fake SDK
测试路径可用。

**步骤**：

1. 在独立 venv 安装 RLinf 的 Piper 依赖；记录 `pip freeze`、commit SHA、
   安装耗时/体积。
2. 解析 `PiperConfig(model="piper_x", can_channel="can0", ...)`，只做
   配置构建，不 `connect()`。
3. 用 fake ZMQ PUB 发 80 Hz JSON（字段同 §4），运行
   `python -m toolkits.realworld_check.test_pico_data --zmq-addr
   ipc:///tmp/vr_data.ipc --max-messages 200`。
4. 运行 `pytest` 中与 Piper/Pico 相关的 fake-SDK 单测（若存在）；记录
   失败/跳过原因。
5. 用 fake SDK 写一个最小 `PiperCartesianEnv` 单测：动作 10 维、限位裁剪、
   TCP→法兰转换、stale 保持（不接硬件）。

**指标/验收**：

- 配置构建成功；`model: piper_x` 被接受；无导入错误。
- `test_pico_data` 收到 ≥ 95% 的 200 条消息，字段/按键正确，`recv_rate`
  在 75–85 Hz；Ctrl-C 干净退出。
- 单测通过；无网络/硬件依赖。

**失败判据**：依赖冲突、配置拒绝 `piper_x`、schema 不匹配、消息率 < 60 Hz
或字段缺失；任一失败即停止，不进入 MVE-1。

## 6. MVE-1 — 只读硬件（无运动）

**目的**：确认 Piper X 的 CAN 反馈、固件探测、夹爪状态与 PICO 流在**不
下发运动**的情况下可用。

**前置**：操作者到场；确认工作空间清空；确认断电开关可用；明确记录
“本次授权只读，不下发运动”。

**步骤**：

1. `sudo ip link set can0 down` → `type can bitrate 1000000` → `up`；
   `ip -details link show can0`；`timeout 5 candump -n 5 can0`。
2. `python -m toolkits.realworld_check.test_piper_controller --channel can0
   --model piper_x --read-only --gripper-max-width 0.1`（若无夹爪用
   `--no-gripper`）；记录 6 关节、TCP 四元数、夹爪开口、固件 profile。
3. 启动 XRoboToolkit PC Service → 连接头显 → 启动 publisher →
   `python -m toolkits.realworld_check.test_pico_data --zmq-addr ...`；
   移动头显/手柄，按 grip/trigger/A/B，记录 `recv_rate`、位姿、按键。
4. 把 publisher 杀掉/断网 2 s，观察 `test_pico_data` 的 stale 行为；
   重启后确认恢复。
5. 记录 CAN 错误计数（`ip -s -details link show can0`）、进程 PID、
   启动时间、日志路径。

**指标/验收**：

- 6 关节/TCP/夹爪均有非零、连续更新；固件版本可解析为
  `default`/`v183`/`v188`/`v189` 之一；无 "stopped reporting" 错误。
- PICO 流 ≥ 60 Hz（目标 80 Hz），`grip`/`trigger` 连续，A/B/X/Y 可读；
  stale ≤ 0.25 s 内被标记，恢复后重新可用。
- 无任何运动命令；CAN 无 bus-off/错误帧激增。

**失败判据**：无反馈、固件不识别、夹爪 mode 不是 `width`、PICO 字段/
按键不匹配、stale 不触发、CAN 错误。任一失败即停止；不进入 MVE-2。

## 7. MVE-2 — 低速单臂笛卡尔遥操（需要单独运动授权）

**目的**：验证 `PiperCartesianEnv` + `PicoTcp` + `move_p` 的最小闭环，
只做小范围、低速、单臂运动。

**前置**：MVE-0/1 通过；操作者明确授权本次运动；`speed_percent=10`；
工作空间盒（例如 base 前方 0.15–0.35 m、±0.15 m、0.05–0.25 m，按实际
工位标定）；桌面清空；物理断电开关在手；单人操作，另一人观察（可选）。

**步骤**：

1. 用 fake SDK 单测确认动作 10 维、rot6d→四元数→Euler、TCP→法兰转换、
   限位/工作空间裁剪。
2. 启动 `PiperCartesianEnv`，先不发 Pico 运动：确认 reset 到安全位、
   观测/相机正常、`move_p` 目标等于当前 TCP（无跳变）。
3. 操作者握住 grip，做 ±2 cm / ±5° 的小幅运动；记录目标/实测 TCP、
   命令时间戳、Pico 时间戳、`move_p` 调用时间。
4. 松开 grip，确认保持；再握，确认从当前位姿重新锚定，无跳变。
5. 杀 publisher/断网，确认在 `max_stale_s` 内保持，不追目标；恢复后
   需重新校准确认。
6. 按 Ctrl-C/杀进程，记录从停止命令到无新命令的时间；最后用物理断电
   开关验证真正的停止路径。

**指标/验收（暂定，需 MVE-1 数据校准）**：

- p95 命令延迟（Pico 采样→`move_p` 调用）≤ 150 ms；无 > 500 ms 的尖峰。
- 稳态位置误差 ≤ 10 mm、旋转误差 ≤ 2°（小范围、低速）。
- 无未命令运动；松手/失联/停止后无持续目标推进。
- 关节不触发限位/故障；CAN 无 bus-off；夹爪开合正常。
- 操作者主观评分（1–5）≥ 3：可预测、无抖动、无需频繁重锚。

**失败判据**：延迟 > 300 ms 或抖动导致无法操作；位置误差 > 20 mm；
任何未命令运动/自碰撞风险/限位故障；停止路径不明确。任一失败即停止，
回到只读模式，记录日志，不重复尝试。

## 8. MVE-3 — 演示采集（需要单独运动授权）

**目的**：采 20 个成功 episode，验证 LeRobot 导出的完整性/可回放性。

**前置**：MVE-2 通过；操作者授权；固定工位、固定任务（例如
“抓取方块放入盒中”）、固定初始布局；相机 1–2 路（腕部/外部），
分辨率/帧率记录；`robot_type: piper_x`；`fps` 与实测控制率一致
（先 10 Hz，若 MVE-2 证明 30 Hz 可行再提高）。

**步骤**：

1. 操作者按 B 开始，X 成功保存，A 失败丢弃（`PicoEpisodeControlWrapper`）；
   每个 episode 15–60 s；失败可重试，但记录失败次数。
2. 每 5 个 episode 回放一次（`toolkits/lerobot/visualize_lerobot_dataset`
   或离线脚本），检查图像/状态/动作/时间戳。
3. 采满 20 个成功后，合并/校验分片；记录数据集大小、帧数、episode 长度
   分布、动作饱和/裁剪计数。
4. 用同一配置重放 1 个 episode（只读/空载，需单独授权），确认动作可复现。

**指标/验收**：

- 20/20 成功 episode 已保存且可读；`meta/info.json` 的 `fps`、
  `robot_type`、维度正确；`episodes.jsonl` 与 parquet 一致。
- 时间戳单调；图像与动作对齐（误差 ≤ 1 帧）；丢帧 < 5%；无损坏分片。
- 动作在关节/工作空间限位内；预裁剪动作的饱和计数被记录（不能靠裁剪
  掩盖）。
- 回放 1 个 episode 无异常；操作者确认数据可用。

**失败判据**：分片损坏/不可读；时间戳回退；图像/动作错位 > 1 帧；
丢帧 > 5%；任何不安全运动。失败即停止采集，保留原始日志，不把失败
episode 标成成功。

## 9. 记录方式

- 每次会话一个目录：`experiments/20261126-rlinf-piper-pico-mve/logs/
  <YYYYMMDD-HHMMSS>/`（本地，不入 git；大文件/视频/数据不入库）。
- 记录：命令、RLinf/pyAgxArm SHA、配置、CAN 状态、`pip freeze`、PID/
  启动时间、操作者授权文本与时间、每步 CSV/JSONL（Pico 时间戳、目标/
  实测 TCP、关节、夹爪、`move_p` 调用时间、stale/fault 标志）、失败/停止
  原因。
- 结果写入 `result.md`，并回填报告 §11；**未运行就不写 result**。
- 任何“已验证”结论必须指向具体日志文件与日期；否则按 C/D 级处理。

## 10. 回退策略

- 任何异常：先停进程（Ctrl-C/`kill`），再 `sudo ip link set can0 down`，
  再物理断电；不反复重连、不无限重试。
- 失败后保留 venv/日志，不改产品仓库；下一次从 MVE-0/1 重新开始。
- 若 PICO/相机/驱动出现不可恢复问题，回退到“只读 Piper + 人工关节示教”
  或“leader-arm 数采”方案，不强行用 PICO。

## 11. 授权与边界

- MVE-0 无运动、无硬件；MVE-1 只读（注意 `connect()` 可能使能电机，
  按厂商文档警示清场）。
- MVE-2/3 的**每一次**运动都需要操作者单独的、明确的、按会话的授权；
  本设计文件不构成授权。
- 不得在 ArmPi/`jcheng-system` 上运行；不得让 RLinf 成为生态运动源；
  不得绕过 `ExecuteMotion`、lease、stop latch 或 `capability.yaml`。
- 不复制厂商源码/固件，不把无许可证的 `pico_software` 入库或再分发。
