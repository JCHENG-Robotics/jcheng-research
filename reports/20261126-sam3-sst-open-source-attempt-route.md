# SAM 3 在 SST 赛后开源仓库中的实现审读与 ArmPi 尝试路线

> 报告状态：**draft**（draft | reviewed | superseded）。日期：2026-11-26。
> 作者：ZCode（研究代理），for J. Cheng。评审：pending。
> 本报告影响的决策：是否、以何种形式在 JCHENG 引入 SAM3 系开放词汇分割；先离线验证还是直接进运行链。
> 研究主题：具身智能挑战赛 SST 队赛后开源仓库中的 SAM3 使用方式、SAM3 上游事实，以及在本平台上的最小尝试路线。
> 研究边界：**没有获得 HF gated 权重**（`facebook/sam3`、`facebook/sam3.1` 均为 manual gating，本机无 HF token），**没有运行任何 SAM3 代码**，**没有机器人访问**；SST 代码为静态审读，pin 在 `8797aa31`；上游代码审读 pin 在 `facebookresearch/sam3` main（`31cb7e62`，2026-11-17 push）；SAM3 论文正文沿用 2026-11-25 的阅读记录，本次未重读；消费级 GPU 数字来自上游 issue 的用户自报（B 级），不是本机实测。

**证据等级**：**S** 在本机复现/实测 · **A** 一手论文、官方仓库、官方文档或源码 · **B** 可信但间接的工程证据 · **C** 基于现有证据的推断 · **D** 未验证假设。

---

## 01. Executive Summary（执行摘要）

**推荐：现在不把 SAM3 放进感知到运动的运行链。先做一条 1–2 天的离线尝试路线——6 GB 显存可行性基准 → 自有帧上的掩码质量与提示词稳定性 → 再决定是否以"顾问式"HTTP 服务接入 `jcheng-perception`。只考虑 SAM 3.0、单物体、504–672 px、图像或短序列视频模式；如果两道门禁（G0/G1）不过，回退 SAM2.1（Apache-2.0）+ GroundingDINO（Apache-2.0），或维持现有 YOLO 检测器。**

支撑这个结论的四条事实：

1. **SST 的 SAM3 不是"一个分割模型"，而是一条数据工程链。** 848M 参数的图像/视频分割器逐短语跟踪 + 27B Qwen 逐对象评审 + 8 GPU 评测环境；发布物是 2,500 episodes / 548,893 帧的"前景掩码"训练集，不是可移植的运行时组件 [A: SST `README.md`、`auto_mask/`、`sam3/tools/`、`base.json`]。值得学的是它的数据治理与评测纪律，不是它的部署形态 [C]。
2. **6 GB 处在"图像模式可能、视频很紧"的边界。** 上游 issue 里 3090 的 PyTorch bf16 实测：1008 px 图像编码 110 ms + 每物体跟踪 21 ms + 文本检测 22 ms；504 px 分别是 46 / 5 / 12 ms [B: #424 评论]。3060 笔记本大致是 3090 的 1/3（C），即 504 px 单物体约 0.1–0.25 s、1008 px 约 0.3–0.6 s；显存则取决于分辨率、物体数与视频长度，必须实测 [C/D]。
3. **真正的迁移成本是词表，不是模型。** SST 交付的是一份 73 行的手工词表：按 RoboTwin 物体类别逐类写短语、颜色备份、`MISSED` 词规避，并强制包含 `robot, robot arm` [A: `vllm_space/sam3_prompt.py`]。换一套物体/相机/指令，这份词表要重做，失败模式要重新标定 [A: 词表内容；C: 迁移判断]。SAM3 不是"零样本即用"。
4. **SAM3.1 对我们这种 1–3 物体场景是负优化。** 官方 release notes 说 3.1 的 Object Multiplex 在单张 H100、128 个物体时约快 7× [A: `RELEASE_SAM3p1.md`]；但 issue #542 的 3060 用户报告 3.1 视频示例跑了 1 小时、3.0 只要 5 分钟，维护者评论确认"1 个物体时 3.1 更慢，4 个以上才更快" [B: #542 及其评论]。要用就用 3.0。

**主要风险**：掩码边界不是我们当前最大的误差源（跨视角残差 10–14 mm，见 §03）；把 SAM3 放进链路会新增一个分布外环节、一个 gated 权重依赖和一份有再分发限制的许可证。它更适合作为**离线标注/评估工具**或**YOLO 框的掩码细化器**，而不是替代现有检测器。

**一句话**：这是一项**值得花 1–2 天离线验证、但不值得现在动运行链**的技术。

---

## 02. Research Questions（研究问题）

**主问题**：基于 SST 赛后开源仓库中对 SAM3（及同类开放词汇分割）的使用，JCHENG 应该以什么形式、在什么前置条件下尝试 SAM3？

| # | 子问题 | 回答位置 |
|---|---|---|
| Q1 | SST 到底用 SAM3 做了什么？数据链和评测链分别怎么接？ | §06 |
| Q2 | SAM3 是什么、能力边界在哪、3.1 改了什么？ | §05 |
| Q3 | 在 6 GB 笔记本 3060 / Pi 5 8 GB 上能不能跑？跑多快？ | §05.4、§08、§11 |
| Q4 | 有哪些同价位替代方案？许可证是否可用？ | §07 |
| Q5 | 在 JCHENG 的最小尝试路线是什么？门禁、回退、成本？ | §09–§11、[design.md](../experiments/20261126-sam3-6gb-feasibility/design.md) |
| Q6 | 还有哪些结论缺证据？缺什么才能关闭？ | §12 |

**约束条件**：

| 类别 | 约束 |
|---|---|
| 硬件 | ArmPi Ultra：Pi 5 8 GB + 5-DoF 总线舵机臂 + 夹爪；D435i；LSLIDAR M10 未接入；操作笔记本 RTX 3060 Laptop **6 GB**（本机实测 6144 MiB，驱动 595.99.02，CUDA 13.2）[S] |
| 软件 | 机器人侧 ROS 2 **Humble**；本机仅 Jazzy，Python 3.12.3；无 `gh` CLI；无 HF token [S] |
| 安全 | 运动只能经 `jcheng_motion.ExecuteMotion`；lease/deadman/limits/stop latch；无 e-stop、无抱闸、无编码器；每次实机运动需单独授权 [A: 工作区 `AGENTS.md`] |
| 数据 | 无演示数据集；`/joint_states` 是命令缓存，不是测量；感知只给 advisory target [A: 工作区 `AGENTS.md`] |
| 法务 | 生态许可证评审未关闭，产品仓库不得出现 `LICENSE`；SST 自有代码无根 LICENSE；SAM3 权重是 SAM License 且 gated [A] |
| 算力 | 无 6B 级训练资源；本次只做离线推理可行性，不做训练 [A: 工作区现状] |

**交付物**：本报告 + 实验设计 `experiments/20261126-sam3-6gb-feasibility/design.md` + 更新后的来源记录 `references/perception/sam3.md`、`references/manipulation/sst-repo-audit.md`。

---

## 03. Current System Analysis（当前系统分析）

### 3.1 与 SAM3 直接相关的现状

| 事实 | 证据 |
|---|---|
| 感知层是 **advisory targets only**：采集、深度/TF 时间戳环、反投影、双视角融合、Kalman；检测在笔记本 GPU 上跑 YOLO | [A: 工作区 `AGENTS.md` §1；`jcheng-perception/docs/ARCHITECTURE.md`] |
| 现有固定点抓取链路依赖已知物体类别与标定；跨视角仍有 **10–14 mm 常数偏移**，怀疑外参 | [A: `jcheng-perception` 证据记录；C: 偏移归因] |
| 没有学习型操作策略，也没有演示数据集；动作标签质量未解 | [A: 工作区 `AGENTS.md` §7] |
| 运动唯一入口是 `jcheng_motion.ExecuteMotion`；capability 只能发 intent | [A: 工作区 `AGENTS.md` §3] |
| 本机 GPU 是 **RTX 3060 Laptop 6 GB**，当前 202 MiB 占用，无 torch | [S: `nvidia-smi` 2026-11-26] |
| Pi 5 是 8 GB 内存、无 CUDA；SAM3 的 848M 参数明显超出其能力 | [A: 硬件规格；C: 可行性判断] |

### 3.2 这意味着什么

- SAM3 若进入运行链，最自然的落点是**笔记本侧 GPU 节点**（与现有 YOLO 同侧），以 HTTP/JSON 或 DDS advisory 的形式把掩码/目标点交给感知层；Pi 5 只做消费，不加载模型 [C]。
- 但感知层当前的主要误差是**标定残差**，不是"物体类别覆盖不足"。SAM3 能补的是后者；前者不会因为换分割器而改善 [C]。
- 在没有演示数据、没有可靠动作标签之前，SAM3 的最大价值更可能是**离线**：给自有帧打掩码、评估 YOLO、为未来数据集合成前景掩码 [C]。

---

## 04. Research Methodology（研究方法）

### 4.1 检索策略

关键词组合（中英并用）：`SAM 3 Segment Anything with Concepts`、`SAM3 promptable concept segmentation`、`SAM 3.1 Object Multiplex`、`SAM3 VRAM consumer GPU`、`SAM3 3060/4090 latency`、`SAM3 OpenVINO/TensorRT/ONNX`、`SAM2.1 model sizes`、`Grounded-SAM-2`、`YOLO-World/YOLOE license`、`Lingbot-Challenge-SST`。

检索顺序：先重读 SST 源码与既有审计记录 → 用 GitHub API 检索上游仓库的 commit/issue（`repo:facebookresearch/sam3` + `VRAM`/`3060`/`OOM`/`laptop`，限定 `is:issue`）→ 用 HF API 读模型卡与文件清单 → 读 SAM3.1 release notes → 用 SAM2 / Grounded-SAM-2 / YOLO-World / YOLOE 做替代方案与许可证对照。

### 4.2 来源与阅读深度

| 来源 | 版本/日期 | 实际读到什么 | 等级 |
|---|---|---|---|
| SST 仓库 | commit `8797aa31`（2026-11-19） | 完整 `sam3/` vendored 树、`auto_mask/`、`inference/`、`tools/`、`vllm_space/`、`base.json`、`README` | A（静态） |
| SAM3 论文 | arXiv:2511.16719 v2 | 2026-11-25 已读 HTML 正文、Limitations、延迟讨论；本次沿用 | A（部分） |
| SAM3 上游仓库 | main `31cb7e62`（2026-11-17） | README、`model_builder.py`、`sam3_image_processor.py`、`sam3_video_inference.py`、`vitdet.py` | A |
| `RELEASE_SAM3p1.md` | 2026-03-27 | Object Multiplex 的动机、7×/128 物体、精度变化 | A |
| HF `facebook/sam3` | API 2026-11-26 | `gated: manual`；`sam3.pt` 3.45 GB；F32 safetensors 3.44 GB / 859,922,360 参数 | A |
| HF `facebook/sam3.1` | API 2026-11-26 | `gated: manual`；`sam3.1_multiplex.pt` 3.5 GB | A |
| sam3 issue #542 | 2026-05-06 | 3060 用户：3.1 视频 1 小时 vs 3.0 5 分钟；维护者确认 1 物体时 3.1 更慢 | B（用户自报） |
| sam3 issue #424 | 2026-01-22 | 4090 + ORT TensorRT EP：600×500、多提示批量 ~1.1 s；3090 PyTorch 分项计时表 | B（用户自报） |
| sam3 issue #408 | 2026-01-14 | 视频流式推理显存随时间增长；每物体每帧约 3 MB（float32）；关闭缓存可 ~3 GB 跑跟踪 | B（用户自报） |
| sam3 issue #526 | 2026-04-20 | `sam3.1_multiplex.pt` 在公开 main 上没有干净加载路径；3.0 正常 | A（issue 正文，未复现） |
| SAM2 仓库 | main，2026-05-30 push | 四个 2.1 变体参数量、A100 FPS、Apache-2.0 | A |
| Grounded-SAM-2 | 访问 2026-11-26 | 组合 GroundingDINO + SAM2；许可证分组件 | A |
| YOLO-World / YOLOE | GitHub API 2026-11-26 | `GPL-3.0` / `AGPL-3.0` | A |
| SAM3 TensorRT 导出 | PINTO0309/SAM3-TensorRT | 3090 4K 端到端 438→75 ms；MIT | B（README 自报） |
| Embedl SAM3 | HF 2026-11-26 | L4 上 TRT FP16 137→104 ms；INT8 精度接近；额外许可禁止托管服务 | B |
| SAM3 OpenVINO | kengboon/sam3_openvino（duplicated from rajeshgangireddy） | fp16 权重 1.63 GB；Intel XPU 约 452 ms/图 | B |

### 4.3 纳入/排除标准

- **纳入**：官方仓库源码/文档、官方 release notes、HF 模型卡与 API 元数据、issue 正文与其评论、可核对的许可证字段、官方基准数字。
- **排除**：把第三方博客/搜索摘要作为关键结论的唯一来源（本次搜索引擎摘要只用于定位一手链接，关键数字均回到 issue/README/API 原文）；未注明测法的"跑分"；把 3.1 的多物体优势外推到单物体。
- **停止条件**：Q1–Q5 有可追溯答案；主要替代方案已比较；继续检索不再改变"先离线、后顾问"的结论。

---

## 05. Literature Review（文献综述）

### 5.1 SAM 3：Promptable Concept Segmentation

- **问题与贡献**：把"分割一切"从"给点/框分割"推进到"给一个短名词短语，分割图像/视频中该概念的**所有**实例"，并返回 mask + identity。检测器（DETR 式）+ 跟踪器（SAM 2 式记忆）共享 Perception Encoder，presence token 把"识别"与"定位"解耦 [A: 论文；`sam3/README.md`]。
- **规模**：README 记 848M 参数；HF 模型卡的 F32 权重计数为 859,922,360（0.86B），两者口径略有差异，本报告按 848M–0.86B 量级处理；F32 权重 3.44 GB，「sam3.pt」3.45 GB [A: README；HF 模型卡]。
- **报告数字**：LVIS 零样本 mask AP 48.8；SA-Co 上达到人类 75–80%；视频 PCS 在 SA-V 30.3 cgF1 / 58.0 pHOTA [A: 论文/README]。
- **延迟**：H200 上 100+ 物体的单图约 30 ms；视频成本随物体数线性增长；约 5 个并发物体可近实时；64 个物体 30 FPS 需要 8×H200；15 帧确认延迟约 0.5 s [A: 论文]。
- **作者自述局限**：只支持简单名词短语（不支持一两个以上属性的复合查询）；歧义、遮挡、小物体、细粒度 OOD 概念困难；跟踪漂移（mask 传播、误检、拥挤场景 IoU 匹配）；masklet 之间无共享物体级上下文 [A: 论文 Limitations]。
- **对 SST 的含义**：SST 的 73 行词表、颜色备份、`MISSED` 规避，正好是在补这些局限 [A: 词表；C: 因果判断]。

### 5.2 SAM 3.1：Object Multiplex

- **动机**：3.0 的跟踪成本随物体数线性增长；3.1 把物体分组到固定容量桶、共享记忆，减少重复计算 [A: release notes]。
- **收益**：单张 H100、128 个物体时约 **7×** 快；CPU-GPU 同步更少、`torch.compile` 融合更好、批处理后处理 [A]。
- **代价/风险**：精度并非全面提升——YT-Temporal-1B +2.1 cgF1，但 LVVIS 36.3→34.3、BURST/YTVIS21 略降；1 个物体时比 3.0 慢、显存更高 [A: release notes；B: #542 评论]。
- **工程状态**：issue #526 报告 `sam3.1_multiplex.pt` 在 2026-04-20 的公开 main 上没有干净加载路径（3.0 正常）；该 issue 截至检索时仍 open [A: issue 正文]。
- **结论**：我们的场景是 1 个目标物体 + 可能 1 个容器，**应使用 3.0** [C]。

### 5.3 SAM 2.1（回退选项）

- 四个变体：tiny 38.9M、small 46M、base+ 80.8M、large 224.4M；A100 上 91.2/84.8/64.1/39.5 FPS [A: SAM2 README]。
- 代码与权重 **Apache-2.0** [A: SAM2 README]。
- 不支持文本提示：需要点/框/掩码；文本开放词汇要靠外部检测器（GroundingDINO 等）[A]。
- 对 6 GB 而言，tiny/small 的参数量比 SAM3 小一个数量级，显存与延迟都更友好 [C]。

### 5.4 GroundingDINO / Grounded-SAM-2（回退组合）

- GroundingDINO：Apache-2.0，文本→框；Grounded-SAM-2 把它与 SAM2 组合成"文本→框→掩码"管线，许可证按组件拆分 [A: 仓库]。
- 代价：两个模型、两段延迟、检测框质量成为掩码上限；但每个组件都比 SAM3 小、且不 gated [C]。
- 与我们的现状契合：已有 YOLO 框，可以直接"框→SAM2 掩码"而不引入文本检测器 [C]。

### 5.5 SST 的工程报告（非同行评审）

SST 的发布页与 README 是一份**受限赛道的工程报告**：clean-only 数据约束下的 36.20%→58.22% random 成功率，其中前景替换 +11.64 pp [A: 发布计数；S: 既有报告的桌面复算]。它不是 SAM3 的方法论文，不能用来推断 SAM3 在其它物体集上的表现 [C]。

### 5.6 可比性说明

以下数字**不能直接比较**：H200 的 30 ms（100+ 物体、图像 PCS）与 3090 的 110+21+22 ms（单物体、bf16、PyTorch）；4090 的 1.1 s（ORT-TRT、多提示批量、600×500）与 3090 的 75 ms（TensorRT、4K、导出实现不同）。本报告只在"同一实现、同一分辨率、同一物体数"内比较 [A/B]。

---

## 06. Repository Investigation（开源仓库调查）

SST 仓库：`https://github.com/YzmYalier/Lingbot-Challenge-SST`，commit `8797aa31`（2026-11-19）。以下均为**静态审读**，未执行其代码。

### 6.1 vendored SAM3 的版本与规模

- `sam3/` 是上游的**全量 vendored 树**：204 个文件、160 个 Python 文件，含 `sam3/model/`、`sam3/train/`、`sam3/eval/`、`tools/`；顶层有 `LICENSE`（SAM License，7,353 B）与 `README.md`（21 KB）[A]。
- 代码已包含 **3.1 Object Multiplex** 的实现（`multiplex_mask_decoder.py`、`sam3_multiplex_*`、`video_tracking_multiplex.py`），`build_sam3_predictor(version="sam3.1")` 指向 `facebook/sam3.1/sam3.1_multiplex.pt`；但 SST 的掩码器默认 `version="sam3"`，即数据生成用的是 3.0 权重 [A: `sam3/sam3/model_builder.py:661-669`；`sam3/tools/sam3_video_masker.py:53`]。
- `sam3/tools/` 下混有 SST 自写的适配层（`sam3_stream_server.py`、`sam3_stream_tracker.py`、`sam3_video_masker.py`、`sam3_video_dim.py`、`sam3_mask_judge.py`），它们调用上游内部 API，但**没有修改上游源文件**（`sam3_stream_tracker.py` docstring 明确说明）[A]。

### 6.2 离线数据链（训练集生成）

调用链（`process_data.sh --stage masks` → `auto_mask/pipeline_lerobot.py`）：

1. **提词**：Qwen-27B 看首帧 + 指令，输出逗号分隔的英文名词短语；模板 73 行，逐类给出首选词、颜色备份、`MISSED` 规避，并强制 `robot, robot arm` [A: `vllm_space/sam3_prompt.py`]。
2. **跟踪**：每个短语一个 SAM3 推理状态，逐帧跟踪；检测阈值 `score_threshold_detection=0.3`、`new_det_thresh=0.5` [A: `auto_mask/pipeline_lerobot.py:100`；`tools/services.py`]。
3. **评审**：每个新物体由 27B Qwen 看"原图 + 高亮掩码图"回答 yes/no，用 logprob 比值、阈值 0.5；被否决的 id 在面积增长到 `--judge-regrow 2.0` 倍时复判一次 [A: `sam3/tools/sam3_mask_judge.py:37-45,109`；`auto_mask/pipeline_lerobot.py:1174,1194`]。
4. **合成/渲染**：按指令把保留物体的掩码取并集；训练集最终用 `outside_scale=0.1` + 2 px 白边（`outline` 样式），评审图用 0.2 [A: `mask_style.py`；`README.md` §Mask semantics]。
5. **产物**：2,500 episodes / 548,893 帧 / 250,000 指令槽；发布 HF 数据集 6.14 GiB（judged multi）[A: SST README；HF 数据集卡]。

**关键点**：SST 的"前景"不是检测框，而是**逐短语实例掩码的并集**；策略输入被改成"目标物体保留、其余变暗"，而教师分支仍看原图 [A: `inference/cam_high_masker.py` docstring；README §pipeline]。

### 6.3 在线评测链

- `sam3/tools/sam3_stream_tracker.py` 把官方**离线**视频 API 改造成**因果流式**：每个 rollout 只喂已观测帧，`num_frames` 随帧增长，保证不偷看未来；每步返回当前帧的并集掩码 [A: docstring 与实现]。
- 与离线训练集的差异被明确写出：离线 `hotstart_delay=15` 会压住前 15 帧的输出，在线不能等；在线掩码在物体被 hotstart 启发式移除后从该帧起消失 [A]。
- `sam3/tools/sam3_stream_server.py` 是 HTTP 服务：`/start`、`/step`、`/end`，以及带 Qwen 评审的 `/start_judged`、`/step_judged`；一个进程独占一张 GPU，GPU 工作用锁串行化；`client_id` 防止重启客户端泄漏会话 [A]。
- 评测时 `inference/cam_high_masker.py` 复现训练时的 `outside_scale`/outline 规则，串行调用 Qwen 提词（`auto_mask.pipeline.extract_operation_objects`）与 SAM3 服务 [A]。
- `base.json`：`inference.gpu="1"`、`memory_window=10`、`qwen.gpu="0,1,2,3"`、`tensor_parallel_size=4`；`tools/services.py` 在启动 SAM3 时固定 0.3/0.5 阈值与 judge 参数 [A]。

### 6.4 提示词契约

- 73 行，英文；要求"每个短语是 SAM3 真正认识的词"，给出逐类词表与反例（例如 hammer 要同时输出 `black object`；pad/mat/skillet/bin/rack/stamp/seal/switch/scanner/sign 等标为 `MISSED`）[A: `vllm_space/sam3_prompt.py`]。
- 这证明：SST 的方法**依赖按物体集的提示工程**，且他们自己承认 SAM3 的词表缺口是方法的一部分 [A: 词表内容；C: 迁移判断]。
- 词表是英文，SAM3 文本编码器是 CLIP BPE 词表（`bpe_simple_vocab_16e6.txt.gz`）[A: `sam3/model/tokenizer_ve.py`]；中文指令需要先翻译成英文短语，且翻译质量会进入分割误差 [C]。

### 6.5 许可证与打包

- `sam3/LICENSE` 是 **SAM License**（2025-11-19）：允许使用、复制、分发、修改；再分发必须附带同一协议；禁止逆向；禁止 ITAR/军事/核/间谍/枪械等用途；Meta 可终止 [A: `sam3/LICENSE`]。
- **打包元数据与许可证不一致**：`sam3/pyproject.toml` 的 classifier 写的是 `License :: OSI Approved :: MIT License`，而实际 `license = {file = "LICENSE"}` 与 GitHub API 的 `license: other / NOASSERTION` 都指向 SAM License [A: `sam3/pyproject.toml`；GitHub API]。任何"SAM3 是 MIT"的判断都是错的。
- SST 根目录**没有 LICENSE**，其自有增量（`auto_mask/`、`tools/`、`inference/`、`data_inputs/`）没有授权 [A: 既有审计 `references/manipulation/sst-repo-audit.md`]。**不能把 SST 的适配代码复制进 JCHENG**；上游 `sam3/` 也应按 SAM License 处理 [A/C]。

### 6.6 工程质量与可复现性

- **强项**：阈值/样式/评审参数都显式配置；离线与在线掩码语义的差异写在 docstring 里；有缓存签名（`PROMPT_VERSION`）与评审日志；有 CPU 单元测试 [A]。
- **弱点**：`base.json` 含作者机器的绝对路径（`/home/pc/miniconda3/...`、`/data1/szh/...`）；4 套 conda 环境；vLLM 需源码编译；无 CI；评测需要 8 GPU × 4 slot + 27B 服务 [A: 既有审计]。
- 上游侧的可复现性风险：`sam3.1_multiplex.pt` 的加载路径问题 #526 仍 open；3.1 的显存增长在用户侧被复现（#542、#408）[A/B]。

### 6.7 静态 vs 已执行

| 结论 | 性质 |
|---|---|
| SST 的调用链、阈值、词表、评审逻辑 | 静态（文件 + 行号） |
| 2,500 episodes / 548,893 帧 / 250,000 槽 | SST 发布计数（A，未独立复算） |
| 3060 上 3.1 比 3.0 慢、显存更高 | 用户自报（B，未复现） |
| 6 GB 能否跑我们的场景 | **未验证**（D） |

---

## 07. Comparative Analysis（横向比较）

| 方案 | 文本提示 | 掩码 | 视频跟踪 | 规模 | 6 GB 可行性 | 许可证 | 集成成本 |
|---|---|---|---|---|---|---|---|
| **SAM 3.0（image）** | 是（英文名词短语） | 强 | 否（image 模式） | 848M / 3.45 GB | 可能，需 504–672 px [C] | SAM License，gated | 中：新服务 + 提示词 |
| **SAM 3.0（video）** | 是 | 强 | 是 | 同上 + 记忆 | 紧：短序列/单物体 [C] | 同上 | 高：流式封装 |
| **SAM 3.1（multiplex）** | 是 | 强 | 是（多物体快） | 3.5 GB | 更紧；1–3 物体负优化 [B] | 同上 | 高；#526 加载风险 |
| **SAM 3.0 + box prompt** | 否（用 YOLO 框） | 强 | 否 | 848M | 同 image | 同上 | 低–中：复用现有 YOLO |
| **SAM2.1 tiny/small + GroundingDINO** | 是（经检测器） | 强 | 是 | 38.9–46M + 检测器 | 较稳 | Apache-2.0 | 中：两模型 |
| **SAM2.1 + 现有 YOLO 框** | 否 | 强 | 是 | 38.9–46M | 稳 | Apache-2.0 | 低：只加掩码头 |
| **现有 YOLO（检测/分割）** | 否（固定类） | 框/粗掩码 | 否 | 小 | 已运行 | 仓库现状 | 零 |
| **YOLO-World** | 是 | 框 | 否 | 小 | 稳 | **GPL-3.0** | 不可用（许可评审） |
| **YOLOE** | 是 | 框/掩码 | 否 | 小 | 稳 | **AGPL-3.0** | 不可用（许可评审） |

**可比性**：SAM3 的"文本→所有实例掩码"能力是 SAM2.1/YOLO 组合没有的；但 SAM2.1+YOLO 框在我们的已知物体场景里能达到相近的掩码质量，且显存/许可更友好 [C]。SST 的完整栈（SAM3 + 27B judge + 8 GPU）与任何单模型方案都不可直接比较 [A]。

**隐藏成本**：
- SAM3 的提示词工程（逐类词表、颜色、`MISSED`）是持续成本 [A: SST]。
- SAM3 的 gated 权重意味着每次新机器部署都要人工接受许可、管理 token [A: HF]。
- SAM3.1 的加载/显存问题意味着版本升级不是免费的 [A/B: #526、#542]。

---

## 08. Critical Findings（关键发现）

**F1. SST 的 SAM3 是"数据引擎"，不是"运行时组件"。** 其数据链需要 Qwen-27B 提词 + 27B judge + 多 GPU SAM3 worker；发布物是数据集，不是可部署服务 [A: `auto_mask/pipeline_lerobot.py`、`tools/services.py`、`base.json`]。把 SST 的形态当作"接一个 SAM3 节点"会低估一个数量级的工程成本 [C]。

**F2. SAM3 的零样本能力被 SST 自己的词表证伪了一半。** 73 行词表里大量 `MISSED` 与颜色备份，说明在他们的物体集上"直接写类别名"并不稳定；换物体集要重做词表 [A: 词表；C: 迁移]。这是本报告最重要的反例。

**F3. 3.1 不适合我们的物体数。** 1–3 物体时 3.1 更慢、显存更高（维护者评论 + 3060 用户实测）[B]；4+ 物体才有收益 [A: release notes]。我们的典型场景是 1 个目标 + 1 个容器，应固定 3.0 [C]。

**F4. 6 GB 的瓶颈是激活与视频记忆，不是权重。** bf16 权重约 1.7 GB；1008 px 图像模式的激活、以及视频每物体每帧约 3 MB（float32）会推高峰值 [A: 参数量算术；B: #408]。降低分辨率（504）能把 3090 的编码从 110 ms 降到 46 ms [B: #424]，但掩码质量会下降，需要实测 [D]。

**F5. 消费级延迟远高于论文的 H200 数字。** 4090 + ORT-TRT 在 600×500、多提示批量下仍约 1.1 s/图 [B: #424]；3090 PyTorch bf16 单物体 1008 px 约 153 ms（编码+文本+跟踪）[B]。不要用 30 ms 做容量规划 [A/C]。

**F6. SAM3 权重是 gated + SAM License，不是 MIT。** `facebook/sam3`、`facebook/sam3.1` 都是 `gated: manual`，需要登录并同意共享 HF 信息 [A: HF API]；`pyproject.toml` 的 MIT classifier 是错的 [A]。再分发受 SAM License 约束 [A]。

**F7. 上游 3.1 的工程质量有可见风险。** #526（3.1 权重加载路径）仍 open；#542（3060 上 3.1 视频 1 小时）被关闭但未修复根因；#408（流式显存增长）仍 open [A/B]。

**F8. 掩码不等于抓取位姿，也不修复我们的主要误差。** SAM3 给 mask/box/score；抓取点仍需 mask 质心/主轴 + 深度反投影 + 手眼标定。当前跨视角 10–14 mm 的残差比掩码边界误差更大 [A: 记忆中的感知证据；C: 误差归因]。

**F9. 提示词语言是英文，且会影响误差。** CLIP BPE 词表 + SST 全英文词表 [A]；中文指令需翻译，翻译歧义会直接进入分割 [C]。

**F10. SST 发布的是 RoboTwin 仿真赛道，不含决赛真机栈。** 仓库目录与 README 只覆盖 RoboTwin 数据/训练/评测；没有真机驱动、DDS 或总线代码 [A: 树与 README；C: "不含真机"是推断]。因此不能从该仓库"抄"一个真机 SAM3 部署。

**什么会改变结论**：
- 若 MVE-0 在 6 GB 上 504 px、单物体、图像模式稳定 ≥2 fps 且峰值 <5.5 GB，且 MVE-1 的掩码质量在自有帧上明显优于 YOLO 框，则"顾问式服务"值得进入 MVE-2。
- 若 MVE-1 显示提示词需要逐类手工修补（像 SST 那样），则 SAM3 的边际价值低于 SAM2.1+YOLO 框，应回退。
- 若 HF 访问长期不可得，则整条 SAM3 路线降级为"观察"，先做 SAM2.1 回退路线。

---

## 09. Engineering Applicability（工程适用性）

### 9.1 三种接入形态

| 形态 | 位置 | 数据流 | 运动影响 | 风险 | 建议 |
|---|---|---|---|---|---|
| **离线标注/评估** | 笔记本，批处理 | 读帧/视频 → 掩码 → 存盘 | 无 | 低 | **先做** |
| **顾问式服务** | 笔记本 GPU 节点 | HTTP/JSON → 掩码/目标点 → 感知 advisory | 无（仍由 system 层决定） | 中 | 门禁通过后做 |
| **闭环控制** | 感知→策略→运动 | 掩码进策略输入 | 有 | 高 | **不做** |

### 9.2 资源估算（6 GB 笔记本 3060）

| 项 | 估算 | 等级 |
|---|---|---|
| 权重（bf16） | ~1.7 GB | A（848M×2 B） |
| 1008 px 图像模式峰值 | ~4–6 GB | C（用户报告 4–12 GB 区间） |
| 504 px 图像模式峰值 | ~2.5–4 GB | C |
| 视频（单物体、100 帧、504 px） | 峰值再 +0.3–1 GB | C（#408 的 3 MB/帧/物体） |
| 磁盘 | 权重 3.45 GB + torch ~3 GB + 依赖 ~1 GB | A/C |
| 延迟（504 px，单物体） | ~0.1–0.25 s/帧 | C（3090 的 1/3） |
| 延迟（1008 px，单物体） | ~0.3–0.6 s/帧 | C |

### 9.3 安全与边界

- 任何形态都**不得**发布 vendor 话题、打开设备、加入 41/42/43 域；顾问式服务只经 HTTP 或既有感知通道输出 advisory [A: 工作区 `AGENTS.md` §3]。
- 不引入 lease、不调用 `ExecuteMotion`、不改变 stop latch [A]。
- 实机验证必须单独授权；MVE-2 之前不做任何运动测试 [A: 工作区 `AGENTS.md` §7]。

### 9.4 回退

- 代码回退：服务是独立进程，停掉即回到现有 YOLO 链路。
- 数据回退：离线掩码只写 `evidence/` 或 `/opt/jcheng/models/` 之外的临时目录，不进 git。
- 许可证回退：若 SAM License 评审不接受，删除权重与代码，改用 Apache-2.0 的 SAM2.1 路线。

---

## 10. Recommended Approach（推荐方案）

### 10.1 推荐：路线 A — 三段式离线优先尝试

1. **MVE-0（0.5–1 天，离线）**：在 6 GB 3060 上测 SAM 3.0 图像模式的显存/延迟，分辨率 1008/756/504，单物体与双物体；再测 50–100 帧短序列视频。**门禁 G0**：504 px、单物体、峰值 ≤5.5 GB、≥1 fps。
2. **MVE-1（1 天，离线）**：用 `jcheng-perception` 现有证据帧/标定采集帧，比较三种输入——(a) 文本短语、(b) YOLO 框 + box prompt、(c) SAM2.1-tiny + YOLO 框；人工框作参照，算 mask IoU、质心误差、提示词变体稳定性。**门禁 G1**：质心误差 < 物体短边的一半，且 ≥80% 帧稳定；否则回退。
3. **MVE-2（2–3 天，离线+顾问）**：把通过的形态包成 HTTP 服务，按现有 YOLO GPU 节点的模式接入感知；只发 advisory，不接运动；用录制帧回放验证 30 分钟稳定性与 p95 延迟。**门禁 G2**：30 分钟无泄漏/无崩溃、p95 <1 s；之后才讨论单次、单独授权的实机抓取。

### 10.2 备选

- **路线 B（回退）**：SAM2.1-tiny/small（Apache-2.0）+ 现有 YOLO 框，做掩码细化/质心；不引入文本提示与 gated 权重。适合"只想要更好的掩码"的场景 [C]。
- **路线 C（只做标注）**：SAM3 仅离线给自有帧打掩码，用于评估 YOLO、做数据治理、为未来数据集合成前景；不进任何运行时 [C]。
- **路线 D（维持现状）**：继续用 YOLO + 标定改进；把预算投到跨视角残差与动作标签，而不是新分割器 [C]。

### 10.3 不推荐

| 选项 | 原因 |
|---|---|
| SAM3 跑在 Pi 5 上 | 848M 参数、无 CUDA；不现实 [A/C] |
| SAM3 进闭环控制 | 新增分布外环节；我们的主要误差是标定，不是类别覆盖 [C] |
| SAM3.1 multiplex | 1–3 物体负优化；加载路径有 issue [A/B] |
| Qwen-27B judge | 资源不匹配；它只能否决候选，不能补回漏检 [A: SST judge 逻辑] |
| 复制 SST `auto_mask/`/`inference/` | SST 自有代码无授权 [A] |
| 用非官方镜像下载 gated 权重 | 违反 gating 意图与 SAM License [A] |

---

## 11. Experimental Design（实验设计）

完整设计见 [experiments/20261126-sam3-6gb-feasibility/design.md](../experiments/20261126-sam3-6gb-feasibility/design.md)。**四个 MVE 均未运行**；MVE-0 有一个用户侧前置动作（HF 许可接受 + token），未完成前不能开始。

| MVE | 假设 | 环境 | 主要指标 | 验收 | 失败判据 | 状态 |
|---|---|---|---|---|---|---|
| **MVE-0** | 6 GB 能跑 SAM 3.0 image @504，单物体 ≥1 fps | 本机 3060 6 GB；torch cu128；SAM 3.0 权重 | 峰值显存、p50/p95 延迟、OOM 率 | 峰值 ≤5.5 GB，≥1 fps | OOM 或 <0.5 fps | 未运行（缺 HF 授权） |
| **MVE-1** | 文本提示与 box prompt 在自有帧上可用 | 同上 + 20–30 帧证据图 | mask IoU、质心误差、提示词稳定性 | ≥80% 帧稳定；质心误差 < 短边一半 | 需逐类手写词表 | 未运行 |
| **MVE-2** | 顾问式 HTTP 服务可稳定接入感知 | 同上 + 录制回放 | 30 min 稳定性、p95、内存增长 | 无崩溃/泄漏，p95 <1 s | 会话泄漏或延迟漂移 | 未运行 |
| **MVE-3** | SAM3 离线标注的性价比高于 SAM2.1 | 同上 | 每帧成本、掩码质量、人工修正时间 | 明显优于 SAM2.1 才继续 | 无显著优势 | 未运行 |

**记录方式**：每个 MVE 在 `experiments/20261126-sam3-6gb-feasibility/` 下建 `data/`（CSV/JSON，不含图像/权重）与 `logs/`（命令、版本、时间戳）；结果写 `result.md`；权重放 `/opt/jcheng/models/sam3/`（不进 git）。

**回退**：MVE-0 失败 → 路线 B/C；MVE-1 失败 → 路线 B/D；MVE-2 失败 → 停服务、回 YOLO。

---

## 12. Limitations & Uncertainties（局限与不确定）

1. **没有运行 SAM3**：本报告的 6 GB 判断是算术 + 他人实测的外推（C），不是本机结果。MVE-0 是唯一能关闭它的实验。
2. **没有 HF 授权**：`facebook/sam3`、`facebook/sam3.1` 都是 manual gating；本机无 token。需要用户登录 HF、接受 SAM License、生成 read token 后才能下载 [A]。
3. **issue 证据是用户自报**：3060/3090/4090 的数字没有统一测法（分辨率、精度、是否含预处理、是否批量），只能作区间参考（B）。
4. **论文只读了 HTML 正文与 Limitations**：没有复现 SA-Co，也没有核对每个表格；论文数字按作者主张处理（A，作者主张）。
5. **SST 仓库不含真机栈**：其 SAM3 经验来自 RoboTwin 仿真与离线数据；真机相机、光照、运动模糊下的表现未知（C/D）。
6. **提示词语言**：本报告假设中文指令需翻译成英文短语；翻译质量对掩码的影响未测（D）。
7. **许可证评审未关闭**：SAM License 的可接受性、以及 gated 权重在团队内的管理方式，需要法务/所有者判断；本报告只陈述条款，不给法律结论。
8. **版本漂移**：上游 main 在 2026-11-17 仍在变；3.1 的加载问题可能被修复，也可能引入新问题；本报告 pin 在 `31cb7e62`。

---

## 13. References（参考文献）

1. Carion, Gustafson, Hu, et al. *SAM 3: Segment Anything with Concepts*. arXiv:2511.16719, v1 2025-11-20, v2 2026-03-28. <https://arxiv.org/abs/2511.16719>
2. `facebookresearch/sam3`, main `31cb7e62`（2026-11-17 push）。<https://github.com/facebookresearch/sam3>
3. *RELEASE_SAM3p1.md*（SAM 3.1 Object Multiplex，2026-03-27）。<https://github.com/facebookresearch/sam3/blob/main/RELEASE_SAM3p1.md>
4. `facebook/sam3` Hugging Face 模型卡（gated: manual；`sam3.pt` 3.45 GB；F32 3.44 GB / 859,922,360 参数）。<https://huggingface.co/facebook/sam3>
5. `facebook/sam3.1` Hugging Face 模型卡（gated: manual；`sam3.1_multiplex.pt` 3.5 GB）。<https://huggingface.co/facebook/sam3.1>
6. sam3 issue #542, *SAM 3.1 Low inference compared to SAM 3*（2026-05-06）。<https://github.com/facebookresearch/sam3/issues/542>
7. sam3 issue #424, *SAM3Image inference latency remains ~1.1s on RTX 4090 with TensorRT EP*（2026-01-22）。<https://github.com/facebookresearch/sam3/issues/424>
8. sam3 issue #408, *Streaming Version of SAM3*（2026-01-14）。<https://github.com/facebookresearch/sam3/issues/408>
9. sam3 issue #526, *`sam3.1_multiplex.pt` has zero `build_*` path that loads cleanly on public `main`*（2026-04-20）。<https://github.com/facebookresearch/sam3/issues/526>
10. `facebookresearch/sam2`（Apache-2.0；2.1 变体 38.9/46/80.8/224.4M）。<https://github.com/facebookresearch/sam2>
11. `IDEA-Research/Grounded-SAM-2`（Apache-2.0 + 组件许可）。<https://github.com/IDEA-Research/Grounded-SAM-2>
12. `IDEA-Research/GroundingDINO`（Apache-2.0）。<https://github.com/IDEA-Research/GroundingDINO>
13. `AILab-CVC/YOLO-World`（GPL-3.0）。<https://github.com/AILab-CVC/YOLO-World>
14. `THU-MIG/yoloe`（AGPL-3.0）。<https://github.com/THU-MIG/yoloe>
15. `PINTO0309/SAM3-TensorRT`（MIT；3090 4K 438→75 ms）。<https://github.com/PINTO0309/SAM3-TensorRT>
16. `embedl/sam3`（gated；L4 TRT FP16 137→104 ms；INT8 精度接近）。<https://huggingface.co/embedl/sam3>
17. `kengboon/sam3_openvino`（duplicated from `rajeshgangireddy/SAM3_OpenVINO`；fp16 1.63 GB；Intel XPU ~452 ms/图）。<https://huggingface.co/kengboon/sam3_openvino>
18. `YzmYalier/Lingbot-Challenge-SST`, commit `8797aa31`。<https://github.com/YzmYalier/Lingbot-Challenge-SST>
19. SST 数据集 `yydsyangsdyy/Lingbot-Challenge-SST`，revision `7111c72`。<https://huggingface.co/datasets/yydsyangsdyy/Lingbot-Challenge-SST>
20. 本仓库既有报告：[LingBot-VLA 2.0 / SST 前景提示配方评估](20261125-lingbot-vla-sst-foreground-prompting.md)。
21. 本仓库来源记录：[SAM 3](../references/perception/sam3.md)、[SST 仓库审计](../references/manipulation/sst-repo-audit.md)。
22. 工作区约束：工作区根 `AGENTS.md`（`~/jcheng/AGENTS.md`，不在本仓库）（分层、DDS 域、安全、模型权重存放）。

---

## 自审

| 问题 | 检查结果 |
|---|---|
| 是否存在确认偏误？ | 已主动寻找反例：SST 词表证伪"零样本即用"；#542 证伪"3.1 全面更快"；#424 证伪"消费级实时"；许可证与 gated 权重限制引入成本。 |
| 是否遗漏明显替代方案？ | 已比较 SAM2.1、Grounded-SAM-2、YOLO-World/YOLOE（许可不可用）、现有 YOLO、SAM3+box prompt。 |
| 是否混淆相关性与因果？ | SST 的成功率增益归因于其完整配方，不是单独 SAM3；本报告没有声称"SAM3 提升抓取成功率"。 |
| 是否存在未经验证的技术假设？ | 6 GB 可行性、3060≈3090/3、504 px 质量下降均为 C/D，已标注并交给 MVE-0/1。 |
| 是否过度解读论文实验？ | 论文数字按作者主张（A），未当作本平台结论；H200 延迟明确标注不可用于容量规划。 |
| 是否把 README 当真实实现？ | 代码结论均给文件/行号；README 只用于版本与发布说明；SST 未执行，已标注静态。 |
| 是否有虚构引用或实验结果？ | 所有外部链接为本次实际访问的页面/API；MVE 全部标注"未运行"。 |
| 推荐方案是否适合当前项目？ | 推荐"离线优先 + 顾问式"，不触碰运动链；回退路径明确；许可证与 gated 权重列为前置条件。 |
| 结论是否足以指导下一步？ | 是：下一步是用户接受 HF 许可 + token，然后跑 MVE-0；否则转路线 B/C。 |
