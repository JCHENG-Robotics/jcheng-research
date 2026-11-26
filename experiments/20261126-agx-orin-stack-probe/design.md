# 实验设计 — AGX Orin 上的 SAM3 + Qwen 栈探测

- **日期**：2026-11-26
- **状态**：MVE-0 **已运行（2026-11-26，S 级）**；MVE-2 **部分完成**（Qwen3-VL-8B CPU+GPU 跑通，评审质量未校准）；MVE-1/3/4 **未运行**
- **负责人**：J. Cheng（决策/授权），ZCode（执行/分析）
- **相关报告**：`reports/20261126-agx-orin-sam3-qwen-deployment.md`
- **前置报告**：`reports/20261126-sam3-sst-open-source-attempt-route.md`
- **目标主机**：Jetson AGX Orin（32GB 或 64GB，未知）；`192.168.5.31`
- **本机**：笔记本 RTX 3060 6GB，`192.168.5.22`；机器人 `10.42.0.x`（USB NIC 当前 DOWN）

> 本文件只描述设计与门禁，不包含可被机器人加载的代码。权重放 Orin 的 `/opt/jcheng/models/`，不进入任何 git 仓库。

---

## 0. 前置动作（用户）

1. ~~提供 Orin 的登录方式~~ **已完成（2026-11-26）**：`ti5robot@192.168.5.31` 可登录；后续命令受控执行，不把口令写入仓库或 shell 历史。
2. 确认 Orin 是否可重启/升级 JetPack（MVE-0 只读，不改配置）。
3. 明确允许在 Orin 上下载：SAM3 权重（gated，3.45 GB）、Qwen3-VL-4B（约 8 GB FP16 / 2.5 GB INT4）、TensorRT Edge-LLM wheel；以及是否允许 `pip install`。
4. 明确 Orin 的用途：离线实验机，还是未来上机器人的推理盒；后者需要网络与供电方案。

**不在本设计内**：把 Orin 接入运动链、在 Orin 上训练/微调、复制 SST 无授权代码、非官方镜像下载 gated 权重。

---

## 1. MVE-0 — 只读探测（已运行 2026-11-26）

1. **假设**：能在 10 分钟内确认型号（32/64GB）、JetPack/L4T、CUDA/TensorRT、内存、功耗模式、Python/torch、磁盘。
2. **基线**：无；这是第一手事实。
3. **变量**：无（只读）。
4. **环境**：Orin 本机；不安装、不改配置、不下载。
5. **命令**：
   ```bash
   hostname; uname -m
   head -2 /etc/nv_tegra_release 2>/dev/null || true
   free -g; nproc
   nvpmodel -q 2>/dev/null | head -5
   timeout 3 tegrastats --interval 1000 2>/dev/null | head -2
   python3 -V
   python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())" 2>&1 | tail -1
   /usr/src/tensorrt/bin/trtexec --version 2>/dev/null | head -3 || true
   dpkg -l 2>/dev/null | grep -E "nvidia-jetpack|tensorrt" | head -8
   df -h / | tail -1
   ip -brief addr | head -10
   ```
6. **指标**：型号、L4T/JetPack、CUDA、TensorRT、RAM、功耗模式、torch 版本、磁盘可用。
7. **验收（G0）**：字段齐全；能判定 32/64GB 与 JetPack 6.2/7.2；能判定 torch 是否可用。
8. **失败判据**：无法登录；或 L4T/JetPack 版本无法识别。
9. **记录**：`data/mve0_probe.txt`（命令输出）、`result.md`（结论表）。
10. **回退**：只读，无副作用。

**结果（2026-11-26，S 级）**：

| 项 | 值 |
|---|---|
| 主机 / 架构 | `ubuntu` / aarch64 |
| 系统 | L4T R36.4.4 = **JetPack 6.2**；Ubuntu 22.04.5 |
| 内存 / CPU | 62,841 MB / 12 核；`nvpmodel` = MAXN (0) |
| CUDA / TensorRT | CUDA 12.6.11；TensorRT 10.3.0.30；`tensorrt` Python 10.3 |
| Python / 框架 | 3.10.12；**无 torch**；numpy 1.24、onnx 1.20、onnxsim、gs、opencv 4.12 |
| 权限 / 容器 | passwordless sudo 可用；Docker 29.10 |
| 磁盘 | 915 GB，可用 782 GB |
| 网络 | `eno1 192.168.5.31`；笔记本 192.168.5.22 可达；**pypi/HF 直连超时**；清华镜像 200（~1.6 MB/s） |
| 已装推理工具 | 无 llama.cpp / ollama / transformers / 模型文件 |

**判定**：64GB 分支；**Qwen 走 llama.cpp**（Edge-LLM 官方只支持 JetPack 7.2）；**SAM3 ONNX 在笔记本导出、Orin 用 trtexec 10.3 构建**（本机无 torch）。

**判定树**：
- 64GB + JetPack 7.2 → 走 4B/8B 分支；
- 32GB + JetPack 7.2 → 走 4B 分支，8B 仅试跑；
- JetPack 6.2 → 先确认 torch 版本；SAM3 PyTorch 可能不可用，优先 TRT；Edge-LLM 需按 6.2 兼容版本；
- 无 torch → 先走 TensorRT 路径或安装 aarch64 torch（需授权）。

---

## 2. MVE-1 — SAM3 3.0 在 Orin 上跑通（未运行）

1. **假设**：SAM3 3.0 图像模式在 924 px、单提示下 ≤2 s/帧，峰值 RAM ≤12 GB（32GB）/≤20 GB（64GB），掩码非空。
2. **基线**：Embedl AGX Orin 462 ms（INT8+FP16）/763 ms（FP16），924 px，TensorRT 10.1/10.3 [B]。
3. **变量**：
   - 路径：TensorRT（ONNX 在笔记本导出，Orin 用 trtexec 10.3 构建）；本机无 torch，不在 Orin 上跑 PyTorch；
   - 分辨率：1008 / 924 / 672 / 504；
   - 输入：文本提示 vs box prompt（模拟 YOLO 框）。
   - 控制：同权重、同精度（FP16）、同图、同预热。
4. **环境**：Orin 本机；SAM3 权重 `sam3.pt`（3.45 GB，gated）；ONNX 在笔记本用 torch cu128 导出（6 GB 显存不够时用 CPU/504 px），scp 到 Orin；Orin 用 TensorRT 10.3 的 `trtexec` 构建 FP16 引擎。
5. **指标**：p50/p95 延迟（ms）、峰值 RAM（`tegrastats`/`free`）、OOM、掩码面积/分数。
6. **验收（G1）**：924 px、单提示：p50 ≤2 s；峰值 RAM 在预算内；20 次无 OOM；掩码非空。
7. **失败判据**：OOM；或 p50 >4 s；或掩码为空/明显错误；或 TRT 引擎在 JetPack 7.2 上加载失败且无法重建。
8. **记录**：`data/mve1_sam3.csv`（路径、分辨率、输入、精度、p50、p95、峰值 RAM、掩码面积）、`logs/`、`result.md`。
9. **回退**：降到 672/504；或只做离线标注（不追求交互）。

**注意**：本机 TensorRT 10.3 正好在 Embedl 的验证范围内；但 Embedl 的引擎是 gated + 额外许可，且需与 sm_87 匹配。优先用 PINTO0309（MIT）的导出脚本自建引擎，并逐张检查掩码正确性 [A/C]。

---

## 3. MVE-2 — Qwen3-VL 评审（部分运行：8B 已跑通）

1. **假设**：Qwen3-VL-4B（Edge-LLM，INT4 AWQ/FP16）在 2 图 yes/no 评审上 ≤1 s、显存 ≤14 GB，并与 100 个手工标注样本的一致率 ≥85%。
2. **基线**：
   - (a) 无评审，仅 SAM3 分数阈值；
   - (b) HF Transformers + 同一 4B 的 logits（离线 oracle，慢但可作参照）。
3. **变量**：模型（2B/4B/8B）；输入（文本 / 1 图 / 2 图）；评审方式（文本 yes/no vs logits）。
4. **环境**：Orin；**llama.cpp**（CUDA 12.6、sm_87；本机 JetPack 6.2，Edge-LLM 官方只支持 7.2）；Qwen3-VL-4B-Instruct GGUF（Q4_K_M 约 2.5 GB）+ mmproj；笔记本下载后 scp 到 Orin；备选 HF Transformers + logits（离线 oracle）。
5. **指标**：prefill/ViT/生成延迟、显存、yes/no 一致率、假阳/假阴、失败率。
6. **验收（G2）**：2 图评审 p50 ≤1 s；显存 ≤14 GB；一致率 ≥85%；假阴（把正确掩码判错）≤10%。
7. **失败判据**：一致率 <75%；或假阴 >20%；或 2 图不支持；或显存超预算。
8. **记录**：`data/mve2_judge.csv`（样本、模型、输入、判决、人工标签、延迟、显存）、`logs/`、`result.md`。
9. **回退**：去掉 judge，只用 SAM3 分数；或换 8B（64GB）；或 HF logits 离线校准。

**结果（2026-11-26，S）**：实际用 Qwen3-VL-8B（Q4_K_M + Q8_0 mmproj，llama.cpp）：1 图 1.95 s、2 图 2.64 s、2 图 yes/no + logprobs 中位 1.18 s；`logprobs` 可用（`yes` -0.0057，`no` -8.91）；进程 RAM 约 12.1 GB。评审质量（100 样本一致率）**未做**。详见 [result.md](result.md)。

**关键差异**：SST 用 27B + logprob 比值；Orin 上 8B + llama.cpp logprobs 是不同模型/阈值，必须重新校准，不能引用 SST 的阈值 0.5 [S/C]。

---

## 4. MVE-3 — 端到端试点（未运行）

1. **假设**：固定英文短语 → SAM3 → 可选评审 → 掩码/质心，在 20–100 episode/片段上 ≥1 fps，掩码可用率 ≥80%。
2. **基线**：只用 SAM3（无评审）；以及现有 YOLO 框。
3. **变量**：有/无评审；分辨率；提示词（固定 vs Qwen 提词）。
4. **环境**：Orin；数据用 `jcheng-perception/evidence/` 与 `phase2/real_capture_20261117/` 的帧/片段（只读）；不接机器人。
5. **指标**：吞吐（帧/s）、端到端延迟、掩码可用率、质心稳定性、失败模式（空掩码/吞并/含机械臂）。
6. **验收（G3）**：≥1 fps；可用率 ≥80%；无 OOM；连续 100 帧无崩溃。
7. **失败判据**：<0.5 fps；或可用率 <60%；或需要逐类手写词表。
8. **记录**：`data/mve3_pilot.csv`、`logs/`、`result.md`；不保存原始图像。
9. **回退**：降到 672/504；或只做离线标注；或改用 SAM2.1 + YOLO 框。

---

## 5. MVE-4 — 顾问式服务与网络（未运行，依赖 G1–G3）

1. **假设**：Orin 上的 HTTP 服务能在 30 分钟内稳定处理 1 Hz 请求，p95 <1.5 s，显存无持续增长；笔记本可中转，不需要 Orin 直连机器人。
2. **基线**：现有 YOLO GPU 节点。
3. **变量**：请求频率（1/2 Hz）；会话生命周期；网络路径（直连 vs 笔记本中转）。
4. **环境**：Orin + 笔记本；录制帧回放；不接机器人、不发布 DDS、不打开设备。
5. **指标**：成功率、p50/p95、显存/RAM 增长、会话泄漏、崩溃。
6. **验收（G4）**：成功率 ≥99%；p95 <1.5 s；30 分钟显存增长 <300 MB；无泄漏。
7. **失败判据**：显存持续增长；或 p95 >3 s；或需要重启恢复。
8. **记录**：`data/mve4_service.csv`、`logs/service.log`、`result.md`。
9. **回退**：停服务；感知回到 YOLO；不改变任何现有配置。

**网络事实**：Orin `192.168.5.31`、笔记本 `192.168.5.22`、机器人 `10.42.0.x`；当前不互通 [S]。MVE-4 只验证"Orin → 笔记本"；"Orin → 机器人"需要单独的路由/双网口方案。

---

## 6. 风险登记

| 风险 | 触发条件 | 缓解 |
|---|---|---|
| 无法登录 Orin | 密钥不被接受 | 用户 `ssh-copy-id` 或提供可用密钥；不猜口令 |
| 型号是 32GB | `free -g` 显示 32 | 只上 4B；8B 仅试跑；27B 放弃 |
| JetPack 6.2 | L4T 36.x | 先确认 torch；SAM3 走 TRT；Edge-LLM 用兼容版本 |
| SAM3 TRT 引擎不兼容 | JetPack 7.2 + 10.3 引擎 | 重建引擎；验证掩码；必要时 PyTorch |
| Qwen 导出失败 | 笔记本 6GB 不够 | 在 Orin 上导出/构建；或换 llama.cpp |
| 评审一致率低 | <75% | 去掉 judge；只用 SAM3 分数 |
| 显存不足 | 4B+SAM3 > 预算 | 降分辨率；INT4；关掉视觉塔缓存 |
| 网络不通 | Orin 到机器人 | 笔记本中转；或双网口 |
| 许可问题 | SAM3 gated/Embedl 限制 | 只用官方 SAM3 + 自建 TRT；不碰 Embedl 引擎 |

---

## 7. 交付与停止条件

- **交付**：每个 MVE 的 `data/*.csv|txt`、`logs/`、`result.md`；报告 §11 状态更新。
- **停止**：G0 无法完成 → 停在"未运行"；G1 失败 → 只做离线标注或换 SAM2.1；G2 失败 → 去掉 judge；G3 失败 → 降分辨率或放弃 Orin 交互路线。
- **不做**：运动闭环、Orin 上训练、SST 全量数据集重建、复制 SST 代码。
