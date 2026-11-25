"""RS4-1. Descriptive synthesis (protocol v1.8, Section 11, first bullet).

Outputs (resultados/):
  D1_registros_por_anio_fuente.csv   screened records and L1 by year and source
  D2_distribuciones_L1.csv           F, A, M, E bin and tags in L1 (all years and 2016-2026)
  D3_distribuciones_L3.csv           F, A (primary and all), M, E level and tags in L3 (full text)
  D4_FxA_L3.csv                      primary F x A map (L3): counts, hardware counts, evidence profile
  D5_FxA_L1_descriptivo.csv          F x A map of L1 (descriptive only; agreement in footnote)
  D6_FxA_L3_por_M.csv, D7_FxA_L3_por_periodo.csv, D8_FxA_L1_por_M_periodo.csv
  descriptivos.json                  headline numbers
"""
from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

out: dict = {}

# ---------------------------------------------------------------- D1
s6 = c.load_s6()
L1 = c.load_l1()
rows = []
for y, g in s6.groupby("year"):
    l1y = L1[L1["year"] == y]
    rows.append(dict(year=y, screened=len(g), screened_wos=int(g["in_wos"].sum()), screened_scopus=int(g["in_scopus"].sum()),
                     L1=len(l1y), L1_wos_only=int((l1y["source"] == "WOS").sum()), L1_scopus_only=int((l1y["source"] == "SCOPUS").sum()),
                     L1_both=int((l1y["source"] == "BOTH").sum()), L1_conf=int(l1y["conf"].sum()),
                     L1_E0E2=int((l1y["E_bin"] == "E0-E2").sum()), L1_E3=int((l1y["E_bin"] == "E3").sum()), L1_E4=int((l1y["E_bin"] == "E4").sum())))
D1 = pd.DataFrame(rows)
c.save_csv(D1, "D1_registros_por_anio_fuente.csv")
out["screened"] = len(s6)
out["L1_n"] = len(L1)
out["L1_window_n"] = int(L1["in_window"].sum())
out["L1_first_year"] = int(L1["year"].min())
out["L1_source"] = L1["source"].value_counts().to_dict()
out["L1_conf_n"] = int(L1["conf"].sum())
out["L1_window_by_period"] = L1[L1["in_window"]]["period"].value_counts().to_dict()
out["L1_window_E_bin"] = L1[L1["in_window"]]["E_bin"].value_counts().to_dict()
out["L1_E_bin"] = L1["E_bin"].value_counts().to_dict()
w = L1[L1["in_window"]]
out["L1_window_share_2021_2026"] = c.rnd((w["period"] == "2021-2026").mean())
out["L1_window_hw_share"] = c.rnd(w["hw"].mean())
out["L1_window_hw_share_ci"] = [c.rnd(x) for x in c.wilson(w["hw"].sum(), len(w))]
for per, g in w.groupby("period"):
    out[f"L1_hw_share_{per}"] = c.rnd(g["hw"].mean())
    out[f"L1_n_{per}"] = len(g)
out["UNCERTAIN_primary_n"] = int(((s6["layer"] == "P") & (s6["decision"] == "UNCERTAIN")).sum())

# ---------------------------------------------------------------- D2
def dist(df, col_list, codes, label, base):
    r = []
    for k in codes:
        n = int(df[col_list].map(lambda v: k in v).sum())
        r.append(dict(set=label, dimension=col_list[:-1], code=k, n=n, share=c.rnd(n / base) if base else None))
    return r


rows = []
for lab, df in [("L1 all years", L1), ("L1 2016-2026", w)]:
    base = len(df)
    rows += dist(df, "Fl", c.F_CODES, lab, base)
    rows += dist(df, "Al", c.A_CODES, lab, base)
    n_anr = int(df["Al"].map(len).eq(0).sum())
    rows.append(dict(set=lab, dimension="A", code="A-NR (unassigned)", n=n_anr, share=c.rnd(n_anr / base)))
    rows += dist(df, "Ml", c.M_CODES, lab, base)
    for e in c.E_ORDER:
        n = int((df["E_bin"] == e).sum())
        rows.append(dict(set=lab, dimension="E bin", code=e, n=n, share=c.rnd(n / base)))
    for t in c.TAGS:
        n = int(df["tags"].str.contains(t, regex=False).sum())
        rows.append(dict(set=lab, dimension="tag", code=t, n=n, share=c.rnd(n / base)))
    rows.append(dict(set=lab, dimension="flag", code="M1-FALLBACK", n=int(df["flags"].str.contains("M1-FALLBACK").sum()), share=None))
    rows.append(dict(set=lab, dimension="flag", code="multi-label F", n=int(df["Fl"].map(len).gt(1).sum()), share=None))
D2 = pd.DataFrame(rows)
c.save_csv(D2, "D2_distribuciones_L1.csv")

# ---------------------------------------------------------------- D3
L3 = c.load_l3()
out["L3_n"] = len(L3)
out["L3_by_sample"] = L3["sample"].value_counts().to_dict()
out["L3_own_n"] = int(L3["own"].sum())
rows = []
base = len(L3)
for k in c.F_CODES:
    n = int(L3["Fl"].map(lambda v: k in v).sum())
    rows.append(dict(dimension="F", code=k, n=n, share=c.rnd(n / base)))
for k in ["F4t", "F4q"]:
    n = int((L3["F4_sub"].fillna("").str.contains(k)).sum())
    rows.append(dict(dimension="F4 sub-code", code=k, n=n, share=c.rnd(n / base)))
for k in c.A_CODES:
    n = int((L3["Ap"] == k).sum())
    rows.append(dict(dimension="A primary", code=k, n=n, share=c.rnd(n / base)))
for k in c.A_CODES:
    n = int(L3["Al"].map(lambda v: k in v).sum())
    rows.append(dict(dimension="A any", code=k, n=n, share=c.rnd(n / base)))
for k in c.M_CODES:
    n = int((L3["M_ft"] == k).sum())
    rows.append(dict(dimension="M", code=k, n=n, share=c.rnd(n / base)))
for k in range(5):
    n = int((L3["E_lev"] == k).sum())
    rows.append(dict(dimension="E level", code=f"E{k}", n=n, share=c.rnd(n / base)))
for k in ["T_ML", "T_DT", "T_OPEN", "T_BENCH"]:
    n = int((L3[k] == "1").sum())
    rows.append(dict(dimension="tag", code=k, n=n, share=c.rnd(n / base)))
n_multi = int(L3["Fl"].map(len).gt(1).sum())
rows.append(dict(dimension="F", code="more than one F code", n=n_multi, share=c.rnd(n_multi / base)))
D3 = pd.DataFrame(rows)
c.save_csv(D3, "D3_distribuciones_L3.csv")
out["L3_hw_n"] = int(L3["hw"].sum())
out["L3_E4_n"] = int(L3["E4"].sum())
out["L3_E_levels"] = {f"E{k}": int((L3['E_lev'] == k).sum()) for k in range(5)}
out["L3_A_primary"] = {k: int((L3["Ap"] == k).sum()) for k in c.A_CODES}
out["L3_M"] = {k: int((L3["M_ft"] == k).sum()) for k in c.M_CODES}
out["L3_F"] = {k: int(L3["Fl"].map(lambda v, k=k: k in v).sum()) for k in c.F_CODES}
out["L3_F_multi_n"] = n_multi
out["L3_F1_any_share"] = c.rnd(out["L3_F"]["F1"] / base)
out["L3_TML_n"] = int((L3["T_ML"] == "1").sum())

# ---------------------------------------------------------------- D4 F x A (L3)
def fxa(df, fcol, aget, label_extra=None):
    r = []
    for f, a in product(c.F_CODES, c.A_CODES):
        sub = df[df[fcol].map(lambda v: f in v) & df.apply(lambda x: aget(x, a), axis=1)]
        rec = dict(F=f, A=a, n=len(sub))
        if "E_lev" in df:
            # full text: hardware evidence counted by pair (the fault class was applied on hardware), stage E8-c
            hwp = sub["hw"] & sub["hwF"].map(lambda v, f=f: f in v) if len(sub) else sub["hw"]
            rec.update(n_E0E2=int((~hwp).sum()), n_E3=int((hwp & (sub["E_lev"] == 3)).sum()), n_E4=int((hwp & (sub["E_lev"] == 4)).sum()),
                       n_hw_study=int(sub["hw"].sum()), n_hw_no_EAMBIG=int((hwp & ~sub["E_AMBIG"]).sum()),
                       rids_hw=";".join(sub.loc[hwp, "rid"]) if len(sub) else "")
        else:
            rec.update(n_E0E2=int((sub["E_bin"] == "E0-E2").sum()), n_E3=int((sub["E_bin"] == "E3").sum()), n_E4=int((sub["E_bin"] == "E4").sum()))
        rec["n_hw"] = rec["n_E3"] + rec["n_E4"]
        rec["status"] = "empty" if rec["n"] == 0 else ("simulation or analysis only" if rec["n_hw"] == 0 else "hardware evidence")
        rec["rids"] = ";".join(sub["rid"]) if "rid" in sub and len(sub) <= 60 else ""
        if label_extra:
            rec.update(label_extra)
        r.append(rec)
    return pd.DataFrame(r)


D4 = fxa(L3, "Fl", lambda x, a: x["Ap"] == a)
c.save_csv(D4, "D4_FxA_L3.csv")
core = D4[D4["F"].isin(["F1", "F2", "F3", "F4", "F5", "F6", "F7"])]  # actuator and joint fault models (F0, F8 secondary)
out["L3_FxA_cells_total_core"] = len(core)
out["L3_FxA_empty_core"] = int((core["status"] == "empty").sum())
out["L3_FxA_simonly_core"] = int((core["status"] == "simulation or analysis only").sum())
out["L3_FxA_hw_core"] = int((core["status"] == "hardware evidence").sum())
out["L3_FxA_hw_core_study_level"] = int((core["n_hw_study"] > 0).sum())  # attribution by study (before stage E8-c)
out["L3_FxA_hw_core_no_EAMBIG"] = int((core["n_hw_no_EAMBIG"] > 0).sum())
out["L3_FxA_hw_ge3_core"] = int((core["n_hw"] >= 3).sum())
out["L3_hw_pairs_reduced"] = int((L3["hw"] & L3["Fl"].map(len).gt(L3["hwF"].map(len))).sum())
out["L3_FxA_top"] = D4.sort_values("n", ascending=False).head(6)[["F", "A", "n", "n_hw"]].to_dict("records")

# ---------------------------------------------------------------- D5 F x A (L1, descriptive)
D5a = fxa(L1, "Fl", lambda x, a: a in x["Al"], dict(set="L1 all years"))
D5b = fxa(w, "Fl", lambda x, a: a in x["Al"], dict(set="L1 2016-2026"))
D5 = pd.concat([D5a, D5b])
D5["rids"] = ""
c.save_csv(D5, "D5_FxA_L1_descriptivo.csv")
core1 = D5a[D5a["F"].isin(["F1", "F2", "F3", "F4", "F5", "F6", "F7"])]
out["L1_FxA_empty_core"] = int((core1["n"] == 0).sum())
out["L1_FxA_simonly_core"] = int(((core1["n"] > 0) & (core1["n_hw"] == 0)).sum())

# ---------------------------------------------------------------- D6-D8 by M and period
rows = []
for mgrp, df in [("M1 serial", L3[L3["M_ft"] == "M1"]), ("M2-M6 other classes", L3[L3["M_ft"] != "M1"])]:
    t = fxa(df, "Fl", lambda x, a: x["Ap"] == a, dict(M_group=mgrp, n_group=len(df)))
    rows.append(t)
D6 = pd.concat(rows)
c.save_csv(D6, "D6_FxA_L3_por_M.csv")
rows = []
for per, df in L3.groupby("period"):
    rows.append(fxa(df, "Fl", lambda x, a: x["Ap"] == a, dict(period=per, n_group=len(df))))
D7 = pd.concat(rows)
c.save_csv(D7, "D7_FxA_L3_por_periodo.csv")
out["L3_by_period"] = L3["period"].value_counts().to_dict()
out["L3_A_primary_by_period"] = {p: {a: int((g["Ap"] == a).sum()) for a in c.A_CODES} for p, g in L3.groupby("period")}
out["L3_A_primary_share_by_period"] = {p: {a: c.rnd((g["Ap"] == a).mean()) for a in c.A_CODES} for p, g in L3.groupby("period")}
out["L1_n_2027_early_access"] = int((L1["year"] == 2027).sum())
out["L3_hw_by_period"] = {p: int(g["hw"].sum()) for p, g in L3.groupby("period")}

rows = []
for m in c.M_CODES:
    df = w[w["Ml"].map(lambda v, m=m: m in v)]
    t = fxa(df, "Fl", lambda x, a: a in x["Al"], dict(group=f"M:{m}", n_group=len(df)))
    rows.append(t)
for per, df in w.groupby("period"):
    rows.append(fxa(df, "Fl", lambda x, a: a in x["Al"], dict(group=f"period:{per}", n_group=len(df))))
D8 = pd.concat(rows)
D8["rids"] = ""
c.save_csv(D8, "D8_FxA_L1_por_M_periodo.csv")

# M and period summaries for the text (L1 window)
out["L1_window_M"] = {m: int(w["Ml"].map(lambda v, m=m: m in v).sum()) for m in c.M_CODES}
out["L1_window_hw_by_M"] = {m: c.rnd(w[w["Ml"].map(lambda v, m=m: m in v)]["hw"].mean()) for m in c.M_CODES}
out["L1_window_A"] = {a: int(w["Al"].map(lambda v, a=a: a in v).sum()) for a in c.A_CODES}
out["L1_window_A_NR"] = int(w["Al"].map(len).eq(0).sum())
out["L1_window_F"] = {f: int(w["Fl"].map(lambda v, f=f: f in v).sum()) for f in c.F_CODES}
out["L1_window_F0_share"] = c.rnd(w["Fl"].map(lambda v: v == ["F0"]).mean())
out["L1_window_TML_share"] = c.rnd(w["tags"].str.contains("T-ML").mean())
out["L1_TML_share_by_period"] = {p: c.rnd(g["tags"].str.contains("T-ML").mean()) for p, g in w.groupby("period")}
out["L1_A4_share_by_period"] = {p: c.rnd(g["Al"].map(lambda v: "A4" in v).mean()) for p, g in w.groupby("period")}

c.save_json(out, "descriptivos.json")
print({k: out[k] for k in ["L1_n", "L1_window_n", "L3_n", "L3_hw_n", "L3_FxA_empty_core", "L3_FxA_simonly_core", "L3_FxA_hw_core", "L1_FxA_empty_core"]})
