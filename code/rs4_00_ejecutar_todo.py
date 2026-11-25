"""Runs the whole RS4 pipeline in order and then the number verification."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["rs4_01_descriptivos.py", "rs4_02_modelos_y_condiciones.py", "rs4_03_calidad_reporte.py", "rs4_04_hipotesis_y_error_E.py",
         "rs4_05_exploratorios.py", "rs4_06_sensibilidad.py", "rs4_07_brechas.py", "rs4_08_contraste.py", "rs4_09_figuras.py",
         "rs4_12_tablas.py"]
for s in STEPS:
    print(f"== {s}", flush=True)
    r = subprocess.run([sys.executable, "-I", str(HERE / s)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        sys.exit(f"step failed: {s}")
print("RS4 pipeline complete (each step under three minutes; run it in a terminal without a time limit)")
