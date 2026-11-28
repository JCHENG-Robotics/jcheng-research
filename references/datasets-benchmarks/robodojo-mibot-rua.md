# RoboDojo 榜单 — Mibot-RUA / Mibot_RSI（simulation agent track）

- **类型**：一手来源（榜单 SPA bundle、GitHub PR / 代码、Hugging Face 元数据、
  arXiv 摘要页）。其中"知识快照内容计数"来自榜单委员会自己的 findings，不是本次
  下载核对的，按 **B 级**处理。
- **访问日期**：2026-11-27
- **阅读范围**：完整读取榜单 bundle（498,357 B，sha256
  `a23d17587b8b062304d4d97067ca6260c9d2b01cced7d2f01629069cd4756195`）中的
  changelog、`Bo`/`rn` 数据数组、`qo`（星号条目 findings）、Agent Track Rules
  文本和指标函数；完整读取 PR #204 的 body、文件清单、`README.md`、
  `runtime/EXPORT.json`、`release.json` 头部、`prompts/priors.json`、
  `submission.py` 455–525 行、`runtime/context.py` 60–100 行、
  `knowledge/store.py` 930–1000 行；读取 RoboDojo README 和安装文档；读取
  XR-1 README/模型卡与 arXiv 摘要；读取 PyRUA-Lean README。
  **未做**：没有用浏览器渲染榜单页面；没有下载 gated 知识库归档；没有运行
  RoboDojo / Isaac Sim；没有调用 GPT-6-Astra；没有读 RoboDojo、XPolicyLab、
  PyRUA-Lean 论文正文；没有读 PR 的全部 11,692 行 diff。

## 关键 URL 与版本

| 项目 | 版本 / 标识 |
|---|---|
| 榜单页 | <https://robodojo-benchmark.com/leaderboard> |
| 榜单 bundle | <https://robodojo-benchmark.com/assets/index-GzJO5R6C.js>，sha256 `a23d17587b8b062304d4d97067ca6260c9d2b01cced7d2f01629069cd4756195` |
| RoboDojo 仓库 | <https://github.com/RoboDojo-Benchmark/RoboDojo> @ `c3af1ac6ad7302c0c09d17f4b050fd3a5c68c921`（2026-11-19），MIT，960★ |
| RoboDojo 论文 | arXiv:2607.04434，v1 2026-07-05，v3 2026-07-08 |
| 安装要求 | <https://robodojo-benchmark.com/doc/usage/install-and-download/>（Ubuntu 22.04 x86-64 / 32 GB RAM / 16 GB+ VRAM / Isaac Sim 5.1 / 300 GB） |
| XPolicyLab | <https://github.com/XPolicyLab/XPolicyLab> @ `24c49cb3e217080af6c66bd7704711d78562fbe0`（2026-11-26） |
| PR #204 | <https://github.com/XPolicyLab/XPolicyLab/pull/204>，open，2026-10-26 创建，head `ffanyt/XPolicyLab:mibot-rsi` @ `c048d3b3f111de2d2607dbfc3e7c14bf243c0cf8`，11 commits，50 files，+11,692 |
| 运行时导出 | `runtime/EXPORT.json`，source commit `42e0d7c7637adf655d7ad8e6a31875ac645213f9`，36 个文件逐个 sha256 |
| 知识库 | HF dataset `ffanyt/Mibot-RSI-knowledge-latest`，gated `manual`，public，lastModified 2026-11-11，revision `a182734b5f271d522c6ff9b8718bac7553a7dbb9` |
| XR-1 仓库 | <https://github.com/XiaomiRobotics/Xiaomi-Robotics-1> @ `0dd7aef8dc87296246aae812a1f59ccb708e5546`（2026-09-09），Apache-2.0，764★ |
| XR-1 论文 | arXiv:2607.15330，v1 2026-07-16，v2 2026-07-22 |
| XR-1 checkpoint | HF `XiaomiRobotics/Xiaomi-Robotics-1-5B`，Apache-2.0，2026-07-28 创建，5B，Qwen3-VL-4B-Instruct 骨干 |
| PyRUA-Lean | <https://github.com/DAGroup-PKU/PyRUA-Lean> @ `8543207e80e17176f2f0d010cb52303d446e951a`（2026-11-26），Apache-2.0，296★；arXiv:2610.01939 |

## 事实摘要

1. **榜单条目**：changelog 2026/11/26 —
   "Add Mibot-RUA* (Avg. (w/o Open): 83.94 / 79.33%, contributed by Xiaomi
   Robotics) to the sim leaderboard (agent track)."
   `83.94` 是 Score，`79.33%` 是 success rate；`Avg. (w/o Open)` 是 agent 赛道的
   四维均值（generalization 的 std/rand 先平均，再加 precision、long-horizon、
   memory），不含 Open 维度。
2. **条目数据**：generalizationStd 74.87/70；generalizationRand 75.27/69.67；
   precision 76.39/73.5；longHorizon 87.09/77；memory 97.23/97；average
   83.94/79.33；**没有 `open` 字段**。四维手算与 average 完全一致：
   `(75.07+76.39+87.09+97.23)/4 = 83.945`，
   `(69.835+73.5+77+97)/4 = 79.334`。
3. **不是 VLA**：PR #204 的 policy 名 `Mibot_RSI`，eval-only；GPT-6-Astra 通过
   Responses API 看三路 RGB + 机器人状态，写 Python 调小型机器人 SDK，以 joint
   target 驱动 ARX X5。无训练、无 `process_data.sh`/`train.sh`。
4. **小米自己的 VLA 是另一条**：Xiaomi-Robotics-1（XR-1）在主榜为
   20.07 / 13.93（五维平均），论文 arXiv:2607.15330 也报 20.07，超过此前 13.07。
5. **星号原因（委员会 findings）**：
   - 按 `task_name` 路由的 RSI 蒸馏知识：34 个 Standard + 12 个 `_random` 任务各挂
     冻结快照；只有 8 个 Open 任务用 `general/` 通用快照。每 episode 注入 34 份
     task brief（23/34 含 Seed-0 官方 dev 分数表）、289 个 task-specific skills、
     7,231 条 task-specific dev experience、65 个 task-specific 视觉/几何工具、
     34 份离线 demo 视频分析。代码证据：`submission.py:464–515`、
     `store.py:947–984`、`context.py:74–89`。
   - `prompts/priors.json` 的 27 条 task-specific 场景/机制先验，超出官方 Detail
     Description（例如 `play_tic_tac_toe` 的对手触发条件、`make_kong` 的仿真步进
     行为、`match_and_pick_from_conveyor` 的传送带行为、`imitate_sorting_sequence`
     的演示臂重放、23 个任务的固定物体表）。代码证据：`context.py:43–57`、
     `prompts/priors.json`。
   - Agent Track Rules §2/§4 明确禁止：测试前准备的 task-specific prompts、
     memory、action programs、scoring information；task identity 不得选择
     workflow/memory/code path/action trajectory。
6. **单 seed**：PR #204 自报 42 tasks × 50 episodes = 2,100 episodes，seed 1 only，
   进度 `33.3% † (42/126)`；Avg SR 78.43% / Score 83.75；分维度 Gen 73.83/79.97、
   Precision 72.50/75.83、LH 75.25/86.36、Memory 96.33/97.45、Open 74.25/79.12。
   榜单的 83.94/79.33 与 PR 的 83.75/78.43 不完全一致，维度值也不同（例如 LH
   score 87.09 vs 86.36），没有公开说明。
7. **代价**：PR 自报 162-episode 样本：episode 中位数 34 min（最大 118 min），
   中位 55 次模型调用，约 3M input tokens（91% 命中 cache）、15k output tokens；
   每 episode 记录 0.3–1 GB；6 h episode 上限；基础设施失败 exit 99，最多重试 9 次。
8. **榜单治理**：15 条 manifest 类型含 `agent` 的条目中 11 条带星号；按 agent
   指标排序的前九名全部带星号；最高未带星条目是 WorldScape-R²SI 45.93/37.31。
   bundle 的 `kc()` 对带星号 agent 返回 `null` 排名（未在浏览器中核实最终 UI 渲染）。
9. **归属**：榜单写 Xiaomi Robotics；PR 的 contributor 写 "Mibot-RSI team"；
   GitHub 账号 `ffanyt` 的公开 profile 写 Harbin Institute of Technology，5 个公开
   仓库中没有 Mibot。PR 的 11 个 commit 全部使用
   `ffanyt@users.noreply.github.com` / `96506495+ffanyt@users.noreply.github.com`，
   没有 `@xiaomi.com` 之类企业地址。GitHub 代码搜索 `Mibot_RSI` 只命中一个第三方
   Awesome 列表（9 条），`Mibot-RUA` 0 条；commit 搜索 `Mibot-RSI` 0 条。
   XiaomiRobotics 组织只有 3 个公开仓库（XR-0、XR-1、XR-U0），没有 Mibot-RUA。
   小米 XR-1 官方项目页只写 RoboDojo 13.93（VLA），没有提 agent/Mibot-RUA。
   榜单的 logo 映射使用 `/data/mibot-xiaomi-logo.png`，说明委员会接受的是带小米
   品牌的提交，而不是匿名提交。
   结论：**榜单/委员会把条目归属为 Xiaomi Robotics；公开代码线索无法独立确认
   雇佣、所有权或授权关系。** 可能是小米团队用个人账号提交、小米–哈工大联合团队、
   profile 过期，或榜单误标；公开材料无法区分。

## 限制

- 榜单是 SPA，数据来自 JS bundle 快照；bundle 的 `updated_at` 常量是
  2026-11-18，但 changelog 有 2026-11-26 条目。没有官方 JSON API。
- 没有用浏览器渲染，星号/排名的最终可见形态是读代码推断的。
- 知识库 gated，未下载归档；289/7,231/65/34 等计数来自委员会 findings（B 级）。
- PR 仍 open（head 2026-11-12），之后可能变化；承诺的 practice code 尚未发布
  （榜单 2026-11-26 起三天内，即 2026-11-29 前）。
- 没有运行 RoboDojo / Isaac Sim / GPT-6-Astra；没有独立复现 83.94。

## 关联报告

- [Mibot-RUA on the RoboDojo agent track — what 83.94 / 79.33% actually measures](../../reports/20261127-mibot-rua-robodojo-agent-track.md)
