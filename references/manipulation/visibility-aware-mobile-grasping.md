# 动态环境中的可见性感知移动抓取 — Visibility-Aware Mobile Grasping in Dynamic Environments

- **类型**：一手论文（arXiv 预印本 v5，8 页全文）+ MIT 代码仓库静态审计
- **访问日期**：2026-11-25
- **阅读范围**：全文 8 页；Table I、Figure 1–7、Eq.(1)–(4)；代码
  `AdaCompNUS/Visibility-Awared-Mobile-Grasping` @ `c37eb1638f66` 的
  README、`experiments/run_maniskill_benchmark.py`、`grasp_anywhere/observation/scene.py`、
  `configs/real_fetch.yaml`、`configs/maniskill_fetch.yaml`（只读，未运行）。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/09_Visibility_Aware_Mobile_Grasping.pdf`
  （8 页，56,242,903 字节）。**未入库**：第三方预印本 + 远超 5 MB 门禁。
- **许可**：论文 arXiv 非独占分发许可（非 CC）；**代码 MIT**；项目页 CC BY-SA 4.0
  （仅网站）。

## 来源

- Hu, T.; Xiao, A.; Hsu, D.; Zhang, H. *Visibility-Aware Mobile Grasping in
  Dynamic Environments*. arXiv:2605.02487v5 [cs.RO], 2026-10-26.
  <https://arxiv.org/abs/2605.02487>
- 项目页：<https://visibility-aware-mobile-grasping.github.io/>（HTTP 200；
  Code 按钮指向下方仓库；有 RoboMesh 在线 demo）。
- 代码：<https://github.com/AdaCompNUS/Visibility-Awared-Mobile-Grasping>
  @ `c37eb1638f66`，MIT，约 94 MB，created 2026-04-24，pushed 2026-09-28。
  含 ManiSkill/Gazebo/真机脚本、RL/VLA baseline、`resources/grasp_benchmark.json`
  （20 scenes × 20 tasks = 400）。**ROS 1 Noetic / Ubuntu 20.04 / CUDA 12.4 /
  Python 3.11 / pixi**。
- 真机：Fetch + ROS + AMCL；5 个室内地点；40 个配置（20 static + 20 dynamic）。

## 论文声称的核心结果（作者报告值，未独立复现）

- 仿真 ManiSkill3 + ReplicaCAD，**400 个场景 × 5 runs**，Table I 报
  mean ± 95% CI 半宽：
  - 未知静态：**70.3±1.1%**；Navigation-and-manipulation 54.0±2.4%；
    CapMap 53.0±2.4%；Direct 27.2±2.5%；RL Hard 12.0%；SG-VLA 0.0%。
  - 动态：**57.9±1.5%**；Nav 48.6±3.4%；CapMap 49.7±0.9%；Direct 16.1±1.1%。
  - 静态碰撞率：Ours **5.0±1.5%** vs Nav 7.7±1.1%、w/o Vel 12.3±2.3%。
  - **动态碰撞率：Ours 13.9±3.4% vs Nav 7.5±1.7%、CapMap 8.2±0.8%**。
- 真机：**只部署完整系统，无 baseline**；20 static + 20 dynamic：
  **65.0% / 55.0%**（仿真同系统 70.4/57.9）。
- 控制周期约 **100 ms**：map 69 ms、gaze 26 ms、collision 3 ms；
  重规划约 150 ms（planning 50–80 ms）；subgoal 369 ms、抓取检测 1.2 s
  仅在阶段转换运行。
- 抓取失败 46 例：43.5% 几何合理但运动学不可行、30.4% 位姿错位、
  23.9% 举升滑落。

## 方法要点

- **问题**：未知/动态室内环境，有限 FOV；两个可见性约束——碰撞可见性
  （进入扫掠体积前刷新观测）与物体可见性（抓取构型保持目标在视野）。
- **Gaze policy**：`a*_v = argmax Σ Φ(x)·V(x,a_v)`；执行阶段
  `Φ(x)=I(x∈V(ξ_t))·w_safety(x)`，`w_safety` 按 lookahead 折扣与路径点速度
  加权，强调“还来得及纠正”的区域；pan-tilt 网格穷举。
- **Subgoal 行为树**：grasp → pre-grasp → observe；Contact-GraspNet 候选 +
  capability map 过滤 + FPS 多样性 + 置信度/距离排序 + 全身 IK/碰撞/
  自遮挡校验；失败则采观察位姿。
- **全身规划**：Hybrid A* + Reeds-Shepp + RRT-Connect + VAMP 并行碰撞 +
  shortcut/B-spline；20 Hz 全身速度跟踪 QP。
- **真机**：Fetch（3-DoF 底盘 + 1-DoF 躯干 + 7-DoF 臂 + pan-tilt 头），
  AMCL 定位。

## 批判性评估

### “unknown static” 与代码里的 canonical map 不一致（最重要）

- 代码核验：`experiments/run_maniskill_benchmark.py:156-171` 读取
  `canonical_map_path` 并作为 `static_pcd_paths` 传入 `Fetch`；
  `grasp_anywhere/observation/scene.py:13` 明确 `static_map (S): canonical
  world PCD, considered immutable`，`:161-162` 的 belief 是 `E(t)=S∪M(t)`；
  `configs/real_fetch.yaml:6` 加载 `resources/mp_collision_models/` 预建
  碰撞模型。
- 因此“unknown static / previously unseen layouts”至少是“已知房间/家具、
  未知物体摆放与动态障碍”，不是完全未知的静态布局。论文正文未披露该先验，
  且与 Related Work 批评“pre-built 3D maps”的立场冲突。

### 动态碰撞率高于解耦 baseline

- 摘要说 “significantly reducing collisions”，但 Table I 动态条件
  Ours 13.9±3.4% vs Nav 7.5±1.7%、CapMap 8.2±0.8%，约为 Nav 的 1.9 倍。
- 可能解释是成功率更高、尝试次数更多，碰撞暴露更大；论文没有按尝试次数/
  行驶距离归一化，也没有 per-attempt 碰撞率。**摘要与表格存在实质矛盾。**

### 真机证据与配置差异

- 真机每条件 20 次、总 40 次、无 CI、只跑完整系统、无 baseline；
  65%/55% 的 Wilson 95% 区间约 [43,82]% / [34,74]%，与仿真 70.4/57.9
  大幅重叠。“strong generalization across diverse indoor settings”是
  过度表述。
- 仿真 `maniskill_fetch.yaml` 的 `dynamic_costmap: True`，真机
  `real_fetch.yaml` 是 `False`；仿真有 canonical map，真机是预建模型 +
  不同 `scene_mode`。sim-to-real gap 混入了配置差异，不能只归因于感知噪声。

### 可见性约束没有被直接测量

- 核心卖点是两个 visibility constraints，但结果只报成功率、碰撞、SPL、
  失败分类；没有“抓取时目标可见比例”“扫掠体积被观测覆盖比例”“目标可见
  时长”“gaze 指向扫掠体积时间占比”。Eq.1–4 的 γ、w_d、ε、lookahead 40、
  decay 0.999 无敏感性分析。

### 统计与 baseline

- 统计设计优于多数机器人论文：5 次 run、95% CI、per-scene 方差、失败分类；
  但只对 w/o Observation Stage 做了 Welch t 检验（p=0.20/0.28），主比较
  没有正式检验/多重比较校正。
- SG-VLA 原代码不可用，作者重实现后 1.6%/0.0%、碰撞 78.8%/94.8%，
  更像未调好的重实现；RL Hard 12.0/9.5。真正有竞争力的 baseline 只有
  Nav（54.0/48.6）与 CapMap（53.0/49.7）。没有对比其他 visibility-aware
  planning / joint gaze-motion 方法，也没有 POMDP/MPC baseline。
- 46 个抓取失败人工标注，未报告标注者数量/一致性。

### 算力与复现

- 100 ms/周期、map 69 ms、gaze 26 ms、planning 50–80 ms 未给硬件；
  ManiSkill3 是 GPU 并行仿真，Contact-GraspNet/VAMP 很可能在工作站/GPU 上，
  Fetch 板载 NUC 不可能同时跑。不能直接换算到 Pi 5/3060。
- 代码/benchmark 齐全，理论上可重跑 400×5；但预计算资源从 Dropbox 下载、
  GPU/服务依赖、真机 Fetch 都不易复现；真机 40 次记录未公开。

## 代码与数据

- **代码 MIT、benchmark JSON 公开**，是本批次可复现性第二好的论文（仅次于
  06）。但 ROS 1 Noetic、Fetch 专用、依赖 VAMP/pytracik/ikfast 编译，
  与 JCHENG 的 ROS 2 Humble/5-DoF 不兼容。
- 未提供：每次 trial 的原始结果、5 次 run 种子/日志、真机记录、Table I
  复现输出、预计算资源（Dropbox 未验证）。

## 与 JCHENG / ArmPi Ultra 的适配

- **平台差距**：Fetch 是 11-DoF 全身（3 底盘 + 1 躯干 + 7 臂 + pan-tilt）；
  ArmPi 是 5-DoF 臂 + 夹爪，无移动底盘/躯干/pan-tilt。whole-body planner、
  非完整底盘、torso height map、gaze policy 大部分不适用。
- **算力**：Pi 5 做 5–10 m 房间点云 + VAMP + Contact-GraspNet 不现实；
  RTX 3060 6 GB 可跑抓取网络，但控制回路要拆成“Pi 采集/执行 + 笔记本
  感知/规划”。论文未给硬件，无法直接换算。
- **状态**：论文假设关节反馈/AMCL/碰撞检查可信；ArmPi 无编码器，
  `/joint_states` 是命令缓存。直接碰撞检查会把命令位置当真实位置。
- **安全**：JCHENG 无 e-stop/刹车/自碰撞模型；论文的实时全身规划不能替代
  安全层，所有运动仍须经 `ExecuteMotion`，低置信度即停。
- **可复用**：① 三层行为树回退（grasp→pre-grasp→observe）适合 5-DoF
  桌面臂的失败恢复；② 可见性约束的 pre-grasp 采样（FOV + 无自遮挡 + IK）
  可直接用于 D435i + 夹爪；③ 失败分类法；④ “先观察再抓”的阶段转换。
  不可复用：whole-body VAMP、非完整底盘、pan-tilt gaze、11-DoF 协调、
  70.4/57.9 指标。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | 三层行为树回退（grasp→pre-grasp→observe） | B（真实系统 + 代码） | **采纳**为状态机设计 |
| 2 | 可见性约束的 pre-grasp 采样（FOV + 无自遮挡 + IK） | B（方法 + 代码） | **采纳**，先在静态桌面验证 |
| 3 | 速度感知 gaze / pan-tilt 主动感知 | D（ArmPi 无 pan-tilt） | **不采纳** |
| 4 | 全身 VAMP/非完整底盘 receding-horizon | D（无底盘/躯干，算力不够） | **不采纳** |
| 5 | 碰撞率按尝试次数/行驶距离归一化 | A（动态 13.9% vs Nav 7.5% 反例） | **采纳**为验收指标 |
| 6 | 披露静态地图先验再谈 unknown | A（代码 canonical map） | **采纳**为文档要求 |
| 7 | 真机 40 次、无 CI、无 baseline 足以证明泛化 | A（论文/本评审 Wilson） | **不采纳**该主张 |
| 8 | 代码 MIT、benchmark 公开 | A（仓库） | **仅借鉴**；ROS 1/Fetch 不可直接移植 |

## 核验片段

1. “our system achieves success rates of 70.4% in unknown static environments and 57.9% in dynamic environments” — Abstract, p.1
2. “outperforming the decoupled navigation-and-manipulation strategy by 16.3 and 9.3 percentage points” — Abstract, p.1
3. “Entries report the mean with the 95% confidence-interval half-width from Student's t distribution over five runs” — Table I caption, p.7
4. “We generated 400 test scenarios (20 scenes × 20 objects)” — p.5
5. “40 configurations total: 20 in static unknown and 20 in dynamic scenarios” — p.5
6. “It achieved success rates comparable to simulation in both static (65.0% vs. 70.4%) and dynamic (55.0% vs. 57.9%) environments” — p.6
7. “Ours (Full System) 70.3 1.1 5.0 1.5 … 57.9 1.5 13.9 3.4” — Table I, p.7
8. “Among 46 manually labeled grasp failures, 43.5% were geometrically sound but kinematically infeasible grasps” — p.7
9. “Each control cycle took approximately 100 ms (map update 69 ms, gaze optimization 26 ms, collision checking 3 ms)” — p.6
10. `canonical_map_path = scene_data.get("canonical_map_path")` →
    `Fetch(static_pcd_paths=static_pcd_paths)` — `experiments/run_maniskill_benchmark.py:156-171`
11. `static_map (S): canonical world PCD, considered immutable` — `grasp_anywhere/observation/scene.py:13`
12. `dynamic_costmap: False` — `configs/real_fetch.yaml:23`；`True` — `configs/maniskill_fetch.yaml:17`

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)
与 MVE-0（失败分类协议）。结论：**不引入运行时**；采纳行为树回退、
可见性 pre-grasp 约束、碰撞归一化与先验披露要求；其“unknown static”表述
必须降级。
