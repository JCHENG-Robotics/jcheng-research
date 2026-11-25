# SAM 3 — promptable concept segmentation

- **Type**: primary paper + official repository
- **Accessed**: 2026-11-25
- **Read scope**: arXiv HTML body, including the Limitations section (Appendix B)
  and the latency/tracking discussion; repository README not audited line by line.
  Claims below are A-grade for the paper's own statements.

## Paper

- Carion, Gustafson, Hu, et al. *SAM 3: Segment Anything with Concepts*.
  arXiv:2511.16719, v1 2025-11-20, v2 2026-03-28. Meta Superintelligence Labs.
  <https://arxiv.org/abs/2511.16719>
- Promptable Concept Segmentation (PCS): short noun phrases, image exemplars, or
  both; returns masks plus identities for **all** matching instances in images and
  video. DETR-style detector + SAM 2-style memory tracker share a Perception
  Encoder; a presence head decouples recognition from localization.
- Numbers quoted in the paper: 48.8 zero-shot mask AP on LVIS; video PCS cgF1 /
  pHOTA: SA-V 30.3 / 58.0, YT-Temporal-1B 50.8 / 69.9, SmartGlasses 36.4 / 63.6;
  VOS J&F 78.4 on MOSEv1, 92.2 on DAVIS17. It reaches >80% of human pHOTA.

## Limitations relevant to the SST pipeline

- **Prompt scope**: "constrained to simple noun phrase prompts"; does not support
  multi-attribute queries beyond one or two attributes. Fine-grained out-of-domain
  concepts (aircraft types, medical terms, thermal imagery) are hard.
- **Ambiguity**: polysemy, subjective descriptors, ungroundable phrases, boundary
  ambiguity, occlusion and blur; mitigated by an ambiguity module (15% reduction
  in overlapping instances), not eliminated.
- **Tracking drift**: errors from mask propagation, false detector predictions,
  and IoU matching in crowded scenes; no shared object-level context across
  masklets; periodic re-prompting is the mitigation.
- **Latency/cost**: 30 ms per image on an H200 with 100+ objects; video cost
  scales linearly with object count; ~5 concurrent objects near real-time; 64
  objects at 30 FPS requires 8 H200s; a 15-frame confirmation delay adds ~0.5 s.

## Why this matters for SST

SST runs SAM 3 as an HTTP service during evaluation, with a memory window and a
27B Qwen judge. The paper's own limitations predict exactly the failure modes the
SST prompt tries to patch by hand ("MISSED" vocabulary, color backup phrases):
ambiguous nouns, small/occluded objects, and drift over long episodes. The prompt
is therefore part of the method, not an implementation detail.

## Relevance to JCHENG

A SAM 3 service is not deployable on a Pi 5 or a 3060 laptop alongside the rest of
the stack. The paper's 30 ms/image figure is an H200 number and excludes the Qwen
judge and the video tracker.
