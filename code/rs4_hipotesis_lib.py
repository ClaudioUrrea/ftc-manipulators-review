"""Definitions of the confirmatory hypotheses H1-H3 shared by the RS4 scripts.

Outcome: hardware validation, E3 or E4 (bench or physical manipulator), from the
abstract bin in L1 and from the full text in L3. E4 alone is a secondary outcome.
H1  exposed: F4 or F5 present; reference: F1 present without F4 or F5. Expected OR > 1.
H2  exposed: A4 present (L1, any code; L3, primary family); reference: an A code
    assigned without A4 (A-NR records excluded). Expected OR < 1.
H3  exposed: 2021-2026; reference: 2016-2020 (synthesis window only). Hypothesis:
    no increase (OR not above 1).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

import rs4_comun as c

HYP = ["H1", "H2", "H3"]
MIN_GROUP = 3  # an odds ratio is not estimated when a group holds fewer studies
DESC = {
    "H1": "Joint-level faults (F4, F5) vs multiplicative faults (F1)",
    "H2": "Learning-based accommodation (A4) vs other families",
    "H3": "2021-2026 vs 2016-2020",
}


def groups(df: pd.DataFrame, h: str, level: str = "L1") -> tuple[pd.Series, pd.Series]:
    """Boolean masks (exposed, reference) for hypothesis h."""
    if h == "H1":
        joint = df["Fl"].map(lambda v: "F4" in v or "F5" in v)
        mult = df["Fl"].map(lambda v: "F1" in v) & ~joint
        return joint, mult
    if h == "H2":
        if level == "L1":
            a4 = df["Al"].map(lambda v: "A4" in v)
            other = df["Al"].map(len).gt(0) & ~a4
        else:
            a4 = df["Ap"].eq("A4")
            other = df["Ap"].isin(["A1", "A2", "A3"])
        return a4, other
    if h == "H3":
        late = df["year"].between(2021, 2026)
        early = df["year"].between(2016, 2020)
        return late, early
    raise ValueError(h)


def _outcome(df: pd.DataFrame, h: str, level: str, outcome: str) -> str:
    """In L3, H1 uses hardware evidence for the fault class of each group (joint-level or F1), stage E8-c."""
    return "hw_H1" if (h == "H1" and level == "L3" and outcome == "hw" and "hw_H1" in df) else outcome


def table(df: pd.DataFrame, h: str, level: str = "L1", outcome: str = "hw"):
    outcome = _outcome(df, h, level, outcome)
    ex, ref = groups(df, h, level)
    y = df[outcome].astype(bool)
    a = int((ex & y).sum()); b = int((ex & ~y).sum())
    cc = int((ref & y).sum()); d = int((ref & ~y).sum())
    return a, b, cc, d


def fisher_exact(a: int, b: int, cc: int, d: int) -> float:
    """Two-sided Fisher exact p (sum of tables no more probable than the observed one)."""
    n1, n2, k = a + b, cc + d, a + cc
    tot = math.comb(n1 + n2, k)
    pr = lambda x: math.comb(n1, x) * math.comb(n2, k - x) / tot  # noqa: E731
    p0 = pr(a)
    return min(1.0, sum(pr(x) for x in range(max(0, k - n2), min(k, n1) + 1) if pr(x) <= p0 * (1 + 1e-7)))


def test(df: pd.DataFrame, h: str, level: str = "L1", outcome: str = "hw") -> dict:
    a, b, cc, d = table(df, h, level, outcome)
    r = c.odds_ratio(a, b, cc, d)
    return dict(hyp=h, a=a, b=b, c=cc, d=d, n_exposed=a + b, n_reference=cc + d,
                p_exposed=c.rnd(a / (a + b)) if a + b else None, p_reference=c.rnd(cc / (cc + d)) if cc + d else None,
                OR=c.rnd(r["OR"]), lo=c.rnd(r["lo"]), hi=c.rnd(r["hi"]), p=r["p"], p_exact=fisher_exact(a, b, cc, d), haldane=r["haldane"])


def weighted_or(df: pd.DataFrame, h: str, outcome: str = "hw", level: str = "L3") -> dict:
    """Design-weighted OR in L3-R (weights normalized to mean 1); Haldane if a weighted cell is 0."""
    outcome = _outcome(df, h, level, outcome)
    ex, ref = groups(df, h, level)
    if ex.sum() < MIN_GROUP or ref.sum() < MIN_GROUP:
        return dict(OR=float("nan"), p_exposed=float("nan"), p_reference=float("nan"), n_exposed=int(ex.sum()),
                    n_reference=int(ref.sum()), k_exposed=int((ex & df[outcome].astype(bool)).sum()),
                    k_reference=int((ref & df[outcome].astype(bool)).sum()), haldane=False)
    w = df["weight"] / df["weight"].mean()
    y = df[outcome].astype(bool)
    a = float(w[ex & y].sum()); b = float(w[ex & ~y].sum())
    cc = float(w[ref & y].sum()); d = float(w[ref & ~y].sum())
    r = c.odds_ratio(a, b, cc, d)
    pe = a / (a + b) if a + b else float("nan")
    pr = cc / (cc + d) if cc + d else float("nan")
    return dict(OR=r["OR"], p_exposed=pe, p_reference=pr, n_exposed=int(ex.sum()), n_reference=int(ref.sum()),
                k_exposed=int((ex & y).sum()), k_reference=int((ref & y).sum()), haldane=r["haldane"])


def boot_weighted_or(df: pd.DataFrame, h: str, rng: np.random.Generator, outcome: str = "hw", level: str = "L3"):
    strata = [g for _, g in df.groupby("E_bin_abs")]
    vals = []
    for _ in range(c.N_BOOT):
        bs = pd.concat([g.sample(len(g), replace=True, random_state=int(rng.integers(1e9))) for g in strata])
        v = weighted_or(bs, h, outcome, level)["OR"]
        if np.isfinite(v):
            vals.append(v)
    if len(vals) < 0.9 * c.N_BOOT:
        return (float("nan"), float("nan"), len(vals))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return (float(lo), float(hi), len(vals))
