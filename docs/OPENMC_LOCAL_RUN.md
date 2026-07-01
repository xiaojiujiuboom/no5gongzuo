# 本地 OpenMC 运行记录

本机已经存在并验证可用的 conda 环境：

```bash
/opt/miniconda3/bin/conda run -n openmc-env python -c "import openmc; print(openmc.__version__)"
```

当前版本：

```text
OpenMC 0.15.0
conda env: /opt/miniconda3/envs/openmc-env
platform: x86_64 under Rosetta
```

当前可用核数据库：

```text
/Users/oomb/Downloads/mcnp_endfb71/cross_sections.xml
```

该库已确认包含 `Li6` 和 `Li7` neutron HDF5。

## Smoke Run

先跑 Stage A/B 小源：

```bash
python3 moduleA_pic/parametric_beam.py --n 20000 -o outputs/smoke_deuteron_beam.h5
python3 moduleB_source/build_source.py outputs/smoke_deuteron_beam.h5 \
  -o outputs/smoke_neutron_source.h5 --max-particles 5000
```

Case A：理想 2.45 MeV 各向同性源：

```bash
/opt/miniconda3/bin/conda run -n openmc-env python moduleC_openmc/run.py \
  --case A --li6 90 \
  --output-dir outputs/openmc_smoke_A \
  --batches 20 --particles 100000 \
  --cross-sections /Users/oomb/Downloads/mcnp_endfb71/cross_sections.xml \
  --run

/opt/miniconda3/bin/conda run -n openmc-env python moduleC_openmc/postprocess.py \
  outputs/openmc_smoke_A/statepoint.20.h5
```

Case B：畸变 D-D 源：

```bash
/opt/miniconda3/bin/conda run -n openmc-env python moduleC_openmc/run.py \
  --case B --li6 90 \
  --nsrc outputs/smoke_neutron_source.h5 \
  --output-dir outputs/openmc_smoke_B \
  --batches 20 --particles 100000 \
  --cross-sections /Users/oomb/Downloads/mcnp_endfb71/cross_sections.xml \
  --run

/opt/miniconda3/bin/conda run -n openmc-env python moduleC_openmc/postprocess.py \
  outputs/openmc_smoke_B/statepoint.20.h5
```

## 已验证的 Smoke 物理信号

用 `Li6=90 at%`、`20 x 100000` 粒子：

```text
Case A:
  TPR_Li6 ~= 1.28e-1 per source neutron
  TPR_Li7 = 0, because 2.45 MeV is below the Li7 threshold

Case B:
  TPR_Li6 ~= 1.16e-1 per source neutron
  TPR_Li7 ~= 3.7e-3 per source neutron
```

这说明 Stage C 的最小 A/B 链路已经能体现目标物理图像：畸变 D-D 源的高能尾打开 `Li7` 阈值通道，而理想 2.45 MeV 源打不开。

## 归一化规则

Case B 的多源 `IndependentSource.strength` 已默认归一化到总和 1，因此 OpenMC tally 是“每源中子”的量。只有在报告每 shot 绝对产额时，才乘 `neutron_source.h5` 里的 `Y_total`。

