# SST 仓库审计 — Lingbot-Challenge-SST

- **类型**：源码审计（静态分析；未执行任何代码）
- **仓库**：<https://github.com/YzmYalier/Lingbot-Challenge-SST>
- **Commit**：`8797aa31dd9798a6e931d57857f32cd5de372b6c`（main），2026-11-19
  推送；2026-11-18 创建。共 5 个 commit（一次压缩发布 + 四次文档提交）；第二个
  分支 `page` 存放 GitHub Pages 站点。
- **体量**：约 4,517 个 tree 条目，仓库约 17.5 MB，工作树 78 MB；Python 约
  7.97 MB，CUDA 约 349 KB，Shell 约 103 KB（GitHub languages API）。
- **许可证**：**根目录没有 LICENSE**；GitHub API 返回 `license: null`。vendored
  的 `Lingbot-vla-challenge/LICENSE` 是 Apache-2.0，`RoboTwin/`、`sam3/` 各自
  带许可证。因此 SST 自有增量（`auto_mask/`、`tools/`、`inference/`、
  `data_inputs/`）没有明确授权。
- **Checkpoints**：未发布；README badge 为 "Coming soon"，报告页导航指向占位符。
  只发布了 8.33 GiB 数据集。
- **阅读范围**：完整 README、配置、入口脚本、关键源码、测试、`base.json`、
  `public_weights.json` 文档；未运行代码、未下载模型、未使用 GPU。

## 目录与调用链

```text
process_data.sh --stage raw      -> tools/rebuild_robotwin_v30_from_v21.py
process_data.sh --stage masks    -> auto_mask/pipeline_lerobot.py
                                    -> Qwen 提词（vLLM）
                                    -> SAM3 服务（sam3/tools/...）
                                    -> Qwen mask judge（sam3/tools/sam3_mask_judge.py）
                                    -> mask_style.py 渲染
process_data.sh --stage assemble -> 成对 raw + SAM 数据集
train.sh                         -> Lingbot-vla-challenge/train_multinode.sh
                                    -> tasks/vla/train_lingbotvla.py + 配方 yaml
eval.sh                          -> script_sam.sh
                                    -> inference/cam_high_masker.py（在线掩码）
                                    -> 策略服务 + RoboTwin 环境
```

## 代码结论（文件 + 符号 + 行号，pin 在上述 commit）

| 结论 | 位置 |
|---|---|
| Padding 从 loss 分子与分母同时剔除；fp32 累加 | `Lingbot-vla-challenge/lingbotvla/models/vla/lingbot_vla/action_loss.py:6-45`（`masked_action_loss`） |
| `mask_action_pad` 选择 masked reduction | `.../modeling_lingbot_vla_v2.py:1297` |
| 分模块 LR：7 个模块、未知 key 报错、0 冻结 | `.../optim/module_lr.py:29-125`（`MODULE_NAMES`、`resolve_module_lr_mult`、`freeze_zero_lr_modules`、`build_module_param_groups`） |
| 教师读 `sam_info.json` 记录的原图；episode 数必须一致 | `.../data/vla_data/base_dataset.py:101-131`、`.../data/dataset.py:94` |
| 评测用 checkpoint 的 `sam_info.json` 记录样式渲染 | `tools/evaluation_config.py:41-44` |
| 提词是 73 行手工词表，含逐类 `MISSED` 规避；始终包含 `robot, robot arm` | `vllm_space/sam3_prompt.py`（73 行） |
| SAM3 检测阈值 | `auto_mask/pipeline_lerobot.py:100`（`score_threshold_detection=0.3`，`new_det_thresh=0.5`） |
| Judge：两图 yes/no 问题、logprob 比值、阈值 0.5、regrow 复判 | `sam3/tools/sam3_mask_judge.py:37-45,109`；`auto_mask/pipeline_lerobot.py:1174,1194` |
| 修复验证 PTS（`frame.pts * time_base == i/fps`）、SHA-256 与内容哈希 | `tools/rebuild_robotwin_v30_from_v21.py:119,145-155,326` |
| 数据溯源：2,500 episodes、548,893 帧、250,000 槽、float32 精确匹配 | `data_inputs/preparation_report.json` |

## 工程质量

- **强项**：数据溯源（SHA-256、manifest、`validation_summary.json`）、明确写出
  验证局限、padding mask 数学正确、评测样式从 checkpoint 回读、episode 数不一致
  时启动报错、针对数值一致性与 LR 分组的测试。
- **复用弱点**：`base.json` 含本机解释器路径（`/home/pc/miniconda3/...`、
  `/usr/local/cuda-13.0`、`/data1/szh/...`）；4 套 conda 环境；vLLM 需从源码
  编译（v0.20.2，`bc150f5`）；约 103 GB 权重/输入；评测在策略之外还要
  mask-Qwen 与 SAM3 服务（其 evidence 头记录 8 GPU × 4 slot 用于策略+仿真）。
  无 CI，无 `.github` 目录。
- **测试**：`Lingbot-vla-challenge/tests/` 10 个文件、`tests/` 3 个、`auto_mask/`
  3 个；以 CPU 数据完整性与单元测试为主，没有 GPU 端到端，也没有实机。
- **文档与代码**：`page` 分支的 `blog.md` 是过期草稿（§7 重复、数字与发布页
  不一致）；发布版 `index.html` 与 `data/results.csv` 才是自洽来源。
  `inference/cam_high_masker.py` 仍写着默认 `outside_scale=0.2`，而最终数据集与
  评测用 0.1 + 2 px 白边（评测路径覆盖了默认值）。

## 已执行 vs 推断

- **已执行**：没有运行 SST 的任何代码。本仓库唯一的计算是对其发布计数的统计
  复算（`experiments/20261125-lingbot-sst-reanalysis/`）。
- **静态**：上文所有文件/行号结论。
- **推断**：决赛真机方案不在本仓库；发布的实验是 RoboTwin 初赛赛道。本报告不对
  决赛真机栈作任何断言。

## 2026-11-26 补充：SAM3 适配层与版本

同一 commit `8797aa31` 的追加静态审读，聚焦 SAM3：

- **vendored 版本**：`sam3/` 是上游全量树（204 文件 / 160 Python 文件），已包含
  SAM 3.1 Object Multiplex 代码（`multiplex_mask_decoder.py`、`sam3_multiplex_*`、
  `video_tracking_multiplex.py`）；`build_sam3_predictor(version="sam3.1")` 映射到
  `facebook/sam3.1/sam3.1_multiplex.pt`。但 SST 的掩码器默认 `version="sam3"`
  （`sam3/tools/sam3_video_masker.py:53`），数据生成用 3.0 权重。
- **在线服务**：`sam3/tools/sam3_stream_server.py` 是 stdlib HTTP 服务，
  `/start`、`/step`、`/end`、`/start_judged`、`/step_judged`；一个进程独占一张
  GPU，GPU 工作用锁串行化；`client_id` 防会话泄漏；空闲会话回收。
  `base.json` 设 `inference.gpu="1"`、`memory_window=10`。
- **因果化封装**：`sam3/tools/sam3_stream_tracker.py` 让 `num_frames` 随帧增长，
  只回看历史；docstring 明确写出与离线训练集的差异——离线 `hotstart_delay=15`
  压住前 15 帧输出，在线不能等，被 hotstart 移除的物体从该帧起消失。
- **提示词契约**：`vllm_space/sam3_prompt.py` 73 行，英文；逐类短语 + 颜色备份 +
  `MISSED` 规避，强制 `robot, robot arm`。词表本身就是方法的一部分。
- **评审参数**：`tools/services.py` 固定 `score_threshold_detection=0.3`、
  `new_det_thresh=0.5`、judge 阈值 0.5、`outside_scale=0.2`、`regrow=2.0`、
  `regrow_min_area=0.002`、超时 120 s；最终渲染用 0.1 + 2 px 白边。
- **许可证/打包**：`sam3/LICENSE` 是 SAM License（2025-11-19）；
  `sam3/pyproject.toml` 的 `MIT` classifier 与实际许可证不一致（打包元数据错误）。
  SST 根目录仍无 LICENSE，自有适配层（`auto_mask/`、`tools/`、`inference/`）无授权。
- **未执行**：以上均为静态；没有运行 SST 的 SAM3 服务，也没有下载 gated 权重。

相关：[SAM 3 来源记录](../perception/sam3.md)、
[SAM3 尝试路线报告](../../reports/20261126-sam3-sst-open-source-attempt-route.md)。
