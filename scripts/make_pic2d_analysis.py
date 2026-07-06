"""Build compact analysis products for the completed 2D full-chain scan."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "hpc" / "results" / "full_chain_20260706"
SCAN_DIR = ROOT / "hpc" / "results" / "pic2d_scan16x40_20260706"


def _fmt_sci(value: float) -> str:
    return f"{value:.3e}"


def _fmt_float(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _to_markdown(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    rows = [[str(v) for v in row] for row in df.to_numpy()]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    header = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |"
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body = ["| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def build_paper_table() -> pd.DataFrame:
    nat = pd.read_csv(RESULT_DIR / "pic2d_full_chain_natural_li_summary.csv")
    enr = pd.read_csv(RESULT_DIR / "pic2d_full_chain_li6_90_summary.csv")
    full = pd.read_csv(RESULT_DIR / "pic2d_full_chain_openmc_summary.csv")
    trends = pd.read_csv(SCAN_DIR / "pic2d_scan16x40_rear10_Egt0p4_trends.csv")

    paper = nat.merge(
        enr[
            [
                "source_id",
                "CaseB_T_Li_total_split_per_shot",
                "CaseB_Li7_fraction_of_Li_total",
            ]
        ],
        on="source_id",
        suffixes=("_natural", "_li6_90"),
    )
    paper = paper.merge(
        full[full["li6_atpct"] == 7.59][
            [
                "source_id",
                "D_macro_Egt0p4",
                "D_weight_Egt0p4_per_shot",
                "D_E_weighted_mean_MeV",
                "D_E_max_MeV",
                "D_weight_frac_mu_gt_0p8",
                "CaseB_T_Li6_per_shot",
                "CaseB_T_Li7_per_shot",
                "CaseB_TPR_Li_total_split_rel_err",
            ]
        ],
        on="source_id",
    )
    paper = paper.merge(
        trends[["a0", "thickness_um", "last_window_ddn_frac", "E_yield_weighted_mean_MeV"]],
        on=["a0", "thickness_um"],
    )
    paper = paper.rename(
        columns={
            "CaseB_T_Li_total_split_per_shot_natural": "T_total_natural_per_shot",
            "CaseB_T_Li_total_split_per_shot_li6_90": "T_total_li6_90_per_shot",
            "CaseB_Li7_fraction_of_Li_total_natural": "Li7_fraction_natural",
            "CaseB_Li7_fraction_of_Li_total_li6_90": "Li7_fraction_li6_90",
        }
    )
    paper["T_total_li6_90_over_natural"] = paper["T_total_li6_90_per_shot"] / paper["T_total_natural_per_shot"]
    paper["scan_family"] = np.where(
        (paper["thickness_um"] == 3.0) & (paper["a0"] != 10.0),
        "a0_scan",
        np.where((paper["a0"] == 10.0) & (paper["thickness_um"] != 3.0), "thickness_scan", "baseline"),
    )
    order = {
        "pic2d_a0_10_t_1um": 0,
        "pic2d_a0_10_t_2um": 1,
        "pic2d_a0_05_t_3um": 2,
        "pic2d_a0_10_t_3um": 3,
        "pic2d_a0_15_t_3um": 4,
        "pic2d_a0_20_t_3um": 5,
        "pic2d_a0_10_t_4um": 6,
    }
    paper["plot_order"] = paper["source_id"].map(order)
    return paper.sort_values("plot_order").reset_index(drop=True)


def write_markdown_tables(paper: pd.DataFrame) -> None:
    md = RESULT_DIR / "pic2d_analysis_tables.md"
    nat_cols = [
        "source_id",
        "DD_neutron_Y_per_shot",
        "n_E_weighted_mean_MeV",
        "n_weight_frac_E_gt_3p1454",
        "CaseB_TPR_Li6_per_n",
        "CaseB_TPR_Li7_per_n",
        "T_total_natural_per_shot",
        "CaseB_T_Li_total_split_per_shot_rel_to_a10_t3",
        "Li7_fraction_natural",
    ]
    compact = paper[nat_cols].copy()
    compact.columns = [
        "point",
        "DD n/shot",
        "mean n E MeV",
        "frac n >3.145 MeV",
        "Li6 TPR/n",
        "Li7 TPR/n",
        "natural Li T/shot",
        "rel. total T",
        "Li7 fraction",
    ]
    for col in ["DD n/shot", "Li6 TPR/n", "Li7 TPR/n", "natural Li T/shot"]:
        compact[col] = compact[col].map(_fmt_sci)
    for col in ["mean n E MeV", "frac n >3.145 MeV", "rel. total T", "Li7 fraction"]:
        compact[col] = compact[col].map(lambda x: _fmt_float(x, 3))

    enriched = paper[
        [
            "source_id",
            "T_total_li6_90_per_shot",
            "T_total_li6_90_over_natural",
            "Li7_fraction_li6_90",
            "CaseB_TPR_Li_total_split_rel_err",
        ]
    ].copy()
    enriched.columns = ["point", "Li6=90% T/shot", "enriched/natural", "Li7 fraction at 90%", "OpenMC total rel.err."]
    enriched["Li6=90% T/shot"] = enriched["Li6=90% T/shot"].map(_fmt_sci)
    for col in ["enriched/natural", "Li7 fraction at 90%", "OpenMC total rel.err."]:
        enriched[col] = enriched[col].map(lambda x: _fmt_float(x, 4))

    text = "\n".join(
        [
            "# 2D Full-Chain Analysis Tables",
            "",
            "Generated from the completed 2D PIC -> Stage B -> OpenMC chain.",
            "",
            "## Natural Lithium",
            "",
            _to_markdown(compact),
            "",
            "## Enriched Lithium and Statistics",
            "",
            _to_markdown(enriched),
            "",
        ]
    )
    md.write_text(text, encoding="utf-8")


def make_dashboard(paper: pd.DataFrame) -> None:
    a0_scan = paper[paper["thickness_um"] == 3.0].sort_values("a0")
    t_scan = paper[paper["a0"] == 10.0].sort_values("thickness_um")
    labels = [f"a{int(row.a0)}\nt{row.thickness_um:g}um" for row in paper.itertuples()]
    x = np.arange(len(paper))

    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.25})
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)

    ax = axes[0, 0]
    ax.plot(a0_scan["a0"], a0_scan["DD_neutron_Y_per_shot"], marker="o", label="DD n/shot")
    ax.plot(a0_scan["a0"], a0_scan["T_total_natural_per_shot"], marker="s", label="natural Li T/shot")
    ax.set_yscale("log")
    ax.set_xlabel("a0 at thickness=3 um")
    ax.set_title("a0 scan yield")
    ax.legend()

    ax = axes[0, 1]
    ax.plot(t_scan["thickness_um"], t_scan["DD_neutron_Y_per_shot"], marker="o", label="DD n/shot")
    ax.plot(t_scan["thickness_um"], t_scan["T_total_natural_per_shot"], marker="s", label="natural Li T/shot")
    ax.set_yscale("log")
    ax.set_xlabel("thickness um at a0=10")
    ax.set_title("thickness scan yield")
    ax.legend()

    ax = axes[0, 2]
    ax.bar(x - 0.2, paper["n_weight_frac_E_gt_3p1454"], width=0.4, label="n > 3.145 MeV")
    ax.bar(x + 0.2, paper["Li7_fraction_natural"], width=0.4, label="Li7 fraction of T")
    ax.set_xticks(x, labels, rotation=0)
    ax.set_ylim(0, max(0.55, paper["Li7_fraction_natural"].max() * 1.15))
    ax.set_title("Li7 threshold leverage")
    ax.legend()

    ax = axes[1, 0]
    ax.plot(a0_scan["a0"], a0_scan["D_E_max_MeV"], marker="o", label="D Emax")
    ax.plot(a0_scan["a0"], a0_scan["E_yield_weighted_mean_MeV"], marker="s", label="D-D-yield-mean E")
    ax.set_xlabel("a0 at thickness=3 um")
    ax.set_ylabel("MeV")
    ax.set_title("deuteron energy in a0 scan")
    ax.legend()

    ax = axes[1, 1]
    ax.bar(x - 0.2, paper["T_total_natural_per_shot"], width=0.4, label="natural Li")
    ax.bar(x + 0.2, paper["T_total_li6_90_per_shot"], width=0.4, label="Li6=90%")
    ax.set_yscale("log")
    ax.set_xticks(x, labels, rotation=0)
    ax.set_title("lithium enrichment effect")
    ax.legend()

    ax = axes[1, 2]
    ax.bar(x, 100.0 * paper["last_window_ddn_frac"])
    ax.set_xticks(x, labels, rotation=0)
    ax.set_ylabel("last 250 fs / 0-6 ps, %")
    ax.set_ylim(0.0, max(0.2, 100.0 * paper["last_window_ddn_frac"].max() * 1.25))
    ax.set_title("source time convergence (<10% criterion)")
    ax.text(0.02, 0.92, "all bars <0.2%", transform=ax.transAxes, ha="left", va="top")

    fig.suptitle("2D PIC -> D-D neutron source -> OpenMC lithium TPR, rear+10, E_D>0.4 MeV", fontsize=12)
    fig.savefig(RESULT_DIR / "pic2d_full_chain_analysis_dashboard.png", dpi=220)
    plt.close(fig)


def main() -> None:
    paper = build_paper_table()
    paper.to_csv(RESULT_DIR / "pic2d_paper_summary.csv", index=False)
    write_markdown_tables(paper)
    make_dashboard(paper)
    print(f"wrote {RESULT_DIR / 'pic2d_paper_summary.csv'}")
    print(f"wrote {RESULT_DIR / 'pic2d_analysis_tables.md'}")
    print(f"wrote {RESULT_DIR / 'pic2d_full_chain_analysis_dashboard.png'}")


if __name__ == "__main__":
    main()
