# SAM 3 — 可提示概念分割

- **类型**：一手论文 + 官方仓库
- **访问日期**：2026-11-25
- **阅读范围**：arXiv HTML 正文，包括 Limitations（附录 B）与延迟/跟踪讨论；
  仓库 README 未逐行审计。下文对论文自述为 A 级。

## 论文

- Carion, Gustafson, Hu 等。*SAM 3: Segment Anything with Concepts*。
  arXiv:2511.16719，v1 2025-11-20，v2 2026-03-28。Meta Superintelligence Labs。
  <https://arxiv.org/abs/2511.16719>
- Promptable Concept Segmentation（PCS）：名词短语、图像 exemplar 或两者组合；
  返回图像与视频中**所有**匹配实例的 mask 与 identity。DETR 式检测器 + SAM 2 式
  记忆跟踪器共享 Perception Encoder；presence head 将识别与定位解耦。
- 论文报告的数字：LVIS 零样本 mask AP 48.8；视频 PCS cgF1 / pHOTA：SA-V
  30.3 / 58.0，YT-Temporal-1B 50.8 / 69.9，SmartGlasses 36.4 / 63.6；VOS J&F：
  MOSEv1 78.4，DAVIS17 92.2。达到人类 pHOTA 的 80% 以上。

## 与 SST 管线相关的局限

- **提示范围**："constrained to simple noun phrase prompts"；不支持超过一两个
  属性的多属性查询。细粒度 OOD 概念（航空器型号、医学术语、热成像）困难。
- **歧义**：多义词、主观描述、不可落地短语、边界歧义、遮挡与模糊；用歧义模块
  缓解（重叠实例减少 15%），但未消除。
- **跟踪漂移**：mask 传播、检测器误检、拥挤场景 IoU 匹配都会导致错误；masklet
  之间没有共享的物体级上下文；缓解手段是周期性重新提示。
- **延迟/成本**：H200 上 100+ 物体的单图 30 ms；视频成本随物体数线性增长；约 5
  个并发物体可近实时；64 个物体 30 FPS 需要 8×H200；15 帧确认延迟约 0.5 s。

## 为什么这对 SST 重要

SST 在评测时把 SAM 3 作为 HTTP 服务运行，带 memory window 和 27B Qwen judge。
论文自述的局限正好预测了 SST 词表手工修补的失败模式（`MISSED` 词、颜色备份）：
歧义名词、小/遮挡物体、长 episode 漂移。因此**词表是方法的一部分**，不是实现
细节。

## 对 JCHENG 的相关性

SAM 3 服务无法与其余栈一起部署在 Pi 5 或 3060 笔记本上。论文的 30 ms/图是 H200
数字，且不含 Qwen judge 与视频跟踪器。
