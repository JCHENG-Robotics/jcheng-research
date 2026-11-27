# Ultralytics — 仓库、许可与运行时行为

- **类型**：官方开源仓库 + 官方文档 + 论文摘要 + Issue 讨论 + PyPI 元数据
- **访问日期**：2026-11-26
- **阅读范围**：`ultralytics/ultralytics` tag **`v8.4.219`**，commit `3a31e32f2e254a13f86ea274d6331e19d0cb4d47`（2026-11-25）的浅克隆静态审查；读了 `README.md`、`pyproject.toml`、`LICENSE`、`CONTRIBUTING.md`、`docs/en/` 的模型/部署/隐私/许可页、`ultralytics/` 的核心源码、`.github/workflows/`、`tests/` 计数；读了 issue #22640、#26703、#25030、#21241、#22791 的正文与维护者回复；读了 YOLO26 论文摘要与作者。**未执行**仓库代码；未在 Pi 5/AGX Orin/RTX 3060 上运行 YOLO26；未读论文全文附录与消融表。GitHub API 与 PyPI JSON 为 2026-11-26 快照。

## 基本事实

| 项 | 值 |
|---|---|
| 仓库 | `ultralytics/ultralytics`，Python，`main` |
| 快照 | `v8.4.219` / `3a31e32f2e25` / 2026-11-25 |
| 规模 | 63,766 stars；12,043 forks；35 open issues + 32 open PRs；约 67 MB（GitHub `size` 68,517 KB） |
| 代码 | 233 个 `.py`，83,585 行；`tests/` 230 个 `test_` |
| 许可 | AGPL-3.0（`LICENSE`、PyPI、GitHub 三处一致）；Enterprise 双许可 |
| Python | `requires-python >=3.8`；`ultralytics-platform` 仅 3.11+ |
| 下载 | 约 5.16M/月（pypistats，近 30 天） |
| 发布 | `v8.4.212`→`v8.4.219` 共 8 个 release / 12 天 |
| 模型线 | v3/v5/v8/v9/v10/v11/v12/**26**；**27 仅预览、未发布** |

## 许可（A）

- `LICENSE:152-153`：AGPL §2，"You may make, run and propagate covered works that you do not convey, without conditions so long as your license otherwise remains in force."
- `LICENSE:539` 起 §13：仅在**修改程序并提供远程网络交互**时要求提供 Corresponding Source。
- `docs/en/help/contributing.md:240-248`：使用 YOLO 代码/模型的项目"entire derivative work"须以 AGPL-3.0 开源；否则购买 Enterprise License。
- issue #22640（2025-11-10，glenn-jocher）：纯内部使用也要求公开整个应用与衍生模型，仅向员工提供源码不够。
- issue #26703（2026-10-16，pderrenger；2026-11-18，glenn-jocher）：A/B 进程用 socket 隔离不豁免 A；需公开完整项目源码、训练脚本、配置与训练权重；训练数据仅在运行/再训练所需且可再分发时要求披露。
- 结论：厂商公开口径**宽于** AGPL 文本的私有使用豁免；法律效果未定，需法务意见（报告按 C 级处理）。

## 运行时行为（A）

| 行为 | 默认 | 关闭/控制 | 代码位置 |
|---|---|---|---|
| 缺依赖自动安装 | 开 | `YOLO_AUTOINSTALL=False`、`ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS=1` | `utils/__init__.py:81`；`utils/checks.py:536-660`（优先 `uv pip install --break-system-packages`） |
| 匿名使用分析 | 开（`sync=True`） | `settings.update({"sync": False})`、`YOLO_OFFLINE=1` | `utils/events.py:50-235`；`docs/en/help/privacy.md`；POST 到 `google-analytics.com/mp/collect`（`:69`），predict/train/val/export 结束时入队，30 s 限流 |
| Sentry | 条件开 | `sync=False` 或不装 `sentry-sdk` | `utils/__init__.py:1492-1564`；仅 `yolo` CLI + pip + 非 git + 在线 + 非测试 |
| 在线检查 | 导入时 DNS | `YOLO_OFFLINE=1` | `utils/__init__.py:1147-1162,1283` |
| 权重自动下载 | 开（按名字） | 绝对路径、`YOLO_OFFLINE=1` | `utils/downloads.py:543` |
| 反序列化 | `weights_only=False` | `ULTRALYTICS_SAFE_LOAD=1`（opt-in 白名单） | `utils/patches.py:228-252`；`nn/tasks.py:1861` |

## 工程与维护（A）

- 230 个测试：`test_python.py` 120、`test_exports.py` 38、`test_solutions.py` 17、`test_engine.py` 15、`test_cli.py` 13、`test_cuda.py` 13、`test_integrations.py` 6、`test_ndjson_converter.py` 6、`test_rocm.py` 2。
- CI：`ubuntu-latest`、`macos-latest`、`ubuntu-26.04-arm`；Python 3.13 主矩阵；`:518` Raspberry Pi runner；GPU runner；ROCm runner；隔离 venv 导出测试；`YOLO_AUTOINSTALL: "false"` 保持 hermetic。
- 每日 fuzz `yolo` CLI（`.github/workflows/fuzz.yml`）；stale bot issue 30+10 天、PR 90+30 天。
- 导出：ONNX/TensorRT/OpenVINO/NCNN/RKNN/TFLite/TF/MNN/ExecuTorch 等；`engine/exporter.py:911-915` 有 JetPack 6 / TRT 10.3 INT8 限制说明。

## 性能（厂商/公开，A/B）

| 硬件 | 模型/格式 | 数字 |
|---|---|---|
| T4 | YOLO26n TensorRT | 1.7 ms；COCO 40.9 mAP（NMS）/40.1（e2e） |
| Pi 5 | YOLO26n ONNX | 128.42 ms/im（7.79 FPS），mAP 40.1；YOLO11n 147.20 ms（6.79 FPS），39.5 |
| AGX Orin 64GB（JP7.2） | YOLO26n PyTorch / TRT FP16 / TRT INT8 | 11.58 / 2.62 / 2.30 ms |
| AGX Orin（issue #25030） | YOLO26n `.pt` | 约 25 ms；换 engine 后与官方一致 |

生态内实测（`jcheng-perception/capability.yaml:123-134`，S）：RTX 3060 Laptop `yolov8s.pt` 9.0 ms FP32 / 7.4 ms FP16；CPU 154.3 ms；首帧 1.04 s；ROS 节点平均 54.3 ms；GPU venv 6.8 GB。

## 论文

- G. Jocher, J. Qiu, M. Liu, S. Lyu, F. C. Akyon, M. E. Kalfaoglu, "Ultralytics YOLO26: Unified Real-Time End-to-End Vision Models," arXiv:2606.03748, 2026-06-02. 摘要：双头 NMS-free、去 DFL、MuSGD、Progressive Loss、STAL；COCO 40.9–57.5 mAP；T4 TRT 1.7–11.8 ms；CPU ONNX 相比 YOLO11n 快 up to 43%。作者含 Ultralytics 创始人/维护者，属厂商自评；未读全文附录/消融。

## 生态内使用

- `jcheng-perception/config/gpu.yaml:22,42` 两台相机均为 `backend: ultralytics`。
- `detectors.py:200` 延迟导入 `YOLO`；`:268` `model.predict(image_bgr, ...)`；pose/OBB 仅此后端支持（`:420-423` 等）。
- `node.py:109` 每相机 worker 线程；`:169` 调 `detect`；`:365` `MultiThreadedExecutor(4)`；无共享 `YOLO` 对象。
- `docs/MODEL_ITERATION.md`：venv 内 Ultralytics 8.4.216、torch 2.9.1+cu128。
- `LICENSE-REVIEW.md:22` 已标注 AGPL；`:49` 写"existing optional runtime; not a default"，但 `gpu.yaml` 实际默认是 ultralytics（文档/配置不一致）。
- `deploy/README.md:45`：GPU venv 6.8 GB；镜像不装 `opencv-python`，用 apt `python3-opencv`。

## 平替候选（附录 A，2026-11-27）

- **D-FINE**（Apache-2.0）：<https://github.com/Peterande/D-FINE>；README model zoo：D-FINE-N 42.8 AP / 2.12 ms T4 / 4M 参数；支持 ONNX 导出与 `trtexec`。
- **RF-DETR**（Apache-2.0：N/S/M/L；Atto/Femto/Pico/XL/2XL 为 PML 1.0）：<https://github.com/roboflow/rf-detr>；SAB 同口径表（T4 TRT FP16、COCO `val2017`）：N 48.4 AP / 2.3 ms / 30.5M / 384，S 53.0 / 3.5 / 32.1 / 512。
- **RTMDet**（Apache-2.0，MMDetection）：<https://github.com/open-mmlab/mmdetection/tree/main/configs/rtmdet>；README：RTMDet-tiny 41.1 AP / 2.34 ms T4（TRT 8.4.3）/ 4.8M / 8.1 GFLOPs。
- **PicoDet**（Apache-2.0，PaddleDetection）：<https://github.com/PaddlePaddle/PaddleDetection/tree/develop/configs/picodet>；README：M-416 37.5 AP / 12.7 ms CPU，S-416 32.5 AP / 6.6 ms CPU（x86）。
- **NanoDet**（Apache-2.0）：<https://github.com/RangiLyu/nanodet>；README：Plus-m-1.5x-416 34.1 AP / 25.49 ms（4×A76）/ 2.44M / 2.97 GFLOPs。
- **LW-DETR**：仅在 RF-DETR 的 SAB 表中引用（T 42.9 AP / 1.9 ms / 12.1M，Apache-2.0 由该表标注）；本次未审仓库。
- **阅读范围**：各 README benchmark 表、GitHub API 的 license/活跃度字段，2026-11-27；**未训练、未导出、未在本机运行**。

## 相关

- 报告：[Ultralytics 仓库调研](../../reports/20261126-ultralytics-repository-review.md)
- 实验：[运行时审计设计](../../experiments/20261126-ultralytics-runtime-audit/design.md)
- 前置：`references/perception/jetson-agx-orin.md`（JetPack 6.2 / TRT 10.3 / 无 torch / 19V 供电）
