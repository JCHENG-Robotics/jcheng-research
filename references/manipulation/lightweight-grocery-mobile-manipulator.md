# 轻量视觉移动机械臂的杂货拣选—装袋 — A Complete Grocery Pick-and-Pack Application Using a Computationally Lightweight Vision-Based Mobile Manipulator

- **类型**：一手论文（Sensors 2026，35 页全文）
- **访问日期**：2026-11-25
- **阅读范围**：全文 35 页；Table 1–10、Figure 1–18；§1–§5、§4 讨论。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/11_Lightweight_Mobile_Manipulator.pdf`
  （35 页，27,688,328 字节）。**未入库**：第三方出版物 + 5 MB 门禁。
- **许可**：CC BY 4.0（MDPI；Crossref 与版权页一致）。

## 来源

- Mansakul, T.; Tang, G.; Webb, P.; Rice, J.; Oakley, D.; Fowler, J.
  *A Complete Grocery Pick-and-Pack Application Using a Computationally
  Lightweight Vision-Based Mobile Manipulator*. **Sensors** 2026, 26(9), 2860.
  <https://doi.org/10.3390/s26092860>
- 投稿 2026-03-28；修回 2026-04-29；接收 2026-05-01；出版 2026-05-03。
- 代码：**无**。数据声明：**“The original contributions presented in this
  study are included in this article.”**（p.33）→ 不开放。
- 前作/benchmark：[4] Mansakul et al., **Sensors 2025, 25(17), 5309**,
  DOI 10.3390/s25175309。**“Grocery Pick-and-Pack Benchmark”是作者团队
  2025 年自订的分级，不是第三方/社区 benchmark**；Level-3 是其第三档。

## 论文声称的核心结果（作者报告值，未独立复现）

- Level-3 五类物品，**每类 5 次、共 25 次**：conditioner 5/5、sweet bag
  **3/5（60%）**、cleaner spray 5/5、Spam 5/5、tape 5/5；合计
  **23/25 = 92%**，Wilson 95% CI **75.1–97.8%**（Table 5, p.23）。
- 平均执行时间 **7.5 s**（“on an edge device”）；模型总大小 **30.9 MB**
  （YOLOv11-Nano + FastSAM-s + PCA）。
- ERL 2025 Episode 4：**17/36 分**，3/6 件交付，1 次碰撞惩罚；作者称该
  episode 第一名，但**拿不到各队分数**（p.27）。
- 跨平台：Dell G16 GPU（RTX 4060 8 GB）23.18 FPS / 6.45 W / 3.594 FPS·W⁻¹；
  Jetson Orin Nano **0.59 FPS**（CPU 路径）/ 6.56 W；XPS 13 3.61 FPS；
  G16 CPU 0.89 FPS（Table 9, p.29）。

## 方法要点

- **硬件**：MiR100 底盘 + **UR16e（6-DoF）** + Robotiq 2F-85 + **ZED 2i**
  （eye-in-hand）+ **Jetson Orin Nano 8 GB**；Jetson 与笔记本无线上联，
  与 UR16e 走有线以太网。
- **两条视觉分支**：
  - 几何分支（conditioner、sweet bag）：YOLOv11 检测 → FastSAM-s 分割
    （框中心点提示，不微调）→ 最大连通域 → PCA，v1 主轴、v2 次轴为夹爪
    闭合方向，质心为抓取点；
  - 学习分支（cleaner spray、Spam、tape）：第二级 YOLOv11 检测“可抓子
    区域”（扳机、罐沿下 1 cm、胶带环面），框中心为抓取点。
- **3D 恢复**：只在预测像素处查一个深度值，经相机内参 + 手眼变换到基座系；
  输出 `(x,y,θ)` 给 UR16e 的 RTDE，由 UR 自带 IK 执行。
- **训练**：Stage-1 YOLOv11-Nano，100 epoch，701 张/类 × 5 类 = 3505 张，
  80/10/10；Stage-2 100 epoch，225 张/3 类，90/5/5，imgsz 225。
- **成功判据**：检测分类正确、夹爪落在容差内、夹紧且运输不掉、放入指定区，
  四条全满足；人工目视判定，系统无成功检测/失败恢复。

## 批判性评估

### 样本量与统计

- **92% 只是 23/25**；四类满分项的 Wilson 下限只有 **56.6%**；去掉 sweet
  bag 后系统几乎是“全对或全错”的二值表现。n=5 无法把 92% 与 75% 区分开。
- 作者自己在 §4 写“5 次/类足以刻画运行行为，但不支持对单类成功率做形式化
  统计推断”，并建议未来 n≥10。这是诚实的自限。
- **Table 5 的 sweet bag CI 异常**：3/5 报 **23.1–88.2%**，用同一 Wilson
  公式（z=1.96）复算应为约 **31–80%**；报出值更接近 z≈2.0。不影响 92%
  的总区间，但说明区间计算未统一核验。
- **无 baseline、无消融、无检测指标**：GraspNet 只做文献引用对比
  （87.3–90.5%、7.2 MB、425 MB 内存、TX1 133 ms），作者明确写“直接比较
  不可能”。全文没有 mAP、IoU、抓取点像素误差，也没有“两阶段学习检测”
  相对“只用 PCA”的对照。92% 是一个孤立数字，无法归因到具体设计。

### 设备与能效口径

- **“7.5 s on an edge device” 的设备从未点名**。§2.8 说主设备是 Jetson
  Orin Nano；Table 7/9 的 Jetson 只有 **0.59 FPS（≈1.7 s/帧）**的 CPU
  路径。若 7.5 s 是 Jetson CPU 的结果，其中约 1.7 s 是视觉、约 5.8 s 是
  臂运动；若是 G16 GPU（23 FPS），“edge”就是错的。**这是最需要作者澄清
  的一处。**
- **Jetson 的 GPU 从未被测**：Table 6 列了 1024 CUDA 核心，但 Table 7/9
  只有一个 Jetson 列，正文又说 “CPU-only mode” 下 Jetson 最慢。所谓
  “边缘设备”结论全部来自 CPU 路径；而“GPU 加速极大提升效率”来自 140 W
  的 RTX 4060 笔记本。两件事被并列陈述，容易被误读。
- **能耗口径不一致**：G16 GPU 的 6.45 W 是 **GPU 单轨**（NVML），不含
  i7-13650HX（CPU-only 66.99 W）、内存、屏幕；Jetson 6.56 W 是
  **SoC 全轨**（INA3221）；XPS 18.90 W 是 TDP 模型估计。三者不同口径，
  却被用来算 18.8×/39.9×/276.5× 的“能效优势”。
- **Table 8 与 Table 9 自相矛盾**：按 Table 9，G16 GPU 23.18 FPS、6.45 W，
  每帧能量应为 **0.278 J**，但 Table 8 报 **0.66 J**（对应约 9.8 FPS）；
  其余三行偏差在 10% 以内，唯独 GPU 行差 2.4 倍。两表可能用了不同 FPS
  口径，论文未说明。
- **“30.9 MB 比 GraspNet 小”按字面是错的**：GraspNet 模型 **7.2 MB**，
  30.9 MB 更大；只有指其 **425 MB 总内存占用**时才成立。且 30.9 MB 没有
  分项构成（YOLOv11n/FastSAM-s 各多少、是否 fp16）。
- **CSR 一名两义**：式(1) 定义 CSR = 推理 FPS / 功率；Table 4 的 CSR 用
  1/整次拣选周期 ÷ 17 W，得到 0.007–0.009；§3.3 的 FPS 是纯推理吞吐。
  同一符号混用两个量纲，17 W 测的是什么也未说明。

### 其他

- **闭集世界**：Level-3 五类物品同时是训练集和测试对象；作者承认这是设计
  选择。Stage-2 只有 225 张，90/5/5 后测试集仅 11 张，论文从未报告这 11 张
  上的任何指标。
- **ERL 证据被硬件故障污染**：同一机器人参加其他 episode 时撞坏相机支架，
  决赛前只做快速重标定/插值，作者自述“无法完全重新对齐”。17/36 与
  “第一名”都不能当作干净的系统性能证据，且无记分板。
- **无连续耐久测试**：没有“连续抓 10 件”、遮挡/密集摆放、透明/反光、
  货架深处、动态光照、多次拣选后的漂移。
- 无代码/数据/种子/训练曲线；batch=auto、GPU 型号、训练时长未报告；
  FastSAM/ZED SDK 版本未给。

## 代码与数据

- **无代码、无数据、无权重**；复现结论：**不可复现**。
- 依赖：YOLOv11（Ultralytics，AGPL-3.0）、FastSAM、ZED SDK、UR RTDE、
  MiR API。若复用视觉前端，需处理 AGPL 与 ZED SDK 许可。

## 与 JCHENG / ArmPi Ultra 的适配

- **相机可替换**：论文用 ZED 2i，但前端只吃 RGB、深度只在单像素取值；
  作者自己点名 **D435i** 是合适替代（$200–300 vs ZED $450–500）。这与
  JCHENG 的 D435i 几乎零成本对接，只需内参与对齐深度。
- **算力**：Jetson Orin Nano CPU 路径 0.59 FPS；Pi 5（4 核 A76、无 CUDA）
  更慢，FastSAM-s 在 Pi 5 上基本不可用。现实方案：YOLOv11n 放 Pi 5，
  FastSAM/后续放 RTX 3060 6 GB；代价是感知环跨网络。
- **机械臂**：5-DoF 做“自上而下 + 绕 z 偏航”的抓取在几何上可行
  （x,y,z,θ 四个量刚好够），但没有冗余自由度做货架内伸入/避障，也没有
  腕部第二相机。论文是 eye-in-hand；ArmPi 的 D435i 通常固定在机架，
  “一张图直接出抓取点”的前提会弱化。
- **负载/尺寸**：Level-3 物品 82–481 g，ERL 需 15 cm 夹持宽度；ArmPi 的
  5-DoF 总线舵机臂与夹爪在这两项上偏紧（额定值未在本仓库文档中给出，
  须实测）。甜袋“低摩擦+可变形”正是论文自己都没解决的失败模式。
- **运动接口**：论文直接下发笛卡尔路点给 UR16e RTDE；JCHENG 必须经
  `ExecuteMotion`，并加限位、lease、deadman、stop latch。论文的“让机器人
  走到预测点、量偏差”标定流程属于真实运动，必须逐次操作员授权。
- **安全**：成功判据完全依赖人工目视，系统不知道抓没抓住；无编码器/
  无 e-stop 的 ArmPi 上这一缺陷会被放大。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | RGB-only + 单像素深度查询，避免稠密点云 | B（工程成立，D435i 可替换，无消融） | **采纳**为轻量抓取管线形态 |
| 2 | 几何物体用 PCA 质心+次轴；特定抓取点用部件检测 | B（分支配设计合理，无消融） | **采纳**为先 PCA、再逐步加学习分支 |
| 3 | Wilson 区间 + 明确成功判据写进报告 | B（方法学） | **采纳**为小样本报告格式 |
| 4 | 92%（23/25）、7.5 s、30.9 MB 作为性能证据 | A（数字）+ C（设备未点名/无 baseline） | **不采纳**为选型依据 |
| 5 | CSR/ηE/ηC 跨设备能效排名 | D（功率口径不一致、两表矛盾） | **不采纳**其倍数结论 |
| 6 | ERL 17/36 与“第一名”作为外部验证 | D（单次事件、相机损坏、无记分板） | **不采纳**，只作轶事 |
| 7 | “Grocery Pick-and-Pack Benchmark”是作者自订分级 | A（前作同作者 + 无独立规范页） | **不采纳**为社区 benchmark |
| 8 | 30.9 MB 小于 GraspNet 的表述 | A（GraspNet 模型 7.2 MB） | 纠正：只能在“总内存 425 MB”语境下成立 |

## 核验片段

1. “an average success rate of 92% across five item classes, with the deformable sweet bag the most challenging at 60%” — Abstract, p.1
2. “an average execution time of 7.5 s on an edge device” — Abstract, p.1
3. “All items 23/25 92 75.1%, 97.8%” — Table 5, p.23
4. “Sweet bag 3/5 60 23.1%, 88.2%” — Table 5, p.23
5. “GraspNet … compact model size of 7.2 MB, a total memory footprint of 425 MB” — §3.1, p.23
6. “the overall model size (30.9 MB) remains smaller than that of GraspNet” — §3.1, p.23
7. “A total of 225 images were collected across the three classes” — §2.5.1, p.11
8. “Dataset split: 90% training, 5% validation, 5% test” — §2.5.1, p.12
9. “The Level 3 benchmark in this paper uses 5 trials per item (25 in total)” — §4, p.31
10. “the Jetson Orin Nano demonstrated the lowest absolute power consumption (6.56 W on average)” — §3.3, p.29
11. “G16 GPU 23.18 6.45 3.594” — Table 9, p.29
12. “G16 GPU 6.45 11.07 0.66” — Table 8, p.29（与 Table 9 的 0.278 J/帧 不一致）
13. “We do not have access to the full per-team scoring breakdown” — §3.2, p.27

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)。
结论：**不引入运行时**；RGB-only 前端、单像素深度、PCA 抓取点与 Wilson
区间报告法可借鉴；其能效排名与 ERL 名次不采纳。
