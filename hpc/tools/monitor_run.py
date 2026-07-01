#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def run(cmd):
    return subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def main():
    if len(sys.argv) != 2:
        print("usage: monitor_run.py RUN_DIR", file=sys.stderr)
        return 2
    run_dir = Path(sys.argv[1]).expanduser().resolve()
    job_file = run_dir / "job_id.txt"
    if not job_file.exists():
        print(f"missing {job_file}", file=sys.stderr)
        return 2
    job_id = job_file.read_text().strip()
    proc = run(["sacct", "-j", job_id, "--format=JobID,JobName,State,ExitCode,Elapsed,NodeList", "--parsable2", "--noheader"])
    status = {
        "job_id": job_id,
        "updated_at": now(),
        "sacct_returncode": proc.returncode,
        "sacct_stdout": proc.stdout.strip().splitlines(),
        "sacct_stderr": proc.stderr.strip(),
    }
    if proc.stdout.strip():
        first = proc.stdout.strip().splitlines()[0].split("|")
        if len(first) >= 4:
            status["state"] = first[2]
            status["exit_code"] = first[3]
            status["elapsed"] = first[4] if len(first) > 4 else ""
            status["node_list"] = first[5] if len(first) > 5 else ""
    else:
        q = run(["squeue", "-j", job_id, "-h", "-o", "%T|%M|%R"])
        status["squeue_stdout"] = q.stdout.strip()
        status["squeue_stderr"] = q.stderr.strip()
        if q.stdout.strip():
            status["state"] = q.stdout.strip().split("|")[0]
    with open(run_dir / "status.json", "w") as f:
        json.dump(status, f, indent=2)
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
