# 计算分工与执行路线

本文档只记录策略和命令模板，不保存任何账号、密码、token 或私有路径。

## 2026-07-03 Strategy Reset

当前策略大改：**3D PIC 是真实性锚点，2D PIC 不再承担最终可信度核心**。

立即执行顺序：

```text
1. 3D resource-controlled deck 50 fs smoke
   -> 校准解析、MPI 拓扑、内存、probe/dist_fn 输出
2. 3D 单点四探针 benchmark，优先 a0=10
   -> rear+5/10/15/20 um D probes, t_end=1500 fs first benchmark
3. Stage B: 3D D source -> thick TiD2/CD2 D-D neutron_source.h5 + direct T
4. Stage C: OpenMC Case A/B, Li6/Li7 分道, per-source-neutron
5. 2D accepted L_pre=0 源只作为开发/对照/参数化区间锚点
```

暂停事项：

- 不再重跑高精度 `L_pre=1` 2D 矩阵，除非 Stage B/C 结果证明预等离子体是必须变量。
- 不再盲目做 2D 大矩阵；任何 PIC 生产 run 必须先有 ETA 或微基准，并显式指定 walltime。
- 3D 不做全扫描。先做一个可信单点，再决定是否加 `a0=5/20`。

## 总原则

本地 M4 Pro 负责开发、半解析源项、OpenMC 调试和后处理；超算负责 EPOCH PIC 生产运行。

| 任务 | 建议位置 | 说明 |
|---|---|---|
| HDF5 schema、参数化氘束、D-D 半解析源项 | 本地 | Python 任务，M4 Pro 足够 |
| OpenMC 小/中统计调试 | 本地 | 固定源、简单锂靶几何先在本地跑通 |
| OpenMC 高统计或细 mesh | 本地优先，必要时超算 | 先用 `1e5-1e6` 粒子，慢了再上超算 |
| EPOCH 2D3V accepted L0 源 | 超算，已完成 | 开发/对照/参数化区间锚点 |
| EPOCH 3D compact source | 超算 | 当前真实性主线；先微基准再正式源 |

## 第一阶段：本地先把链路通电

目标：不用等 PIC，先用参数化 TNSA 氘束跑通 `deuteron_beam.h5 -> neutron_source.h5`。

```bash
python3 tests/test_gates.py
python3 moduleA_pic/parametric_beam.py --n 200000 -o deuteron_beam.h5
python3 moduleB_source/build_source.py deuteron_beam.h5 -o neutron_source.h5
```

当前 `moduleB_source/thick_target.py` 使用 CD2 占位阻止本领并只输出中子分支，只能用于软件链路验证。正式 baseline 前必须加入 TiD2 阻止本领、TiD2 氘密度和 `D(d,p)T` 直接氚分支。

## 第二阶段：本地 OpenMC

先做最小锂靶固定源：

- Case A：各向同性单能 2.45 MeV。
- Case B：读取 `neutron_source.h5`，按角度 bin 保留能量-角度相关。
- tally：总 TPR、`Li6`/`Li7` 分道、能量分辨、空间 mesh。

调试推荐：

```text
particles = 1e5
batches = 20
```

生产推荐：

```text
particles = 1e6-1e7
batches = 50-100
```

## 第三阶段：超算 EPOCH 3D Anchor

当前 3D anchor 模板：

```text
smoke template = hpc/templates/epoch3d_stage1_benchmark_3um_512_smoke.deck
full template  = hpc/templates/epoch3d_stage1_benchmark_3um_512_full.deck
a0 = 10 first
target = 3 um CD2
probe planes = rear+5/10/15/20 um
t_end = 50 fs smoke, then 1500 fs benchmark if smoke passes
dx = 16 nm, dy = dz = 80 nm
```

提交正式 benchmark 前必须先跑 50 fs smoke，检查：

```text
wall-clock / step
内存和 scratch
输出策略是否避免大型 restart
氘束 probe/dist_fn 是否正常写出
probe/dist_fn 输出是否正常
```

旧的 2D 扫描矩阵保留为历史和对照：

```bash
python3 scripts/make_pic_scan_manifest.py
```

输出见 `hpc/pic_first_2d_scan.csv`。

PIC 只追求导出穿过源面的氘束相空间：

```text
E, dir, weight, t -> deuteron_beam.h5
```

大的 SDF 留在超算，本地只拉回：

```text
deuteron_beam.h5
summary.json
metrics.json
少量 PNG/SVG 图
```

## 第四阶段：真实 PIC 源替换参数化源

把 EPOCH 导出的 `deuteron_beam.h5` 放入本地链路：

```bash
python3 moduleB_source/build_source.py deuteron_beam.h5 -o neutron_source.h5
```

然后重跑 OpenMC Case B，与 Case A 对比。后续 Stage B 完整版还要同时导出/统计
`T_direct_DD`，它不进入 OpenMC，只在最终产氚账中与 `T_Li_neutron` 分列。

## 论文主线

不要把论文写成“我耦合了 PIC 和 OpenMC”。主线应是：

```text
激光 D-D 源的谱-角畸变
-> 前向高能尾越过 7Li 阈值
-> 外部锂靶 TPR 的分道、空间、能量响应发生可量化偏差
```

最关键的判断：

- `6Li` 通道应对源谱细节相对钝感。
- `7Li` 通道应对 >2.82 MeV 的前向高能尾敏感。
- A/B 对比优先用“每源中子 TPR”，避免总产额归一化掩盖谱形效应。

## OpenMC API 依据

按 OpenMC stable 文档实现 Stage C：

- `EnergyFilter` 的能量边界使用 eV。
- `H3-production` 属于 particle production score，可用于产氚 tally。
- 多个外源可通过 `Settings.source = [IndependentSource, ...]` 设置，并用 `strength` 表示相对源强。
- `PolarAzimuthal` 可用 `mu` 和 `phi` 分布指定相对于 +z 的角分布。
