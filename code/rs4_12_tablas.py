"""RS4-12. Manuscript-ready tables (values only from resultados/ and the coded data).

T1_tabla_modelos_falla.csv  one row per fault model: normal-form expression, evidence, families,
                            structural reserve, fault information, sensing and delay (RQ1-RQ2 summary)
T2_tabla_hipotesis.csv      H1-H3: L1 primary (Wald and Fisher exact, Holm) and L3-R check
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

Q = pd.read_csv(c.RES / "Q1_codigos_por_estudio.csv")
L3 = c.load_l3().merge(Q[["rid", "struct_c", "sens_c", "info_c", "delay_c", "fit_c"]], on="rid")
L1 = c.load_l1()
W = L1[L1["in_window"]]
FORM = {"F1": "0 < lambda_i < 1", "F2": "b_i != 0", "F3": "u_bar_i below nominal after onset", "F4t": "s_i = 1, tau_bar_i fixed",
        "F4q": "dq_i = 0, q_i = q_i(t_f)", "F5": "lambda_i = 0, b_i = 0", "F6": "lambda_i, b_i or s_i time-varying or switching",
        "F7": "motor-to-joint map changes", "F8": "y_i = q_i + delta_i"}
NAME = {"F1": "Loss of effectiveness", "F2": "Additive bias or drift", "F3": "Reduced torque bound", "F4t": "Stuck actuator",
        "F4q": "Locked joint", "F5": "Free-swinging joint", "F6": "Intermittent or time-varying", "F7": "Transmission", "F8": "Sensor (secondary)"}
RESERVE = ["actuation redundancy", "kinematic redundancy", "underactuation exploited or reached", "task relaxation or safe degradation"]
rows = []
for f in FORM:
    if f in ("F4t", "F4q"):
        sub = L3[L3["F4_sub"].fillna("").str.contains(f)]
        l1n = None
    else:
        sub = L3[L3["Fl"].map(lambda v, f=f: f in v)]
        l1n = int(W["Fl"].map(lambda v, f=f: f in v).sum())
    n = len(sub)
    fam = {a: int((sub["Ap"] == a).sum()) for a in c.A_CODES}
    fc = "F4" if f in ("F4t", "F4q") else f
    hwp = sub["hw"] & sub["hwF"].map(lambda v, fc=fc: fc in v)  # hardware evidence for this fault class (stage E8-c)
    rows.append(dict(code=f, fault_model=NAME[f], normal_form=FORM[f], L1_2016_2026=l1n if l1n is not None else "", L3_n=n,
                     L3_hardware=int(hwp.sum()), L3_hardware_study_level=int(sub["hw"].sum()),
                     L3_hardware_no_EAMBIG=int((hwp & ~sub["E_AMBIG"]).sum()), A1=fam["A1"], A2=fam["A2"], A3=fam["A3"], A4=fam["A4"],
                     full_actuation=int(sub["struct_c"].fillna("").str.contains("full actuation").sum()),
                     structural_reserve=int(sub["struct_c"].fillna("").map(lambda v: any(k in v for k in RESERVE)).sum()),
                     fault_info_used=int((sub["info_c"] != "none").sum()), fault_assumed_known=int((sub["info_c"] == "known (assumed)").sum()),
                     sensing_beyond_q_dq=int(sub["sens_c"].fillna("").map(lambda v: any(k not in ("joint position", "joint velocity") for k in v.split(";") if k)).sum()),
                     delay_quantified=int((sub["delay_c"] == "quantified").sum()), normal_form_full=int((sub["fit_c"] == "full").sum())))
T1 = pd.DataFrame(rows)
c.save_csv(T1, "T1_tabla_modelos_falla.csv")

# Decision matrix for designers (stage E8-c): by fault model, the evidence of L3 only (no prospective content).
RES_LABEL = {"modeled redundant inputs": "redundant inputs (modeled)", "kinematic redundancy of the arm": "kinematic redundancy",
             "physical actuation redundancy": "actuation redundancy (physical)", "underactuation of the arm": "underactuated control"}
rows = []
for f in ["F1", "F2", "F4t", "F4q", "F5", "F6", "F7", "F8"]:
    sub = L3[L3["F4_sub"].fillna("").str.contains(f)] if f in ("F4t", "F4q") else L3[L3["Fl"].map(lambda v, f=f: f in v)]
    fc = "F4" if f in ("F4t", "F4q") else f
    hwp = sub["hw"] & sub["hwF"].map(lambda v, fc=fc: fc in v)
    fam = sub["Ap"].value_counts()
    top = fam.index[0] if len(fam) else ""
    hw_by_a = {a: int((hwp & (sub["Ap"] == a)).sum()) for a in c.A_CODES}
    best_hw = max(hw_by_a, key=lambda a: (hw_by_a[a], fam.get(a, 0))) if any(hw_by_a.values()) else ""
    if f in ("F4t", "F4q", "F5"):
        reserve = sub["reserve_type"].fillna("").map(lambda v: RES_LABEL.get(v, "")).value_counts()
        reserve = reserve[reserve.index != ""]
    elif f == "F7":  # transmission faults: reserve coded at full text
        reserve = pd.Series({k: int(sub["struct_c"].fillna("").str.contains(k).sum()) for k in
                             ["full actuation", "actuation redundancy", "kinematic redundancy", "underactuation", "task relaxation or safe degradation"]})
        reserve = reserve[reserve > 0]
    else:  # faults that leave the joint actuated: how many studies keep full actuation
        reserve = pd.Series({"full actuation kept": int(sub["struct_c"].fillna("").str.contains("full actuation").sum())})
    EXTRA = ["joint torque", "motor current", "vision or end-effector pose", "force or cable tension", "link deflection or strain", "inertial"]
    sens = {}
    for v in sub["sens_c"]:
        for k in str(v).split(";"):
            if k in EXTRA:
                sens[k] = sens.get(k, 0) + 1
    rows.append(dict(code=f, n=len(sub), full_actuation=int(sub["struct_c"].fillna("").str.contains("full actuation").sum()),
                     reserve="; ".join(f"{k} {v}" for k, v in reserve.items()), info_none=int((sub["info_c"] == "none").sum()),
                     info_known=int((sub["info_c"] == "known (assumed)").sum()),
                     info_obtained=int(sub["info_c"].isin(["estimation", "detection", "detection and estimation", "isolation"]).sum()),
                     sensing_beyond_q_dq=int(sub["sens_c"].fillna("").map(lambda v: any(k not in ("joint position", "joint velocity") for k in v.split(";") if k)).sum()),
                     sensing_extra=int(sub["sens_c"].fillna("").map(lambda v: any(k in EXTRA for k in v.split(";"))).sum()),
                     sensing_types="; ".join(f"{k} {v}" for k, v in sorted(sens.items(), key=lambda kv: -kv[1])),
                     top_family=top, top_family_n=int(fam.get(top, 0)), hw_family=best_hw, hw_family_n=hw_by_a.get(best_hw, 0),
                     hw_pairs=int(hwp.sum()), hw_pairs_no_EAMBIG=int((hwp & ~sub["E_AMBIG"]).sum()),
                     hw_rids=";".join(sub.loc[hwp, "rid"])))
c.save_csv(pd.DataFrame(rows), "T3_matriz_decision.csv")

h = json.loads((c.RES / "hipotesis.json").read_text(encoding="utf-8"))
rows = []
for k in ["H1", "H2", "H3"]:
    p = h["primary"][k]; r = h["L3R_check"][k]
    rows.append(dict(hypothesis=k, exposed_hw=f"{p['a']}/{p['a'] + p['b']}", reference_hw=f"{p['c']}/{p['c'] + p['d']}",
                     OR=p["OR"], CI=f"{p['lo']:.2f}-{p['hi']:.2f}", p_wald=p["p"], p_holm=p["p_holm"], p_exact=p["p_exact"],
                     p_exact_holm=p["p_exact_holm"],
                     L3R_OR=r["OR"] if r["OR"] == r["OR"] else "not estimable",
                     L3R_CI=f"{r['lo']:.2f}-{r['hi']:.2f}" if r["lo"] == r["lo"] else "",
                     L3R_exposed_hw=f"{r['a']}/{r['n_exposed']}"))
c.save_csv(pd.DataFrame(rows), "T2_tabla_hipotesis.csv")
print(T1.to_string()); print(pd.DataFrame(rows).to_string())
