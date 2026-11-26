# 实验结果 — AGX Orin 栈探测（MVE-0 / MVE-2 部分）

- **日期**：2026-11-26
- **状态**：MVE-0 **完成**；MVE-1 未运行；MVE-2 **部分完成**（CPU-only 成功，GPU 路径待隔离）
- **主机**：Jetson AGX Orin Developer Kit，64GB，JetPack 6.2 / L4T 36.4.4，CUDA 12.6.11，TensorRT 10.3，Python 3.10.12，kernel `5.15.148-rt-tegra`
- **相关**：[实验设计](design.md)、[报告](../../reports/20261126-agx-orin-sam3-qwen-deployment.md)

## MVE-0 — 只读探测（完成，S）

| 项 | 值 |
|---|---|
| 主机 | `ubuntu`，aarch64；Jetson AGX Orin Developer Kit |
| 系统 | L4T R36.4.4 = JetPack 6.2；Ubuntu 22.04.5；kernel 5.15.148-rt-tegra |
| 内存 / CPU | 62,841 MB / 12 核；`nvpmodel` MAXN；governor schedutil |
| CUDA / TensorRT | CUDA 12.6.11；TensorRT 10.3.0.30；tensorrt Python 10.3 |
| Python / 框架 | 3.10.12；无 torch；numpy 1.24、onnx 1.20、onnxsim、gs、opencv 4.12 |
| 权限 / 容器 | passwordless sudo；Docker 29.10 |
| 磁盘 | 915 GB，可用 782 GB |
| 网络 | `eno1 192.168.5.31`；笔记本 192.168.5.22 可达；pypi/HF 直连超时；魔搭 200；GitHub 200 |
| 已装推理工具 | 无 llama.cpp / ollama / transformers / 模型文件 |

**判定**：64GB 分支；Qwen 走 llama.cpp（Edge-LLM 官方只支持 JetPack 7.2）；SAM3 ONNX 在笔记本导出、Orin 用 trtexec 10.3 构建。

## MVE-2 部分 — Qwen3-VL-8B（S/B）

### 下载与校验

- 来源：魔搭 `Qwen/Qwen3-VL-8B-Instruct-GGUF`
  - `Qwen3VL-8B-Instruct-Q4_K_M.gguf` 5,027,784,800 B
  - `mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf` 752,289,728 B
- SHA-256 与魔搭 API 给出的值逐字节一致：
  - `67d1659bfe71b89d50b45a4ad1a9e5b997e5bb16ce5da66a6a6167abd569e9e2`
  - `c6ba85508d82f42590e6eb77d5340369ab6fecf107a7561d809523d8aa5f3bfd`
- 存放：`/opt/jcheng/models/qwen3-vl-8b/`（不进 git）。

### 构建

- `llama.cpp` master `aee03fbe804c650c300694b9564dc5e7154fbb2b`，CUDA 12.6、`CMAKE_CUDA_ARCHITECTURES=87`、12 线程。
- 产物：`llama-cli`、`llama-server`、`llama-mtmd-cli` 构建成功。
- 构建日志中的 `UI: HF download failed` 是 llama-server 网页 UI 资源（Hugging Face 被墙），不影响 API 二进制。

### CPU-only 推理（成功）

```bash
llama-mtmd-cli \
  -m /opt/jcheng/models/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf \
  --mmproj /opt/jcheng/models/qwen3-vl-8b/mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf \
  -ngl 0 -n 32 --temp 0 -c 1024 \
  --image ~/qwen-test/snap_ext_rgb.jpg \
  -p "Describe the main objects in this image in one sentence."
```

- 结果：16.5 s 完成；输出
  “The image shows a close-up of an orange-colored beverage can with Chinese characters, likely an orange-flavored soda, sitting on a white surface.”
- 图像编码 358 ms；CPU 12 线程；模型与 mmproj 正常。

### GPU 全 offload 尝试（未结论）

- 命令：同图，`-ngl 99`，`-c 2048`，`-n 96`，默认 mmproj offload。
- 10:43 左右启动；10:46 主机 **硬重启**（`uptime` 归零，`last -x` 记为 `crash`）。
- 无 pstore、无持久 journal，崩溃前日志未落盘；无法确认是 llama.cpp/CUDA、供电、散热还是 RT 内核。
- `last -x` 显示此前多次 crash：11-23 16:13、11-23 18:23、11-25 19:27、11-26 09:10、11-26 10:46；说明机器在本次测试前已有不稳定历史。
- **不能归因**：只能记录“GPU 全 offload 与一次硬重启同时发生”。

### GPU 隔离复测（成功）

启用持久 journal 后，按风险从低到高复测，全部通过、无重启：

| # | 配置 | 结果 | 时间 |
|---|---|---|---|
| 1 | 文本-only，`-ngl 99`，`-fa off`，`-c 512`，8 tok | “Hello!” | 4.1 s；prompt 126.6 t/s，生成 11.0 t/s |
| 2 | 1 图，CPU 视觉塔（`--no-mmproj-offload`），GPU LLM | 正确描述橙色易拉罐 | 15.4 s；图像编码 9.98 s |
| 3 | 1 图，GPU 视觉塔 + GPU LLM，`-fa off`，`-c 1024` | 正确 | 8.5 s；图像编码 591 ms |
| 4 | 1 图，`-fa on`，`-c 1024` | 正确 | 5.3 s；图像编码 390 ms；峰值 VIN 9.6 W，tj 51°C |
| 5 | 1 图，`-c 2048`，默认 `-fa auto`（原崩溃配置） | 正确 | 5.6 s；峰值 VIN 10.1 W |

**结论**：最初的硬重启**未能复现**；GPU 路径（LLM + 视觉塔 + FA）本身可用。仍保留“机器有 crash 历史、原因未确认”的记录。

### 服务化与评审接口（成功）

- `llama-server`：`127.0.0.1:8080`，4 slots，4096 ctx，模型 `Qwen3VL-8B-Instruct-Q4_K_M.gguf` + `mmproj-...-Q8_0.gguf`。
- 注意：11:28 硬重启后 `llama-server` **没有自动启动**；需要手动重启，或后续加 systemd。
- `/health` = `{"status":"ok"}`；`/v1/models` 报告 `n_params=8,190,735,360`、`n_ctx_train=262144`、`ftype=Q4_K - Medium`，capabilities `completion` + `multimodal`。
- OpenAI 兼容接口：
  - 1 图描述：1.95 s，321 prompt tokens，23 输出 tokens。
  - 2 图描述：2.64 s，577 prompt tokens，32 输出 tokens（max_tokens 截断）。
  - **2 图 yes/no + logprobs**：未缓存中位 **1.18 s**（min 1.17，max 1.41）；`yes` logprob -0.0057，`no` -8.91。
  - 相同 prompt 重复：0.07–0.08 s（KV cache 命中，不代表真实评审）。
  - 10 次连续请求：全部成功；RAM 约 12.1 GB（含模型/OS），无重启。
- `logprobs` 可用（`top_logprobs` 返回 yes/Yes/no/No 的分数），SST 的 logprob 评审可在 llama.cpp 上实现，不需要 Edge-LLM。

### SAM3 部署尝试与第二次硬重启（2026-11-26 11:28，S/C）

**资源快照（11:10）**：RAM 13,893 / 62,841 MB；磁盘 98 / 915 GB；GPU 0%；46.6 °C；VIN 3.93 W；`llama-server` RSS 1.76 GB；无 Docker 容器。

**SAM3 准备（完成）**：

- 魔搭 `facebook/sam3`：`sam3.pt` 3,450,062,241 B，SHA-256 `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e` 与魔搭一致；LICENSE 为 SAM License。
- 代码：`/opt/jcheng/src/sam3`（上游 vendored，5.7 MB）；venv `/opt/jcheng/venvs/sam3`（899 MB）基于 anaconda `human_interaction_env` 的 **torch 2.8.0（CUDA 可用）** + torchvision 0.23.0；补装 triton 3.4.0、timm 1.0.31、einops、pycocotools；`from sam3.model_builder import build_sam3_image_model` 成功。
- 磁盘：权重 3.3 GB + venv 0.9 GB + 代码 5.7 MB。

**CPU-only（未通过）**：模型加载 16.3 s；`set_image` 在 `vitdet.py` MLP 处报
`mat1 and mat2 must have the same dtype, but got BFloat16 and Float`
（CPU bf16/float32 混用，非硬件问题；GPU 上可能由 autocast 处理）。

**GPU（硬重启）**：`build_sam3_image_model(device="cuda")` 加载 3.45 GB 权重期间，
11:28 主机硬重启（uptime 归零，`last -x` 记为 crash）；`/tmp/sam3_test.log` 为空，
未打印 `load_s`。

**电源**：两路 USB-C 均 `online=0`，整机走桶形接口；VDD_GPU_SOC / VDD_CPU_CV
≈ 11.76 V；用户确认使用 **12V 适配器**。官方 AGX Orin 开发套件要求
**19V / 3.42A（约 65W）**。

**判断（C）**：两次硬重启都发生在 3–5 GB 权重进 GPU 时（llama.cpp 10:46、
SAM3 11:28），而 CPU-only 构建/加载稳定；12V 适配器在 GPU 瞬态下欠压是首要
嫌疑。未测量到崩溃瞬间的电压跌落，需换 19V 电源后复测确认。

### SAM3 GPU 成功（2026-11-26 14:13–14:14，S）

**供电修复验证**：接 19V/4.74A 适配器后，`VDD_GPU_SOC / VDD_CPU_CV` 从 11.76 V
变为 **19.17 V**。30 s CUDA 压力测试：8192² FP32 matmul，**94 次 / 30.1 s**，
GPU 99%，峰值 **44.4 W**，最高 53.2 °C，无重启。

**Qwen 8B 复测**：`llama-server` 成功加载 5 GB 权重 + mmproj；1 图 **2.03 s**，
描述正确，`logprobs` 可用。

**SAM3 复测（成功）**：

- 3.45 GB `sam3.pt` 加载 **16.07 s**，无重启。
- **可用配置（关键）**：
  - `Sam3Processor(model, resolution=1008, device="cuda")`；
  - `with torch.autocast("cuda", dtype=torch.bfloat16):` 包住 `set_image` 与
    `set_text_prompt`；
  - 不需要改 `gather_backbone_out`。
- 结果：`orange can` → **1 个目标，score 0.902**；`beverage can` / `can` →
  0 个（默认 confidence 0.5）→ 提示词需要具体。
- 性能：图像编码 **0.69 s**（1008 px）；20 次 `set_text_prompt` 中位
  **0.202 s**（min 0.186 / max 0.212），每次 1 个检测；峰值 VRAM **5.34 GB**；
  系统 RAM 约 16.6 GB（含 Qwen server）。
- 失败过的配置：924/504 px 触发 RoPE `freqs_cis` shape 断言（必须 1008）；
  不用 autocast 会报 bf16/float32 dtype 不匹配。

### 数据集端到端试点（2026-11-26 14:23，S/B）

- 数据：`~/dataset/1015`（LeRobot v3.0，`dual_arm_grippers`，41 episodes / 20,652 帧 / 25 fps，front + wrist_left + wrist_right，640×480；任务 `start / grasp`）。`1003` 为 278 episodes / 183,246 帧；`1014` 为 64 / 34,510。帧从 front 视频 `videos/observation.images.front/chunk-000/file-000.mp4` 抽取。
- SAM3 提示词扫描（f_01/f_03）：green bottle 1–2（0.96）、orange bottle 1（0.97）、clear bottle 2–3（0.96/0.88）、coca cola bottle 1（0.97）、snack bag 5–6（0.56–0.91）、red can 3（0.79–0.94）、shelf 4（0.64–0.91）；每提示 0.18–0.52 s。
- 端到端：4 个掩码（green bottle、orange bottle、coca cola bottle、snack bag）× 2 个问题（正确/错误）；Qwen 两图 yes/no + logprobs：**8/8 文本判决正确**；Qwen 0.70–2.18 s；SAM3 提示 0.45–0.62 s。
- 掩码质量：目视检查 `f_01_green_bottle.png`（绿色 Sprite 瓶）与 `f_03_snack_bag.png`（Lay's 袋）均准确。
- 关键更正：之前把 `top_logprobs` 按"最后一个"聚合，导致 yes/no 都落在 -20 附近；改为按归一化 token 取**最大** logprob 后，正确例 yes ≈ 0 / no ≈ -16。见下节 40 对校准。

### 40 对校准（2026-11-26 14:29，S）

- 20 个掩码（来自 30 帧；green / orange / clear bottle、coca cola bottle、snack bag、red can，score ≥0.8，area 300–80,000），每个掩码问正确提示 + 一个易分错误提示，共 **40 对**。
- **文本判决 40/40；`p_yes ≥ 0.5` 阈值也 40/40**。
- logprob 分离：正确例 `p_yes` 最小 **0.9746**、中位 **1.0**；错误例 `p_yes` 最大 **0.0048**、中位 **0.0**。
- Qwen 2 图：p50 **2.23 s**、p95 **2.61 s**；SAM3 提示 p50 0.33 s。
- 掩码目视检查（contact sheet 6 张）：绿瓶、橙瓶、透明瓶、红罐、可乐、Lay's 袋均准确。
- CSV：[data/ds_calibration.csv](data/ds_calibration.csv)。
- 局限：负例是易分样本（不同颜色/类别），尚未测同色/同类硬负例；40 对不等于通用准确率。

### 硬负例 A：歧义负例（2026-11-26 14:33，S/B）

- 30 个掩码 / 60 对；错误提示：green→clear bottle、orange→clear bottle、coca cola→clear bottle、clear→green bottle、snack bag→red can、red can→snack bag。
- **文本与阈值 0.5 都是 47/60 = 78.3%**；13 个错误：10 个是"clear bottle"用在彩色 PET 瓶上（green 3、orange 3、coke 3、clear→green 1），3 个是红罐→"snack bag"。
- 关键：彩色 PET 瓶本身也是透明塑料，**"clear bottle" 不是一个干净的负例**；红罐与零食袋的包装边界也模糊。这是提示词语义问题，不是视觉能力问题。
- Qwen p50 1.33 s / p95 1.49 s；SAM3 p50 0.19 s。
- CSV：[data/ds_calibration_hard_ambiguous.csv](data/ds_calibration_hard_ambiguous.csv)。

### 硬负例 B：无歧义负例（2026-11-26 14:35，S）

- 30 个掩码 / 60 对；错误提示：green→coca cola、orange→green、clear→coca cola、coca cola→orange、snack bag→green bottle、red can→green bottle（颜色/品牌/物体类别明确不同）。
- **文本与阈值 0.5 都是 60/60**；正确例 p_yes 最小 **0.9903**，错误例 p_yes 最大 **0.022**；6 个类别各 100%。
- Qwen p50 0.78 s / p95 0.85 s；SAM3 p50 0.19 s。
- CSV：[data/ds_calibration_hard_unambiguous.csv](data/ds_calibration_hard_unambiguous.csv)。

**结论**：judge 在提示词语义互斥时可靠（60/60）；78.3% 的失败来自"clear bottle"这类歧义提示。需要一份**互斥的提示词本体**（颜色/品牌/物体类别），而不是靠 judge 猜语义。

### 50 帧端到端流水线（2026-11-26 14:47，S）

- 50 帧，5 个提示轮换（green/orange/cola/transparent/chip bag）；每帧 1 个掩码 + Qwen 判决，每 5 帧加一个错误提示。
- 60 行：**57 个有效对**（3 帧 NO_MASK：f_26 green、f_43/f_48 cola），**56/57 = 98.25%** 文本与阈值 0.5 一致。
- 唯一错误：f_21 `green soda bottle`，掩码是画面左边缘被裁掉的绿瓶局部（score 0.91），Qwen 判 no（p_yes 0.017）——**边缘/局部目标假阴性**，不是语义失败。
- 端到端 p50 **3.84 s**、p95 **6.56 s**；其中 SAM3 预处理 p50 0.09 s、提示/骨干 p50 0.95 s、Qwen 2 图 p50 2.61 s。
- 50 帧 + 67 次 Qwen 调用，无重启；19V 稳定。
- CSV：[data/ds_pipeline50.csv](data/ds_pipeline50.csv)。
- 建议：流水线加**边框/局部掩码过滤**（bbox 距边缘 <8 px 或面积过小 → 不送 judge），否则边缘物体会被误判。

### 100 帧 + wrist 相机 + 局部措辞（2026-11-26 14:55–14:58，S）

- front 50 + wrist_left 50；front 5 提示轮换、wrist 4 提示；每 5 帧一个反例。先跑 4 px 边框过滤版，再用 SST 的 "that object, or a part of it?" 措辞重测 partial。
- **边框过滤版**：front 36 valid / 11 partial / 3 no-mask；wrist 9 valid / 23 partial / 18 no-mask / 2 low。过滤把 front 的 chip bag（底边，10 个）和 wrist 近距离瓶（23 个）都挡掉了——**硬边框过滤太激进**。
- **局部措辞重测 34 个 partial**：**32/34 yes（94.1%）**，front 10/11、wrist 22/23。2 个 no 都是"只剩一条边"的不可辨认局部（f_21 绿瓶左边缘、wrist f_72 透明瓶右边缘），judge 判 no 合理。
- 采用 part-aware 措辞后：front 47 judged / 46 yes = **97.9%**；wrist 32 judged / 31 yes = **96.9%**；合计 **79 judged / 77 yes = 97.5%**；23 帧 no-mask/low。
- 端到端：front p50 **1.46 s** / p95 1.55 s（Qwen 0.25 s，相似帧缓存）；wrist p50 **3.84 s** / p95 6.37 s（Qwen 2.62 s）。无重启（uptime 1 h）。
- **结论**：不要用硬边框过滤；用 SST 的 "object, or a part of it?" 让 judge 判断可见部分是否足够。wrist 的 no-mask 率高（18/50），需要更近的目标提示/ROI 或只在抓取段触发。
- CSV：[data/ds_pipeline100.csv](data/ds_pipeline100.csv)、[data/ds_partial_retest.csv](data/ds_partial_retest.csv)。

### Wrist 100 帧多 episode（2026-11-26 15:10，S）

- 100 帧 wrist_left，两个视频段（file000/file001 各 50），提示词 **`bottle`**，part-aware judge，无边框过滤。
- file000：58 行（含反例），**49 valid / 9 no-mask / 97.96%**；file001：56 行，**40 valid / 16 no-mask / 100%**。
- 合计 **89 valid / 88 correct = 98.9%**；25 帧 no-mask（目标不在/太近/遮挡）；e2e p50 **3.76–3.83 s**、p95 6.4–6.45 s；Qwen p50 2.52–2.59 s；无重启（uptime 1 h 14 min）。
- 唯一错误：file000 f19，橙色瓶上半部在画面顶边被裁掉（score 0.973，area 7957），即使 "or a part of it?" 仍判 no（p_yes 0.037）——**顶边局部残留假阴性**。
- wrist 提示词变体（15 帧）：`bottle` 14/15（0.979，4.1 实例）、`plastic bottle` 13/15（0.848）、`soda bottle` 11/15（0.904）、`water bottle` 11/15（0.669）、`black object` 15/15（0.755，过泛）、`robot hand` 6/15、`gripper`/`black gripper` 0。
- CSV：[data/ds_wrist100.csv](data/ds_wrist100.csv)。

### Judge 模板敏感性（2026-11-26 15:14，S）

12 个掩码 × 3 种模板（T1 简单、T2 part-aware、T3 SST 原模板）：

| case | expected | T1 | T2 | T3 |
|---|---|---|---|---|
| easy_green | yes | yes 1.0 | yes 1.0 | yes 1.0 |
| easy_orange | yes | yes 0.9995 | yes 1.0 | yes 1.0 |
| easy_cola | yes | yes 1.0 | yes 1.0 | yes 1.0 |
| easy_clear (0.754) | yes | no 0.019 | no 0.341 | yes 1.0 |
| hard1 green→cola | no | no 0.014 | no 0.217 | **yes 0.988** |
| hard2 orange→green | no | no 0.0 | no 0.0 | no 0.0 |
| hard3 cola→orange | no | no 0.001 | no 0.014 | no 0.017 |
| hard4 clear→cola (0.754) | no | no 0.001 | no 0.384 | **yes 0.9996** |
| part_top f19 (0.973) | yes | **yes 0.979** | no 0.007 | **no 0.0** |
| part_left f21 (0.91) | ambig | no 0.005 | no 0.002 | no 0.001 |
| part_right w72 (0.762) | yes | no 0.0004 | no 0.102 | no 0.0003 |
| part_bottom chip (0.883) | yes | yes 0.984 | yes 0.999 | yes 0.991 |

**关键发现**：

- 同一掩码仅换措辞就能翻转判决（f19：T1 yes / T2 no / T3 no；hard1：T1/T2 no / T3 yes）。
- 没有单一模板在 12 个案例上全对：T1 9/11（不含 ambig）、T2 8/11、T3 7/11。
- 低分掩码（easy_clear 0.754、hard4 0.754、part_right 0.762）最容易受措辞影响。
- 之前 40/40、60/60、98.9% 都是**特定模板 + 特定样本**的结果，不能跨模板比较，也不能当作通用准确率。

**建议**：固定 **T1**（最简单、硬负例最稳）并加 **SAM3 score ≥0.8** 门禁；低分掩码跳过或标记 `uncertain`，不要送 judge 硬判；judge 只作为候选复核，不作为通用细粒度验证器。

### T1 + score≥0.8 策略验证（2026-11-26 15:24，S）

- 18 个案例：7 易分、7 硬负例、4 局部；SAM3 score≥0.8 才送 judge，其余标 SKIP。
- **15 judged / 15 correct = 100%**；3 个 SKIP：easy_clear（0.754）、hard_clear_cola（0.754）、part_right_wrist（0.762）。
- ambig f21（左边缘绿瓶局部，0.91）判 no，符合"太局部不可辨认"。
- 代价：低分 clear bottle 与右边缘透明瓶被跳过，覆盖率 15/18；低分/强局部仍需人工或第二视角兜底。
- CSV：[data/ds_t1gate.csv](data/ds_t1gate.csv)。

### 200 帧固定策略稳定性（2026-11-26 15:40，S）

- 200 帧：frontA/B + wristA/B 各 50；T1 + SAM3 score≥0.8；每 10 帧一个反例。
- 216 行：**judged 183、skipped 33**（NO_MASK 30 + score<0.8 3）。
- 正确对 167：166 yes、1 error（frontA f21 左边缘绿瓶，score 0.91，T1 no）；错误对 16：全部 no。
- accuracy **182/183 = 99.45%**；frontA 98.08%、frontB/wristA/wristB 100%。
- e2e p50 **3.93 s** / p95 6.62 s；judge p50 2.68 s；prompt p50 1.0 s；无重启（uptime 1 h 45 min）。
- 覆盖 183/200 = 91.5%；NO_MASK 30（wrist 25、front 5），低分 3。
- 结论：固定策略在 200 帧上稳定；唯一失败模式是**高分边缘局部**（f21），score 门禁抓不到。
- CSV：[data/ds_stability200.csv](data/ds_stability200.csv)。

### MVE-4 顾问式 HTTP 服务（2026-11-26 16:57，S）

- 本地服务 `127.0.0.1:8090`：`/health`、`/infer`；SAM3 只加载一次；T1 + score≥0.8；Qwen 走 `8080`；只返回 mask/bbox/judge。
- 60 请求（20 front 轮换 + 20 wrist `bottle` + 20 soak，5 s 间隔）：**58 JUDGE / 2 NO_MASK / 0 SKIP**；p50 **2.04 s**、p95 2.08 s；`/health` model/qwen true；无崩溃。
- RSS 1,386 → 2,088 MB（+702 MB / 220 s）；可能是 PyTorch/Qwen 缓存，未证明泄漏，需要更长 soak。
- 服务代码：Orin `/opt/jcheng/sam3_advisor/server.py`（root 644，手动启动、无 systemd；不入 git；`client.py` 同目录）；结果 JSON：[data/ds_advisor_service.json](data/ds_advisor_service.json)。

### 30 min 顾问服务 soak（2026-11-26 17:31，S）

- **1,800 s / 180 请求 / 0 error**；162 JUDGE / 18 NO_MASK / 0 SKIP。
- p50 **1.04 s**、p95 2.32 s、max 2.77 s（重复帧/前缀缓存使 p50 偏低）。
- **RSS 平台化**：服务 2,106→2,109 MB（+3 MB，max 2,109）；Qwen 9,279→9,286 MB（+7 MB，max 9,286）。
- `/health` model/qwen true；无崩溃。free 33.4→27.9 GB（min 22.3），但服务/Qwen RSS 未涨，下降来自其它进程/缓存。
- 结论：30 min/180 请求下无泄漏迹象；18 个 NO_MASK 是 wrist 目标不在视野。
- 数据：[data/ds_advisor_soak30.json](data/ds_advisor_soak30.json)、[data/ds_advisor_soak30.csv](data/ds_advisor_soak30.csv)。

### 500 请求服务压测（2026-11-26 17:40–18:03，S）

- 500 个顺序请求：200 帧池（frontA/frontB/wristA/wristB 各 50）循环 2.5 轮，front 5 个提示轮换，间隔 0.3 s；总 **1,273.9 s**。
- **0 error**；**427 JUDGE / 8 SKIP / 65 NO_MASK**（NO_MASK 仍集中在 wrist 目标不在视野的帧）。
- p50 **2.11 s**、p95 **3.77 s**、max **4.02 s**；p50 高于 30 min soak（1.04 s），因为本次序列包含完整 judge、重复/缓存命中更少。
- 内存平台化：服务 RSS 2,109→2,112 MB（+3 MB，max 2,112）；Qwen 9,285→9,297 MB（+12 MB，max 9,297）；`/health` model/qwen true；无崩溃。
- free 33,239→29,757 MB（min 28,679），两进程 RSS 未涨，下降来自页缓存/其它进程。
- **不是 500 个唯一帧**（200 帧池 ×2.5 轮），不能当作独立准确率；它验证的是服务层重复请求下的**延迟上界与内存稳态**。
- **工程含义**：p95 3.77 s 超过 1 Hz 周期 → 接入必须异步、只取最新帧并允许丢帧，不能同步阻塞相机回调（见报告 §9.5）。
- 数据：[data/ds_advisor_svc500.json](data/ds_advisor_svc500.json)、[data/ds_advisor_svc500.csv](data/ds_advisor_svc500.csv)。

### 500 唯一帧 + 跨机 LAN（2026-11-26 20:18–20:39，S）

- 500 个**互不重复**的帧：250 front + 250 wrist；来自 1003 的 ep≥120（每相机 158）+ 1014（64）+ 1015（28），每 episode 取中点一帧；提示仍为 front 5 词轮换、wrist `bottle`。
- 客户端在**笔记本**上，经 Wi-Fi `192.168.5.22` 直连 Orin `192.168.5.31:8090`（服务临时绑 `0.0.0.0`，测试后已停）；这是真正的跨机路径，不再只是回环。
- **0 error**；**412 JUDGE / 7 SKIP / 81 NO_MASK**；front 164 judge + 79 no-mask（31.6%，提示与场景不匹配），wrist 248 judge + 2 no-mask。
- p50 **2.15 s**、p95 **3.74 s**、max **4.03 s**；front p50 2.09 / p95 3.81，wrist p50 2.16 / p95 3.62。
- 与回环 500 请求（重复帧）几乎相同：p50 2.11→2.15、p95 3.77→3.74、max 4.02→4.03 → **与回环差异 ≤0.04 s（在噪声范围内），模型时间是主导**；G4 的 p95 <1.5 s 仍未达。
- RSS：服务冷启动 1,387 → 2,086 MB（max 2,086），**最后 5 min 平台 2,085–2,086**；Qwen 9,296 → 9,277 MB（max 9,315），平台 9,276–9,277；无崩溃。服务 +699 MB 是首次推理缓存，25 s 内完成，不是缓慢泄漏。
- free 33,849→28,308 MB（min 28,265），下降来自页缓存/其它进程；两进程 RSS 已平台化。
- **NO_MASK 81 是提示轮换与场景不匹配**（例如无 orange bottle 的货架），不是服务失败；本测试不计算准确率。
- 数据：[ds_uniq500_requests.csv](data/ds_uniq500_requests.csv)、[ds_uniq500_monitor.csv](data/ds_uniq500_monitor.csv)、[ds_uniq500_summary.json](data/ds_uniq500_summary.json)、[ds_uniq500_analysis.json](data/ds_uniq500_analysis.json)、[ds_uniq500_targets.tsv](data/ds_uniq500_targets.tsv)。

## 结论与下一步

1. **Qwen3-VL-8B 已部署成功**（llama.cpp CUDA 12.6/sm_87，Q4_K_M + Q8_0 mmproj），1 图 1.95–2.03 s、2 图 2.64 s、2 图 yes/no 1.18 s；`logprobs` 可用（S）。
2. **SAM3 3.0 已在 Orin 上跑通**：1008 px + bf16 autocast，20 次提示中位 0.202 s，VRAM 5.34 GB（S）。
3. **12V 适配器是两次硬重启的原因（强证据）**：换 19V/4.74A 后，30 s 压力（44.4 W）、Qwen 5 GB 加载、SAM3 3.45 GB 加载与 20 次推理全部稳定（S）。
4. **校准结果**：易分 40/40；无歧义硬负例 60/60；歧义硬负例 47/60（78.3%）（S/B）。
5. **50 帧流水线**：56/57 = 98.25%（S）。
6. **100 帧 front+wrist**：part-aware 措辞下 77/79 = 97.5%（S）。
7. **Wrist 100 帧多 episode**：88/89 = 98.9%；25 no-mask；唯一错误是顶边局部（S）。
8. **Judge 模板敏感性**：12 掩码 × 3 模板，无一对全对；措辞可翻转判决；之前数字均为特定模板结果（S）。建议 T1 + SAM3 score≥0.8 门禁，低分跳过/标 uncertain。
9. **T1+score≥0.8 策略验证**：18 案例 **15 judged / 15 correct**、3 skipped（低分 clear/right-edge）；当前推荐策略（S）。
10. **200 帧稳定性**：**183 judged / 182 correct = 99.45%**，16/16 反例全对；1 个高分边缘局部假阴性（f21）；30 NO_MASK + 3 低分跳过；无重启（S）。
11. **顾问式 HTTP 服务**：60 请求 **58 judge / 2 no-mask**，p50 2.04 s / p95 2.08 s，health model/qwen true，无崩溃；RSS 1.39→2.09 GB/220 s（S）。
12. **30 min soak**：180 请求 / 0 error / 162 judge / 18 no-mask；服务 RSS +3 MB、Qwen +7 MB（平台化），无崩溃（S）。
13. **500 请求压测**：0 error / 427 judge / 8 skip / 65 no-mask；p50 2.11 s、p95 3.77 s、max 4.02 s；服务 RSS +3 MB、Qwen +12 MB；health true、无崩溃；**G4 的 p95 <1.5 s 未达**（门限保持失败）；200 帧池复用 2.5 轮，不是 500 个唯一帧（S）。
14. **500 唯一帧 + 跨机 LAN**：0 error / 412 judge / 7 skip / 81 no-mask；p50 2.15 s、p95 3.74 s、max 4.03 s；与回环几乎相同（与回环差异 ≤0.04 s）；服务 1,387→2,086 MB 后平台、Qwen 平台；G4 p95 <1.5 s 仍未达（S）。
15. **下一步**：接感知异步 latest-frame advisory 节点（单独分支/PR；当前 perception 有未提交 ore-scene 工作）；或 24 h soak；500 唯一帧测试不等于 24 h 稳定性。
