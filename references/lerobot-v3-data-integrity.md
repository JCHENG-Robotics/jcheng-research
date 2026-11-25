# LeRobot v3.0 数据完整性 — 外部佐证

- **类型**：issue tracker（二手，但接近一手：维护者/用户复现）
- **访问日期**：2026-11-25
- **阅读范围**：issue 页面通过检索摘要阅读，未逐条打开。按 B 级佐证处理；SST
  的修复代码是针对 RoboTwin 缺陷的 A 级一手证据。

## 已知问题

- **huggingface/lerobot issue #5039** — `lerobot/berkeley_autolab_ur5` v3.0：
  31 个视频文件中有 28 个缺少最后一个 episode；episode 元数据把缺失的 episode
  分配给一个 `from_timestamp`/`to_timestamp` 超出视频末尾的文件。示例错误：
  `Invalid frame index=3839 ... must be less than 3839`；在每个短文件里，缺口
  正好等于分配给该文件的最后一个 episode 的长度。
  <https://github.com/huggingface/lerobot/issues/5039>
- **Good First Issue tracker #5187（DATA-04）** — 同类问题影响 12 个数据集
  （`aloha_mobile_*`、`berkeley_rpt`、`stanford_hydra_dataset`、`taco_play`、
  `toto`、`utaustin_mutex` 等）。根因指向被移除的 converter 代码 commit
  `59d108a80`：在文件滚动时，当前 episode 的元数据被写到旧文件，而下一个文件
  从该 episode 开始。
  <https://github.com/huggingface/lerobot/issues/5187>
- **PR #5051** — 增加加载时检查；issue #2189 是最初的崩溃报告。
- 另一类帧精确切片 bug 记录在 Hebbian-Robotics/hflow commit `720329dc`：在非
  关键帧边界做 stream-copy 切片会丢帧；窗口结束点正好落在帧边界时会把下一个
  episode 的第一帧拉进来（源端时间戳是排他的）；一个语料出现 226 vs 227 个
  access unit。

## 为什么这重要

SST 声称**官方 RoboTwin LeRobot v3.0** 的 episode 末帧会渗到下一个 episode，
而 v2.1 正常。这个具体断言是作者自己的（对其代码/报告为 A），但**这类 bug 在
LeRobot 中有独立记录**。SST 的修复（`tools/rebuild_robotwin_v30_from_v21.py`）
用 v2.1 重建视频，同时保留 v3.0 episode ID 与状态/动作字节；
`data_inputs/preparation_report.json` 记录 2,500 episodes、548,893 帧、250,000
个指令槽，并匹配“exact full chronological state/action float32 bytes and shapes”。

## 对 JCHENG 的相关性

任何未来用 LeRobot（或任何分段视频）组装的模仿数据集，在训练前应带三项检查：
（1）每个 episode 解码帧数等于 parquet 行数；（2）PTS 单调且等于 `i/fps`；
（3）首/末帧解码 + 内容哈希。这些检查便宜，且能抓住已记录的失败类。SST 的
工具是好的参考实现，但它没有许可证（见 `sst-repo-audit.md`）。
