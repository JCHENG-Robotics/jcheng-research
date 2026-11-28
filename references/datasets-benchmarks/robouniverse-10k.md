# RoboUniverse-10K — 环境包、评测仓库与数据集（来源记录）

- **类型**：一手来源（arXiv v1 全文 HTML、GitHub 仓库原始文件与 API、Hugging
  Face 数据集 API / raw / 单个任务 ZIP）。项目页数字与论文一致，按一手处理；
  AI News 的"数据集卡片披露 68 个替换"说法按 **D 级**处理（见末节）。
- **访问日期**：2026-11-28
- **阅读范围**：完整读取 arXiv:2611.31002v1 HTML 的摘要、§2、§3、§4、§6、
  §7.1–7.3、§8.1 与表 5–7；完整读取 GitHub `README.md`、
  `requirements.txt`、`evaluate.py`（169 行）、`inference.py` 的 README 说明、
  `docker/sim-base/Dockerfile`、`docker/agent-base/Dockerfile`；读取 HF 数据集
  卡片、`catalog.csv`（10,807 行）、`splits/heldout500.csv`（500 行）、
  `THIRD_PARTY.md`；下载并静态检查任务包
  `tasks/franka/000/000247_rotate_twist.zip`（1,757,355 B，47 个文件），
  读取 `release.json`、`instruction.md`、`task.toml`、`tests/grade.py`、
  `environment/roboenv_client.py`、`workspace/verify.py`、
  `workspace/task_definition.json`、`workspace/env_spec.json`、
  `workspace/dependencies.json`、`workspace/evidence.md`。
  **未做**：没有 GPU / Isaac Sim 运行；没有执行任何包内脚本；没有下载完整
  18.6 GB 数据集；没有复现任何模型分数；没有实机。

## 关键 URL 与版本

| 项目 | 版本 / 标识 |
|---|---|
| 论文 | arXiv:2611.31002v1，2026-11-23 提交，cs.RO（cross-list cs.CL），CC BY 4.0，DOI 10.48550/arXiv.2611.31002 |
| 项目页 | <https://lab.einsia.ai/robo-universe> |
| 评测仓库 | <https://github.com/Einsia/RoboUniverse-10K> @ `532745c834`（2026-11-26T11:55:45Z，"Release RoboUniverse-10K"），Apache-2.0，95★，1 fork，0 open issues，仓库大小 1,653 KB，1 个提交 |
| 数据集 | HF `Einsia/RoboUniverse-10K`，revision `0775b4832b70`（lastModified 2026-11-26T12:51:27Z），10,807 个 ZIP，18.6 GB，75 likes，8,969 downloads，`license` 字段为空 |
| 评测框架 | `harbor==0.25.0`（Terminal-Bench 的容器化评测框架，论文 ref [43]） |
| 仿真 | Isaac Sim 5.1.0.0（任务包 `dependencies.json`），Python 3.11.18（任务包运行时） |
| 模型 | `Einsia/RoboUniverse-35B-A3B`，Qwen3.6-35B-A3B SFT；下载 72 GB；SGLang 0.5.21 服务 |
| Agent 适配器 | Claude Code 2.1.283（npm tarball，sha256 校验） |
| 双臂资产上游 | <https://github.com/agilexrobotics/piper_isaac_sim> @ `8e1f88fdb7afca49c40e9a0c1c01cc588e86f0d2`（125★，无 LICENSE 文件） |

## 事实摘要

1. **规模**（`catalog.csv` 实算）：10,807 行；`franka` 4,132、`agilex` 6,675；
   总归档 18.6 GB，单包中位数 1.1 MB、最大 32.5 MB。`splits/heldout500.csv`
   正好 500 行，字段含 `final_index, case, robot, compact_category,
   original_category_id, original_category_zh`。
2. **测试集构成**（论文 §3.1、表 6）：200 单臂（45/68/68/19）+ 300 双臂
   （93/99/78/30），覆盖 8 个任务族。
3. **任务包结构**（S 级，静态检查 `000247_rotate_twist`）：47 个文件，含
   `instruction.md`、`task.toml`、`tests/grade.py`、`solution/oracle.py`、
   `workspace/scene.py`、`env_backend.py`、`reference_controller.py`、
   `verify.py`、`verifier_fixtures.py`、`task_definition.json`、`env_spec.json`、
   `dependencies.json`、`evidence.md` 与 10 张纹理 PNG。
4. **接口**（`env_spec.json`）：`joint_position_target`，9 维（7 关节 + 2 指），
   控制 20 Hz（`control_dt_s=0.05`），物理 120 Hz（`physics_dt_s=1/120`）；
   图像 + 关节位置/速度为公开观测，无物体位姿。
5. **隔离与判分**（`task.toml`、`tests/grade.py`、`verify.py`）：
   `[verifier] environment_mode="separate"`、`network_mode="no-network"`；
   grade.py 只信任 sim 服务收集的 `result.json`，`infra_error.json` 直接抛错；
   reward 必须与 `verdict` 一致；verify.py 要求 120 Hz 私有证据（`contact_graph`、
   `forces`、`q/qd` 等）、时间连续性、目标几何、以及 `scene.py`/`env_backend.py`/
   `drive_config.json`/`task_definition.json` 的 sha256 绑定，缺证据返回
   `inconclusive`。
6. **资源声明**（`task.toml`）：`cpus=6`、`memory_mb=32768`、`storage_mb=30720`、
   `gpus=1`、`gpu_memory_mb=6144`；README 实测每仿真 **18–44 GiB** 显存、
   ≥8 核。两者不一致，见报告 §08。
7. **评测器**（`evaluate.py`）：`materialize()` 校验 ZIP 与 `release.json` 的
   case 身份，从 `upstream.json` 拉取 NVIDIA Isaac 资产 / Piper / RoboDojo 资产
   并逐个校验 sha256；把 sim 的 CPU 下限抬到 8（`ROBOUNIVERSE_SIM_CPUS`）；
   给 sidecar 打补丁以适配 NVIDIA 独立 Isaac Sim 镜像（无
   `importlib.metadata.version('isaacsim')`）；重写 docker-compose 的 EULA 与
   bind mount；最后调用 `harbor run -a <agent> -e docker`。
8. **判分口径**（README、论文 §3.1）：单次尝试，成功 1 / 失败或
   inconclusive 0，基础设施异常不计分；报告 successes/500 与 scored/missing/error。
9. **SFT**（论文 §4.1）：17K 轨迹、0.79B token，GPT-6 Astra (Medium) 生成；
   Qwen3.6-35B-A3B 语言主干全参 SFT，视觉编码器与 aligner 冻结；
   AdamW 1e-5、5% warmup、cosine 到 1e-6、batch 64、256k 上下文、约 1,500
   H100 小时；0.8%→21.2%（单臂 2.0→40.5，双臂 0.0→8.3）。
10. **分数**（项目页，与论文一致）：GPT-6.2 Astra 85.8、Claude Opus 5.5 76.8、
    GPT-6 Astra 54.6、GPT-6.1 Sol 49.4、DeepSeek-V4.1-Flash 10.0、
    Tencent-Hy4 9.2、Qwen4-Max 8.6、GPT-6 Luna 5.6、Kimi-K3.1-Pro 5.0、
    Doubao-Seed-Evolving 4.0、GLM-5.3-Flash 2.6。
11. **未发布**：Real2Sim 构建与 QA 流水线代码不在仓库；仓库只有评测/推理
    代码。论文 §9 给出 builder/QA/rollout 提示词，但不是可执行流水线。
12. **许可**：仓库 Apache-2.0 + NOTICE；数据集卡片无 `license` 字段，仅
    `THIRD_PARTY.md` 声明第三方资产沿用上游条款（NVIDIA Franka 资产、
    `agilexrobotics/piper_isaac_sim`、RoboDojo 资产）；Isaac Sim 需接受 NVIDIA
    EULA。

## 争议：AI News 的"68 个替换 / 38 个 grader 修改"

AI News（2026-11-25，AI News AI Editorial）称数据集卡片披露：500 个评测条目中
68 个（13.6%）用"先前观察到的成功"替换，38 个（7.6%）grader 被修改，并写明
"不应视为 blind random sample"、"train/test disjointness is not guaranteed"。
**本次核对不成立**：HF 数据集只有 1 个提交（`0775b48`，2026-11-26T12:51:27Z，
标题 "Release RoboUniverse-10K"），其 `README.md`（2,804 B）不含
`68`/`blind`/`random sample`/`disjoint`/`replace` 任一关键词；论文 v1 也没有
该披露，只说候选任务按分层抽样、专家验证不合格者"removed from the candidate
pool"。因此该说法按 **D 级**处理，不能作为引用事实。可确证的只有：测试集与
训练集来自同一 Real2Sim 流水线，且 500 个任务全部通过专家验证后才保留——这本身
意味着测试集不是对 10,807 个环境的盲随机抽样。
