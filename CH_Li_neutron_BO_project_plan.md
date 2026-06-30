# CH-Li 激光驱动中子源 BO 项目方案

## 0. 项目一句话

本项目采用两步模拟链:

```text
CH foil + intense laser -> TNSA protons -> Li converter -> neutron yield + neutron FWHM
```

目标是用 Bayesian optimization, BO, 寻找在普通 CH 薄靶 TNSA 质子源驱动下, Li 转换靶产生中子时的最佳参数组合。

最终优化目标:

```text
maximize  neutron yield
minimize  neutron pulse FWHM at the Li exit surface
```

第一版不加入 FLASH, double-layer target, detector response, activation foil, diamond detector, Be/LiD/CD2 converter。先只做最干净的闭环:

```text
EPOCH:  laser -> CH -> proton phase space
Geant4: proton phase space -> Li(p,n) -> neutron time profile and yield
BO:     parameters -> EPOCH -> Geant4 -> objectives
```

---

## 1. 科学问题和论文主线

### 1.1 物理问题

激光打 CH 薄靶后, TNSA 机制在靶后表面产生 MeV 级质子。质子进入 Li 转换靶后通过核反应产生中子, 主要反应为:

```text
7Li + p -> 7Be + n
```

该反应有阈值, 约为 1.88 MeV。因此, EPOCH 输出的质子谱中必须有足够多的质子超过约 2 MeV, Geant4 中才会得到有效中子产额。

### 1.2 优化问题

Li 靶厚度越大, 质子发生核反应的机会通常越多, 中子产额可能增加; 但中子在 Li 中产生和输运的时间跨度也会变长, 因此 Li 后表面出射时间分布可能展宽。因此产额和 FWHM 天然存在 trade-off:

```text
thicker Li -> higher neutron yield, larger temporal broadening
thinner Li -> lower neutron yield, shorter pulse
```

论文主线可以写为:

> We perform an end-to-end EPOCH-Geant4 Bayesian optimization of a Li-converter neutron source driven by TNSA protons from CH foils, revealing the trade-off between neutron yield and the neutron pulse duration at the converter exit.

---

## 2. 总体工作流

```text
Input parameters x
    |
    v
EPOCH 2D simulation
    laser + CH foil -> proton phase space
    |
    v
Phase-space exporter
    x, y, px, py, energy, weight, time
    |
    v
Geant4 simulation
    protons -> Li converter -> neutrons
    |
    v
Objectives
    Y_n, tau_exit,FWHM
    |
    v
Bayesian optimization
    propose next x
```

推荐分阶段执行:

```text
Stage 0: Geant4 monoenergetic proton benchmark
Stage 1: EPOCH baseline CH TNSA
Stage 2: EPOCH-Geant4 coupling
Stage 3: initial LHS/Sobol sampling
Stage 4: BO optimization
Stage 5: selected 3D validation
Stage 6: paper figures and analysis
```

---

## 3. 主参数设置

### 3.1 固定物理常数

```text
laser wavelength lambda0 = 0.8 um
laser incidence          = normal incidence
laser polarization       = linear
laser spatial profile    = Gaussian
laser temporal profile   = Gaussian
focal spot radius w0     = 5 um
focus position           = CH front surface
```

临界密度:

```text
n_c = epsilon0 * m_e * omega0^2 / e^2
```

对 `lambda0 = 0.8 um`, 约为:

```text
n_c ≈ 1.74e21 cm^-3
```

### 3.2 主 BO 变量

第一版建议只优化 5 个变量:

| 符号 | 参数 | 范围 | 备注 |
|---|---|---:|---|
| `I0` | 激光峰值强度 | `5e19 - 3e20 W/cm2` | 约 `a0 = 4.8 - 11.8` |
| `tau` | 激光脉宽 FWHM | `20 - 60 fs` | 高斯时间包络 |
| `d_CH` | CH 靶厚度 | `0.2 - 3.0 um` | 靶太厚会降低 TNSA 效率 |
| `L_pre` | 前表面预等离子体尺度 | `0 - 1.0 um` | 指数型 preplasma |
| `D_Li` | Li 转换靶厚度 | `0.05 - 3.0 cm` | Geant4 参数 |

主方案中固定 CH 密度, 焦斑半径和 Li 材料。这样 BO 维度不高, 第一轮更容易收敛。

### 3.3 可选扩展变量

如果第一版跑通后想提升文章完整度, 可加入:

| 参数 | 范围 | 建议 |
|---|---:|---|
| `n_e_CH` | `100 - 400 nc` | 第二轮再加, 第一轮固定 |
| `w0` | `3 - 7 um` | 若扫 `w0`, 建议固定激光能量 |
| `z_gap` | `0.5 - 3 cm` | CH 源到 Li converter 距离 |
| `theta_accept` | `10 - 30 deg` | 若优化前向中子产额 |

第一篇不建议一开始加入这些变量。

---

## 4. EPOCH 模拟设置

### 4.1 2D baseline box

推荐 2D 笛卡尔坐标:

```text
x direction: laser propagation direction
y direction: transverse direction
```

模拟盒子:

```text
x_min = 0 um
x_max = 80 um
y_min = -25 um
y_max = 25 um

box size = 80 um x 50 um
```

靶位置:

```text
CH front surface = x = 20 um
CH rear surface  = x = 20 um + d_CH
laser focus      = x = 20 um
proton diagnostic plane = x = 65 um
```

结束时间:

```text
t_end = 0.8 - 1.0 ps
```

这个时间通常足够让主要 TNSA 质子离开靶后区并通过诊断面。

### 4.2 2D resolution

主推荐:

```text
dx = 0.01 um
dy = 0.05 um

Nx = 8000
Ny = 1000
```

若算力压力较大, 可做预扫描:

```text
dx = 0.02 um
dy = 0.05 um

Nx = 4000
Ny = 1000
```

但正式 BO 数据建议至少保证 longitudinal direction 足够解析靶厚和 sheath field。

### 4.3 boundary conditions

```text
field boundary: absorbing / open
particle boundary: open
```

避免粒子和电磁波从边界反射回模拟区。

### 4.4 CH 靶材料

主方案使用 fully ionized stoichiometric CH:

```text
species:
  electron
  C6+
  H+
```

固定电子密度:

```text
n_e = 200 nc
```

由于 CH 中 `n_C = n_H`, 且 fully ionized carbon 给 6 个电子:

```text
n_e = 6 n_C + n_H = 7 n_CH
n_C = n_H = n_e / 7
```

所以:

```text
n_C6+ = 28.57 nc
n_H+  = 28.57 nc
n_e   = 200 nc
```

初始温度:

```text
T_e = 10 eV
T_i = 10 eV
```

macro-particles:

```text
electrons: 16 - 32 ppc
C6+      : 16 - 32 ppc
H+       : 16 - 32 ppc
```

正式结果建议用 32 ppc; BO 初期可用 16 ppc 降低成本。

### 4.5 preplasma 设置

只在 CH 前表面设置指数型 preplasma:

```text
n_e(x) = n0 * exp((x - x_front) / L_pre), x < x_front
```

其中:

```text
x_front = 20 um
n0 = 200 nc
L_pre in [0, 1.0] um
```

为了避免无限长低密度尾巴, 设置 cutoff:

```text
n_e < 0.01 nc -> set to vacuum
```

rear side 保持 sharp boundary:

```text
x_front + d_CH < x -> vacuum
```

第一版不设置 rear-side preplasma。

### 4.6 激光设置

固定:

```text
lambda0 = 0.8 um
w0 = 5 um
linear polarization
normal incidence
Gaussian transverse profile
Gaussian temporal profile
```

BO 变量:

```text
I0  in [5e19, 3e20] W/cm2
tau in [20, 60] fs
```

近似关系:

```text
a0 ≈ 0.855 * sqrt(I0[10^18 W/cm2] * lambda0[um]^2)
```

因此:

```text
I0 = 5e19 W/cm2  -> a0 ≈ 4.8
I0 = 2e20 W/cm2  -> a0 ≈ 9.7
I0 = 3e20 W/cm2  -> a0 ≈ 11.8
```

baseline point:

```text
I0   = 2e20 W/cm2
tau  = 30 fs
d_CH = 1.0 um
L_pre = 0.2 um
D_Li = 1.0 cm
```

### 4.7 EPOCH 输出

必须输出通过诊断面的质子 phase space, 不只输出能谱。

诊断面:

```text
x_diag = 65 um
```

每个质子记录:

```text
x, y
px, py
energy
weight
arrival_time
```

若是 3D EPOCH, 记录:

```text
x, y, z
px, py, pz
energy
weight
arrival_time
```

同时记录源端诊断量:

```text
E_p,max
N_p(Ep > 2 MeV)
N_p(Ep > 5 MeV)
N_p(Ep > 10 MeV)
laser-to-proton conversion efficiency
proton pulse duration at x_diag
```

这些不是 BO 目标, 但用于后续物理解释。

---

## 5. 2D EPOCH 到 3D Geant4 源的处理

2D PIC 输出本质是每单位长度的粒子数。接入 3D Geant4 时有两种方案。

### 5.1 第一阶段: axisymmetric reconstruction

把 2D 的 `y` 和横向动量视为径向分布, 随机采样方位角 `phi` 重建:

```text
r = |y|
phi ~ Uniform(0, 2pi)

y_3D = r cos(phi)
z_3D = r sin(phi)
```

横向动量同样旋转:

```text
p_perp = py
py_3D = p_perp cos(phi)
pz_3D = p_perp sin(phi)
px_3D = px
```

优点: 简单, 适合 BO 阶段。

缺点: 绝对粒子数需要几何归一化, 最终需要 3D EPOCH 验证。

### 5.2 最终结果: 3D EPOCH validation

文章的最终绝对产额建议来自 3D EPOCH + Geant4。2D 结果用于趋势发现和 BO 探索, 3D 结果用于验证 Pareto ranking。

---

## 6. Geant4 模拟设置

### 6.1 几何

Geant4 坐标:

```text
x direction: proton beam direction
```

几何:

```text
source plane at x = 0
vacuum gap: 1 cm
Li converter front surface: x = 1 cm
Li converter thickness: D_Li
detector plane: 10 cm behind Li rear surface
```

注意: detector plane 主要用于统计后向可用中子数和 TOF 展宽诊断, 不用于主优化的脉宽目标。由于 1-10 MeV 中子在 10 cm 飞行距离上的 TOF 色散可达数 ns, `tau_det` 会主要反映中子能谱宽度, 而不是 Li converter 内部的产生/输运展宽。

Li converter:

```text
material = pure 7Li
density = 0.534 g/cm3
shape = cylinder
radius = 2 cm
thickness = D_Li
```

主方案用纯 `7Li`, 因为主反应清楚, benchmark 容易。后续可加入 natural Li。

探测面:

```text
shape = disk
radius = 2 cm
position = Li rear surface + 10 cm
```

探测面记录所有穿过的中子:

```text
energy
arrival_time
position
direction
weight
```

同时必须记录 Li 后表面出射中子:

```text
exit_time at Li rear surface
exit_energy
exit_position
exit_direction
weight
```

同时记录 4pi birth neutrons:

```text
neutron birth time
birth position
birth energy
birth direction
```

### 6.2 物理列表

推荐:

```text
QGSP_BIC_AllHP
```

或:

```text
QGSP_BIC_HP
```

要求:

```text
enable high-precision neutron transport
enable proton inelastic reactions on Li
use ParticleHP / TENDL-like evaluated data if available
```

必须先做单能质子 benchmark, 确认 `7Li(p,n)` 阈值和产额趋势合理。

### 6.3 单能 proton benchmark

在接 EPOCH 前, 先用 monoenergetic proton beam 打 Li slab:

```text
Ep = 1.5, 2, 3, 5, 10, 20, 40 MeV
D_Li = 0.1, 0.5, 1.0 cm
beam = pencil beam
```

检查:

```text
Ep < 1.88 MeV -> neutron yield ≈ 0
Ep > 2 MeV -> neutron yield starts rising
yield vs Ep trend reasonable
neutron energy spectrum reasonable
relative Monte Carlo error < 5%
```

如果 benchmark 不通过, 不要进入 EPOCH-Geant4 coupling。

### 6.4 Geant4 统计误差

每个 BO 点 Geant4 初期可以低统计:

```text
relative error target = 5 - 10%
```

最终 Pareto 点高统计:

```text
relative error target < 3 - 5%
```

记录:

```text
N_primary_protons
N_neutrons_total
N_neutrons_detector
N_neutrons_exit
relative error
```

---

## 7. 优化目标定义

### 7.1 主目标

目标 1: 中子产额

```text
Y_n = number of neutrons crossing the Li rear surface
```

建议同时记录归一化产额:

```text
Y_n_norm = Y_n / E_L
```

其中 `E_L` 是激光能量。因为 BO 扫 `I0` 和 `tau`, 激光能量会变化; 若只优化绝对 `Y_n`, BO 可能倾向于更高激光能量。

第一篇可采用:

```text
maximize log10(Y_n_norm)
```

同时在图中报告绝对 `Y_n`。

目标 2: 中子脉宽

```text
tau_FWHM = FWHM of neutron exit-time distribution at the Li rear surface
```

也可报告:

```text
tau_birth = FWHM of neutron birth-time distribution inside Li
tau_exit  = FWHM at Li rear surface
tau_det   = FWHM at detector plane
```

主优化用:

```text
tau_FWHM = tau_exit
```

### 7.2 为什么不用 detector-plane FWHM 作为主目标

`tau_det` 会受到真空飞行距离上的 TOF 色散强烈影响。举例来说, 1 MeV 中子速度约为 1.4 cm/ns, 10 MeV 中子速度约为 4.4 cm/ns; 在 10 cm 飞行距离上, 单纯能谱导致的到达时间差就可达到数 ns。而 Li converter 内部的产生/出射时间展宽通常是亚 ns 到 ns 量级, 很容易被 TOF 色散淹没。

因此主优化目标使用:

```text
tau_exit = FWHM at Li rear surface
```

这样它更直接反映 Li 厚度、质子慢化、核反应发生位置和中子在 converter 内部输运造成的时间展宽。

`tau_det` 仍然保留, 但作为应用端 TOF 诊断量:

```text
tau_det = convolution of source/converter pulse duration and neutron spectral TOF dispersion
```

### 7.3 多目标形式

推荐使用多目标 BO:

```text
objective 1: maximize log10(Y_n / E_L)
objective 2: minimize tau_FWHM
```

得到 Pareto front:

```text
high yield, longer FWHM
low yield, shorter FWHM
knee point: best compromise
```

不要一开始把两个目标硬合成一个 score。Pareto front 更好写文章。

---

## 8. BO 设置

### 8.1 参数空间

```text
x = [I0, tau, d_CH, L_pre, D_Li]
```

范围:

```text
I0    = [5e19, 3e20] W/cm2
tau   = [20, 60] fs
d_CH  = [0.2, 3.0] um
L_pre = [0.0, 1.0] um
D_Li  = [0.05, 3.0] cm
```

建议对 `I0`, `d_CH`, `D_Li` 使用 log 或 quasi-log sampling:

```text
I0:    log scale
d_CH:  log scale optional
D_Li:  log scale
tau:   linear
L_pre: linear
```

### 8.2 初始采样

```text
initial design = Sobol or Latin hypercube sampling
N_initial = 30 - 40
```

Sobol 更适合覆盖连续空间。

### 8.3 BO 迭代

```text
N_BO = 30 - 50
total 2D EPOCH evaluations = 60 - 90
```

多目标 acquisition:

```text
EHVI, expected hypervolume improvement
```

如果工具不方便, 可使用 ParEGO:

```text
random scalarization of objectives
single-objective GP/EI at each iteration
```

### 8.4 噪声处理

EPOCH 有粒子噪声, Geant4 有 Monte Carlo 噪声。因此 GP 中应加入 observation noise:

```text
sigma_noise != 0
```

对 Geant4 输出, 保存统计误差:

```text
Y_n ± delta_Y_n
```

BO 早期不需要极高统计, 但 Pareto 点必须高统计复跑。

### 8.5 失败点处理

若某个 EPOCH 点质子能量不足:

```text
E_p,max < 2 MeV
```

则 Geant4 可以跳过或快速判定:

```text
Y_n = 0
tau_FWHM = undefined / penalty
```

BO 中给 penalty:

```text
log10(Y_n / E_L) = very low value
tau_FWHM = large penalty
```

---

## 9. 3D 验证

### 9.1 为什么需要 3D

2D EPOCH 的粒子数和发散结构不等同于真实 3D。第一篇如果想投到比较好的期刊, 至少需要几个 3D 点验证趋势和 ranking。

### 9.2 3D 选择点

从 2D BO/Pareto front 中选 4-5 个点:

```text
1. baseline point
2. maximum Y_n point
3. minimum tau_FWHM point
4. Pareto knee point
5. one control/failure point
```

若算力允许, 增加:

```text
6. second Pareto point
7. high-intensity thick-Li point
8. thin-Li short-pulse point
```

### 9.3 3D EPOCH 设置

推荐初始 3D box:

```text
x = 0 - 60 um
y = -15 - 15 um
z = -15 - 15 um
```

靶位置:

```text
CH front surface = x = 15 um
CH rear surface  = x = 15 um + d_CH
diagnostic plane = x = 50 um
```

分辨率:

```text
dx = 0.03 - 0.05 um
dy = 0.08 - 0.12 um
dz = 0.08 - 0.12 um
```

particles:

```text
8 - 16 ppc per species
```

正式 3D 点若可承受, 提高到:

```text
dx = 0.025 - 0.03 um
dy = dz = 0.06 - 0.08 um
16 ppc
```

---

## 10. 数据管理

每个样本一个目录:

```text
runs/
  sample_000/
    params.json
    epoch_input.deck
    epoch_outputs/
    proton_phase_space.h5
    geant4_input.json
    geant4_outputs/
    objectives.json
```

`params.json`:

```json
{
  "I0_Wcm2": 2.0e20,
  "tau_fs": 30.0,
  "d_CH_um": 1.0,
  "L_pre_um": 0.2,
  "D_Li_cm": 1.0
}
```

`objectives.json`:

```json
{
  "Y_n_exit": 1.23e8,
  "Y_n_exit_per_J": 4.1e6,
  "Y_n_detector": 8.7e7,
  "Y_n_detector_per_J": 2.9e6,
  "Y_n_total": 9.8e8,
  "tau_exit_FWHM_ps": 280.0,
  "tau_detector_FWHM_ps": 5200.0,
  "geant4_rel_error": 0.035,
  "Ep_max_MeV": 22.5,
  "Np_gt_2MeV": 3.2e11
}
```

所有 BO 输入输出必须可复现, 否则后期写文章会非常痛苦。

---

## 11. 关键检查清单

### 11.1 Geant4 检查

```text
[ ] 1.5 MeV proton on Li gives nearly zero neutrons
[ ] 2-3 MeV proton starts producing neutrons
[ ] yield increases reasonably with proton energy
[ ] neutron time and energy tallies are correct
[ ] relative statistical error is recorded
[ ] Li thickness scan shows yield-FWHM trade-off
```

### 11.2 EPOCH 检查

```text
[ ] baseline CH target produces Ep,max > 10 MeV
[ ] proton spectrum is physically reasonable
[ ] target is not numerically destroyed before main pulse
[ ] boundary reflections are negligible
[ ] diagnostic plane captures outgoing protons
[ ] proton phase-space exporter conserves total weight
```

### 11.3 Coupling 检查

```text
[ ] imported Geant4 proton spectrum matches EPOCH exported spectrum
[ ] imported angular distribution is reasonable
[ ] particle weights are handled correctly
[ ] time offset is consistently defined
[ ] 2D-to-3D reconstruction is documented
```

---

## 12. 最终图表设计

### Figure 1: workflow

```text
laser -> CH foil -> TNSA protons -> Li converter -> neutron detector
```

展示 EPOCH 和 Geant4 的耦合。

### Figure 2: Geant4 benchmark

```text
monoenergetic proton energy vs neutron yield
neutron yield threshold near 1.88 MeV
```

### Figure 3: baseline EPOCH result

```text
proton energy spectrum
proton angular distribution
proton phase-space snapshot
```

### Figure 4: BO convergence

```text
best hypervolume vs iteration
best yield vs iteration
best FWHM vs iteration
```

### Figure 5: Pareto front

```text
x-axis: tau_FWHM
y-axis: log10(Y_n / E_L)
```

标出:

```text
best-yield point
best-FWHM point
knee point
baseline point
```

### Figure 6: neutron time profiles

比较:

```text
best-yield
best-FWHM
knee
baseline
```

### Figure 7: physical interpretation

可画:

```text
D_Li vs yield/FWHM
I0/tau/d_CH sensitivity
proton Ep_max vs neutron yield
Np(Ep>2MeV) vs neutron yield
```

### Figure 8: 3D validation

```text
2D-predicted Pareto points vs 3D Geant4 results
```

---

## 13. 推荐时间表

### Month 1

```text
Geant4 Li(p,n) benchmark
EPOCH baseline CH TNSA
phase-space export format finalized
```

### Month 2

```text
EPOCH-Geant4 coupling
initial 30-40 Sobol/LHS samples
low-stat Geant4 runs
```

### Month 3

```text
BO 30-50 iterations
Pareto front preliminary result
high-stat Geant4 rerun of best points
```

### Month 4

```text
3D EPOCH validation points
final high-stat Geant4
figures and analysis
```

### Month 5-6

```text
paper writing
extra sensitivity checks
revision-quality plots
```

现实估计:

```text
fast version: 3-4 months
solid version: 5-6 months
```

---

## 14. 预期论文定位

如果只做 2D EPOCH + Geant4 + BO:

```text
NIM A
Radiation Physics and Chemistry
Laser and Particle Beams
```

如果加入:

```text
Geant4 benchmark
yield-FWHM Pareto
high-stat final Geant4
selected 3D EPOCH validation
clear physical interpretation
```

可以考虑:

```text
Physics of Plasmas
High Energy Density Physics
High Power Laser Science and Engineering
```

这个项目的主要价值不是提出新靶型, 而是建立一个清楚的 end-to-end optimization workflow:

```text
laser-plasma proton source -> nuclear converter -> application-relevant neutron pulse metrics
```

---

## 15. 第一版最小可执行方案

如果要马上开始, 第一周就做这 4 件事:

```text
1. Geant4: monoenergetic 2, 5, 10, 20 MeV protons on 1 cm Li
2. EPOCH: baseline CH target
   I0 = 2e20 W/cm2
   tau = 30 fs
   d_CH = 1 um
   L_pre = 0.2 um
3. export proton phase space at x = 65 um
4. inject exported protons into Geant4 1 cm Li and get Y_n_exit, tau_exit,FWHM
```

只要这四步跑通, 项目就已经成立。

---

## 16. Baseline parameter card

最终推荐 baseline:

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
  front surface x = 20 um
  d_CH = 1.0 um
  n_e = 200 nc
  n_C6+ = 28.57 nc
  n_H+ = 28.57 nc
  T_e = T_i = 10 eV
  L_pre = 0.2 um

EPOCH 2D:
  box = 80 um x 50 um
  dx = 0.01 um
  dy = 0.05 um
  t_end = 1 ps
  diagnostic plane x = 65 um

Geant4:
  source plane x = 0
  Li front x = 1 cm
  Li thickness D_Li = 1 cm
  Li radius = 2 cm
  detector plane = 10 cm behind Li rear
  detector radius = 2 cm
  physics list = QGSP_BIC_AllHP or QGSP_BIC_HP

Objectives:
  maximize log10(Y_n_exit / E_L)
  minimize tau_exit_FWHM

Additional diagnostics:
  Y_n_detector at 10 cm behind Li rear
  tau_detector_FWHM for TOF/spectral broadening analysis only
```
