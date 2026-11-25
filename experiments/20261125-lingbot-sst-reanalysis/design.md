# 实验设计 — LingBot/SST 复算与后续实验

- **日期**：2026-11-25
- **状态**：MVE-0 **已运行**（桌面复算）；MVE-1 与 MVE-2 **未运行**
- **负责人**：J. Cheng（决策），ZCode（分析）
- **相关报告**：`reports/20261125-lingbot-vla-sst-foreground-prompting.md`

## MVE-0 — SST 各阶段增益能否与噪声区分？（已运行）

1. **假设**：在 50 episodes/task 下，中间阶段的 +2–3 pp 在采样噪声内；只有前景
   替换的跳变和等步数的数据修复能通过两比例检验。
2. **基线**：N0→N5 链中的前一阶段；数据修复用 30k 的 N4 作等步数对照。
3. **变量**：阶段（N0…N5）、场景（clean/randomized）。控制：发布计数、同一
   基准、同一评测器。
4. **环境**：无 GPU、无机器人；Python 3.12 标准库；输入是 `data/` 中的派生计数。
5. **指标**：成功率、Wilson 95% CI、两比例 z 检验（乐观：忽略 task 聚类）、
   逐任务差值分布。
6. **验收**：复现发布阶段差值的方向与幅度；只有 p<0.05 才称为“成立”。
7. **失败判据**：计数与发布成功率对不上，或检验与发布方向相反 → 停止并复查输入。
8. **记录**：`analysis.py`、`logs/analysis.txt`、`data/*.csv`、`result.md`。
9. **回退**：不需要（只读桌面分析）。

## MVE-1 — 前景条件对小策略是否有帮助？（未运行）

1. **假设**：在 2 个 RoboTwin 任务上，小 BC 策略 + 指令条件前景变暗，在
   `demo_randomized` 上优于 raw，且不劣于光度域随机化。
2. **基线**：raw 图像；第二对照：仅光度增强。
3. **变量**：输入管线（raw / 前景变暗 / 光度 DR）；控制：策略、数据、seeds、
   训练步数、评测协议。
4. **环境**：RoboTwin 2.0 仿真，2 个任务，每任务 50 条 clean 演示，每任务 100
   trials，固定 seeds；ACT 或 DP3 量级的小策略（约 10–30M 参数），单张消费级
   GPU。**未执行。**
5. **指标**：各场景成功率；相同 seeds 上的配对 McNemar；clean 回退；在线掩码
   延迟（若使用）。
6. **验收**：random 比 raw 高 ≥5 pp 且 p<0.05；clean 回退 ≤2 pp。次级验收：
   前景 ≥ DR（非劣）。
7. **失败判据**：random 无增益；或 clean 回退 >2 pp；或把 mask 改成指令无关后
   增益消失（说明是指令条件，而不是前景本身）。
8. **记录**：固定 seeds、逐 episode CSV、原始 `stats` 文件、配置哈希。
9. **回退**：保留 raw 策略；不引入掩码服务。

**SST 没有做的关键消融**：把指令条件 mask 换成（a）所有指令共用同一 mask，
（b）随机物体 mask。如果（a）仍有增益，就是前景/增强效应；如果增益消失，就是
通过像素实现的指令条件。SST 的 `single` vs `multi` 对比对两种解释都成立。

## MVE-2 — 未来 JCHENG 演示集的数据完整性门禁（未运行）

1. **假设**：任何未来 LeRobot 风格演示集的 10 episode 抽样，都能在训练前发现
   帧/行错位、PTS 违规、首末帧解码失败、padding 未掩。
2. **基线**：交付时的数据集。
3. **变量**：无（只验证）。
4. **环境**：CPU；`ffmpeg`/PyAV；无机器人。
5. **指标**：帧数 ≠ parquet 行数的 episode 数；PTS 违规；解码失败；padding 动作数。
6. **验收**：抽样零 mismatch；所有 padding 位置在 loader 中被掩。
7. **失败判据**：任一 mismatch → 不训练；修复或丢弃该 episode。
8. **记录**：逐 episode JSON + 汇总；检查器放在数据仓库，不放在
   `jcheng-research`。
9. **回退**：不适用（只读检查）。

## MVE-3 — SST checkpoints 的配对重评（阻塞）

如果 SST 发布 checkpoints，用相同 seeds、每任务 100 episodes 重评 30k 的 N4 与
N5，并对配对结果做 McNemar。这是唯一能在逐 episode 层面判定 +3.98 pp 数据修复
增益是否真实的方法。阻塞原因：截至 2026-11-25 checkpoints 未发布。
