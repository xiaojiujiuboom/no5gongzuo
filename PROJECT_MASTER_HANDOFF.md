# 项目主交接文档 · 激光 D-D 中子源 → 锂靶产氚（轻量 3D 端到端）

> 本文件是**自包含**主交接。新 agent 只读本文件即可理解全貌并接手，不依赖原 GitHub 仓库。
> 定稿口径：**只做一条轻量 3D 流水线，端到端串起来产氚（T），不搞大扫描、不追 3D 收敛、不再拖延。**

---

## 1. 目标与科学问题

激光打薄 CD2 箔产生前向氘束，氘束进外置厚 CD2 converter 慢化并发生 D(d,n)³He，得到**畸变**（多普勒展宽 + 前向各向异性）的 D-D 中子源；该源照射外部锂靶算产氚率 TPR。

**核心问题**：相对理想的各向同性单能 2.45 MeV 源，这个畸变源使锂靶 TPR 差多少、差在哪。
**预期结论**：差异集中在 `⁷Li(n,n'α)T` 阈值窗口（>2.82 MeV）与前向角区；`⁶Li(n,α)T` 主通道对源细节钝感。

**诚实边界（写进论文，别越界）**：
- 不主张"激光能产氚"（能量账差几个数量级）、不主张"激光是更好的源"。
- 激光/紧凑源是背景动机（IFE 电站中子本就畸变脉冲），不是论点。
- 只算 D-D 分支；`¹²C(d,n)`、体相反应、hole-boring 作为假设边界声明。
- 论文落点（so what）：给用紧凑/激光 D-D 源做增殖包层试验台的社区一个可操作修正——**把真实畸变源当理想 2.45 MeV 各向同性源来解读产氚测量，会在 ⁷Li 阈值窗口/前向角系统性偏差 X%**。

---

## 2. 端到端工作流（唯一主线）

```text
[A] EPOCH 3D PIC (轻量)          [B] 半解析源项 (Python)          [C] OpenMC 输运
激光→薄CD2→前向氘束         ->  厚CD2 converter D-D 中子源   ->  外置锂靶 TPR
近面 rear+5µm 记录氘相空间       Bosch-Hale + 阻止本领 + 两体boost   Li6/Li7 分道, per-source-neutron
   |                                   |                                |
deuteron_beam.h5   ------------>   neutron_source.h5   ----------->   TPR (Case A vs B)
```

**关键解耦**：三段之间只通过两个 HDF5 文件传数据（见 §3）。任一段可独立替换/调试。
**产 T 的最终对比**：Case A（理想各向同性 2.45 MeV 源）vs Case B（畸变 PIC 源），比 per-source-neutron 的 ⁷Li/⁶Li 分道 TPR。

---

## 3. 数据契约（HDF5 schema，三段的唯一接口）

`deuteron_beam.h5`（A→B）与 `neutron_source.h5`（B→C）同结构：

| dataset | 形状 | 单位 | 含义 |
|---|---|---|---|
| `E` | (N,) | MeV | 粒子动能 |
| `dir` | (N,3) | 单位矢量 | 方向（每行模=1） |
| `weight` | (N,) | 粒子/shot | 权重（氘或中子） |
| `t` | (N,) | ns | 时间（可全 0） |

文件属性：`deuteron_beam.h5` 带 `n_deuterons_total = sum(weight)`；`neutron_source.h5` 带 `Y_total = sum(weight)`。
校验函数 `interfaces/schema.py::validate_*` 会强制：dir 为单位矢量、E/weight≥0、total 属性等于 sum(weight)。**写文件必须走 `write_deuteron_beam` / `write_neutron_source`，别手写。**

---

## 4. Stage A — EPOCH 3D PIC（轻量源锚点）

**职责**：只负责把 TNSA 氘束算到"加速定型"，在近靶面记录氘相空间。**不陪慢氘飞、不追 5ps、不追收敛。**

**源定义（已修订，弃旧 rear+20µm/5ps）**：探针面 `rear+5µm`；跑到 `~1ps`，用快照确认 **E_max 与 >2.82MeV 产额占比已 plateau 即停**；D PPC 拉高喂高能尾统计。

**网格（C 变体，单节点 256 核，内存 ~35GB）**：`nx,ny,nz=1500,320,320`，`x=[-8,30]µm`，`y,z=[-10,10]µm`，`dx≈25nm, dy=dz≈62nm`，`dt≈0.07fs`。分辨率欠解析趋肤深度(~6×)是可负担 3D 的固有妥协，**文里诚实声明即可**。

**提交铁律（血泪教训）**：
- 上传的 `input.deck` 必须 **comment-free**（连空行也可能触发 EPOCH3D parser 报 `Value "constant" invalid`；保险起见首行直接 `begin:constant`）。
- **强制拓扑** `nprocx,nprocy,nprocz`（别让它自动 `1×2×128`，否则 x 全留每个 rank、halo 爆内存 OOM）。
- **关周期 restart**（`restart_dump_every=-1`），只保留 final restartable；否则第一个 dump 写巨型 SDF 撑爆节点。
- walltime 必须显式设，别用乐观硬墙时（曾三发 4h 全超时、烧 ~192 CNY 无产出）。

**完整 input.deck（300fs 微基准；正式源把 `t_end` 改到 ~1000fs）**：

```
begin:constant
  lambda0 = 0.8 * micron
  omega0 = 2.0 * pi * c / lambda0
  a0 = 10.0
  w0 = 3.0 * micron
  tau = 30.0 * femto
  t0 = 3.0 * tau
  thickness = 3.0 * micron
  x_front = 0.0 * micron
  x_rear = x_front + thickness
  target_half = 5.0 * micron
  src_plane = x_rear + 5.0 * micron
  n_unit = 3.98e28
  n_D = 2.0 * n_unit
  n_C = 1.0 * n_unit
  n_e = 8.0 * n_unit
end:constant

begin:control
  nx = 1500
  ny = 320
  nz = 320
  x_min = -8.0 * micron
  x_max = 30.0 * micron
  y_min = -10.0 * micron
  y_max = 10.0 * micron
  z_min = -10.0 * micron
  z_max = 10.0 * micron
  nprocx = 16
  nprocy = 4
  nprocz = 4
  t_end = 300.0 * femto
  dt_multiplier = 0.95
  dlb_threshold = 0.5
  stdout_frequency = 200
  physics_table_location = /publicfs10/fs10-m9/home/m9s003861/pic/software/epoch_release-4.20.1/epoch3d/src/physics_packages/TABLES
end:control

begin:boundaries
  bc_x_min = simple_laser
  bc_x_max = simple_outflow
  bc_y_min = simple_outflow
  bc_y_max = simple_outflow
  bc_z_min = simple_outflow
  bc_z_max = simple_outflow
end:boundaries

begin:laser
  boundary = x_min
  intensity_w_cm2 = 1.37e18 * a0^2 / (lambda0 / micron)^2
  lambda = lambda0
  pol_angle = 0.0
  phase = 0.0
  t_profile = gauss(time, t0, tau)
  profile = gauss(y, 0.0, w0) * gauss(z, 0.0, w0)
end:laser

begin:species
  name = electron
  charge = -1.0
  mass = 1.0
  nparticles_per_cell = 8
  temp = 0.0
  number_density = if((x gt x_front) and (x lt x_rear) and (abs(y) lt target_half) and (abs(z) lt target_half), n_e, 0.0)
end:species

begin:species
  name = deuteron
  charge = 1.0
  mass = 3670.5
  nparticles_per_cell = 32
  temp = 0.0
  number_density = if((x gt x_front) and (x lt x_rear) and (abs(y) lt target_half) and (abs(z) lt target_half), n_D, 0.0)
end:species

begin:species
  name = carbon
  charge = 6.0
  mass = 22032.0
  nparticles_per_cell = 4
  temp = 0.0
  number_density = if((x gt x_front) and (x lt x_rear) and (abs(y) lt target_half) and (abs(z) lt target_half), n_C, 0.0)
end:species

begin:probe
  name = D_source_rear5
  point = (src_plane, 0.0, 0.0)
  normal = (1.0, 0.0, 0.0)
  ek_min = 100.0 * kev
  ek_max = -1.0
  include_species:deuteron
  dumpmask = always
end:probe

begin:dist_fn
  name = deuteron_en
  ndims = 1
  dumpmask = always
  direction1 = dir_en
  range1 = (0.0, 8.0e-12)
  resolution1 = 1000
  include_species:deuteron
end:dist_fn

begin:output
  dt_snapshot = 100.0 * femto
  dump_first = F
  dump_last = T
  grid = never
  ex = never
  ey = never
  number_density = never
  particles = never
  px = never
  py = never
  particle_probes = always
  distribution_functions = always
  full_dump_every = -1
  restart_dump_every = -1
  force_final_to_be_restartable = T
end:output
```

**A 的输出转换**：probe SDF 里 `src_plane` 穿面氘（px>0, E>0.1MeV）→ 提取相空间 → 换算 `E[MeV], dir(单位矢量), weight[氘/shot]` → 用 `write_deuteron_beam` 存 `deuteron_beam.h5`。（原仓库对应 `tools/extract_deuteron_npz.py` + `moduleA_pic/convert_epoch_npz.py`；脱离仓库时按 §3 schema 自行实现即可。）

---

## 5. Stage B — 半解析 D-D 中子源（Python）

**职责**：读 `deuteron_beam.h5`，对每个氘用**厚靶产额** `Y = ∫ n_D·σ(E_cm)/S(E) dE`（Bosch-Hale D(d,n)³He 截面 + D-in-CD2 阻止本领 S），逆 CDF 采样反应发生能量，再做**两体运动学 boost** 得到实验室系中子能量与方向；权重 = 氘权重 × 产额。写 `neutron_source.h5`。

**关键实现点/已知约束**：
- `E_cm = E_lab/2`；`E_d→0` 时中子 ≈ 2.45 MeV；1 MeV 前向 ≈ 4.14 MeV、后向 ≈ 1.76 MeV（GATE 已固化）。
- Bosch-Hale 在 CM 拟合区间外（氘 lab >9.8 MeV）置零。已核 accepted 源 >9.8 MeV 权重占比 ~5e-5，可忽略；若换更高能源需复核。
- 命令（原仓库）：`python3 moduleB_source/build_source.py deuteron_beam.h5 -o neutron_source.h5`

**必须替换的占位项**：`data/stopping_D_in_CD2.csv` 现为 provisional PSTAR-style seed，**正式产额前必须换 SRIM/PSTAR 可靠数据**。

---

## 6. Stage C — OpenMC 锂靶输运（产 T）

**职责**：读 `neutron_source.h5`，在外置锂靶算 TPR。
- **几何**：圆柱锂靶（`radius=10cm, height=20cm, cavity=1cm`），源在腔内。
- **材料**：金属锂 `density=0.534 g/cc`，`Li6 at% ∈ {7.59(天然), 90(富集)}`。
- **tally**：`H3-production`（或按安装版本确认 `(n,t)`/MT 号），按核素 filter **Li6/Li7 分道**；空间/能量 mesh（建议 CylindricalMesh）。
- **两个 case**：
  - **Case A**（理想基线）：各向同性单能 2.45 MeV 点源。
  - **Case B**（畸变）：读 PIC/参数化 `neutron_source.h5`，**按 μ 分 bin 建多源保留 E-μ 相关**，strength 归一到 **per-source-neutron**。
- 命令（原仓库）：`python3 moduleC_openmc/run.py --case A|B --li6 7.59 --neutron neutron_source.h5 [--production]`
- 机器相关：`OPENMC_CROSS_SECTIONS` 放本地 `.env`，别提交；`preferred_library` 建议 FENDL-3.2。

**报告口径**：per-source-neutron 的 A/B 比是稳健量；per-shot 绝对氚数仅 illustrative（2D/单发归一）。

---

## 7. 验证关卡（GATE，勿回退）

| GATE | 内容 | 通过标准 |
|---|---|---|
| env | OpenMC 环境 | 最小固定源算例跑通 |
| sigma | Bosch-Hale 截面 | 对 ENDF/NRL 两点核对数量级与趋势；越界置零 |
| kin | 两体 boost | E_d→0 得 ~2.45 MeV；1 MeV 前向 ~4.14、后向 ~1.76 MeV |
| B | 中子源项 | 有 2.45 MeV 峰 + 越阈高能尾，角分布前向偏置 |
| C | 锂靶 TPR | ⁶Li 通道 A≈B；⁷Li 差异集中在 >2.82 MeV |
| norm | 归一化 | per-source-neutron 与 per-shot 绝对产额分开报告 |

---

## 8. 必补三硬洞（不补易被审稿人毙）

1. **D(d,n) 的 CM 各向异性**（接口已留 `cm_dir_unit`）：论文主题即"各向异性"，核反应本身用各向同性是最大漏洞。用 Legendre/ENDF 参数化实现，保留各向同性可切换基线，出敏感性图。勿破坏 `gate_kinematics`。
2. **真实阻止本领**：SRIM/PSTAR 换掉占位表。
3. **多库不确定度**：⁷Li 关键截面 ENDF/B vs FENDL 对比一版。

---

## 9. 接手即可执行的顺序

1. 上传 §4 的 `input.deck`（comment-free）+ Slurm（256 核 / walltime 显式），先跑 **300fs 微基准**，实测 `s/step` 与 `MaxRSS`，确认不 OOM。
2. 正式源：`t_end→~1000fs`，跑完看快照确认 E_max/>2.82MeV 占比 plateau；提取穿 `rear+5µm` 氘相空间 → `deuteron_beam.h5`。
3. `build_source.py` → `neutron_source.h5`（**先换好阻止本领**）。
4. OpenMC Case A vs Case B（天然 + 富集）→ ⁷Li/⁶Li 分道 TPR，per-source-neutron。
5. 补三硬洞 + 出主图（见下）。

**主图**：① ⁷Li vs ⁶Li 分道、理想 vs 畸变，差异集中 >2.82 MeV；② 畸变强度（>2.82MeV 占比/前向张角）→ ⁷Li 超额 TPR 标度曲线；③ CM 带异性 vs 各向同性、天然 vs 富集、ENDF vs FENDL 敏感性。

---

## 10. 环境/成本备忘

- 超算计价 ~0.1 CNY/core-hour。轻量 3D 单发估：微基准 300fs ~15-30 元；正式 ~1ps 源单个 a0 估几十元。
- EPOCH3D binary 与 TABLES 路径见 §4 deck；`amd_m9_768` 分区，单节点 256 核。
- Python 依赖：numpy, h5py, matplotlib, pyyaml；OpenMC 单独装。
