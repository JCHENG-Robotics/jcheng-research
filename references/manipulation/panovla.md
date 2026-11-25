# PanoVLA — 全景感知的移动双臂 VLA 与全身遥操作

- **类型**：一手论文（arXiv 预印本，8 页全文）
- **访问日期**：2026-11-25
- **阅读范围**：全文 8 页；§I–§VI、Eq.(1)–(5)、Table I–III、Figure 1–4；
  双栏串行处已按页回读。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/08_PanoVLA.pdf`
  （8 页，8,142,289 字节）。**未入库**：第三方预印本 + 5 MB 门禁。
- **许可**：PDF 未声明 CC；arXiv 页面为默认 arXiv 许可（非 CC BY）。

## 来源

- Yang, D.; Chen, H.; Chen, X.; Liu, L.; Li, M.; Tu, C.; Xu, K.; Ma, X.; Liu, S.
  *Learning Panorama-Aware VLA for Mobile Manipulation with Whole-Body
  Teleoperation*. arXiv:2608.02257v1 [cs.RO], 2026-08-03.
  <https://arxiv.org/abs/2608.02257>
- 无期刊/会议信息、无项目页、无数据可用性声明。
- 代码：GitHub 检索到 `puffyyy/panovla`（Apache-2.0，created 2026-11-24），
  但 **tree 为空（0 files）、无 README**；等同未发布。另有
  `puffyyy/panovla.github.io`（项目页仓库）。
- 数据集/权重：未发布。

## 论文声称的核心结果（作者报告值，未独立复现）

- 真实机器人数据：4 个任务 × 200 条 = **800 条**，5.5 小时、约 50 万同步帧，
  25 Hz；机器人 RANGER MINI 3 底盘 + 2× Agilex PIPER 6-DoF 臂 + 双夹爪 +
  顶部 360° 相机 + 3 路局部 RGB。
- 4 个真实任务，每方法每任务 **15 次**闭环试验：
  PanoVLA **SCR 91.3% / SR 73.4%**；π0.5 **58.6% / 30.0%**；
  π0.5 w/ Pano **80.8% / 56.7%**；π0.5 w/ Stacked Pano **70.4% / 38.3%**
  （Table II）。
- 消融（仅 Move Pen，15 次/变体）：全景专家 50M **84.4/60.0**、
  100M **95.6/86.7**、200M **93.3/86.7**、300M **91.1/73.3**；
  编码器换 SigLIP **75.6/40.0**（Table III）。
- 训练：4× NVIDIA A100，bf16，30K steps，batch 64/卡；推理单张
  RTX 4090；Gemma-2B 语言主干与 MTPano 冻结，100M 全景专家可训练。

## 方法要点

- **遥操作**：VR 头显 + 双手控制器 + 3 个身体追踪器；SMPL 重建骨盆/双脚/
  双手位姿，重定向为底盘 3-DoF + 双臂 14 维 + 夹爪；底盘建模为“平面虚拟
  浮动基座”，按代价在 spin/ackermann/对角平移间切换。
- **数据**：每条含 ERP 全景、前视/双腕 RGB、本体状态、全身动作，共享时间戳；
  动作 `a_t∈R^17` = 14 维双臂关节/夹爪 + 3 维底盘速度。
- **模型**：π0.5 双专家主干 + 第三个全景专家；MTPano 编码 ERP（双鱼眼 →
  球面重投影 → ERP → 分割/深度中间特征拼接 → 池化 → MLP 适配）；
  三专家 block-wise 因果掩码联合自注意力；条件 flow matching 输出 32 步
  chunk（25 Hz 下约 1.28 s 开环）。
- **每任务独立微调**：不是单一多任务通才策略；91.3% 是 4 个模型的平均。

## 批判性评估

- **容量/预训练混淆**：PanoVLA = π0.5 + 100M 可训练专家 + 冻结的 MTPano
  （大规模全景稠密预测预训练）。没有“容量匹配但喂局部视图/打乱全景 token”
  的对照，因此“提升来自全景几何”与“提升来自更多参数/更强预训练”不可分离。
  Table III 只排除了编码器选择一个因子。
- **不是通才模型**：4 个任务各自微调；标题/摘要读起来像一个统一策略。
- **baseline 家族过窄**：只与 π0.5 三个变体比，未与 §II 引用的 MoManipVLA、
  SG-VLA、AC-DiT 等移动操作 VLA 比。“substantially outperforming local-view
  baselines”成立，“SOTA”不成立。
- **统计功效不足**：n=15/任务；单任务 CI 很宽（46.7% 的 Wilson 区间约
  25–70%）。按每方法 60 次汇总，73.3% vs 最强 baseline 56.7% 的 z≈1.91、
  p≈0.056（本评审计算），α=0.05 下不显著；逐试次数据未公开，无法做配对检验。
- **消融只在 Move Pen**：而 Move Pen 恰好是 π0.5 w/ Pano 已打平的任务
  （95.6/86.7 vs 95.6/86.7），“100M 最优”的规律只有一个任务、15 次支撑。
- **无导航/安全指标**：没有碰撞、路径长度、底盘速度/加速度、急停/人工干预；
  学习策略直接输出 (vx,vy,ω)，无速度限幅/安全层。32 步开环约 1.28 s。
- **全景相机规格缺失**：只写 “Insta X5 360 Camera”，无分辨率、帧率、ERP
  尺寸、token 数、拼接延迟。
- **SCR 分母不透明**：只有 Wipe Table 的 4 阶段可从图 4 读出；其余任务阶段数
  与“适用阶段”判定未报告，SCR 不可跨论文比较。
- **示教选择偏置**：只保留 800 条“successful”轨迹，丢弃率未报告；评测与
  训练同实验室、同物体、同房间，无新物体/新房间/跨任务迁移。
- **无代码/数据/权重**：完全不可复现；连项目页都没有。

## 代码与数据

- 代码仓库为空（`puffyyy/panovla`），无 README、无模型、无数据。
- 复现结论：**不可复现**；要从零实现 π0.5 + MTPano + 第三专家，并自采
  5.5 小时全身遥操作数据。

## 与 JCHENG / ArmPi Ultra 的适配

- **硬件结构性不匹配**：需要轮式双臂（2×6-DoF）+ 双夹爪 + 顶部 360° 相机 +
  3 路局部 RGB。JCHENG 是单条 5-DoF 臂 + 1 夹爪 + D435i + 未接入的 2D LiDAR，
  无全景、无底盘协同。17 维全身动作、底盘-臂耦合无对应物。
- **算力**：Gemma-2B（bf16≈4 GB）+ SigLIP + 动作专家 + 100M 全景专家 +
  MTPano，权重已约 6–8 GB；加 KV cache/32 步 chunk，RTX 3060 6 GB 在 bf16
  下**大概率不足**（C 级推断，MTPano 规模未知）；Pi 5 完全不可能。
- **安全**：SR 73.4%（最差任务 46.7%），无速度限幅/碰撞检测/急停；在无
  e-stop、无编码器的平台上让学习策略直接驱动底盘与臂不可接受。
- **可借鉴**：① “全景输入必须用专用全景编码器，不能直接丢给透视预训练
  编码器”的设计约束（若未来加 360 相机）；② 4 任务 800 条/5.5 h 的数据
  预算量级；③ 单次不中断 rollout、失败不复位、SR + 分阶段 SCR 双指标的
  评测协议。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | 专用全景编码器显著优于透视编码器（同架构、同容量） | B（仅 Move Pen、15 次） | **采纳**为设计约束（若加全景） |
| 2 | 仅把 ERP 当额外图像塞进 VLM，收益远小于专用专家 | B（四任务表 II） | **采纳**为设计原则 |
| 3 | 全身遥操作 + 平面虚拟浮动基座可采协调底盘/双臂示教 | B（800 条数据存在但未公开） | **仅借鉴** |
| 4 | 4 任务 800 条/5.5 h 足以让 π0.5 级模型达到 73.4% SR | B（单实验室、同物体） | **仅借鉴**为数据预算 |
| 5 | 100M 是全景专家最优规模 | C（单任务、15 次） | **不采纳**为规律 |
| 6 | 移动操作 VLA 需要 12 GB 以上显存闭环 | C（参数估算，未实测） | **待验证**；6 GB 先做沙箱 |
| 7 | 学习策略直接输出底盘速度可安全运行 | D（无安全指标） | **不采纳** |
| 8 | 代码/数据/权重已发布 | A（仓库为空/无声明） | **不采纳**为可复现证据 |

## 核验片段

1. “an average stage completion rate of 91.3% and an end-to-end success rate of 73.4%” — Abstract, p.1
2. “The collected dataset contains 800 successful teleoperated trajectories” — §I, p.2
3. “we collect 200 demonstration trajectories for each of the four real-world mobile manipulation tasks” — §III.B, p.3
4. “Each trajectory lasts about 20–30 seconds and is recorded at 25 Hz, yielding roughly 500k synchronized frames.” — §III.B, p.3
5. “evaluate each method with 15 closed-loop real-robot trials per task” — §V.A, p.5
6. “we freeze the language model and the pretrained MTPano encoder and optimize the remaining modules” — §V.A, p.6
7. “augments the policy with a pretrained MTPano encoder and a 100M-parameter panorama expert” — §V.A, p.6
8. “Training is performed in bfloat16 precision on four NVIDIA A100 GPUs with a per-GPU batch size of 64.” — §V.A, p.6
9. “the policy runs in closed loop on a single NVIDIA RTX 4090 GPU” — §V.A, p.6
10. “We conduct all ablation studies on the Move Pen task, evaluating each variant over 15 closed-loop real-robot trials.” — §V.C, p.7
11. “scaling beyond 100M parameters does not lead to consistent closed-loop improvements” — §V.C, p.7

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)。
结论：**不引入运行时**；只把“专用全景编码器”“数据预算”“SR+SCR 评测协议”
作为设计参考。论文本身不可复现。
