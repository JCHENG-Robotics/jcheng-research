# 煤矸石抓取的有界残差精化 — Sensor-Guided Intelligent Strategy Optimization for Robot-Assisted Grasping in Complex Coal Gangue Environments

- **类型**：一手论文（Sensors 2026，25 页全文）
- **访问日期**：2026-11-25
- **阅读范围**：全文 25 页；Table 1–5（p.6/8/15/16/20）、Figure 1–9；
  §3.1–3.2 Eq.(1)–(10)、§4.1–4.6、参考文献 30 条。未获取补充材料（论文未提供）。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/01_Coal_Gangue_Grasping.pdf`
  （25 页，11,861,337 字节）。**未入库**：超过本仓库 5 MB 门禁，且为第三方出版物。
- **许可**：CC BY 4.0（MDPI；Crossref 与版权页一致）。

## 来源

- Wang, H.; Wu, G.; Yang, Q.; Yang, J. *Sensor-Guided Intelligent Strategy
  Optimization for Robot-Assisted Grasping in Complex Coal Gangue Environments*.
  **Sensors** 2026, 26(22), 7230. <https://doi.org/10.3390/s26227230>
- 投稿 2026-10-09；修回 2026-11-11；接收 2026-11-12；出版 2026-11-16。
- 代码/项目页：无。GitHub API 检索 `coal gangue grasp` 无方法代码
  （2026-11-25）。数据声明：**“available on request from the corresponding
  author”**（p.24）。
- MDPI 落地页对自动抓取返回 403（Cloudflare）；DOI 解析 302 至
  `mdpi.com/1424-8220/26/22/7230`，Crossref 元数据已核对。

## 论文声称的核心结果（作者报告值，未独立复现）

- MuJoCo 仿真，**2000 次/方法**（5 个评测种子 × 20 个摆放 × 20 次尝试）：
  Full Model **98.0%（1960/2000）**；Baseline PPO **97.5%（1950/2000）**；
  Geometric Perception PPO **96.0%（1920/2000）**。
- 渐进消融成功次数：Baseline 1950 → Residual RL only **1944（97.2%）** →
  +Contrastive **1952（97.6%）** → Full **1960（98.0%）**。
- CR5 六轴真机，**200 次/方法、共 600 次**：Full **86%（172/200）**；
  Baseline PPO **70%（140/200）**；Geometric **76%（152/200）**。末端位置
  偏差 **0.031 m vs 0.046 m**；执行时间 **6.73±0.98 s vs 8.62±1.34 s**。
- 作者明确写：**“No claim of statistical significance is made for the observed
  differences.”**（§4.6, p.22）；并写仿真 0.5 pp 差异应与真机差异分开解释。

## 方法要点

- **两阶段**：GraspNet 从点云生成 6-DoF 标称抓取；PPO 策略在其邻域输出有界
  残差（单次平移 ±20 mm、旋转 ±15°，最多 K=5 次决策），
  `g_final = g_init ⊕ Δg`；平移在机器人基座系，旋转在标称抓取系右乘。
- **表征**：PointNet++ 点云特征 + 12 维关节状态（q, q̇）；InfoNCE 做跨模态
  对齐，cross-attention 以物理状态为 query、点云局部特征为 K/V。
- **训练目标**：PPO clipped surrogate + 对比损失 + 动作正则
  `E||μ_θ(s)||²`；PPO 超参 η=3e-4、γ=0.99、GAE λ=0.95、ε=0.2、batch 256。
- **成功判据**：抬升 ≥0.10 m 并保持 ≥2.0 s 不滑落。

## 批判性评估

### 统计与可比性

- **仿真主结果在噪声内。** 98.0% vs 97.5% 只差 **10/2000**；按独立二项近似，
  合并 p=0.9775、SE≈0.00469、z≈1.07、双侧 p≈0.29（本评审计算，C 级）。
  作者自己也不做显著性声明。把 +0.5 pp 当作“有效”是过度解读。
- **缺最强下界对照。** 没有“GraspNet 原样执行、零残差”这一臂。Baseline PPO
  只吃 12 维关节状态、看不到物体，等价于近零修正策略；97.5% 很可能主要是
  几何先验本身的性能，而不是“残差方法的对照”。
- **仿真 +0.5 pp 与真机 +16 pp 相差 32 倍**，而全文无系统辨识、无域随机化、
  无真机微调；真机三种方法是否用同一批物体、同一摆放序列、失败是否重试均
  未报告。真机提升的替代解释（试次不独立、baseline 更脆弱、重试次数不同）
  作者未排除。
- **执行时间反而下降 21.9%**（8.62→6.73 s），与“最多 5 次闭环修正”的直觉
  相反；论文没有给出时间分解（失败重抓减少？baseline 重试更多？）。
- **消融不支持组件独立贡献**：Residual RL only（1944）**低于** Baseline
  （1950），作者用“残差把可行抓取推离可行域”解释；cross-attention 与动作
  正则的独立效应作者明确说未隔离。

### 未报告/内部不一致

- §3.2.4 称物理流编码“real-time 6D pose information”，§4.1 与 Table 2 却是
  **12 维关节角+角速度**。二者对应完全不同的可获取性与泛化性。
- 点云点数 N、特征维 C、嵌入维 d、温度 τ、batch B、λ_RL/λ_CL/λ_reg、
  训练回合数、训练种子、训练硬件、GraspNet 权重来源、RGB-D 相机型号、
  夹爪宽度、碰撞模型均未报告。
- 手眼标定只写“做了”，无残差量级；真机末端偏差的测量仪器与失败试次是否
  计入未说明。

### 失败模式

- 残差把已可行的标称抓取推离可行域（1944<1950 的直接证据）。
- 单次界 ≠ 累计界：K=5 次累计可达 100 mm/75°，作者只声明“不是累计界”。
- 点云↔关节状态对比学习在相机固连于臂时可能退化为运动学恒等式；作者未做
  “打乱配对”的 sanity check，也未测假负例频率。

## 代码与数据

- **无代码、无公开数据、无训练配置**；数据仅“应要求提供”。复现结论：
  **不可复现**。
- 论文的写作值得肯定：大量自限表述、明确不主张泛化到井下/任意平台。

## 与 JCHENG / ArmPi Ultra 的适配

- **自由度硬阻断**：CR5 为 6 轴，策略需要任意 SO(3) 旋转修正；ArmPi 是
  **5-DoF + 夹爪**，无法实现任意 6D 修正，必须投影到 5-DoF 可达流形，论文
  没有提供方法。
- **状态观测硬阻断**：Full Model 吃 12 维 `(q, q̇)`；ArmPi 无编码器，
  `/joint_states` 是命令缓存，没有可信 q̇。把指令差分伪装成 q̇ 会违反 L3
  “不得伪造数据”的红线。
- **算力**：残差策略是小 MLP + 单层 attention，Pi 5 可实时；GraspNet
  （PointNet++）需在 RTX 3060 6 GB 侧推理，跨域传输时延未评估。
- **可借鉴的工程契约**：有界残差 + 显式位姿合成（基座系平移、局部系右乘
  旋转）+ “零修正”回退选项 + **累计界**。这些语义可写入 `ExecuteMotion`
  的位姿增量设计评审，但不能把论文的 86% 当作本平台收益。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | 仿真 +0.5 pp（10/2000）在统计上不可区分于零 | A（Table 3 + 本评审二项检验） | **不采纳**为有效性证据 |
| 2 | 残差项本身可能伤害已可行的标称抓取（1944<1950） | A（Table 4） | **仅借鉴**：残差层必须有零修正回退与 A/B 门控 |
| 3 | 单次界 ≠ 累计界；安全必须由系统层另行约束 | A（作者自述） | **采纳**：写入安全评审 |
| 4 | 有界残差 + 位姿合成语义是可复用的契约 | A（Eq.2/§3.2.1） | **采纳**为设计参考，不采纳其数字 |
| 5 | 6-DoF 动作空间与 12 维 q/q̇ 输入无法迁移到 5-DoF/无编码器平台 | A（平台事实） | **不采纳**运行时 |
| 6 | 真机 86% vs 70% 在独立同分布假设下显著，但试次独立性未证明 | B（Table 5 + 本评审检验） | **仅借鉴**，需自行复测 |

## 核验片段

1. “the full model achieves 98.0% grasp success versus 97.5% for Baseline PPO” — Abstract, p.1
2. “5 × 20 × 20 = 2000 post-training attempts per method (400 attempts per seed)” — §4.1, p.15
3. “each method was tested over 200 grasping trials, resulting in 600 trials” — §4.1, p.16
4. “Baseline PPO 1950 97.5 88.5 ± 4.3 1200 / Full Model 1960 98.0 91.2 ± 3.1 1000” — Table 3, p.15
5. “Residual RL only 97.2 1100” — Table 4, p.16
6. “No claim of statistical significance is made for the observed differences.” — §4.6, p.22
7. “limited to ±0.020 m and ±15° per action component” — §4.1, p.15
8. “A maximum of K = 5 corrective decisions were permitted” — §4.1, p.15
9. “encodes the real-time 6D pose information through a fully connected layer” — §3.2.4, p.14（与 12-D 关节状态矛盾）
10. “The data presented in this study are available on request from the corresponding author.” — p.24

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)
的分类与推荐。结论：**不引入运行时**；只采纳“有界残差 + 零修正回退 +
累计界”的设计语义，以及作者诚实报告局限的写法。
