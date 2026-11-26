# Ultralytics 运行时审计与后端一致性 — MVE 设计

- **状态**：pre-registered，**未运行**（截至 2026-11-26）。
- **关联报告**：[Ultralytics 仓库调研](../../reports/20261126-ultralytics-repository-review.md)
- **来源记录**：[ultralytics-repository.md](../../references/perception/ultralytics-repository.md)
- **决策对象**：是否保留 `backend: ultralytics`、是否切换到导出的 ONNX/OpenVINO/TensorRT、以及需要哪些环境开关。

## 约束

- 不做任何实机运动；本实验只跑离线帧，不接机器人。
- 权重不进入 git；记录 SHA-256 与来源。
- 运行类任务超过 60 s，执行前需操作者确认；MVE-1 约 2 h，MVE-2 约 1 h，MVE-3 约 1–2 天。
- 使用独立 venv，不修改 ROS 系统 Python；不改生产 `config/gpu.yaml`，直到验收通过。

## MVE-1：运行时加固审计（2 h）

**假设**：在 `YOLO_AUTOINSTALL=False`、`YOLO_OFFLINE=1`、`settings["sync"]=False`、`ULTRALYTICS_SAFE_LOAD=1` 下，`ultralytics==8.4.216` 连续推理 2 小时不产生任何出站连接与 pip/uv 安装，RSS 增长 <5%。

| 项 | 设计 |
|---|---|
| 基线 | 默认设置（`sync=True`、`AUTOINSTALL=True`）下同一循环；只用于对比出站/RSS，不用于生产 |
| 自变量 | 四个开关（全开 vs 全关） |
| 控制变量 | 同一笔记本、RTX 3060 Laptop 6 GB、同一 `yolov8s.pt`、同一 200 帧循环、同一 Python 3.12 venv、同一 `imgsz=640/conf=0.35` |
| 环境 | `~/.venvs/jcheng-perception-gpu`（Ultralytics 8.4.216、torch 2.9.1+cu128）或新建隔离 venv |
| 指标 | 出站连接（`tcpdump -ni any port 443 or 80` / `ss -tnp`）、`execve` 的 pip/uv 次数（`strace -f -e execve`）、RSS（每 60 s，`/proc/<pid>/status`）、推理 p50/p95、异常数 |
| 验收 | 0 次到 `google-analytics.com` / `sentry.io` / `pypi.org` 的连接；0 次 pip/uv 安装；RSS 增长 <5%；p95 ≤ 基线 120% |
| 失败 | 任意外联、任意安装、RSS 增长 ≥10%、未处理异常 |
| 记录 | `result.md` + `rss.csv`（时间、RSS、p50、p95、连接数） |
| 回退 | 删除实验 venv；生产配置不变 |

## MVE-2：后端一致性（1 h）

**假设**：同一权重导出的 ONNX/OpenVINO 与 `.pt` 在 200 帧固定样本上检测框匹配率 ≥99%（IoU>0.99、score 差 <0.01），p95 延迟 ≤ `.pt` 的 120%。

| 项 | 设计 |
|---|---|
| 基线 | `ultralytics` + `.pt`（当前生产路径） |
| 自变量 | `ultralytics` / `onnxruntime` / `openvino` |
| 控制变量 | 同一 200 帧（矿石 100 + 货架 100）、同一 `imgsz`/`conf`/`iou`/`max_det`、同一预处理、同一 3060 |
| 指标 | 匹配率、IoU 分布、score 差、p50/p95、漏检/误检 |
| 验收 | 匹配率 ≥99%；p95 ≤ 基线 120%；无系统性坐标偏移（均值 ≤2 px） |
| 失败 | 匹配率 <95%、p95 >150%、或固定偏移 >2 px |
| 记录 | `result.md` + 逐帧 CSV；导出命令、权重/导出件 SHA-256 |
| 回退 | 生产继续用 `.pt`；导出件保留但不切换 |

## MVE-3：许可干净训练对比（1–2 天，可选）

**假设**：RF-DETR-nano / RTMDet-tiny / YOLOX-tiny 在矿石/货架数据上达到 YOLOv8n 基线 −2 mAP 以内，导出 ONNX 可被现有后端加载。

| 项 | 设计 |
|---|---|
| 基线 | 现有 YOLOv8n 权重与 mAP（来自 `jcheng-perception` 的 ore/shelf 证据） |
| 自变量 | 训练框架/模型 |
| 控制变量 | 同一数据切分、同一输入尺寸、同一增强预算、同一评估脚本 |
| 指标 | mAP50-95、AP50、p50/p95（3060/Orin）、导出成功率、许可 |
| 验收 | mAP ≥ 基线 −2；延迟 ≤ 基线 120%；ONNX 可加载 |
| 失败 | mAP < 基线 −5、导出/运行失败、6 GB OOM 不可恢复 |
| 记录 | `result.md` + 训练配置 + 权重 SHA-256（权重不入 git） |
| 回退 | 继续用现有 YOLOv8n + 生产 ONNX |

## 执行顺序与依赖

1. MVE-1（运行时加固）→ 决定开发/实验环境开关。
2. MVE-2（后端一致性）→ 决定生产是否切到 ONNX/OpenVINO。
3. MVE-3（可选）→ 仅在许可结论要求替换训练框架时执行。

## 明确不做

- 不在机器人上安装/升级 Ultralytics。
- 不加载来源不明的 `.pt`。
- 不用 `.pt` 的 Orin 延迟做预算；Orin 只认目标机导出的 TensorRT engine。
- 不把 YOLO27 纳入实验（未发布）。
