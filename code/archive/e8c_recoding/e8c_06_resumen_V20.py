"""E8-c step 6. Summary of the adjudication of the third extraction (V20, 20 studies).

Reads the adjudicated discrepancy file written by e8c_04 (columns 'adjudication (full text)' and 'source') and
writes ADJUDICACION_VERIFICACION_20.json next to it: number of field-level discrepancies, studies involved and
counts by verdict (extraction error, verification error, ambiguous). The step is assisted by generative AI.
Run: python3 -I e8c_06_resumen_V20.py
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V20 = HERE.parent / "verificacion_V20"
rows = list(csv.DictReader(open(V20 / "DISCREPANCIAS_VERIFICACION_20.csv", encoding="utf-8")))
col = "adjudication (full text)"
assert all(r[col].strip() for r in rows), "adjudication column incomplete"


def verdict(s):
    s = s.lower()
    if s.startswith("extraction error"):
        return "extraction_error"
    if s.startswith("verification error"):
        return "verification_error"
    if s.startswith("ambiguous"):
        return "ambiguous"
    raise ValueError(s)


v = [verdict(r[col]) for r in rows]
out = {
    "n_studies_sample": 20,
    "discrepancies": len(rows),
    "studies_with_discrepancy": len({r["rid"] for r in rows}),
    "extraction_error": v.count("extraction_error"),
    "verification_error": v.count("verification_error"),
    "ambiguous_extraction_kept": v.count("ambiguous"),
    "studies_extraction_corrected": len({r["rid"] for r, x in zip(rows, v) if x == "extraction_error"}),
}
(V20 / "ADJUDICACION_VERIFICACION_20.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(out)
