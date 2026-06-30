# M4 Pro 本地 2D + Geant4, 后续超算 3D 执行手册

## 0. 结论先说

这个资源安排是合理的:

```text
M4 Pro:
  2D EPOCH smoke test / medium-resolution runs
  Geant4 Li(p,n) benchmark
  EPOCH -> Geant4 phase-space coupling
  small Sobol/LHS sampling
  optional local BO

Supercomputer:
  selected 3D EPOCH validation points only
  optional high-resolution 2D reruns if M4 Pro too slow
```

核心原则:

```text
不要把 3D 当探索工具。
M4 Pro 先证明链条成立。
超算只验证少数有价值点。
```

本项目固定为:

```text
CH foil -> TNSA protons -> Li converter -> neutron yield + tau_exit,FWHM
```

主目标:

```text
maximize  log10(Y_n_exit / E_L)
minimize  tau_exit,FWHM
```

其中:

```text
Y_n_exit       = 穿过 Li 后表面的中子数
tau_exit,FWHM = 中子穿过 Li 后表面的出射时间分布 FWHM
```

`10 cm detector plane` 仍然可以记录, 但只作为 TOF/能谱弥散诊断, 不作为主优化 FWHM 目标。

---

## 1. 为什么这样分资源

### 1.1 M4 Pro 适合做什么

M4 Pro 适合:

```text
1. 编译和调试 EPOCH2D
2. 跑低/中分辨率 2D TNSA
3. 写 phase-space exporter
4. 编译和调试 Geant4
5. 跑 Geant4 单能 proton benchmark
6. 跑 EPOCH phase-space -> Geant4 Li 的耦合
7. 做几十个低成本 Geant4 厚度扫描
8. 做 10-30 个 2D 样本, 判断项目是否值得继续
```

M4 Pro 不适合:

```text
1. 大规模 3D EPOCH
2. 80-100 个高分辨率 2D EPOCH 全量 BO
3. 高频全场 dump 的 PIC 大输出
4. 长时间超高 ppc convergence study
```

### 1.2 超算适合做什么

超算适合:

```text
1. 3D EPOCH validation
2. 少数高分辨率 2D/3D reruns
3. 高 ppc 收敛验证
4. 大批量 job array
```

推荐只送 4-6 个 3D 点:

```text
baseline point
best yield point
best short-pulse point
Pareto knee point
control point
optional second Pareto point
```

---

## 2. 总体执行路线

推荐按下面顺序做, 不要跳步骤:

```text
Phase A: local Geant4 Li(p,n) benchmark
Phase B: local EPOCH2D CH TNSA smoke test
Phase C: local EPOCH2D -> Geant4 coupling
Phase D: local small parameter sampling
Phase E: local BO only if D looks promising
Phase F: HPC 3D validation
Phase G: final plots and paper decision
```

判断是否继续的关口:

```text
After Phase C:
  如果中子产额为 0 或 Geant4 benchmark 不可信, 先停。

After Phase D:
  如果 Y_n_exit 和 tau_exit 对参数没有明显变化, 不要急着 BO。

After Phase E:
  如果 Pareto front 有清楚结构, 再申请/使用超算做 3D。
```

---

## 3. 本地目录结构

建议在本地建立一个独立项目目录:

```text
ch_li_neutron_bo/
  env/
  epoch/
    decks/
    templates/
    scripts/
  geant4/
    src/
    build/
    macros/
  runs/
    epoch2d/
    geant4/
    coupled/
  data/
    phase_space/
    objectives/
    benchmarks/
  bo/
    configs/
    logs/
  analysis/
    notebooks/
    scripts/
    figures/
  hpc/
    epoch3d_decks/
    submit_scripts/
```

每个样本一个目录:

```text
runs/coupled/sample_0001/
  params.json
  epoch.deck
  epoch_stdout.log
  proton_phase_space.h5
  geant4_DLi_0p05cm/
  geant4_DLi_0p10cm/
  geant4_DLi_0p20cm/
  geant4_DLi_0p50cm/
  geant4_DLi_1p00cm/
  objectives.csv
```

---

## 4. 本地软件环境

### 4.1 必要软件

本地需要:

```text
EPOCH2D
Geant4
CMake
MPI, e.g. OpenMPI
Fortran compiler, e.g. gfortran
HDF5
Python 3
Python packages: numpy, scipy, h5py, pandas, matplotlib
BO package: BoTorch/Ax or scikit-optimize
```

### 4.2 macOS 上的建议

M4 Pro 是 Apple Silicon, 主要风险是编译和依赖路径, 不是物理代码本身。

建议策略:

```text
1. Geant4 先只做 headless simulation, 不要先折腾 GUI/visualization。
2. EPOCH2D 先不启用复杂外部依赖, 先跑 ASCII/SDF 基本输出。
3. Python 后处理用 venv 或 conda 单独隔离。
4. 所有路径写进 Makefile/CMake 配置, 不要手动反复 export。
```

### 4.3 推荐 Python 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy scipy h5py pandas matplotlib scikit-learn scikit-optimize tqdm
```

如果要用 BoTorch:

```bash
pip install torch gpytorch botorch ax-platform
```

注意: BO 本身几乎不耗算力。若 BoTorch 安装麻烦, 第一版可先用:

```text
Sobol/LHS sampling + Pareto sorting
```

这已经足够判断项目是否值得继续。

---

## 5. 本地 EPOCH2D 资源估算

### 5.1 为什么 2D 可以在 M4 Pro 上跑

PIC 的粒子主要存在于靶和 preplasma 区域, 不是整个真空盒子都填满粒子。因此 2D 中等分辨率可以在本地跑。

但要控制:

```text
1. 网格规模
2. ppc
3. 输出频率
4. 全场 dump 数量
```

### 5.2 三档 EPOCH2D 设置

#### Tier 0: smoke test

用于调 deck、边界、输出、脚本。

```text
box = 40 um x 30 um
x_front = 10 um
x_diag = 30 um
dx = 0.04 um
dy = 0.08 um
Nx = 1000
Ny = 375
t_end = 300 fs
ppc = 4 - 8 per species
```

预计:

```text
runtime: minutes to < 1 hour
storage: < 1 GB per run
```

只看:

```text
laser reaches target
target ionizes/expands
TNSA protons appear
diagnostic plane can export protons
```

#### Tier 1: local medium baseline

用于第一版耦合和小样本扫描。

```text
box = 60 um x 40 um
x_front = 15 um
x_diag = 50 um
dx = 0.02 um
dy = 0.05 um
Nx = 3000
Ny = 800
t_end = 700 - 800 fs
ppc = 8 - 16 per species
```

预计:

```text
runtime: 1 - 8 hours per run, depending on M4 Pro cores and ppc
storage: 1 - 5 GB per run if output is controlled
```

这是 M4 Pro 的主力设置。

#### Tier 2: local production 2D

用于少数关键 2D 点, 不建议一开始批量跑。

```text
box = 80 um x 50 um
x_front = 20 um
x_diag = 65 um
dx = 0.02 um
dy = 0.05 um
Nx = 4000
Ny = 1000
t_end = 1 ps
ppc = 16 per species
```

预计:

```text
runtime: several hours to overnight per run
storage: 2 - 10 GB per run
```

如果 M4 Pro 实测每个 Tier 2 点超过 8-12 小时, 不建议本地做大批量 BO。改为:

```text
local Tier 1 sampling + selected Tier 2 reruns
```

---

## 6. EPOCH2D 主物理参数

### 6.1 baseline

```text
Laser:
  lambda0 = 0.8 um
  I0 = 2e20 W/cm2
  a0 ≈ 9.7
  tau = 30 fs
  w0 = 5 um
  normal incidence
  linear polarization

CH target:
  d_CH = 1.0 um
  n_e = 200 nc
  n_C6+ = 28.57 nc
  n_H+ = 28.57 nc
  Te = Ti = 10 eV
  L_pre = 0.2 um
```

### 6.2 本地初始参数范围

本地第一轮不要扫 5 维全范围。建议先固定或半固定一部分。

推荐第一轮小扫描:

```text
I0    = 1e20, 2e20, 3e20 W/cm2
tau   = 30 fs fixed initially
d_CH  = 0.5, 1.0, 2.0 um
L_pre = 0.0, 0.2, 0.5 um
```

这已经是:

```text
3 x 3 x 3 = 27 EPOCH2D cases
```

如果觉得太多, 先做 9 个:

```text
I0 = 1e20, 2e20, 3e20
d_CH = 0.5, 1.0, 2.0
L_pre = 0.2 fixed
tau = 30 fs fixed
```

### 6.3 BO 阶段参数范围

如果小扫描有意义, 再进入 BO:

```text
I0    in [5e19, 3e20] W/cm2
tau   in [20, 60] fs
d_CH  in [0.2, 3.0] um
L_pre in [0.0, 1.0] um
```

注意: `D_Li` 不建议作为 EPOCH BO 变量, 因为它只影响 Geant4, 很便宜。更聪明的做法是:

```text
BO controls EPOCH variables: I0, tau, d_CH, L_pre
For each EPOCH source, Geant4 sweeps D_Li grid.
```

这样每个昂贵 EPOCH 源都能产出一整条 Li 厚度 yield-FWHM 曲线。

---

## 7. Geant4 本地任务

### 7.1 Geant4 benchmark 必做

先做单能质子打 Li:

```text
proton energies:
  1.5, 2, 3, 5, 10, 20, 40 MeV

Li thickness:
  0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0 cm

Li:
  pure 7Li
  density = 0.534 g/cm3
  cylinder radius = 2 cm
```

记录:

```text
Y_n_exit
tau_exit_FWHM
Y_n_detector_10cm
tau_detector_FWHM
neutron energy spectrum at Li exit
relative statistical error
```

物理检查:

```text
Ep = 1.5 MeV -> almost zero neutrons
Ep >= 2 MeV -> neutron production begins
yield increases reasonably with Ep
thicker Li generally increases yield then saturates
tau_exit_FWHM increases with D_Li
tau_detector_FWHM is much larger due to TOF dispersion
```

### 7.2 Li 厚度扫描

对每个 EPOCH source, 本地 Geant4 扫:

```text
D_Li = 0.05, 0.10, 0.20, 0.50, 1.00, 2.00, 3.00 cm
```

这比把 `D_Li` 放进 BO 更划算, 因为 Geant4 比 EPOCH 便宜得多。

输出一张表:

```csv
sample_id,D_Li_cm,Y_n_exit,Y_n_exit_per_J,tau_exit_FWHM_ps,Y_n_det_10cm,tau_det_FWHM_ps,rel_err
0001,0.05,...
0001,0.10,...
...
```

### 7.3 Geant4 统计量

本地调试:

```text
N_primary = 1e5
relative error target = 10 - 20%
```

正式本地点:

```text
N_primary = 1e6 - 1e7, depending on yield
relative error target = 5 - 10%
```

最终 Pareto 点:

```text
relative error target < 3 - 5%
```

如果事件太少:

```text
increase proton resampling
use weighted tallies
focus on exit tally first
do not store full tracks
```

---

## 8. EPOCH phase-space 如何导入 Geant4

### 8.1 EPOCH 输出文件内容

在诊断面 `x_diag` 记录穿过的质子:

```text
x
y
px
py
energy
weight
arrival_time
```

保存成 HDF5:

```text
proton_phase_space.h5
  /x_um
  /y_um
  /px_SI or /px_mc
  /py_SI or /py_mc
  /energy_MeV
  /weight
  /time_fs
```

### 8.2 2D 到 3D 的本地近似

本地 2D 阶段可以用轴对称重建:

```text
r = abs(y_2D)
phi ~ Uniform(0, 2pi)

y_3D = r cos(phi)
z_3D = r sin(phi)
```

动量:

```text
p_perp = py_2D
py_3D = p_perp cos(phi)
pz_3D = p_perp sin(phi)
px_3D = px_2D
```

位置:

```text
x_3D = 0 at Geant4 source plane
y_3D, z_3D from above
```

时间:

```text
t_3D = EPOCH arrival_time at x_diag
```

### 8.3 权重处理

推荐两种方式。

#### 方法 A: weighted tally

Geant4 每个 primary 带一个 source weight:

```text
event_weight = EPOCH macro-particle weight
```

所有 neutron tally 累加权重。

优点:

```text
保留原始权重
无需大量 resampling
```

缺点:

```text
需要确认 Geant4 tally 代码正确处理权重
```

#### 方法 B: resampling

按 EPOCH 权重抽样生成 Geant4 primaries:

```text
sample proton i with probability p_i = weight_i / sum(weight)
run N_primary Geant4 protons
scale result by total proton weight
```

优点:

```text
Geant4 generator 简单
```

缺点:

```text
高权重粒子可能被重复抽样
需要记录 scale factor
```

第一版推荐方法 B, 因为更容易调通。最终可以转方法 A。

### 8.4 Geant4 PrimaryGenerator 逻辑

伪代码:

```cpp
Read phase_space.h5
Precompute cumulative distribution from weights

For each event:
    i = sample_proton_index()
    E = energy_MeV[i]
    dir = normalize(px, py, pz)
    pos = source_position_from_phase_space(i)
    t0 = time_fs[i]

    particle = proton
    set energy E
    set position pos
    set direction dir
    set time t0
```

Geant4 记录:

```text
when neutron crosses Li rear surface:
  exit_time
  exit_energy
  exit_position
  exit_direction

when neutron crosses detector at 10 cm:
  detector_time
  detector_energy
```

---

## 9. 本地 sampling / BO 计划

### 9.1 不建议一开始就 BO

先做:

```text
9-point or 12-point manual/Sobol scan
```

看:

```text
1. 是否稳定产生 Ep > 2 MeV protons
2. Geant4 是否有非零 neutron yield
3. D_Li 是否造成清楚的 yield-FWHM trade-off
4. 不同 CH/EPOCH 参数是否改变结果
```

### 9.2 Local Stage D: small sampling

推荐最小采样:

```text
N_EPOCH2D = 9 - 12
N_DLi per source = 7
Total Geant4 tasks = 63 - 84
```

这是 M4 Pro 可接受的第一批。

### 9.3 Local Stage E: optional BO

如果 9-12 个点有意义, 扩到:

```text
N_initial = 20 Sobol points
N_BO = 10 - 20 iterations
Total EPOCH2D = 30 - 40
```

每个 EPOCH point 后接:

```text
7 Li thickness Geant4 runs
```

总 Geant4:

```text
210 - 280 tasks
```

这些 Geant4 任务可以低统计先跑, Pareto 点再高统计复跑。

### 9.4 本地 BO 目标

对每个 EPOCH source + D_Li 组合, 目标:

```text
f1 = maximize log10(Y_n_exit / E_L)
f2 = minimize tau_exit_FWHM
```

如果 BO 只控制 EPOCH variables, 而 `D_Li` 是内层扫描, 则每个 EPOCH source 会得到多个 candidate points:

```text
(I0, tau, d_CH, L_pre, D_Li)
```

最后用所有 candidate 做 Pareto sorting。

---

## 10. 本地运行时间和存储预算

### 10.1 M4 Pro 估计

实际耗时必须用第一两个 runs 测。粗略估计:

```text
Tier 0 EPOCH2D:
  minutes to < 1 hour

Tier 1 EPOCH2D:
  1 - 8 hours per run

Tier 2 EPOCH2D:
  several hours to overnight per run

Geant4 benchmark:
  minutes to hours per case, depending on N_primary

Geant4 coupled:
  tens of minutes to hours per D_Li per source
```

如果实测:

```text
Tier 1 > 6 hours/run
```

则不要本地做 40 个 BO 点。改为:

```text
local 9-12 samples only
then decide whether to move 2D production to cluster
```

### 10.2 存储预算

本地建议:

```text
available free disk: at least 1 TB
comfortable: 2 TB external SSD
```

每个 2D run 控制在:

```text
1 - 5 GB
```

关键方法:

```text
1. 不保存高频全场 dump
2. 只保存少数 field snapshots
3. proton phase-space 用 HDF5 压缩
4. Geant4 只保存 histograms/tallies, 不保存 full tracks
5. 每个 run 完成后自动生成 summary.json/csv
```

---

## 11. 输出控制

### 11.1 EPOCH 最小输出

每个 run 保留:

```text
params.json
epoch.deck
stdout.log
proton_phase_space.h5
proton_spectrum.csv
summary.json
2-3 field snapshots for sanity check
```

不要保留:

```text
hundreds of full field dumps
all particles at every timestep
```

### 11.2 Geant4 最小输出

每个 Geant4 task 保留:

```text
geant4_params.json
exit_neutron_energy_hist.csv
exit_neutron_time_hist.csv
detector_time_hist.csv
summary.json
```

`summary.json`:

```json
{
  "sample_id": "0001",
  "D_Li_cm": 1.0,
  "N_primary": 1000000,
  "Y_n_exit": 1.2e8,
  "Y_n_exit_per_J": 4.0e6,
  "tau_exit_FWHM_ps": 320.0,
  "Y_n_detector_10cm": 7.5e7,
  "tau_detector_FWHM_ps": 5200.0,
  "relative_error": 0.06
}
```

---

## 12. 超算 3D 验证计划

### 12.1 什么时候上超算

只有满足下面条件才建议上 3D:

```text
[ ] Geant4 benchmark 可信
[ ] EPOCH2D baseline produces Ep,max > 5-10 MeV
[ ] EPOCH2D -> Geant4 coupling gives nonzero neutron yield
[ ] D_Li thickness scan shows yield/FWHM trade-off
[ ] local 2D sampling gives at least a rough Pareto front
```

否则 3D 会浪费超算时间。

### 12.2 3D 点选择

从本地结果选 4-5 个点:

```text
P0 baseline:
  I0 = 2e20 W/cm2
  tau = 30 fs
  d_CH = 1 um
  L_pre = 0.2 um
  D_Li = 1 cm

P1 best yield:
  max Y_n_exit / E_L

P2 shortest pulse:
  min tau_exit_FWHM with non-negligible Y_n_exit

P3 knee:
  best compromise on Pareto front

P4 control:
  a low-yield or off-Pareto point
```

### 12.3 3D EPOCH recommended settings

保守 3D:

```text
box = 50 um x 30 um x 30 um
x_front = 12 - 15 um
x_diag = 40 - 45 um
dx = 0.04 - 0.05 um
dy = dz = 0.10 - 0.12 um
ppc = 8 per species
t_end = 700 - 900 fs
```

较好 3D:

```text
box = 60 um x 36 um x 36 um
dx = 0.03 - 0.04 um
dy = dz = 0.08 - 0.10 um
ppc = 8 - 16 per species
t_end = 0.8 - 1.0 ps
```

### 12.4 3D 资源粗估

每个 3D 点:

```text
cores: 512 - 2048
walltime: 12 - 72 hours
memory: hundreds of GB to ~1 TB
storage: 0.5 - 5 TB if output is controlled
```

总量:

```text
4-5 points:
  50k - 500k core-hours
```

具体以超算测试 run 为准。

### 12.5 3D 输出

3D 只需要:

```text
proton_phase_space_3d.h5 at x_diag
proton_spectrum_3d.csv
few field snapshots
summary.json
```

然后 Geant4 可以:

```text
option A: 在超算跑
option B: 把 downsampled phase-space 拿回 M4 Pro 跑
```

如果 3D phase-space 太大:

```text
weighted downsampling to 1e6 - 1e7 source protons
preserve spectrum and angular/time distribution
```

---

## 13. go/no-go 决策

### 13.1 一周后判断

一周目标:

```text
1. Geant4 monoenergetic benchmark works
2. EPOCH2D smoke test works
3. baseline CH produces protons above 2 MeV
```

如果失败:

```text
不要 BO, 先修物理/代码。
```

### 13.2 两到三周后判断

目标:

```text
1. EPOCH phase-space successfully imported into Geant4
2. Li gives nonzero neutron yield
3. D_Li scan changes Y_n_exit and tau_exit_FWHM
```

如果看不到 trade-off:

```text
不要写成 BO 论文。
可以停在 demo / skill-building。
```

### 13.3 一到两个月后判断

目标:

```text
1. 10-30 2D EPOCH sources
2. each source has Li thickness scan
3. a visible Pareto front
```

如果 Pareto front 有结构:

```text
选择 3D points, 上超算。
```

如果 Pareto front 没结构:

```text
降低项目优先级, 不要强行写论文。
```

---

## 14. 推荐时间表

### Week 1

```text
compile Geant4
compile EPOCH2D
Geant4 monoenergetic Li benchmark
EPOCH2D Tier 0 smoke test
```

### Week 2

```text
EPOCH2D Tier 1 baseline
proton phase-space exporter
first EPOCH -> Geant4 coupling
```

### Week 3-4

```text
9-12 local EPOCH2D samples
Li thickness scan for each source
first Pareto plot
```

### Month 2

```text
optional local BO to 30-40 EPOCH2D points
high-stat Geant4 rerun of Pareto points
prepare 3D point list
```

### Month 3

```text
HPC 3D EPOCH validation
3D phase-space -> Geant4
compare 2D ranking vs 3D ranking
```

### Month 4+

```text
decide whether to write paper
or keep as skill/demo project
```

---

## 15. 本地第一批实际任务清单

按这个顺序做:

```text
Task 1:
  Geant4 pure 7Li, monoenergetic protons
  Ep = 1.5, 2, 5, 10, 20 MeV
  D_Li = 0.1, 1.0 cm

Task 2:
  EPOCH2D smoke CH
  I0 = 2e20 W/cm2
  tau = 30 fs
  d_CH = 1 um
  L_pre = 0.2 um
  low resolution, t_end = 300 fs

Task 3:
  EPOCH2D medium baseline
  t_end = 700 - 800 fs
  export proton phase-space at x_diag

Task 4:
  import baseline proton phase-space into Geant4
  D_Li = 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0 cm

Task 5:
  plot Y_n_exit vs D_Li
  plot tau_exit_FWHM vs D_Li
  plot Y_n_exit vs tau_exit_FWHM
```

如果 Task 5 有清楚 trade-off, 再进入 sampling/BO。

---

## 16. 对你个人精力的建议

因为你已经满足毕业条件, 这个项目不应该一开始就按论文压力推进。建议把它当成三层目标:

```text
Level 1:
  跑通 EPOCH -> Geant4, 证明自己会 PIC-MC coupling。

Level 2:
  做出 local 2D Pareto front, 证明它有物理趋势。

Level 3:
  做 3D validation, 再决定是否写论文。
```

只要 Level 1 完成, 简历上就已经可以合理写:

```text
Built an EPOCH-Geant4 workflow for laser-driven neutron source modeling.
```

不要在 Level 1 之前就承诺 Level 3。

