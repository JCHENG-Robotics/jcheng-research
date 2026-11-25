# LingBot-VLA 2.0 — 论文、仓库、权重与 SST 衍生工作

- **类型**：一手论文 + 官方仓库 + 模型权重 + 竞赛衍生工作
- **访问日期**：2026-11-25
- **阅读范围**：论文摘要与 HTML 正文（已检查正文，**不含** RoboTwin 内容）；官方
  `main` 分支的 README、`robotwin.yaml`、`assets/training_data/robotwin.txt` 直接
  读取；SST 报告与代码另行审计（见 `sst-repo-audit.md`）。**未通读 PDF 全文。**

## 原始论文

- Wu, Wang, Lu, Sun, Liu, Wang 等。*From Foundation to Application: Improving VLA
  Models in Practice*（LingBot-VLA 2.0）。arXiv:2607.06403，v1 2026-07-07。
  <https://arxiv.org/abs/2607.06403>
- 摘要/HTML 声称的贡献：约 60,000 小时预训练数据（50,000 小时机器人轨迹，覆盖 20
  种本体；10,000 小时第一人称人类视频）；55 维统一状态/动作向量；稀疏 MoE 动作
  专家；从 LingBot-Depth（几何）与 DINO-Video（时序）做双查询蒸馏。
- 论文报告的基准：GM-100（AgileX Cobot Magic 平均成功率 34.4%，Galaxea R1Pro
  15.6%；progress/success 的拆分来自检索摘要，未在 HTML 中复核）、长时序移动操作、
  LARYBench。论文正文**没有** RoboTwin 2.0 数字。
- 作者自述局限（HTML 正文）：任务间 progress 与 success 差距大；本体因素
  （运动学、相机视角、动作空间对齐）仍然困难；OOD 退化。

## 官方仓库

- <https://github.com/Robbyant/lingbot-vla-v2>，Apache-2.0，访问 2026-11-25。
- README 原文："Below we use **RoboTwin 2.0** 50 tasks, trained with clean and
  randomized data together, as an example."（README 第 138 行；第 146 行重复。）
- RoboTwin 后训练表（README 第 164 行）：Muon **93.52 clean / 92.80 randomized**，
  5.93 s/it；对照列为 π0.5（82.74/76.76）与 LingBot-VLA 1.0（88.56/86.68）
  （README 第 251–252 行）。
- 数据清单 `assets/training_data/robotwin.txt`：每个任务一条
  `*_randomized_500-1000` 加一条 `*_clean_50-50`。因此 92.80 的 randomized 结果
  使用一个名为 `*_randomized_500-1000` 的随机池（每任务 500–1,000 条演示；清单
  未说明精确条数），加每任务 50 条 clean 演示——至少是竞赛允许的 clean-only
  预算的 10 倍。
- 评测注意事项（README 第 190 行）："Release validation of the published
  checkpoint uses **FP32 inference**; BF16 uses less GPU memory, but can produce
  materially different success rates."
- 已发布权重：`robbyant/lingbot-vla-v2-6b`（native depth）与
  `robbyant/lingbot-vla-v2-6b-robotwin`（2026-07-25）。
- 真机推理延迟：RTX 4090D、10 步去噪、`--use_length 25` 时约 130 ms（README 部署
  章节）。

## 竞赛衍生工作（SST）

- 报告：<https://yzmyalier.github.io/Lingbot-Challenge-SST/>
- 代码：<https://github.com/YzmYalier/Lingbot-Challenge-SST>，commit
  `8797aa31dd9798a6e931d57857f32cd5de372b6c`。
- 数据：<https://huggingface.co/datasets/yydsyangsdyy/Lingbot-Challenge-SST>，
  revision `7111c726e5f45e045e5ead62816a1d175a826a9e`。
- SST 只训练 `demo_clean-50`（2,500 episodes），这是竞赛约束（见
  `competition-rules.md`）。因此它的基线与终版不能与官方 clean+randomized 配方
  直接比较。

## 对 JCHENG 的相关性

上游仓库（Apache-2.0）是唯一可以合法复用的部分；SST 自有增量没有根许可证。
93.52/92.80 说明：当数据预算不受约束时，增加 randomized 演示是主导杠杆，而不是
前景提示。
