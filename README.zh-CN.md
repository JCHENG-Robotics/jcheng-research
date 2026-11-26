# jcheng-research

**简体中文** | [English](README.md)

**JCHENG 生态的调研工作区。** 面向 ArmPi Ultra 平台的文献调研、技术选型、根因分析与
预注册实验设计。本仓库产出**报告与决策，而不是运行时代码**：本目录中的任何内容都
不会被机器人导入、部署或执行。

> 状态：**Experimental** — v0.1.0，2026-11-25。仓库当前只包含调研规范、报告模板和
> 产出目录约定；**尚无已完成的调研**，因此不构成任何技术结论。仓库为公开，且不在
> 运行时依赖图中。
> 本文为英文主文档的中文对照；如有歧义，以英文版为准。

---

## 1. 为什么需要这个仓库

生态里的调研工作与代码有相同的失效模式：结论被引用却没有来源，mock 结果被记成
硬件结果，论文摘要被当成实验评估，"已验证"失去对应的命令和日期。本仓库用流程
替代记忆：

- **[AGENTS.md](AGENTS.md)** 是调研规范（本仓库内生效）：一手来源、论文与仓库
  审查、批判性比较、项目适配、最小可行实验、S–D 证据分级、报告提纲。
- **[templates/research-report.md](templates/research-report.md)** 是规范推导出的
  固定 13 节报告骨架。
- **`reports/`、`experiments/`、`references/`** 把三类产物（结论、执行、来源）
  分开存放，各自可追溯。

该规范**仅在本仓库内适用**。日常代码、构建与部署遵循生态根目录 `AGENTS.md` 和
各产品仓库自身的规则。

## 2. 范围与边界

| 项 | 本仓库 |
|---|---|
| 层级 | **Research** — 在 L0–L4 与 OPS 之外；没有运行时仓库依赖它 |
| 输入 | 生态各仓库及其证据、公开文献、Owner 提出的问题 |
| 输出 | `reports/*.md`、`experiments/*/`、`references/<主题>/*.md` |
| 在机器人上执行 | 否 |
| 硬件访问 | `none` — 不访问设备、DDS、串口、相机或总线 |
| 运行时依赖 | 双向都无；产品仓库不得从本仓库导入 |
| 禁止 | 运动指令；参与 DDS；复制厂商源码或固件；模型权重、录包或原始视频；密钥；私有计划内容（`MASTER_PLAN_V3_PRIVATE.md`） |
| 结论效力 | 无。报告可以建议决策，但不能替其他仓库接受硬件结论 |

## 3. 目录结构

```text
jcheng-research/
├── AGENTS.md                  # 调研规范（本仓库内生效）
├── README.md / README.zh-CN.md
├── ROADMAP.md                 # 里程碑与退出条件
├── CHANGELOG.md               # Keep a Changelog 1.1.0
├── ACCEPTANCE.md              # 本仓库已验证的内容（目前仅 L0）
├── LICENSE-REVIEW.md          # 许可证审查未关闭前的状态
├── VERSION
├── templates/
│   └── research-report.md     # 13 节报告骨架
├── reports/                   # 每次调研一份报告（索引：reports/README.md）
├── experiments/               # 每个最小可行实验一个目录
├── references/                # 按主题归档的来源记录（索引：references/README.md）
│   ├── system/                # jcheng-system：安全、仲裁、运动
│   ├── perception/            # jcheng-perception：视觉、深度/TF、融合
│   ├── mobile/                # jcheng-mobile：LiDAR、SLAM、Nav2
│   ├── ops/                   # jcheng-ops：探针、看门狗、自愈
│   ├── manipulation/          # jcheng-manipulation：VLA、抓取、机械臂
│   │   └── papers/            # 本地 PDF 副本
│   └── datasets-benchmarks/   # 跨仓库：数据集、基准、赛事规则
├── scripts/
│   └── check_repo_gate.sh     # 本地与 CI 共用的门禁
└── .github/workflows/ci.yml   # research-gate
```

## 4. 环境要求

- `bash`、`git`、`grep`、`find` — 门禁是唯一的可执行产物。
- 可选：`python3`，用于 `experiments/<id>/` 内的分析脚本或 notebook。
- 本仓库不需要 ROS、GPU 或机器人访问权限。

## 5. 快速开始

```bash
git clone git@github.com:JCHENG-Robotics/jcheng-research.git
cd jcheng-research
bash scripts/check_repo_gate.sh     # 必须输出 "Repository gate OK"
```

开始一次调研：

```bash
cp templates/research-report.md reports/$(date +%Y%m%d)-<slug>.md
mkdir -p experiments/$(date +%Y%m%d)-<slug>/{data,logs}
```

## 6. 产出约定

**报告** — `reports/YYYYMMDD-<slug>.md`，每次调研一份。按主题的索引见
[reports/README.md](reports/README.md)；文件名保持平铺与日期前缀。

1. 从模板开始，保持 13 节顺序。
2. 每条关键结论标注证据等级：**S** 在本系统完成可复现实测，**A** 直接的一手
   来源或源码，**B** 可信但间接，**C** 合理推断，**D** 未经验证的假设。
3. 每个外部主张都给出链接；来源同时登记在 `references/`，记录 URL/DOI、版本或
   commit SHA、访问日期。
4. 失败的边界保持失败。合成、mock、回放结果不得写成硬件验证；未执行的实验不得
   描述为已完成。
5. 工具、权限、时间或资料受限时，必须写明研究边界。

**实验** — `experiments/YYYYMMDD-<slug>/`，包含 `design.md`（假设、Baseline、
自变量与控制变量、环境、指标、验收与失败判据、记录方式、回退策略）、`data/`、
`logs/`，执行后补 `result.md`。

**来源** — `references/<主题>/<slug>.md`，一组来源一个文件，记录 DOI 或 URL、
版本、发表或提交日期，以及实际阅读范围（全文、仅摘要、指定 SHA 的代码）。
访问受限时如实记录。主题与产品仓库一一对应：`system/`、`perception/`、
`mobile/`、`ops/`、`manipulation/`，另有跨仓库的 `datasets-benchmarks/`。按
主要使用方归档；被多个主题使用时只保留一份，并在其他主题 README 中交叉链接。
本地 PDF 副本放在 `references/<主题>/papers/YYYYMMDD-<slug>.pdf`，需核对许可
并受 5 MB 门禁约束。索引与归档规则见
[references/README.md](references/README.md)。

**永不入库**：原始录制数据、模型权重、厂商源码或固件、第三方保密材料、密钥、
私有计划内容。

## 7. 验证状态

| 结论 | 状态 | 证据 |
|---|---|---|
| 必需的文档集、规范、模板与产出目录齐备 | Verified（L0，2026-11-25） | `scripts/check_repo_gate.sh`、CI `research-gate` |
| 未跟踪密钥、模型权重、录制数据或 > 5 MB 的文件 | Verified（L0，2026-11-25） | 同一门禁 |
| 任何调研结论 | 草案已产出，未经评审（2026-11-25） | [报告](reports/20261125-lingbot-vla-sst-foreground-prompting.md) |

本仓库没有硬件通路，因此不可能产生 L1–L5 结果。细节与限制见
[ACCEPTANCE.md](ACCEPTANCE.md)。

## 8. 相关仓库

| 仓库 | 关系 |
|---|---|
| [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) | 契约权威；报告可引用其哈希 |
| [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) | 特权运行时；唯一的运动入口 |
| [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) | L3 感知 |
| [`jcheng-mobile`](https://github.com/JCHENG-Robotics/jcheng-mobile) | L3 移动底盘 |
| [`jcheng-ops`](https://github.com/JCHENG-Robotics/jcheng-ops) | 运维与恢复 |
| [`jcheng-manipulation`](https://github.com/JerichoCheng/jcheng-manipulation) | 冻结的 v1.0.0 基线与设计记录 |
| [`JCHENG-Robotics/.github`](https://github.com/JCHENG-Robotics/.github) | 治理、文档标准、仓库分类 |

本仓库为公开仓库，已列入仓库分类（RESEARCH），但仍不在运行时依赖图中。

## 9. 许可证

许可证审查尚未完成。本仓库没有 `LICENSE`，保留所有权利；见
[LICENSE-REVIEW.md](LICENSE-REVIEW.md)。
