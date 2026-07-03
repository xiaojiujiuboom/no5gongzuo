# 物理几何锁定

本项目第一篇小论文采用以下几何解释，后续代码、配置、图注和论文文字都按这个版本保持一致：

```text
激光打薄 CD2 foil
-> 产生前向 TNSA-like 氘束
-> 氘束进入外置厚 TiD2 baseline converter 并慢化到停
-> 厚靶 D-D 同时产生 D(d,n)3He 中子分支与 D(d,p)T 直接氚分支
-> 中子分支进入外部锂靶，计算 Li 产氚 TPR
```

也就是说，Stage B 不是计算薄靶内部“自发中子”作为最终源，而是计算外置厚 deuteride converter 的 D-D 厚靶反应。baseline 物理解释采用 TiD2；CD2 保留为当前软件链路和后续材料敏感性对照。

## 为什么这样锁定

- 厚靶产额可用 `integral n_D sigma(E_cm) / S(E) dE` 做清晰归一化。
- 中子能量-角度畸变来自入射氘束方向和 D-D 两体 boost，论文主问题更干净。
- OpenMC Stage C 只接收中子源，不需要处理初级带电粒子。
- `D(d,p)T` 直接氚必须单独报告为 converter 内产额，不能混进 Li tally。

## Stage B 产物锁定

```text
neutron_source.h5              from D(d,n)3He, passed to OpenMC
triton_direct_source.h5/table   from D(d,p)T, reported outside OpenMC
```

论文主表应至少分列：

```text
T_direct_DD
T_Li_neutron
T_total = T_direct_DD + T_Li_neutron
```

其中 `T_total` 只有在两个分支都按同一个每 shot 归一化后才报告。

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
