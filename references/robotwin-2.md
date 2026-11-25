# RoboTwin 2.0 — 基准与数据生成器

- **类型**：同行评审基准论文 + 官方仓库 + 数据集
- **访问日期**：2026-11-25
- **阅读范围**：arXiv 摘要与 **HTML 正文**（协议与局限章节）；官方项目页与数据集
  清单通过检索结果核对；**未通读 PDF 全文**。下文协议/局限类结论对论文自述为
  A 级；来自检索结果的数据集计数为 B 级。

## 论文

- Chen, Chen, Chen 等。*RoboTwin 2.0: A Scalable Data Generator and Benchmark
  with Strong Domain Randomization for Robust Bimanual Robotic Manipulation*。
  arXiv:2506.18088，2025-06-22 提交；项目文档称已被 ICML 2026 接收。
  <https://arxiv.org/abs/2506.18088>
- 50 个双臂任务，覆盖 5 种本体（Aloha-AgileX、ARX-X5、Franka、Piper、UR5）；
  SAPIEN 物理引擎；RoboTwin-OD 物体库（731 个实例 / 147 类）；超过 100,000 条
  域随机化专家轨迹。
- 五条结构化域随机化轴：杂物、光照、背景、桌面高度、语言指令。桌面高度变化
  最多 3 cm；随机相机位姿扰动上限 1 cm。
- 评测协议："50 clean expert demonstrations per task are used for training"；
  "100 rollouts under two conditions: Easy (clean) and Hard"（randomized）。
  `demo_clean` = easy，`demo_randomized` = hard。
- 论文报告：RDT 从 clean 到 randomized 下降 20.8 个百分点，Pi0 下降 30.1 个
  百分点——这个缺口是基准层面的，不是 SST 独有。
- 与替代路线相关的作者自述局限："DP3's strong results partly stem from perfect
  point clouds and clean background segmentation in simulation." 这是把
  DP3 类 3D 策略迁移到真实噪声深度时的重要警示。

## 仓库与数据集

- <https://github.com/RoboTwin-Platform/RoboTwin>
- 项目页：<https://robotwin-platform.github.io/>
- 物体/数据：<https://huggingface.co/datasets/TianxingChen/RoboTwin2.0>；
  LeRobot v3.0 统一数据集为 `lerobot/robotwin_unified`（约 79.6 GB，
  Apache-2.0，据检索摘要）。
- SST 使用 2,500 episodes（50 任务 × 50 clean 演示）、548,893 帧、每 episode
  100 条 seen instruction。

## 为什么这对 SST 结果重要

`demo_randomized` 由**强**域随机化在五个轴上生成。一个只在 clean 数据上训练的
策略在这里被测试，面对的是基准**刻意放大**的合成外观偏移。这使 RoboTwin 成为
一个好的压力测试，但对真实相机鲁棒性的预测力很弱：偏移是合成的，物体集是封闭的
（147 类），指令来自固定的 seen pool。

## 对 JCHENG 的相关性

RoboTwin 是双臂 ALOHA 风格基准；ArmPi Ultra 是 5-DoF 单臂 + 夹爪。它不能作为
JCHENG 的目标任务集，成功率也不可迁移。它只适合作为**机制**（外观偏移 vs 输入
条件）的受控试验台。
