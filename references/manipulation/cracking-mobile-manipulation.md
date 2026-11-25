# 长程移动操作的失败诊断与 agentic 干预 — Cracking Mobile Manipulation: From Failure Diagnosis to Agentic Robot System

- **类型**：一手论文（arXiv 预印本，30 页全文，含附录 A–L）
- **访问日期**：2026-11-25
- **阅读范围**：全文 30 页；正文 §1–§6（pp.1–11）、附录 A–L（pp.18–30）；
  Table 1–18、Figure 1–11。
- **本地副本**：`/home/jerichocheng/文档/JCHENG_Robotics_Papers/07_Cracking_Mobile_Manipulation.pdf`
  （30 页，9,495,096 字节）。**未入库**：第三方预印本 + 5 MB 门禁。
- **许可**：CC BY 4.0（arXiv 摘要页）。

## 来源

- Wang, Z.; Li, J.-N.; Tang, Y.; Yu, Y.; Wu, B.; Fang, M.; Li, X.; Zhong, Y.
  *Cracking Mobile Manipulation: From Failure Diagnosis to Agentic Robot
  System*. arXiv:2610.19600v1 [cs.RO], 2026-10-14.
  <https://arxiv.org/abs/2610.19600>
- 代码仓库：<https://github.com/PKU-VaLuE-Lab/Cracking-Mobile-Manipulation>
  @ `2702ab119840`（Apache-2.0）。**仓库只有论文 PDF、README、LICENSE 和
  3 张图；README 的 Release 清单全部是未勾选的 “Coming soon”**（2026-11-25）。
  即“论文称将发布”，实际**未发布**。
- 数据：RoboCasa365、BEHAVIOR-1K 为公开 benchmark；评测 episode seed 列表
  未发布。

## 论文声称的核心结果（作者报告值，未独立复现）

- 同一个子任务 VLA：原子任务 **80%**，组合成长程移动操作只有 **19%**。
- 20 个 RoboCasa365 移动操作任务（91 个子任务，均值 4.55）；失败归因：
  任务规划 21.0%、导航/底盘位姿 25.9%、局部操作 53.1%（Fig.2）。
- 开发集 100 episodes：**19.0%→47.0%**；held-out 100 episodes：
  **18.0%→49.0%**。
- 最强端到端对照 **Xiaomi Robotics 1：44.0%（dev）/45.0%（held-out）**；
  本文 47.0/49.0，仅高 **+3/+4 pp**（Table 1）。
- BEHAVIOR-1K：14%→37%；真机（Astribot-S1，2 任务×10 trials）：
  **5/20→13/20**。
- 渐进集成：19→25→29→40→47；留一消融：−base 35.0（p=0.004）、
  −demo 39.0（p=0.057）、−memory 41.0（p=0.146）、−EEF 40.0（p=0.092）。
  **只有 base adjustment 稳定显著**。
- 0.8^H 独立子任务参考：20 任务平均 **41.0%**；全系统 47.0% 只高 6 pp。

## 方法要点

- **四个干预**（底层 VLA 冻结）：
  1. 技能库：用 Gemini 3.5 Flash 从训练集演示生成 skill card，评测前冻结；
  2. 自适应视觉记忆：缓存最多 256 帧，Qwen3.8-27B 排序返回 top-16；
  3. 可达性检查 + 底盘调整：Grounding DINO + SAM 掩码 → 深度反投影；
     d≤0.75 m 可达、0.75–1.0 m 临界、>1.0 m 不可达；临界做 ≤0.25 m
     局部平移，不可达用 A* 选新站位；
  4. 末端调整：掩码内 3D 点中位数 + 表面法向，单次平移 ≤0.30 m。
- **子任务 VLA**：Qwen3-VL-4B + DINOv2 ViT-S/14 + DiT-B 动作头；
  3×224×224 RGB + 16 维状态；12 维动作、50 步 chunk；200k steps、
  batch 256、单种子 42。
- **高层规划器**：Kimi K3（论文只给名称）；另有 Gemini 3.5 Flash、
  Qwen3.8-27B。**token 数、调用次数、延迟、费用全部未报告。**
- 一次 VLA 调用执行 350 个控制步后交回规划器；未报告端到端墙钟时间。

## 批判性评估

### 叙事与数字

- **“19→47→49”不是同一条曲线**：47% 在开发 seed（baseline 19%），49% 在
  held-out seed（baseline 18%）。两个分母不同，摘要并置成递进容易误读。
- **相对“独立子任务组合”只高 6 pp**：用作者自己的 0.8^H 参考，20 任务
  平均应有 41.0%；全系统 47.0%。5–15 子任务组 34.3% vs 参考 25.0%。
  这套系统大致做到“和它的零件一样好、没有额外复合崩溃”，而不是“破解了”
  长程移动操作。
- **最强端到端几乎追平**：Xiaomi Robotics 1 在 held-out 是 45.0% vs 49.0%
  （+4 pp，无 CI、无配对检验）。摘要/结论没有提这一点；若把“统一扩
  scaling 无效”作为核心论点，这个对照是反证而非佐证。
- **baseline 是作者改造版**：Harness VLA 被“移除仿真专用工具”，
  CaP-X/Pigey 为复现；工具集、prompt、retry 预算的具体值未报告。19% 这个
  分母的稳健性未知。

### 统计

- **单训练种子 42**，没有多训练种子方差；所有对照是同一 100 个配对 episode。
  held-out 只是换 5 个评估 seed，不是换任务、不是重训。
- 配对 McNemar + 分层 bootstrap 的实现可信（本评审用其 n01/n10 反算与论文
  一致），但单组件显著性不足：memory/EEF/demo 的 p 多在 0.057–0.344。
- 真机 2 任务×10 trials、单机单操作员、无随机化顺序、无盲评；13/20 vs
  5/20 的 Fisher 精确检验约 p≈0.011（本评审计算，C 级），但 n=20 下一条
  trial 翻转就改变结论。演示数 500 vs 300 也不对等。

### 失败诊断

- 失败归因采用“三次重规划内可恢复则不计”，并把主因判给**最早未解决**的
  错误；该规则会把晚期错误系统性算到早期阶段头上。作者用转移表部分承认
  幸存者效应，但 53.1% 这个“操作是主因”的数字仍受规则影响。
- 细粒度标注一致性较好：30 例子集 3 人一致 26/30、Fleiss κ=0.86；
  细粒度 24/30、κ=0.79。这是全文最扎实的部分。

### 成本与部署

- 规划器依赖 Kimi K3、Gemini 3.5 Flash、Qwen3.8-27B 三个外部服务；
  任一版本漂移都不可复现。论文没有 token/金额/延迟数据，无法判断能否
  上机器人。
- 可达性检查**不校验关节限位、IK、整机碰撞**；末端修正单次 0.30 m。
  在无编码器、无 e-stop 的 ArmPi 上，这正是最危险的失效模式。

## 代码与数据

- 仓库公开但**无代码**（只有 PDF/图片）；无 checkpoint、无 prompt 全文、
  无 episode seed 列表。复现结论：**不可复现**。
- 数据：RoboCasa365 / BEHAVIOR-1K 公开；HIW-500 公开；但评测 seed 未发布。

## 与 JCHENG / ArmPi Ultra 的适配

- **形态差异大**：Astribot-S1 是轮式双臂 + 平行夹爪；ArmPi 是 5-DoF 单臂。
  “底盘位姿决定可达工作空间”的结论仍成立，但 `approach_xy`/`goto_stance`
  是为可平移底盘设计的，ArmPi 若底盘可动也需重新定义 intent。
- **算力**：Kimi K3/Qwen3.8-27B 不可能本地部署，6 GB 更放不下；
  Grounding DINO + SAM 在 3060 上可跑但帧率低。agentic 层只能作为云端
  方案，不能进入安全闭环。
- **运动接口**：论文让 agent 直接下发底盘平移与末端修正；在 JCHENG 必须
  经 `ExecuteMotion`，并新增“底盘微调”“站位重规划”两类受控 intent。
- **可借鉴（低成本）**：失败分类框架、配对 McNemar + 分层 bootstrap 的
  统计口径、可达性门控（目标距离分档，超限先调位姿）。可达性门控是消融中
  唯一稳定显著项（p=0.004/0.013）。

## 结论

| # | 结论 | 证据等级 | 处置 |
|---|---|---|---|
| 1 | “先诊断失败分布、再在瓶颈处干预”应作为评测协议 | B（单 benchmark、配对统计、单种子） | **采纳**为流程，不采纳其系统 |
| 2 | 操作前做可达性门控（距离分档，超限先调位姿） | B（唯一稳定显著项） | **采纳**为纯几何检查 |
| 3 | 配对 McNemar + 分层 bootstrap、同 episode 集对照 | B（方法可复用） | **采纳**为小样本实验默认统计 |
| 4 | 规划器触发的视觉记忆优于每步灌历史帧 | C（p=0.09–0.27，多数不显著） | **仅借鉴**，不引入 27B 模型 |
| 5 | 视频演示→技能卡做规划引导 | C（p=0.057–0.109） | **不采纳**（无演示数据/无 VLA） |
| 6 | 用超大规模云端 VLM 做闭环规划 | D（无成本/延迟数据） | **不采纳**（与无 e-stop 平台不兼容） |
| 7 | 代码/checkpoint/prompt 未发布 | A（仓库 tree/README） | **不采纳**为可复现证据 |

## 核验片段

1. “a pretrained subtask VLA achieves 80% success rate on atomic manipulation tasks but only 19% when these skills are composed” — Abstract, p.1
2. “from 19% to 47%, with the finalized system reaching 49% on held-out episode seeds, compared with 18% for the baseline” — Abstract, p.1
3. “Pigey and our Harness VLA adaptation use the same subtask VLA checkpoint as our method” — §5.3, p.9
4. “Our full system also achieves performance comparable to the strongest end-to-end VLA baseline, Xiaomi Robotics 1” — §5.3, p.9
5. “Base adjustment yields the largest incremental improvement … 29.0% to 40.0%” — §5.2, p.7
6. “Removing base adjustment produces the largest observed drop, from 47.0% to 35.0%” — App K, p.27
7. “the full system completes 13 of 20 trials, compared with 5 of 20 for the agentic baseline” — §5.3, p.9
8. “Each VLA call executes for 350 control steps before returning control to the planner.” — App B.1, p.18
9. “Averaging over the 20 tasks gives 41.0%.” — App H, p.25
10. “Code coming soon” / all release items unchecked — repository README, `main` @ `2702ab119840`

## 对本仓库的意义

用于 [10 篇论文批次评估](../../reports/20261125-paper-batch-mobile-manipulation.md)
与 MVE-0（失败分类桌面研究）。结论：**不引入 agentic 运行时**；采纳其
失败诊断协议、可达性门控与配对统计口径。
