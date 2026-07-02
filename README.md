# laser-DD-neutron -> Li breeding neutronics

激光驱动 D-D 脉冲中子源 -> 外部锂靶产氚特性的跨尺度模拟方案。当前仓库用于明确科学问题、模块边界、数据契约、验证关卡和小论文执行路线。

**2026-07-03 策略更新**：项目不再以高精度 2D PIC 参数矩阵作为最终可信度核心。当前主线改为 **3D PIC 源锚点 + Stage B 半解析 D-D converter + Stage C OpenMC Li 产氚响应**。已有 2D `L_pre=0` accepted sources 保留用于开发、对照和参数化源区间校准；`L_pre=1` 高精度 2D 扫描暂停，不再盲目重跑。

## 核心问题

激光束-靶产生的畸变谱中子（多普勒展宽 + 前向各向异性），打进锂靶后的 TPR，相对理想各向同性单能 2.45 MeV 源差多少、差在哪？

预期物理图像：差异主要集中在 `7Li(n,n'alpha)T` 阈值窗口（约 >2.82 MeV）和前向角区；`6Li(n,alpha)T` 主通道对源谱细节相对钝感。

## 技术路线

```text
[A] EPOCH 3D PIC anchor       [B] 半解析源项 Python           [C] OpenMC 输运
激光打 CD2 产生 D 束       ->  厚 CD2 converter D-D 源     ->  锂靶 TPR
deuteron_beam.h5              neutron_source.h5              Li6/Li7 分道 + 空间/能量 tally
```

关键设计：Stage B 不用 Geant4，而是用 Python 半解析源项（Bosch-Hale 截面 + 阻止本领 + 两体 boost）生成 D-D 中子源。OpenMC 负责中子输运和锂靶产氚，不负责氘束-靶聚变。

## 当前文档

- [一个月小论文执行框架_激光D-D中子源驱动锂靶产氚.md](一个月小论文执行框架_激光D-D中子源驱动锂靶产氚.md)：面向课题执行的路线、周计划、风险和论文骨架。
- [AGENT交接规格书_激光D-D中子源_锂靶产氚流水线.md](AGENT交接规格书_激光D-D中子源_锂靶产氚流水线.md)：面向代码实现的公式、接口 schema、模块职责、验证关卡和参数建议。
- [docs/PHYSICS_LOCK.md](docs/PHYSICS_LOCK.md)：锁定“薄靶产氘束 + 外置厚 CD2 converter + 锂靶 TPR”的物理几何。
- [docs/COMPUTE_STRATEGY.md](docs/COMPUTE_STRATEGY.md)：本地 M4 Pro 与超算的计算分工、运行顺序和数据传输原则。
- [docs/PROJECT_POSITIONING.md](docs/PROJECT_POSITIONING.md)：项目重新定位、3D 可信度策略和论文主张边界。

## 当前可运行内容

```bash
python3 tests/test_gates.py
python3 moduleA_pic/parametric_beam.py --n 200000 -o deuteron_beam.h5
python3 moduleB_source/build_source.py deuteron_beam.h5 -o neutron_source.h5
python3 moduleA_pic/parametric_scan.py --n 50000
```

说明：当前 Stage B 从 `data/stopping_D_in_CD2.csv` 读取 D-in-CD2 阻止本领。仓库内表格是 provisional PSTAR-style seed，正式产额和论文结果前必须替换为 SRIM/PSTAR 导出的可靠数据。

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
| C | 锂靶 TPR | `6Li` 通道 A≈B，`7Li` 通道差异集中在 >2.82 MeV |
| norm | 归一化 | 每源中子 TPR 与每 shot 绝对产额分开报告，放大因子已除回 |

## 必须核实的占位项

1. `D(d,n)3He` Bosch-Hale 截面绝对值：至少对照 ENDF/B 或 NRL Formulary 两个能量点。
2. D 在 CD2 中的阻止本领：正式结果前使用 SRIM/PSTAR/可靠表格替换占位模型。
3. OpenMC 产氚 score/MT：按实际安装版本确认 `H3-production`、`(n,t)` 或 MT 号。
4. CD2 密度、锂密度、Li6 富集度、靶几何尺寸：按实验或论文设定锁定。

## 诚实边界

- 中子源侧（激光 -> D-D 中子）已有大量前人工作，本文创新点不应写成“搭建了激光中子源”。
- 更合理的卖点是：把激光 D-D 源的谱-角畸变，定量映射到外部锂靶 TPR，并指出偏差集中于 `7Li` 阈值窗口。
- 当前模型只聚焦 D-D 分支；CD2 中 `12C(d,n)`、体相反应、hole-boring 等额外产中子机制需要作为假设边界说明。
- 3D PIC 不做大矩阵；先做 300 fs 微基准校准机时/内存/横向边界，再决定正式 3D source run。
