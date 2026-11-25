"""E8-c step 3 (optional verification by the author). Draws 20 full-text studies for a blind human check of the
AI-assisted extraction: every study with a locked joint (F4q), a free-swinging joint (F5) or a transmission fault (F7),
completed at random (seed 20261125) from the rest of L3. Writes the coding sheet without the extracted codes and the key
in a separate folder that the coder must not open before delivering the sheet.
Run: python3 -I e8c_03_muestra_verificacion.py
"""
import csv
import hashlib
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent
ROOT = STAGE.parent
L3 = [r for r in csv.DictReader(open(next(ROOT.glob("08 *")) / "EXTRACCION_L3_S5.csv", encoding="utf-8")) if r["ft_eligible"] == "yes"]
SEED = 20261125
pri = [r for r in L3 if "F4q" in r["F4_sub"] or any(f in r["F_ft"].split(";") for f in ("F5", "F7"))]
pri_ids = {r["rid"] for r in pri}
rest = sorted([r for r in L3 if r["rid"] not in pri_ids], key=lambda r: r["rid"])
rng = random.Random(SEED)
sample = sorted(pri, key=lambda r: r["rid"]) + rng.sample(rest, 20 - len(pri))
rng.shuffle(sample)
FIELDS = ["E_level (E0-E4)", "hardware_fault_classes (F codes applied on the hardware run, or none)", "A_primary (A1-A4)",
          "F_codes (F0-F8; F4t or F4q)", "structural_reserve (full actuation / modeled redundant inputs / kinematic redundancy of the arm / physical actuation redundancy / underactuation / task relaxation)",
          "fault_information (none / detection / isolation / estimation / known)"]
sheet = STAGE / "VERIFICACION_AUTOR_20.csv"
with open(sheet, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["n", "rid", "doi", "first_author", "year", "title"] + FIELDS + ["comment"])
    for i, r in enumerate(sample, 1):
        w.writerow([i, r["rid"], r["doi"], r["first_author"], r["year"], r["title"]] + [""] * (len(FIELDS) + 1))
key_dir = STAGE / "NO_ABRIR_clave_verificacion_autor"
key_dir.mkdir(exist_ok=True)
with open(key_dir / "CLAVE_VERIFICACION_AUTOR_20.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "rid", "E_ft", "hw_fault_classes", "A_primary", "F_ft", "F4_sub", "reserve_type", "structural_condition", "fault_info"])
    for i, r in enumerate(sample, 1):
        w.writerow([i, r["rid"], r["E_ft"], r["hw_fault_classes"], r["A_primary"], r["F_ft"], r["F4_sub"], r["reserve_type"], r["structural_condition"], r["fault_info"]])
h = hashlib.sha256((key_dir / "CLAVE_VERIFICACION_AUTOR_20.csv").read_bytes()).hexdigest()
(key_dir / "CLAVE.sha256").write_text(h + "  CLAVE_VERIFICACION_AUTOR_20.csv\n", encoding="utf-8")
print(len(sample), "studies;", len(pri), "priority (F4q, F5, F7);", "key sha256", h[:12])
