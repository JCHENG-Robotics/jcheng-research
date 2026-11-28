# Ultralytics 仓库调研：工程质量、许可边界与 JCHENG 感知栈适配

> 报告状态：**draft**（draft | reviewed | superseded）。日期：2026-11-26。
> 作者：ZCode（研究代理），for J. Cheng。评审：pending。
> 本报告影响的决策：是否继续把 Ultralytics 作为 `jcheng-perception` 的检测后端与训练/导出工具；如果继续，用什么许可、版本、运行时边界和回退方案。
> 研究边界：**未在本机运行 ultralytics**。仓库事实来自 `v8.4.219`（commit `3a31e32f2e25`）的源码、文档、CI 与 issue 静态审查，以及 PyPI/GitHub API、arXiv 和 `jcheng-perception` 的既有实测记录；**未做任何法律判断**，许可结论只区分"厂商口径"与"AGPL 文本"，实际法律效果需法务意见。未在 Pi 5 / AGX Orin 上运行本仓库的 YOLO26，相关硬件数字均为厂商或第三方记录。

**证据等级**：**S** 本系统实测 · **A** 一手论文/官方仓库/官方文档/官方基准 · **B** 可信间接工程证据 · **C** 推断 · **D** 未验证假设。

## 00. 核查快照（2026-11-26）

| 项 | 值 | 来源/等级 |
|---|---|---|
| 仓库 | `ultralytics/ultralytics`，Python，默认分支 `main` | GitHub API [A] |
| 快照 | tag **`v8.4.219`**，commit `3a31e32f2e254a13f86ea274d6331e19d0cb4d47`，2026-11-25 | GitHub API / `git log` [A] |
| 规模 | **63,766 stars / 12,043 forks**；35 open issues + 32 open PRs；约 67 MB（GitHub `size` 68,517 KB） | GitHub API [A] |
| 代码量 | 233 个 `.py`，**83,585 行**；`tests/` 下 **230** 个 `test_` 函数 | 本地浅克隆 [A] |
| 许可 | **AGPL-3.0**（仓库 `LICENSE`、PyPI、GitHub license 字段一致） | 三处一致 [A] |
| 最新版 | PyPI `8.4.219`，`requires-python >=3.8` | PyPI JSON [A] |
| 采纳量 | **约 516 万次/月** PyPI 下载（近 30 天），19.3 万/日 | pypistats [B] |
| 模型线 | YOLOv3/v5/v8/v9/v10/v11/v12/**YOLO26**；**YOLO27 仅预览、未发布** | 仓库 `cfg/models/`、README [A] |
| 当前生态内版本 | `jcheng-perception` GPU venv：**Ultralytics 8.4.216**、torch 2.9.1+cu128 | `docs/MODEL_ITERATION.md` [S] |
| 论文 | YOLO26：arXiv **2606.03748**（2026-06-02），作者含 Ultralytics 创始人/维护者 | arXiv API [A] |
| 发布节奏 | `v8.4.212`→`v8.4.219`：**8 个 release / 12 天** | GitHub releases [A] |

**本次实际阅读范围**：仓库根文档（`README.md`、`pyproject.toml`、`LICENSE`、`CONTRIBUTING.md`、`AGENTS.md`/`CLAUDE.md`）、`docs/en/` 的模型/部署/隐私/许可页、`ultralytics/` 的核心源码（`__init__.py`、`utils/__init__.py`、`utils/checks.py`、`utils/events.py`、`utils/patches.py`、`nn/tasks.py`、`engine/exporter.py`、`engine/predictor.py`、`utils/downloads.py`）、`.github/workflows/`、`tests/` 计数、issue #22640/#26703/#25030/#21241/#22791 的正文与维护者回复。未逐行审查 83.6k 行全部源码，未执行训练、导出或推理。

---

## 01. Executive Summary（执行摘要）

**推荐：把 Ultralytics 定位为"开发期训练/导出工具"，不要把它作为出厂运行时依赖。** 现有 `jcheng-perception` 已经具备 Ultralytics `.pt`、ONNX Runtime、OpenVINO、OpenCV DNN 四条推理路径；检测任务的迁移成本低。若需要保留 pose/OBB 或继续用 YOLO 系列训练，必须先把许可问题定案：**要么取得 Enterprise License，要么让部署图只运行导出的 ONNX/OpenVINO/TensorRT 工件，并接受权重/导出件的许可不确定性由法务评估**。

支撑结论的五条事实：

1. **工程质量是同类里最高一档 [A]。** 233 个源文件、83.6k 行、230 个测试；CI 覆盖 Ubuntu/macOS/Windows/Ubuntu-ARM（主矩阵 Python 3.13，include 覆盖 3.8/3.14/3.15）、Raspberry Pi runner、GPU runner、ROCm、隔离 venv 的导出矩阵，另有每日 fuzz 工作流；release 近乎每日。YOLO26 论文、完整文档、迁移指南、Issue/PR 模板齐备。`jcheng-perception` 已实测：RTX 3060 上 `yolov8s.pt` **9.0 ms FP32 / 7.4 ms FP16** 稳态，CPU **154.3 ms/frame**，首帧 1.04 s [S]。
2. **许可是决策阻塞项，而不是普通依赖注脚 [A]。** 代码与 PyPI 元数据都是 **AGPL-3.0**；官方文档要求"使用模型或代码的项目整体以 AGPL-3.0 开源"，并提供 Enterprise License 作为替代。维护者在 issue #22640、#26703 中进一步明确：**即使纯内部使用、即使把 YOLO 进程与其他进程用 socket 隔开，也要求公开整个项目及衍生权重**，否则购买 Enterprise License。这个口径比 AGPL §2 的"不 convey 的私有运行不受条件约束"更严格，法律上存在争议（见 §08 F1），但对一个尚未完成 license review、仓库无 `LICENSE` 的私有机器人栈，这是必须由法务拍板的商业风险。
3. **默认运行时行为不适合机器人/离线环境，但可关 [A]。** `YOLO_AUTOINSTALL` 默认 **True**，缺依赖时会在运行时 `pip install`（优先 `uv pip install --break-system-packages`）；`sync` 默认 **True**，会向 Google Analytics 发送匿名使用事件（CPU 型号、torch 版本、模型文件名、任务、设备、耗时），并在安装 `sentry-sdk` 且通过 `yolo` CLI 运行时上报崩溃；`.pt` 加载默认 `weights_only=False`，**可执行任意 pickle**，安全加载是 opt-in（`ULTRALYTICS_SAFE_LOAD=1`）。这些都有官方开关，但必须显式配置并验证。
4. **性能不是瓶颈，但厂商数字不能直接搬到我们的硬件 [A/B]。** 官方 YOLO26n：COCO 40.9 mAP（NMS）/40.1（NMS-free），T4 TensorRT **1.7 ms**；Raspberry Pi 5 ONNX **128.4 ms/im（7.79 FPS）**；AGX Orin 64GB（JetPack 7.2）PyTorch **11.58 ms**、TensorRT FP16 **2.62 ms**、INT8 **2.30 ms**。但 issue #25030 显示 Orin 上 `.pt` 实测约 **25 ms**，换 TensorRT engine 后才与官方基准一致；本机 Orin 是 **JetPack 6.2 / TensorRT 10.3**，与官方基准的 7.2 不同，且 exporter 对 TRT 10.3 的 INT8/NMS 有已知限制 [A]。
5. **版本节奏要求严格锁定 [A]。** 12 天 8 个 release，行为变化（例如 Sentry SDK 3 兼容、导出后端修复）会进入 patch 版本；生态内 8.4.216 与最新 8.4.219 已相差 3 个版本。生产环境必须固定精确版本、离线安装、并在升级时跑后端回归。

**主要风险**：许可口径与 AGPL 文本冲突，实际义务取决于是否 convey、是否提供网络服务以及法务解释 [C]；其次是默认遥测/自动安装/不安全反序列化在机器人上的可靠性与供应链风险 [A]；第三是长期运行的 RSS 增长（issue #21241 记录了访问推理结果时的内存上涨，OpenVINO 后端，1 小时可到 GB 级）[B]。

**一句话**：**这是一个工程质量很高、但许可与默认运行时行为都不适合"直接塞进产品"的仓库；用它的正确姿势是"开发期用、导出后跑"，并把许可决策前置。**

---

## 02. Research Questions（研究问题）

**主问题**：`ultralytics/ultralytics` 是什么样的仓库；它的能力、工程质量、许可与运行时行为是否适合 JCHENG 的感知栈；如果不适合，替代路径是什么？

| # | 子问题 | 回答位置 |
|---|---|---|
| Q1 | 仓库的模型/任务覆盖、代码规模、维护与发布状态如何？ | §06.1–06.5、§00 |
| Q2 | AGPL-3.0 + Enterprise 双许可对私有机器人栈意味着什么？厂商口径与法条文本是否一致？ | §06.6、§08 F1 |
| Q3 | 默认运行时有哪些网络、安装、反序列化副作用？能否关闭？ | §06.7–06.8 |
| Q4 | 在 Pi 5、RTX 3060、AGX Orin 上的真实性能证据是什么？ | §05、§07、§08 F4 |
| Q5 | 与 `jcheng-perception` 现有五后端架构的适配性和迁移成本？ | §03、§09 |
| Q6 | 继续用 / 替换 / 购买许可，各自的最小验证实验是什么？ | §10、§11 |

**约束**：

| 类别 | 约束 |
|---|---|
| 许可 | `jcheng-perception` 无 `LICENSE`，license review 未关闭；生态规则要求新依赖先记录许可与权重来源（`jcheng-perception/LICENSE-REVIEW.md`） |
| 架构 | 感知只发布 advisory targets；不得绕过 `ExecuteMotion`、lease、stop latch；L3 不得发布厂商话题或直接控制设备 |
| 硬件 | Pi 5 8 GB（Humble、Python 3.10）、笔记本 RTX 3060 Laptop **6 GB**、AGX Orin 64 GB（JetPack 6.2 / TRT 10.3） |
| 网络 | 机器人/Orin 不应依赖公网；Orin 直连 PyPI/HF 不通（既有记录） |
| 安全 | 权重不进入 git；不加载不可信 `.pt`；不在无人值守流程里触发运动 |
| 时间 | 本报告为静态调研；运行类验证放到 §11 的 MVE，需另行授权 |

**交付物**：本报告 + 来源记录 `references/perception/ultralytics-repository.md` + 预注册实验 `experiments/20261126-ultralytics-runtime-audit/design.md`。

---

## 03. Current System Analysis（当前系统）

### 03.1 感知栈怎么用 Ultralytics

`jcheng-perception` 的 GPU 节点是"每相机一个 worker 线程 + 每 worker 一个 detector 实例"的结构：`CameraWorker` 在 `node.py:109` 启动独立线程，`node.py:169` 调 `self._detector.detect(image)`；`MultiThreadedExecutor(num_threads=4)` 只负责 ROS 回调。因此**没有多线程共享同一个 `YOLO` 对象**的竞态（`YOLO` 的 predictor 持有可变状态，本来也不是线程安全的）[A/C]。

`build_detector()` 支持五种模型后端（另有 `aruco`/`apriltag` 标记检测；`detectors.py`）：

| backend | 运行时 | 支持任务 | 备注 |
|---|---|---|---|
| `ultralytics` | Ultralytics + torch | detect / pose / OBB | `detectors.py:200` 延迟导入 `YOLO`；`detectors.py:268` 调 `model.predict(image_bgr, ...)` |
| `onnxruntime` | ONNX Runtime | detect | 生态内实测 CPU 197.5 ms / ROS 节点 232.8 ms |
| `openvino` | OpenVINO Runtime | detect | 生态内实测 CPU 126.7 ms |
| `opencv` | OpenCV DNN | detect | 老 YOLO ONNX；OpenCV 4.6 不能解析 YOLOv8 DFL |
| `mock` | 无 | 颜色阈值 | CI / 无模型演示 |

生产配置 `config/gpu.yaml` 当前把两台相机都设为 `backend: ultralytics`（`:22`、`:42`），模型路径在 `/opt/jcheng/models/`；`half: false`，`imgsz: 640/416`。也就是说，**Ultralytics 目前是默认后端，不是"可选后端"**。pose 任务（腕部关键点）只能走 `ultralytics`；ONNX/OpenVINO/OpenCV 路径在代码里显式拒绝 pose/OBB（`detectors.py:420-423`、`:544-547`、`:613-616`）。

### 03.2 已实测数据（S）

来自 `jcheng-perception/capability.yaml:123-134` 与 `docs/MODEL_ITERATION.md`：

| 项 | 实测值 | 条件 |
|---|---|---|
| `ultralytics_cuda` | **9.0 ms FP32 / 7.4 ms FP16** 稳态，4 detections | torch 2.9.1+cu128，RTX 3060 Laptop 6 GB |
| `ultralytics_cpu` | 首帧 **1.04 s**，4 detections | CPU |
| `ros_ultralytics_node` | **154.3 ms/frame** 稳态 | venv Python，`yolov8s.pt`，CPU |
| `ros_ultralytics_gpu` | **54.3 ms/frame** 平均 | RTX 3060，含 ROS 解码/发布开销 |
| `cross_machine_yolo` | 2.06 fps / 55.2 ms 平均 | Pi 5 edge + laptop GPU，CycloneDDS domain 0 |
| GPU venv | **6.8 GB** | torch + CUDA wheels；镜像不装 `opencv-python`，用 apt `python3-opencv` 提供 ArUco |

这些数字证明：**在 3060 上推理不是问题**；真正的成本在许可、依赖体积、离线安装和运行时行为。

### 03.3 许可现状

`LICENSE-REVIEW.md:22` 已把 Ultralytics 标为 "**AGPL-3.0 by default**; commercial licensing may be required"；`:49` 只把 YOLO-seg 列为 "existing optional runtime; not a default"。但 `config/gpu.yaml` 的 **detect 默认后端就是 `ultralytics`**，license review 没有记录这一事实。建议在 review 关闭前补齐：要么把默认后端改为 ONNX/OpenVINO，要么明确接受 Ultralytics 作为默认后端并给出许可结论。

---

## 04. Research Methodology（研究方法）

**检索与取材**：

1. **仓库本体**：浅克隆 `v8.4.219` 到 `/tmp/ultralytics-review/src`（不执行其代码），检查 233 个源文件、`pyproject.toml`、`LICENSE`、`README.md`、`docs/en/`、`.github/workflows/`、`tests/`。
2. **发布与元数据**：GitHub API（repo、tags、releases、commits、issues、search）；PyPI JSON（`ultralytics`、`ultralytics-platform`、`ultralytics-thop`）；pypistats 近 30 天下载。
3. **一手文档**：YOLO26 论文 arXiv 2606.03748（摘要 + 作者）；仓库内 `docs/en/models/yolo26.md`、`docs/en/guides/raspberry-pi.md`、`docs/en/guides/nvidia-jetson.md`、`docs/en/help/privacy.md`、`docs/en/help/contributing.md`。
4. **Issue 证据**：按标题检索并阅读 #22640（内部使用是否合规）、#26703（私有数据集/进程隔离）、#25030（Orin 延迟）、#21241（内存增长）、#22791（内存泄漏）的正文与维护者回复。
5. **替代方案**：GitHub API 读取 YOLOX、MMDetection、RF-DETR、Super-Gradients、YOLOv6、PaddleDetection 的 license/活跃度；未逐一审查其源码。
6. **生态内部**：`jcheng-perception` 的 `capability.yaml`、`config/gpu.yaml`、`detectors.py`、`node.py`、`docs/MODEL_ITERATION.md`、`deploy/README.md`、`LICENSE-REVIEW.md`，以及 `jcheng-research/references/perception/jetson-agx-orin.md` 的 Orin 事实。

**纳入/排除标准**：

- 纳入：能直接支持"能否用、怎么用、代价是什么"的一手证据；有版本/SHA/issue 编号可追溯。
- 排除：第三方博客、模型排行榜、无出处的性能对比；无法确认硬件/精度/输入尺寸的数字。
- **未做**：在本机安装或运行 ultralytics；在 Pi 5/Orin 上跑 YOLO26；法律意见；对 83.6k 行源码的逐行审计；对替代框架的训练精度实测。

**方法限制**：GitHub 未认证 API 有速率限制，issue 检索只覆盖标题命中的样本；厂商文档的数字多为自测，且硬件/精度/输入尺寸不同，不能直接横比。

---

## 05. Literature Review（论文与相关研究）

### 5.1 YOLO26 论文（arXiv 2606.03748，2026-06-02）

| 项 | 内容 |
|---|---|
| 研究问题 | 实时检测仍依赖 NMS、DFL 导致头部重、训练日程长、小目标缺少正样本分配 |
| 核心贡献 | 双头设计支持原生 NMS-free 端到端推理；完全移除 DFL；MuSGD（Muon+SGD）优化器；Progressive Loss；STAL 小目标标签分配；统一检测/实例分割/姿态/OBB/分类/深度 |
| 机制 | 一对多 + 一对一双头；推理可走 NMS 或 e2e；轻量头 + 无约束回归；训练期把监督移向推理头 |
| 基准 | COCO 五尺度：40.9–57.5 mAP（NMS）、40.1–56.9（e2e）；T4 TensorRT **1.7–11.8 ms**；YOLO26n 相比 YOLO11n 的 CPU ONNX 推理快 **up to 43%**（Intel Xeon @2.00 GHz） |
| 假设/条件 | 以 COCO 为主；T4 TensorRT 延迟；CPU 数字是 Xeon ONNX；未覆盖 Pi 5/Orin/Jetson、未覆盖机器人小目标域 |
| 基线/消融 | 论文报告了相对 YOLO11 的精度与速度增益；本次只读摘要与官方模型页，**未读全文附录与消融表**，不能判断消融是否充分 |
| 可复现性 | 代码/权重/训练配方在仓库与文档中公开，复现门槛低；但训练配方（MuSGD、STAL）细节需读全文 |
| 迁移价值 | 检测精度/速度的通用提升可迁移；NMS-free 对端侧部署有吸引力；但**没有针对矿石/货架/机械臂工作空间的证据** |
| 利益冲突 | 作者包括 Ultralytics 创始人/维护者，属**厂商自评**；没有独立同行评审或第三方复现（本次检索范围内）[A/C] |

**结论**：YOLO26 的论文足以支持"这是一个设计合理、工程化程度高的实时检测家族"，**不足以支持"它在我们 6 GB 3060 / Orin / Pi 5 的机器人任务上更优"**。后者只能靠 §11 的 MVE。

### 5.2 YOLO27：尚未发布

仓库 `README.md:125`、`docs/en/models/yolo27.md` 明确写 "**models are not yet available, and no launch date is set**"；`docs/en/tasks/index.md:14` 说 "coming soon and is not yet available; this guide uses released YOLO26 models"。预览页给的 42.6–60.5 mAP / 0.44–1.86 ms 是 **RTX PRO 6000** 上的数字，与我们的硬件无关。**仓库描述与 banner 把 YOLO27 放在最前面，容易让读者误以为已发布**；在选型文档里应明确标注"不可用"。

### 5.3 证据缺口

- 没有独立第三方在 **Pi 5 / AGX Orin / RTX 3060 Laptop** 上对 YOLO26 与 YOLO11/YOLOv8 的同条件对比（本次检索范围内）。
- 没有针对 **矿石、货架、机械臂抓取** 域的迁移证据；生态内的 ore/shelf 工作仍以 YOLOv8 为基线。
- 没有 ROS 2 集成的官方论文或基准；`docs/en/guides/ros-quickstart.md` 只是用法示例，不是实时性/确定性证据。

---

## 06. Repository Investigation（仓库审查）

### 6.1 结构与模块划分

```
ultralytics/
├── cfg/            # 默认参数、模型 YAML、数据集 YAML、tracker 配置
├── data/           # Dataset/DataLoader、增强、split_dota 等脚本
├── engine/         # Model / Trainer / Validator / Predictor / Exporter / Tuner
├── models/         # yolo (v3/v5/v8/v9/v10/v11/v12/26), rtdetr, sam, fastsam, nas, utils
├── nn/             # 模块、任务头、backends（ONNX/OpenVINO/TensorRT/...）
├── optim/          # MuSGD 等优化器
├── solutions/      # 计数、测距、热图、OCR、安防等应用层封装
├── trackers/       # BoT-SORT、ByteTrack、OC-SORT、Deep OC-SORT、FastTracker
├── utils/          # checks、downloads、events、patches、torch_utils、callbacks
└── assets/         # 示例图片/字体
```

模型配置目录 `cfg/models/` 覆盖 `v3 v5 v6 v8 v9 v10 v11 v12 26 rt-detr`；**没有 `27/` 目录**，与"YOLO27 未发布"一致。任务覆盖 detect/segment/semantic/classify/pose/obb/depth/track；`solutions/` 提供计数、区域、距离、热图、OCR、安防等示例封装（约 20 个模块，含配置/入口），这些是示例级封装，不是生产服务。

### 6.2 入口与核心调用链

| 层 | 位置 | 作用 |
|---|---|---|
| 包入口 | `ultralytics/__init__.py:2` | `__version__ = "8.4.219"`；模型类通过 `__getattr__` 懒加载（`:36-46`） |
| Python API | `ultralytics/engine/model.py` | `YOLO(path)` → `_load` → `predict/train/val/export/track` |
| 推理 | `ultralytics/engine/predictor.py` | 预处理、批推理、后处理、回调；`on_predict_end` 在 `:523` 每次 `predict()` 结束时触发 |
| 导出 | `ultralytics/engine/exporter.py` | ONNX/TensorRT/OpenVINO/NCNN/RKNN/TFLite/... 的统一导出；`:911-915` 有 JetPack 6 / TRT 10.3 INT8 的已知限制 |
| 依赖检查 | `ultralytics/utils/checks.py:536` | `check_requirements()`；`:638` 在 `AUTOINSTALL` 为真时执行安装 |
| 遥测 | `ultralytics/utils/events.py:69` | Google Analytics Measurement Protocol；`:222` 在 predict 结束时入队 |
| 权重加载 | `ultralytics/nn/tasks.py:1861` | `torch_safe_load()`；默认走 `torch.load(weights_only=False)`（`utils/patches.py:228-252`） |

### 6.3 依赖与打包

`pyproject.toml` 的核心依赖（12 个）：`numpy`、`matplotlib`、`opencv-python`、`pillow`、`requests`、`torch`、`torchvision`、`psutil`、`polars`、`nvidia-ml-py`、`ultralytics-thop`、`ultralytics-platform`（`python_version >= '3.11'`）。

| 观察 | 影响 |
|---|---|
| `opencv-python` 是**核心**依赖（不是 headless） | 无 GUI 的机器人/Pi 会多装 GUI 库；生态内用 apt `python3-opencv` 规避，但 pip 解析仍可能拉 `opencv-python` |
| `polars`、`nvidia-ml-py`、`ultralytics-thop` 是核心依赖 | 为训练/监控/FLOPs 服务，推理也需要安装；增大镜像与攻击面 |
| `ultralytics-platform` 是核心依赖（Python≥3.11） | 引入 Platform API 客户端（AGPL-3.0-only）；静态检查显示只在访问 `ultralytics.Platform` 时才导入，不会自动联网，但**默认会被安装** |
| 可选 extras 很大（`export-*`、`solutions`、`llm`、`logging`…） | 导出/解决方案会触发更多依赖与自动安装 |
| 生态内 GPU venv **6.8 GB** | 主要是 torch+CUDA；出厂镜像应避免把训练栈带进去 |

### 6.4 测试、CI 与发布工程

| 项 | 事实 | 评价 |
|---|---|---|
| 测试 | **230** 个 `test_` 函数；`test_python.py` 120、`test_exports.py` 38、`test_solutions.py` 17、`test_engine.py` 15、`test_cli.py` 13、`test_cuda.py` 13 | A：覆盖面广，含导出/CLI/解决方案 |
| CI 矩阵 | `ci.yml`：`ubuntu-latest`、`macos-latest`、`windows-latest`、`ubuntu-26.04-arm`；主矩阵 Python 3.13，include 覆盖 3.8/3.14/3.15；`:518` 有 **Raspberry Pi** runner；GPU runner、ROCm runner；独立 venv 的导出测试 | A：对 ARM/Pi/Jetson 有真实投入 |
| 导出回归 | `tests/test_exports.py` + 隔离 venv + `YOLO_AUTOINSTALL: "false"` | A：这是同类仓库少见的工程化 |
| Fuzz | `.github/workflows/fuzz.yml` 每日 Monte Carlo fuzz `yolo` CLI，自动去重建 issue | A：健壮性投入高 |
| Stale | `stale.yml:49-52`：issue 30 天 stale + 10 天关闭；PR 90+30 | B：open issue 只有 35 个，部分是"快速关闭"策略的结果，不能只看数量判断响应质量 |
| 发布 | 12 天 8 个 release；每日 commit | A：活跃，但也意味着 patch 级行为漂移 |
| CLA | `docs/en/help/CLA.md`：贡献者需签 CLA，含专利许可 | A：公司主导的开源治理，允许企业版再许可 |

### 6.5 许可与治理

- 代码：**AGPL-3.0**（`LICENSE` 661 行）；PyPI `license: AGPL-3.0`；GitHub license 字段一致 [A]。
- 商业：Enterprise License（`https://www.ultralytics.com/license`），条款需联系销售；仓库内没有价格 [A]。
- 官方合规口径（`docs/en/help/contributing.md:240-248`）："Using Ultralytics YOLO models or code in your project? The AGPL-3.0 license requires that your entire derivative work also be open-sourced under AGPL-3.0." 并明确 "If you prefer not to open-source your project, consider obtaining an Enterprise License" [A]。
- 维护者口径（issue #22640，2025-11-10，glenn-jocher）："under AGPL-3.0, using Ultralytics YOLO in an internal app requires that you open-source the entire application and any derivative models publicly under AGPL-3.0; providing source only to employees is not sufficient." [A]
- 维护者口径（issue #26703，2026-10-16，pderrenger + glenn-jocher）："splitting it into processes that talk over sockets doesn't exempt Process A"；训练数据是否披露取决于是否运行/再训练所需，但"complete project source, training scripts, configurations, and trained weights"要发布 [A]。
- **AGPL 文本**：`LICENSE:152-153` "You may make, run and propagate covered works that you do not convey, without conditions so long as your license otherwise remains in force."；§13（`:539` 起）只在**修改程序并提供远程网络交互**时要求提供 Corresponding Source [A]。
- **判断**：厂商口径明显宽于 AGPL 文本对"私有使用"的豁免；两者是否冲突、模型权重是否属于"covered work"、DDS/socket 隔离是否构成 derivative work，都需要法务意见，本报告不做结论 [C/D]。**但对项目决策而言，厂商的公开立场本身就是风险：即使法律上站得住，也可能面临厂商主张。**

### 6.6 运行时副作用（默认值）

| 行为 | 默认 | 关闭方式 | 代码/文档 | 风险 |
|---|---|---|---|---|
| 缺依赖自动安装 | **开**（`AUTOINSTALL=True`） | `YOLO_AUTOINSTALL=False` 或 `ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS=1` | `utils/__init__.py:81`；`utils/checks.py:536-660` | 运行时改环境、联网、`--break-system-packages`；离线机器人会失败或挂起 |
| 匿名使用分析 | **开**（`sync=True`） | `settings.update({"sync": False})` 或 `YOLO_OFFLINE=1` | `utils/events.py:50-235`；`docs/en/help/privacy.md` | predict/train 结束、val 开始、export 开始时入队，30 s 限流后 POST 到 `google-analytics.com`；数据含 CPU 型号、torch 版本、模型 basename、任务、设备、耗时、session id（随机）与 `SETTINGS["uuid"]`（MAC+hostname 的 SHA-256） |
| Sentry 崩溃上报 | 条件开 | `sync=False` / 不装 `sentry-sdk` | `utils/__init__.py:1492-1564` | 仅当 `sentry-sdk` 已安装、`yolo` CLI、pip 安装、非 git 目录、在线、非测试；上报栈、版本、主机名、包版本；不含局部变量 |
| 在线检查 | 导入时 DNS | `YOLO_OFFLINE=1` | `utils/__init__.py:1147-1162`、`:1283` | 每次 `import ultralytics` 对 `one.one.one.one` / `dns.google` 做 DNS 解析；离线环境快速失败，但仍是导入副作用 |
| 权重自动下载 | 开（按名字） | 用绝对路径；`YOLO_OFFLINE=1` | `utils/downloads.py:543` | `YOLO("yolo26n.pt")` 会从 GitHub assets 下载；我们的配置用绝对路径，规避 |
| 不安全反序列化 | **默认 `weights_only=False`** | `ULTRALYTICS_SAFE_LOAD=1`（opt-in 白名单） | `utils/patches.py:228-252`；`nn/tasks.py:1861` | 加载不可信 `.pt` = 任意代码执行；官方权重可信，但供应链/第三方权重不可信 |

**结论**：这些副作用在"开发机 + 公网 + 自己训练的权重"场景可以接受；在"机器人 + 离线 + 第三方权重"场景必须全部显式关闭/开启安全模式，并做 MVE-1 验证。

### 6.7 Issue 证据

| Issue | 内容 | 对结论的作用 |
|---|---|---|
| [#22640](https://github.com/ultralytics/ultralytics/issues/22640) | 内部使用是否合规；维护者回复"也要公开整个应用，否则买 Enterprise" | 许可口径的一手证据 [A] |
| [#26703](https://github.com/ultralytics/ultralytics/issues/26703) | 私有数据集 + 进程 A/B 用 socket 隔离；回复"socket 不豁免 A" | 直接对应我们 DDS 分层的场景 [A] |
| [#25030](https://github.com/ultralytics/ultralytics/issues/25030) | Orin 上 `.pt` 实测约 25 ms，官方 <10 ms；换 TensorRT engine 后一致 | 厂商数字必须按导出格式/硬件解读 [B] |
| [#21241](https://github.com/ultralytics/ultralytics/issues/21241) | OpenVINO 后端下访问推理结果，内存随时间上涨，1 小时可到 GB 级 | 长期运行需监控 RSS；我们的循环也访问结果 [B] |
| [#22791](https://github.com/ultralytics/ultralytics/issues/22791) | "memory leak"（2025-11-25，已关闭） | 同类问题反复出现 [B] |

Issue 质量：官方回复通常给出可操作步骤（升级、导出 engine、环境匹配），但许可类问题会回到 "buy Enterprise"；stale bot 会关闭不活跃讨论，**不能用 issue 是否 open 判断问题是否解决**。

### 6.8 文档与实现一致性

- README 的模型表、`docs/en/models/*`、`cfg/models/*` 基本一致；YOLO26 是当前发布主线 [A]。
- **不一致点**：GitHub 仓库描述与 README banner 把 **YOLO27** 放在最前，但 YOLO27 未发布、无权重/配置；`cfg/models/` 没有 `27/` [A]。
- `docs/en/help/privacy.md` 明确写了 Google Analytics 与 Sentry 的采集范围，比代码注释更完整；这是正面项 [A]。
- `pyproject.toml` 声明 `requires-python >=3.8`，CI 覆盖 3.8–3.15；但 `ultralytics-platform` 只在 3.11+ 安装，功能在 3.10 以下缺失（`__init__.py:36-46` 会抛 ImportError）[A]。

---

## 07. Comparative Analysis（横向比较）

### 7.1 训练/模型框架

| 候选 | 代码许可 | 活跃度（2026-11-26） | 导出/部署 | 对 JCHENG 的意义 |
|---|---|---|---|---|
| **Ultralytics** | **AGPL-3.0**（Enterprise 双许可） | 63.8k stars，每日 commit，230 测试 | ONNX/TensorRT/OpenVINO/NCNN/RKNN/... 最全 | 工程最强，但许可风险最高；适合开发期 |
| **YOLOX** | **Apache-2.0** | 10.7k stars，最后 push 2025-06 | ONNX/TensorRT 导出成熟 | 许可干净、代码稳定；模型代际较旧，精度/维护不如 YOLO26 |
| **MMDetection / RTMDet** | **Apache-2.0** | 33.1k stars，最后 push 2024-08 | mmdeploy → ONNX/TensorRT | 生态大、许可干净；维护放缓，部署链更重 |
| **RF-DETR** | **Apache-2.0** | 10.2k stars，2026-11-26 仍活跃 | ONNX/TensorRT 导出 |  transformer 检测器，许可干净、活跃；需验证 6 GB 训练与 Orin 部署 |
| **PaddleDetection** | **Apache-2.0** | 14.5k stars，2026-05 活跃 | Paddle Inference/ONNX | 许可干净、中文资料多；引入 Paddle 运行时，迁移成本高 |
| **YOLOv6** | **GPL-3.0** | 5.9k stars，2024-08 | — | 拒绝：GPL 传染性 |
| **YOLOv9** | GPL-3.0（上游） | — | — | 拒绝：GPL |
| **YOLOv10** | AGPL-3.0 | — | — | 拒绝：与 Ultralytics 同类许可风险 |

> 说明：上表的 stars/最后 push 来自 GitHub API；许可以仓库 `LICENSE` 字段为准。未逐一验证各仓库的权重许可（部分项目的代码与权重许可不同），选型前必须单独核对。

### 7.2 推理运行时

| 运行时 | 许可 | 生态内实测 | 适用 |
|---|---|---|---|
| Ultralytics + torch | AGPL-3.0 | 3060：**9.0 ms FP32 / 7.4 ms FP16**；CPU 154.3 ms；首帧 1.04 s | 开发、pose/OBB、快速迭代 |
| ONNX Runtime | MIT | CPU 197.5 ms；ROS 232.8 ms | 生产 CPU/GPU（ORT-GPU） |
| OpenVINO | Apache-2.0 | CPU 126.7 ms | Intel CPU/GPU；IR 部署 |
| TensorRT | NVIDIA EULA（免费使用） | 官方 Orin：FP16 2.62 ms / INT8 2.30 ms（JP7.2） | Orin/Jetson 生产；需在目标机构建 engine |
| OpenCV DNN | Apache-2.0 | 未在本项目作为主路径 | 轻量、无额外运行时；算子覆盖有限 |

**可比性**：生态内的 9.0/7.4/154.3 ms 是同一台 3060 Laptop、同一 `yolov8s` 权重、不同后端的实测，**可以直接横比**；厂商的 Pi 5 128.4 ms、Orin 11.58/2.62/2.30 ms 是不同硬件/精度/输入尺寸，**不能与我们的数字直接比较**。Orin 的 `.pt` 25 ms 是用户实测（issue #25030），只说明"PyTorch 路径远慢于 TensorRT"，不是我们的机器。

### 7.3 结论

- **精度/速度**：Ultralytics 的 YOLO26 在通用 COCO 上领先，但我们的任务域（矿石、货架、机械臂）没有证据；不能仅凭 COCO 数字选型。
- **许可**：Apache-2.0 的 YOLOX/MMDetection/RF-DETR/PaddleDetection 明显更适合产品化；代价是模型代际、部署链和维护活跃度。
- **工程**：Ultralytics 的 CI/导出/文档显著强于替代品；如果许可问题解决（Enterprise），它仍是效率最高的选择。
- **运行时**：无论用哪个训练框架，生产都应走 ONNX/OpenVINO/TensorRT；这部分与训练框架解耦。

---

## 08. Critical Findings（关键发现）

### F1. 许可口径与 AGPL 文本存在实质张力，构成决策阻塞 [A/C]

- 事实：AGPL §2（`LICENSE:152-153`）允许"不 convey 的运行"不受条件约束；§13 只在"修改程序 + 提供远程网络交互"时要求提供 Corresponding Source。
- 事实：Ultralytics 官方文档与维护者回复要求"整个项目 + 衍生权重"公开，**包括纯内部使用**，并明确 socket 隔离不豁免。
- 推断：厂商口径是**合同/合规立场**，不完全等于 AGPL 的法条效果；实际风险取决于是否 convey、是否对外提供网络服务、以及法院/法务对"derivative work"的认定。
- **什么会改变结论**：法务出具"内部使用不触发 AGPL 义务"的书面意见；或 Enterprise License 报价在可接受范围；或项目决定整体 AGPL 开源。

### F2. 默认运行时行为不是机器人安全的 [A]

- 自动安装（默认开）会在运行时改 Python 环境，优先 `uv pip install --break-system-packages`；离线机器人会失败或长时间挂起。
- 匿名分析（默认开）在每次 predict 结束入队并 POST 到 Google Analytics；机器人运行期间会周期性外联。数据不含图像，但含 CPU 型号、模型文件名、设备、耗时、UUID。
- `.pt` 默认 `weights_only=False`，第三方权重可执行任意代码；安全加载是 opt-in。
- **缓解**：`YOLO_AUTOINSTALL=False`、`YOLO_OFFLINE=1`、`settings.update({"sync": False})`、`ULTRALYTICS_SAFE_LOAD=1`；并在 MVE-1 中用 `tcpdump`/`strace` 验证零外联。

### F3. YOLO27 是"预览"，不是可用模型 [A]

仓库描述、README banner、docs 首页都把 YOLO27 放在最前，但模型/权重/配置均未发布。任何选型文档若写"支持 YOLO27"都是错误的；当前可用主线是 **YOLO26**。

### F4. 厂商基准与真实部署有 5–10 倍差距，导出格式是关键 [A/B]

- 官方 Orin 表：PyTorch 11.58 ms、TensorRT FP16 2.62 ms、INT8 2.30 ms（JetPack 7.2）。
- 用户实测（#25030）：Orin 上 `.pt` 约 25 ms，换 engine 后与官方一致。
- 本机 Orin 是 **JetPack 6.2 / TRT 10.3**，官方基准是 7.2；exporter 对 TRT 10.3 的 INT8/NMS 有已知限制（`engine/exporter.py:911-915`）。
- **结论**：Orin 上必须用目标机导出的 TensorRT engine，不能用 `.pt` 的延迟做预算；INT8 需要单独验证精度与可构建性。

### F5. 长期运行的内存行为需要监控 [B]

Issue #21241 记录 OpenVINO 后端下访问推理结果导致 RSS 持续上涨（1 小时到 GB 级）；我们的 `CameraWorker` 每帧都访问 `results[0].boxes`，属于同一模式。虽然当前没有在我们的机器上复现，**长稳测试必须记录 RSS 斜率**，不能只看推理耗时。

### F6. 版本节奏要求锁定与回归 [A]

12 天 8 个 release；`8.4.216` 与 `8.4.219` 已有行为差异（Sentry SDK 3 修复、导出修复）。生产环境必须固定精确版本（`ultralytics==8.4.216`），升级走"导出回归 + 后端一致性"流程，不能 `pip install -U`。

### F7. 功能锁定只在 pose/OBB [A]

detect 可以完全走 ONNX/OpenVINO/OpenCV；**pose 与 OBB 只有 `ultralytics` 后端支持**（`detectors.py:420-423` 等）。腕部关键点模型是当前唯一难以立即去 Ultralytics 的功能；替代方案是 MMPose（Apache-2.0）或自训关键点头，但需要额外工作。

### F8. 厂商自评 + 社区快速关闭，独立证据不足 [A/C]

YOLO26 论文作者是厂商；issue 在 30+10 天后自动关闭；open issue 只有 35 个不代表问题少。选型不能依赖"star 多/issue 少"，必须用自己的数据做 MVE。

---

## 09. Engineering Applicability（工程适配）

### 9.1 与现有架构的兼容性

| 维度 | 评估 |
|---|---|
| 分层 | Ultralytics 只在 L3 `jcheng-perception` 的 GPU 节点内使用；不发布厂商话题、不直接控制设备、不触碰 `ExecuteMotion`，边界合规 |
| 接口 | 输出仍是 `Detection2DArray`（advisory target），与后端无关；切换 backend 不改上层契约 |
| 线程 | 每相机一个 worker + 每 worker 一个 detector；没有共享 `YOLO` 对象的竞态；但 `MultiThreadedExecutor` 下仍需保证 detector 只被自己的 worker 调用（当前满足） |
| 热加载 | `hot_reload` 按模型 mtime 重建 detector；切换后端/模型不需要重启节点 |
| 回退 | 改 `config/gpu.yaml` 的 `backend` 即可回退到 `onnxruntime`/`openvino`/`mock`；无需改代码 |
| 契约 | 无 `jcheng-interfaces` 变更；无 DDS 域变更；无 `capability.yaml` 变更（除非新增依赖记录） |

### 9.2 迁移成本

| 路径 | 成本 | 说明 |
|---|---|---|
| 保持 `ultralytics` 后端 | 低 | 现状；需许可与运行时加固 |
| 切到 ONNX/OpenVINO（detect） | **低** | 已有后端与实测；只需导出权重、改配置、跑精度对齐 |
| 切到 ONNX/OpenVINO（pose/OBB） | **中** | 现有后端不支持；需要新增关键点解码或换框架 |
| 换训练框架（RF-DETR/RTMDet/YOLOX） | **中–高** | 数据格式、训练配方、导出、精度回归；但一次性 |
| 购买 Enterprise License | 低（技术）/未知（商务） | 保留全部能力；仍需运行时加固 |

### 9.3 计算与部署成本

- **RTX 3060 Laptop 6 GB**：YOLO26n/s 推理和微调可行；YOLO26m 以上训练可能 OOM；当前 `yolov8s` 9.0 ms，余量充足。
- **AGX Orin 64 GB**：内存不是瓶颈；但 JetPack 6.2 / TRT 10.3、系统 Python 3.10 无 torch；需要 conda/venv + NVIDIA torch wheel，或只在笔记本导出 engine 后在 Orin 用 `trtexec` 构建。TensorRT engine 必须在目标机构建/验证。
- **Pi 5 8 GB**：厂商 ONNX 7.79 FPS（128 ms），适合"低频检测"，不适合闭环控制；我们的生产分工仍是 Pi 采集 + 笔记本/Orin 推理。
- **镜像体积**：GPU venv 6.8 GB；生产镜像不应带训练依赖（polars、matplotlib、nvidia-ml-py 等）。

### 9.4 安全与可靠性

- **网络外联**：默认 analytics 会在机器人运行期间外联；必须关。
- **自动安装**：运行时 pip 可能改环境、联网、失败挂起；必须关。
- **反序列化**：只加载自己训练/校验过的权重；开启 `ULTRALYTICS_SAFE_LOAD=1` 并验证兼容性。
- **供应链**：每日 release + 宽依赖范围 + 自动下载权重，意味着不能"装最新版然后锁镜像"；要锁精确版本 + 权重 SHA-256。
- **长稳**：RSS 斜率、线程泄露、模型热加载失败重试都需要监控；现有 `stats_interval_s` 只覆盖耗时/帧数，不含 RSS。

### 9.5 对现有功能的影响

- 切换到 ONNX/OpenVINO 后，detect 的 `model_id`/`describe()` 仍可用（基于文件 mtime），但 pose 功能会缺失。
- 若保留 `ultralytics`，`model_id` 基于 `.pt` mtime；导出模型目录的 mtime 逻辑已支持（`detectors.py:_stat_mtime_ns`）。
- 许可变更不影响 DDS、TF、融合、Kalman 或安全层。

---

## 10. Recommended Approach（推荐方案）

### R1（推荐）：开发期工具 + 生产期导出

1. **许可**：在 license review 中把 Ultralytics 从"optional runtime"改为"**development-only tool, not shipped**"；如果产品要商业化/对外服务，先取得法务对 AGPL 的书面意见或 Enterprise License，再把 `backend: ultralytics` 从出厂配置移除。
2. **运行时**：生产配置改为 `backend: onnxruntime` 或 `openvino`（detect）；TensorRT 用于 Orin。导出在开发机完成，权重/engine 放 `/opt/jcheng/models/`，记录 SHA-256。
3. **开发环境加固**（所有使用 ultralytics 的 venv/脚本）：
   ```bash
   export YOLO_AUTOINSTALL=False
   export YOLO_OFFLINE=1
   export ULTRALYTICS_SAFE_LOAD=1
   python - <<'PY'
   from ultralytics import settings
   settings.update({"sync": False})
   PY
   ```
   并固定 `ultralytics==8.4.216`（或经验证的精确版本）。
4. **验证**：跑 §11 的 MVE-1（运行时审计）与 MVE-2（后端一致性），通过后再改生产配置。
5. **监控**：长稳测试记录 RSS；升级 ultralytics 时重跑 MVE-2。

### R2（替代）：购买 Enterprise License

- 适用：需要持续用 YOLO26/后续版本训练、需要 pose/OBB、且商务上可接受。
- 代价：许可费用未知（需询价）；仍需 R1 的运行时加固（遥测/自动安装/反序列化与许可无关）。
- 收益：保留全部能力，避免 AGPL 公开义务。

### R3（替代）：换 Apache-2.0 训练框架

- 候选：**RF-DETR**（活跃、Apache-2.0）、**MMDetection/RTMDet**（成熟、维护放缓）、**YOLOX**（稳定、代际较旧）、**PaddleDetection**（中文生态、运行时重）。
- 步骤：用同一数据集/切分训练，导出 ONNX，跑 MVE-2 的精度/延迟对齐；达标后替换训练工具，运行时不变。
- 代价：一次性迁移 + 精度回归；收益：许可干净、长期可控。

### 不推荐（明确拒绝）

| 方案 | 理由 |
|---|---|
| 把 `ultralytics` 作为出厂运行时依赖，且不做许可处理 | 厂商口径要求整体 AGPL 或 Enterprise；风险不可接受 |
| 依赖"内部使用一定豁免 AGPL"的假设 | 厂商公开反驳；法律效果未定；不能作为工程默认 |
| 在机器人上 `pip install -U ultralytics` 或开自动安装 | 版本漂移、联网、改环境；离线必挂 |
| 加载第三方/来源不明的 `.pt` | 任意 pickle 执行；供应链风险 |
| 用 YOLO27 做选型 | 未发布、无权重、无配置；文档明确不可用 |
| 用 `.pt` 的 Orin 延迟做预算 | issue #25030 显示与 engine 差 5–10 倍；必须用目标机 engine |

---

## 11. Experimental Design（实验设计）

> 状态：**未运行**（pre-registered）。三项 MVE 均需单独授权；MVE-1 约 2 小时，MVE-2 约 1 小时，MVE-3 约 1–2 天。

### MVE-1：运行时加固审计（2 h）

| 项 | 内容 |
|---|---|
| 假设 | 在 `YOLO_AUTOINSTALL=False`、`YOLO_OFFLINE=1`、`sync=False`、`ULTRALYTICS_SAFE_LOAD=1` 下，`ultralytics==8.4.216` 在 2 小时连续推理中零外联、零 pip 子进程、RSS 增长 <5% |
| 基线 | 当前默认设置（sync=True、AUTOINSTALL=True）下同一循环的外联/RSS |
| 自变量 | 四个环境/设置开关 |
| 控制变量 | 同一台笔记本、同一 3060、同一 `yolov8s.pt`、同一 200 帧循环、同一 Python/venv |
| 环境 | `~/.venvs/jcheng-perception-gpu`（8.4.216、torch 2.9.1+cu128） |
| 指标 | 出站连接数（`tcpdump`/`ss`）、pip/uv 子进程数（`strace -f -e execve`）、RSS 斜率（每 60 s）、推理 p50/p95、异常数 |
| 验收 | 0 次外联到 `google-analytics.com`/`sentry.io`/`pypi.org`；0 次 pip/uv 安装；RSS 增长 <5%；p95 不超过基线的 120% |
| 失败判据 | 任意外联、任意安装、RSS 增长 ≥10%、或出现未处理异常 |
| 记录 | `experiments/20261126-ultralytics-runtime-audit/result.md` + CSV（时间、RSS、p50/p95、连接数） |
| 回退 | 关闭实验 venv，生产配置不变；不影响现有节点 |

### MVE-2：后端一致性（1 h）

| 项 | 内容 |
|---|---|
| 假设 | 同一权重导出的 ONNX/OpenVINO 与 `.pt` 在 200 帧固定样本上检测框一致率 ≥99%（IoU>0.99、score 差 <0.01），延迟在 ±20% 内 |
| 基线 | `ultralytics` + `.pt`（当前生产路径） |
| 自变量 | `ultralytics` / `onnxruntime` / `openvino` |
| 控制变量 | 同一 200 帧（矿石/货架各 100）、同一 `imgsz`/`conf`/`iou`/`max_det`、同一预处理、同一 3060 |
| 指标 | 匹配率、IoU 分布、score 差、p50/p95 延迟、漏检/误检数 |
| 验收 | 匹配率 ≥99%；p95 延迟 ≤ `.pt` 的 120%；无类别/坐标系统性偏移 |
| 失败判据 | 匹配率 <95%、p95 延迟 >150%、或出现固定偏移（>2 px 均值） |
| 记录 | `result.md` + 逐帧 CSV；导出命令与 SHA-256 |
| 回退 | 生产继续用 `.pt`；导出件留在 `/opt/jcheng/models/` 不切换 |

### MVE-3：许可干净训练对比（1–2 天，可选）

| 项 | 内容 |
|---|---|
| 假设 | RF-DETR-nano / RTMDet-tiny / YOLOX-tiny 在矿石/货架数据上达到 YOLOv8n 基线 −2 mAP 以内，且导出/延迟可用 |
| 基线 | 现有 YOLOv8n 权重与 mAP（记录在 `jcheng-perception` 的 ore/shelf 证据） |
| 自变量 | 训练框架/模型 |
| 控制变量 | 同一数据切分、同一输入尺寸、同一增强预算、同一评估脚本 |
| 指标 | mAP50-95、AP50、p50/p95 延迟（3060/Orin）、导出成功率、许可 |
| 验收 | mAP 在基线 −2 以内；延迟不高于基线 120%；ONNX 导出可被现有后端加载 |
| 失败判据 | mAP 低于基线 −5、或导出/运行失败、或训练在 6 GB 上 OOM 不可恢复 |
| 记录 | `result.md` + 训练配置 + 权重 SHA-256（权重不入 git） |
| 回退 | 继续用现有 YOLOv8n + 生产 ONNX；训练实验不进入运行时 |

---

## 12. Limitations & Uncertainties（限制与不确定）

1. **未运行**：本报告没有在本机安装/运行 ultralytics，所有运行时行为来自源码与文档；MVE-1 才能证明开关在 8.4.216 上确实生效。
2. **未做法务判断**：AGPL 对私有使用、模型权重、DDS/socket 隔离的适用性存在争议；厂商口径与法条文本的冲突需要律师意见。本报告只记录双方文本。
3. **厂商基准不可直接迁移**：YOLO26 论文/文档的数字是 T4/Jetson 7.2/Pi 5 的特定条件；本机 Orin 是 JetPack 6.2/TRT 10.3，且无 torch；必须自测。
4. **独立证据不足**：没有第三方在相同硬件/数据上的复现；ore/shelf 域没有 YOLO26 的迁移结果。
5. **内存问题未定论**：#21241 已关闭，但没有看到根因修复；我们的长稳测试尚未覆盖 RSS。
6. **权重许可不清**：官方称模型/权重受 AGPL 约束，但 AGPL 是软件许可；权重与导出件的法律性质需法务确认。
7. **替代框架未实测**：YOLOX/MMDetection/RF-DETR/PaddleDetection 的许可来自仓库字段，权重许可、6 GB 训练可行性、Orin 部署均未验证。
8. **YOLO27 路线不确定**：官方说"今年晚些时候"，无日期；不能把 YOLO27 纳入任何交付计划。
9. **版本漂移**：本报告锁定 8.4.219 审查、生态内 8.4.216 实测；两者差异未逐条比对。

---

## 13. References（参考）

### 仓库与版本

- `ultralytics/ultralytics` — <https://github.com/ultralytics/ultralytics>，tag `v8.4.219`，commit `3a31e32f2e254a13f86ea274d6331e19d0cb4d47`（2026-11-25）。
- `pyproject.toml`（依赖、Python 版本、extras）— 同上 SHA，约 `:68-190`。
- `LICENSE`（AGPL-3.0，661 行；§2 私有使用 `:152-153`；§13 网络交互 `:539` 起）。
- `README.md:125`（YOLO27 未发布）；`docs/en/models/yolo26.md`；`docs/en/models/yolo27.md`；`docs/en/guides/raspberry-pi.md:139-204`；`docs/en/guides/nvidia-jetson.md:531-600`；`docs/en/help/privacy.md`；`docs/en/help/contributing.md:234-306`。
- 关键源码：`ultralytics/utils/__init__.py:81,1147-1162,1283,1492-1564,1703-1704`；`utils/checks.py:536-660`；`utils/events.py:50-235`；`utils/patches.py:228-252`；`nn/tasks.py:1861-1996`；`engine/predictor.py:523`；`engine/exporter.py:911-915`；`utils/downloads.py:543`。
- CI/测试：`.github/workflows/ci.yml:69-84,518`；`.github/workflows/fuzz.yml`；`.github/workflows/stale.yml:49-52`；`tests/`（230 个 `test_`）。

### 论文

- G. Jocher, J. Qiu, M. Liu, S. Lyu, F. C. Akyon, M. E. Kalfaoglu, "Ultralytics YOLO26: Unified Real-Time End-to-End Vision Models," arXiv:2606.03748, 2026-06-02. <https://arxiv.org/abs/2606.03748>（本次只读摘要与官方模型页，未读全文附录/消融）。

### Issue / 许可讨论

- #22640 "Seeking help: Does our use case comply with AGPL-3.0?"（2025-11-10，含 glenn-jocher 回复）。
- #26703 "Questions About AGPL-3.0 Licensing: Private Datasets and Source Code Disclosure"（2026-10-16，含 pderrenger/glenn-jocher 回复）。
- #25030 "YOLO26n inference latency much higher than official benchmark on Jetson AGX Orin"（2026-07-05）。
- #21241 "YoloV11 CPU Memory Leaks When Access Inference Results"（2025-06-30）。
- #22791 "memory leak"（2025-11-25）。

### 元数据与统计

- PyPI `ultralytics` 8.4.219（license AGPL-3.0，requires-python >=3.8）：<https://pypi.org/project/ultralytics/>。
- PyPI `ultralytics-platform` 0.1.121（AGPL-3.0-only，>=3.11）：<https://pypi.org/project/ultralytics-platform/>。
- pypistats 近 30 天下载：<https://pypistats.org/packages/ultralytics>。
- GitHub API：repo/tags/releases/commits/issues（访问日期 2026-11-26）。

### 替代方案（许可证字段来自 GitHub API，访问 2026-11-26）

- YOLOX — Apache-2.0，<https://github.com/Megvii-BaseDetection/YOLOX>。
- MMDetection — Apache-2.0，<https://github.com/open-mmlab/mmdetection>。
- RF-DETR — Apache-2.0，<https://github.com/roboflow/rf-detr>。
- Super-Gradients — Apache-2.0，<https://github.com/Deci-AI/super-gradients>。
- PaddleDetection — Apache-2.0，<https://github.com/PaddlePaddle/PaddleDetection>。
- YOLOv6 — GPL-3.0，<https://github.com/meituan/YOLOv6>（拒绝）。

### 生态内部

- `jcheng-perception/config/gpu.yaml:22,42`；`ros2_ws/src/jcheng_perception_gpu/jcheng_perception_gpu/detectors.py:200,268,420-423`；`node.py:109,169,365`；`capability.yaml:123-134`；`docs/MODEL_ITERATION.md`；`deploy/README.md:45`；`LICENSE-REVIEW.md:22,49`。
- `jcheng-research/references/perception/jetson-agx-orin.md`（JetPack 6.2 / TRT 10.3 / 无 torch / 19V 供电）。
- 来源记录：[ultralytics-repository.md](../references/perception/ultralytics-repository.md)。
- 实验设计：[experiments/20261126-ultralytics-runtime-audit/design.md](../experiments/20261126-ultralytics-runtime-audit/design.md)。

---

## 附录 A — 检测器平替候选（2026-11-27 补充）

> 本附录在主报告完成后补充，回答"如果要把检测器换成许可证干净、低延迟、低算力的项目，选什么"。**主报告 §10 的结论不变**（Ultralytics 只做开发期工具，生产跑导出工件）；本附录**不注册新实验**，也不改变 §11 已有的 MVE。

### A.1 先明确基线

- 若基线是 **YOLO26n**（40.1 AP / 2.4 GFLOPs / 2.6M 参数 / 1.7 ms T4）：**"算力更低且精度不掉"基本不存在**——YOLO26n 已在 Pareto 前沿。平替的收益是**许可证**和**同延迟下更高 AP**，不是更省 FLOPs。
- 若基线是 **YOLOv8n / YOLOv8s**（37.3 / 44.9 AP）：选择空间大；D-FINE-N、RTMDet-tiny、RF-DETR-N 都能做到"精度不降、算力更低"。

### A.2 同口径对比

未标 †/‡ 的 7 行来自 Roboflow SAB 同一套评测（COCO `val2017` 全量 5,000 张、pycocotools、T4 TensorRT FP16、batch 1），**可以直接横比**；† 行来自各自 README（TRT 版本不同，仅作量级参考）；‡ 行来自 Ultralytics 官方表，不能与 SAB 直接比。

| 模型 | 许可 | COCO AP50-95 | 延迟 (ms) | 参数 (M) | 输入 | 备注 |
|---|---|---:|---:|---:|---:|---|
| YOLO26-N | AGPL-3.0 | 40.3 | **1.7** | 2.6 | 640 | 当前基线，算力最低 |
| **D-FINE-N** | **Apache-2.0** | **42.7** | 2.1 | 3.8 | 640 | **最接近的无损平替** |
| LW-DETR-T | Apache-2.0 | 42.9 | 1.9 | 12.1 | 640 | 同延迟，参数偏大；未审仓库 |
| **RTMDet-tiny** † | **Apache-2.0** | 41.1 | 2.34 | 4.8 | 640 | 最成熟；MMDetection，TRT 8.4.3 |
| **RF-DETR-N** | **Apache-2.0** | **48.4** | 2.3 | 30.5 | 384 | 精度最高档，参数大、分辨率低 |
| RF-DETR-S | Apache-2.0 | 53.0 | 3.5 | 32.1 | 512 | 精度优先 |
| D-FINE-S | Apache-2.0 | 50.6 | 3.5 | 10.2 | 640 | 精度/参数更均衡 |
| YOLO11-N | AGPL-3.0 | 37.4 | 2.5 | 2.6 | 640 | 许可证不解决 |
| YOLOv8n ‡ | AGPL-3.0 | 37.3 | 0.99 | 3.2 | 640 | 8.7 GFLOPs；不同 harness |
| YOLOv8s ‡ | AGPL-3.0 | 44.9 | 1.20 | 11.2 | 640 | 28.6 GFLOPs；当前烟测模型 |
| PicoDet-M 416 † | Apache-2.0 | 37.5 | 12.7 (CPU) | 3.46 | 416 | x86 CPU；Pi 会更慢 |
| PicoDet-S 416 † | Apache-2.0 | 32.5 | 6.6 (CPU) | 1.18 | 416 | x86 CPU |
| NanoDet-Plus-m-1.5x-416 † | Apache-2.0 | 34.1 | 25.49 (ARM) | 2.44 | 416 | 4×A76 |

### A.3 三个档位

1. **GPU 部署、要"无损换许可"（推荐）**：**D-FINE-N** 首选（42.7 AP、2.1 ms、3.8M、640、ONNX+`trtexec`）；**RTMDet-tiny** 备选（41.1 AP、4.8M、8.1 GFLOPs，生态成熟但 2024-08 后停更）；**LW-DETR-T** 同延迟、参数偏大。
2. **精度优先**：**RF-DETR-N/S**（48.4/53.0 AP，2.3/3.5 ms，384/512）；**D-FINE-S**（50.6 AP、3.5 ms、10.2M、640）在参数上更均衡。RF-DETR-N 的 30.5M 参数和 6 GB 微调可行性需要先验证。
3. **Pi 5 CPU 上跑检测（当前架构不需要）**：**NanoDet-Plus-m-1.5x-416**（34.1 AP、2.97 GFLOPs、约 25 ms/4×A76）或 **PicoDet-M/S 416**（37.5/32.5 AP）；代价是相对 YOLOv8n 掉 3–6 AP。

### A.4 隐藏成本

- **解码器适配**：`jcheng-perception` 的 `detectors.py` 目前只解 YOLO 风格输出；D-FINE/LW-DETR/RF-DETR 是 NMS-free DETR 输出，RTMDet 有独立 decode，都需要新的 pre/postprocess 适配器与测试。这是主要集成成本。
- **训练栈**：D-FINE 依赖 mmengine/mmcv，RTMDet 依赖 MMDetection；6 GB 上 D-FINE-N/S 与 RTMDet-tiny 微调可行，RF-DETR-N 的 30.5M 参数需验证。
- **分辨率口径**：RF-DETR-N 是 384 输入，和 YOLO 的 640 不是同一条件；矿石/小目标可能吃亏，抬到 640 后延迟会上升。
- **数据域**：COCO AP 不等于矿石/货架；必须用自有数据微调后重测，排序可能反转。
- **延迟口径**：表内是 T4 TensorRT FP16；本机 3060（`yolov8s` 9.0 ms FP32）与 Orin（JetPack 6.2 / TRT 10.3）都要实测；DETR 类模型的 INT8 精度损失也可能大于 YOLO。

### A.5 建议

- **先试 D-FINE-N**：Apache-2.0、640 输入、3.8M 参数，精度和延迟都压得住 YOLO26n；用现有矿石/货架数据微调，和当前 YOLOv8n/s 做同帧对比。
- **备选 RTMDet-tiny**：不想碰 mmengine 训练栈时更稳。
- **精度优先再上 RF-DETR-N/S**：先确认 6 GB 微调与 384/512 分辨率是否够用。
- **pose/OBB 不要一起换**：这些平替主要解决 detect；腕部关键点仍建议 MMPose（Apache-2.0）或暂时保留 Ultralytics，OBB 可看 RTMDet-R（Apache-2.0，MMRotate）。
- **不新增 MVE**：本附录只做选型记录。未来若真要换检测器，沿用主报告 §11 MVE-2 的"同帧、同 `conf`/`iou`、匹配率/延迟"方法即可，不另注册实验。

### A.6 附录来源（2026-11-27）

- D-FINE（Apache-2.0）：<https://github.com/Peterande/D-FINE>；README model zoo（D-FINE-N 42.8 AP / 2.12 ms T4 / 4M，ONNX 导出 + `trtexec`）。
- RF-DETR（Apache-2.0：N/S/M/L；Atto/Femto/Pico/XL/2XL 为 PML 1.0）：<https://github.com/roboflow/rf-detr>；SAB 同口径表（T4 TRT FP16、COCO `val2017`）。
- RTMDet（Apache-2.0，MMDetection）：<https://github.com/open-mmlab/mmdetection/tree/main/configs/rtmdet>；README 表（RTMDet-tiny 41.1 AP / 2.34 ms T4，TRT 8.4.3）。
- PicoDet（Apache-2.0，PaddleDetection）：<https://github.com/PaddlePaddle/PaddleDetection/tree/develop/configs/picodet>；README CPU 延迟表。
- NanoDet（Apache-2.0）：<https://github.com/RangiLyu/nanodet>；README ARM 延迟表。
- LW-DETR：仅在 RF-DETR 的 SAB 表中引用（T 42.9 AP / 1.9 ms / 12.1M，Apache-2.0 由该表标注）；本次未审仓库。
- YOLOv8 / YOLO26 官方表：<https://github.com/ultralytics/ultralytics/blob/main/docs/en/models/yolov8.md>。
- GitHub API 的 license/活跃度字段：访问 2026-11-27。表内数字为各来源的公开 benchmark，**本次未训练、未导出、未在本机运行**。
