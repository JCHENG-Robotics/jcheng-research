# GloVLA — 几何搬运 + 局部 VLA 的混合操作框架

- **类型**：一手论文（arXiv v1 全文 9 页）+ 官方项目页 + GitHub 检索
- **访问日期**：2026-11-25
- **阅读范围**：**PDF 全文 9 页**，包括 Table I–VI、Fig. 2/3/5/6/7；arXiv abs
  页；项目页；GitHub API 搜索。**没有代码可审计**（截至访问日无方法代码发布）。
- **本地副本**：`references/manipulation/papers/20261125-glovla.pdf`（9 页，291,316 字节）
- **许可**：arXiv abs 页标注 **CC BY-NC-SA 4.0**（Attribution–NonCommercial–
  ShareAlike 4.0）。本副本仅供私有研究使用，不得商用；转载/再分发需遵守
  CC BY-NC-SA 4.0。该许可不改变 `jcheng-research` 自身的许可状态。

## 来源

- Nguyen, T. T., Nguyen, H. H., Nguyen, H. A., Dinh, B. K., Vien, N. A.,
  Nguyen Ho Minh, D., Vu, M. N., Le, N. *GloVLA: Let Geometry Move and Local
  VLA Interact for Robust Object-Centric Manipulation in Unstructured
  Environments*. arXiv:2609.06256v1, 2026-09-05；投稿 IEEE RA-L。
  <https://arxiv.org/abs/2609.06256>
- 项目页：<https://glovla-project.github.io/>（视频；无 code/dataset 链接；
  BibTeX 为 "Under review", "Anonymous Authors"）
- 网页仓库：<https://github.com/glovla-project/glovla-project.github.io>
- GitHub 搜索 `GloVLA`：3 个结果，均为 profile/网页，**无方法代码**。
- 本地 PDF 说明：原始 arXiv PDF 为 5,279,845 字节，超过本仓库 5 MB 门禁；
  用 Ghostscript `-dPDFSETTINGS=/ebook` 压缩为 291,316 字节。文本层与页数
  （9 页）保持不变，图像分辨率降低；引用数字以论文表格/正文为准。

## 论文声称的核心结果（作者报告值，未独立复现）

- 标准 LIBERO Object（10 任务 × 50 episodes × 5 runs）：π0 87.4→98.6，
  π0.5 97.8→99.6，GR00T N1.6 88.8→98.4，GR00T N1.7 96.4→99.6。
- LIBERO-Challenge（50 场景；30 easy/10 medium/10 hard；每场景 50 episodes）：
  GR00T N1.6 full **20.8±10.0%** → GloVLA **88.5±9.4%**；hard 1.5→74.9%。
- LIBERO-Plus：加权平均 **88.2%**，6/7 轴领先或持平。
- 真实 UR10e（90 trials）：总体 **35.6% → 90.0%**；表 VI 的 inference
  **60.1±19.6 s → 28.2±2.0 s**（2.13×；未注明统计单位/推理硬件）。
- 数据效率：Table V 仅 Alphabet Soup；10 demos clean 100% vs FullVLA 86.0%；
  50 demos 非结构化平均 99.9% vs 48.5%。

## 方法要点

- 7D OSC 动作（6 维位姿增量 + 夹爪）；策略输出 chunk，执行 `n_act ≤ H` 后重查。
- 提取区域 `R_j^clip = {p : ||p − c_j||₂ ≤ r_j}`；`r_o=0.12 m`、`r_b=0.18 m`。
- 抓取片段：进入物体球且夹爪开（指令/观测）→ 首次闭合指令 → 离开物体球 +1。
- 放置片段：进入篮子球且持物 → 首次释放指令 → `+9` 步。
- transport：`p_hj = ĉ_j + δ_j`；`δ_o=(0.04,0,0.08)`、`δ_b=(0.005,0.005,0.12)`；
  `a_xyz = clip(S^{-1} K_p (p_hj − p_ee), −1, 1)`；姿态保持；无碰撞检查。
- handoff：`H_j = {||p − p_hj||₂ ≤ ε_j}`；四模式 `app/grasp/trans/place`。
- 包含条件：`ε_j + η_j + ||δ_j||₂ ≤ r_j`；只保证位置包含，不保证
  orientation/gripper/visual context 的 in-distribution。

## 关键限制（与 JCHENG 决策相关）

- **无代码/数据/LIBERO-Challenge 发布**；RA-L 在审；没有独立复现。
- 仿真用**真值**物体/容器中心；FullVLA 只有 RGB + proprioception，不是
  感知公平的对比。真实机器人用 SAM 3，但论文没有报告 SAM 3 的定位误差 η。
- 训练**两个独立局部策略**（πg、πp），FullVLA 是一个策略；没有策略数/容量
  匹配的消融。
- 局部策略使用固定阶段指令 `ℓg`/`ℓp`；语言 grounding 被外置；没有小型
  vision-only 局部策略的消融。
- transport 无碰撞检查；“obstruction”未说明是物理占道还是视觉遮挡。
- 统计：50 episodes/scene、5×10 runs、无 CI/显著性；真实 10–20 trials/条件；
  Table V 与消融只用一个任务；摘要 20.9 vs Table II 20.8。
- ε、K_p、S、真实机器人演示数量均未报告；arXiv v1 无附录。

## 对本仓库的意义

用于 [GloVLA 评估报告](../../reports/20261125-glovla-hybrid-factorization-eval.md)
与 [MVE-0 桌面复算](../../experiments/20261125-glovla-handoff-budget/result.md)。
结论：现在不引入 GloVLA 运行时；采纳 Eq. 12 门禁、分级扰动评测与阶段标注
schema；若扩物体/语言条件，先用 ACT/DP3 量级小策略做仿真 MVE。
