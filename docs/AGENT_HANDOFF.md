# AGENT HANDOFF

本文件由 supervisor 角色的 Claude 追加维护,记录每次审查/改动,供后续编码 agent(codex)接手。
**只追加,不覆盖历史条目。** 新条目加在最上面。

---

## 2026-07-03 codex changed - 3D strategy reset

### 后续执行更新
- 第一发 3D compact-deck 微基准 `r001`，Job ID `1417042`，在 35 秒内 `FAILED`，原因是 EPOCH3D parser 拒绝带中文/特殊字符注释的 deck；未进入物理计算，成本约 `2.5` core-hours。
- 第二发 `r002`，Job ID `1417631`，ASCII/comment-stripped 后成功进入物理推进，但在约 `94.9 fs`、首次 restart-like 输出附近 `OUT_OF_MEMORY`；1 节点 256 ranks 无内存余量，不能直接 production。
- `r003`，Job ID `1449565`，失败原因仍是 EPOCH3D parser 对注释敏感；实际提交的 `input.deck` 必须 comment-free。
- `r004`，Job ID `1473749`，comment-free 但在开始前取消，原因是复核发现 r002 自动拓扑为 `1 x 2 x 128`，会放大 halo/buffer；不应重复这个布局。
- 已提交 `r005`，Job ID `1475280`：2 节点、512 ranks、`t_end=100 fs`、comment-free，并强制 `nprocx/nprocy/nprocz = 8/8/8`。该 run 仍是 microbenchmark，不是 production source。
- 后续 production 必须等 `r005` 证明两节点内存和输出/restart 正常后再提交。

### 改动内容
- 按用户指示采用 Claude 最新策略：3D PIC 作为真实性锚点，不再把高精度 2D 参数矩阵当最终可信度核心。
- 从 `origin/claude/supervisor-review` 引入 `docs/PROJECT_POSITIONING.md` 和 `hpc/templates/epoch3d_dd_cd2_source_compact.deck`。
- 更新 `README.md`、`docs/COMPUTE_STRATEGY.md`、`docs/FORMAL_RUN_PLAN.md`、`hpc/README.md`：当前主线改为 `3D anchor -> Stage B -> Stage C`。
- 明确 3D 不直接大规模投产：先做 300 fs 微基准，测 wall-clock/内存/restart/横向边界，再决定正式 3D source run。
- 2D `L_pre=0` 三个 accepted 5 ps 源保留为 Stage B/C 开发和参数化区间锚点；2D `L_pre=1` timeout partial 不作为正式源。

### 给后续 agent 的注意
- 不要直接提交长 3D production run。第一步必须是 300 fs microbenchmark。
- 3D 模板是起点，不是已验证最终 production deck；提交前还要生成显式 Slurm walltime、确认 EPOCH3D binary、节点/内存/scratch/restart。
- Claude 分支中 3D 成本估计多次修订且存在取舍变化；主线采用保守执行原则：以实测微基准为准。

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
