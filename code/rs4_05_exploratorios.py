"""RS4-5. Exploratory associations with hardware validation (E3-E4).

Labelled exploratory (protocol v1.8, Section 11): odds ratios with 95 % CI,
Haldane-Anscombe correction when a cell is zero, no p-values and no significance claims.
L1 2016-2026 (abstract bins) and L3 (full text, unweighted; L3-P is purposive).
Output: X1_exploratorios.csv, exploratorios.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

L1 = c.load_l1()
W = L1[L1["in_window"]]
L3 = c.load_l3()
rows = []


def add(setname, df, label, mask):
    y = df["hw"].astype(bool)
    a, b = int((mask & y).sum()), int((mask & ~y).sum())
    cc, d = int((~mask & y).sum()), int((~mask & ~y).sum())
    if a + b == 0:
        return
    r = c.odds_ratio(a, b, cc, d)
    rows.append(dict(set=setname, factor=label, n_with=a + b, hw_with=a, share_with=c.rnd(a / (a + b)),
                     n_without=cc + d, hw_without=cc, share_without=c.rnd(cc / (cc + d)) if cc + d else None,
                     OR=c.rnd(r["OR"], 2), lo=c.rnd(r["lo"], 2), hi=c.rnd(r["hi"], 2), haldane=r["haldane"]))


for f in c.F_CODES:
    add("L1 2016-2026", W, f"F: {f}", W["Fl"].map(lambda v, f=f: f in v))
for a in c.A_CODES:
    add("L1 2016-2026", W, f"A: {a}", W["Al"].map(lambda v, a=a: a in v))
add("L1 2016-2026", W, "A: unassigned (A-NR)", W["Al"].map(len).eq(0))
for m in c.M_CODES:
    add("L1 2016-2026", W, f"M: {m}", W["Ml"].map(lambda v, m=m: m in v))
for t in ["T-ML", "T-SAT", "T-DT", "T-BENCH"]:
    add("L1 2016-2026", W, f"tag: {t}", W["tags"].str.contains(t, regex=False))
add("L1 2016-2026", W, "conference paper", W["conf"])

for f in c.F_CODES:
    add("L3 full text", L3, f"F: {f}", L3["Fl"].map(lambda v, f=f: f in v))
for k in ["F4t", "F4q"]:
    add("L3 full text", L3, f"F4 sub-code: {k}", L3["F4_sub"].fillna("").str.contains(k))
for a in c.A_CODES:
    add("L3 full text", L3, f"A primary: {a}", L3["Ap"] == a)
add("L3 full text", L3, "M: M1", L3["M_ft"] == "M1")
add("L3 full text", L3, "T_ML", L3["T_ML"] == "1")
add("L3 full text", L3, "fault information used (not none)", ~L3["fault_info"].fillna("none").str.lower().str.startswith("none"))
add("L3 full text", L3, "more than one simultaneous fault", L3["n_simultaneous"].fillna("").str.contains(r"[2-9]|then|and"))
add("L3 full text", L3, "period 2021-2026", L3["period"] == "2021-2026")
X = pd.DataFrame(rows)
c.save_csv(X, "X1_exploratorios.csv")
c.save_json({r["set"] + " | " + r["factor"]: {k: r[k] for k in ["n_with", "hw_with", "share_with", "OR", "lo", "hi"]} for r in rows}, "exploratorios.json")
print(X.to_string())
