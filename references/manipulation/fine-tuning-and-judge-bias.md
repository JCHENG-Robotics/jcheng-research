# 微调策略与 LLM judge 偏差

- **类型**：一手论文
- **访问日期**：2026-11-25
- **阅读范围**：ULMFiT PDF（用 `pdftotext` 抽取相关章节）；两篇 judge 偏差论文
  只读摘要/检索摘要，未读 PDF 全文。

## 判别式微调（ULMFiT）

- Howard & Ruder。*Universal Language Model Fine-tuning for Text Classification*。
  arXiv:1801.06146，ACL 2018。<https://arxiv.org/abs/1801.06146>
- PDF §3.2 原文："Instead of using the same learning rate for all layers of the
  model, discriminative fine-tuning allows us to tune each layer with different
  learning rates." 其动机是不同层捕获不同类型的信息，应以不同幅度微调，以保留
  预训练知识、避免灾难性遗忘。
- **相关性**：这是 SST `module_lr_mult`（ViT 0.3×、merger/LLM 0.5×、embedding
  冻结、action/align 1.0×）的概念先例。SST 的分组更粗（7 个模块，不是逐层），
  消融只有约 2.2 pp 且在噪声边缘，但方向与长期微调实践一致。

## LLM-as-a-judge 偏差

- Wang, Li, Chen 等。*Large Language Models are not Fair Evaluators*。
  arXiv:2305.17926，ACL 2024。<https://arxiv.org/abs/2305.17926>
- 位置偏差：交换两个候选的顺序就能翻转排名；在顺序交换下，较弱模型在 66/80 个
  查询上“击败”ChatGPT。缓解：平衡位置校准（两种顺序各跑一次取平均）、先给证据
  再打分、对歧义样本引入人工。
- Zheng, Chiang, Sheng 等。*Judging LLM-as-a-Judge with MT-Bench and Chatbot
  Arena*。arXiv:2306.05685，NeurIPS 2023。<https://arxiv.org/abs/2306.05685>
- 记录了位置、冗长、自我增强偏差，以及 LLM judge 的推理局限。
- **相关性**：SST 的 judge 不是 pairwise，经典位置偏差不直接适用。但它是每个
  物体一次 yes/no、阈值 0.5、没有人工校准集、没有报告 judge 错误率。`--judge-regrow`
  规则缓解了一种失败（首次只看到部分物体），不是普遍的校准问题。Judge 只能否决
  候选，不能补回 SAM 3 从未提出的物体。
