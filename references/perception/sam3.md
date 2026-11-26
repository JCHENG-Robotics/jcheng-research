# SAM 3 — 可提示概念分割

- **类型**：一手论文 + 官方仓库
- **访问日期**：2026-11-25（论文）；2026-11-26（上游仓库、HF、issue 更新）
- **阅读范围**：arXiv HTML 正文，包括 Limitations（附录 B）与延迟/跟踪讨论；
  2026-11-26 补读上游 README、`model_builder.py`、`sam3_image_processor.py`、
  `sam3_video_inference.py`、`vitdet.py`、SAM3.1 release notes 与相关 issue；
  未下载 gated 权重，未运行代码。下文对论文自述为 A 级。

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

## 2026-11-26 更新：上游状态、消费级证据与 SST 用法

**上游（main `31cb7e62`，2026-11-17 push；本次静态审读）**

- 848M 参数；`sam3.pt` 3.45 GB（`facebook/sam3`），`sam3.1_multiplex.pt` 3.5 GB
  （`facebook/sam3.1`）。两个 HF 仓库都是 **`gated: manual`**，需要登录并同意
  共享用户名/邮箱；本机无 HF token，未下载、未运行。
- 图像输入默认 **1008×1008**（`Sam3Processor(resolution=1008)`），可改；
  ViT window partition 会 padding，504 px 在代码上可运行（用户实测见 #424）。
- 图像模式支持文本提示与几何提示：`Sam3Processor.add_geometric_prompt(box, label)`
  接受归一化的 `[cx, cy, w, h]`，可用于"YOLO 框 → SAM3 掩码"。
- 视频 API 是**离线**的：`init_state` 先解码整段视频，`propagate_in_video` 按
  固定 `num_frames` 传播；在线/因果封装需要自己维护增长的状态（SST 的做法）。
- 许可证是 **SAM License**（2025-11-19），不是 MIT；再分发须附同一协议，禁止
  逆向与 ITAR/军事等用途。`sam3/pyproject.toml` 的 `MIT` classifier 与
  `LICENSE` 不一致，是打包元数据错误。

**SAM 3.1 Object Multiplex（2026-03-27）**

- 共享记忆、多物体联合跟踪；单张 H100、128 个物体时约 **7×** 快于 3.0。
- 精度有升有降：YT-Temporal-1B +2.1 cgF1，LVVIS 36.3→34.3，BURST/YTVIS21 略降。
- **1–3 个物体时 3.1 比 3.0 更慢、显存更高**：issue #542 的 3060 用户报告视频
  示例 1 小时 vs 3.0 的 5 分钟，维护者评论确认"1 个物体更慢，4 个以上才更快"；
  issue #526 报告 `sam3.1_multiplex.pt` 在公开 main 上没有干净加载路径（仍 open）。

**消费级 GPU 证据（用户自报，B 级）**

| 来源 | 配置 | 数字 |
|---|---|---|
| #424 评论（3090） | PyTorch，1008 px，f32 | 编码 390 / 跟踪 125 / 文本 70 ms |
| #424 评论（3090） | PyTorch，1008 px，bf16 | 编码 110 / 跟踪 21 / 文本 22 ms |
| #424 评论（3090） | PyTorch，504 px，bf16 | 编码 46 / 跟踪 5 / 文本 12 ms |
| #424 正文（4090） | ORT TensorRT EP，~600×500，多提示批量 | ~1.1 s/图 |
| #542（3060） | 3.1 vs 3.0 视频示例 | >1 h vs 5 min |
| #408 评论 | 视频流式 | 约 3 MB/帧/物体（float32）；关闭缓存可 ~3 GB 跑跟踪 |

**派生实现**

- `PINTO0309/SAM3-TensorRT`（MIT）：ONNX→TensorRT；3090 4K 端到端 438→75 ms。
- `embedl/sam3`（gated，额外禁止托管服务）：L4 TRT FP16 137→104 ms，INT8 精度接近。
- `kengboon/sam3_openvino`（duplicated from `rajeshgangireddy`）：fp16 权重 1.63 GB，
  Intel XPU 约 452 ms/图；没有 NVIDIA 3060 数据。

**结论**：6 GB 笔记本处于"图像模式可能、视频很紧"的边界；必须实测，不能引用
H200 的 30 ms。详见
[报告](../../reports/20261126-sam3-sst-open-source-attempt-route.md) 与
[实验设计](../../experiments/20261126-sam3-6gb-feasibility/design.md)。
