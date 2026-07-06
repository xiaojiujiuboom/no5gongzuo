# 物理几何锁定

本项目第一篇小论文采用以下几何解释，后续代码、配置、图注和论文文字都按这个版本保持一致：

```text
激光打薄 CD2 foil
-> 产生前向 TNSA-like 氘束
-> 氘束进入外置厚 CD2 converter 并慢化到停
-> 厚靶 D-D 的 D(d,n)3He 中子分支进入外部锂靶
-> 计算 Li6/Li7 每源中子 TPR，比较理想源与 PIC 派生源的保真度
```

也就是说，Stage B 不是计算薄靶内部“自发中子”作为最终源，而是计算外置厚 CD2 converter 的 D-D 厚靶中子分支。当前论文主张收窄为 **CD2 converter 的每源中子 Li-TPR 保真度**。TiD2 和 `D(d,p)T` 直接氚不再作为当前论文承诺，除非后续补齐材料阻止本领、截面核验和直接氚实现。

## 为什么这样锁定

- 厚靶产额可用 `integral n_D sigma(E_cm) / S(E) dE` 做清晰归一化，但绝对归一化必须等截面与阻止本领 GATE 通过后再作为最终结论。
- 中子能量-角度畸变来自入射氘束方向和 D-D 两体 boost，论文主问题更干净。
- OpenMC Stage C 只接收中子源，不需要处理初级带电粒子。
- `D(d,p)T` 直接氚若未来实现，必须单独报告为 converter 内产额，不能混进 Li tally；当前论文不把它计入结果。

## Stage B 产物锁定

```text
neutron_source.h5              from D(d,n)3He, passed to OpenMC
```

当前论文主表优先分列：

```text
TPR_Li6_per_source_neutron
TPR_Li7_per_source_neutron
TPR_Li_total_per_source_neutron
```

`T/shot` 只作为诊断归一化展示，不能把旧 full-chain 表直接当最终定量结论。
当前 `D(d,n)3He` 截面已通过 Bosch-Hale 逐点核对，D-in-CD2 阻止本领已替换为
NIST PSTAR 同速实体表；最终绝对表需要用新阻止本领重算，SRIM 级别闭合仍待补。

## 当前第一轮 PIC 扫描

第一轮只做 6 个 2D3V 源：

```text
a0 = {5, 10, 20}
preplasma L = {0, 1 um}
CD2 foil thickness = 5 um
```

若结果对源强或谱形敏感，再补 `3 um` 厚度扫描。这样避免一开始做 12 点导致排队和数据管理压力翻倍。

## 参数化备份源

参数化源不只保留一个点，而是用于敏感性小扫描：

```text
kT = {1, 2, 3} MeV
theta_max = {10, 20} deg
```

论文里它的作用是证明主结论不是某个任意参数化源造成的；最终主图仍优先使用 PIC 导出的氘束。
