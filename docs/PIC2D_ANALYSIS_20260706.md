# 2D full-chain analysis, 2026-07-06

本文件总结当前完成的 2D 参数矩阵结果。它的定位是：用低成本 2D
扫描找趋势、找候选最优点、支撑后续只补少量 3D 验证。不要把这里的
2D 绝对产额直接写成最终物理产额。

## Data scope

PIC 设置：

- EPOCH 2D3V，`x=-6..26 um`，`y=-10..10 um`。
- 网格 `2000 x 500`，`dx=16 nm`，`dy=40 nm`。
- PPC `electron/deuteron/carbon = 16/32/4`，与当前 3D anchor 对齐。
- 主源面 `rear+10`，收集 `0-6 ps`。
- Stage B 输入门槛 `E_D > 0.4 MeV`。
- 七个点：固定 `t=3um` 扫 `a0={5,10,15,20}`；固定 `a0=10` 扫
  `t={1,2,3,4}um`。

Stage B/C 设置：

- 当前 Stage B 是 CD2 thick-converter 的 `D(d,n)3He` 中子分支。
- 当前论文范围收窄为每源中子 Li-TPR 保真度；直接 `D(d,p)T` 产氚分支和
  TiD2 converter 都列为未来工作。
- `T/shot` 只作为诊断归一化；最终绝对产额必须等 D-D 截面核验和真实
  D-in-CD2 阻止本领表替换后再写。
- Stage C 用 OpenMC 0.15.0 计算锂靶中 `Li6`/`Li7` 分道产氚。
- OpenMC 统计：`20 batches x 50,000 particles`，8 threads。
- 核数据：本地 ENDF/B-VII.1 HDF5。
- `Li7` 使用 OpenMC `H3-production`，即 MT205 `(n,Xt)` 总产氚 score；
  在本能区基本由阈值附近的 `7Li(n,n' t)` 主导，但论文文字应写成
  “总产氚 score”，不要写成只 tally 单一排他道。

核心产物：

- 总览图：
  `hpc/results/full_chain_20260706/pic2d_full_chain_analysis_dashboard.png`
- 论文表：
  `hpc/results/full_chain_20260706/pic2d_paper_summary.csv`
- Markdown 表：
  `hpc/results/full_chain_20260706/pic2d_analysis_tables.md`

## Time convergence

这一轮 2D 不是按“最后一窗粒子数”判断，而是按 D-D 产额加权判断。
所有点在 `rear+10`、`E_D>0.4 MeV` 下，最后一个 `250 fs` 时间窗对
`0-6 ps` 累计 D-D 源强的贡献均小于 `0.2%`，远低于当前 `<10%`
停止标准。因此对 2D 参数趋势来说，`6 ps` 已经足够。

这点很重要：冷的、晚到的 D 粒子数量可能不少，但它们对 D-D thick-target
中子产额贡献很小。我们后续写论文时应强调“yield-weighted convergence”，
不是 raw-particle convergence。

## Main trends

### a0 scan at thickness = 3 um

以 `a0=10,t=3um` 为 baseline：

| point | D Emax MeV | DD n/shot | natural Li T/shot | relative total T | Li7 fraction |
|---|---:|---:|---:|---:|---:|
| `a0=5,t=3um` | `2.00` | `7.51e12` | `8.25e10` | `0.928` | `0.041` |
| `a0=10,t=3um` | `2.16` | `8.06e12` | `8.89e10` | `1.000` | `0.045` |
| `a0=15,t=3um` | `7.39` | `1.08e13` | `1.30e11` | `1.456` | `0.127` |
| `a0=20,t=3um` | `19.14` | `1.82e13` | `3.44e11` | `3.863` | `0.465` |

解释：

- `a0=5` 到 `a0=10` 的提升很弱，说明在当前 2D 设置中，低到中等强度下
  主要受可用 D 束权重和低能谱控制。
- `a0=15` 开始出现明显高能尾，`Li7` 分量明显上升。
- `a0=20` 同时提高 D-D 中子数和超过 `7Li` 阈值的中子比例，使自然锂总
  T/shot 达到 baseline 的 `3.86x`。这是当前最适合补 3D 的候选点，
  因为它最能检验“激光 D-D 源谱角畸变影响 Li7 阈值产氚”这个主问题。

### thickness scan at a0 = 10

以 `a0=10,t=3um` 为 baseline：

| point | DD n/shot | mean n MeV | frac n >3.145 MeV | natural Li T/shot | relative total T | Li7 fraction |
|---|---:|---:|---:|---:|---:|---:|
| `t=1um` | `3.96e11` | `3.076` | `0.348` | `7.48e9` | `0.084` | `0.460` |
| `t=2um` | `1.37e12` | `2.682` | `0.179` | `1.50e10` | `0.168` | `0.025` |
| `t=3um` | `8.06e12` | `2.756` | `0.256` | `8.89e10` | `1.000` | `0.045` |
| `t=4um` | `2.45e13` | `2.857` | `0.329` | `2.90e11` | `3.265` | `0.122` |

解释：

- `t=1um` 总量很小，但谱更硬，所以 `Li7` 占比高；这不是好源强点，
  但说明薄靶可以改变阈值通道权重。
- `t=4um` 在当前 2D 设置下给出最大总 D-D 中子数，因此自然锂总
  T/shot 是 baseline 的 `3.27x`。
- 如果目标是“总产氚最大化”，`a0=10,t=4um` 值得关注；如果目标是论文
  主线中的 `Li7` 阈值敏感性和高能尾，`a0=20,t=3um` 更有解释力。

## Lithium enrichment

`Li6=90%` 会显著抬高总 TPR，通常比自然锂高约 `10x`。但它也会把
产氚几乎全部压到 `Li6` 通道，`Li7` 对总产氚的贡献降到约 `0.01%-0.8%`。

所以两种锂靶对应两种论文叙事：

- 自然锂：更适合讨论源谱高能尾和 `Li7` 阈值通道。
- 高富集 `Li6`：更适合讨论工程上总 TPR 的增益，但会弱化 `Li7` 谱敏感性。

## Current best candidates

我建议按两个目标并列保留候选：

1. `a0=20,t=3um`：优先 3D 验证点。理由是自然锂每源中子 `Li7`
   阈值贡献最强，同时诊断性 T/shot 也最高或接近最高，
   且 `Li7` 分量最强，最贴合本文“非理想 D-D 中子谱影响锂靶产氚”的物理故事。
2. `a0=10,t=4um`：总源强/总产氚优化候选。理由是固定 `a0=10` 时总
   D-D 中子数最大，成本和激光强度解释更温和。

如果只能补一个 3D，我更倾向于 `a0=20,t=3um`。如果后续还有资源，可以再补
`a0=10,t=4um` 作为“总产额优化”的对照。

## Limitations

当前 2D 结果可以用于趋势，不足以单独支撑最终绝对产额：

- 2D 会改变横向扩展、电子热输运和鞘场几何，不能替代 3D 绝对标定。
- `16x40nm` 是成本可控的趋势矩阵，不是严格网格收敛结果。
- 两个旧 `10nm` 点改变了盒子和 PPC，只能作为数值敏感性提醒，不是严格
  同条件收敛测试。
- Stage B 当前仍是 CD2 converter 的中子分支。TiD2 和 `D(d,p)T`
  直接氚分支已经从当前论文承诺移到未来工作。
- `D(d,n)3He` 截面已通过 Bosch-Hale 逐点核对；D-in-CD2 阻止本领已从旧
  占位表替换为 NIST PSTAR 同速实体表。旧 full-chain 每 shot 绝对值仍需
  用新表重算；严格 SRIM 表仍未闭合。因此稳健结论仍优先写成
  per-source-neutron TPR/n。
- 当前 3D 粒子源因缺少 `0020` 窗口，不能直接形成严格完整的 `0-6 ps`
  3D `deuteron_beam.h5`。后续应补一个干净 3D 验证点，而不是用缺窗归一化
  做最终论文结果。

## Next action

短期：

1. 用本报告中的 2D 排名决定 3D 补点。
2. 先把论文图框架搭起来：2D dashboard、自然锂分道表、富集锂对照表。
3. 用新 NIST PSTAR 阻止本领重跑 Stage B/C 的最终表；如果要写
   SRIM 级别结论，再补 SRIM D-in-CD2 导出表对比。

中期：

1. 对最终候选点做一个同盒子、同 PPC、只改变网格的 2D 分辨率复核。
2. 跑一个干净 3D 验证点，优先 `a0=20,t=3um`。
3. 未来若要扩大范围，再补 TiD2 材料模型和 `D(d,p)T` 直接氚分支。
4. 用 3D/2D 比值给 2D 扫描趋势一个谨慎的维度修正，而不是宣称 2D
   绝对产额等同真实三维。
