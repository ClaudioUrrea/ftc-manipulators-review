"""RS4-4. Confirmatory tests H1-H3 (protocol v1.8, Section 11) and measurement error of E.

Primary: L1 (abstract-based E bins; H1 and H2 on all years, H3 on 2016-2026), Wald
odds ratios with 95 % CI, Holm adjustment across the three tests. H2 uses the
mapping-set A codes, whose agreement was below 0.60 (round 2: A4 kappa 0.52); it is
reported as pre-specified with that warning, and the full-text check carries the
main weight (decision recorded in the RS4 analysis notes).
Check: L3-R (probability sample of L1 2016-2026), full-text E, design weights N_h/n_h,
percentile CI from a bootstrap stratified by the sampling stratum.
Measurement error: abstract bin vs full-text E in L3-R; sensitivity and specificity
(design-weighted), Rogan-Gladen correction of L1 proportions with bootstrap CI.

Outputs: H1_confirmatorias.csv, E1_matriz_confusion.csv, E2_rogan_gladen.csv, hipotesis.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402
import rs4_hipotesis_lib as hl  # noqa: E402

rng = np.random.default_rng(c.SEED_BOOT)
L1 = c.load_l1()
W = L1[L1["in_window"]]
L3 = c.load_l3()
LR = L3[L3["sample"] == "L3-R"].copy()
out: dict = {}

# ------------------------------------------------------------ confirmatory, L1
rows = []
prim = {}
for h in hl.HYP:
    df = W if h == "H3" else L1
    r = hl.test(df, h, "L1")
    r.update(set="L1 primary", population="L1 2016-2026" if h == "H3" else "L1 all years", outcome="E3-E4")
    prim[h] = r
adj = c.holm({h: prim[h]["p"] for h in hl.HYP})
adj_x = c.holm({h: prim[h]["p_exact"] for h in hl.HYP})  # robustness: Fisher exact p, Holm-adjusted
for h in hl.HYP:
    prim[h]["p_holm"] = adj[h]
    prim[h]["p_exact_holm"] = adj_x[h]
    rows.append(prim[h])
# secondary outcome E4 and window-only version of H1, H2 (reported, not part of the Holm family)
for h in ["H1", "H2"]:
    r = hl.test(W, h, "L1"); r.update(set="L1 2016-2026", population="L1 2016-2026", outcome="E3-E4"); rows.append(r)
for h in hl.HYP:
    df = W if h == "H3" else L1
    r = hl.test(df, h, "L1", outcome="E4"); r.update(set="L1 secondary outcome E4", population="as primary", outcome="E4"); rows.append(r)

# ------------------------------------------------------------ check, L3-R (design-weighted)
for h in hl.HYP:
    r = hl.weighted_or(LR, h)
    lo, hi, nb = hl.boot_weighted_or(LR, h, rng)
    rows.append(dict(hyp=h, set="L3-R check (weighted)", population="L3-R eligible (n = %d)" % len(LR), outcome="E3-E4 (full text)",
                     n_exposed=r["n_exposed"], n_reference=r["n_reference"], a=r["k_exposed"], c=r["k_reference"],
                     p_exposed=c.rnd(r["p_exposed"]), p_reference=c.rnd(r["p_reference"]),
                     OR=c.rnd(r["OR"]), lo=c.rnd(lo), hi=c.rnd(hi), haldane=r["haldane"], boot_valid=nb))
# descriptive, all L3 (non-probability: L3-P is purposive), unweighted
for h in hl.HYP:
    r = hl.test(L3, h, "L3"); r.update(set="L3 all (descriptive, unweighted)", population="L3 (n = %d)" % len(L3), outcome="E3-E4 (full text)")
    r.pop("p"); r.pop("p_exact"); rows.append(r)
H = pd.DataFrame(rows)
c.save_csv(H, "H1_confirmatorias.csv")
out["primary"] = {h: {k: prim[h][k] for k in ["a", "b", "c", "d", "p_exposed", "p_reference", "OR", "lo", "hi", "p", "p_holm", "p_exact", "p_exact_holm", "haldane"]} for h in hl.HYP}
for h in hl.HYP:
    out["primary"][h]["p"] = c.rnd(out["primary"][h]["p"], 4)
    out["primary"][h]["p_holm"] = c.rnd(out["primary"][h]["p_holm"], 4)
    out["primary"][h]["p_exact"] = c.rnd(out["primary"][h]["p_exact"], 4)
    out["primary"][h]["p_exact_holm"] = c.rnd(out["primary"][h]["p_exact_holm"], 4)
out["L3R_check"] = H[H["set"] == "L3-R check (weighted)"].set_index("hyp")[["n_exposed", "a", "n_reference", "c", "p_exposed", "p_reference", "OR", "lo", "hi", "haldane", "boot_valid"]].to_dict("index")
out["L3R_boot_degenerate"] = {h: int(c.N_BOOT - v["boot_valid"]) for h, v in out["L3R_check"].items()}
out["L3_all"] = H[H["set"].str.startswith("L3 all")].set_index("hyp")[["a", "b", "c", "d", "p_exposed", "p_reference", "OR", "lo", "hi", "haldane"]].to_dict("index")
out["L1_window_H1H2"] = H[H["set"] == "L1 2016-2026"].set_index("hyp")[["OR", "lo", "hi", "p_exposed", "p_reference"]].to_dict("index")
out["L1_E4"] = H[H["set"] == "L1 secondary outcome E4"].set_index("hyp")[["OR", "lo", "hi"]].to_dict("index")
out["L3R_eligible_n"] = len(LR)
out["L3R_A4_primary_n"] = int((LR["Ap"] == "A4").sum())
out["L3R_joint_n"] = int(LR["Fl"].map(lambda v: "F4" in v or "F5" in v).sum())

# ------------------------------------------------------------ measurement error of E
LR["abs_hw"] = LR["E_bin_abs"].isin(["E3", "E4"])
conf = pd.crosstab(LR["E_bin_abs"], LR["E_bin_ft"]).reindex(index=c.E_ORDER, columns=c.E_ORDER, fill_value=0)
conf_out = conf.reset_index().rename(columns={"E_bin_abs": "abstract bin \\ full-text bin"})
conf_out["weight_N_over_n"] = [c.rnd(LR[LR["E_bin_abs"] == e]["weight"].iloc[0], 4) if (LR["E_bin_abs"] == e).any() else None for e in c.E_ORDER]
c.save_csv(conf_out, "E1_matriz_confusion.csv")
out["confusion"] = {r: conf.loc[r].to_dict() for r in c.E_ORDER}
out["L3R_excluded_by_stratum"] = c.load_l3(False).query("sample == 'L3-R' and ft_eligible == 'no'")["E_bin_abs"].value_counts().to_dict()


def se_sp(df):
    w = df["weight"]
    t = df["hw"].astype(bool); o = df["abs_hw"].astype(bool)
    se = w[t & o].sum() / w[t].sum() if w[t].sum() > 0 else float("nan")
    sp = w[~t & ~o].sum() / w[~t].sum() if w[~t].sum() > 0 else float("nan")
    prev = w[t].sum() / w.sum()
    return se, sp, prev


se, sp, prev = se_sp(LR)
strata = [g for _, g in LR.groupby("E_bin_abs")]
nW = len(W)
p_obs = float(W["hw"].mean())
groups_for_rg = {"L1 2016-2026": W}
for per, g in W.groupby("period"):
    groups_for_rg[f"L1 {per}"] = g
for h in ["H1", "H2"]:
    ex, ref = hl.groups(W, h, "L1")
    groups_for_rg[f"{h} exposed (2016-2026)"] = W[ex]
    groups_for_rg[f"{h} reference (2016-2026)"] = W[ref]

boot = {"se": [], "sp": [], "prev": []}
boot_rg = {k: [] for k in groups_for_rg}
for _ in range(c.N_BOOT):
    bs = pd.concat([g.sample(len(g), replace=True, random_state=int(rng.integers(1e9))) for g in strata])
    s_, p_, pv = se_sp(bs)
    boot["se"].append(s_); boot["sp"].append(p_); boot["prev"].append(pv)
    for k, g in groups_for_rg.items():
        po = rng.binomial(len(g), g["hw"].mean()) / len(g)
        boot_rg[k].append(c.rogan_gladen(po, s_, p_))
ci = lambda v: [c.rnd(x) for x in np.nanpercentile(v, [2.5, 97.5])]  # noqa: E731
out["E_se"], out["E_se_ci"] = c.rnd(se), ci(boot["se"])
out["E_sp"], out["E_sp_ci"] = c.rnd(sp), ci(boot["sp"])
out["E_prev_design"], out["E_prev_design_ci"] = c.rnd(prev), ci(boot["prev"])
# Influence of the single most-weighted hardware study (stage E8-c, E8-14): the hardware-validated L3-R study with the
# largest weight N_h/n_h (a false negative of the abstract rule in the simulation stratum).
hwLR = LR[LR["hw"]]
top = hwLR.sort_values(["weight", "rid"], ascending=[False, True]).iloc[0]
se_x, sp_x, prev_x = se_sp(LR[LR["rid"] != top["rid"]])
out["E_influential_rid"] = top["rid"]
out["E_influential_weight"] = c.rnd(top["weight"], 2)
out["E_prev_design_without_influential"] = c.rnd(prev_x)
out["E_se_without_influential"] = c.rnd(se_x)
# The design-based estimate refers to full-text eligible studies; Rogan-Gladen refers to all rule-included
# records. The weighted abstract-hardware share among eligible L3-R studies shows how eligibility differs by stratum.
out["abs_hw_share_eligible_weighted"] = c.rnd(float((LR["abs_hw"] * LR["weight"]).sum() / LR["weight"].sum()))
allr = c.load_l3(False).query("sample == 'L3-R' and status == 'done'")
out["L3R_eligible_share_by_stratum"] = {k: [int((g["ft_eligible"] == "yes").sum()), len(g)] for k, g in allr.groupby("E_bin_abs")}
abs_hw = LR[LR["abs_hw"]]
abs_no = LR[~LR["abs_hw"]]
out["E_ppv"] = c.rnd(abs_hw["hw"].mean()); out["E_ppv_k_n"] = [int(abs_hw["hw"].sum()), len(abs_hw)]
out["E_ppv_ci"] = [c.rnd(x) for x in c.wilson(abs_hw["hw"].sum(), len(abs_hw))]
out["E_npv"] = c.rnd(1 - abs_no["hw"].mean()); out["E_npv_k_n"] = [int((~abs_no["hw"]).sum()), len(abs_no)]
out["E_npv_ci"] = [c.rnd(x) for x in c.wilson((~abs_no["hw"]).sum(), len(abs_no))]
rows = []
for k, g in groups_for_rg.items():
    po = float(g["hw"].mean())
    rows.append(dict(group=k, n=len(g), p_raw=c.rnd(po), raw_lo=c.rnd(c.wilson(g["hw"].sum(), len(g))[0]),
                     raw_hi=c.rnd(c.wilson(g["hw"].sum(), len(g))[1]), p_corrected=c.rnd(c.rogan_gladen(po, se, sp)),
                     corr_lo=ci(boot_rg[k])[0], corr_hi=ci(boot_rg[k])[1]))
RG = pd.DataFrame(rows)
c.save_csv(RG, "E2_rogan_gladen.csv")
out["rogan_gladen"] = RG.set_index("group").to_dict("index")


# Corrected odds ratios are not reported: corrected proportions reach the boundary 0
# in small groups (for example the H1 reference group), where the odds ratio is undefined.
c.save_json(out, "hipotesis.json")
print(H[["hyp", "set", "n_exposed", "a", "n_reference", "c", "OR", "lo", "hi", "p_exposed", "p_reference"]].to_string())
print({k: out[k] for k in ["E_se", "E_se_ci", "E_sp", "E_sp_ci", "E_prev_design", "E_ppv", "E_npv", "confusion"]})
print(out["primary"]); print(RG.to_string())
