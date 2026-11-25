"""Common paths, loaders and statistics for stage RS4 (synthesis) of the FAME review.

All paths are relative to the project root (two levels above this file).
Input data are read only; outputs go to ../resultados and ../figuras.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent
ROOT = STAGE
RES = STAGE / "results"
FIG = STAGE / "figures"
RES.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)


def _one(pattern: str) -> Path:
    hits = sorted(ROOT.glob(pattern))
    if len(hits) != 1:
        raise FileNotFoundError(f"{pattern}: {len(hits)} matches")
    return hits[0]


RS3 = ROOT / "data"
DATA = ROOT / "data"
P_S6 = RS3 / "S6_L1_corpus_codes.csv"
P_L3 = RS3 / "EXTRACCION_L3_S5.csv"

Z95 = NormalDist().inv_cdf(0.975)
SEED_BOOT = 20261126
N_BOOT = 2000
WINDOW = (2016, 2026)
PERIODS = {"2016-2020": (2016, 2020), "2021-2026": (2021, 2026)}
F_CODES = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
A_CODES = ["A1", "A2", "A3", "A4"]
M_CODES = ["M1", "M2", "M3", "M4", "M5", "M6"]
TAGS = ["T-ML", "T-DT", "T-SAT", "T-OPEN", "T-BENCH", "OWN"]
E_ORDER = ["E0-E2", "E3", "E4"]

# Author-group dependencies and the Markov-jump line, recorded during RS3
# (08/ESTADO_cierre_RS3.md, decisions of 16-11-2026).
GROUPS = {
    "Van et al.": ["R00461", "R00700", "R00824", "R00863", "R01770"],
    "Le et al.": ["R00316", "R00790"],
    "Jin": ["R01046", "R00990"],
    "SSRMS": ["R01043", "R00682", "R00909"],
    "Baxter": ["R00615", "R00689", "R00096"],
    "Googol SCARA": ["R00613", "R00463"],
    "Semi-Markov one-link": ["R00667", "R00763", "R00541", "R00801"],
    "BU-RASL-10": ["R00783", "R00918"],
    "Quanser": ["R00550", "R00446"],
}
MARKOV_JUMP = ["R00705", "R00981", "R00699"]


# ----------------------------------------------------------------- loaders
def split(v) -> list[str]:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return []
    return [t.strip() for t in str(v).split(";") if t.strip()]


def load_s6() -> pd.DataFrame:
    d = pd.read_csv(P_S6, dtype=str)
    d["year"] = d["year"].astype(int)
    d["flags"] = d["flags"].fillna("")
    d["tags"] = d["tags"].fillna("")
    d["Fl"] = d["F"].map(split)
    d["Al"] = d["A"].map(split)
    d["Ml"] = d["M"].map(split)
    d["hw"] = d["E_bin"].isin(["E3", "E4"])
    d["E4"] = d["E_bin"].eq("E4")
    d["conf"] = d["doctype"].str.contains("Conference|Proceedings", case=False, na=False)
    d["in_wos"] = d["source"].isin(["WOS", "BOTH"])
    d["in_scopus"] = d["source"].isin(["SCOPUS", "BOTH"])
    d["own"] = d["tags"].str.contains("OWN")
    d["noabs"] = d["flags"].str.contains("NO-ABS")
    d["anr"] = d["flags"].str.contains("A-NR")
    d["in_window"] = d["year"].between(*WINDOW)
    d["period"] = np.where(d["year"].between(*PERIODS["2016-2020"]), "2016-2020",
                           np.where(d["year"].between(*PERIODS["2021-2026"]), "2021-2026", "other"))
    return d


def load_l1(include_uncertain: bool = False) -> pd.DataFrame:
    """Mapping set L1: primary records (layer P) with rule decision INCLUDE."""
    d = load_s6()
    keep = d["decision"].eq("INCLUDE") | (include_uncertain & d["decision"].eq("UNCERTAIN"))
    return d[(d["layer"] == "P") & keep].copy()


def e_level(v) -> int | None:
    if not isinstance(v, str) or not v.startswith("E"):
        return None
    return int(v[1])


def load_l3(eligible_only: bool = True) -> pd.DataFrame:
    d = pd.read_csv(P_L3, dtype=str)
    if eligible_only:
        d = d[d["ft_eligible"] == "yes"].copy()
    d["year"] = d["year"].astype(int)
    d["weight"] = pd.to_numeric(d["weight"], errors="coerce")
    d["Fl"] = d["F_ft"].map(split)
    d["Al"] = d["A_all"].map(split)
    d["Ap"] = d["A_primary"]
    d["E_lev"] = d["E_ft"].map(e_level)
    d["hw"] = d["E_lev"].ge(3)
    d["E4"] = d["E_lev"].eq(4)
    d["E_bin_ft"] = d["E_lev"].map(lambda x: None if x is None or pd.isna(x) else ("E4" if x == 4 else "E3" if x == 3 else "E0-E2"))
    d["notes"] = d["notes"].fillna("")
    d["E_AMBIG"] = d["notes"].str.contains("E_AMBIG")
    d["A_AMBIG"] = d["notes"].str.contains("A_AMBIG")
    for k in [f"R{i}" for i in range(1, 11)] + ["R_score"]:
        d[k] = pd.to_numeric(d[k], errors="coerce")
    d["period"] = np.where(d["year"] <= 2020, "2016-2020", "2021-2026")
    d["own"] = d["OWN"].fillna("0").isin(["1", "yes", "True", "true"])
    # Hardware evidence by fault class (stage E8-c): a study supports hardware evidence for fault class f only if
    # f was applied on the hardware run (field hw_fault_classes; NR = not stated, counts for no class).
    d["hwF"] = d["hw_fault_classes"].map(lambda v: [x for x in split(v) if x != "NR"])
    # Stage E8-c3: reserve exercised on the robot of the hardware run (hw_reserve) and kind of result reported for the
    # faulty hardware run (hw_result); category = text before the location in parentheses. Empty for E0-E2 studies.
    for k in ("hw_reserve", "hw_result"):
        if k not in d:
            d[k] = ""
        d[k + "_c"] = d[k].fillna("").map(lambda v: v.split(" (")[0].strip())
    # pair-level hardware evidence that does not rest on virtual actuator channels or on an unstated reserve
    d["hw_phys"] = d["hw"] & ~d["hw_reserve_c"].isin(["virtual channels", "none or not stated"])
    d["scope"] = d["scope_flag"].map(split)
    d["GEN"] = d["scope"].map(lambda v: "GEN" in v)
    d["NET"] = d["scope"].map(lambda v: "NET" in v)
    d["RULE"] = d["scope"].map(lambda v: any(x.startswith("RULE") for x in v))
    d["target_journal"] = d["selection"].fillna("").str.contains("target_journal")
    return set_hw_H1(d)


def set_hw_H1(d: pd.DataFrame) -> pd.DataFrame:
    """H1 outcome at L3 by fault class (stage E8-c): a joint-level study (F4 or F5) counts as hardware-validated only if
    F4 or F5 was applied on the hardware run, the F1 reference group only if F1 was. Recomputed whenever hw or hwF
    change (stage E8-c2, E8r-02: the E_AMBIG sensitivity variants previously reused the base value)."""
    joint = d["Fl"].map(lambda v: "F4" in v or "F5" in v)
    d["hw_H1"] = d["hw"] & np.where(joint, d["hwF"].map(lambda v: "F4" in v or "F5" in v), d["hwF"].map(lambda v: "F1" in v))
    return d


def hw_pair(row, f: str) -> bool:
    """Hardware evidence of one study for fault class f (pair-level rule, stage E8-c)."""
    return bool(row["hw"]) and f in row["hwF"]


# ------------------------------------------------------------- statistics
def wilson(k: float, n: float, z: float = Z95):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def odds_ratio(a, b, c, d, haldane: str = "auto"):
    """OR = (a/b)/(c/d) for exposed (a events, b non-events) vs reference (c, d).

    Woolf (Wald) 95 % CI and two-sided Wald p. Haldane-Anscombe (+0.5 to every
    cell) when any cell is zero (haldane='auto') or always (haldane='always').
    """
    cells = [a, b, c, d]
    corrected = haldane == "always" or (haldane == "auto" and min(cells) == 0)
    if corrected:
        a, b, c, d = (x + 0.5 for x in cells)
    if min(a, b, c, d) == 0:
        return dict(OR=float("nan"), lo=float("nan"), hi=float("nan"), p=float("nan"), haldane=corrected)
    lor = math.log(a * d / (b * c))
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    p = 2 * (1 - NormalDist().cdf(abs(lor) / se))
    return dict(OR=math.exp(lor), lo=math.exp(lor - Z95 * se), hi=math.exp(lor + Z95 * se), p=p, haldane=corrected)


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        out[k] = running
    return out


def rogan_gladen(p_obs: float, se: float, sp: float) -> float:
    den = se + sp - 1
    if den <= 0:
        return float("nan")
    return min(1.0, max(0.0, (p_obs + sp - 1) / den))


def rnd(x, k=3):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    return round(float(x), k)


def save_json(obj, name: str):
    path = RES / name
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=_default), encoding="utf-8")
    return path


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(type(o))


def save_csv(df: pd.DataFrame, name: str):
    path = RES / name
    df.to_csv(path, index=False, encoding="utf-8")
    return path
