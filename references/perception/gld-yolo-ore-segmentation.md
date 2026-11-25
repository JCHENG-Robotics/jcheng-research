# 井下矿块实例分割 — GLD-YOLO: An Ore Instance Segmentation Algorithm for Underground Crushing Scenes

- **类型**：一手论文（Machines 2026，23 页全文）
- **访问日期**：2026-11-25
- **阅读范围**：全文 23 页；Table 1–8、Figure 1–8、Eq.(1)–(13)；逐页回读
  p.15（Table 2）、p.16（Table 3）、p.18–19（Table 4–8）。未获取补充材料。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/04_GLD_YOLO.pdf`
  （23 页，6,095,034 字节）。**未入库**：第三方出版物 + 5 MB 门禁。
- **许可**：CC BY 4.0（MDPI）。注意：方法基于 **Ultralytics YOLO11-seg**，
  上游代码为 **AGPL-3.0**；论文本身的 CC BY 不改变上游许可。

## 来源

- Chen, M.; Liu, Y.; Si, L.; Wang, X.; Gu, J. *GLD-YOLO: An Ore Instance
  Segmentation Algorithm for Underground Crushing Scenes*. **Machines** 2026,
  14(7), 731. <https://doi.org/10.3390/machines14070731>
- 投稿 2026-05-19；修回 2026-06-17；接收 2026-06-25；出版 2026-06-29。
- 代码/数据：**“Data are contained within the article; the code is
  confidential.”**（p.21）。GitHub API 检索 `GLD-YOLO` 返回 0 条（2026-11-25）。

## 论文声称的核心结果（作者报告值，未独立复现）

- 自建矿块数据集 2100 张（自采 1900 + 公开选 200），21,420 个实例，
  随机 8:1:1 → 1680/210/210。
- Table 2：GLD-YOLO **mAP50 98.1、mAP50-95 82.3**；YOLO11n-seg **93.7/77.2**；
  提升 **+4.4/+5.1 pp**。Params 3.52 M、GFLOPs 16.1、**90 FPS**（RTX 5070，
  Windows 11，batch=1，含预处理/前向/NMS）。
- Table 3 消融（本评审按原页核对）：baseline 93.7/77.2；C3k2_GBC 单独
  96.0/78.8；C2PSA_LRSA 单独 95.1/78.0；PAFPN_DDFE 单独 96.4/79.5；
  Focaler 单独 94.4/77.7；C3k2+C2PSA 96.2/79.7；C3k2+PAFPN 96.3/80.1；
  三模块（无 Focaler）96.7/80.8；四模块全开 **98.1/82.3**。**全模块行与
  Table 2 一致**，不存在“全模块 96.7 vs 主表 98.1”的矛盾。
- 泛化：MineralImage5k mAP50 **83.0** vs YOLO11n 81.1（+1.9）；
  Crack-seg **86.4** vs 84.3（+2.1）（Table 8, p.19）。

## 方法要点

- **骨干**：C3k2_GBC（Gated Bottleneck Convolution，双分支门控 + GroupNorm）
  + C2PSA_LRSA（重叠切块局部自注意力 + ConvFFN）。
- **颈部**：PAFPN_DDFE，引入 P2/P3 浅层；DDFE 含 EDLKC（可变形大核卷积）、
  WTConv（小波频域重标定）、空间-频域双向 cross-attention、SPD 下采样。
- **损失**：Focaler-Shape-IoU（Focaler 重映射 d=0、u=0.95 + Shape-IoU）。
- **训练**：Windows 11、i5-14600KF、**RTX 5070**、PyTorch 2.7.0/CUDA 12.8；
  SGD、300 epochs、batch 16、640×640、depth/width 0.25；**全部从零训练，
  无预训练权重**；取验证集最优权重，再在独立测试集评估。

## 批判性评估

### 消融表：先纠正一个误读，再记录真实问题

- **不存在“全模块行无勾选/96.7 vs 98.1”的矛盾。** 原页 p.16 显示：三模块
  行（C3k2+C2PSA+PAFPN，无 Focaler）为 96.7/80.8；四模块全开行为
  98.1/82.3。把三模块行误读为“全模块”会得出错误指控。
- **真实问题是跨表不一致**：同一模块单独启用时，Table 3 与 Table 4/5/6/7
  的数值有小幅差异：
  - C3k2_GBC：Table 3 96.0/78.8 vs Table 4 95.5/78.7；
  - C2PSA_LRSA：Table 3 95.1/78.0 vs Table 5 95.1/78.5；
  - PAFPN_DDFE：Table 3 96.4/79.5 vs Table 6 96.7/80.6；
  - Focaler：Table 3 94.4/77.7 vs Table 7 95.3/78.2。
  差异 0.3–1.1 pp，未解释（不同随机种子？不同 run？）。这不推翻主结论，
  但说明“单模块增益”不能精确重建。

### 数据集与统计

- **单一场景、单类别、固定相机/光照**：98.1% mask mAP50 是**同分布内插**的
  结果；全体 baseline 也异常高（Mask-RCNN 88.4、RF-DETR 94.5、YOLO13n 93.1），
  说明数据集偏易。论文把高绝对值当作“井下复杂工况”的能力证据，动机与
  验证之间有落差。
- **泄漏风险（推断，未证明）**：1900 张来自连续破碎实验，随机 8:1:1 很可能
  让相邻帧同时进训练/测试；论文未按拍摄批次/时间去重，未做重复图检测。
  这是 98.1% 最合理的替代解释之一。
- **无种子/重复/方差/显著性检验**：每个配置单一结果；+0.3–0.6 pp 的消融
  差异可能落在单次训练波动内。
- **从零训练 ≠ 公平**：对 Mask-RCNN、SOLOv2、FastInst、RF-DETR 这类依赖
  预训练/长 schedule 的模型，300 epoch、SGD、1680 张图是明显不足的配方；
  对 YOLO11 轻量模型则是标准配方。领先幅度可能被系统性放大。
- **“90 FPS”语境**：RTX 5070 桌面卡 + Windows 11 + batch=1，不是边缘设备；
  相对 YOLO11n 的 120 FPS 下降 25%，GFLOPs +55%。不能外推到 RTX 3060
  Laptop 6 GB，更不能外推到 Pi 5。

### 泛化实验的证据链

- **MineralImage5k 的原始定位是“零样本矿物视觉识别与描述”基准**（Nesteruk
  et al., Computers & Geosciences 2023, 178, 105414,
  DOI 10.1016/j.cageo.2023.105414），其分割子集约 **100 张**；本文称
  该数据集有 5341 张、3 万余实例标注并报告 mask AP，**与原始基准描述不一致**。
  掩码从何而来、是否重训、训练/测试划分均未报告。→ 这两列数字应降为
  “未验证”。
- Crack-seg 源自裂缝**语义分割**工作，转为**实例**分割 AP 同样缺少说明。
- 两数据集相对 YOLO11n 的增益仅 +1.9/+2.1 mAP50，且无方差，无法判断显著。

### 其他

- Focaler 的 d/u=0、0.95 是经验设定，无敏感性分析；u=0.95 会截断高 IoU
  样本梯度。
- 无失败案例定量统计、无按尺寸/遮挡分层的误差分析、无低照度/粉尘退化曲线。
- 代码保密使四个自定义模块（GBC、LRSA、DDFE/EDLKC/WTConv、Focaler-Shape-IoU）
  的实现细节永久不可得；只有公式与框图，无法对齐数字。

## 代码与数据

- **无代码、无独立数据下载、无权重**；复现结论：**不可复现**。
- 若要复用，只能按 Eq.(1)–(9) 重写并重新调参；届时 98.1/82.3 不能作为
  对照数字。

## 与 JCHENG / ArmPi Ultra 的适配

- **任务相关性有限**：JCHENG 当前瓶颈不在“矿块分割”，而在位姿估计与执行；
  现有 YOLO 检测 + 深度反投影已能给抓取点。实例 mask 对“粘连物体分离”
  有潜在价值，但收益未验证。
- **算力**：3.52 M/16.1 GFLOPs 的实例分割在 RTX 3060 6 GB 上预计 35–55 FPS
  @640（C 级推断，未实测）；Pi 5 CPU 上预计 1–3 FPS，无法闭环。只能放
  3060 侧，走“感知 GPU 节点 → 域 42 → 系统层”的既有通路。
- **许可**：基于 Ultralytics YOLO11-seg（AGPL-3.0）。JCHENG 多数仓库目前
  无 LICENSE（许可评审未结）；把 AGPL 代码/衍生模块并入会造成许可污染。
  任何复用前必须做许可评审，或改用 Apache/MIT 授权的替代骨干。
- **可借鉴的低成本零件**：Focaler-IoU 难样本重加权（十余行）、P2/P3 浅层
  注入（小目标/细边界）、GroupNorm（小 batch）。这些可在自有检测器上做
  A/B，不必复现整篇。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | Table 3 全模块行与 Table 2 一致；不存在“全模块 96.7”矛盾 | A（原页 p.16 核对） | 纠正误读，不引用该指控 |
| 2 | 跨表单模块数值有 0.3–1.1 pp 不一致，未解释 | A（Table 3–7） | **仅借鉴**相对趋势，不引用精确增益 |
| 3 | 98.1% 是单场景/单类别/随机帧划分下的结果，不能外推 | B（数据集描述 + 泄漏推断） | **不采纳**绝对值 |
| 4 | 从零训练对重模型不公平，领先幅度被放大 | B（配方对比） | 自行复现时给足预训练/schedule |
| 5 | Focaler-IoU + P2/P3 注入是低成本可插拔改进 | A（架构）+ C（对本平台收益未知） | **仅借鉴**，先做 A/B |
| 6 | MineralImage5k/Crack-seg 的 mask AP 证据链不成立 | B（原始基准描述 + 缺失协议） | **不采纳**为泛化证据 |
| 7 | 90 FPS 不能外推到 3060/Pi 5 | C（算力推断） | **不采纳**，须自行测 |
| 8 | 代码保密 + Ultralytics AGPL-3.0 | A（声明/上游许可） | **不采纳**运行时；复用前许可评审 |

## 核验片段

1. “improves the mAP50 and mAP50-95 metrics by 4.4% and 5.1%, respectively” — Abstract, p.1
2. “GLD-YOLO 95.9 95.6 98.1 82.3 3.52 16.1 90” — Table 2, p.15
3. “an NVIDIA GeForce RTX 5070 GPU” — §3.4, p.14
4. “1900 ore images … 1680 training images, 210 validation images, and 210 test images” — §3.2, p.13
5. “C3k2_GBC 93.8 93.4 96.0 78.8” — Table 3, p.16
6. “C3k2+C2PSA+PAFPN（无 Focaler）95.3 94.7 96.7 80.8；四模块 95.9 95.6 98.1 82.3” — Table 3, p.16
7. “all networks are trained from scratch without any pre-trained weights” — §3.4, p.14
8. “the model weights that achieve the highest accuracy on the validation set during 300 training epochs” — §3.4, p.14
9. “constitutes 5341 high-resolution images with over 30,000 instance annotations” — §3.2, p.13
10. “Data are contained within the article; the code is confidential.” — p.21
11. “has not yet been field-tested in a real mine environment” — Conclusions, p.21

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)。
结论：**不引入运行时**；只把 Focaler-IoU/P2-P3 注入列为可选的低成本 A/B，
且先过许可评审。记录同时纠正了“消融表全模块行矛盾”的误读，避免把排版
错位当成学术问题。
