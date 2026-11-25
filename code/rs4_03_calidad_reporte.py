"""RS4-3. Reporting quality: FAME checklist R1-R10 per study and per item (RQ4).

Outputs (resultados/):
  R1_checklist_por_estudio.csv   R1-R10 and score per L3 study (Supplementary Table S5 subset)
  R2_checklist_por_item.csv      share per item: all L3, L3-R design-weighted, simulation vs hardware
  R3_disponibilidad_efectos.csv  availability of the three metric values needed for D0, D1 and RF
  reporte.json                   headline numbers
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

L3 = c.load_l3()
R = [f"R{i}" for i in range(1, 11)]
LABEL = {"R1": "Fault equation", "R2": "Fault magnitude", "R3": "Onset and time profile", "R4": "Injection mechanism",
         "R5": "Fault-free and faulty baselines", "R6": "Quantitative metric", "R7": "Actuator limits",
         "R8": "Noise or disturbances", "R9": "Repetitions or statistics", "R10": "Code or data available"}
out: dict = {}

c.save_csv(L3[["rid", "sample", "first_author", "year", "E_ft", "A_primary", "F_ft"] + R + ["R_score"]], "R1_checklist_por_estudio.csv")

LR = L3[L3["sample"] == "L3-R"]
rng = np.random.default_rng(c.SEED_BOOT)


def wmean(df, col):
    return float((df[col] * df["weight"]).sum() / df["weight"].sum())


def boot_wmean(df, col):
    vals = []
    groups = [g for _, g in df.groupby("E_bin_abs")]
    for _ in range(c.N_BOOT):
        bs = pd.concat([g.sample(len(g), replace=True, random_state=int(rng.integers(1e9))) for g in groups])
        vals.append(wmean(bs, col))
    return np.percentile(vals, [2.5, 97.5])


rows = []
sim, hw = L3[~L3["hw"]], L3[L3["hw"]]
for k in R:
    n = len(L3)
    s = int(L3[k].sum())
    lo, hi = c.wilson(s, n)
    wlo, whi = boot_wmean(LR, k)
    rows.append(dict(item=k, label=LABEL[k], n=n, k=s, share=c.rnd(s / n), lo=c.rnd(lo), hi=c.rnd(hi),
                     share_L3R_weighted=c.rnd(wmean(LR, k)), L3R_lo=c.rnd(wlo), L3R_hi=c.rnd(whi),
                     share_simulation=c.rnd(sim[k].mean()), share_hardware=c.rnd(hw[k].mean()),
                     share_2016_2020=c.rnd(L3[L3["period"] == "2016-2020"][k].mean()),
                     share_2021_2026=c.rnd(L3[L3["period"] == "2021-2026"][k].mean())))
IT = pd.DataFrame(rows)
c.save_csv(IT, "R2_checklist_por_item.csv")
out["items"] = {r["item"]: r["share"] for r in rows}
out["items_L3R_weighted"] = {r["item"]: r["share_L3R_weighted"] for r in rows}
out["n_sim"], out["n_hw"] = len(sim), len(hw)
out["score_median"] = float(L3["R_score"].median())
out["score_iqr"] = [float(L3["R_score"].quantile(0.25)), float(L3["R_score"].quantile(0.75))]
out["score_range"] = [int(L3["R_score"].min()), int(L3["R_score"].max())]
out["score_median_sim"] = float(sim["R_score"].median())
out["score_median_hw"] = float(hw["R_score"].median())
out["score_weighted_mean_L3R"] = c.rnd(wmean(LR, "R_score"), 2)
out["score_ge8_n"] = int((L3["R_score"] >= 8).sum())
out["R9_n"] = int(L3["R9"].sum())
out["R10_n"] = int(L3["R10"].sum())
out["R4_hw_share"] = c.rnd(hw["R4"].mean())
# fault injection on hardware: how the fault was produced in E3-E4 studies
inj = hw["injection"].fillna("").str.lower()
# stage E8-c2 (E8r-07): a fault imposed in a hardware-in-the-loop loop or designated in the planner is a software
# injection; "not described" only when the hardware run states no mechanism
PHYS = r"hardware disconnection|air switch|electromagnet"
NOTD = r"mechanism not (?:described|stated|specified)|not described"
SOFT = r"software|command|scal|switched off|velocity set|hil loop|in the planner|designat|artificial"
inj_cat = np.select([inj.str.contains(PHYS), inj.str.contains(NOTD), inj.str.contains(SOFT)],
                    ["physical (disconnection, damage, locking hardware)", "simulated only or not described", "software command modification"],
                    default="simulated only or not described")
out["hw_injection"] = pd.Series(inj_cat).value_counts().to_dict()
out["hw_injection_by_rid"] = {k: str(v) for k, v in zip(hw["rid"], inj_cat)}
out["hw_injection_rids_physical"] = list(hw["rid"][inj_cat == "physical (disconnection, damage, locking hardware)"])

# availability of metric triplets for dimensionless effect ratios (S5 dictionary)
def has_num(v):
    v = str(v or "").strip()
    if v == "" or v.lower() in ("nan",) or v.lower().startswith(("nr", "not applicable", "0 by construction")):
        return False
    return bool(re.search(r"\d", v))


eff = L3[["rid", "metric", "m_nominal", "m_fault_noFTC", "m_fault_FTC"]].copy()
eff["nominal"] = eff["m_nominal"].map(has_num)
eff["fault_noFTC"] = eff["m_fault_noFTC"].map(has_num)
eff["fault_FTC"] = eff["m_fault_FTC"].map(has_num)
eff["RF_computable"] = eff["nominal"] & eff["fault_noFTC"] & eff["fault_FTC"]
eff["D1_computable"] = eff["nominal"] & eff["fault_FTC"]
c.save_csv(eff, "R3_disponibilidad_efectos.csv")
out["eff_fault_FTC_numeric_n"] = int(eff["fault_FTC"].sum())
out["eff_nominal_numeric_n"] = int(eff["nominal"].sum())
out["eff_noFTC_numeric_n"] = int(eff["fault_noFTC"].sum())
out["eff_RF_computable_n"] = int(eff["RF_computable"].sum())
out["eff_RF_computable_rids"] = list(eff.loc[eff["RF_computable"], "rid"])
out["eff_D1_computable_n"] = int(eff["D1_computable"].sum())
out["eff_figures_only_n"] = int(L3["metric"].fillna("").str.contains("figures? only|figures\\)|none printed|plots? only", regex=True).sum())
# version of the full text read when the publisher's version was not accessible (stage E8-c; from the extraction notes)
nt = L3["notes"].fillna("").str.lower()
ver = np.select([nt.str.contains(r"read from[^;]*accepted (?:manuscript|version)"), nt.str.contains(r"read from[^;]*(?:preprint|submitted version)"), nt.str.contains(r"author copy on")],
                ["accepted manuscript", "preprint (submitted version)", "author copy"], default="publisher version")
out["fulltext_version"] = pd.Series(ver).value_counts().to_dict()
out["fulltext_version_rids"] = {k: list(L3["rid"][ver == k]) for k in ["accepted manuscript", "preprint (submitted version)", "author copy"]}
c.save_json(out, "reporte.json")
print(out)
