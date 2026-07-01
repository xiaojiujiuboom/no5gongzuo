# 计算分工与执行路线

本文档只记录策略和命令模板，不保存任何账号、密码、token 或私有路径。

## 总原则

本地 M4 Pro 负责开发、半解析源项、OpenMC 调试和后处理；超算负责 EPOCH PIC 生产运行。

| 任务 | 建议位置 | 说明 |
|---|---|---|
| HDF5 schema、参数化氘束、D-D 半解析源项 | 本地 | Python 任务，M4 Pro 足够 |
| OpenMC 小/中统计调试 | 本地 | 固定源、简单锂靶几何先在本地跑通 |
| OpenMC 高统计或细 mesh | 本地优先，必要时超算 | 先用 `1e5-1e6` 粒子，慢了再上超算 |
| EPOCH 2D3V 生产扫描 | 超算 | PIC 最吃核数、内存和并行通信 |
| EPOCH 3D | 超算，只做少量验证点 | 不做 3D 大扫描 |

## 第一阶段：本地先把链路通电

目标：不用等 PIC，先用参数化 TNSA 氘束跑通 `deuteron_beam.h5 -> neutron_source.h5`。

```bash
python3 tests/test_gates.py
python3 moduleA_pic/parametric_beam.py --n 200000 -o deuteron_beam.h5
python3 moduleB_source/build_source.py deuteron_beam.h5 -o neutron_source.h5
```

当前 `moduleB_source/thick_target.py` 使用占位阻止本领，只能用于软件链路验证。正式结果前必须替换为 SRIM/PSTAR 数据。

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

## 第三阶段：超算 EPOCH 2D3V

最小扫描矩阵：

```text
a0 = 5, 10, 20
preplasma L = 0, 1 um
target = CD2, thickness = 5 um
```

这是第一轮 6 点扫描。若结果对靶厚敏感或审稿/组会需要，再补 `3 um` 厚度形成 12 点扫描。

扫描 manifest 由配置自动生成：

```bash
python3 scripts/make_pic_scan_manifest.py
```

输出见 `hpc/pic_first_2d_scan.csv`。

先只追求每个 case 导出穿过靶后采样面的氘束相空间：

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

然后重跑 OpenMC Case B，与 Case A 对比。

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
