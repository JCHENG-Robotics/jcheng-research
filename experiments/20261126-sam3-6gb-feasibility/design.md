# 实验设计 — SAM 3 在 6 GB 笔记本 3060 上的可行性与质量门禁

- **日期**：2026-11-26
- **状态**：MVE-0…MVE-3 **均未运行**；MVE-0 阻塞在 HF gated 权重（需用户接受 SAM License 并生成 token）
- **负责人**：J. Cheng（决策/授权），ZCode（执行/分析）
- **相关报告**：`reports/20261126-sam3-sst-open-source-attempt-route.md`
- **上游版本**：`facebookresearch/sam3` main `31cb7e62`（2026-11-17）；SAM 3.0 权重 `facebook/sam3/sam3.pt`（3.45 GB，gated）
- **本机环境**：Python 3.12.3、pip 24.0、RTX 3060 Laptop **6144 MiB**、驱动 595.99.02 / CUDA 13.2、27 GB RAM、16 核；无 torch；磁盘可用 249 GB

> 本文件只描述设计与门禁，不包含可被机器人加载的代码。所有权重放 `/opt/jcheng/models/sam3/`，不进入任何 git 仓库。

---

## 0. 前置动作（用户，必须先完成）

1. 登录 Hugging Face，在 <https://huggingface.co/facebook/sam3> 接受 SAM License 并申请访问（`gated: manual`，需共享用户名/邮箱）。
2. 生成 **read** token，放到 `~/.cache/huggingface/token`（权限 0600），或执行 `hf auth login`。
3. 明确批准以下下载（约 3.5 GB 权重 + 约 3 GB torch wheel）：
   - `facebook/sam3` → `sam3.pt` 到 `/opt/jcheng/models/sam3/sam3.pt`
   - 上游代码 `git clone https://github.com/facebookresearch/sam3` 到 `/opt/jcheng/src/sam3`，checkout `31cb7e62`
4. 可选：若 MVE-3 需要对照，批准 `facebook/sam3.1`（3.5 GB）。**默认不下载**，因为 1–3 物体场景 3.1 负优化（报告 F3）。

**不在本设计内的动作**：非官方镜像/转存权重、把权重提交进仓库、把 SAM3 接入运动链、任何实机运动。

---

## 1. MVE-0 — 6 GB 显存与延迟基准（未运行）

1. **假设**：SAM 3.0 图像模式在 504–672 px、单物体、bf16 下，峰值显存 ≤5.5 GB，p50 延迟 ≤1 s，能稳定跑 20 次不 OOM。
2. **基线**：无（首次测量）；对照点用上游 issue 的 3090 分项计时（1008 px bf16：编码 110 ms + 跟踪 21 ms + 文本 22 ms；504 px：46/5/12 ms）[B: #424 评论]。
3. **变量**：
   - 分辨率：1008 / 756 / 672 / 504（方形 resize）。
   - 物体数：1（单提示）、2（两个提示取并集）。
   - 输入：文本提示 vs box prompt（模拟 YOLO 框）。
   - 控制：同一权重、同一精度（bf16 autocast）、同一预热次数、同一图像。
4. **环境**：venv（Python 3.12）+ `torch==2.10.0` cu128 + 上游 `sam3` 可编辑安装；`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`；`torch.inference_mode()`；每配置 3 次预热 + 20 次计时；`torch.cuda.max_memory_allocated()` 与 `max_memory_reserved()` 都记录。
5. **指标**：峰值 allocated/reserved（MiB）、p50/p95 延迟（ms）、OOM 次数、掩码分数与面积（健全性检查）。
6. **验收（G0）**：504 px、单物体、图像模式：峰值 reserved ≤5.5 GB；p50 ≤1 s；20 次无 OOM；掩码非空。
7. **失败判据**：504 px 仍 OOM；或 p50 >2 s；或掩码为空/明显错误 → 停止，转路线 B/C。
8. **记录**：`data/mve0_bench.csv`（配置、分辨率、物体数、精度、峰值、p50、p95、OOM、掩码面积）、`logs/mve0_*.txt`（命令、版本、GPU 状态）、`result.md`。
9. **回退**：删除 venv 与权重即可；不影响任何现有仓库。

**补充测量（同一天，可选）**：50–100 帧短序列视频，504 px、1 个提示，记录每帧延迟与显存增长斜率；如果增长 >5 MB/帧或峰值 >5.8 GB，视频模式直接判负。

---

## 2. MVE-1 — 自有帧上的掩码质量与提示词稳定性（未运行）

1. **假设**：在 ArmPi 真实相机帧上，文本提示与 box prompt 都能给出可用掩码；box prompt（YOLO 框）比文本提示更稳定；不需要逐类手写词表。
2. **基线**：
   - (a) 现有 YOLO 框（作为定位参照）；
   - (b) SAM2.1-tiny + 同一 YOLO 框（Apache-2.0，回退方案）。
3. **变量**：输入方式（文本短语 / box prompt / SAM2.1 框）；提示词变体（同义词 3 个、颜色前缀 2 个）；物体类别 5 个。
4. **数据**（只读，不复制进本仓库）：
   - `jcheng-perception/evidence/hardware_20261124_fixedpoint/snap_ext_rgb.jpg`
   - `jcheng-perception/evidence/hardware_20261124_fixedpoint/snap_wrist_rgb.jpg`
   - `phase2/real_capture_20261117/rgb_*.png`（多帧、含深度）
   - 必要时补拍：**不涉及运动**，仅相机采集，需单独授权。
5. **环境**：同 MVE-0；标注用 20–30 帧，人工画框/多边形作为参照；不需要机器人运动。
6. **指标**：
   - mask IoU（vs 人工多边形，若有）；
   - 质心误差（px，及用深度反投影后的 mm）；
   - 提示词变体间的掩码面积变化率；
   - 失败率（空掩码、掩码含机械臂/桌面、掩码吞并相邻物体）；
   - 每帧人工修正时间（秒）。
7. **验收（G1）**：≥80% 帧质心误差 ≤ 物体短边的一半；提示词变体面积变化 ≤10%；不出现"必须逐类写词表才能工作"的证据；box prompt 不劣于文本提示。
8. **失败判据**：>20% 帧空掩码或掩码含机械臂；或提示词变体导致掩码面积变化 >30%；或必须像 SST 那样逐类修补 → 判负，转路线 B/D。
9. **记录**：`data/mve1_quality.csv`（帧、类别、输入方式、IoU、质心误差、面积、失败原因）、`logs/`、`result.md`；不保存原始图像。
10. **回退**：只读分析，无副作用。

**关键对照**：同一帧、同一物体，比较"文本提示 `cup`"与"YOLO 框 + box prompt"。如果两者质量接近，则后续一律用 box prompt，避免英文词表与翻译问题（报告 F9）。

---

## 3. MVE-2 — 顾问式 HTTP 服务与感知接入（未运行，依赖 G0/G1）

1. **假设**：单进程、单 GPU、stdlib HTTP 的掩码服务可在 30 分钟内稳定处理 1 Hz 请求，p95 <1 s，显存无持续增长；输出可作为 advisory target 的一种来源。
2. **基线**：现有 YOLO GPU 节点（同侧、同通道）。
3. **变量**：请求频率（1 Hz / 2 Hz）；会话生命周期（每帧新建 vs 复用）；空闲超时（60 s / 300 s）。
4. **环境**：笔记本 3060；录制帧回放（不用机器人）；服务只读帧、返回掩码/质心；不加入 41/42/43 域，不发布 vendor 话题，不打开设备。
5. **接口**：HTTP/JSON，帧用 base64（或共享内存），掩码用 RLE/PNG；`/health` 返回 `{ok, loaded, sessions, vram_mib}`；空闲会话回收；单 GPU 锁。
6. **指标**：30 分钟内的请求成功率、p50/p95 延迟、显存/RSS 增长、会话泄漏数、崩溃次数。
7. **验收（G2）**：成功率 ≥99%；p95 <1 s；30 分钟显存增长 <200 MB；无会话泄漏；进程可被 systemd 正常重启。
8. **失败判据**：显存持续增长（>500 MB/30 min）；或 p95 >2 s；或需要重启才能恢复 → 判负，不进入感知。
9. **记录**：`data/mve2_service.csv`（时间、请求、延迟、显存、会话数）、`logs/service.log`、`result.md`。
10. **回退**：停服务；感知回到 YOLO；不改变任何现有配置。

**安全边界**：MVE-2 只做 advisory，不调用 `ExecuteMotion`、不申请 lease、不触发运动。若未来要做单次实机抓取，必须另开一次**单独授权**的硬件会话，并按 `jcheng-perception` 的固定点流程执行。

---

## 4. MVE-3 — 离线标注性价比（未运行，可选）

1. **假设**：SAM3 离线标注（掩码 + 质心）在 100 帧上的"质量/人工修正时间"明显优于 SAM2.1-tiny，足以抵消其显存与许可成本。
2. **基线**：SAM2.1-tiny + 同一 YOLO 框；人工纯手绘作为上限参照。
3. **变量**：模型（SAM3 / SAM2.1-tiny）；输入（文本 / box）；帧数 100。
4. **环境**：同 MVE-1；离线批处理，无机器人。
5. **指标**：每帧耗时、峰值显存、mask IoU、人工修正秒数、失败率。
6. **验收**：SAM3 的 IoU 或修正时间至少一项显著优于 SAM2.1（>20%），且失败率不更高。
7. **失败判据**：无显著优势 → 未来标注一律用 SAM2.1。
8. **记录**：`data/mve3_annotation.csv`、`result.md`。
9. **回退**：只读分析。

---

## 5. 风险登记

| 风险 | 触发条件 | 缓解 |
|---|---|---|
| HF 访问被拒/延迟 | 许可申请未通过 | 路线 B/C；SAM2.1 不 gated |
| 6 GB OOM | 1008 px 或视频多物体 | 降到 504/672；单物体；短序列；`expandable_segments` |
| 3.1 加载失败 | 误用 3.1 | 固定 3.0；不下载 3.1 |
| 提示词脆弱 | 需要逐类词表 | 改用 box prompt；否则回退 |
| 许可证不可接受 | 生态评审 | 删除权重；改用 Apache-2.0 路线 |
| 显存泄漏 | 长会话 | 空闲回收；每帧新建；监控 `/health` |
| 把 advisory 误当运动许可 | 接入感知后 | 保持 system 层唯一运动入口；单独授权 |

---

## 6. 交付与停止条件

- **交付**：`data/*.csv`、`logs/*.txt`、`result.md`（每个 MVE 一份）；更新报告 §11 的状态。
- **停止**：G0 失败 → 停 SAM3 路线；G1 失败 → 转路线 B/D；G2 失败 → 停服务；任一阶段出现许可证问题 → 删除权重与代码。
- **不做的实验**：任何需要运动的抓取、任何 SAM3 训练/微调、任何 3.1 多物体基准、任何 Pi 5 上的 SAM3 部署。
