# VLA 鲁棒性、动作分块与替代策略族

- **类型**：一手论文（摘要；LIBERO-Plus 为检索摘要）与官方仓库
- **访问日期**：2026-11-25
- **阅读范围**：摘要与检索摘要；RTC、SAM2Act、DP3、π0、LIBERO-Plus 的 **PDF
  全文未读**。机制类结论按 B 级处理，数字为作者报告值，未独立核验。

## LIBERO-Plus — VLA 鲁棒性

- Fei, Wang, Shi 等。*LIBERO-Plus: In-depth Robustness Analysis of
  Vision-Language-Action Models*。arXiv:2510.13626，2025。
  <https://arxiv.org/abs/2510.13626>
- 10,030 个任务，覆盖七个扰动维度：物体布局、相机视角、机器人初始状态、语言
  指令、光照、背景纹理、传感器噪声。
- 头条结论：在 LIBERO 上报告 >95% 的模型，在温和扰动下跌到 <30%；相机视角与
  初始状态最致命；模型大量忽略语言；存在轨迹记忆的证据。
- **相关性**：支持“外观/视角偏移是真问题”的前提，同时警告基准高分可能脆弱。
  它还提示：指令条件的视觉提示可能通过把语言注入输入而帮助模型，这是 SST 没有
  单独隔离的假设。

## Real-Time Chunking（RTC）

- Black, Galliker, Levine。*Real-Time Execution of Action Chunking Flow
  Policies*。arXiv:2506.07339，NeurIPS 2025。
  <https://arxiv.org/abs/2506.07339>
- 把实时执行建模为 inpainting：冻结推理期间会执行的前缀，inpaint 其余部分；
  对重叠动作做 soft masking；异步执行；**无需重训**。
- **相关性**：SST 的结论“每个任务有最佳执行长度，但只能选一个全局值（50）”
  是静态折中。RTC 是处理延迟与块边界的标准替代，且不重训；SST 没有测它，尽管
  竞赛允许推理策略。

## SAM2Act — 分割骨干，而不是掩码预处理

- Fang, Grotz, Pumacay 等。*SAM2Act: Integrating Visual Foundation Model with
  a Memory Architecture for Robotic Manipulation*。arXiv:2501.18564，ICML 2025。
  <https://arxiv.org/abs/2501.18564>
- 把 SAM 2 **编码器**作为多视角 transformer 策略的视觉骨干，加记忆库
  （SAM2Act+）；18 个 RLBench 任务平均 86.8%；The Colosseum 扰动下差距 4.3%。
- **相关性**：这是相对于“测试时跑 SAM 3 + 27B judge”的替代方案。它在训练时改变
  一次表示，不增加逐帧分割服务。对 JCHENG 来说，这比 SST 管线更现实，但仍属于
  研究路线。

## DP3 — 3D 扩散策略

- Ze, Zhang, Zhang 等。*3D Diffusion Policy: Generalizable Visuomotor Policy
  Learning via Simple 3D Representations*。arXiv:2403.03954，2024。
  <https://arxiv.org/abs/2403.03954>
- 稀疏点云 + 点编码器 + 扩散策略；72 个仿真任务中多数只需 10 条演示（相对基线
  提升 24.2%）；4 个真机任务、每任务 40 条演示，成功率 85%；在空间、视角、外观、
  实例上泛化。
- **相关性**：对带深度（D435i）的工位最现实的学习型策略替代。它用几何而不是
  外观，因此外观偏移的伤害更小，也不需要 6B VLA 或 27B judge。它仍然需要可靠
  演示与动作标签，而 JCHENG 目前没有。
- **RoboTwin 论文的警示**："DP3's strong results partly stem from perfect point
  clouds and clean background segmentation in simulation." 真实 D435i 点云有空洞、
  噪声和缺失分割，DP3 的仿真优势在投入前应打折。

## π0 — 流匹配 VLA 谱系

- Black, Brown, Driess 等。*π0: A Vision-Language-Action Flow Model for
  General Robot Control*。arXiv:2410.24164，RSS 2025。
  <https://arxiv.org/abs/2410.24164>
- VLM 主干 + 独立流匹配动作专家；跨多个机器人平台训练；可微调新技能。摘要
  **没有**给出 chunk 长度或控制频率，本次未核验。
- **相关性**：LingBot-VLA 2.0 的动作专家与双系统设计属于这一谱系。只作为架构
  背景引用。

## 域随机化

- Tobin, Fong, Ray 等。*Domain Randomization for Transferring Deep Neural
  Networks from Simulation to the Real World*。arXiv:1703.06907，IROS 2017。
  <https://arxiv.org/abs/1703.06907>
- 训练时随机化渲染，让真实世界看起来只是另一种变化；仅用仿真 RGB 训练检测器，
  迁移到真实定位（1.5 cm）与杂乱场景抓取。
- **相关性**：clean+randomized 的 RoboTwin 配方是直接应用。如果项目能生成或
  采集多样数据，这是主导杠杆，而且比测试时掩码简单。
