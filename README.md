# laser-DD-neutron -> Li breeding neutronics

激光驱动 D-D 脉冲中子源 -> 外部锂靶产氚特性的跨尺度模拟方案。当前仓库用于明确科学问题、模块边界、数据契约、验证关卡和小论文执行路线。

**2026-07-06 状态更新**：当前主线已经从“准备 3D benchmark”推进到
**已完成 6 ps 3D PIC 源锚点 + 重新规划低成本 2D 参数矩阵 + Stage B/C 源项/输运链路开发**。3D 用来给论文可信度和维度修正提供 anchor；2D 用来做趋势扫描和参数筛选；Stage B/C 负责把 PIC 氘束映射到 D-D 中子源、直接 D-D 氚和锂靶 TPR。

**2026-07-06 计算状态快照**：

- 3D anchor 已接受：`a0=10`、CD2 厚度 `3 um`、源面 `rear+10`、收集到 `6 ps`。
  D-D 产额加权的最后 `250 fs` 窗口占 `0-6 ps` 的 `5.57%`，满足当前 `<10%`
  收敛标准。关键 job：`1837996`。
- 原 `dx=dy=10 nm` 2D 大矩阵因成本过高已止损：保留已完成的
  `a0=10,t=1um` 与 `a0=10,t=2um` 两个 6 ps 点作为分辨率/厚度复核；
  其余慢点在确认 restart dump 后取消，避免继续烧费。
- 新低成本 2D 矩阵已完成：`dx=16 nm, dy=40 nm`，盒子对齐 3D
  `x=-6..26 um, y=-10..10 um`，PPC 对齐 3D `16/32/4`，`64` 核，
  `18 h` 墙时，`t_end=6 ps`。job `1937305`-`1937311` 全部
  `COMPLETED`，总费用约 `92.09 CNY`。
- 2026-07-06 CST 发现隐藏磁盘配额限制，旧大矩阵曾触发
  `Disk quota exceeded`。已清理旧中间 SDF，项目目录从约 `94G`
  降低并保留关键 3D/2D 资产。
- `/publicfs10` 总盘约 `4.1P` 可用，但账号/目录仍可能受隐藏 quota 限制。重要远端目录见
  [hpc/IMPORTANT_RUNS.md](hpc/IMPORTANT_RUNS.md)，未验证完成前不要删除旧 r001
  目录。

**Stage B 更新**：D-D converter 需要分两条产氚账：`D(d,p)T` 在 converter 内直接产氚，`D(d,n)3He` 产生中子后进入 Li 靶再产氚。论文报告应分列 `T_direct_DD` 与 `T_Li_neutron`，必要时再给总和。第二靶 baseline 计划采用 TiD2；CD2 保留为当前代码路径和后续材料敏感性对照。

## 核心问题

激光束-靶产生的畸变谱中子（多普勒展宽 + 前向各向异性），打进锂靶后的 TPR，相对理想各向同性单能 2.45 MeV 源差多少、差在哪？

预期物理图像：差异主要集中在 `7Li` 产氚阈值窗口和前向角区；当前 OpenMC HDF5 核数据中 `Li7` 的 `H3-production` 对应 MT205 `(n,Xt)` 总产氚截面，294 K 阈值为 3.1454 MeV。`6Li(n,alpha)T` 主通道对源谱细节相对钝感。

## 技术路线

```text
[A] EPOCH 3D PIC anchor       [B] 半解析源项 Python              [C] OpenMC 输运
激光打 CD2 产生 D 束       ->  厚 TiD2/CD2 converter D-D 源  ->  中子进锂靶 TPR
deuteron_beam.h5              neutron_source.h5 + direct T     Li6/Li7 分道 + 空间/能量 tally
```

关键设计：Stage B 不用 Geant4，而是用 Python 半解析源项（D-D 截面 + 阻止本领 + 两体 boost）生成 D-D 中子源，并单独统计 `D(d,p)T` 直接氚。OpenMC 负责中子输运和锂靶产氚，不负责初级氘束-靶聚变。

当前 PIC 数据使用原则：

- 3D anchor 是论文主可信度基准，不做昂贵的大矩阵。
- 2D 矩阵用于趋势、优化和参数敏感性；2D 绝对产额需要通过 3D anchor 谨慎解释。
- 低成本矩阵使用 `dx=16 nm, dy=40 nm`；已完成的两个 `dx=dy=10 nm`
  点用于分辨率复核，不再把所有扫描点都按 10 nm 昂贵设置硬跑。
- Stage B 输入采用 `rear+10` 氘束相空间，并使用 D-D 产额加权收敛而不是单纯粒子数收敛。
- 如果使用 restart 续跑点，后处理必须跨 r001/r002 目录合并 probe 数据。

## 当前文档

- [一个月小论文执行框架_激光D-D中子源驱动锂靶产氚.md](一个月小论文执行框架_激光D-D中子源驱动锂靶产氚.md)：面向课题执行的路线、周计划、风险和论文骨架。
- [AGENT交接规格书_激光D-D中子源_锂靶产氚流水线.md](AGENT交接规格书_激光D-D中子源_锂靶产氚流水线.md)：面向代码实现的公式、接口 schema、模块职责、验证关卡和参数建议。
- [docs/PHYSICS_LOCK.md](docs/PHYSICS_LOCK.md)：锁定“薄靶产氘束 + 外置厚 deuteride converter + 锂靶 TPR”的物理几何。
- [docs/STAGE2_DD_CHANNELS.md](docs/STAGE2_DD_CHANNELS.md)：锁定 Stage B 的 D-D 双分支、直接氚统计和 TiD2 baseline 计划。
- [docs/COMPUTE_STRATEGY.md](docs/COMPUTE_STRATEGY.md)：本地 M4 Pro 与超算的计算分工、运行顺序和数据传输原则。
- [docs/PROJECT_POSITIONING.md](docs/PROJECT_POSITIONING.md)：项目重新定位、3D 可信度策略和论文主张边界。
- [hpc/README.md](hpc/README.md)：超算运行策略、墙时保护和远端布局。
- [hpc/IMPORTANT_RUNS.md](hpc/IMPORTANT_RUNS.md)：当前最重要的 3D/2D job、远端目录、不要删除的文件。

## 当前可运行内容

```bash
python3 tests/test_gates.py
python3 moduleA_pic/parametric_beam.py --n 200000 -o deuteron_beam.h5
python3 moduleB_source/build_source.py deuteron_beam.h5 -o neutron_source.h5
python3 moduleA_pic/parametric_scan.py --n 50000
```

说明：当前 Stage B 代码仍从 `data/stopping_D_in_CD2.csv` 读取 D-in-CD2 阻止本领，只实现 CD2 converter 的中子分支，适合软件链路验证和 CD2 对照。正式 TiD2 baseline 前必须加入 D-in-TiD2 阻止本领、TiD2 氘密度，以及 `D(d,p)T` 直接氚分支。

本机 OpenMC 运行记录见 [docs/OPENMC_LOCAL_RUN.md](docs/OPENMC_LOCAL_RUN.md)。机器相关路径放在本地 `.env`，不要提交。

## 建议实现结构

```text
interfaces/schema.py
moduleA_pic/parametric_beam.py
moduleA_pic/extract_epoch.py
moduleB_source/cross_section.py
moduleB_source/stopping.py
moduleB_source/kinematics.py
moduleB_source/thick_target.py
moduleB_source/build_source.py
moduleC_openmc/materials.py
moduleC_openmc/geometry.py
moduleC_openmc/source.py
moduleC_openmc/tallies.py
moduleC_openmc/run.py
moduleC_openmc/postprocess.py
tests/test_gates.py
config.yaml
```

## 验证关卡

| GATE | 内容 | 通过标准 |
|---|---|---|
| env | OpenMC 环境 | 最小固定源算例跑通 |
| sigma | Bosch-Hale 截面 | 对 ENDF/NRL 两点核对数量级和趋势 |
| kin | 两体 boost | `E_d -> 0` 得约 2.45 MeV；1 MeV 前向约 4.14 MeV、后向约 1.76 MeV |
| B | 中子源项 | 能谱有 2.45 MeV 峰和越阈高能尾，角分布前向偏置 |
| C | 锂靶 TPR | `6Li` 通道 A≈B，`7Li` 通道差异集中在 MT205 阈值以上（当前库为 >3.1454 MeV） |
| norm | 归一化 | 每源中子 TPR 与每 shot 绝对产额分开报告，放大因子已除回 |

## 必须核实的占位项

1. `D(d,n)3He` 与 `D(d,p)T` 截面绝对值：至少对照 ENDF/B 或 NRL Formulary 两个能量点。
2. D 在 TiD2 和 CD2 中的阻止本领：正式结果前使用 SRIM/PSTAR/可靠表格替换占位模型。
3. OpenMC 产氚 score/MT：当前已确认 `H3-production` 对 `Li7` 使用 MT205 `(n,Xt)` 总产氚生产截面；论文中按 3.1454 MeV 阈值标图，不写成单一排他反应道。
4. TiD2/CD2 密度、锂密度、Li6 富集度、靶几何尺寸：按实验或论文设定锁定。

## 诚实边界

- 中子源侧（激光 -> D-D 中子）已有大量前人工作，本文创新点不应写成“搭建了激光中子源”。
- 更合理的卖点是：把激光 D-D 源的谱-角畸变，定量映射到外部锂靶 TPR，并指出偏差集中于 `7Li` 阈值窗口。
- 当前 Stage B 实现只聚焦 CD2 的 D(d,n) 中子分支；TiD2 baseline、`D(d,p)T` 直接氚、体相反应、hole-boring 等需要作为实现状态和假设边界说明。
- 3D PIC 已完成一个 6 ps source anchor。后续参数扫描优先依靠 2D 矩阵；如要追加 3D，只做少量验证点或最终最优点复核。
