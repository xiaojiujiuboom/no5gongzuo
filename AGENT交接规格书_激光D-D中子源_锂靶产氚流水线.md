# AGENT 交接规格书
## 激光驱动 D-D 脉冲中子源 → 外部锂靶产氚 中子学流水线（一个月小论文）

**读者：负责实现的编码 Agent。** 本文给出精确到公式、常数、文件 schema、代码骨架与验证锚点的规格。
凡标 **[VERIFY]** 处必须对照权威来源核实后再用；凡标 **[GATE]** 处是不通过就不许往下走的验收关。
物理量单位在每处显式标注，**不要凭记忆改单位或 API 字符串**。

---

## 0. 给 Agent 的工作准则

1. **先立契约后写模块**：第 4 节两个 HDF5 接口文件的 schema 是全项目地基，先实现读写与校验，三模块即可并行。
2. **每个模块自带验证**：见第 8 节的 [GATE]。没过关的模块产物不许进入下游。
3. **归一化是生死线**：任何"人为放大反应概率/截面偏置"都必须在最终产额里除回去。绝对产额虚高几个量级 = 毁灭性错误。
4. **不确定就查文档、不要脑补**：OpenMC 的 score 名、MT 号、Bosch-Hale 系数，一律现查现核。
5. **单位统一约定**：粒子能量内部计算用 **MeV**；写入 OpenMC 源时转 **eV**；截面内部用 **mb 或 cm²**（1 mb = 1e-27 cm²，1 barn = 1e-24 cm²）；长度 **cm**；阻止本领 **MeV/cm**。

---

## 1. 科学目标（唯一结论）

回答：**激光束-靶产生的"畸变谱"中子（多普勒展宽 + 前向各向异性），打进锂靶后的空间产氚率 TPR，
与理想各向同性单能 2.45 MeV 源相比差多少、差在哪？**

**预期物理图像（也是论文卖点，代码要能显式呈现出来）：**
- **⁶Li(n,α)T 主通道**：靠中子慢化后的低能中子，对源谱细节**钝感** → Case A ≈ Case B。
- **⁷Li 产氚阈值通道**：当前 OpenMC `Li7.h5` 中 `H3-production` 对应 MT205 `(n,Xt)` 总产氚截面，294 K 阈值为 **3.1454 MeV**。热核 D-D 中子 2.45 MeV 卡在阈值下；
  只有**束-靶前向被顶过 3.1454 MeV 的高能尾**能开启它 → 对"谱里多少料在 3.1454 MeV 以上"和"朝哪个方向"极度敏感。
- 因此 Case A 与 Case B 的 TPR 差异应**集中在 ⁷Li 通道、集中在 >3.1454 MeV 能段、且各向异性**。注意：MT205 是总产氚 `(n,Xt)`，不是排他单一 `(n,n'alpha)T` tally；在几 MeV 的 `Li7` 区间可表述为由阈值产氚通道主导。

---

## 2. 物理参考表（Agent 的 ground truth，实现时按此核对）

### 2.1 常数与质量（能量当量）
| 量 | 值 |
|---|---|
| 氘核质量 m_d·c² | 1875.613 MeV |
| 中子质量 m_n·c² | 939.565 MeV |
| ³He 质量 m_He3·c² | 2808.391 MeV |
| ⁴He 质量 m_He4·c² | 3727.379 MeV |
| N_A | 6.02214e23 /mol |
| 1 barn | 1e-24 cm² ；1 mb = 1e-27 cm² |

### 2.2 反应
| 反应 | Q 值 | 备注 |
|---|---|---|
| D(d,n)³He | **+3.269 MeV** | 本项目中子来源；E_d→0 时中子能 →2.45 MeV |
| D(d,p)T | +4.033 MeV | 另一分支，不产中子，可忽略（只影响氘消耗，本文不算） |
| ⁶Li(n,α)T | +4.78 MeV | 无阈值，热中子截面极大（~940 barn @2200 m/s） |
| ⁷Li MT205 `(n,Xt)` total tritium production | library-defined | OpenMC HDF5 294 K 阈值 **3.1454 MeV**；几 MeV 区间由阈值产氚通道主导 |

### 2.3 D(d,n)³He 截面：Bosch-Hale 参数化 **[VERIFY]**
以质心系能量 E（**keV**）为自变量，截面（**mb**）：
```
σ(E) [mb] = S(E) / ( E · exp(B_G / sqrt(E)) )
S(E) = A1 + E*(A2 + E*(A3 + E*(A4 + E*A5)))         # 该反应分母 Padé 项为 1
```
系数（Bosch & Hale, Nuclear Fusion 32 (1992) 611，²H(d,n)³He 分支）：
```
B_G = 31.3970
A1 = 5.3701e4
A2 = 3.3027e2
A3 = -1.2706e-1
A4 = 2.9327e-5
A5 = -2.5151e-9
```
适用范围约 0.5–4900 keV(CM)。
**[VERIFY][GATE-σ]**：实现后必须对照 ENDF/B 或 NRL Formulary 的 D-D(n 分支) 截面在至少两个能量点核对（数量级+趋势）。
若对不上，优先怀疑：(a) 用了 lab 能量而非 CM 能量（对等质量 **E_cm = E_lab/2**）；(b) 系数抄错。**核对通过前不得进入产额积分。**

---

## 3. 仓库结构与环境

```
project/
├── README.md
├── requirements.txt
├── config.yaml                # 全局参数：靶厚、锂靶尺寸、富集度、a0 扫描表、库名等
├── data/
│   ├── stopping_D_in_CD2.csv  # 阻止本领表 (E_MeV, S_MeVcm)  ← 由 SRIM/PSTAR 生成
│   └── xs/                     # OpenMC 核数据 (FENDL-3.2 HDF5 等)
├── interfaces/
│   └── schema.py              # 两个 h5 的读写 + 校验（先写这个）
├── moduleA_pic/
│   ├── extract_epoch.py       # SDF → deuteron_beam.h5
│   └── parametric_beam.py     # 降级预案：参数化 TNSA 氘谱 → deuteron_beam.h5
├── moduleB_source/
│   ├── cross_section.py       # Bosch-Hale σ_DD(E_cm)
│   ├── stopping.py            # S(E) 读表+插值
│   ├── kinematics.py          # CM 各向同性 → lab boost
│   ├── thick_target.py        # 产额积分 + 反应能量采样
│   └── build_source.py        # deuteron_beam.h5 → neutron_source.h5 (+ 能谱/角分布图)
├── moduleC_openmc/
│   ├── materials.py
│   ├── geometry.py
│   ├── source.py              # Case A (理想) / Case B (畸变) 两种源
│   ├── tallies.py
│   ├── run.py                 # 组装+运行
│   └── postprocess.py         # 归一化 + 出图 + A/B 比对
└── outputs/
    ├── figures/
    └── tables/
```

**环境（requirements.txt）**：`openmc`, `numpy`, `scipy`, `h5py`, `pandas`, `matplotlib`, `pyyaml`。
- OpenMC 建议 conda 安装：`conda install -c conda-forge openmc`。
- 核数据：下载 OpenMC 格式的 **FENDL-3.2 HDF5**（主用）；`ENDF/B-VIII.0` 或 `VIII.1`、`JEFF-3.3`（多库比对用，可后补）。
  设环境变量 `OPENMC_CROSS_SECTIONS=/path/to/cross_sections.xml`。
- **[GATE-env]**：跑通 OpenMC 自带最小算例（一个球+点源）拿到非零 keff/flux，再开工。

---

## 4. 接口契约（两个 HDF5，先实现 `interfaces/schema.py`）

### 4.1 `deuteron_beam.h5`（模块 A 产出）
| dataset | shape | 单位 | 说明 |
|---|---|---|---|
| `E`     | (N,)  | MeV  | 氘动能 |
| `dir`   | (N,3) | -    | 单位方向矢量 (nx,ny,nz)，束轴约定为 +z |
| `weight`| (N,)  | -    | 每宏粒子代表的**真实氘数/shot** |
| `t`     | (N,)  | ns   | 可选，氘到达采样面时间；缺省填 0 |
| attrs: `n_deuterons_total` | scalar | - | 每 shot 总氘数 = sum(weight)，冗余存便于校验 |

### 4.2 `neutron_source.h5`（模块 B 产出）
| dataset | shape | 单位 | 说明 |
|---|---|---|---|
| `E`     | (M,)  | MeV  | 中子能量 |
| `dir`   | (M,3) | -    | 单位方向矢量 |
| `weight`| (M,)  | -    | 每中子代表的**真实中子数/shot** |
| `t`     | (M,)  | ns   | 中子发射时间 |
| attrs: `Y_total` | scalar | - | 每 shot 总中子数 = sum(weight)；OpenMC 归一化要用 |

**校验函数**（schema.py 内）：加载后断言无 NaN、`dir` 归一化（|dir|≈1）、`weight`≥0、attrs 与 sum 一致。

---

## 5. 模块 A —— 氘束（EPOCH 或参数化）

### 5.1 主路径：EPOCH
- EPOCH 2D，靶 3–5 μm 固体密度 CD₂，PPC≥100，入射 I~1e19 W/cm²（`a0`≈5 起）。
- 靶后 x≈20 μm 虚拟面，在 ~0.8–1 ps 导出穿面氘的 `E, dir, weight`。
- `extract_epoch.py`：SDF reader → 写 `deuteron_beam.h5`。
- **红线**：靶厚 ≤ 5 μm，绝不把 mm 塞进 PIC。

### 5.2 降级预案：`parametric_beam.py`（**第 1 周就实现，保下游不等 PIC**）
参数化 TNSA 氘谱：
```
dN/dE ∝ exp(-E / kT),  E ∈ [E_min, E_max],  kT ∈ [1,3] MeV   # 从 config.yaml 读
方向：前向锥，半角 θ_max ∈ [10°,20°]，锥内 (近似) 均匀或 ∝cosθ
```
采样 N 个氘，dir 绕 +z 采样，weight 归一到给定总氘数（如 1e12/shot，量级即可，绝对值由归一化管）。
产出同格式 `deuteron_beam.h5`，attrs 标注 `source_type='parametric'`。

---

## 6. 模块 B —— 半解析厚靶 D-D 中子源项（**技术核心，替代 Geant4**）

> 物理：MeV 氘进入固体 CD₂，一边慢化一边与静止靶氘聚变。产额由 σ/S 沿射程积分决定；
> 中子能量-角度由两体运动学 boost 决定（前向顶高、后向压低）——这就是畸变谱来源。

### 6.1 靶介质常数（CD₂）**[VERIFY 密度]**
```
ρ_CD2 ≈ 1.06 g/cm³            # 氘代聚乙烯，[VERIFY] 可取 1.06–1.13
M_CD2unit = 12.011 + 2*2.014 = 16.039 g/mol
n_unit = ρ*N_A/M_CD2unit ≈ 3.98e22 /cm³
n_D    = 2*n_unit ≈ 7.95e22 /cm³      # 靶氘数密度（产额公式用它）
n_C    = 1*n_unit ≈ 3.98e22 /cm³
```

### 6.2 阻止本领 `stopping.py` **[VERIFY 数据源]**
- 生成 D 在 CD₂ 的 S(E) 表 `data/stopping_D_in_CD2.csv`，覆盖 E∈[10 keV, E0_max]。
- 数据源三选一：
  1. **SRIM** 直接导 D-in-CD2 电子阻止（推荐，最省心）。
  2. **PSTAR(质子)同速度换算**：`S_D(E_d) ≈ S_p(E_d/2)`（同速度电子阻止近似相等；E_p = E_d·m_p/m_d = E_d/2）；
     化合物用 Bragg 加和（按各元素原子分数对每原子阻止截面加权）。
  3. Andersen–Ziegler 解析式（次选）。
- 核阻止在 >100 keV 可忽略；低于此可选择性加。
- 实现：读表 + 单调三次样条插值，返回 S(E) [MeV/cm]。

### 6.3 截面 `cross_section.py`
实现 6.3 的 Bosch-Hale。输入 E_cm[keV]，输出 σ[mb]（再转 cm²）。过 **[GATE-σ]** 才算完成。

### 6.4 两体运动学 `kinematics.py`（CM 各向同性 → lab boost）
```python
# 非相对论足够（β~0.09，误差<0.5%）。全部用能量当量 mc² (MeV)。
def dd_neutron_lab(E_d_MeV, dir_d_unit, rng):
    mdc2, mnc2, mHe3c2 = 1875.613, 939.565, 2808.391
    Q = 3.269
    # CM 速度 (β单位)，沿 dir_d
    beta_cm = 0.5 * (2*E_d_MeV/mdc2)**0.5          # V_cm = v_d/2
    # 产物可用动能：E_cm_rel + Q，其中 E_cm_rel = E_d/2 (等质量)
    E_avail = 0.5*E_d_MeV + Q
    # n 与 He3 反比质量分能：E_n* = E_avail * mHe3/(mn+mHe3)
    E_n_cm = E_avail * mHe3c2/(mnc2+mHe3c2)
    beta_n_cm = (2*E_n_cm/mnc2)**0.5
    # CM 各向同性方向
    u = rng.normal(size=3); u /= (u@u)**0.5         # 或用 cosθ 均匀+φ 均匀
    # lab β 矢量 = β_cm*dir_d + β_n_cm*u
    beta_lab = beta_cm*dir_d_unit + beta_n_cm*u
    b2 = beta_lab@beta_lab
    E_n_lab = 0.5*mnc2*b2                            # 非相对论
    dir_n = beta_lab/ b2**0.5
    return E_n_lab, dir_n
```
**[GATE-kin]** 数值自检（必须复现）：
- `E_d→0`：`E_n_lab → 2.45 MeV`（任意方向都接近）。
- `E_d=1 MeV`，**前向**（u 与 dir_d 同向）：`E_n_lab ≈ 4.14 MeV`（>3.1454，开 ⁷Li MT205 产氚）。
- `E_d=1 MeV`，**后向**：`E_n_lab ≈ 1.76 MeV`。
对不上说明 boost 写错，禁止进入 build_source。
（可选精化：D-D 的 CM 角分布在 >1 MeV 有轻微 (1+a·cos²θ) 各向异性，先按各向同性做，讨论里注明。）

### 6.5 产额与反应能量采样 `thick_target.py`
```
每入射氘的中子产额:  Y(E0) = ∫_0^{E0} n_D * σ_DD(E_cm(E)) / S(E) dE     # E 为氘 lab 能量, E_cm=E/2
反应发生处氘能量的 pdf ∝ σ_DD(E_cm)/S(E)  在 [0, E0]
```
- 在能量网格上算被积函数，`Y = trapz`。
- 反应能量采样：对 pdf 归一 → CDF → 逆变换抽样，得该氘"聚变时刻的能量 E_react"。
- **单位自检**：`n_D[cm^-3] * σ[cm²] / S[MeV/cm]` → `1/MeV`，积分 dE → 无量纲。✓
- 假设氘慢化沿直线、方向不变（小角散射可忽略），用 PIC 给的入射方向作 dir_d。

### 6.6 组装 `build_source.py`
```
读 deuteron_beam.h5
for 每个氘 (E0, dir_d, w_d):
    Y = thick_target_yield(E0)                    # 该氘期望产中子数
    E_react = sample_reaction_energy(E0)          # 聚变时氘能量
    E_n, dir_n = dd_neutron_lab(E_react, dir_d, rng)
    t_n = t_d (+ 可选 ps-ns 展宽)
    记录一条中子: E=E_n, dir=dir_n, weight = w_d * Y, t=t_n
（可每个氘发多条中子以降方差，weight 相应均分）
sum(weight) → Y_total 写入 attrs
存 neutron_source.h5，并出两张图:
  fig1 中子能谱（应见 2.45 MeV 峰 + 前向高能尾）
  fig2 中子角分布（应前向偏置）
```
**[GATE-B]**：
- fig1 能谱有 2.45 MeV 峰且高能侧拖尾越过 3.1454 MeV；
- fig2 明显前向偏置；
- `Y_total/n_deuterons_total`（每氘平均产额）量级与文献厚靶 D-D 产额一致（**[VERIFY]** 对照厚靶 D-D 产额表，典型 ~1e-6…1e-5/氘 量级，具体核）。
三者全过才算模块 B 完成。**这两张图是论文主结果之一。**

---

## 7. 模块 C —— OpenMC 锂靶输运与 TPR

### 7.1 材料 `materials.py` **[VERIFY 富集/密度]**
```python
import openmc
def make_lithium(li6_atpct):   # li6_atpct: 天然=7.59, 富集=90.0
    li = openmc.Material(name=f"Li_{li6_atpct}")
    li.add_nuclide('Li6', li6_atpct/100.0, 'ao')
    li.add_nuclide('Li7', (100-li6_atpct)/100.0, 'ao')
    li.set_density('g/cm3', 0.534)      # 金属锂
    return li
```
两套：天然 Li（Li6=7.59 at%）与富集（Li6=90 at%）各跑一遍。
（可选：靶内混铍做 (n,2n) 倍增剂，属第四阶段，不在本月必需。）

### 7.2 几何 `geometry.py`
- 锂圆柱：Ø20 cm × 高 20 cm（`config.yaml` 可调），外包真空边界（vacuum BC）。
- 中心留小腔（如 Ø1–2 cm）放源；源已是"CD₂ 表面飞出的中子"，故 CD₂ 靶本身在 Stage 3 可省略几何，只作点/小体源。
- 用 `openmc.ZCylinder` + 两个 `openmc.ZPlane` 组合；最外层设 `boundary_type='vacuum'`。

### 7.3 源 `source.py`（**关键：Case B 必须保留能量-角度相关**）
**Case A（理想基准）**：单一 `IndependentSource`
```python
srcA = openmc.IndependentSource()
srcA.space  = openmc.stats.Point((0,0,0))
srcA.angle  = openmc.stats.Isotropic()
srcA.energy = openmc.stats.Discrete([2.45e6], [1.0])   # eV！
```
**Case B（畸变源）**：**不要**用可分离的 E 与 Ω（会丢掉"前向=高能"的相关性）。
按极角 μ=cosθ（相对 +z 束轴）分 bin，每个 bin 建一个 IndependentSource，能谱是该 bin 内中子的谱：
```python
# 从 neutron_source.h5 读 E(MeV), dir, weight
mu = dir[:,2]                     # cosθ, 束轴=+z
bins = np.linspace(-1, 1, NB+1)   # NB≈10~20
sources = []
for i in range(NB):
    sel = (mu>=bins[i]) & (mu<bins[i+1])
    if sel.sum()==0: continue
    Ei = E[sel]*1e6               # MeV→eV
    wi = weight[sel]
    hist, edges = np.histogram(Ei, bins=NEbins, weights=wi)   # 该bin能谱
    s = openmc.IndependentSource()
    s.space  = openmc.stats.Point((0,0,0))
    s.angle  = openmc.stats.PolarAzimuthal(
                   mu=openmc.stats.Uniform(bins[i], bins[i+1]),
                   phi=openmc.stats.Uniform(0, 2*np.pi),
                   reference_uvw=(0,0,1))
    s.energy = openmc.stats.Tabular(edges, np.append(hist,0), interpolation='histogram')
    s.strength = wi.sum()          # bin 权重
    sources.append(s)
# settings.source = sources  (OpenMC 按 strength 归一)
```
**[VERIFY]** `PolarAzimuthal` / `Tabular` 的参数名、`interpolation` 取值对照当前 OpenMC 文档；能量单位 **eV**。

### 7.4 Tally `tallies.py`（**⁶Li 与 ⁷Li 必须分道**）
- 产氚用 **`score='H3-production'`**（汇总所有产氚反应，绕开 MT 记账坑）；用 **nuclide filter** 拆两核素。
  当前已核对 `Li7.h5`：该 score 对 `Li7` 对应 `reaction_205`/MT205/`(n,Xt)` 总产氚生产截面，阈值 3.1454 MeV，不写成排他单一反应道。
  **[VERIFY]** 确认安装版 OpenMC 支持该 score 名；若不支持，Li6 退回 `score='(n,t)'`/MT=105，Li7 用产氚 score 或对应 MT。
```python
t_li6 = openmc.Tally(name='TPR_Li6'); t_li6.nuclides=['Li6']; t_li6.scores=['H3-production']
t_li7 = openmc.Tally(name='TPR_Li7'); t_li7.nuclides=['Li7']; t_li7.scores=['H3-production']
# 空间分布：柱网格 mesh tally
mesh = openmc.RegularMesh(); mesh.dimension=[1,20,20]  # 或 CylindricalMesh 更贴几何
t_map = openmc.Tally(name='TPR_map'); t_map.filters=[openmc.MeshFilter(mesh)]; t_map.scores=['H3-production']
# 能量分辨：看 ⁷Li 贡献是否集中在 >3.1454 MeV
efilter = openmc.EnergyFilter(np.logspace(3, 7.3, 60))  # eV
t_li7_E = openmc.Tally(name='TPR_Li7_vsE'); t_li7_E.nuclides=['Li7']
t_li7_E.filters=[efilter]; t_li7_E.scores=['H3-production']
```
`settings`: `batches≈100`, `particles≈1e6`（先小后大），`run_mode='fixed source'`。

### 7.5 归一化与后处理 `postprocess.py`
- OpenMC tally 值是**每源中子**的量。
- **每 shot 氚数** = tally 值 × `Y_total`（来自 neutron_source.h5 的 attrs）。
- **A/B 对比用"每源中子 TPR"**（不乘 Y_total），这样隔离掉总产额差异、只比较**谱形畸变**的影响 —— 这正是论文要的量。
- 检查每个 tally 的相对统计误差 < 5%（不够就加 particles）。
- 出图：TPR(r,z) 云图；Case A vs B 的 ⁶Li/⁷Li 分道柱状；⁷Li 的 TPR-vs-能量曲线（标出 3.1454 MeV MT205 阈值线）；A−B 相对偏差谱。

**[GATE-C]**：⁶Li 通道 A≈B（差异小）；⁷Li 通道 A、B 差异明显且 B 的贡献集中在 >3.1454 MeV。
若两通道都无差异 → 回查源是否真畸变（模块 B）或 Case B 源是否误用了各向同性。

### 7.6 多库比对（有余力才做，否则进"未来工作"）
切换 `OPENMC_CROSS_SECTIONS` 指向 FENDL-3.2 / ENDF-B / JEFF，重跑，给 TPR 的库间"误差带"。

---

## 8. 验证关卡汇总（[GATE]，不过不许往下）

| 关卡 | 内容 | 通过标准 |
|---|---|---|
| GATE-env | OpenMC 最小算例 | 跑出非零结果 |
| GATE-σ | Bosch-Hale 截面 | 对 ENDF/NRL 两点核对（数量级+趋势）；注意 CM=lab/2 |
| GATE-kin | 运动学 boost | E_d→0→2.45；1 MeV 前向≈4.14、后向≈1.76 MeV |
| GATE-B | 中子源项 | 能谱有2.45峰+越阈尾、角分布前向偏置、每氘产额量级对文献 |
| GATE-C | 锂靶 TPR | ⁶Li 通道 A≈B；⁷Li 通道 A/B 差异集中在 >3.1454 MeV |
| GATE-norm | 归一化 | 任何放大因子已除回；每shot绝对产额量级合理 |

---

## 9. 执行顺序（任务 DAG，供 agent 排期）

```
Week1: schema.py → GATE-env → parametric_beam.py → 三模块空壳+画图脚手架
       目标：用参数化氘谱把 A→B→C 全链路先跑出一个(粗糙)TPR 数字
Week2: cross_section(GATE-σ) → stopping → kinematics(GATE-kin) → thick_target → build_source(GATE-B)
       (若 EPOCH 已出数据，替换参数化输入重跑)
Week3: materials/geometry/source(Case A,B)/tallies/run → postprocess(GATE-C)
       天然 Li 与富集 Li 各一组
Week4: (可选)多库 → 全部成图/成表 → 按第10节写稿 → 自查(GATE-norm 复核)
```

---

## 10. 交付物清单

**图**（`outputs/figures/`）：
1. 氘束能谱 + 角分布（模块 A）
2. 中子源能谱（2.45 峰 + 越阈高能尾）
3. 中子角分布（前向各向异性）
4. TPR(r,z) 空间云图（Case B）
5. Case A vs B：总 TPR、⁶Li/⁷Li 分道对比
6. ⁷Li TPR-vs-中子能量（标 3.1454 MeV MT205 阈值线）+ A−B 偏差谱

**表**（`outputs/tables/`）：
- 总 TPR、⁶Li/⁷Li 占比、天然 vs 富集、A/B 相对偏差(%)（及多库误差带，若做）

**论文骨架**（供人写作）：引言(氚自持痛点+传统源局限) → 方法(PIC+半解析+OpenMC，说明为何弃 Geant4) →
结果一(源畸变) → 结果二(TPR A vs B) → 结果三(偏差集中于 ⁷Li 阈值窗口且各向异性) → (可选多库) → 结论与展望(14 MeV/D-T、铍倍增、瞬态时间结构)。
拟题：《激光驱动厚 CD₂ 靶脉冲 D-D 中子源的谱-角畸变及其对外部锂靶空间产氚率的影响》

---

## 11. 已知坑 / 禁止事项

1. **不把 mm 靶塞进 PIC**（内存爆炸）；PIC 靶厚 ≤5 μm。
2. **不用 OpenMC 做氘束-靶聚变**（它不输运初级带电粒子）——那是模块 B 半解析的活。
3. **Case B 源不可分离 E 与 Ω**：必须按角度 bin 建多源保留"前向=高能"相关性。
4. **能量单位**：内部 MeV，写入 OpenMC 一律 **eV**。忘转会差 10⁶。
5. **CM vs lab 能量**：等质量 D-D，`E_cm = E_lab/2`。截面用 CM。
6. **归一化**：放大因子必须除回；A/B 谱形对比用"每源中子 TPR"。
7. **score/MT 名现查现核**，不背；⁷Li 产氚优先 `H3-production` + nuclide filter。
8. **统计误差**未收敛不下结论（相对误差 <5% 再画谱）。
9. **降级预案随时可用**：PIC 慢→参数化谱；多库来不及→单库主结论、多库进展望。

---

## 12. config.yaml 建议字段（供集中调参）
```yaml
beam:        {source_type: parametric, kT_MeV: 2.0, theta_max_deg: 15, n_deuterons: 1.0e12, E_min_MeV: 0.1, E_max_MeV: 10}
target_cd2:  {rho_gcc: 1.06}
source_bins: {n_mu: 15, n_E: 100}
lithium:     {radius_cm: 10, height_cm: 20, cavity_cm: 1.0, li6_atpct_list: [7.59, 90.0], density_gcc: 0.534}
openmc:      {batches: 100, particles: 1000000, libraries: [FENDL-3.2]}
```

---

## 附录 A：推荐仿真参数与扫描矩阵

> 参数依据当前激光-CD₂ TNSA / 中子学文献锚定；标 **[VERIFY]** 处按实际算力/集群核实微调。

### A.1 PIC（EPOCH）

**维度决策：全部用 2D3V 做生产与扫描，最多补 1 发 3D 校验。**
2D 足以抓 TNSA 能谱与标度；3D 贵 100–1000×，小论文不需要。注意 2D 会**高估**离子截止能与前向聚焦。
2D 宏粒子隐含第三维，**绝对产额靠归一到给定总氘数确定**（与参数化方案一致），谱形对比不受影响。

**激光（0.8 μm Ti:Sapphire 路线）**
| 参数 | 值 |
|---|---|
| 波长 λ | 0.8 μm |
| 强度↔a₀ | I[W/cm²]≈1.37e18·a₀²/λ²；a₀=5→5.4e19, 10→2.1e20, 20→8.6e20, 30→1.9e21 |
| a₀ 扫描 | 一个月只 {5,10,20} |
| 脉宽 | 30–50 fs FWHM 高斯 |
| 焦斑 w₀ | 3–5 μm FWHM |
| 偏振 | 线偏 |

**靶与网格**
| 参数 | 值 | 说明 |
|---|---|---|
| 靶材/厚度 | 固体 CD₂, **3–5 μm**（绝不 mm） | 红线 |
| 密度 | ρ≈1.06 g/cm³, 全电离 n_e≈180 n_c(0.8μm) | 强过密 |
| **dx=dy** | **5–10 nm** | 必须 dx ≲ c/ω_pe(≈10 nm) 否则数值加热 |
| 盒子 x | 40–60 μm, 靶距左边界 10–15 μm | 采样面留靶后 |
| 盒子 y | 60–80 μm | 抓发散 |
| PPC | 每种(e/D/C) ≥100（氘≥100） | 谱要干净 |
| 预等离子体 | 前表面指数标长 L=0.5–2 μm, 扫 {0,1 μm} | 关键控制量 |
| 后表面污染 | 清氢, 富氘 | 决定拔出氘还是质子 |
| 边界 | 粒子 open/thermal, 场 laser+open | |
| 电离 | 开场致电离或预置电荷态 | |
| 时长 | ~0.8–1 ps（氘穿采样面、谱稳定） | ~120k 步, dt 由 CFL 定 |
| 采样面 | 靶后 ~20 μm 虚拟面, 记 E/方向/权重/时间 | → deuteron_beam.h5 |

省算力：5 nm 太重时可降密度到 ~100 n_c（论文注明），或守住"每趋肤深度 ≥2–3 格"。

### A.2 OpenMC
| 参数 | 值 | 说明 |
|---|---|---|
| run_mode | fixed source | 无 inactive batch |
| particles | 调试 1e5 → 生产 1e6–1e7 | mesh 分辨偏大端 |
| batches | 50–100 | 统计误差 |
| 锂靶几何 | Ø20 cm×高 20 cm 圆柱, 中心腔 r≈0.5–1 cm, 外真空 | 测试块 |
| (可选)积分TBR | r=30–50 cm 厚球壳 | 要类 TBR 数字时 |
| 材料 | 金属 Li, ρ=0.534 g/cm³ | |
| 富集 | ⁶Li {7.59%, 90%}(+可选30/60%) | 最影响 TPR |
| 温度 | 293.6 K | 室温截面 |
| 产氚 score | H3-production + nuclide filter 拆 Li6/Li7 | Li7 已核对为 MT205 `(n,Xt)` 总产氚 |
| 空间 tally | 柱网格(r,z)≈20×20 | TPR(r,z) |
| 能量 tally | log 1e3–2e7 eV, 50–100 bins | 验证 ⁷Li 集中 >3.1454 MeV |
| 收敛 | 积分量相对误差<5%, 单体素<10% | 不达标加 particles |
| 光子输运 | 关 | |
| 归一化 | tally×Y_total=每shot氚数; A/B比对用"每源中子TPR" | 隔离谱形效应 |

### A.3 一个月最小扫描矩阵
`a₀∈{5,10,20} × 预等离子体 L∈{0,1 μm}`（模块A，6 源）→ 各生成中子源 →
`锂富集∈{7.59%,90%} × Case{A理想,B畸变}`（模块C）。OpenMC 部分半天跑完，PIC 是瓶颈但可控。

### A.4 已知前人工作与本文定位（诚实边界）
- **中子源侧（激光→D-D 中子，PIC+MC）**：已被大量研究（Trident、多篇 PIC+MCNPX/Geant4），**非本文创新**。勿把论文写成"搭了个激光中子源"。
- **紧凑 D-D 源→增殖体 mock-up TPR**：已有实验工作（放电型 D-D 源 + FENDL C/E 比对）；2.5 MeV 下锂产氚计算亦有。
- **本文 niche（未见直接撞车）**：激光驱动的**畸变+各向异性+脉冲** D-D 源打锂靶，定量 TPR 相对理想各向同性单能源的偏差、并锁定其集中在 ⁷Li MT205 产氚阈值窗口(>3.1454 MeV)。属**增量新意**，小论文足够；撑博士需后续系统扫描+定标律+多库预算。
- **必写假设**：仅计 D-D 分支；CD₂ 中 ¹²C(d,n)/体相/hole-boring 等其他产中子道不计，聚焦 2.45 MeV 峰附近谱形。
