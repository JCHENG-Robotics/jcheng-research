# AGX Orin 上 SAM3 + Qwen 部署可行性调研与尝试路线

> 报告状态：**draft**（draft | reviewed | superseded）。日期：2026-11-26。
> 作者：ZCode（研究代理），for J. Cheng。评审：pending。
> 本报告影响的决策：是否把 AGX Orin 作为 SAM3 + Qwen 的推理主机；用哪条软件栈、哪个 Qwen 规模、先做什么实验。
> 研究主题：Jetson AGX Orin 上部署 SAM 3（分割/跟踪）与 Qwen（提示词提取/掩码评审）的可行性、性能边界与最小尝试路线。
> 研究边界：**已在 2026-11-26 用 `ti5robot@192.168.5.31` 登录并完成只读探测**（64GB、JetPack 6.2 / L4T 36.4.4、CUDA 12.6、TensorRT 10.3、Python 3.10、无 torch、MAXN、782GB 空闲）；**尚未在 Orin 上运行 SAM3/Qwen**；SAM3 的 Orin 数字来自第三方 TensorRT 基准（B 级）；Qwen 的 Orin 数字来自 NVIDIA TensorRT Edge-LLM 官方基准（A 级，但为 v0.8.0、单图、2048 输入，且 Edge-LLM 官方只支持 JetPack 7.2）；SAM3 论文与仓库事实沿用 [2026-11-26 SAM3 报告](20261126-sam3-sst-open-source-attempt-route.md)。

**证据等级**：**S** 本机实测 · **A** 一手论文/官方仓库/官方文档/官方基准 · **B** 可信间接工程证据 · **C** 推断 · **D** 未验证假设。

## 00. 实测快照（2026-11-26，S 级）

| 项 | 实测值 |
|---|---|
| 主机 | `ubuntu`，aarch64 |
| 系统 | L4T **R36.4.4** = **JetPack 6.2**；Ubuntu 22.04.5 |
| 内存 | 62,841 MB（约 61 GiB），空闲 56 GiB；swap 30 GiB |
| CPU | 12 核；`nvpmodel` = **MAXN (0)**；governor `schedutil` |
| CUDA / TensorRT | CUDA **12.6.11**；TensorRT **10.3.0.30**；`tensorrt` Python 10.3 |
| Python / 框架 | Python 3.10.12；**无 torch**；有 numpy 1.24、onnx 1.20、onnxsim、onnx_graphsurgeon、opencv 4.12 |
| 容器 / 权限 | Docker 29.10；**passwordless sudo 可用**；无运行中容器 |
| 磁盘 | 915 GB，已用 91 GB，**可用 782 GB** |
| 网络 | `eno1 192.168.5.31/24`；笔记本 `192.168.5.22` 可达（1.9 ms）；**pypi.org / huggingface.co 直连超时**；清华镜像 200（约 1.6 MB/s）；NVIDIA 中国站 307 |
| 已装工具 | git 2.34、cmake 3.22、gcc 11.4；**无 llama.cpp / ollama / transformers**；无模型文件 |

**对结论的修订**：

1. **64GB 已确认**，MAXN 已开；内存不是瓶颈。32GB 分支不再适用。
2. **本机是 JetPack 6.2，不是 7.2**。Edge-LLM 官方 Orin 支持是 7.2；本机若用 Edge-LLM 只能走 6.2 的兼容/实验路径，因此 **Qwen 首选 llama.cpp**，Edge-LLM 留到升级 7.2 之后 [A/S/C]。
3. **TensorRT 10.3 恰好是 Embedl 验证 SAM3 的版本**，SAM3 的 TRT 路径在本机更顺；但系统 Python 无 torch，而 anaconda `human_interaction_env` 有 **torch 2.8.0（CUDA 可用）**，SAM3 已在其 venv 中跑通 import；GPU 加载目前受电源阻塞 [S/C]。
4. **Orin 不能直连 PyPI/Hugging Face**；下载走"笔记本 → scp 到 Orin"，或清华镜像（纯 Python 包）[S]。
5. **有 passwordless sudo 和 Docker**，容器路线可用，但 native 构建更简单 [S]。
6. **Qwen3-VL-8B 已部署成功**（llama.cpp Q4_K_M + Q8_0 mmproj）：1 图 1.95 s、2 图 2.64 s、2 图 yes/no + logprobs 中位 1.18 s；`logprobs` 可用；进程 RAM 约 12.1 GB [S]。
7. **首次 GPU 全 offload 的硬重启未复现**：机器本身有 crash 历史（11-23/11-25/11-26 09:10），已启用持久 journal；后续 5 种 GPU 配置均通过 [S]。
8. **SAM3 GPU 加载曾触发第二次硬重启（11:28）**：`sam3.pt` 3.45 GB 进 GPU 期间整机复位；与 llama.cpp 10:46 的首次全 GPU 加载同一模式 [S]。
9. **19V 供电已验证（S）**：接 19V/4.74A 后 `VDD_GPU_SOC/VDD_CPU_CV` 从 11.76 V 升到 **19.17 V**；30 s 压力 44.4 W、Qwen 5 GB 加载、SAM3 3.45 GB 加载与 20 次推理全部稳定。12V 适配器是两次硬重启的原因（强证据）[S]。
10. **SAM3 GPU 已跑通**：`Sam3Processor(resolution=1008)` + `torch.autocast("cuda", bfloat16)`；加载 16.07 s、编码 0.69 s、20 次提示中位 **0.202 s**、VRAM **5.34 GB**；`orange can` score 0.902，`can`/`beverage can` 0 个（需具体提示词）[S]。
11. **货架数据集端到端 + 校准（S/B）**：`~/dataset`（LeRobot v3，`1003/1014/1015` = 278/64/41 episodes，3 相机）取 front 帧；SAM3 对 green/orange/clear bottle、coca cola、snack bag、red can、shelf 均出多实例。易分 40 对：文本与阈值 0.5 均 **40/40**；无歧义硬负例 60 对：**60/60**（p_yes 最小 0.9903 / 错误例最大 0.022）；歧义硬负例 60 对：**47/60 = 78.3%**。**之前"logprob 不可用"是聚合 bug**（按最后一个而非最大值）；修正后分离正常。
12. **50 帧流水线（S）**：5 个互斥提示轮换、每帧 1 掩码 + Qwen；57 个有效对 **56/57 = 98.25%**；端到端 p50 **3.84 s** / p95 6.56 s；3 帧 NO_MASK；唯一错误是画面左边缘被裁掉的绿瓶局部（score 0.91），属**边缘/局部掩码**假阴性。建议加边框/局部过滤。
13. **100 帧 + wrist（S）**：front 50 + wrist_left 50；4 px 硬边框过滤误杀 34 个合法边缘/近距离掩码（front chip bag 10、wrist 瓶 23）；改用 SST 的 "object, or a part of it?" 重测 34 个 partial：**32/34 yes（94.1%）**；合计 **79 judged / 77 yes = 97.5%**；front p50 1.46 s、wrist p50 3.84 s；wrist no-mask 18/50。**不要用硬边框过滤。**
14. **Wrist 100 帧多 episode（S）**：file000/file001 各 50，提示 `bottle`，part-aware，无边框过滤；**89 valid / 88 correct = 98.9%**；25 no-mask；唯一错误是顶边被裁掉的橙瓶上半部（score 0.973，p_yes 0.037）；e2e p50 3.76–3.83 s、Qwen p50 2.52–2.59 s；`bottle` 14/15 是最佳 wrist 提示（`gripper`/`black gripper` 0）。
15. **Judge 模板敏感性（S）**：12 掩码 × 3 模板，T1 9/11、T2 8/11、T3 7/11（不含 ambig）；f19 T1 yes / T2/T3 no；hard1 T1/T2 no / T3 yes；低分掩码（0.754–0.762）最易翻转。**之前 40/40、60/60、98.9% 都是特定模板 + 特定样本的结果**，不能跨模板比较。建议固定 **T1 + SAM3 score≥0.8** 门禁，低分跳过/标 uncertain。
16. **T1+score≥0.8 策略验证（S）**：18 案例 **15 judged / 15 correct**、3 skipped（easy_clear 0.754、hard_clear 0.754、right wrist 0.762）；覆盖率 15/18，低分/强局部仍需人工或第二视角兜底。
17. **200 帧固定策略稳定性（S）**：frontA/B+wristA/B 各 50；**183 judged / 182 correct = 99.45%**；16 个反例全对；唯一错误是 f21 左边缘绿瓶（score 0.91，T1 no）；30 NO_MASK + 3 低分跳过；e2e p50 3.93 s；无重启。
18. **顾问式 HTTP 服务（S）**：127.0.0.1:8090；60 请求 58 judge / 2 no-mask；p50 **2.04 s** / p95 2.08 s；health model/qwen true；RSS 1.39→2.09 GB/220 s；无崩溃；只发 advisory，无 DDS/运动。
19. **30 min soak（S）**：180 请求 / 0 error / 162 judge / 18 no-mask；p50 1.04 s、p95 2.32 s；服务 RSS 2,106→2,109 MB、Qwen 9,279→9,286 MB（平台化）；无崩溃；free 下降来自其它进程/缓存。
20. **500 请求压测（S）**：0 error / 427 judge / 8 skip / 65 no-mask；p50 **2.11 s**、p95 **3.77 s**、max 4.02 s；服务 RSS +3 MB、Qwen +12 MB；health model/qwen true；无崩溃；200 帧池复用 2.5 轮，不是 500 个唯一帧。
21. **500 唯一帧 + 跨机 LAN（S）**：0 error / 412 judge / 7 skip / 81 no-mask；p50 **2.15 s**、p95 **3.74 s**、max 4.03 s；服务冷启动 1,387→2,086 MB 后平台、Qwen 平台；与回环 500 请求差异 ≤0.04 s（Wi-Fi 不是瓶颈）；G4 p95<1.5 s 仍未达。

---

## 01. Executive Summary（执行摘要）

**推荐：这台 64GB AGX Orin 已能同时跑 Qwen3-VL-8B（llama.cpp）与 SAM 3.0（PyTorch，1008 px + bf16 autocast）：SAM3 加载 16 s、编码/提示 ~1 s、每次提示 0.20 s、VRAM 5.34 GB；Qwen 2 图评审 1.18–2.62 s。19V/4.74A 供电是稳定前提；12V 会在 GPU 模型加载时硬重启。货架校准：易分 40/40；无歧义硬负例 60/60；歧义负例 47/60；50 帧 56/57；100 帧 front+wrist part-aware 97.5%；wrist 100 帧多 episode 88/89 = 98.9%（`bottle` 提示；顶边局部仍会漏）。**

支撑结论的五条事实：

1. **Orin 的算力/内存足以容纳这条栈。** AGX Orin 64GB：2048 CUDA / 64 Tensor Core、12 核 CPU、64GB LPDDR5 @204.8 GB/s、275 TOPS、15–60W；32GB：1792 / 56、8 核、32GB @204.8 GB/s、200 TOPS、15–40W [A: NVIDIA 产品页/数据手册]。统一内存意味着 SAM3（FP16 ~1.7 GB 权重）和 8B VLM 可以共存，不存在 6 GB 笔记本那种硬墙 [A/C]。
2. **SAM3 在 Orin 上有可用的 TensorRT 数字。** Embedl 在 AGX Orin 上测得 SAM3 输入 924 px：FP16 baseline **763 ms / 1.31 QPS**，INT8+FP16 混合 **462 ms / 2.17 QPS** [B: Embedl HF 模型卡]。这比 6 GB 笔记本的估算更可信，且足以支撑"离线/顾问式 1–2 fps"。
3. **Qwen3-VL-8B 已在本机实测跑通（llama.cpp）。** 本机 JetPack 6.2 不在 Edge-LLM 的官方 Orin 轮子矩阵内（其官方支持是 7.2；AGX Orin 64GB 上 4B 52.2 tok/s / 9.9 GB、8B 32.2 tok/s / 13.1 GB、27B 10.5 tok/s / 24 GB）[A: Edge-LLM v0.8.0]。改用 llama.cpp（CUDA 12.6、sm_87）后，Qwen3-VL-8B Q4_K_M + Q8_0 mmproj：1 图 1.95 s、2 图 2.64 s、**2 图 yes/no + logprobs 中位 1.18 s**；`logprobs` 可用；进程 RAM 约 12.1 GB [S]。
4. **SST 的原栈不能照搬。** SST 用 vLLM 服务 Qwen3.8-27B，并依赖 logprob 做评审；vLLM 官方不支持 Jetson（文档只覆盖 x86 与 Grace/Blackwell ARM），Edge-LLM 的 OpenAI 服务文档也没有 logprobs 字段 [A: vLLM 文档；A: Edge-LLM 文档]；但 llama.cpp 的 OpenAI 接口实测支持 `logprobs` [S]。27B 在 64GB 上能跑，但 10.5 tok/s、24 GB 显存，吞吐不适合交互；在 32GB 上不可行 [A/C]。
5. **真正的收益是"离线可跑"，不是"实时闭环"。** 以 462–763 ms/帧估算，SST 的 548,893 帧全量重放需要 **70–116 小时**（仅 SAM3，不含 Qwen 与 I/O）；SST 用 8 GPU，Orin 只有一张 GPU [A: 计数；C: 算术]。因此 Orin 适合做**小规模试点、离线标注、顾问式目标**，不适合重建 SST 数据集或闭环控制 [C]。

**主要风险**：**judge 对模板措辞高度敏感**——同一掩码可翻转判决（f19 T1 yes / T2/T3 no；hard1 T1/T2 no / T3 yes），之前 40/40、60/60、98.9% 均为特定模板结果，不能跨模板比较 [S]。建议固定 **T1 + SAM3 score≥0.8** 门禁，低分跳过/标 uncertain。其余风险：SAM3 提示词敏感（`orange can` 0.902，`can` 0 个）[S/C]；924/504 px 不可用（RoPE）[S]；Orin 直连 PyPI/HF 不通 [S]。19V 供电已验证，不再是阻塞 [S]。

**一句话**：**Qwen + SAM3 已在 Orin 上跑通；judge 的模板敏感性是当前最大风险，先固定模板 + score 门禁，再谈规模化。**

---

## 02. Research Questions（研究问题）

**主问题**：在 AGX Orin 上部署 SAM3 + Qwen（提示词提取/掩码评审），哪条软件栈、哪个 Qwen 规模、什么性能，最小尝试路线是什么？

| # | 子问题 | 回答位置 |
|---|---|---|
| Q1 | AGX Orin 32GB/64GB 的算力、内存、功耗差异？ | §03、§07 |
| Q2 | SAM3 在 Orin 上怎么跑、多快、多少内存？ | §05.1、§06.1、§07 |
| Q3 | Qwen 在 Orin 上怎么部署、选哪个模型、多快？ | §05.2、§06.2、§07 |
| Q4 | SST 的 vLLM + 27B + logprob 评审能否照搬？ | §06.4、§08 |
| Q5 | 与 JCHENG 现有架构/网络怎么接？安全边界？ | §09 |
| Q6 | 最小可行实验与门禁？ | §11、[design.md](../experiments/20261126-agx-orin-stack-probe/design.md) |

**约束**：

| 类别 | 约束 |
|---|---|
| 硬件 | Orin 型号未知（32/64GB）；机器人侧 Pi 5 8GB；笔记本 RTX 3060 6GB；Orin 在 `192.168.5.31`，笔记本 `192.168.5.22`，机器人在 `10.42.0.x`（USB NIC，当前 DOWN） [S] |
| 软件 | Orin 的 JetPack 未知；机器人 Humble；本机 Jazzy/Python 3.12；无 `gh` CLI [S/A] |
| 安全 | 运动只经 `ExecuteMotion`；Orin 只能做感知/顾问，不得成为运动源 [A: 工作区 `AGENTS.md`] |
| 法务 | SAM3 是 SAM License + gated；Qwen3-VL 与 Edge-LLM 是 Apache-2.0；SST 自有代码无授权 [A] |
| 算力 | 单张 Orin GPU；不做训练/微调；只做推理与离线试点 [A/C] |

---

## 03. Current System Analysis（当前系统分析）

### 3.1 三台机器的角色

| 机器 | 当前事实 | 在本路线中的角色 |
|---|---|---|
| ArmPi Ultra / Pi 5 8GB | 厂商 Humble 栈、5-DoF 臂、D435i；感知节点在容器内；无 CUDA | 机器人控制与执行；**不加载 SAM3/Qwen** |
| 笔记本 RTX 3060 6GB | 现有 YOLO GPU 节点；CUDA 13.2 驱动；无 torch | 开发/对比；不适合常驻 4B+ 模型 |
| AGX Orin `192.168.5.31` | SSH 可达但密钥不被接受；型号/JetPack 未知；与笔记本同一 `192.168.5.0/24` | 候选推理主机；先离线，后顾问式 |

### 3.2 网络拓扑（已实测）

- 笔记本：`wlp4s0 192.168.5.22/24`，默认网关 `192.168.5.1`；Orin `192.168.5.31` 在同一网段（ARP REACHABLE）[S]。
- 机器人：`enx00e04ca373c7`（USB NIC）当前 **DOWN**，机器人地址 `10.42.0.218` 在不同子网 [S]。
- 含义：Orin 现在能到笔记本，但**不能直接到机器人**；如果未来要让 Orin 给机器人提供顾问目标，需要（a）笔记本做路由/NAT，（b）Orin 接入机器人网络，或（c）经笔记本中转 HTTP。第一阶段的离线实验不受影响 [C]。

### 3.3 安全边界

- Orin 只能输出 advisory（掩码/目标点/置信度）；不得发布 vendor 话题、不得打开设备、不得加入 41/42/43 域、不得调用 `ExecuteMotion` [A: 工作区 `AGENTS.md` §3/§7]。
- 任何实机运动仍需单独授权；Orin 的接入不改变这一点 [A]。

---

## 04. Research Methodology（研究方法）

### 4.1 检索策略

关键词：`Jetson AGX Orin 32GB 64GB specs`、`JetPack 7.2 CUDA TensorRT`、`TensorRT Edge-LLM Jetson Orin Qwen3-VL`、`SAM3 Jetson AGX Orin latency`、`SAM3 TensorRT Orin`、`vLLM Jetson sm_87`、`llama.cpp Qwen3-VL mtmd logprobs`、`Qwen3-VL model sizes license`。

检索顺序：NVIDIA 官方规格/JetPack → Edge-LLM 官方文档与基准（GitHub raw）→ SAM3 的 Orin 第三方基准（Embedl、PINTO0309）→ vLLM/llama.cpp/jetson-containers 的支持边界 → Qwen3-VL 官方仓库。

### 4.2 来源与阅读深度

| 来源 | 版本/日期 | 读到什么 | 等级 |
|---|---|---|---|
| NVIDIA Jetson AGX Orin 产品页 | 2026-11-26 | 32/64GB 的 TOPS、CUDA/Tensor Core、CPU、内存、功耗 | A（页面有排版错位，已交叉核对） |
| Jetson AGX Orin 数据手册 DS-10662-001 v1.5 | 2026-11-26 | 32GB：200 TOPS、1792 CUDA、939 MHz、15–40W；64GB：275 TOPS、2048 CUDA、1.3 GHz、15–60W | A |
| NVIDIA JetPack 页 | 2026-11-26 | JetPack 7.2、Ubuntu 24.04、kernel 6.8、CUDA 13.0（页面措辞） | A |
| TensorRT Edge-LLM docs | main，2026-11-26 | 支持矩阵（Orin/JetPack 7.2/CUDA 13.2/sm_87/FP16-INT8-INT4）、支持模型（Qwen2.5-VL/Qwen3-VL）、安装、OpenAI server、limitations | A |
| Edge-LLM 性能基准 | v0.8.0，JetPack 7.2 | AGX Orin 64GB 上 Qwen3-VL-2B/4B/8B、Qwen3.5-27B 的 prefill/ViT/生成/显存 | A（官方基准，单图、2048 输入） |
| Embedl SAM3 | 访问 2026-11-26 | AGX Orin 924 px：763 ms FP16 / 462 ms INT8+FP16；1.31/2.17 QPS；TensorRT 10.1/10.3 验证 | B（厂商基准） |
| PINTO0309/SAM3-TensorRT | 访问 2026-11-26 | ONNX→TensorRT；Orin NX 4K 6600→950 ms；MIT | B（README 自报） |
| Qwen3-VL 仓库 | 访问 2026-11-26 | 2B/4B/8B/32B/30B-A3B/235B-A22B；Apache-2.0；256K 上下文；多图 | A |
| vLLM 安装文档 | latest，2026-11-26 | 支持 CUDA 7.5+；ARM 只提 Grace/Blackwell；无 Jetson/sm_87 | A（支持边界） |
| llama.cpp server README | master，2026-11-26 | 多模态 `image_url`；`/completion` 有 `n_probs`；chat 的 logprobs 未明确 | A/B |
| jetson-containers | 访问 2026-11-26 | 支持 JetPack 6.2/7；含 vLLM/llama.cpp/Ollama/Transformers；无 Qwen 专门包 | B |
| SAM3 报告与来源记录 | 2026-11-26 | 848M、gated、3.1 负优化、SAM License、消费级延迟 | A |

### 4.3 排除与边界

- 不把搜索引擎摘要作为关键数字的唯一来源；所有关键数字回到 NVIDIA 文档/基准表、HF 模型卡或 GitHub 原文。
- 不比较不同精度/分辨率/批大小的"跑分"；Edge-LLM 的数字是 INT4 AWQ + 单图 + 2048 输入，SAM3 的数字是 924 px + TensorRT。
- 没有 Orin 实测；所有"能否跑"的结论都是 C/D，交给 §11 的探测与实验。

---

## 05. Literature Review（文献综述）

### 5.1 SAM 3 在边缘设备上的已知数字

- **论文**：848M 参数，检测器 + 跟踪器共享编码器；H200 上 100+ 物体单图 30 ms；64 物体 30 FPS 需要 8×H200 [A: 论文]。
- **Orin**：Embedl 的 924 px TensorRT 基准是 763 ms（FP16）/ 462 ms（INT8+FP16），1.31/2.17 QPS [B]。这是"图像 PCS"的数字，不含视频跟踪与 judge。
- **Orin NX**：PINTO0309 的 TensorRT 实现在 4K 图像上 6600→950 ms；AGX Orin 更强，924 px 预计 0.3–0.6 s [B/C]。
- **关键限制**：Embedl 明确只在 TensorRT 10.1/10.3 验证，更新版本"可能产生错误掩码" [A: 模型卡]；JetPack 7.2 是 TensorRT 10.16/11.x，**引擎必须重建并重新验证** [A/C]。

### 5.2 Qwen3-VL 与边缘部署

- Qwen3-VL：2B/4B/8B/32B/30B-A3B/235B-A22B，Apache-2.0，原生 256K 上下文，多图输入 [A: 仓库]。
- 对 SST 的两个角色：
  - **提词**：27B 看首帧 + 指令，输出 73 行词表约束下的英文短语；
  - **评审**：27B 看"原图 + 高亮掩码图"，用 logprob 比值判 yes/no。
- 在 Orin 上，27B 的官方基准是 10.5 tok/s、24 GB（INT4 AWQ，VLM）[A: Edge-LLM]；4B 是 52.2 tok/s、9.9 GB；8B 是 32.2 tok/s、13.1 GB [A]。**4B 是交互式评审的甜点；27B 只适合离线批处理，且 32GB 不可行** [C]。
- **SST 的 27B 不可得**：Edge-LLM 的模型列表里是 Qwen3.5-27B，不是 SST 的 Qwen3.8-27B；精确复现不可能 [A/C]。

### 5.3 TensorRT Edge-LLM

- NVIDIA 的 C++ 边缘推理运行时，Apache-2.0；官方支持 Jetson Orin（JetPack 7.2、CUDA 13.2、sm_87、FP16/INT8/INT4；**不支持 FP8/FP4**）[A: 支持矩阵]。
- 支持 Qwen2.5-VL/Qwen3-VL 的视觉塔与 LLM 组件（`cpp/multimodal/qwen2_5`、`qwen3`；基准表有 Qwen3-VL-4B/8B）[A]。
- 提供 OpenAI 兼容 server 和 Python API；但文档没有列出 `logprobs`/`top_logprobs` [A: server 文档]。这意味着 SST 的 logprob 评审需要改写为文本 yes/no，或换运行时 [C]。

### 5.4 其他 Qwen 运行时

| 运行时 | Orin 支持 | Qwen3-VL | 备注 |
|---|---|---|---|
| **TensorRT Edge-LLM** | 官方（JetPack 7.2） | 是（官方基准） | 推荐；INT4/FP16；无 logprobs 文档 |
| vLLM | **无官方**（ARM 只提 Grace/Blackwell；sm_87 未认证） | 可能（需源码编译） | 不建议作为第一选择 [A] |
| llama.cpp | 社区/容器 | 是（mtmd，有已知精度/预处理 bug） | 灵活；chat logprobs 不确定；适合快速验证 [B] |
| HF Transformers | 是（需 aarch64 torch） | 是 | 最慢；但 logits/logprobs 直接可得，适合做评审 oracle [C] |
| MLC-LLM | 社区（jetson-containers） | 视模型 | 备选 [B] |
| Ollama | 社区容器 | 视模型 | 简单，但 logprobs/多图能力需验证 [C] |

### 5.5 功耗与散热

- AGX Orin 32GB 模块 15–40W，64GB 15–60W（开发套件可到 75W）[A: 数据手册/产品页]。
- Edge-LLM 与 Embedl 的基准通常在 MAXN/高功耗模式下取得；SAM3 + 4B VLM 同时跑会接近功耗上限，持续频率可能下降 [C]。必须在 `nvpmodel` 的同一模式下比较 [D]。

---

## 06. Repository Investigation（仓库/实现调查）

### 6.1 SAM3 的 Orin 实现路径

| 路径 | 做法 | 优点 | 风险 |
|---|---|---|---|
| **TensorRT（Embedl）** | 预导出 ONNX→TRT，924 px，INT8+FP16 | 462 ms，官方 AGX Orin 数字 | TensorRT 10.1/10.3 限定；10.16/11.x 需重建；额外许可禁止托管服务 |
| **TensorRT（PINTO0309）** | ONNX 导出 + `trtexec`，MIT；aarch64 Docker | 可自己重建；Jetson 支持 | 需要 x86/设备上的导出与引擎构建；版本要匹配 |
| **PyTorch（上游 sam3）** | `build_sam3_image_model` + `Sam3Processor` | 最简单；源码可读 | 需 aarch64 torch≥2.7；比 TRT 慢；显存更高 |
| **视频模式** | `build_sam3_video_predictor` | 可跟踪 | 显存随物体/帧增长；Orin 上建议短序列、单物体 |

**结论**：实际部署用 PyTorch（anaconda torch 2.8.0）在 **1008 px + bf16 autocast** 下跑通；TensorRT 10.3 仍是后续提速选项，尚未开始 [S]。

### 6.2 Qwen 的两种实现：Edge-LLM（7.2）与 llama.cpp（本机实测）

- 支持矩阵：Orin 官方、JetPack 7.2、CUDA 13.2、sm_87、平台自带 TensorRT 10、FP16/INT8/INT4 [A]。
- 基准（AGX Orin 64GB，v0.8.0，batch 1，2048 输入，单图）：

| 模型 | 精度 | Prefill (ms) | ViT (ms) | 生成 (tok/s) | GPU Mem (MB) |
|---|---|---|---|---|---|
| Qwen3-VL-2B | INT4 AWQ / FP16 | 48.0 | 38.7 | 95.7 | 8,235 |
| Qwen3-VL-4B | INT4 AWQ / FP16 | 118.6 | 39.0 | 52.2 | 9,863 |
| Qwen3-VL-8B | INT4 AWQ / FP16 | 213.2 | 56.5 | 32.2 | 13,133 |
| Qwen3.5-27B | INT4 AWQ / FP16 | 1,037.4 | 53.5 | 10.5 | 24,048 |

- 2 张图的评审：ViT token 约翻倍（262→~524），prefill 相应增加；4B 的评审延迟估计 **0.2–0.4 s**（不含网络）[C]。
- 显存是"峰值 GPU Mem"，包含 KV cache/visual engine；与 SAM3 同机时要相加，再留 OS/其他进程余量 [A/C]。

**本机实测（llama.cpp，2026-11-26，S）**：

- 本机 JetPack 6.2 不支持 Edge-LLM 的官方 Orin 轮子，改用 llama.cpp master `aee03fbe`（CUDA 12.6、sm_87）。
- 模型：Qwen3-VL-8B-Instruct Q4_K_M（5.03 GB）+ mmproj Q8_0（0.75 GB），魔搭下载，SHA-256 与魔搭一致。
- 1 图描述：**1.95 s**（321 prompt tokens，23 输出 tokens）。
- 2 图描述：**2.64 s**（577 prompt tokens）。
- **2 图 yes/no + logprobs：中位 1.18 s**（min 1.17，max 1.41）；`yes` logprob -0.0057，`no` -8.91。
- 相同 prompt 重复：0.07–0.08 s（KV cache 命中，不代表真实评审）。
- 进程 RAM 约 12.1 GB；连续 10 次请求稳定；首次 GPU 全 offload 的一次硬重启未复现。

### 6.3 SST 栈到 Orin 的映射

| SST 组件 | Orin 替代 | 可行性 |
|---|---|---|
| vLLM + Qwen3.8-27B（提词/评审） | llama.cpp + Qwen3-VL-8B（本机实测）；Edge-LLM 留给 7.2 | 可行：模型不同；logprobs 实测可用 [S] |
| SAM3 3.0（视频/图像） | SAM3 3.0 TRT 或 PyTorch | 可行；TRT 版本需重建 [B/C] |
| 73 行英文词表 | 固定英文短语（我们的物体集） | 可行；但失去"自动提词" [C] |
| Qwen judge（logprob 比值） | llama.cpp OpenAI 接口 + `logprobs`/`top_logprobs` | 接口可用；阈值需重新校准 [S/C] |
| 8 GPU × 4 slot | 单 Orin | 吞吐差一个数量级 [A/C] |
| RoboTwin 仿真 + 策略 | 不在 Orin 上跑 | 不同任务 [C] |

### 6.4 许可证与访问

- SAM3：SAM License；官方 HF 仓库 gated；本次从魔搭第三方镜像 `facebook/sam3` 取得（含 SAM License，README 仍带 HF gated 字段），用于本地研究 [A]。
- Qwen3-VL：Apache-2.0 [A]。
- TensorRT Edge-LLM：Apache-2.0 [A]。
- Embedl SAM3：SAM License + 额外"禁止作为托管服务再分发" [A]。
- SST 自有代码：无根 LICENSE；**不能复制** [A]。

---

## 07. Comparative Analysis（横向比较）

### 7.1 硬件：32GB vs 64GB

| 维度 | 32GB | 64GB | 对本路线的影响 |
|---|---|---|---|
| GPU | 1792 CUDA / 56 TC / 939 MHz | 2048 / 64 / 1.3 GHz | 64GB 约 1.5× GPU 吞吐 [A/C] |
| CPU | 8 核 | 12 核 | 数据预处理/HTTP 更好 [A] |
| 内存 | 32GB @204.8 GB/s | 64GB @204.8 GB/s | 32GB 能跑 SAM3+4B；64GB 才能舒服跑 8B/27B [A/C] |
| 功耗 | 15–40W | 15–60W（套件可到 75W） | 64GB 持续性能更好，但散热要求更高 [A] |
| 推荐 | SAM3 + Qwen3-VL-4B | SAM3 + Qwen3-VL-8B（或 27B 离线） | 见 §10 |

### 7.2 软件栈

| 栈 | SAM3 | Qwen | 安装难度 | 性能 | 许可 | 建议 |
|---|---|---|---|---|---|---|
| **Edge-LLM + SAM3 TRT** | TRT | Edge-LLM | 中–高（导出/引擎） | 最好 | Apache-2.0 + SAM | **推荐** |
| Edge-LLM + SAM3 PyTorch | PyTorch | Edge-LLM | 中 | 中 | 同上 | 先 smoke test |
| llama.cpp + SAM3 TRT | TRT | llama.cpp | 中 | 中 | 宽松 | Qwen 备选 |
| vLLM + SAM3 | TRT | vLLM | 高（无官方 Orin） | 未知 | Apache-2.0 | 不推荐 |
| HF Transformers | PyTorch | Transformers | 低 | 低 | 宽松 | 仅 oracle/校准 |

### 7.3 模型规模

| 模型 | 显存（Edge-LLM） | 生成 | 评审适用性 | 结论 |
|---|---|---|---|---|
| Qwen3-VL-2B | 8.2 GB | 95.7 tok/s | 弱 | 只做提词/快速分类 |
| **Qwen3-VL-4B** | **9.9 GB** | **52.2 tok/s** | 中 | **甜点** |
| Qwen3-VL-8B | 13.1 GB | 32.2 tok/s | 较好 | 64GB 可选 |
| Qwen3.5-27B | 24.0 GB | 10.5 tok/s | 接近 SST | 64GB 离线；32GB 不可行 |

**本机实测（llama.cpp，8B Q4_K_M + Q8_0 mmproj）**：1 图 1.95 s、2 图 2.64 s、2 图 yes/no + logprobs 中位 1.18 s；进程 RAM 约 12.1 GB [S]。

---

## 08. Critical Findings（关键发现）

**F1. Orin 的关键瓶颈是软件栈，不是算力。** 32GB 就足以让 SAM3 + 4B VLM 共存；真正的坑是 JetPack/TensorRT 版本、SAM3 引擎重建、Qwen 导出与 logprob 评审 [A/C]。

**F2. vLLM 不是 Orin 的选项。** vLLM 官方文档的 ARM 支持只覆盖 Grace/Blackwell；没有 Jetson/sm_87 的预编译轮子 [A]。SST 的 `vllm serve` 启动方式不能照搬 [C]。

**F3. SST 的 27B 评审在 Orin 上是"能跑但不好用"。** 64GB 上 10.5 tok/s、24 GB；32GB 上放不下 SAM3 + 27B [A/C]。4B/8B 是唯一可交互的选择；评审质量必须重新校准 [C]。

**F4. logprob 评审可移植到 llama.cpp。** Edge-LLM 的 OpenAI 服务没有文档化 logprobs [A]；但 llama.cpp 的 OpenAI 兼容接口实测支持 `logprobs`/`top_logprobs`，2 图 yes/no 直接返回 yes/no 分数（`yes` -0.0057，`no` -8.91）[S]。SST 的 logprob 评审可在 llama.cpp 上实现，不需要 27B/Edge-LLM。

**F5. SAM3 的 TRT 引擎与版本绑定。** Embedl 只在 TensorRT 10.1/10.3 验证 [A]；本机正好是 10.3，这是唯一的好消息；但仍需自建/验证引擎，不能直接假设 462 ms 可用 [A/C]。

**F6. SAM3.1 仍然不适用。** 1–3 物体时 3.1 更慢、显存更高（见 SAM3 报告 F3）[B]。Orin 上更应固定 3.0。

**F7. 全量 SST 数据集在 Orin 上不现实。** 548,893 帧 × 0.46–0.76 s ≈ 70–116 小时（仅 SAM3），加 Qwen 与 I/O 更久；单 GPU vs SST 的 8 GPU [A/C]。Orin 适合 20–100 episode 的试点。

**F8. 网络拓扑是接入的隐藏成本。** Orin 在 `192.168.5.0/24`，机器人在 `10.42.0.x`；当前不互通 [S]。顾问式接入需要路由/NAT 或双网口，不能假设"同一个 Wi-Fi" [C]。

**F9. 功耗模式会改变结论。** 32GB 模块 15–40W、64GB 15–60W；低功耗模式下 SAM3 的 462 ms 可能显著变慢 [A/C]。所有基准必须在同一 `nvpmodel` 模式下比较 [D]。

**F10. 许可证是可行的。** Qwen3-VL 与 Edge-LLM 都是 Apache-2.0，SAM3 是 SAM License（gated）；相比 SST 的无授权代码，这条栈在法务上更干净 [A]。

**F11. Qwen3-VL-8B 已在 Orin 上跑通。** llama.cpp（CUDA 12.6/sm_87）1 图 1.95 s、2 图 2.64 s、2 图 yes/no + logprobs 中位 1.18 s；`logprobs` 可用；进程 RAM 约 12.1 GB [S]。

**F12. 两次硬重启都发生在 GPU 模型加载时，19V 后未复现。** llama.cpp 8B 首次全 GPU 加载（10:46）与 SAM3 3.45 GB 权重加载（11:28）都导致整机复位；换 19V/4.74A 后，44.4 W 压力、Qwen 5 GB 加载、SAM3 3.45 GB 加载与 20 次推理全部稳定 [S]。

**F13. 12V 适配器是两次硬重启的原因（强证据）。** 两路 USB-C 均 `online=0`，整机走桶形接口；用户确认使用 12V 适配器；官方 AGX Orin 开发套件要求 **19V / 3.42A（约 65W）**。换 19V/4.74A 后 VDD rails 11.76 → **19.17 V**，44.4 W 压力与 Qwen/SAM3 加载均稳定。未测得崩溃瞬间压降，但替换实验支持因果 [S]。

**F14. SAM3 GPU 已跑通，但配置敏感。** 1008 px + `torch.autocast("cuda", bfloat16)`：load 16.07 s、encode 0.69 s、prompt 0.202 s（20 次）、VRAM 5.34 GB；`orange can` 0.902，`can`/`beverage can` 0 个。924/504 px 触发 RoPE shape 断言；不用 autocast 报 bf16/float32 不匹配 [S]。

**F15. 货架数据集端到端 + 校准可用，但提示词语义是瓶颈。** `~/dataset`（LeRobot v3，`1003/1014/1015` = 278/64/41 episodes，3 相机，640×480）front 帧上，SAM3 对 green/orange/clear bottle、coca cola、snack bag、red can、shelf 均出多实例（scores 0.56–0.97）。易分 40 对：文本与阈值 0.5 均 **40/40**。硬负例 A（歧义：clear bottle 用在彩瓶、红罐→snack bag）：**47/60 = 78.3%**，13 个错误中 10 个是 "clear bottle" 语义歧义。硬负例 B（无歧义：绿→可乐、橙→绿、透明→可乐、可乐→橙、袋→绿瓶、红罐→绿瓶）：**60/60**，p_yes 最小 **0.9903**、错误例最大 **0.022**。50 帧流水线：57 有效对 **56/57 = 98.25%**，端到端 p50 **3.84 s**、p95 6.56 s。100 帧 front+wrist：4 px 硬边框过滤误杀 34 个合法边缘/近距离掩码；改用 "object, or a part of it?" 后 34 个 partial 中 **32/34 yes**，合计 **79 judged / 77 yes = 97.5%**；front p50 1.46 s、wrist p50 3.84 s、wrist no-mask 18/50。Wrist 100 帧多 episode（`bottle` 提示）：**89 valid / 88 correct = 98.9%**，25 no-mask；唯一错误是顶边被裁掉的橙瓶上半部（score 0.973，p_yes 0.037）。**judge 在提示词互斥时可靠；歧义提示、硬边框过滤和顶边局部是主要失败模式；wrist 用 `bottle` 泛化词最稳。** [S/B]

**F16. Judge 模板措辞可翻转判决。** 12 个掩码 × T1/T2/T3：T1 **9/11**、T2 **8/11**、T3 **7/11**（不含 ambig）；f19 T1 yes / T2/T3 no；hard1 T1/T2 no / T3 yes；低分掩码（0.754–0.762）最易翻转。**之前 40/40、60/60、98.9% 都是特定模板 + 特定样本的结果，不能跨模板比较。** 建议固定 T1 + SAM3 score≥0.8，低分跳过或标 uncertain；不要把 judge 当作通用细粒度验证器 [S]。

**F17. T1 + score≥0.8 在 18 个案例上 15/15。** 7 易分 + 7 硬负例 + 4 局部：15 judged 全对，3 skipped（clear 0.754、hard_clear 0.754、right wrist 0.762）；ambig f21 判 no。低分掩码被跳过，覆盖率 15/18；这是当前最稳的简单策略，但仍需人工/第二视角兜底，不能当通用验证器 [S]。

**F18. 200 帧固定策略稳定，唯一失败是高分边缘局部。** 200 帧（frontA/B + wristA/B 各 50）在 T1 + score≥0.8 下：183 judged / 182 correct = **99.45%**；16 个反例全部 no；唯一错误是 f21 左边缘绿瓶（score 0.91，T1 no）；30 NO_MASK + 3 低分跳过；e2e p50 **3.93 s**、p95 6.62 s；无重启（uptime 1 h 45 min）。score 门禁抓不到高分边缘局部，需要双视角/上下文/top-edge 处理 [S]。

**F19. 顾问式服务可跑，但 RSS 需观察。** 本地 HTTP 服务（127.0.0.1:8090）60 请求：58 judge / 2 no-mask / 0 skip，p50 **2.04 s**、p95 2.08 s；`/health` model/qwen true；无崩溃。RSS 1,386→2,088 MB（+702 MB / 220 s），可能是 PyTorch/Qwen 缓存，未证明泄漏；需要 30 min soak。服务只返回 mask/bbox/judge，不发 DDS、不接运动；代码在 Orin，不入 git [S]。

**F20. 30 min soak 无泄漏迹象。** 1,800 s / 180 请求 / 0 error：162 judge / 18 no-mask；p50 **1.04 s**、p95 2.32 s、max 2.77 s；服务 RSS 2,106→2,109 MB（+3 MB），Qwen 9,279→9,286 MB（+7 MB），health model/qwen true，无崩溃。free 33.4→27.9 GB（min 22.3）但两个进程 RSS 未涨，下降来自其它进程/缓存。30 min 单服务 soak 不等于 24 h 稳定性 [S]。

**F21. 500 请求压测：服务层无泄漏，延迟上界约 4 s。** 500 个顺序请求（200 帧池 ×2.5 轮，间隔 0.3 s，总 1,273.9 s）：**0 error**，427 judge / 8 skip / 65 no-mask；p50 **2.11 s**、p95 **3.77 s**、max **4.02 s**；服务 RSS 2,109→2,112 MB（+3 MB），Qwen 9,285→9,297 MB（+12 MB）；`/health` model/qwen true；无崩溃。**p95 3.77 s 超过 1 Hz 周期**：接入必须异步、只取最新帧并允许丢帧，不能同步阻塞相机回调。复用帧池，不是 500 个唯一帧 [S]。

**F22. 500 唯一帧 + 跨机 LAN：Wi-Fi 不是瓶颈，G4 仍失败。** 500 个互不重复帧（250 front + 250 wrist；1003 ep≥120 各 158、1014 各 64、1015 各 28），客户端在笔记本经 Wi-Fi 直连 Orin：**0 error**，412 judge / 7 skip / 81 no-mask；p50 **2.15 s**、p95 **3.74 s**、max **4.03 s**（front 2.09/3.81，wrist 2.16/3.62）。与回环 500 请求（2.11/3.77/4.02）差异 **≤0.04 s**（在噪声范围内），说明 Wi-Fi + HTTP 链路开销远小于模型时间。服务冷启动 1,387→2,086 MB（+699 MB 在 25 s 内完成），最后 5 min 平台 2,085–2,086 MB；Qwen 平台 9,276–9,277 MB（max 9,315）；无崩溃。81 NO_MASK 来自提示轮换与场景不匹配，不是服务失败。**G4 的 p95 <1.5 s 仍未达到**；本测试不计算准确率 [S]。

---

## 09. Engineering Applicability（工程适用性）

### 9.1 三种接入形态

| 形态 | 位置 | 数据流 | 运动影响 | 建议 |
|---|---|---|---|---|
| **离线批处理** | Orin 本地 | 读帧/视频 → 掩码/评审 → 存盘 | 无 | **先做** |
| **顾问式服务** | Orin → 笔记本/机器人 | HTTP/JSON → 掩码/目标点 | 无（system 层仍唯一入口） | 门禁通过后 |
| **闭环控制** | Orin → 策略 | 掩码进策略 | 有 | **不做** |

### 9.2 资源预算（估算）

| 项 | 32GB | 64GB | 等级 |
|---|---|---|---|
| SAM3（FP16/TRT） | ~3–4 GB | ~3–4 GB | C |
| Qwen3-VL-4B（Edge-LLM） | 9.9 GB | 9.9 GB | A |
| Qwen3-VL-8B | 13.1 GB | 13.1 GB | A |
| Qwen3.5-27B | 不可行 | 24.0 GB | A/C |
| OS + 其他 | 4–6 GB | 4–6 GB | C |
| **合计（4B）** | **~17–20 GB** | **~17–20 GB** | C |
| **合计（8B）** | **~20–23 GB（紧）** | **~20–23 GB** | C |
| **合计（27B）** | — | **~31–34 GB（可行但慢）** | C |

**本机 llama.cpp 8B 实测：进程 RAM 约 12.1 GB（含模型/OS）[S]。**

### 9.3 延迟预算（估算）

| 环节 | 4B | 8B | 27B | 等级 |
|---|---|---|---|---|
| SAM3 单图 924 px | 0.46–0.76 s | 同 | 同 | B |
| Qwen 评审（2 图 + 1 token） | 0.2–0.4 s | 0.3–0.5 s | 1.2–1.6 s | C（基于 A 的分项） |
| 提词（1 图 + ~50 token） | 0.8–1.2 s | 1.0–1.5 s | 3–5 s | C |
| **每帧总延迟（含评审）** | **~0.7–1.2 s** | **~0.8–1.3 s** | **~1.7–2.4 s** | C |

**本机实测（SAM3 3.0，1008 px + autocast）**：load 16.07 s、encode 0.69 s、prompt **0.202 s**、VRAM 5.34 GB [S]。

### 9.4 安全与边界

- 只输出 advisory；不发布 vendor 话题、不打开设备、不加入 41/42/43 域、不调用 `ExecuteMotion` [A]。
- 评审模型不能直接否决"运动"，只能否决"掩码候选"；最终目标仍由感知/系统层决定 [C]。
- 实机验证单独授权；Orin 的接入不改变安全边界 [A]。

---

### 9.5 顾问式接入契约（提案，未在产品仓库实施）

- **路径**：笔记本 GPU 节点（与现有 YOLO 同侧）→ Orin `http://192.168.5.31:8090/infer`。Orin 只返回 mask/bbox/score/judge，不加入 41/42/43 域、不打开设备、不调用 `ExecuteMotion`。
- **服务位置**：Orin `/opt/jcheng/sam3_advisor/server.py`（root 644，手动启动，无 systemd/自启；`client.py` 同目录）；**已扩展为同时接受 `{image_b64}`（旧 path 模式备份 `server_pathmode.py`）**；**Orin 回环和笔记本→Orin Wi-Fi 直连都已验证**（2026-11-26，500 唯一帧：p50 2.15 s、p95 3.74 s，与回环差异 ≤0.04 s）。
- **请求**：实验用 `{image_path}`；生产用 `{image_b64, prompt}`。**响应**：`gate`（JUDGE / SKIP / NO_MASK）、`score`、`bbox`、`mask_rle`、`judge`（answer/p_yes）、`timings`。
- **接入点**：新增 L3 节点订阅相机 image，**异步** 按 1–2 Hz 取最新帧调用（单 worker，忙时丢帧）；结果转成 `Detection2DArray` / `FusedTarget` 的 advisory 字段。超时、非 200、`gate=SKIP` → 丢弃该帧并降级到 YOLO，**绝不阻塞主链路**。500 唯一帧 p95 **3.74 s**、max 4.03 s，同步 1–2 Hz 不可行（S）。
- **网络**：Orin `192.168.5.x` 与机器人 `10.42.0.x` 不同子网；笔记本中转已实测可行（Wi-Fi 直连），机器人侧仍需单独路由/双网口。
- **状态**：2026-11-26 已在 `jcheng-perception` 的独立 worktree/branch `feat/advisor-client-20261126` 实现 `sam3_advisor` 客户端（`jcheng_perception_gpu`；107 tests；离线 fake transport + 2 帧跨机冒烟 0.961/3.39 s、0.973/2.24 s；**未合并、未部署**）。主 checkout 的 `feat/ore-scene-s0s1` 未提交工作未被触碰；落地仍需单独 PR、配置项和一次单独授权的硬件会话。

## 10. Recommended Approach（推荐方案）

### 10.1 推荐：路线 A — 本机离线优先，SAM3 TRT 10.3 + Qwen llama.cpp

1. **MVE-0（已运行，2026-11-26）**：只读探测完成：64GB、JetPack 6.2 / L4T 36.4.4、CUDA 12.6、TensorRT 10.3、无 torch、MAXN、782GB 空闲；直连 PyPI/HF 超时。结论见 §00 [S]。
2. **MVE-2（已运行，2026-11-26）**：Qwen3-VL-8B 通过 llama.cpp 跑通：1 图 1.95 s、2 图 2.64 s、2 图 yes/no + logprobs 中位 1.18 s；`logprobs` 可用；进程 RAM 约 12.1 GB；10 次连续请求稳定。**门禁 G2 的延迟/接口部分通过；评审质量仍需 100 样本校准** [S]。
3. **MVE-1（已完成，2026-11-26）**：19V/4.74A 供电；SAM3 3.0 用 PyTorch **1008 px + bf16 autocast**；load 16.07 s、encode 0.69 s、prompt **0.202 s**（20 次）、VRAM 5.34 GB；`orange can` 0.902。**门禁 G1 通过** [S]。下一步 MVE-3：掩码 → Qwen judge 端到端试点。
4. **MVE-3（部分完成，2026-11-26）**：易分 40/40；无歧义硬负例 60/60；歧义硬负例 47/60；50 帧 56/57；100 帧 front+wrist part-aware 97.5%；wrist 100 帧多 episode **88/89 = 98.9%**（`bottle` 提示，25 no-mask，1 个顶边局部假阴性）；硬边框过滤误杀 34 个合法边缘/近距离掩码，已弃用。**下一步**：顶边局部处理/ROI、抓取段触发、扩到 200+ 帧多 episode 长期稳定性 [S/B]。
5. **MVE-4（可选）**：顾问式 HTTP 服务 + 网络中转（Orin → 笔记本 → 机器人），30 分钟稳定性；不做运动。

### 10.2 备选

- **路线 B**：升级到 JetPack 7.2 后用 Edge-LLM 跑 Qwen（官方支持、52 tok/s）；代价是重刷/升级与 SAM3 引擎重建 [A/C]。
- **路线 C**：SAM3 only（固定提示，不要 Qwen judge）；最快、最稳，适合"只想要掩码"的场景 [C]。
- **路线 D**：llama.cpp + Qwen3-VL-8B 作为本机首选（已实测）；若评审质量不足，换 4B/2B 或 HF Transformers + logits 做离线校准 [S/C]。

### 10.3 不推荐

| 选项 | 原因 |
|---|---|
| 在 Orin 上复刻 vLLM + 27B + logprob judge | vLLM 无 Jetson 支持；27B 在 32GB 不可行；logprob 改用 llama.cpp 已实测可用 [A/S] |
| 直接把任意 TensorRT 引擎跨 JetPack 版本使用 | 引擎与 TensorRT 版本绑定；本机 10.3 必须匹配 |
| 在 Orin 上跑 SAM3.1 multiplex | 1–3 物体负优化 [B] |
| 在 Orin 上重建 SST 全量数据集 | 70–116 小时仅 SAM3；单 GPU [A/C] |
| 把 Orin 接进运动闭环 | 安全边界；我们的主要误差是标定 [C] |
| 复制 SST 的 `auto_mask/`/`inference/` | 无授权 [A] |

---

## 11. Experimental Design（实验设计）

完整设计见 [experiments/20261126-agx-orin-stack-probe/design.md](../experiments/20261126-agx-orin-stack-probe/design.md)。**MVE-0/1/2 已运行（2026-11-26）；MVE-3 部分完成；MVE-4 部分完成（回环 + 跨机 Wi-Fi 已测，p95 未达 <1.5 s 门限，无 24 h）**。

| MVE | 假设 | 环境 | 指标 | 验收 | 失败判据 | 状态 |
|---|---|---|---|---|---|---|
| **MVE-0** | 能确认型号/JetPack/TRT/torch | Orin 只读 | 规格、版本、内存、功耗模式 | 记录完整 | 无法登录 | **已运行 2026-11-26（S）**：64GB / JetPack 6.2 / TRT 10.3 / 无 torch / MAXN / 782GB |
| **MVE-1** | SAM3 3.0 在 Orin 上 ≤2 s/帧 | Orin；PyTorch 1008 + autocast | 延迟、RAM、掩码 | G1 | OOM/掩码空 | **完成 2026-11-26（S）**：load 16.07 s、encode 0.69 s、prompt 0.202 s、VRAM 5.34 GB；20 次稳定；`orange can` 0.902 |
| **MVE-2** | 8B 评审 ≤1.5 s；logprobs 可用 | Orin；llama.cpp（Qwen3-VL-8B GGUF） | 延迟、RAM、一致率 | G2 延迟/接口 | 一致率 <75% | **已运行 2026-11-26（S）**：1 图 1.95 s、2 图 2.64 s、yes/no 1.18 s；logprobs 可用；RAM 12.1 GB；质量校准未做 |
| **MVE-3** | 试点端到端 ≥1 fps | Orin；固定短语 | 吞吐、可用率 | G3 | <0.5 fps | **部分完成（S/B）**：易分 40/40；无歧义硬负例 60/60；歧义硬负例 47/60；50 帧 56/57；100 帧 front+wrist 97.5%；wrist 100 帧多 episode 88/89（`bottle`）；**judge 模板敏感（12 掩码 × 3 模板：T1 9/11、T2 8/11、T3 7/11），建议 T1+score≥0.8**；吞吐/长期稳定性未测 |
| **MVE-4** | 顾问服务 30 min 稳定 | Orin + 笔记本 | p95、内存增长 | G4 | 泄漏/崩溃 | **部分完成（S）**：30 min / 180 请求 / 0 error；162 judge / 18 no-mask；p50 1.04 s、p95 2.32 s；服务 RSS +3 MB、Qwen +7 MB；**500 请求 / 0 error / p95 3.77 s / max 4.02 s / RSS +3/+12 MB**；**500 唯一帧跨机 Wi-Fi / 0 error / p50 2.15 s / p95 3.74 s / RSS 平台**；无崩溃；**G4 的 p95 <1.5 s 未达到**；无 24 h |

**探测命令（复现用，只读）**：

```bash
hostname; uname -m
head -2 /etc/nv_tegra_release 2>/dev/null || true
free -g; nproc
nvpmodel -q 2>/dev/null | head -5
timeout 3 tegrastats --interval 1000 2>/dev/null | head -2
python3 -V; python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())" 2>&1 | tail -1
/usr/src/tensorrt/bin/trtexec --version 2>/dev/null | head -3 || true
dpkg -l 2>/dev/null | grep -E "nvidia-jetpack|tensorrt" | head -8
df -h / | tail -1
```

**记录方式**：`experiments/20261126-agx-orin-stack-probe/data/*.csv`、`logs/*.txt`、`result.md`；权重放 Orin 的 `/opt/jcheng/models/`，不进 git。

**回退**：MVE-0 已确认 64GB + JetPack 6.2 → Qwen 走 llama.cpp；MVE-1 导出失败 → 降分辨率或改用现成 ONNX；MVE-2 一致率低 → 去掉 judge，只保留 SAM3 分数阈值；MVE-3 吞吐低 → 降到 672/504 px 或只做离线标注。

---

## 12. Limitations & Uncertainties（局限与不确定）

1. **SAM3 已跑通**：1008 px + autocast；提示词敏感性与跨物体质量未评估（S/D）。
2. **JetPack 6.2 与 Edge-LLM 的 7.2 支持不匹配**：本机 Qwen 走 llama.cpp；Edge-LLM 的 52 tok/s 不能直接套用（S/A）。
3. **Orin 直连 PyPI/Hugging Face 超时**：下载经魔搭/笔记本中转；魔搭直连约 35 MB/s（S）。
4. **SAM3 的 Orin 数字是第三方**：Embedl 462/763 ms 是 924 px、TensorRT 10.1/10.3、图像 PCS；不含视频跟踪与 judge（B）。
5. **Qwen 的 Edge-LLM 数字是 v0.8.0、单图、2048 输入**：本机 llama.cpp 实测 8B 的数字见 §6.2；两者不可直接比较（A/S）。
6. **judge 在无歧义负例上 60/60，在歧义负例上 47/60**：提示词语义是瓶颈，不是视觉能力（S/B）。
7. **logprob 可用，阈值 0.5 在无歧义集 60/60**；在歧义集同样 78.3%，阈值不能救语义歧义（S/C）。
8. **SAM3 运行时已验证**：PyTorch 1008 + autocast；924/504 px 不可用（RoPE）；ONNX/TRT 路径未开始（S/D）。
9. **供电已解决**：19V/4.74A；12V 导致两次硬重启（强证据）；仍建议保留 19V（S）。
10. **网络未打通**：Orin 与机器人不同子网；顾问式接入需要额外路由（S/C）。
11. **许可证**：SAM3 从魔搭第三方镜像取得（SAM License，README 仍带 HF gated 字段）；Embedl 额外限制；SST 代码无授权（A）。
12. **数据集试点范围**：100 帧 front+wrist + 100 帧 wrist 多 episode + 30 掩码 × 60 对 × 2 组，640×480，无逐像素真值；硬边框过滤会误杀合法边缘目标；"part of it" 提升 partial 接受率但顶边局部仍会漏；数字不代表通用准确率（B/C）。
13. **模板敏感性**：12 个掩码 × 3 模板；T1 9/11、T2 8/11、T3 7/11；低分掩码最易翻转；需要固定模板 + 更大校准集，当前数字不代表通用准确率（S/D）。
14. **T1+gate 策略验证**：18 案例 15 judged/15 correct、3 skipped；低分/强局部被跳过；样本仍小（S/D）。
15. **200 帧稳定性**：183 judged/182 correct = 99.45%；16 反例全对；1 个高分边缘局部假阴性；无重启，但不代表通用准确率（S/B）。
16. **顾问服务 30 min soak**：180 请求/0 error，服务 RSS +3 MB、Qwen +7 MB；无泄漏迹象；仍非 24 h 稳定性（S/D）。
17. **500 请求压测**：0 error、p95 3.77 s、max 4.02 s、服务/Qwen RSS +3/+12 MB；复用 200 帧池 2.5 轮，不是 500 个唯一帧；只测回环，跨机网络与 24 h 稳定性未测（S/D）。
18. **500 唯一帧 + 跨机 LAN**：0 error、p50 2.15 s、p95 3.74 s、max 4.03 s；服务冷启动 +699 MB 后平台、Qwen 平台；与回环差异 ≤0.04 s；81 NO_MASK 来自提示/场景不匹配；本测试不计算准确率，且仍非 24 h 稳定性（S/D）。

---

## 13. References（参考文献）

1. NVIDIA, *Jetson AGX Orin* 产品页（32GB/64GB 规格）。<https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin>
2. NVIDIA, *Jetson AGX Orin Series Data Sheet* DS-10662-001 v1.5（32GB：200 TOPS/1792 CUDA/939 MHz/15–40W；64GB：275 TOPS/2048 CUDA/1.3 GHz/15–60W）。<https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5380/Jetson_AGX_Orin_Series_Data_Sheet_DS-10662-001_v1.5.pdf>
3. NVIDIA, *JetPack* 页（JetPack 7.2、Ubuntu 24.04、kernel 6.8、CUDA 13.0 表述）。<https://developer.nvidia.com/embedded/jetpack>
4. NVIDIA, *TensorRT Edge-LLM* 文档：overview、support matrix、supported models、performance benchmarks、installation、server、limitations。<https://nvidia.github.io/TensorRT-Edge-LLM/>
5. `NVIDIA/TensorRT-Edge-LLM`（Apache-2.0，main 2026-11-17 push）。<https://github.com/NVIDIA/TensorRT-Edge-LLM>
6. Embedl, *SAM3* Hugging Face 模型卡（AGX Orin 924 px：763 ms FP16 / 462 ms INT8+FP16；TensorRT 10.1/10.3）。<https://huggingface.co/embedl/sam3>
7. `PINTO0309/SAM3-TensorRT`（MIT；Orin NX 4K 6600→950 ms）。<https://github.com/PINTO0309/SAM3-TensorRT>
8. `QwenLM/Qwen3-VL`（2B/4B/8B/32B/30B-A3B/235B-A22B；Apache-2.0；256K；多图）。<https://github.com/QwenLM/Qwen3-VL>
9. vLLM, *GPU installation*（支持 CUDA 7.5+；ARM 仅 Grace/Blackwell；无 Jetson/sm_87）。<https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html>
10. llama.cpp, *server README*（多模态 `image_url`；`/completion` 的 `n_probs`；chat logprobs 未明确）。<https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
11. `dusty-nv/jetson-containers`（JetPack 6.2/7；vLLM/llama.cpp/Ollama/Transformers 容器）。<https://github.com/dusty-nv/jetson-containers>
12. 本仓库：[SAM 3 在 SST 仓库中的实现与 ArmPi 尝试路线](20261126-sam3-sst-open-source-attempt-route.md)；[SAM 3 来源记录](../references/perception/sam3.md)；[SST 仓库审计](../references/manipulation/sst-repo-audit.md)。
13. 工作区约束：工作区根 `AGENTS.md`（`~/jcheng/AGENTS.md`，不在本仓库）（分层、DDS 域、安全、模型权重存放）。
14. `ggml-org/llama.cpp` master `aee03fbe804c650c300694b9564dc5e7154fbb2b`（multimodal/Qwen3-VL；OpenAI server logprobs）。<https://github.com/ggml-org/llama.cpp>
15. 魔搭 `Qwen/Qwen3-VL-8B-Instruct-GGUF`（Q4_K_M 5.03 GB、mmproj Q8_0 0.75 GB；SHA-256 已核对）。<https://modelscope.cn/models/Qwen/Qwen3-VL-8B-Instruct-GGUF>

---

## 自审

| 问题 | 检查结果 |
|---|---|
| 是否存在确认偏误？ | 主动列出反例：vLLM 不可用、27B 不实用、TRT 版本锁定、logprob 不可得、网络不通、导出链路未验证。 |
| 是否遗漏替代方案？ | 已比较 Edge-LLM、vLLM、llama.cpp、HF Transformers、MLC/Ollama；SAM3 的 TRT 与 PyTorch 两条路径。 |
| 是否混淆相关性与因果？ | 没有声称"Orin 会提升抓取成功率"；只评估部署可行性与吞吐。 |
| 是否把厂商基准当实测？ | Embedl/Edge-LLM 的数字均标注 B/A，并注明分辨率、精度、批大小、版本；本机/Orin 未实测。 |
| 是否把 README 当实现？ | Edge-LLM 的模型支持与基准来自官方 docs/基准表；SAM3 的 TRT 路径来自第三方 README，标注 B。 |
| 是否有虚构引用？ | 所有链接为本次实际访问的页面/仓库/文档。 |
| 推荐是否适合当前项目？ | 推荐"离线优先 + 顾问式"，不触碰运动；32/64GB 分支明确；回退路径明确。 |
| 结论能否指导下一步？ | 是：先拿到 Orin 登录并跑 MVE-0 探测；再按 32/64GB 分支选 4B/8B。 |
