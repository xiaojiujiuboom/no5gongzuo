"""Run C4: 3D anchor Stage C and 2D/3D validation.

All heavy OpenMC statepoints stay under the no6 data area. The original C1
outputs are read as references only and are not overwritten.
"""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_c1_part1_3 import (
    CROSS_SECTIONS,
    LI6_CASES,
    NO6_ROOT,
    OPENMC_BIN,
    SourceSpec,
    build_aprime_model,
    li_tag,
    run_model_if_needed,
    source_description_row,
    tally_sum,
)
from moduleC_openmc.run import build_model


OUT_ROOT = NO6_ROOT / "openmc_c4_3d_anchor_20260708"
C1_ROOT = NO6_ROOT / "openmc_c1_20260706" / "part1_3_decomposition"
C1_SUMMARY = C1_ROOT / "c1_part1_3_source_decomposition_summary.csv"
PIC3D_DIR = NO6_ROOT / "stageB_inputs_3d" / "pic3d_a0_20_t_3um_6ps"
PIC2D_ID = "pic2d_a0_20_t_3um"
PIC3D_ID = "pic3d_a0_20_t_3um"


@dataclass(frozen=True)
class RatioWithUncertainty:
    value: float
    std: float
    rel_err: float


def configure_env() -> None:
    os.environ["OPENMC_CROSS_SECTIONS"] = str(CROSS_SECTIONS)
    os.environ["PATH"] = f"{OPENMC_BIN}:{os.environ.get('PATH', '')}"


def statepoint_path(case: str, li6: float) -> Path:
    run_root = OUT_ROOT / "openmc_runs"
    if case == "A":
        return run_root / f"caseA_li6_{li_tag(li6)}" / "statepoint.100.h5"
    if case == "Aprime":
        return run_root / f"caseAprime_{PIC3D_ID}_li6_{li_tag(li6)}" / "statepoint.100.h5"
    if case == "B":
        return run_root / f"caseB_{PIC3D_ID}_li6_{li_tag(li6)}" / "statepoint.100.h5"
    raise ValueError(case)


def run_openmc(args: argparse.Namespace, spec: SourceSpec) -> None:
    configure_env()
    run_root = OUT_ROOT / "openmc_runs"
    run_root.mkdir(parents=True, exist_ok=True)
    for li6 in LI6_CASES:
        print(f"RUN C4 Case A Li6={li6:g}", flush=True)
        model = build_model(
            "A",
            li6,
            str(ROOT / "config.yaml"),
            production=False,
            batches=args.batches,
            particles=args.particles,
        )
        run_model_if_needed(model, statepoint_path("A", li6).parent, args.threads, args.force_openmc)

        print(f"RUN C4 Case A-prime {PIC3D_ID} Li6={li6:g}", flush=True)
        model = build_aprime_model(spec.neutron_h5, li6, batches=args.batches, particles=args.particles)
        run_model_if_needed(model, statepoint_path("Aprime", li6).parent, args.threads, args.force_openmc)

        print(f"RUN C4 Case B {PIC3D_ID} Li6={li6:g}", flush=True)
        model = build_model(
            "B",
            li6,
            str(ROOT / "config.yaml"),
            neutron_h5=str(spec.neutron_h5),
            production=False,
            batches=args.batches,
            particles=args.particles,
        )
        run_model_if_needed(model, statepoint_path("B", li6).parent, args.threads, args.force_openmc)


def _case_values(sp: Path) -> dict[str, float]:
    li6, li6_std, li6_rel = tally_sum(sp, "TPR_Li6")
    li7, li7_std, li7_rel = tally_sum(sp, "TPR_Li7")
    total = li6 + li7
    total_std = math.sqrt(li6_std * li6_std + li7_std * li7_std)
    return {
        "Li6": li6,
        "Li6_std": li6_std,
        "Li6_rel_err": li6_rel,
        "Li7": li7,
        "Li7_std": li7_std,
        "Li7_rel_err": li7_rel,
        "total": total,
        "total_std": total_std,
        "total_rel_err": total_std / total if total else float("nan"),
    }


def _ratio(num: float, num_std: float, den: float, den_std: float) -> RatioWithUncertainty:
    if den == 0.0:
        return RatioWithUncertainty(float("nan"), float("nan"), float("nan"))
    value = num / den
    rel2 = 0.0
    if num != 0.0:
        rel2 += (num_std / num) ** 2
    if den != 0.0:
        rel2 += (den_std / den) ** 2
    std = abs(value) * math.sqrt(rel2)
    return RatioWithUncertainty(value, std, std / abs(value) if value else float("nan"))


def summarize_3d(spec: SourceSpec) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    desc = source_description_row(spec)
    for li6 in LI6_CASES:
        vals = {case: _case_values(statepoint_path(case, li6)) for case in ["A", "Aprime", "B"]}
        row: dict[str, object] = {
            **desc,
            "li6_atpct": li6,
            "CaseA_statepoint": str(statepoint_path("A", li6)),
            "CaseAprime_statepoint": str(statepoint_path("Aprime", li6)),
            "CaseB_statepoint": str(statepoint_path("B", li6)),
        }
        for case in ["A", "Aprime", "B"]:
            for tally in ["Li6", "Li7", "total"]:
                row[f"{case}_TPR_{tally}_per_n"] = vals[case][tally]
                row[f"{case}_TPR_{tally}_std"] = vals[case][f"{tally}_std"]
                row[f"{case}_TPR_{tally}_rel_err"] = vals[case][f"{tally}_rel_err"]
        for tally in ["Li6", "Li7", "total"]:
            a = vals["A"][tally]
            ap = vals["Aprime"][tally]
            b = vals["B"][tally]
            row[f"ratio_Aprime_over_A_{tally}"] = ap / a if a else float("nan")
            row[f"ratio_B_over_Aprime_{tally}"] = b / ap if ap else float("nan")
            row[f"ratio_B_over_A_{tally}"] = b / a if a else float("nan")
            product = (ap / a) * (b / ap) if a and ap else float("nan")
            row[f"ratio_closure_product_minus_B_over_A_{tally}"] = product - (b / a) if a else float("nan")
        r = _ratio(vals["B"]["total"], vals["B"]["total_std"], vals["A"]["total"], vals["A"]["total_std"])
        row["ratio_B_over_A_total_std"] = r.std
        row["ratio_B_over_A_total_rel_err"] = r.rel_err
        rows.append(row)
    return pd.DataFrame(rows)


def _prediction_from_reference(ref: pd.DataFrame, li6: float, x: float) -> dict[str, float | str]:
    part = ref[(ref["li6_atpct"] == li6) & (ref["family"].isin(["pic2d", "parametric"]))].copy()
    part = part[np.isfinite(part["li7_mt205_fluxavg_b"]) & np.isfinite(part["ratio_B_over_A_total"])]
    grouped = (
        part.groupby("li7_mt205_fluxavg_b", as_index=False)["ratio_B_over_A_total"]
        .mean()
        .sort_values("li7_mt205_fluxavg_b")
    )
    xs = grouped["li7_mt205_fluxavg_b"].to_numpy(float)
    ys = grouped["ratio_B_over_A_total"].to_numpy(float)
    if xs.size < 2:
        return {"prediction_method": "insufficient_reference", "predicted_B_over_A_total": float("nan")}
    if x <= xs[0]:
        y = float(ys[0])
        mode = "below_reference_clamped"
    elif x >= xs[-1]:
        y = float(ys[-1])
        mode = "above_reference_clamped"
    else:
        y = float(np.interp(x, xs, ys))
        mode = "linear_interpolation_mean_duplicate_x"
    return {
        "prediction_method": mode,
        "predicted_B_over_A_total": y,
        "reference_x_min": float(xs[0]),
        "reference_x_max": float(xs[-1]),
        "n_reference_unique_x": int(xs.size),
    }


def compare_2d_3d(c1: pd.DataFrame, c4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    curve_rows: list[dict[str, object]] = []
    for li6 in LI6_CASES:
        row2 = c1[(c1["source_id"] == PIC2D_ID) & (c1["li6_atpct"] == li6)].iloc[0]
        row3 = c4[c4["li6_atpct"] == li6].iloc[0]
        out: dict[str, object] = {"li6_atpct": li6, "source_2d": PIC2D_ID, "source_3d": PIC3D_ID}
        for col in [
            "source_E_mean_MeV",
            "source_E_max_MeV",
            "frac_E_gt_2p82",
            "frac_E_gt_3p1454",
            "frac_E_gt_4MeV",
            "li7_mt205_fluxavg_b",
            "frac_mu_gt_0p8",
            "ratio_Aprime_over_A_total",
            "ratio_B_over_Aprime_total",
            "ratio_B_over_A_total",
            "B_TPR_Li6_per_n",
            "B_TPR_Li7_per_n",
            "B_TPR_total_per_n",
        ]:
            v2 = float(row2[col])
            v3 = float(row3[col])
            out[f"{col}_2d"] = v2
            out[f"{col}_3d"] = v3
            out[f"{col}_delta_3d_minus_2d"] = v3 - v2
            out[f"{col}_ratio_3d_over_2d"] = v3 / v2 if v2 else float("nan")
        rows.append(out)

        pred = _prediction_from_reference(c1, li6, float(row3["li7_mt205_fluxavg_b"]))
        measured = float(row3["ratio_B_over_A_total"])
        measured_std = float(row3["ratio_B_over_A_total_std"])
        predicted = float(pred["predicted_B_over_A_total"])
        residual = measured - predicted
        z = residual / measured_std if measured_std and np.isfinite(measured_std) else float("nan")
        curve_rows.append(
            {
                "li6_atpct": li6,
                "source_id": PIC3D_ID,
                "li7_mt205_fluxavg_b": float(row3["li7_mt205_fluxavg_b"]),
                **pred,
                "measured_B_over_A_total": measured,
                "measured_B_over_A_total_std": measured_std,
                "residual_measured_minus_predicted": residual,
                "residual_in_measured_sigma": z,
                "consistent_with_curve_at_2sigma": bool(abs(z) <= 2.0) if np.isfinite(z) else False,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(curve_rows)


def make_plots(c1: pd.DataFrame, c4: pd.DataFrame, curve: pd.DataFrame) -> None:
    figdir = OUT_ROOT / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    for li6 in LI6_CASES:
        ref = c1[c1["li6_atpct"] == li6].copy()
        row3 = c4[c4["li6_atpct"] == li6].iloc[0]
        fig, ax = plt.subplots(figsize=(8.0, 5.0))
        for family, marker, color in [("parametric", ".", "0.55"), ("pic2d", "o", "tab:blue")]:
            part = ref[ref["family"] == family]
            ax.scatter(
                part["li7_mt205_fluxavg_b"],
                part["ratio_B_over_A_total"],
                s=28 if family == "parametric" else 52,
                marker=marker,
                color=color,
                label=family,
                alpha=0.8,
            )
        c = curve[curve["li6_atpct"] == li6].iloc[0]
        ax.errorbar(
            [row3["li7_mt205_fluxavg_b"]],
            [row3["ratio_B_over_A_total"]],
            yerr=[row3["ratio_B_over_A_total_std"]],
            fmt="*",
            markersize=14,
            color="tab:red",
            capsize=3,
            label="pic3d anchor",
        )
        ax.scatter([c["li7_mt205_fluxavg_b"]], [c["predicted_B_over_A_total"]], marker="x", s=80, color="black", label="C1 trend prediction")
        ax.axhline(1.0, color="0.25", ls="--", lw=1.0)
        ax.set_xlabel("Weighted source-average Li7 MT205 cross section (barn)")
        ax.set_ylabel("Case B / Case A total TPR")
        ax.set_title(f"C4 3D anchor on C1 trend, Li6={li6:g} at%")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figdir / f"c4_3d_anchor_curve_check_li6_{li_tag(li6)}.png", dpi=240)
        plt.close(fig)


def write_report(c4: pd.DataFrame, compare: pd.DataFrame, curve: pd.DataFrame, args: argparse.Namespace) -> None:
    lines = [
        "# C4 3D anchor Stage C and 2D/3D validation",
        "",
        f"- Nuclear data: `{CROSS_SECTIONS}`.",
        f"- Statistics: `{args.particles}` particles x `{args.batches}` batches.",
        f"- 3D source: `{PIC3D_DIR / 'neutron_source_pstar.h5'}`.",
        "- Output is per source neutron only; no absolute T/shot is reported.",
        "",
        "## Case A gate",
        "",
    ]
    for row in c4.itertuples():
        lines.append(
            f"- Li6={row.li6_atpct:g} at%: Case A total TPR/n = "
            f"`{row.A_TPR_total_per_n:.6g}` "
            f"(Li6 `{row.A_TPR_Li6_per_n:.6g}`, Li7 `{row.A_TPR_Li7_per_n:.6g}`)."
        )
    lines.extend(["", "## 3D source descriptors", ""])
    desc_cols = ["frac_E_gt_2p82", "frac_E_gt_3p1454", "li7_mt205_fluxavg_b", "frac_mu_gt_0p8"]
    first = c4.iloc[0]
    for col in desc_cols:
        lines.append(f"- `{col}` = `{float(first[col]):.6g}`.")
    lines.extend(["", "## 3D ratios", ""])
    for row in c4.itertuples():
        lines.append(
            f"- Li6={row.li6_atpct:g} at%: A'/A=`{row.ratio_Aprime_over_A_total:.6g}`, "
            f"B/A'=`{row.ratio_B_over_Aprime_total:.6g}`, "
            f"B/A=`{row.ratio_B_over_A_total:.6g}`."
        )
    lines.extend(["", "## 2D to 3D correction", ""])
    for row in compare.itertuples():
        lines.append(
            f"- Li6={row.li6_atpct:g} at%: B/A changes from "
            f"`{row.ratio_B_over_A_total_2d:.6g}` (2D) to "
            f"`{row.ratio_B_over_A_total_3d:.6g}` (3D), "
            f"ratio 3D/2D=`{row.ratio_B_over_A_total_ratio_3d_over_2d:.6g}`."
        )
    lines.extend(["", "## Universal-curve check", ""])
    for row in curve.itertuples():
        verdict = "consistent within 2 sigma" if row.consistent_with_curve_at_2sigma else "not consistent within 2 sigma"
        lines.append(
            f"- Li6={row.li6_atpct:g} at%: predicted B/A=`{row.predicted_B_over_A_total:.6g}`, "
            f"measured 3D B/A=`{row.measured_B_over_A_total:.6g}` +/- "
            f"`{row.measured_B_over_A_total_std:.2g}`, residual "
            f"`{row.residual_in_measured_sigma:.2f}` sigma -> {verdict}."
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `c4_3d_anchor_source_decomposition_summary.csv`: C4 3D rows only.",
            "- `c4_c1_plus_3d_source_decomposition_summary.csv`: C1 rows plus C4 3D rows, same C1 column format.",
            "- `c4_2d_3d_validation.csv`: descriptor and B/A correction table.",
            "- `c4_universal_curve_check.csv`: C1 trend interpolation check.",
            "- `figures/c4_3d_anchor_curve_check_li6_*.png`: visual trend check.",
            "- `openmc_runs/`: local OpenMC statepoints, not for git.",
            "",
        ]
    )
    (OUT_ROOT / "README.md").write_text("\n".join(lines))


def run_all(args: argparse.Namespace) -> None:
    configure_env()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    spec = SourceSpec(
        source_id=PIC3D_ID,
        family="pic3d",
        neutron_h5=PIC3D_DIR / "neutron_source_pstar.h5",
        deuteron_h5=PIC3D_DIR / "deuteron_beam.h5",
    )
    if args.run_openmc:
        run_openmc(args, spec)
    c4 = summarize_3d(spec)
    c1 = pd.read_csv(C1_SUMMARY)
    c4.to_csv(OUT_ROOT / "c4_3d_anchor_source_decomposition_summary.csv", index=False)
    c4_same_format = c4.reindex(columns=c1.columns)
    pd.concat([c1, c4_same_format], ignore_index=True, sort=False).to_csv(
        OUT_ROOT / "c4_c1_plus_3d_source_decomposition_summary.csv", index=False
    )
    compare, curve = compare_2d_3d(c1, c4)
    compare.to_csv(OUT_ROOT / "c4_2d_3d_validation.csv", index=False)
    curve.to_csv(OUT_ROOT / "c4_universal_curve_check.csv", index=False)
    make_plots(c1, c4, curve)
    write_report(c4, compare, curve, args)
    print(f"wrote {OUT_ROOT / 'c4_3d_anchor_source_decomposition_summary.csv'}")
    print(f"wrote {OUT_ROOT / 'c4_2d_3d_validation.csv'}")
    print(f"wrote {OUT_ROOT / 'c4_universal_curve_check.csv'}")
    print(f"wrote {OUT_ROOT / 'README.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--batches", type=int, default=100)
    parser.add_argument("--particles", type=int, default=1_000_000)
    parser.add_argument("--run-openmc", action="store_true")
    parser.add_argument("--force-openmc", action="store_true")
    args = parser.parse_args()
    run_all(args)


if __name__ == "__main__":
    main()
