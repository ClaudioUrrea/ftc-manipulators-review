"""RS4-9. Publication figures (Sensors). All values read from resultados/.

Fig. 1  Mapping-set records per year by evidence bin (L1).
Fig. 2  Fault model x accommodation map: (a) full text, L3, primary family; (b) mapping set, L1, descriptive.
Fig. 3  Confirmatory odds ratios H1-H3 (L1 primary, L1 sensitivity variants, L3-R check).
Fig. 4  FAME reporting checklist R1-R10 (L3), by evidence level.
Fig. 5  Hardware share in 2016-2026: abstract bin, Rogan-Gladen corrected, by period.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import estilo_figuras as st  # noqa: E402
import rs4_comun as c  # noqa: E402

_D = json.loads((c.RES / "descriptivos.json").read_text(encoding="utf-8"))
N3, N1 = _D["L3_n"], _D["L1_n"]

st.setup()
R = c.RES
MINUS = "−"


def num(x, k=2):
    s = f"{x:.{k}f}"
    return s.replace("-", MINUS)


# ------------------------------------------------------------------ Fig. 1
D1 = pd.read_csv(R / "D1_registros_por_anio_fuente.csv")
D1 = D1[D1["year"] <= 2026]
early = D1[D1["year"] < 2000][["L1_E0E2", "L1_E3", "L1_E4"]].sum()
late = D1[D1["year"] >= 2000].set_index("year")[["L1_E0E2", "L1_E3", "L1_E4"]]
labels = ["Before 2000"] + [str(y) for y in late.index]
vals = np.vstack([early.values, late.values])
fig, ax = plt.subplots(figsize=(st.WIDTH_IN, 2.3))
x = np.arange(len(labels))
bottom = np.zeros(len(labels))
names = {"L1_E0E2": "Simulation or analysis (E0–E2)", "L1_E3": "Bench or HIL (E3)", "L1_E4": "Physical manipulator (E4)"}
for j, (col, e) in enumerate(zip(["L1_E0E2", "L1_E3", "L1_E4"], ["E0-E2", "E3", "E4"])):
    ax.bar(x, vals[:, j], bottom=bottom, color=st.E_COLORS[e], width=0.78, edgecolor="white", linewidth=0.4, label=names[col])
    bottom += vals[:, j]
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=90)
ax.set_ylabel("Primary studies (L1)")
ax.yaxis.grid(True, color=st.GRID, linewidth=0.4)
ax.set_axisbelow(True)
ax.axvspan(x[labels.index("2016")] - 0.5, x[-1] + 0.5, color="#f0efec", zorder=0, linewidth=0)
ax.text(x[labels.index("2016")] - 0.3, bottom.max() * 0.97, "Synthesis window", fontsize=7.5, color=st.INK2, va="top")
ax.legend(loc="upper left", bbox_to_anchor=(0.07, 0.97))
ax.set_xlim(-0.6, len(labels) - 0.4)
st.save(fig, "Fig1_registros_por_anio")

# ------------------------------------------------------------------ Fig. 2
D4 = pd.read_csv(R / "D4_FxA_L3.csv")
D5 = pd.read_csv(R / "D5_FxA_L1_descriptivo.csv")
D5 = D5[D5["set"] == "L1 all years"]
Fs = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F0"]
Fnames = {"F1": "F1 Loss of effectiveness", "F2": "F2 Additive bias", "F3": "F3 Reduced torque bound", "F4": "F4 Stuck or locked",
          "F5": "F5 Free-swinging", "F6": "F6 Intermittent or time-varying", "F7": "F7 Transmission", "F8": "F8 Sensor",
          "F0": "F0 Unspecified"}
As = ["A1", "A2", "A3", "A4"]
Anames = ["A1", "A2", "A3", "A4"]
fig, axes = plt.subplots(1, 2, figsize=(st.WIDTH_IN, 3.0), gridspec_kw=dict(wspace=0.22))
any_amb = False
for k, (ax, df, ttl) in enumerate(zip(axes, [D4, D5], [f"(a) Full text, L3 (n = {N3})", f"(b) Abstracts, L1 (n = {N1}), descriptive"])):
    M = np.zeros((len(Fs), len(As))); H = np.zeros_like(M); HA = np.zeros_like(M)
    for i, f in enumerate(Fs):
        for j, a in enumerate(As):
            r = df[(df["F"] == f) & (df["A"] == a)].iloc[0]
            M[i, j] = r["n"]; H[i, j] = r["n_hw"]
            HA[i, j] = r["n_hw_no_EAMBIG"] if "n_hw_no_EAMBIG" in r and pd.notna(r["n_hw_no_EAMBIG"]) else r["n_hw"]
    bounds = [0, 1, 2, 4, 8, 16, 32, 64, 1e6] if k == 0 else [0, 1, 4, 8, 16, 32, 64, 128, 1e6]
    cmap = ListedColormap(st.SEQ)
    norm = BoundaryNorm(bounds, cmap.N)
    im = ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
    # color scale (stage E8-c2b, E8r-10): discrete bins of the number of studies per cell
    cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.02, spacing="uniform", boundaries=bounds[1:-1] + [bounds[-2] * 2])
    cb.set_ticks(bounds[1:-1])
    cb.set_ticklabels([str(int(b)) for b in bounds[1:-1]])
    cb.ax.tick_params(labelsize=6.5, length=2)
    cb.outline.set_visible(False)
    cb.ax.minorticks_off()
    if k == 1:
        cb.set_label("Studies per cell", fontsize=7)
    for i in range(len(Fs)):
        for j in range(len(As)):
            n, h = int(M[i, j]), int(H[i, j])
            if n == 0:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="////", edgecolor="#b9b8b2", linewidth=0))
                continue
            dark = norm(n) >= 4
            col = "white" if dark else st.INK
            amb = k == 0 and h > 0 and HA[i, j] == 0  # hardware only from an ambiguous evidence claim (E_AMBIG)
            any_amb = any_amb or amb
            ax.text(j, i, f"{n}" + (f" ({h}{'*' if amb else ''})" if h else ""), ha="center", va="center", fontsize=7.5, color=col)
            if k == 0 and h == 0:
                ax.add_patch(Rectangle((j - 0.46, i - 0.46), 0.92, 0.92, fill=False, edgecolor=st.ACCENT, linewidth=0.9))
    ax.set_xticks(range(len(As))); ax.set_xticklabels(Anames)
    ax.set_yticks(range(len(Fs)))
    ax.set_yticklabels([Fnames[f] for f in Fs] if k == 0 else [""] * len(Fs))
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(As)), minor=True); ax.set_yticks(np.arange(-0.5, len(Fs)), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", length=0)
    ax.axhline(6.5, color=st.INK2, linewidth=0.6)
    ax.set_title(ttl, loc="left", fontsize=8)
handles = [Patch(facecolor="white", edgecolor="#b9b8b2", hatch="////", label="Empty cell"),
           Patch(facecolor="white", edgecolor=st.ACCENT, linewidth=0.9, label="Simulation or analysis only (L3)")]
fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.55, -0.06))
fig.text(0.5, -0.11, "A1 passive, A2 active, A3 redundancy-based, A4 learning-based. Cell value: studies; in parentheses, studies with hardware evidence (E3–E4)", ha="center", fontsize=7.5, color=st.INK2)
fig.text(0.5, -0.155, "for that fault class in (a) and in the abstract bin in (b)" + ("; * hardware only from an ambiguous evidence claim." if any_amb else "."), ha="center", fontsize=7.5, color=st.INK2)
st.save(fig, "Fig2_mapa_FxA")

# ------------------------------------------------------------------ Fig. 3
H = pd.read_csv(R / "H1_confirmatorias.csv")
S1 = pd.read_csv(R / "S1_sensibilidad_L1.csv")
hyp_lbl = {"H1": "H1  Joint-level (F4, F5) vs F1", "H2": "H2  Learning-based (A4) vs other", "H3": "H3  2021–2026 vs 2016–2020"}
fig, ax = plt.subplots(figsize=(st.WIDTH_IN, 2.6))
ypos, ylab = [], []
y = 0
for h in ["H1", "H2", "H3"]:
    prim = H[(H["hyp"] == h) & (H["set"] == "L1 primary")].iloc[0]
    chk = H[(H["hyp"] == h) & (H["set"] == "L3-R check (weighted)")].iloc[0]
    sens = S1[(S1["hyp"] == h) & (S1["variant"] != "Primary (union, INCLUDE)")]
    ax.scatter(sens["OR"], np.full(len(sens), y + 0.22), s=9, color="#9ec5f4", zorder=2, linewidths=0, label="L1 sensitivity variants" if h == "H1" else None)
    ax.errorbar(prim["OR"], y, xerr=[[prim["OR"] - prim["lo"]], [prim["hi"] - prim["OR"]]], fmt="o", color=st.E_COLORS["E4"], ms=4.5,
                capsize=0, elinewidth=1.2, label="L1 primary (abstract E bin)" if h == "H1" else None, zorder=3)
    if np.isfinite(chk["OR"]):
        ax.errorbar(chk["OR"], y - 0.3, xerr=[[chk["OR"] - chk["lo"]], [chk["hi"] - chk["OR"]]], fmt="s", color=st.ACCENT, ms=4,
                    capsize=0, elinewidth=1.2, label="L3-R check (full-text E, weighted)" if h == "H1" else None, zorder=3)
    else:
        ax.text(1.0, y - 0.3, "  L3-R: not estimable (one A4 study)", fontsize=7, color=st.INK2, va="center")
    ax.text(305, y, f"p(Holm) = {num(prim['p_holm'])}" if "p_holm" in prim and pd.notna(prim["p_holm"]) else "", fontsize=7.5, va="center", ha="right", color=st.INK2)
    ypos.append(y); ylab.append(hyp_lbl[h]); y -= 1.3
ax.axvline(1, color=st.INK2, linewidth=0.6, linestyle=(0, (3, 2)))
ax.set_xscale("log")
ax.set_xlim(0.05, 320)
ax.set_xticks([0.1, 0.3, 1, 3, 10, 30, 100])
ax.set_xticklabels(["0.1", "0.3", "1", "3", "10", "30", "100"])
ax.set_yticks(ypos); ax.set_yticklabels(ylab)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.set_xlabel("Odds ratio of hardware validation (E3–E4), 95% CI, log scale")
ax.set_ylim(y + 0.6, 0.6)
ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3)
st.save(fig, "Fig3_hipotesis_OR")

# ------------------------------------------------------------------ Fig. 4
IT = pd.read_csv(R / "R2_checklist_por_item.csv")
fig, ax = plt.subplots(figsize=(st.WIDTH_IN, 2.6))
yy = np.arange(len(IT))[::-1]
ax.barh(yy, IT["share"], color="#cde2fb", height=0.62, label=f"All L3 studies (n = {N3})")
ax.errorbar(IT["share"], yy, xerr=[IT["share"] - IT["lo"], IT["hi"] - IT["share"]], fmt="none", ecolor=st.INK2, elinewidth=0.6, capsize=0)
ax.scatter(IT["share_simulation"], yy + 0.12, marker="o", s=14, color=st.E_COLORS["E0-E2"], edgecolor=st.E_COLORS["E4"], linewidth=0.5, zorder=3, label="Simulation or analysis (E0–E2)")
ax.scatter(IT["share_hardware"], yy - 0.12, marker="D", s=13, color=st.E_COLORS["E4"], zorder=3, label="Hardware (E3–E4)")
ax.set_yticks(yy); ax.set_yticklabels([f"{r.item}  {r.label}" for r in IT.itertuples()])
ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 1); ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); ax.set_xticklabels(["0", "20", "40", "60", "80", "100"])
ax.set_xlabel("Studies reporting the item (%)")
ax.xaxis.grid(True, color=st.GRID, linewidth=0.4); ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.legend(loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=3)
st.save(fig, "Fig4_checklist_R1_R10")

# ------------------------------------------------------------------ Fig. 5
RG = pd.read_csv(R / "E2_rogan_gladen.csv").set_index("group")
hj = json.loads((R / "hipotesis.json").read_text(encoding="utf-8"))
groups = ["L1 2016-2026", "L1 2016-2020", "L1 2021-2026"]
glab = ["2016–2026", "2016–2020", "2021–2026"]
fig, ax = plt.subplots(figsize=(st.WIDTH_IN * 0.62, 2.0))
xx = np.arange(len(groups))
for dx, col, lo, hi, lab, colr, mk in [(-0.12, "p_raw", "raw_lo", "raw_hi", "Abstract bin (raw)", st.E_COLORS["E3"], "o"),
                                       (0.12, "p_corrected", "corr_lo", "corr_hi", "Rogan–Gladen corrected", st.ACCENT, "s")]:
    v = RG.loc[groups, col].values
    ax.errorbar(xx + dx, v, yerr=[v - RG.loc[groups, lo].values, RG.loc[groups, hi].values - v], fmt=mk, color=colr, ms=4, elinewidth=1.1, capsize=0, label=lab)
ax.errorbar([-0.36], [hj["E_prev_design"]], yerr=[[hj["E_prev_design"] - hj["E_prev_design_ci"][0]], [hj["E_prev_design_ci"][1] - hj["E_prev_design"]]],
            fmt="D", color=st.E_COLORS["E4"], ms=3.8, elinewidth=1.1, capsize=0, label="Full text, L3-R design-based")
ax.set_xticks(xx); ax.set_xticklabels(glab)
ax.set_ylim(0, 0.45); ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4]); ax.set_yticklabels(["0", "10", "20", "30", "40"])
ax.set_ylabel("Hardware-validated (%)")
ax.yaxis.grid(True, color=st.GRID, linewidth=0.4); ax.set_axisbelow(True)
ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
st.save(fig, "Fig5_correccion_E")
print("figures written")
