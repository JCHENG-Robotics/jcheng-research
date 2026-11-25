# VP-VLA — 视觉提示接口、代码、权重与上游依赖

- **类型**：一手论文 + 官方仓库 + 模型权重 + 上游依赖
- **访问日期**：2026-11-25
- **阅读范围**：论文 PDF 全文 25 页（正文 §1–§5、附录 A–H、表 1–12）；
  仓库 README、文件树在 `5d92396` 读取；**未逐行审计** `data_preparation/`、
  `examples/*/train_files/`、`deployment/model_server/` 的代码；**未运行**任何
  代码或仿真。下文对论文数字为 A 级；对未读代码标“未审计”。

## 论文

- Wang, Chen, Liu, Ye, Chen, Lu, Liu, Yu, Jia。*VP-VLA: Visual Prompting as an
  Interface for Vision-Language-Action Models*。arXiv:2603.22003v3，2026-05-09，
  25 页，preprint。<https://arxiv.org/abs/2603.22003>
- 许可：CC BY 4.0（PDF XMP `dc:rights`）。
- 本地副本：[`papers/20261125-vp-vla.pdf`](papers/20261125-vp-vla.pdf)
  （ghostscript 压缩，1.1 MB；原始 9.6 MB，页数与文字可读性已核对）。
- 方法：System 2 = Qwen3-VL-4B planner + SAM3；System 1 = QwenOFT
  (Qwen3-VL-4B) + action decoder；事件驱动（夹爪开合；工具任务用 z 轴抬升）；
  crosshair/bbox 叠加为独立视觉提示图；grounding CE 只在关键帧、只回传 VLM。
- 关键数字：RoboCasa 53.8 vs 48.8；SimplerEnv 58.3 vs 50.0；真实垃圾分类
  87.5/85.0 vs 80.0/63.3；彩蛋 77.1/75.0/75.0 vs 58.3/29.2/54.2；蛋盒
  91.25/68.75 vs 70.63/55；消融 full 53.8 / no grounding 49.4 / all-frame
  49.5 / point 47.3 / direct overlay 50.8；分解消融 57.3 vs 58.3。
- 算力：8×H200 140 GB，约 46 h；推理 1×4090 24 GB；延迟 0.78 s（8B API）、
  SAM3 0.36 s、chunk 0.108 s。
- 真实机器人：Franka Research 3 7-DoF，第三人称 + 腕部 RGB，224×224，
  50 演示/物体，10k steps，8 GPU，batch 256。
- 局限（作者自述）：仅 2D bbox/crosshair；复杂任务需 3DGS/接触热力图。

## 官方仓库

- <https://github.com/JIA-Lab-research/VP-VLA> @
  `5d92396e96ef3a20eacfeecb4771db6b1016b93f`，MIT（Copyright StarVLA
  Team）；代码 2026-04-12 发布。
- 文件树：`data_preparation/`（VLM 子任务 + SAM3 掩码，输出 `.npz`）、
  `examples/*/train_files/`（训练配置，`feed_both_images`）、
  `examples/*/visual_prompt_utility/`（SAM3/VLM client/server）、
  `deployment/model_server/`（policy server）。
- 评测需要三服务：policy server、SAM3 server、VLM server；README 的脚本按 GPU
  启动，8 GPU 是默认配置。
- 权重：README 指向 HF collection `Vincent2311/vp-vla`；模型卡许可**未核对**。

## 上游依赖

- starVLA：<https://github.com/starVLA/starVLA>，默认分支 `starVLA_dev`；
  GitHub 许可识别为 NOASSERTION，**条款未读**。
- Qwen3-VL-4B-Instruct：<https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct>，
  Apache-2.0（HF API）。
- SAM3：<https://github.com/facebookresearch/sam3>，GitHub 许可
  NOASSERTION/Other（自定义），**条款未读**；商用/再分发需单独核对。

## 对 JCHENG 的相关性

- 论文的 5 个真实/仿真平台没有 5-DoF 机械臂；ArmPi 的动作空间、夹爪、相机
  视角都不同，不能把论文增益直接外推。
- 论文的 0.78 s 是 8B planner 经 OpenRouter 的 API 延迟；0.36 s SAM3 是 4090
  数字；不是 4B 本地 + 3060 的端到端延迟。
- 论文的真实机器人数据未发布；复现真实任务需要自采 5-DoF 演示。
- 接口层（VLM + SAM3 + crosshair/bbox）可以独立于 System 1 评估；这是本任务
  书把 B 路线单列的原因。
