"""RS4-2. Fault-model library (RQ1) and structural-condition and sensing table (RQ2).

The free-text fields of the L3 extraction sheet are mapped to categories with the
fixed keyword rules below (written from the S5 data dictionary, not tuned to results).
Per-study codes are saved for audit (Q1_codigos_por_estudio.csv).

Outputs (resultados/):
  Q1_biblioteca_modelos_falla.csv   one row per study and fault code: equation as written, fit to the FAME normal form
  Q1_ajuste_forma_normal.csv        fit (full, partial, none) by fault code
  Q1_codigos_por_estudio.csv        categories assigned to every L3 study (audit trail)
  Q2_condiciones_sensado.csv        by fault code and primary family: structural conditions, sensing, fault information, delay
  Q2_resumen_por_familia.csv        the same by primary family only
  rq1_rq2.json                      headline numbers
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

L3 = c.load_l3()
out: dict = {}

# --------------------------------------------------------------- rules
STRUCT = {
    "full actuation retained": r"full actuation",
    "actuation redundancy": r"actuation redundancy|redundant actuation|two actuators|two inputs|three actuators|cables? for|8-cable|redundancy condition",
    "kinematic redundancy": r"kinematic|hyper-redundan|extra dof",
    "underactuation exploited or reached": r"underactuat|under-constrained|underconstrained",
    "task relaxation or safe degradation": r"task limited|unreachable|task abandoned|safe degradation|speed reduction|workspace shrinks|nonzero path rate|safe point",
    "sensor redundancy or correction": r"sensor redundancy|measurement correction",
}
SENS = {
    "joint position": r"\benc\b|joint position|joint angles|full state|joint state|absolute encoders|hub angle",
    "joint velocity": r"\bvel\b|velocit|full state|joint state",
    "joint torque": r"\btau\b",
    "motor current": r"current",
    "vision or end-effector pose": r"\bvis\b|camera|end-effector|eef",
    "force or cable tension": r"force|tension",
    "link deflection or strain": r"deflection|strain",
    "inertial": r"\bimu\b",
    "output only": r"output measurement",
    "other (not specified)": r"^other$",
}


INFO_DICT = ("none", "detection", "isolation", "estimation", "known", "full knowledge")


def info_cat(v: str) -> str:
    """Category of the fault information (stage E8-c3). The S5 dictionary category leads the field; the qualifier in
    parentheses is ignored, so a passive study whose qualifier mentions a known bound stays "none" and a qualifier
    such as "no FDI unit" does not cancel an estimation (the keyword rules used before E8-c3 read the qualifiers and
    misclassified R00878 and R00475; "unknown" also matched "known"). Wording outside the dictionary, which occurs
    only in the codes kept from E8-r (15/A_codigos_E8r.csv), falls back to whole-word keyword rules."""
    t = (v or "").lower()
    while re.search(r"\([^()]*\)", t):
        t = re.sub(r"\([^()]*\)", "", t)
    toks = [x.strip() for x in t.split(";") if x.strip()]
    cats = set()
    for x in toks:
        k = next((c for c in INFO_DICT if x == c or x.startswith(c + " ")), None)
        if k is None:
            cats = None
            break
        cats.add("known" if k == "full knowledge" else k)
    if cats:
        if "known" in cats:
            return "known (assumed)"
        if cats == {"none"}:
            return "none"
        if "isolation" in cats:
            return "isolation"
        if {"detection", "estimation"} <= cats:
            return "detection and estimation"
        return "estimation" if "estimation" in cats else "detection"
    w = (v or "").lower()
    if re.search(r"\bknown\b|full knowledge|\bgiven\b", w):
        return "known (assumed)"
    if w.startswith("none") or "no fdi" in w:
        return "none"
    if "isolation" in w:
        return "isolation"
    if "detection" in w and "estimat" in w:
        return "detection and estimation"
    if re.search(r"estimat|smo|rls", w):
        return "estimation"
    if "detection" in w:
        return "detection"
    return "unclear"


def delay_cat(v: str) -> str:
    v = (v or "").strip()
    lv = v.lower()
    if lv.startswith("not applicable"):
        return "not applicable"
    if lv.startswith(("nr", "not quantified", "not reported", "not modeled", "compute-budget")):
        return "not reported"
    if re.search(r"\d+(\.\d+)?\s*(ms|s)\b", lv):
        return "quantified"
    if "threshold" in lv:
        return "not reported"
    return "not reported"


def fit_cat(v) -> str:
    v = str(v or "").strip().lower()
    if v.startswith(("full", "yes", "joint-level constraint", "f5:", "f4")):
        return "full"
    if v.startswith("sensor fault"):
        return "sensor-side form (F8)"
    if v.startswith("not applicable"):
        return "not applicable"
    if v in ("nr", ""):
        return "not reported"
    if v.startswith("partial"):
        return "partial"
    if v.startswith("none"):
        return "none"
    return "unclassified"


def tags(text: str, rules: dict) -> list[str]:
    t = (text or "").lower()
    return [k for k, rx in rules.items() if re.search(rx, t)]


L3["struct_c"] = L3["structural_condition"].fillna("").map(lambda s: tags(s, STRUCT))
L3["sens_c"] = L3["sensing"].fillna("").map(lambda s: tags(s, SENS))
L3["info_c"] = L3["fault_info"].fillna("").map(info_cat)
L3["delay_c"] = L3["detection_delay"].fillna("").map(delay_cat)
L3["fit_c"] = L3["normal_form_fit"].map(fit_cat)
L3["beyond_qqd"] = L3["sens_c"].map(lambda v: any(k not in ("joint position", "joint velocity") for k in v))
# signals added to the encoders (stage E8-c): "output only" and "other (not specified)" are not additional sensing
EXTRA = ["joint torque", "motor current", "vision or end-effector pose", "force or cable tension", "link deflection or strain", "inertial"]
L3["extra_sens"] = L3["sens_c"].map(lambda v: any(k in v for k in EXTRA))
audit = L3[["rid", "sample", "F_ft", "F4_sub", "A_primary", "M_ft", "E_ft", "structural_condition", "struct_c", "sensing", "sens_c",
            "fault_info", "info_c", "detection_delay", "delay_c", "normal_form_fit", "fit_c"]].copy()
for col in ["struct_c", "sens_c"]:
    audit[col] = audit[col].map(lambda v: ";".join(v))
c.save_csv(audit, "Q1_codigos_por_estudio.csv")
out["struct_uncoded"] = list(L3.loc[L3["struct_c"].map(len) == 0, "rid"])
out["sens_uncoded"] = list(L3.loc[L3["sens_c"].map(len) == 0, "rid"])
out["info_unclear"] = list(L3.loc[L3["info_c"] == "unclear", "rid"])

# --------------------------------------------------------------- RQ1 library
rows = []
for _, r in L3.iterrows():
    for f in r["Fl"]:
        rows.append(dict(F=f, F4_sub=r["F4_sub"] if f == "F4" else "", rid=r["rid"], sample=r["sample"], first_author=r["first_author"],
                         year=r["year"], M=r["M_ft"], A_primary=r["Ap"], E=r["E_ft"], fault_equation=r["fault_equation"],
                         normal_form_fit=r["normal_form_fit"], fit=r["fit_c"], magnitude=r["fault_magnitude"], profile=r["profile"],
                         n_simultaneous=r["n_simultaneous"]))
LIB = pd.DataFrame(rows).sort_values(["F", "year", "rid"])
c.save_csv(LIB, "Q1_biblioteca_modelos_falla.csv")
fit = (pd.crosstab(LIB["F"], LIB["fit"]).reindex(columns=["full", "partial", "none", "sensor-side form (F8)", "not applicable", "not reported", "unclassified"], fill_value=0))
fit["n"] = fit.sum(axis=1)
fit = fit.reset_index()
c.save_csv(fit, "Q1_ajuste_forma_normal.csv")
out["fit_studies"] = L3["fit_c"].value_counts().to_dict()
out["fit_full_share"] = c.rnd((L3["fit_c"] == "full").mean())
out["fit_none_rids"] = list(L3.loc[L3["fit_c"] == "none", "rid"])
out["fit_partial_rids"] = list(L3.loc[L3["fit_c"] == "partial", "rid"])
out["R1_equation_share"] = c.rnd(L3["R1"].mean())
out["F4_sub"] = L3["F4_sub"].value_counts().to_dict()
out["n_simultaneous_gt1"] = int(L3["n_simultaneous"].fillna("").str.contains(r"[2-9]|then|and").sum())

# --------------------------------------------------------------- RQ2 table
def summarize(df, f=None):
    n = len(df)
    fc = None if f is None else ("F4" if f in ("F4t", "F4q") else f)
    hwp = df["hw"] if fc is None else df["hw"] & df["hwF"].map(lambda v: fc in v)
    rec = dict(n=n, n_hw=int(hwp.sum()), n_hw_study=int(df["hw"].sum()))
    for k in STRUCT:
        rec[f"struct: {k}"] = int(df["struct_c"].map(lambda v, k=k: k in v).sum())
    for k in SENS:
        rec[f"sensing: {k}"] = int(df["sens_c"].map(lambda v, k=k: k in v).sum())
    rec["sensing beyond joint position and velocity"] = int(df["beyond_qqd"].sum())
    for k in ["none", "estimation", "detection", "detection and estimation", "isolation", "known (assumed)"]:
        rec[f"fault info: {k}"] = int((df["info_c"] == k).sum())
    for k in ["quantified", "not reported", "not applicable"]:
        rec[f"delay: {k}"] = int((df["delay_c"] == k).sum())
    rec["rids"] = ";".join(df["rid"])
    return rec


rows = []
for f in ["F1", "F2", "F4t", "F4q", "F5", "F6", "F7", "F8", "F0"]:
    if f in ("F4t", "F4q"):
        dff = L3[L3["F4_sub"].fillna("").str.contains(f)]
    else:
        dff = L3[L3["Fl"].map(lambda v, f=f: f in v)]
    for a in c.A_CODES + ["all"]:
        sub = dff if a == "all" else dff[dff["Ap"] == a]
        if len(sub) == 0:
            continue
        rows.append(dict(F=f, A_primary=a, **summarize(sub, f)))
Q2 = pd.DataFrame(rows)
c.save_csv(Q2, "Q2_condiciones_sensado.csv")
rows = [dict(A_primary=a, **summarize(L3[L3["Ap"] == a])) for a in c.A_CODES] + [dict(A_primary="all", **summarize(L3))]
Q2b = pd.DataFrame(rows)
c.save_csv(Q2b, "Q2_resumen_por_familia.csv")

# headline numbers
out["sens_only_qqd_share"] = c.rnd(1 - L3["beyond_qqd"].mean())
out["sens_beyond_n"] = int(L3["beyond_qqd"].sum())
out["sens_torque_n"] = int(L3["sens_c"].map(lambda v: "joint torque" in v).sum())
out["sens_current_n"] = int(L3["sens_c"].map(lambda v: "motor current" in v).sum())
out["sens_vision_n"] = int(L3["sens_c"].map(lambda v: "vision or end-effector pose" in v).sum())
out["info"] = L3["info_c"].value_counts().to_dict()
out["info_by_A"] = {a: L3[L3["Ap"] == a]["info_c"].value_counts().to_dict() for a in c.A_CODES}
out["delay"] = L3["delay_c"].value_counts().to_dict()
needs_info = L3[~L3["info_c"].isin(["none"])]
out["needs_info_n"] = len(needs_info)
out["needs_info_delay_quantified"] = int((needs_info["delay_c"] == "quantified").sum())
out["struct"] = {k: int(L3["struct_c"].map(lambda v, k=k: k in v).sum()) for k in STRUCT}
f4q = L3[L3["F4_sub"].fillna("").str.contains("F4q")]
f45 = L3[L3["Fl"].map(lambda v: "F4" in v or "F5" in v)]
out["F4q_n"] = len(f4q)
out["F4q_A"] = f4q["Ap"].value_counts().to_dict()
out["F4q_kinematic_or_task"] = int(f4q["struct_c"].map(lambda v: "kinematic redundancy" in v or "task relaxation or safe degradation" in v).sum())
out["F45_n"] = len(f45)
out["F45_A"] = f45["Ap"].value_counts().to_dict()
out["F45_structural_reserve"] = int(f45["struct_c"].map(lambda v: any(k in v for k in ["actuation redundancy", "kinematic redundancy", "underactuation exploited or reached", "task relaxation or safe degradation"])).sum())
f1 = L3[L3["Fl"].map(lambda v: "F1" in v)]
out["F1_full_actuation_share"] = c.rnd(f1["struct_c"].map(lambda v: "full actuation retained" in v).mean())
out["F5_rids"] = list(L3.loc[L3["Fl"].map(lambda v: "F5" in v), "rid"])
# --------------------------------------------------------------- sensing by family (stage E8-c, E8-10)
# Physical sensors are those used on a hardware run (E3-E4); in simulation (E0-E2) a "measurement" is a state
# assumed available to the controller. A study counts once per sensor type it uses.
rows = []
for k in SENS:
    rec = dict(sensor=k)
    for grp, sub in [("hardware (E3-E4)", L3[L3["hw"]]), ("simulation or analysis (E0-E2)", L3[~L3["hw"]])]:
        for a in c.A_CODES:
            rec[f"{grp} {a}"] = int(sub[sub["Ap"] == a]["sens_c"].map(lambda v, k=k: k in v).sum())
        rec[f"{grp} total"] = int(sub["sens_c"].map(lambda v, k=k: k in v).sum())
        rec[f"{grp} rids"] = ";".join(sub.loc[sub["sens_c"].map(lambda v, k=k: k in v), "rid"])
    rows.append(rec)
QS = pd.DataFrame(rows)
c.save_csv(QS, "Q3_sensado_por_familia.csv")
out["sens_by_group_n"] = {"hardware": int(L3["hw"].sum()), "simulation": int((~L3["hw"]).sum())}
out["sens_hw_beyond_n"] = int((L3["hw"] & L3["beyond_qqd"]).sum())
out["sens_extra_n"] = int(L3["extra_sens"].sum())
out["sens_extra_hw_n"] = int((L3["hw"] & L3["extra_sens"]).sum())
out["sens_extra_sim_n"] = int((~L3["hw"] & L3["extra_sens"]).sum())
out["sens_only_qqd_n"] = int((~L3["beyond_qqd"]).sum())
out["sens_output_or_unspecified_n"] = int((L3["beyond_qqd"] & ~L3["extra_sens"]).sum())
out["sens_sim_beyond_n"] = int((~L3["hw"] & L3["beyond_qqd"]).sum())
out["sens_counts"] = {k: int(L3["sens_c"].map(lambda v, k=k: k in v).sum()) for k in SENS}
out["sens_counts_hw"] = {k: int(L3[L3["hw"]]["sens_c"].map(lambda v, k=k: k in v).sum()) for k in SENS}
for a in c.A_CODES:
    sub = L3[L3["Ap"] == a]
    out[f"sens_beyond_{a}"] = [int(sub["beyond_qqd"].sum()), len(sub)]

# --------------------------------------------------------------- quantified delays (stage E8-c, E8-10)
dq = L3[L3["delay_c"] == "quantified"][["rid", "F_ft", "A_primary", "E_ft", "mechanism", "fault_info", "detection_delay", "own"]].copy()
c.save_csv(dq, "Q4_retardos_cuantificados.csv")
out["delay_quantified_rids"] = list(dq["rid"])
# numbers printed in the delay field (values and units in Q4_retardos_cuantificados.csv), for the text check
out["delay_values"] = {r: [float(x) for x in re.findall(r"\d+(?:\.\d+)?", v)] for r, v in zip(dq["rid"], dq["detection_delay"])}
out["delay_hw_n"] = int(L3[(L3["delay_c"] == "quantified") & L3["hw"]].shape[0])
# structural reserve of the joint-level studies (F4, F5) by type, and of the stuck-actuator studies (stage E8-c, E8-03)
j = L3[L3["Fl"].map(lambda v: "F4" in v or "F5" in v)]
out["joint_reserve_type"] = j["reserve_type"].fillna("").value_counts().to_dict()
f4t = L3[L3["F4_sub"].fillna("").str.contains("F4t")]
out["F4t_reserve_type"] = f4t["reserve_type"].fillna("").value_counts().to_dict()
out["F4t_GEN_n"] = int(f4t["GEN"].sum())
out["F4t_physical_reserve_n"] = int((f4t["reserve_type"] != "modeled redundant inputs").sum())
out["joint_GEN_n"] = int(j["GEN"].sum())
out["A4_GEN_n"] = int(L3[(L3["Ap"] == "A4") & L3["GEN"]].shape[0])
out["GEN_n"] = int(L3["GEN"].sum()); out["NET_n"] = int(L3["NET"].sum())
out["F7_sub"] = L3["F7_sub"].fillna("").value_counts().to_dict()
out["info_known_F4q"] = [int((L3[L3["F4_sub"].fillna("").str.contains("F4q")]["info_c"] == "known (assumed)").sum()), out["F4q_n"]]
f5 = L3[L3["Fl"].map(lambda v: "F5" in v)]
out["info_known_F5"] = [int((f5["info_c"] == "known (assumed)").sum()), len(f5)]
out["info_known_F4t"] = [int((f4t["info_c"] == "known (assumed)").sum()), len(f4t)]
out["F4t_passive_n"] = int((f4t["Ap"] == "A1").sum())
# stage E8-c3 (E8r2-01): a passive law (A1) may use fault information given a priori (fault_info known); the counts of
# passive laws "that need no fault information" exclude those studies
out["A1_info"] = L3[L3["Ap"] == "A1"]["info_c"].value_counts().to_dict()
out["A1_known_rids"] = list(L3.loc[(L3["Ap"] == "A1") & (L3["info_c"] == "known (assumed)"), "rid"])
f1a1 = L3[L3["Fl"].map(lambda v: "F1" in v) & (L3["Ap"] == "A1")]
out["F1_A1_n"] = len(f1a1)
out["F1_A1_noinfo_n"] = int((f1a1["info_c"] == "none").sum())
out["F1_A1_known_n"] = int((f1a1["info_c"] == "known (assumed)").sum())
f4ta1 = f4t[f4t["Ap"] == "A1"]
out["F4t_passive_noinfo_n"] = int((f4ta1["info_c"] == "none").sum())
out["F4t_passive_known_n"] = int((f4ta1["info_c"] == "known (assumed)").sum())
# the same counts with the A and fault_info codes of E8-r, before the literal A1/A2 reading (15/A_codigos_E8r.csv)
_e8r = pd.read_csv(c._one("15 ·*") / "A_codigos_E8r.csv", dtype=str).set_index("rid")
_old_a = L3["rid"].map(_e8r["A_primary"])
_old_i = L3["rid"].map(_e8r["fault_info"]).fillna("").map(info_cat)
_f4t_old = L3["F4_sub"].fillna("").str.contains("F4t") & _old_a.eq("A1")
out["F4t_passive_earlier_n"] = int(_f4t_old.sum())
out["F4t_passive_earlier_noinfo_n"] = int((_f4t_old & _old_i.eq("none")).sum())
_f1_old = L3["Fl"].map(lambda v: "F1" in v) & _old_a.eq("A1")
out["F1_A1_earlier_n"] = int(_f1_old.sum())
out["needs_info_earlier_n"] = int((_old_i != "none").sum())
out["needs_info_earlier_delay_quantified"] = int(((_old_i != "none") & (L3["delay_c"] == "quantified")).sum())
out["info_earlier_unclear"] = list(L3.loc[_old_i == "unclear", "rid"])
# hardware runs: reserve exercised on the robot and kind of result (fields added in E8-c3)
hwd = L3[L3["hw"]]
out["hw_reserve"] = hwd["hw_reserve_c"].value_counts().to_dict()
out["hw_result"] = hwd["hw_result_c"].value_counts().to_dict()
out["hw_reserve_A3"] = hwd[hwd["Ap"] == "A3"]["hw_reserve_c"].value_counts().to_dict()
out["hw_virtual_rids"] = list(hwd.loc[hwd["hw_reserve_c"] == "virtual channels", "rid"])
out["hw_quantitative_n"] = int((hwd["hw_result_c"] == "quantitative").sum())
out["hw_uncoded"] = list(hwd.loc[(hwd["hw_reserve_c"] == "") | (hwd["hw_result_c"] == ""), "rid"])
c.save_json(out, "rq1_rq2.json")
print({k: out[k] for k in ["struct_uncoded", "sens_uncoded", "info_unclear", "fit_studies", "info", "delay", "struct", "F4q_n", "F4q_A", "F45_structural_reserve", "F45_n"]})
