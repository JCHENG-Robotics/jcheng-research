# 输送带煤矸石的动态视觉定位 — A dynamic visual localization method for intelligent coal gangue sorting robots

- **类型**：一手论文（Scientific Reports 2026，13 页全文）
- **访问日期**：2026-11-25
- **阅读范围**：全文 13 页；Table 1–5、Figure 1–9、Eq.(1)–(14)。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/03_Dynamic_Visual_Localization.pdf`
  （13 页，3,423,072 字节）。**未入库**：第三方出版物；本仓库 5 MB 门禁。
- **许可**：CC BY 4.0（Scientific Reports 版权页）。

## 来源

- Ye, Z.; Bohao, C.; Peng, W.; Yuanhao, Z.; Kexiang, M.; Hongwei, M.; Xudong, W.;
  Jiahui, L. *A dynamic visual localization method for intelligent coal gangue
  sorting robots*. **Scientific Reports** 2026, 16, 38110.
  <https://doi.org/10.1038/s41598-026-71502-5>
- 收稿 2026-07-12；接收 2026-09-09；在线 2026-09-24。
- 代码：无仓库、无项目页。数据：**“available from the corresponding author
  upon reasonable request”**（p.11）。

## 论文声称的核心结果（作者报告值，未独立复现）

- 312 条视频、34,860 帧、52 个标注煤矸石目标；按序列划分训练/测试。
- 带速 0.7–1.0 m/s、距离 70 cm：平均定位误差 **δx=1.8 mm、δy=1.7 mm**，
  Pr≈84.6%、Cr>98%，**约 58 FPS**（Table 2, p.8）。
- 距离 40–70 cm：δx=1.8 mm、δy=1.9 mm（Table 3, p.9）。
- 视觉退化补偿（530 帧）：Pr 82→**85%**、Cr 96→**98.4%**，误差
  2.1/2.2→**1.7/1.8 mm**（Table 4, p.10）。
- 消融：SiamDW 82.5/96.7/63 → +ECA 83.4/97.2/64 → +多尺度 84.5/97.8/60 →
  SiamCSF **85.2/98.6/58**（Pr/Cr/FPS，Table 5, p.11）。

## 方法要点

- **SiamCSF**：SiamDW/CIResNet22 backbone；Conv3 阶段插入 ECA 通道注意力；
  融合 Conv1/Conv2/Conv3 多尺度特征。
- **置信度门控**：APCE（平均峰值相关能量）连续 3 帧平均，阈值
  `T = K × 历史平均 APCE`，K=0.4；低于阈值时用**编码器位移**沿输送方向
  补偿：`x_code(t)=x_vis(t−1)+v·Δt`，横向 `y` 保留上次视觉值。
- 输入模板 127×127、搜索区 255×255；输出目标框/中心，经 hand-eye 与机械臂
  位姿变换到基座系。
- 对比：SiamDW、SiamMask、SiamRPN、SiamFC；统一 OPE 协议，首帧 GT 初始化，
  后续不重初始化。

## 批判性评估

### 动机—实验不匹配（最重要）

引言把**带速波动、打滑、跑偏、振动**列为核心问题，但实验只做了四种**恒定**
带速、四种**恒定**距离；没有变速序列、没有打滑、没有跑偏、没有振动注入，
也没有测量带速估计误差。补偿触发条件是“视觉特征退化”，不是“皮带打滑”。
论文没有证据证明它能处理自己声称的四类扰动。

### 1.7/1.8 mm 的测量条件不成立或未报告

- 误差是图像坐标经内参、hand-eye、机械臂位姿变换后的 `|x_g−x_r|`；但
  ground truth 如何获得完全未报告（编码器+人工标定？停带静态测量？外部
  跟踪仪？）。
- 1 m/s、58 FPS 下目标每帧移动约 17 mm；若时间戳错 1 帧就是 17 mm，远大于
  1.7 mm。论文未报告曝光/时间戳同步、hand-eye 标定残差、机械臂重复定位精度。
  1.7 mm 更可能是**标定残差主导的静态/准静态精度**，而不是动态跟踪精度。
- **摘要选择性引用**：摘要的 1.7/1.8 mm 来自 Table 4 的补偿子集；主速度实验
  Table 2 是 1.8/1.7，1.0 m/s 行为 1.9/2.0；结论段又写 1.8/1.7。

### 指标自相矛盾

Pr≈85% 意味着约 15% 的帧中心误差 >20 px；Cr 却 >98% 的帧两轴都 ≤10 mm。
若 20 px 对应的物理尺寸大于 10 mm，则“>20 px 失败”的帧不可能同时“≤10 mm
成功”；若小于 10 mm，则两个指标测的不是同一件事。论文未说明分母/成功帧
筛选规则。

### 统计与基线

- 无种子数、重复次数、均值±方差、置信区间、显著性检验；所有表格是单次
  点估计。Table 5 中 +ECA 的 FPS=64 **高于** SiamDW 的 63，已暴露计时噪声。
- 测试帧数小：速度实验合计 2,158 帧，100 条序列平均约 21.6 帧/条（约 0.37 s）；
  距离实验合计 2,172 帧。只能覆盖短时窗口，不能证明长时漂移/遮挡恢复。
- 312 条序列、52 个目标，平均每目标 6 条；按序列随机划分可能让同一目标的
  序列同时进训练/测试（目标级泄漏），论文只说“by sequence”。
- 基线是 2016–2019 的 Siamese 系列，没有 OSTrack/MixFormer/TransT 等现代
  跟踪器；四个 baseline 是否在同一煤矸石训练集上训练/调参未报告。
- 没有与“仅视觉 + 匀速/Kalman 外推”对比，补偿的 +3 pp 无法归因于编码器。

### 其他

- 无真实抓取实验；标题是分拣机器人，但只测定位，没有抓取成功率/节拍/
  空抓漏抓统计。“满足动态抓取要求”是从 ±10 mm 容差推出来的。
- p10 页边有 “AQ1” 作者查询标记，Table 1 的 “32×22” 与 255/8=32 不符，
  说明 PDF 可能不是最终清稿。

## 代码与数据

- 无代码、无公开数据、无预训练权重、无标定参数。复现风险：**高**。

## 与 JCHENG / ArmPi Ultra 的适配

- **平台冲突（硬阻断）**：JCHENG 没有皮带/龙门架/编码器；论文的“动态”来自
  输送带，ArmPi 的目标通常在桌面静态。编码器补偿在无编码器平台上无法直接
  复用；若把 `v` 换成视觉速度，需重新验证打滑/漂移。
- **精度不可迁移**：5-DoF 总线舵机无编码器，`/joint_states` 是命令缓存；
  hand-eye 残差与舵机重复定位精度很可能远大于 1.7 mm。
- **算力**：58 FPS 的测量硬件未报告；SiamCSF（255×255、CIResNet22）在
  RTX 3060 6 GB 上跑 58 FPS 可能，但 D435i 通常 30 FPS，系统被相机帧率
  限制；Pi 5 CPU 推理大概率远低于 58 FPS（未实测）。
- **可借鉴**：APCE 置信度门控 + 短期外推的分层结构，可映射为
  “perception 发布目标位姿 + 置信度，system 层低置信度限幅/停止”。跟踪器
  只能发布意图，不能直接驱动舵机。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | 编码器位移补偿依赖本平台不存在的传感器 | A（方法 Eq.10 + 平台事实） | **不采纳** |
| 2 | 1.7/1.8 mm、58 FPS 的测量条件未报告，摘要选择性引用补偿子集 | A（Table 2 vs Table 4）+ C（推断） | **不采纳**为选型依据 |
| 3 | 动机中的打滑/跑偏/振动没有被实验覆盖 | A（实验设计） | **不采纳**其鲁棒性主张 |
| 4 | APCE 置信度门控 + 短期外推的结构可借鉴 | B（方法 + 有限数据） | **仅借鉴**，需换成视觉速度并重测 |
| 5 | 定位指标之外必须做抓取闭环 | A（论文缺口） | **采纳**为 JCHENG 验收原则 |
| 6 | 报告标定残差、时间同步与 GT 获取方式 | A（精度可复核的前提） | **采纳**为实验规范 |

## 核验片段

1. “localization frame rate of about 58 FPS, with average localization errors of approximately 1.7 mm and 1.8 mm” — Abstract, p.1
2. “The dataset contains 312 video sequences, comprising 34,860 frames and 52 annotated coal gangue targets.” — p.6
3. “the average position errors in the X and Y directions are 1.8 mm and 1.7 mm” — p.7
4. “When both δx and δy are less than 10 mm, the localization of the frame is considered correct.” — p.7
5. “Compared with visual tracking only, the proposed compensation strategy increases Pr from 82 to 85% and Cr from 96 to 98.4%” — p.10
6. “the APCE values of three consecutive frames (N = 3) are averaged … K = 0.4” — p.9
7. “SiamDW 82.5 96.7 63；SiamDW + ECA 83.4 97.2 64” — Table 5, p.11
8. “all trackers were evaluated using the same test sequences and initialized with the ground-truth target bounding box in the first frame” — p.10
9. “The data supporting the findings of this study are available from the corresponding author upon reasonable request.” — p.11

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)。
结论：**不引入运行时**；只借鉴“置信度门控 + 短期外推”的结构，且必须由
system 层兜底。
