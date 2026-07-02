# AGENT HANDOFF

本文件由 supervisor 角色的 Claude 追加维护,记录每次审查/改动,供后续编码 agent(codex)接手。
**只追加,不覆盖历史条目。** 新条目加在最上面。

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
