# Fine-tuning strategy and LLM-judge bias

- **Type**: primary papers
- **Accessed**: 2026-11-25
- **Read scope**: ULMFiT PDF (relevant section extracted with `pdftotext`); the two
  judge-bias papers were read as abstracts/search summaries, not full PDFs.

## Discriminative fine-tuning (ULMFiT)

- Howard & Ruder. *Universal Language Model Fine-tuning for Text Classification*.
  arXiv:1801.06146, ACL 2018. <https://arxiv.org/abs/1801.06146>
- PDF, §3.2: "Instead of using the same learning rate for all layers of the model,
  discriminative fine-tuning allows us to tune each layer with different learning
  rates." The stated motivation is that different layers capture different types
  of information and should be fine-tuned to different extents, to retain previous
  knowledge and avoid catastrophic forgetting.
- **Relevance**: the conceptual precedent for SST's `module_lr_mult` (ViT 0.3×,
  merger/LLM 0.5×, embeddings frozen, action/align 1.0×). SST's grouping is
  coarser (7 modules, not per layer), and its ablation is only ~2.2pp at the noise
  floor, but the direction is consistent with a long line of fine-tuning practice.

## LLM-as-a-judge bias

- Wang, Li, Chen, et al. *Large Language Models are not Fair Evaluators*.
  arXiv:2305.17926, ACL 2024. <https://arxiv.org/abs/2305.17926>
- Position bias: swapping the order of two candidates can invert the ranking;
  a weaker model beat ChatGPT on 66/80 queries under order swap. Mitigations:
  balanced position calibration (run both orders and average), evidence-first
  scoring, human-in-the-loop for ambiguous cases.
- Zheng, Chiang, Sheng, et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot
  Arena*. arXiv:2306.05685, NeurIPS 2023. <https://arxiv.org/abs/2306.05685>
- Documents position, verbosity and self-enhancement biases, and limited reasoning
  in LLM judges.
- **Relevance**: SST's judge is not a pairwise comparison, so classic position bias
  does not directly apply. But it is a single yes/no judgement per object with a
  0.5 threshold, no human calibration set, and no reported judge error rate. The
  `--judge-regrow` rule mitigates one failure (a partial first view), not the
  general calibration problem. The judge can reject a candidate object but cannot
  add an object SAM 3 never proposed.
