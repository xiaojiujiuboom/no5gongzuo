"""Export Li7 MT205 tritium-production cross sections and overlay a source spectrum."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_neutron_source
from moduleC_openmc.nuclear_data import LI7_MT205_THRESHOLD_MEV


@dataclass(frozen=True)
class LibrarySpec:
    name: str
    cross_sections: Path


@dataclass(frozen=True)
class Mt205Data:
    library: str
    li7_h5: Path
    label: str
    mt: int
    redundant: int
    threshold_MeV: float
    E_MeV: np.ndarray
    sigma_b: np.ndarray


def _parse_library_arg(value: str) -> LibrarySpec:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--library must be NAME=/path/to/cross_sections.xml")
    name, path = value.split("=", 1)
    if not name:
        raise argparse.ArgumentTypeError("library NAME must not be empty")
    xs = Path(path).expanduser().resolve()
    if not xs.exists():
        raise argparse.ArgumentTypeError(f"cross_sections.xml not found: {xs}")
    return LibrarySpec(name=name, cross_sections=xs)


def _li7_path(cross_sections: Path) -> Path:
    root = ET.parse(cross_sections).getroot()
    for elem in root.findall("library"):
        materials = set((elem.attrib.get("materials") or "").split())
        if elem.attrib.get("type") == "neutron" and "Li7" in materials:
            path = Path(elem.attrib["path"])
            if not path.is_absolute():
                path = cross_sections.parent / path
            return path.resolve()
    raise ValueError(f"Li7 neutron data not listed in {cross_sections}")


def read_li7_mt205(spec: LibrarySpec) -> Mt205Data:
    li7_h5 = _li7_path(spec.cross_sections)
    with h5py.File(li7_h5, "r") as h5:
        reaction = h5["Li7/reactions/reaction_205"]
        xs_node = reaction["294K/xs"]
        threshold_idx = int(xs_node.attrs["threshold_idx"])
        xs = np.asarray(xs_node[:], dtype=float)
        energy = np.asarray(h5["Li7/energy/294K"][threshold_idx : threshold_idx + xs.size], dtype=float)
        label_raw = reaction.attrs.get("label", b"")
        label = label_raw.decode("utf-8") if isinstance(label_raw, bytes) else str(label_raw)
        return Mt205Data(
            library=spec.name,
            li7_h5=li7_h5,
            label=label,
            mt=int(reaction.attrs["mt"]),
            redundant=int(reaction.attrs.get("redundant", -1)),
            threshold_MeV=float(energy[0] / 1.0e6),
            E_MeV=energy / 1.0e6,
            sigma_b=xs,
        )


def _write_xs_csv(path: Path, datasets: list[Mt205Data]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["library", "E_MeV", "sigma_b"])
        for data in datasets:
            for E, sigma in zip(data.E_MeV, data.sigma_b):
                writer.writerow([data.library, E, sigma])


def _write_summary_csv(path: Path, datasets: list[Mt205Data], source_h5: Path | None) -> None:
    source_stats = {}
    if source_h5:
        src = read_neutron_source(source_h5)
        wsum = float(np.sum(src.weight))
        above = src.E > LI7_MT205_THRESHOLD_MEV
        source_stats = {
            "source_h5": str(source_h5),
            "source_N": float(src.E.size),
            "source_Y_total": wsum,
            "source_weighted_E_mean_MeV": float(np.average(src.E, weights=src.weight)),
            "source_E_max_MeV": float(np.max(src.E)),
            "source_weight_frac_E_gt_3p1454": float(np.sum(src.weight[above]) / wsum),
        }

    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "library",
            "mt",
            "label",
            "redundant",
            "threshold_MeV",
            "max_sigma_b",
            "E_at_max_sigma_MeV",
            "li7_h5",
            *source_stats.keys(),
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in datasets:
            imax = int(np.argmax(data.sigma_b))
            row = {
                "library": data.library,
                "mt": data.mt,
                "label": data.label,
                "redundant": data.redundant,
                "threshold_MeV": data.threshold_MeV,
                "max_sigma_b": float(data.sigma_b[imax]),
                "E_at_max_sigma_MeV": float(data.E_MeV[imax]),
                "li7_h5": str(data.li7_h5),
            }
            row.update(source_stats)
            writer.writerow(row)


def _plot(path: Path, datasets: list[Mt205Data], source_h5: Path | None) -> None:
    import matplotlib.pyplot as plt

    fig, ax_xs = plt.subplots(figsize=(7.4, 4.8))
    for data in datasets:
        ax_xs.plot(data.E_MeV, data.sigma_b, linewidth=1.8, label=data.library)
    ax_xs.axvline(
        LI7_MT205_THRESHOLD_MEV,
        color="black",
        linestyle="--",
        linewidth=1.0,
        label=f"MT205 threshold {LI7_MT205_THRESHOLD_MEV:g} MeV",
    )
    ax_xs.set_xlabel("Incident neutron energy (MeV)")
    ax_xs.set_ylabel("Li7 MT205 (n,Xt) cross section (barn)")
    ax_xs.set_xlim(2.0, 8.5)
    ax_xs.set_ylim(bottom=0.0)

    if source_h5:
        src = read_neutron_source(source_h5)
        bins = np.linspace(2.0, max(8.5, float(np.max(src.E))), 110)
        hist, edges = np.histogram(src.E, bins=bins, weights=src.weight)
        norm = float(np.max(hist)) if np.max(hist) > 0 else 1.0
        mids = 0.5 * (edges[:-1] + edges[1:])
        ax_src = ax_xs.twinx()
        ax_src.step(mids, hist / norm, where="mid", color="0.35", alpha=0.55, label="PIC-DD neutron spectrum")
        ax_src.set_ylabel("Neutron source spectrum (normalized)")
        lines, labels = ax_xs.get_legend_handles_labels()
        lines2, labels2 = ax_src.get_legend_handles_labels()
        ax_xs.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=8)
    else:
        ax_xs.legend(loc="upper right", fontsize=8)

    ax_xs.set_title("Li7 MT205 tritium production vs PIC-DD neutron spectrum")
    fig.tight_layout()
    fig.savefig(path, dpi=240)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", action="append", type=_parse_library_arg, required=True)
    parser.add_argument("--source-h5", default=None)
    parser.add_argument("--output-dir", default="hpc/results")
    parser.add_argument("--prefix", default="li7_mt205")
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    source_h5 = Path(args.source_h5).expanduser().resolve() if args.source_h5 else None
    datasets = [read_li7_mt205(spec) for spec in args.library]
    _write_xs_csv(outdir / f"{args.prefix}_xs_libraries.csv", datasets)
    _write_summary_csv(outdir / f"{args.prefix}_library_summary.csv", datasets, source_h5)
    _plot(outdir / f"{args.prefix}_xs_with_neutron_spectrum.png", datasets, source_h5)
    print(f"wrote {outdir / f'{args.prefix}_xs_libraries.csv'}")
    print(f"wrote {outdir / f'{args.prefix}_library_summary.csv'}")
    print(f"wrote {outdir / f'{args.prefix}_xs_with_neutron_spectrum.png'}")


if __name__ == "__main__":
    main()

