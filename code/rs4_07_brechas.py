"""RS4-7. Gaps (RQ5): F x A cells that are empty or supported by simulation only.

Combines the full-text map (L3, primary family; basis of every F x A statement) with the
mapping-set map (L1, all years and 2016-2026; descriptive only because round-2 agreement on
A was below 0.60). Core fault models F1-F7; F0 (unspecified) and F8 (sensor, secondary) are
listed separately.
Status per cell:
  hardware (L3)            at least one L3 study with E3-E4 in the cell
  simulation only (L3)     L3 studies in the cell, none with E3-E4
  abstract only            empty in L3 but present in L1 (not confirmed at full text)
  empty                    empty in L1 and L3
Output: G1_brechas_FxA.csv, brechas.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

d4 = pd.read_csv(c.RES / "D4_FxA_L3.csv")
d5 = pd.read_csv(c.RES / "D5_FxA_L1_descriptivo.csv")
l1a = d5[d5["set"] == "L1 all years"].set_index(["F", "A"])
l1w = d5[d5["set"] == "L1 2016-2026"].set_index(["F", "A"])
L3 = c.load_l3()
rows = []
for _, r in d4.iterrows():
    k = (r["F"], r["A"])
    sub = L3[L3["Fl"].map(lambda v, f=r["F"]: f in v) & (L3["Ap"] == r["A"])]
    if r["n"] > 0 and r["n_hw"] > 0:
        status = "hardware (L3)"
    elif r["n"] > 0:
        status = "simulation only (L3)"
    elif l1a.loc[k, "n"] > 0:
        status = "abstract only (not confirmed at full text)"
    else:
        status = "empty"
    phys = int((sub["hw_phys"] & sub["hwF"].map(lambda v, f=r["F"]: f in v)).sum())
    rows.append(dict(L3_hw_physical_reserve=phys, F=r["F"], A=r["A"], core=r["F"] in ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
                     L3_n=int(r["n"]), L3_hw=int(r["n_hw"]), L3_E4=int(r["n_E4"]), L3_hw_study_level=int(r["n_hw_study"]),
                     L3_hw_no_EAMBIG=int(r["n_hw_no_EAMBIG"]),
                     L3_physical_injection=int(sub["injection"].fillna("").str.lower().str.contains("hardware disconnection|air switch").sum()),
                     L1_n_all=int(l1a.loc[k, "n"]), L1_hw_all=int(l1a.loc[k, "n_hw"]),
                     L1_n_window=int(l1w.loc[k, "n"]), L1_hw_window=int(l1w.loc[k, "n_hw"]),
                     status=status, L3_rids=r["rids"] if isinstance(r["rids"], str) else ""))
G = pd.DataFrame(rows)
c.save_csv(G, "G1_brechas_FxA.csv")
core = G[G["core"]]
out = dict(
    core_status=core["status"].value_counts().to_dict(),
    core_empty=[f"{a}x{b}" for a, b in core.loc[core["status"] == "empty", ["F", "A"]].values],
    core_not_read=[f"{a}x{b}" for a, b in core.loc[core["status"] == "abstract only (not confirmed at full text)", ["F", "A"]].values],
    core_sim_only=[f"{a}x{b}" for a, b in core.loc[core["status"] == "simulation only (L3)", ["F", "A"]].values],
    core_hw_single=[f"{a}x{b}" for a, b in core.loc[(core["status"] == "hardware (L3)") & (core["L3_hw"] == 1), ["F", "A"]].values],
    core_hw_ge3=[f"{a}x{b}" for a, b in core.loc[core["L3_hw"] >= 3, ["F", "A"]].values],
    core_hw_only_EAMBIG=[f"{a}x{b}" for a, b in core.loc[(core["L3_hw"] > 0) & (core["L3_hw_no_EAMBIG"] == 0), ["F", "A"]].values],
    core_hw_no_EAMBIG_n=int((core["L3_hw_no_EAMBIG"] > 0).sum()),
    core_hw_study_level_n=int((core["L3_hw_study_level"] > 0).sum()),
    core_lost_by_pair_rule=[f"{a}x{b}" for a, b in core.loc[(core["L3_hw_study_level"] > 0) & (core["L3_hw"] == 0), ["F", "A"]].values],
    core_physical_injection_cells=[f"{a}x{b}" for a, b in core.loc[core["L3_physical_injection"] > 0, ["F", "A"]].values],
    core_hw_only_virtual=[f"{a}x{b}" for a, b in core.loc[(core["L3_hw"] > 0) & (core["L3_hw_physical_reserve"] == 0), ["F", "A"]].values],
    core_hw_physical_reserve_n=int((core["L3_hw_physical_reserve"] > 0).sum()),
    F3_L1_n=int(G[G["F"] == "F3"]["L1_n_all"].sum()),
    F5_L3_n=int(L3["Fl"].map(lambda v: "F5" in v).sum()),
    A4_L3_cells=[f"{a}x{b}" for a, b in core.loc[(core["A"] == "A4") & (core["L3_n"] > 0), ["F", "A"]].values],
)
c.save_json(out, "brechas.json")
print(G.drop(columns=["L3_rids"]).to_string())
print(out)
