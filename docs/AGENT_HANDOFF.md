# AGENT HANDOFF

本文件由 supervisor 角色的 Claude 追加维护,记录每次审查/改动,供后续编码 agent(codex)接手。
**只追加,不覆盖历史条目。** 新条目加在最上面。

---

## 2026-07-02 (5) claude changed

### 改动内容
- 新增 `hpc/templates/epoch3d_dd_cd2_source_compact.deck` —— 压缩版 3D EPOCH 源生成 deck(草稿,供评估/微基准)。

### 决定与依据(3D 方案)
- 预算 3000 CNY(~3 万 core-h @0.1)。完整 5µm 3D 装不下(~1.2-4.7 万 CNY);**压缩版可装下,单例估 ~1.8e4 core-h ≈ 1800 CNY(0.6× 预算)**。
- 取舍(每条都是旋钮):
  - **各向异性网格 dx=10nm(压趋肤深度~10nm)/ dy=dz=24nm**(沿用用户 laptop deck 经验;比 BSCC 25nm 各向同性更准也更省)。
  - **薄靶 2µm**(5µm 超预算);为一致,全线(含 2D 扫描)需统一到 2µm。
  - **t_end=1.5ps + 产额早停**(高能氘早到,⁷Li 信号已捕获)。
  - **PPC 氘优先 D32/e20/C8**(成本主旋钮;尾巴统计靠氘)。
  - **盒子 x[-6,30]µm、横向 ±12µm**。横向 ±12µm 是**物理地板**(兜住 rear+20 处发散束,半宽~11.5µm),勿再砍。
  - 只留 **rear+20 源面 probe**(沿用仓库已验证 probe 语法)+ 轻量 dist_fn;restart 每 750fs。
- **源面保持 rear+20,不改 rear+10**: rear+10 更便宜但更软(2D 实测: 平均氘能 rear+10 ~2.2 vs rear+20 ~2.9 MeV),会削弱 ⁷Li 高能尾信号;而 1800 CNY 已在预算内,无需为省钱牺牲信号。

### 提交前必做(吸取超时教训)
1. 先跑 **300 fs 微基准**: (a) 实测每步开销校准机时; (b) dx=10 vs 8nm 各一发查数值加热(谱漂=欠分辨); (c) 看氘是否在到 rear+20 前打横向边界(确认 ±12µm 够)。
2. restart 为全量(3D 每个 ~TB 级),确认 scratch 配额。

### 待定(用户 / supervisor 拍板)
- 靶厚 **2µm 是否接受**(牵动全线,2D 也要改)。
- 激光 **单脉冲(现基线)vs 用户此前优化的双脉冲**。

---

## 2026-07-02 (4) claude changed

### 改动内容
- 文件: 重写 `docs/PROJECT_POSITIONING.md` §4.5(可信度两条腿 + 3D 单发机时预算表)。未动代码/数据。

### 更正(重要)
- 上一条把 2D→3D **标度律**当主要可信度依据是**写松了**: 标度律基本只给最大/截止能,
  pin 不住完整谱形 + 角分布 + 绝对产额。降级为"截止能旁证"。
- 可信度改为**两条腿**: (腿一) 参数化扫描使**结论对源稳健**(夹逼真实 3D,无需 3D 即成立);
  (腿二) **1 发做对的 3D 校验**给完整 dN/dE+dN/dθ,坐实"参数化区间括住了真实源"。3D 校验从"可选"提为"推荐"。

### 3D 单发机时预算(粗估,详见 §4.5 表)
- A 激进最小(15nm,40×30×30µm,1.0ps): ~2.8e5 core-h(~2.8 万 CNY),~2.3TB,~3 节点。
- C 降密度 100nc(15nm): ~3.4e5 core-h。 B 稳妥(12.5nm): ~8.8e5 core-h。
- 即便最省也约 = 整个 2D 扫描的 ~150×。**结论: 一发即止,优先 A/C,先跑微基准校准估算,开 restart。**
- **别做低精度全 3D 扫描,也别粗化到 >15nm(会数值加热把源做假)。**

---

## 2026-07-02 (3) claude changed

### 改动内容
- 文件/模块: 本条 + `docs/PROJECT_POSITIONING.md` 新增 §4.5(2D→3D 策略+参考)。未动代码/数据。
- 目的: 把"1 发最小 3D 校验 + 文献定界"写成可执行任务; 澄清产额加权判据; 记录"改判据不作废已跑数据"。

### 澄清: 产额加权完整度判据(细化上一条建议 1)
- **物理已正确**: `build_source.py` 生成中子时已按 `weight = w_d × Y(E_d)` 加权,无需改。
- **只有完整度判据用错权重**: `hpc/tools/integrate_probe_sdf.py` 判 PIC 停不停时用的是**原始氘权重**。
  改为**逐粒子按 Y(E_d) 加权**的末窗占比(代理量); 可选更贴信号 = 只按 **>2.82 MeV 快中子产额**加权。
- **改判据不作废任何已跑数据**: 这是后处理验收标准。现有 5ps 的 L_pre=0 数据是超集,套新判据只会显示"~3.5ps 已达标",
  直接用即可、不重跑。建议全部源用同一判据定义以保一致性。省机时只兑现在未跑的(如 L_pre=1 重跑)。

### 新任务: 2D→3D 偏差处理 —— **不要做低精度 3D 扫描**
**陷阱**: 维度与分辨率是两根独立的轴。固体密度 n_e≈160 n_c,趋肤深度 ~10nm; 2D 已用 25nm(文档标 5-10nm 才够)。
粗化到 50nm 做 3D 会数值加热、把离子谱做假,比"收敛 2D + 维度修正"更难辩护。且 3D 不加新意、只加防御力,升不了区。

**推荐做法(专业标准,省机时,对齐 MRE 严谨要求):**
1. 主扫描继续用收敛好的 2D(现有)。
2. 补 **1 发最小化但分辨率达标(≤10-15nm)的 3D 校验**: 单 a0(建议 a0=10)、盒子与时长砍到刚够拿
   氘**截止能**与**前向发散角**即可(不追 5ps 完整源,只要 2D→3D 比值)。用它实测 2D 对 3D 的高估比值,给 2D 源定校验锚。
3. 叠加文献 2D↔3D 标度律折算成偏差带(见下)。文献是质子 TNSA; 2D↔3D 的**几何**高估对氘同样适用
   (同为鞘层空间电荷几何效应),但绝对比值以本项目那发 3D 校验为准。
4. 论文里把 2D 从"最易攻击"写成"已声明、已用 3D 校验 + 文献标度律定界"的常规限制。

**参考文献(2D↔3D 定界)**:
- S. Sinigardi et al., "TNSA proton maximum energy laws for 2D and 3D PIC simulations", NIM-B (2018), arXiv:1801.04737.
- J. Babaei, L. A. Gizzi et al., "Rise time of proton cut-off energy in 2D and 3D PIC simulations", Phys. Plasmas 24, 043106 (2017), doi:10.1063/1.4979901.
- "A particle-in-cell code comparison for ion acceleration: EPOCH, LSP, and WarpX" (2021).

**若坚持全 3D**: 先出一版"达标分辨率(≤10nm)下单例 3D 的机时/内存预算"再决定; 大概率证明全 3D 扫描不可行。

---

## 2026-07-02 (2) claude changed

### 改动内容
- 文件/模块: 新增 `docs/PROJECT_POSITIONING.md`; 追加本条目。未改动任何代码/数据。
- 目的: 记录一次战略重定位讨论的结论(项目意义、可信度论证、下一步方向),并更新可执行清单。

### 关键决定(供 codex 与 supervisor 对齐)
- **重定位**: 放弃"证明激光可产氚"(能量-经济账差几个数量级,会得反面结论),
  改为"评估紧凑/激光 D-D 源作为**产氚试验台**的**源保真度**"。详见 `docs/PROJECT_POSITIONING.md`。
- 产业背景真实: Astral(2025 首个 D-D→Li→T 商业演示)、UKAEA LIBRTI(£220M)、SHINE(14 MeV 源)、CFS。
- 主张改为**条件性/相对/机理层**: PIC 是畸变参数空间的物理锚点,稳健性来自参数化畸变扫描;
  2D 夸大畸变=保守上界; 可信度由分件验证 + 标定过的核数据/输运承载。

### 状态更新
- **[已解决]** 首条建议 1(Bosch-Hale 9.8 MeV 上限): codex 已核, a0=20 源 E_D>9.8 MeV 占比 5.2e-5,
  远低于 1% 阈值,非阻塞。此项关闭。

### 下一步建议(codex 可执行,按优先级)

1. **[高] 完整度判据: 从"氘权重"改为"产额加权"(甚至 TPR 加权)。**
   - 问题: 现判据在 `rear+20 um` 用氘权重末窗占比 <10%,把结束时间顶到 5 ps; 但下游要的是中子/产氚,
     由高能氘主导,而高能氘早到、低能氘晚到。
   - 量化(用仓库 `thick_target_yield`, a0=5 源, 窗均能已保守低估高能窗):
     3500 fs 时氘权重末窗 13.3%(判据没过)但产额末窗仅 6.3%(已达标)、中子产额已累积 90.3%;
     4000 fs 产额末窗 2.4%(96.2%);5000 fs 0.6%(100%)。
   - 动作: 在 `hpc/tools/integrate_probe_sdf.py` 增加**逐粒子按 Y(E_d) 加权**的完整度指标,
     判据切到产额加权(或 ⁷Li 相关的 >2.82 MeV 中子产额加权,更贴信号)。预期每点少跑 ~1-1.5 ps。
   - 收益: 省机时; 更物理可辩护; 直接缓解 L_pre=1 那类 4h 超时(结束时间需求下降)。

2. **[高] 开 EPOCH restart/dump, 使墙钟超时可续算。**
   - 背景: L_pre=1 三例按 4h 提交全部 TIMEOUT(只到 2.73-3.41 ps), ~1921 core-hours ≈ 192 CNY 打水漂,
     因为没断点。动作: deck/Slurm 加周期性 restartable dump + 从最新 dump 续算的提交路径; 配合建议 1 双保险。

3. **[高] 参数化源从"备份"升为"主干"。**
   - 扫 `kT∈{1,2,3}`、`theta_max∈{10,20}`, 换算 >2.82 MeV 占比, 画"畸变强度 → ⁷Li 超额 TPR"曲线;
     PIC 点叠加当物理锚。这是新定位下论文主结论稳健性的来源(见 PROJECT_POSITIONING §3)。

4. **[中] CM 各向异性**(接口 `cm_dir_unit` 已留): 见首条建议 2, 分支 `claude/anisotropy-cm`。

5. **[中] Stage C 前先做 a0=5 源的 per-source-neutron A/B 快算**, 确认 ⁷Li 差异统计可分辨。

6. **[低] tally mesh 换 CylindricalMesh**(现 RegularMesh 四角落真空, 浪费 bin)。

### 写作提醒
- 论文里给一版正式的能量-经济账(定位论据), 明确"相对机理映射、非绝对预测、2D=保守上界"。
- 绝对 per-shot 产氚仅 illustrative; 稳健量是 per-source-neutron 的 A/B、分 Li6/Li7 道。

---

## 2026-07-03 codex changed

### 改动内容
- 记录 `L_pre=1` 三个 4 ps 作业的 walltime 事故：`a0=5/10/20,L_pre=1` 均因 `#SBATCH -t 04:00:00` 到时被 Slurm 停止。
- 已把 `hpc/pic_scan4ps_first_20260702_jobs.csv` 中三个 L1 作业标记为 `TIMEOUT_PARTIAL_NOT_ACCEPTED`。
- 已把 `config.yaml` 的 first 2D scan walltime 改为 `null`，表示每次提交必须显式选择。
- 已把 `hpc/tools/render_epoch_4ps_scan.py` 的 `--hours` 改为必填参数；没有显式 walltime 就拒绝生成 Slurm 文件。
- `hpc/RUN_LOG.md` 已记录事故成本：三个 timeout 约 1,921 core-hours，按 0.1 CNY/core-hour 约 192 CNY，且没有产生 accepted source。

### 给后续 agent 的注意
- 这三个 L1 partial 输出不得进入 Stage B，只能用于趋势/运行时间估计。
- 后续不要再用过紧墙时提交生产 PIC；必须用 EPOCH ETA 或短 benchmark 决定 walltime/ranks，并在命令里显式写 `--hours`。
- 当前可推进 Stage B 的正式源仍是 `L_pre=0` 的 `a0={5,10,20}` 三个 5 ps accepted sources。

---

## 2026-07-03 codex changed

### 改动内容
- `a0=20, L_pre=0` 的 5 ps 延长作业 `1380981` 已完成并解析。
- `rear+20 um` final-window fraction 从 4 ps 的 14.2% 降到 5 ps 的 6.22%，通过 `<=10%` 源时间完整性门槛。
- 该点可作为 Stage B 候选 D 源，源定义为 `rear+20 um` 穿面探针从起始到 5.0 ps 的累计相空间。
- 已复查 accepted 5 ps 源的 Bosch-Hale 高能截断风险：`E_D > 9.8 MeV` 累计权重占比约 5.20e-5，低于 1% 动作阈值。

### 给后续 agent 的注意
- `a0=20, L_pre=0` 使用 5 ps 源，不使用 4 ps 源。
- 目前 `L_pre=0` 的 `a0={5,10,20}` 三个点均已有通过门槛的 5 ps 源，可进入 Stage B 准备。
- 继续监控三个 `L_pre=1` 的 4 ps 作业；`a0=20,L_pre=1` 完成后仍需重复 `E_D > 9.8 MeV` 高能尾统计。

---

## 2026-07-03 codex changed

### 改动内容
- `a0=5, L_pre=0` 的 5 ps 延长作业 `1381095` 已完成并解析。
- `rear+20 um` final-window fraction 从 4 ps 的 21.6% 降到 5 ps 的 9.25%，通过 `<=10%` 源时间完整性门槛。
- 该点可作为 Stage B 候选 D 源，源定义为 `rear+20 um` 穿面探针从起始到 5.0 ps 的累计相空间。

### 给后续 agent 的注意
- `a0=5, L_pre=0` 使用 5 ps 源，不使用 4 ps 源。
- 目前已接受的 Stage B 候选源：`a0=5,L_pre=0,t=5ps` 与 `a0=10,L_pre=0,t=5ps`。
- 继续监控 `a0=20,L_pre=0` 的 5 ps 延长作业，以及三个 `L_pre=1` 的 4 ps 作业。

---

## 2026-07-03 codex changed

### 改动内容
- `a0=10, L_pre=0` 的 5 ps 延长作业 `1377658` 已完成并解析。
- `rear+20 um` final-window fraction 从 4 ps 的 18.1% 降到 5 ps 的 7.72%，通过 `<=10%` 源时间完整性门槛。
- 该点可作为 Stage B 候选 D 源，源定义为 `rear+20 um` 穿面探针从起始到 5.0 ps 的累计相空间。

### 给后续 agent 的注意
- `a0=10, L_pre=0` 使用 5 ps 源，不使用 4 ps 源。
- `rear+30/40/50 um` 在 5 ps 仍未过时间完整性门槛，只作为诊断，不作为本轮 source plane。
- 继续监控 `a0=20,L_pre=0` 和 `a0=5,L_pre=0` 的 5 ps 延长作业，以及三个 `L_pre=1` 的 4 ps 作业。

---

## 2026-07-03 codex changed

### 改动内容
- 继续监控第一轮 PIC 扫描；新增完成并解析 `a0=20, L_pre=0` 和 `a0=5, L_pre=0` 两个 4 ps 作业。
- `a0=20, L_pre=0` 的 `rear+20 um` final-window fraction = 14.2%，未通过 `<=10%` 源时间完整性门槛。
- `a0=5, L_pre=0` 的正式 16/16/8 PPC 扫描 `rear+20 um` final-window fraction = 21.6%，也未通过门槛。
- 已提交 5 ps 延长作业：`a0=20, L_pre=0` Job ID `1380981`；`a0=5, L_pre=0` Job ID `1381095`。
- 完成了 `a0=20, L_pre=0` 的 Bosch-Hale 高能截断检查：`E_D > 9.8 MeV` 累计权重占比约 7.47e-5，远低于 1% 动作阈值。

### 给后续 agent 的注意
- `a0=5/10/20, L_pre=0` 的 4 ps 正式源都不得进入 Stage B；必须等对应 5 ps 延长版解析通过，若仍不过门槛再继续延长。
- 继续监控仍在跑的 4 ps 作业：`a0=10,L_pre=1`、`a0=20,L_pre=1`、`a0=5,L_pre=1`。
- `a0=20,L_pre=1` 完成后仍需重复 `E_D > 9.8 MeV` 高能尾统计；5 ps 的 `a0=20,L_pre=0` 接受前也要复查。

---

## 2026-07-03 codex changed

### 改动内容
- 合并了 Claude 的只读审查文档到 `main`。
- 监控第一轮 6 点 PIC 扫描；`a0=10, L_pre=0` 的 4 ps 作业已完成并解析。
- 该点 `rear+20 um` final-window fraction = 18.1%，未通过 `<=10%` 源时间完整性门槛。
- 已提交 5 ps 延长作业 `pic2d_dd_cd2_scan5ps_a0_10_L_0_t_5um_20260703_r001`，Job ID `1377658`。

### 给后续 agent 的注意
- `a0=10, L_pre=0` 的 4 ps 源不得进入 Stage B；必须等 5 ps 延长版解析通过或继续延长。
- 继续监控其余 5 个 4 ps 扫描点。每个点完成后都要检查 `rear+20 um` final-window fraction、累计均能和角 RMS。
- Claude 提醒的高能截断检查仍等待 `a0=20` 扫描结果：统计 `E_D > 9.8 MeV` 的权重占比。

---

## 2026-07-02 claude changed

### 改动内容
- 文件/模块: 新增本文件 `docs/AGENT_HANDOFF.md`(仅此一个文件;未改动任何现有代码/配置/数据)。
- 目的: 记录一次**只读**的物理与执行方案审查结论,并把可执行的下一步交给 codex。
- 本次未推送任何代码变更,只有这份交接文档。

### 审查范围
只读 clone,审了:`moduleB_source/{cross_section,kinematics,thick_target}.py`、
`moduleC_openmc/{source,tallies}.py`、`tests/test_gates.py`、`interfaces/schema.py`,
以及 `hpc/RUN_LOG.md`、`docs/{PHYSICS_LOCK,FORMAL_RUN_PLAN,PIC_SOURCE_CRITERIA}.md`。

### 结论(通过项,勿回退)
- Bosch-Hale 系数、`E_cm = E_lab/2`、两体 boost、产额积分 `n_D·σ/S`、逆 CDF 采样反应能量:
  与规格一致,单位正确。GATE 测试(2.449 / 4.14 / 1.76 MeV;截面单调且越界置零;产额随 E0 升;
  源含 >2.82 MeV 中子)已把物理校验点固化,保留。
- Case B 源正确保留 E-μ 相关(按 μ 分 bin 建多源),strength 归一到 per-source-neutron;
  A/B 比对方式正确。tally 用 `H3-production` + 核素 filter 分道,正确。
- 几何锁定(薄箔→真空隙→外置厚 CD2 converter→Li)、PIC 源时间窗完整性判据
  (rear+20µm 末窗占比 7.19% < 10% 才接受)都是规范做法,勿改。
- "效应太小"的风险基本解除:smoke 中 >2.82 MeV 中子占比 ~0.17,PIC 氘束多 MeV
  (rear+20µm 积分均 ~2.9 MeV,p99 ~6.7 MeV),⁷Li 阈值通道有料。

### 下一步建议(codex 可执行,按优先级)

1. **[高·且与在跑扫描相关] 检查高 a₀ 氘能是否顶穿 Bosch-Hale 上限。**
   - 现状: `moduleB_source/cross_section.py` 在 `E_cm > 4900 keV`(氘 lab > 9.8 MeV)把 σ 置零,
     那部分最高能氘被当成不产中子 → 系统性压低高 a₀ 产额并削掉最该关注的高能尾。
   - 动作: 对 `a0=20` 的扫描输出统计氘谱最大能量与 >9.8 MeV 的权重占比。
     若占比不可忽略(经验阈值 >1%),把截面高能段接上 ENDF/B D(d,n) 数据后延伸 `E_MAX_KEV`;
     否则在论文/文档显式声明截断并报告被截权重占比。
   - 交付: 一段统计脚本 + 结论写回本文件;必要时改 `cross_section.py`(附单元测试)。

2. **[高·对论文防御力最大] 实现 CM 各向异性(接口已留 `cm_dir_unit`)。**
   - 理由: 氘多 MeV、E_cm ~1–2 MeV,此区间 D(d,n) 前向各向异性已不可忽略;
     论文主题是"各向异性",忽略核反应本身异性最易被审稿人攻击。
   - 动作: 在 `moduleB_source/kinematics.py` 用 Legendre 系数(ENDF 或文献参数化)给 CM 角分布采样,
     替换默认各向同性;保留各向同性作为可切换基线。
   - 交付: 建议在分支 `claude/anisotropy-cm` 上做;加"各向同性 vs 带异性"敏感性对比图 + GATE。
   - **勿破坏现有 GATE**: `gate_kinematics` 用 `cm_dir_unit` 显式传方向,异性实现须保持该路径行为不变。

3. **[中] Stage C 前先做 per-source-neutron 的 A/B 快算(a₀=5 源)。**
   - 目的: 确认 ⁷Li 通道 A/B 差异在统计上可分辨(相对误差 <5%),避免全跑完才发现效应埋在噪声里。
   - 这是半天的保险,不是最终生产 run。

4. **[低] `moduleC_openmc/tallies.py` 的 mesh 换 CylindricalMesh。**
   - 现用 RegularMesh 立方体罩在圆柱外,四角落在真空、浪费 bin;换 CylindricalMesh 让 TPR(r,z) 更干净。

### 写作提醒(非代码)
- 2D PIC 给不出绝对产额;per-shot 绝对氚数只是 illustrative,稳健量是 per-source-neutron 的 A/B 比。
- 论文可点出"氘束能量-角度相关(高能更前向、低能更宽)"天然强化"前向=高能"的主结论。
