"""Regenerates every result, table (CSV/JSON) and figure, including the PRISMA 2020 diagram (relative paths only).

Usage:  python3 -I run_all.py
Steps: analysis pipeline (code/rs4_00_ejecutar_todo.py; the sensitivity step takes about a minute) -> PRISMA diagram.
Outputs are written to results/ and figures/; with the same inputs they are identical to the files distributed here.
"""
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent / "code"


def run(script):
    print("==", script, flush=True)
    r = subprocess.run([sys.executable, "-I", str(CODE / script)], cwd=CODE, capture_output=True, text=True)
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print(r.stderr[-2500:])
        sys.exit(f"step failed: {script}")


run("rs4_00_ejecutar_todo.py")
run("rs5_03_prisma.py")
print("done")
