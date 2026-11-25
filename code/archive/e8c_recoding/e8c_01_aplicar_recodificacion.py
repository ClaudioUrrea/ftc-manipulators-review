"""E8-c step 1. Writes the fields recoded in stage E8-c into the per-study extraction files (fichas) and adds the
new columns to the L3 extraction sheet, so that the RS3 merge (rs3_s5_merge.py) carries them.

New fields (data dictionary, Supplementary Table S5):
  hw_fault_classes  E3-E4 studies only: fault classes (subset of F_ft) actually applied on hardware; NR = not stated
  hw_note           why hw_fault_classes differs from F_ft
  scope_flag        GEN (generic system class, manipulator as validation plant), NET (network of manipulators),
                    RULE-IC1, RULE-IC3, RULE-A3 (eligibility rules written in amendment 1.10)
  reserve_type      F4 and F5 studies: the structural reserve used (modeled redundant inputs, physical actuation
                    redundancy, kinematic redundancy of the arm, underactuation of the arm)
  F7_sub            F7c (cable break or damage) or F7r (reducer, backlash or wear of the transmission)
It also applies the eligibility decision on R01777 (EX-HW) and appends its note.
Input: ../RECODIFICACION_E8c.csv (rid, field, value, source). Paths are relative to this file.
Run: python3 -I e8c_01_aplicar_recodificacion.py
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RS3 = next(ROOT.glob("08 *"))
NEW = ["hw_fault_classes", "hw_note", "scope_flag", "reserve_type", "F7_sub"]
EXISTING = ["ft_eligible", "ft_exclusion"]  # eligibility decisions taken in E8-c (R01777, amendment 1.10)

rec = list(csv.DictReader(open(HERE.parent / "RECODIFICACION_E8c.csv", encoding="utf-8")))
by: dict = {}
for r in rec:
    assert r["field"] in NEW + EXISTING + ["notes_append"], r
    d = by.setdefault(r["rid"], {})
    d[r["field"]] = (d[r["field"]] + ";" + r["value"]) if (r["field"] == "scope_flag" and r["field"] in d) else r["value"]

# 1. columns of the extraction sheet (inserted before "notes")
p = RS3 / "EXTRACCION_L3_S5.csv"
rows = list(csv.DictReader(open(p, encoding="utf-8")))
cols = list(rows[0].keys())
for k in NEW:
    if k not in cols:
        cols.insert(cols.index("notes"), k)
for r in rows:
    for k in NEW:
        r.setdefault(k, "")
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    w.writerows(rows)

# 2. fichas
hw_seen = 0
for fn in sorted((RS3 / "extracciones").glob("*.json")):
    d = json.loads(fn.read_text(encoding="utf-8"))
    for k in NEW:
        d[k] = by.get(d["rid"], {}).get(k, "")
    for k in EXISTING:
        if k in by.get(d["rid"], {}):
            d[k] = by[d["rid"]][k]
    na = by.get(d["rid"], {}).get("notes_append")
    if na and na not in d.get("notes", ""):
        d["notes"] = (d.get("notes", "") + " " + na).strip()
    if d.get("ft_eligible") == "yes" and d.get("E_ft") in ("E3", "E4"):
        assert d["hw_fault_classes"], f"{d['rid']}: hardware study without hw_fault_classes"
        hw_seen += 1
        hwF = [x for x in d["hw_fault_classes"].split(";") if x and x != "NR"]
        assert set(hwF) <= set(d["F_ft"].split(";")), d["rid"]
    elif d["hw_fault_classes"]:
        raise AssertionError(f"{d['rid']}: hw_fault_classes on a non-hardware study")
    fn.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
print(f"fichas updated; hardware studies with hw_fault_classes: {hw_seen}; studies recoded: {len(by)}")
