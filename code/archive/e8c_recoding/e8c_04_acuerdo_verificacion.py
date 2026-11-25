"""E8-c step 4. Agreement between an independent blind coding of the 20-study verification sample and the extraction.

Run only after the coded sheet has been frozen (its SHA-256 written next to it). The key's SHA-256 is checked against
CLAVE.sha256 before it is read. Field-level agreement is reported as a proportion with a Wilson 95% interval, plus Cohen's
kappa for single-label fields; fault-class sets are compared as exact sets and by Jaccard index. Free-text key fields
(structural reserve, fault information) are mapped to the categories of Table 3 with fixed keyword rules.

Run: python3 -I e8c_04_acuerdo_verificacion.py <coded sheet .csv>
Writes, next to the coded sheet: ACUERDO_VERIFICACION_20.json and DISCREPANCIAS_VERIFICACION_20.csv
"""
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent
KEY_DIR = STAGE / "NO_ABRIR_clave_verificacion_autor"
KEY = KEY_DIR / "CLAVE_VERIFICACION_AUTOR_20.csv"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wilson(k, n, z=1.959964):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def kappa(a, b):
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def fset(s):
    """Fault-class set: F4t and F4q collapse to F4; 'none' and empty give the empty set; NR is kept."""
    s = (s or "").strip()
    if s.lower() in ("", "none", "-", "n/a"):
        return frozenset()
    toks = [t.strip().upper() for t in re.split(r"[;,/\s]+", s) if t.strip()]
    return frozenset("F4" if t in ("F4T", "F4Q") else t for t in toks)


def f4sub(s):
    m = re.search(r"F4([TQ])", (s or "").upper())
    return "F4" + m.group(1).lower() if m else ""


def info3(s):
    s = (s or "").lower()
    if not s.strip():
        return ""
    if re.search(r"\b(detect|isolat|estimat|diagnos|observer|identif)", s) and not re.search(r"assumed|left to future", s):
        return "obtained"
    if re.search(r"known|full knowledge|assumed|given", s):
        return "known"
    if s.startswith("none"):
        return "none"
    return "other"


RESERVE_RULES = [
    (r"modeled redundant", "modeled redundant inputs"),
    (r"full actuation", "full actuation"),
    (r"kinematic|hyper-redundan", "kinematic redundancy of the arm"),
    (r"physical actuation|actuation redundancy|redundant actuation", "physical actuation redundancy"),
    (r"underactuat", "underactuation"),
    (r"task|degradation|abandon|underconstrained", "task relaxation"),
]


def reserve_set(text):
    t = (text or "").lower()
    return frozenset(lab for pat, lab in RESERVE_RULES if re.search(pat, t))


def norm(s):
    return (s or "").strip().upper()


def col(row, prefix):
    for k in row:
        if k and k.strip().lower().startswith(prefix.lower()):
            return row[k]
    raise KeyError(prefix)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: e8c_04_acuerdo_verificacion.py <coded sheet .csv>")
    coded = Path(sys.argv[1]).resolve()
    frozen = coded.with_suffix(coded.suffix + ".sha256")
    if not frozen.exists() or frozen.read_text(encoding="utf-8").split()[0] != sha256(coded):
        sys.exit("the coded sheet is not frozen or was modified after freezing")
    expected = (KEY_DIR / "CLAVE.sha256").read_text(encoding="utf-8").split()[0]
    if sha256(KEY) != expected:
        sys.exit("key SHA-256 does not match CLAVE.sha256")

    key = {r["rid"]: r for r in csv.DictReader(open(KEY, encoding="utf-8"))}
    rows = list(csv.DictReader(open(coded, encoding="utf-8-sig")))
    if sorted(r["rid"] for r in rows) != sorted(key):
        sys.exit("the coded sheet does not hold the 20 sampled studies")

    fields = {k: ([], []) for k in ("E_level", "hardware_validated", "A_primary", "F4_sub", "fault_information")}
    sets = {"F_codes": [], "hardware_fault_classes": []}
    reserve_hits, disc = [], []
    for r in sorted(rows, key=lambda x: x["rid"]):
        k = key[r["rid"]]
        c_e, k_e = norm(col(r, "E_level")), norm(k["E_ft"])
        pairs = {
            "E_level": (c_e, k_e),
            "hardware_validated": (str(c_e in ("E3", "E4")), str(k_e in ("E3", "E4"))),
            "A_primary": (norm(col(r, "A_primary")), norm(k["A_primary"])),
            "F4_sub": (f4sub(col(r, "F_codes")), k["F4_sub"]),
            "fault_information": (info3(col(r, "fault_information")), info3(k["fault_info"])),
        }
        for f, (a, b) in pairs.items():
            fields[f][0].append(a)
            fields[f][1].append(b)
            if a != b:
                disc.append([r["rid"], f, a, b])
        for f, ca, ka in (("F_codes", col(r, "F_codes"), k["F_ft"]),
                          ("hardware_fault_classes", col(r, "hardware_fault_classes"), k["hw_fault_classes"])):
            a, b = fset(ca), fset(ka)
            jac = 1.0 if not (a | b) else len(a & b) / len(a | b)
            sets[f].append((a == b, jac))
            if a != b:
                disc.append([r["rid"], f, ";".join(sorted(a)) or "none", ";".join(sorted(b)) or "none"])
        cres = col(r, "structural_reserve").strip().lower()
        kres = reserve_set(k["reserve_type"]) or reserve_set(k["structural_condition"])
        hit = any(lab == cres or lab in cres for lab in kres)
        reserve_hits.append(hit)
        if not hit:
            disc.append([r["rid"], "structural_reserve", cres, " | ".join(sorted(kres))])

    n = len(rows)
    out = {"n": n, "coded_sheet_sha256": sha256(coded), "key_sha256": expected, "fields": {}}
    for f, (a, b) in fields.items():
        k_ = sum(x == y for x, y in zip(a, b))
        out["fields"][f] = {"agree": k_, "n": n, "prop": round(k_ / n, 3), "wilson95": wilson(k_, n), "kappa": kappa(a, b)}
    for f, v in sets.items():
        k_ = sum(e for e, _ in v)
        out["fields"][f] = {"exact_agree": k_, "n": n, "prop": round(k_ / n, 3), "wilson95": wilson(k_, n),
                            "mean_jaccard": round(sum(j for _, j in v) / n, 3)}
    k_ = sum(reserve_hits)
    out["fields"]["structural_reserve"] = {"agree": k_, "n": n, "prop": round(k_ / n, 3), "wilson95": wilson(k_, n)}
    tot = sum(v.get("agree", v.get("exact_agree")) for f, v in out["fields"].items() if f != "hardware_validated")
    cnt = n * (len(out["fields"]) - 1)
    out["overall_fields_agree"] = {"agree": tot, "n": cnt, "prop": round(tot / cnt, 3)}

    (coded.parent / "ACUERDO_VERIFICACION_20.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    with open(coded.parent / "DISCREPANCIAS_VERIFICACION_20.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rid", "field", "verification", "extraction", "adjudication (full text)", "source (page/section)"])
        w.writerows(d + ["", ""] for d in disc)
    for f, v in out["fields"].items():
        print(f, v)
    print("overall", out["overall_fields_agree"], "| discrepancies", len(disc))


if __name__ == "__main__":
    main()
