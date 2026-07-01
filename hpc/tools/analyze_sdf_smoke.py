#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path


def now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def main():
    if len(sys.argv) != 2:
        print("usage: analyze_sdf_smoke.py RUN_DIR", file=sys.stderr)
        return 2
    run_dir = Path(sys.argv[1]).expanduser().resolve()
    data_dir = run_dir / "Data"
    sdf_files = sorted(data_dir.glob("*.sdf"))
    summary = {
        "run_dir": str(run_dir),
        "data_dir": str(data_dir),
        "analyzed_at": now(),
        "analysis_status": "no_sdf",
        "sdf_count": len(sdf_files),
        "sdf_files": [p.name for p in sdf_files],
    }
    metrics = {
        "run_dir": str(run_dir),
        "analyzed_at": summary["analyzed_at"],
        "analysis_status": "no_sdf",
        "sdf_count": len(sdf_files),
    }
    if sdf_files:
        try:
            from sdf_helper import sdfr
            latest = sdf_files[-1]
            data = sdfr(str(latest))
            keys = [k for k in data.__dict__ if not k.startswith("_")]
            interesting = [
                k for k in keys
                if "deuteron" in k.lower()
                or "density" in k.lower()
                or "Particles" in k
                or "Px" in k
                or "Py" in k
                or "Weight" in k
            ]
            summary.update({
                "analysis_status": "ok",
                "latest_sdf": latest.name,
                "key_count": len(keys),
                "interesting_keys": interesting[:120],
            })
            metrics.update({
                "analysis_status": "ok",
                "latest_sdf": latest.name,
                "has_deuteron": any("deuteron" in k.lower() for k in keys),
                "has_deuteron_px": any("px_deuteron" in k.lower() for k in keys),
                "has_deuteron_py": any("py_deuteron" in k.lower() for k in keys),
                "has_deuteron_weight": any("weight_deuteron" in k.lower() for k in keys),
                "has_deuteron_density": any("density_deuteron" in k.lower() for k in keys),
            })
        except Exception as exc:
            summary["analysis_status"] = "failed"
            summary["error"] = repr(exc)
            metrics["analysis_status"] = "failed"
            metrics["error"] = repr(exc)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    return 0 if metrics["analysis_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

