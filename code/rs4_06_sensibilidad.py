"""RS4-6. Sensitivity analyses (protocol v1.8, Section 11, and RS3 decisions of 16-11-2026 and 24-11-2026).

L1 (H1-H3 and hardware share): WoS only, Scopus only, union; without conference papers;
with UNCERTAIN added (the primary set already excludes them) and without NO-ABS; without
OWN; 2016-2026 only; without the A-NR stratum (post hoc, after round 2 of the blind coding);
tipping point for the records lost by the string (SF08sup estimate: 23, 11-42).
L3 (full-text synthesis): without the Markov-jump line; one study per author group;
E_AMBIG studies moved down (hardware claim not counted) and up (to E4); A codes as extracted before the
literal A1/A2 reading (stage E8-c2b); without OWN.
Outputs: S1_sensibilidad_L1.csv, S2_punto_de_quiebre.csv, S3_sensibilidad_L3.csv, sensibilidad.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402
import rs4_hipotesis_lib as hl  # noqa: E402

out: dict = {}
L1 = c.load_l1()
L1u = c.load_l1(include_uncertain=True)

variants = {
    "Primary (union, INCLUDE)": L1,
    "WoS only": L1[L1["in_wos"]],
    "Scopus only": L1[L1["in_scopus"]],
    "Without conference papers": L1[~L1["conf"]],
    "Without NO-ABS": L1[~L1["noabs"]],
    "With UNCERTAIN added": L1u,
    "Without OWN": L1[~L1["own"]],
    "2016-2026 only": L1[L1["in_window"]],
    "Without A-NR stratum (post hoc)": L1[~L1["anr"]],
}
rows = []
for name, df in variants.items():
    w = df[df["in_window"]]
    res = {}
    for h in hl.HYP:
        r = hl.test(w if h == "H3" else df, h, "L1")
        res[h] = r
    adj = c.holm({h: res[h]["p"] for h in hl.HYP})
    for h in hl.HYP:
        r = res[h]
        rows.append(dict(variant=name, n=len(df), n_window=len(w), hw_share_window=c.rnd(w["hw"].mean()), hyp=h,
                         n_exposed=r["n_exposed"], n_reference=r["n_reference"], OR=r["OR"], lo=r["lo"], hi=r["hi"],
                         p=c.rnd(r["p"], 4), p_holm=c.rnd(adj[h], 4), haldane=r["haldane"]))
S1 = pd.DataFrame(rows)
c.save_csv(S1, "S1_sensibilidad_L1.csv")
out["L1_variants"] = {v: {h: dict(OR=g.set_index("hyp").loc[h, "OR"], lo=g.set_index("hyp").loc[h, "lo"], hi=g.set_index("hyp").loc[h, "hi"],
                                  p_holm=g.set_index("hyp").loc[h, "p_holm"]) for h in hl.HYP} | {"n": int(g["n"].iloc[0]), "hw_share_window": g["hw_share_window"].iloc[0]}
                      for v, g in S1.groupby("variant", sort=False)}
out["L1_any_holm_significant"] = bool((S1["p_holm"] < 0.05).any())
out["L1_holm_significant_rows"] = S1.loc[S1["p_holm"] < 0.05, ["variant", "hyp", "OR", "lo", "hi", "p_holm"]].to_dict("records")

# ---------------------------------------------------------- tipping point (string loss)
base = {h: hl.table(L1[L1["in_window"]] if h == "H3" else L1, h, "L1") for h in hl.HYP}
pbase = {h: c.odds_ratio(*base[h])["p"] for h in hl.HYP}
# cell added: the one that moves the estimate in the direction of each hypothesis
# (H1 exposed with hardware; H2 exposed without hardware; H3 late period with hardware,
# which would contradict H3 by making an increase significant).
cell = {"H1": 0, "H2": 1, "H3": 0}
rows = []
for h in hl.HYP:
    k_flip = None
    for k in range(0, 501):
        t = list(base[h]); t[cell[h]] += k
        r = c.odds_ratio(*t)
        ps = dict(pbase); ps[h] = r["p"]
        if c.holm(ps)[h] < 0.05:
            k_flip = k
            break
    rows.append(dict(hyp=h, added_cell={0: "exposed, hardware", 1: "exposed, no hardware"}[cell[h]], k_to_holm_significance=k_flip,
                     string_loss_estimate=23, string_loss_ci="11-42"))
S2 = pd.DataFrame(rows)
# expected number of such records among the ~23 lost by the string, at the rates observed in L1
for i, h in enumerate(hl.HYP):
    df = L1[L1["in_window"]] if h == "H3" else L1
    ex, _ = hl.groups(df, h, "L1")
    y = df["hw"].astype(bool)
    m = (ex & y) if cell[h] == 0 else (ex & ~y)
    S2.loc[i, "expected_among_23"] = c.rnd(23 * m.sum() / len(df), 2)
c.save_csv(S2, "S2_punto_de_quiebre.csv")
out["tipping"] = {r["hyp"]: r["k_to_holm_significance"] for r in rows}
out["tipping_expected_among_23"] = dict(zip(S2["hyp"], S2["expected_among_23"]))

# ---------------------------------------------------------- L3 variants
L3 = c.load_l3()


def one_per_group(df):
    drop = []
    for g, rids in c.GROUPS.items():
        mem = df[df["rid"].isin(rids)].copy()
        if len(mem) <= 1:
            continue
        mem["is_R"] = mem["sample"].eq("L3-R")
        mem = mem.sort_values(["is_R", "E_lev", "rid"], ascending=[False, False, True])
        drop += list(mem["rid"].iloc[1:])
    return df[~df["rid"].isin(drop)].copy(), drop


def e_down(df):
    d = df.copy()
    m = d["E_AMBIG"] & d["E_lev"].ge(3)
    d.loc[m, "E_lev"] = 1
    d["hw"] = d["E_lev"].ge(3)
    d.loc[m, "hwF"] = d.loc[m, "hwF"].map(lambda v: [])
    return c.set_hw_H1(d), list(df.loc[m, "rid"])


def e_up(df):
    d = df.copy()
    m = d["E_AMBIG"] & d["E_lev"].lt(3)
    d.loc[m, "E_lev"] = 4
    d["hw"] = d["E_lev"].ge(3)
    d.loc[m, "hwF"] = d.loc[m, "Fl"].map(list)  # the hardware claim is taken to cover the study's fault classes
    return c.set_hw_H1(d), list(df.loc[m, "rid"])


def a_e8r(df):
    """A codes as extracted before the literal A1/A2 reading (stage E8-c2b): A_primary and A_all restored from the
    E8-r extraction (15/A_codigos_E8r.csv). Replaces the earlier 'Alternative A' variant, whose studies (A_AMBIG and
    A1 with an observer in A_all) are all A2 under the literal reading."""
    ref = pd.read_csv(c._one("15 ·*") / "A_codigos_E8r.csv", dtype=str).set_index("rid")
    d = df.copy()
    old_p = d["rid"].map(ref["A_primary"]).fillna(d["Ap"])
    old_l = d["rid"].map(ref["A_all"]).map(lambda v: c.split(v) if isinstance(v, str) else None)
    m = old_p.ne(d["Ap"])
    d["Ap"] = old_p
    d["Al"] = [o if o is not None else n for o, n in zip(old_l, d["Al"])]
    return d, list(df.loc[m, "rid"])


def with_r01777():
    """L3 plus R01777 coded F4q x A3, E4, hardware for F4 (sensitivity to exclusion rule (d), stage E8-c2)."""
    src = pd.read_csv(c.P_L3, dtype=str).set_index("rid").loc["R01777"]
    row = L3.iloc[[0]].copy()
    row["rid"] = "R01777"
    row["sample"] = src["sample"]
    row["weight"] = float(src["weight"])
    row["F_ft"], row["F4_sub"], row["Ap"] = "F4", "F4q", "A3"
    row["Fl"] = [["F4"]]
    row["Al"] = [["A3"]]
    row["E_lev"], row["hw"] = 4, True
    row["hw_fault_classes"] = "F4"
    row["hwF"] = [["F4"]]
    for k in ("E_AMBIG", "A_AMBIG", "GEN", "NET", "RULE", "own", "target_journal"):
        if k in row:
            row[k] = False
    d = pd.concat([L3, row], ignore_index=True)
    return c.set_hw_H1(d)


def hw_physical_only(df):
    """Hardware evidence by fault class counted only when the run does not rest on virtual actuator channels or on an
    unstated reserve (hw_reserve, stage E8-c3); the study-level hardware share is unchanged."""
    d = df.copy()
    m = ~d["hw_phys"] & d["hw"]
    d.loc[m, "hwF"] = d.loc[m, "hwF"].map(lambda v: [])
    return c.set_hw_H1(d), list(df.loc[m, "rid"])


one, dropped = one_per_group(L3)
down, down_ids = e_down(L3)
up, up_ids = e_up(L3)
alt, alt_ids = a_e8r(L3)
L3v = {
    f"Base (L3, n = {len(L3)})": (L3, []),
    "Without Markov-jump line": (L3[~L3["rid"].isin(c.MARKOV_JUMP)], [r for r in c.MARKOV_JUMP if r in set(L3["rid"])]),
    "One study per author group": (one, dropped),
    "E_AMBIG hardware claim not counted": (down, down_ids),
    "E_AMBIG moved to E4": (up, up_ids),
    "A as coded before the literal A1/A2 reading (E8-r)": (alt, alt_ids),
    "Without OWN": (L3[~L3["own"]], list(L3.loc[L3["own"], "rid"])),
    # stage E8-c (amendment 1.10): eligibility rules written after the synthesis
    "Without generic-system studies (GEN)": (L3[~L3["GEN"]], list(L3.loc[L3["GEN"], "rid"])),
    "Without networks of manipulators (NET)": (L3[~L3["NET"]], list(L3.loc[L3["NET"], "rid"])),
    "Without R00003 and R00312 (IC1 and IC3 rules)": (L3[~L3["RULE"]], list(L3.loc[L3["RULE"], "rid"])),
    "Without the target-journal stratum": (L3[~L3["target_journal"]], list(L3.loc[L3["target_journal"], "rid"])),
    # stage E8-c2 (E8r-08): R01777, excluded under rule (d), added back as F4q x A3 with its Kinova Gen3 run counted as
    # hardware for F4 (upper bound for the excluded study)
    "With R01777 (rule-d exclusion reversed)": (with_r01777(), ["R01777"]),
    # stage E8-c3 (E8r2-02): hardware for a fault class only when the run rests on a physical reserve or needs none
    "Hardware only with a physical reserve": hw_physical_only(L3),
}
rng = np.random.default_rng(c.SEED_BOOT)
rows = []
core = ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]
# Optional time budget (environment variable RS4_TIME_BUDGET, seconds) for shells that stop long commands: the loop
# saves its rows and the generator state after each variant and resumes from them on the next run, so the result is
# identical to one uninterrupted run. Without the variable the loop runs to the end.
import os, pickle, time, hashlib, tempfile  # noqa: E401,E402
_t0 = time.time()
_budget = float(os.environ.get("RS4_TIME_BUDGET", "0") or 0)
_key = hashlib.md5(pd.util.hash_pandas_object(L3[["rid", "hw", "E_lev", "Ap", "F_ft", "hw_fault_classes", "scope_flag", "weight"]].astype(str)).values.tobytes()
                   + "|".join(L3v).encode()).hexdigest()
_part = Path(tempfile.gettempdir()) / "rs4_S3_partial.pkl"  # outside the project folder
_done = set()
if _part.exists():
    _st = pickle.loads(_part.read_bytes())
    if _st["key"] == _key:
        rows, _done = _st["rows"], set(_st["done"])
        rng.bit_generator.state = _st["rng"]
for name, (df, changed) in L3v.items():
    if name in _done:
        continue
    if _budget and time.time() - _t0 > _budget:
        _part.write_bytes(pickle.dumps(dict(key=_key, rows=rows, done=sorted(_done), rng=rng.bit_generator.state)))
        sys.exit(f"time budget reached after {len(_done)} of {len(L3v)} L3 variants; run again to resume")
    lr = df[df["sample"] == "L3-R"]
    cells_hw = cells_sim = cells_ge3 = 0
    for f in core:
        for a in c.A_CODES:
            sub = df[df["Fl"].map(lambda v, f=f: f in v) & (df["Ap"] == a)]
            if len(sub):
                k_hw = int((sub["hw"] & sub["hwF"].map(lambda v, f=f: f in v)).sum())  # pair-level rule (stage E8-c)
                if k_hw:
                    cells_hw += 1
                    cells_ge3 += k_hw >= 3
                else:
                    cells_sim += 1
    rec = dict(variant=name, n=len(df), n_L3R=len(lr), changed=";".join(changed), n_changed=len(changed),
               hw_share=c.rnd(df["hw"].mean()), hw_share_L3R_weighted=c.rnd((lr["hw"] * lr["weight"]).sum() / lr["weight"].sum()),
               A_primary=json.dumps({a: int((df["Ap"] == a).sum()) for a in c.A_CODES}),
               core_cells_hardware=cells_hw, core_cells_hw_ge3=cells_ge3, core_cells_sim_only=cells_sim,
               core_cells_empty=len(core) * 4 - cells_hw - cells_sim,
               F4t_n=int(df["F4_sub"].fillna("").str.contains("F4t").sum()), A4_n=int((df["Ap"] == "A4").sum()),
               joint_n=int(df["Fl"].map(lambda v: "F4" in v or "F5" in v).sum()))
    for h in hl.HYP:
        r = hl.test(df, h, "L3")
        rec[f"{h}_L3_OR"], rec[f"{h}_L3_lo"], rec[f"{h}_L3_hi"] = r["OR"], r["lo"], r["hi"]
        w = hl.weighted_or(lr, h)
        lo, hi, nvalid = hl.boot_weighted_or(lr, h, rng)
        rec[f"{h}_L3R_OR"], rec[f"{h}_L3R_lo"], rec[f"{h}_L3R_hi"] = c.rnd(w["OR"]), c.rnd(lo), c.rnd(hi)
        rec[f"{h}_L3R_boot_degenerate"] = c.N_BOOT - nvalid  # replicates without a finite OR (empty or single-group cells)
    rows.append(rec)
    _done.add(name)
if _part.exists():
    _part.unlink()
S3 = pd.DataFrame(rows)
c.save_csv(S3, "S3_sensibilidad_L3.csv")
out["L3_variants"] = S3.set_index("variant").drop(columns=["A_primary"]).to_dict("index")
out["group_dropped"] = dropped
out["E_AMBIG_down"] = down_ids
out["E_AMBIG_up"] = up_ids
out["A_alt"] = alt_ids
c.save_json(out, "sensibilidad.json")
print(S1.pivot_table(index="variant", columns="hyp", values=["OR", "p_holm"], sort=False).round(3).to_string())
print(S2.to_string())
print(S3.drop(columns=["changed"]).T.to_string())
