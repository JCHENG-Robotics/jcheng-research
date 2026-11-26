# Jetson AGX Orin — 规格、JetPack 与边缘推理栈

- **类型**：官方硬件文档 + 官方推理框架 + 第三方基准
- **访问日期**：2026-11-26
- **阅读范围**：NVIDIA 产品页与数据手册、JetPack 页、TensorRT Edge-LLM 文档（overview/support matrix/supported models/benchmarks/installation/server/limitations）、Embedl SAM3 模型卡、PINTO0309/SAM3-TensorRT、Qwen3-VL 仓库、vLLM 安装文档、llama.cpp server 文档。未在 Orin 上运行模型；2026-11-26 完成只读探测。

## 本机实测（2026-11-26，S）

- 主机 `ubuntu`，aarch64；L4T **R36.4.4** = **JetPack 6.2**，Ubuntu 22.04.5。
- 62,841 MB RAM，12 核；`nvpmodel` MAXN (0)；governor `schedutil`。
- CUDA **12.6.11**；TensorRT **10.3.0.30**；tensorrt Python 10.3；Python **3.10.12**；**无 torch**；numpy 1.24、onnx 1.20、onnxsim、onnx_graphsurgeon、opencv 4.12。
- Docker 29.10；**passwordless sudo 可用**；915 GB 磁盘，**782 GB 可用**。
- 网络：`eno1 192.168.5.31/24`；笔记本 `192.168.5.22` 可达（1.9 ms）；**pypi.org / huggingface.co 直连超时**；清华镜像 200（约 1.6 MB/s）；NVIDIA 中国站 307。
- 无 llama.cpp / ollama / transformers / 模型文件。

**结论修订**：本机是 JetPack 6.2，Edge-LLM 官方 Orin 支持是 7.2 → 本机 Qwen 首选 llama.cpp；TensorRT 10.3 正好是 Embedl 验证 SAM3 的版本 → SAM3 的 TRT 路径在本机更顺；但本机无 torch，SAM3 ONNX 建议在笔记本导出、Orin 用 trtexec 10.3 构建。

### Qwen3-VL-8B 实测（llama.cpp，S）

- 模型：魔搭 `Qwen/Qwen3-VL-8B-Instruct-GGUF`，Q4_K_M 5.03 GB + mmproj Q8_0 0.75 GB；SHA-256 与魔搭一致。
- 运行时：llama.cpp master `aee03fbe`，CUDA 12.6、sm_87；`llama-server 127.0.0.1:8080`，4 slots，4096 ctx。
- 1 图描述 1.95 s（321 prompt tokens，23 输出）；2 图 2.64 s（577 prompt tokens）；2 图 yes/no + logprobs 中位 **1.18 s**；`logprobs` 可用（`yes` -0.0057，`no` -8.91）；进程 RAM 约 12.1 GB。
- 相同 prompt 重复 0.07–0.08 s（KV cache 命中，不代表真实评审）。
- 首次 GPU 全 offload 与一次硬重启（10:46）同时发生；后续 5 种 GPU 配置（文本、CPU/GPU 视觉塔、FA on/off、2048 ctx）均通过，未复现。`last -x` 显示机器此前已有多次 crash；持久 journal 已启用。
- **SAM3（2026-11-26）**：魔搭 `facebook/sam3` 的 `sam3.pt` 3.45 GB（SHA-256 `9999e234…` 一致，SAM License）；代码 `/opt/jcheng/src/sam3`；venv `/opt/jcheng/venvs/sam3`（anaconda torch 2.8.0 + torchvision 0.23.0 + triton 3.4.0 + timm 1.0.31 + SAM3 0.1.0）。**19V 供电下 GPU 跑通**：`Sam3Processor(resolution=1008)` + `torch.autocast("cuda", bfloat16)`；load 16.07 s、encode 0.69 s、prompt 0.202 s（20 次）、VRAM 5.34 GB；`orange can` 0.902。**924/504 px 触发 RoPE shape 断言；不用 autocast 报 bf16/float32 不匹配**。
- **供电**：两路 USB-C `online=0`，整机走桶形接口；VDD_GPU_SOC/VDD_CPU_CV ≈11.76 V；用户确认 **12V 适配器**，官方要求 **19V/3.42A（~65W）**。两次硬重启都在 3–5 GB 权重进 GPU 时，CPU-only 稳定；换电源后再复测（S/C）。

## 硬件规格

| 项 | AGX Orin 32GB | AGX Orin 64GB |
|---|---|---|
| AI TOPS（稀疏 INT8） | 200 | 275 |
| GPU | 1792 CUDA / 56 Tensor Core / 939 MHz | 2048 / 64 / 1.3 GHz |
| CPU | 8-core Cortex-A78AE | 12-core Cortex-A78AE |
| 内存 | 32GB 256-bit LPDDR5 @204.8 GB/s | 64GB 256-bit LPDDR5 @204.8 GB/s |
| 模块功耗 | 15–40W | 15–60W（开发套件可到 75W） |
| GPU 架构 | Ampere（sm_87） | Ampere（sm_87） |

来源：NVIDIA 产品页与 *Jetson AGX Orin Series Data Sheet* DS-10662-001 v1.5。
注意：产品页把 32GB 写成 157 TOPS、64GB 功耗写成 15–75W，与数据手册不一致；本记录采用数据手册。

## JetPack

- JetPack 7.2：Ubuntu 24.04、kernel 6.8、CUDA 13.x；TensorRT 由 JetPack 提供（Edge-LLM 支持矩阵写 CUDA 13.2、平台 TensorRT 10）。NVIDIA JetPack 页对 CUDA 的措辞是 13.0，具体补丁级以设备为准。
- JetPack 6.2：L4T 36.x、Ubuntu 22.04、CUDA 12.6、TensorRT 10.3；Edge-LLM 对 Orin 的支持以 7.2 为官方，6.2 需按兼容版本处理。

## TensorRT Edge-LLM（Qwen 的推荐运行时）

- Apache-2.0；官方支持 Jetson Orin（JetPack 7.2、CUDA 13.2、sm_87、FP16/INT8/INT4；**不支持 FP8/FP4**）。
- 支持 Qwen2.5-VL 与 Qwen3-VL（源码 `cpp/multimodal/qwen2_5`、`qwen3`；基准表有 Qwen3-VL-2B/4B/8B）。
- 安装：`pip install "tensorrt-edgellm[runtime]"`（aarch64 wheel，cp310-abi3）；引擎在设备上构建。
- 基准（AGX Orin 64GB，v0.8.0，JetPack 7.2，batch 1，2048 输入，单图）：

| 模型 | 精度 | Prefill (ms) | ViT (ms) | 生成 (tok/s) | GPU Mem (MB) |
|---|---|---|---|---|---|
| Qwen3-VL-2B | INT4 AWQ / FP16 | 48.0 | 38.7 | 95.7 | 8,235 |
| Qwen3-VL-4B | INT4 AWQ / FP16 | 118.6 | 39.0 | 52.2 | 9,863 |
| Qwen3-VL-8B | INT4 AWQ / FP16 | 213.2 | 56.5 | 32.2 | 13,133 |
| Qwen3.5-27B | INT4 AWQ / FP16 | 1,037.4 | 53.5 | 10.5 | 24,048 |

- OpenAI 兼容 server 文档没有列出 `logprobs`/`top_logprobs`；SST 的 logprob 评审需要改写或在别的运行时上做。

## SAM3 在 Orin 上的已知数字

| 来源 | 配置 | 数字 |
|---|---|---|
| Embedl（TensorRT 10.1/10.3） | AGX Orin，924 px，图像 PCS，FP16 baseline | 763 ms / 1.31 QPS |
| Embedl | 同上，INT8+FP16 混合 | 462 ms / 2.17 QPS |
| PINTO0309/SAM3-TensorRT（MIT） | Orin NX，4K，TRT | 6600→950 ms |

注意：Embedl 只在 TensorRT 10.1/10.3 验证，更新版本"可能产生错误掩码"；JetPack 7.2 是 10.16/11.x，引擎必须重建并验证。

## 其他运行时边界

- **vLLM**：官方文档的 CUDA 支持是 compute capability 7.5+，ARM 只覆盖 Grace/Blackwell；没有 Jetson/sm_87 的官方支持或预编译轮子。
- **llama.cpp**：多模态 `image_url` 可用；Qwen3-VL 有 mtmd 支持但存在已知预处理/位置编码 bug；`/completion` 有 `n_probs`，chat 的 logprobs 未明确。
- **jetson-containers**：支持 JetPack 6.2/7，含 vLLM/llama.cpp/Ollama/Transformers 容器，无 Qwen 专门包。
- **Qwen3-VL**：2B/4B/8B/32B/30B-A3B/235B-A22B，Apache-2.0，256K 上下文，多图输入。

## 相关

- 报告：[AGX Orin 上 SAM3 + Qwen 部署可行性调研](../../reports/20261126-agx-orin-sam3-qwen-deployment.md)
- 实验：[AGX Orin 栈探测](../../experiments/20261126-agx-orin-stack-probe/design.md)
- 前置：[SAM 3 来源记录](sam3.md)、[SAM3 尝试路线报告](../../reports/20261126-sam3-sst-open-source-attempt-route.md)
