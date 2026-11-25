"""RS5-03. PRISMA 2020 flow diagram, drawn from the counts of the supplementary table S3 (S3_PRISMA_counts.csv).

Writes ../figures/Fig_PRISMA.pdf (and a PNG preview). Style: estilo_figuras.py (TeX Gyre Pagella, 8 pt, TrueType).
Run: python3 -I rs5_03_prisma.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent
ROOT = STAGE
RS4 = ROOT
RS3 = ROOT / "data"
sys.path.insert(0, str(ROOT / "code"))
import pandas as pd  # noqa: E402

import estilo_figuras as sf  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

def read_s3() -> pd.DataFrame:
    """S3 has one unquoted comma inside a label (UNCERTAIN row): split on the first and the last comma."""
    rows = []
    for ln in (RS3 / "S3_PRISMA_counts.csv").read_text(encoding="utf-8").splitlines()[1:]:
        phase, rest = ln.split(",", 1)
        box_, nn = rest.rsplit(",", 1)
        rows.append((phase, box_.strip('"'), nn))
    return pd.DataFrame(rows, columns=["phase", "box", "n"])


S3 = read_s3()


def n(label_start: str) -> int:
    row = S3[S3["box"].str.startswith(label_start)]
    assert len(row) == 1, label_start
    return int(str(row.iloc[0]["n"]).split("/")[0].strip())


N = dict(wos=n("Records identified: Web of Science"), sco=n("Records identified: Scopus"), dup=n("Duplicate records removed"), snow=n("Other methods: snowball"),
         rev3=n("Other methods: reviews added"), scr=n("Records screened"), uncertain=n("Records UNCERTAIN"), l1=n("Mapping set L1"), layerR=n("Layer R"),
         win=n("L1 primary studies 2016-2026"), sought=n("Reports sought"), notret=n("Reports not retrieved"), assessed=n("Reports assessed"),
         exft=n("Reports excluded at full text"), l3=n("Studies included in the synthesis set"))
EX = {k: n("Records excluded: " + k) for k in ["EX-SCOPE", "EX-FDI", "EX-IC1", "EX-IC2", "EX-PLAT", "EX-FAULT", "EX-HW"]}
EXLAB = {"EX-SCOPE": "Multi-robot team fault tolerance", "EX-FDI": "Diagnosis without accommodation", "EX-IC1": "No robot or manipulator term",
         "EX-IC2": "No specific fault term", "EX-PLAT": "Other platform", "EX-FAULT": "Fault type outside scope", "EX-HW": "Hardware design only"}
N["excl"] = sum(EX.values())
# reasons for full-text exclusion (PRISMA 2020 item 16a; Supplementary Table S4)
S4 = pd.read_csv(RS3 / "S4_fulltext_exclusions.csv", dtype=str)
FTLAB = {"EX-PLAT": "Other platform", "IC2": "No actuator or joint fault model", "EX-FDI": "Diagnosis without accommodation",
         "EX-HW": "Design without a control law or\npost-failure behavior", "EX-FAULT": "Fault type outside scope", "EX-SCOPE": "Multi-robot team fault tolerance",
         "IC1": "Not a manipulator", "IC3": "No accommodation", "EX-TYPE": "Not a primary article"}
FT = S4["reason"].value_counts()
assert int(FT.sum()) == N["exft"], (int(FT.sum()), N["exft"])
assert N["wos"] + N["sco"] - N["dup"] == N["scr"]


def main():
    sf.setup()
    fig = plt.figure(figsize=(sf.WIDTH_IN, 9.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ink, face, edge = sf.INK, "#f4f8fd", sf.INK2

    def box(x, y, w, h, text, bold=False, fc=face):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fc=fc, ec=edge, lw=0.6))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.5, color=ink, fontweight="bold" if bold else "normal", linespacing=1.25)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=edge, shrinkA=0, shrinkB=0, mutation_scale=7))

    def band(y0, y1, label):
        ax.add_patch(FancyBboxPatch((0.0, y0), 0.045, y1 - y0, boxstyle="square,pad=0", fc="#cde2fb", ec=edge, lw=0.6))
        ax.text(0.0225, (y0 + y1) / 2, label, rotation=90, ha="center", va="center", fontsize=7.5, color=ink)

    LX, LW, RX, RW = 0.07, 0.40, 0.55, 0.43
    mid = LX + LW / 2

    def stack(y, h, text, **kw):
        box(LX, y, LW, h, text, **kw)

    def branch(y, x1):
        ax.plot([mid, mid + 0.0001], [y, y], lw=0)  # anchor
        arrow(mid, y, x1, y)

    # identification
    band(0.765, 1.0, "Identification")
    box(LX, 0.885, LW, 0.115, f"Records identified from databases\n(n = {N['wos'] + N['sco']})\nWeb of Science Core Collection (n = {N['wos']})\nScopus (n = {N['sco']})")
    box(RX, 0.885, RW, 0.115, f"Records identified from other methods\nSnowballing with OpenAlex (n = {N['snow']})\nReviews added by expert knowledge (n = {N['rev3']})\nUsed for the recall estimate and the review layer")
    box(RX, 0.775, RW, 0.06, f"Duplicate records removed (n = {N['dup']})")
    ax.plot([mid, mid], [0.885, 0.72], color=edge, lw=0.6)
    arrow(mid, 0.805, RX, 0.805)
    # screening
    band(0.44, 0.745, "Screening")
    stack(0.64, 0.08, f"Records screened by scripted rules\non title, abstract and author\nkeywords (n = {N['scr']})")
    arrow(mid, 0.725, mid, 0.72)
    ex_text = f"Records excluded (n = {N['excl']})\n" + "\n".join(f"{EXLAB[k]} (n = {v})" for k, v in EX.items())
    box(RX, 0.575, RW, 0.15, ex_text)
    arrow(mid, 0.68, RX, 0.68) if False else arrow(LX + LW, 0.68, RX, 0.68)
    box(RX, 0.45, RW, 0.08, f"Records flagged as uncertain (n = {N['uncertain']});\nnot in the mapping set, added in a\nsensitivity analysis", fc="#fdf1ea")
    ax.plot([mid, mid], [0.64, 0.40], color=edge, lw=0.6)
    arrow(mid, 0.49, RX, 0.49)
    # mapping set
    band(0.215, 0.42, "Mapping set")
    stack(0.325, 0.075, f"Primary studies in the mapping set\n(n = {N['l1']})")
    box(RX, 0.325, RW, 0.075, f"Reviews retrieved by the search strings\n(n = {N['layerR']})")
    arrow(mid, 0.40, mid, 0.40)
    arrow(mid, 0.325, mid, 0.30)
    stack(0.225, 0.075, f"Primary studies in the synthesis window\n2016\u20132026 (n = {N['win']})")
    # synthesis set
    band(0.0, 0.2, "Synthesis set")
    arrow(mid, 0.225, mid, 0.19)
    stack(0.135, 0.055, f"Reports sought for retrieval (n = {N['sought']})")
    box(RX, 0.135, RW, 0.055, f"Reports not retrieved (n = {N['notret']})")
    arrow(LX + LW, 0.1625, RX, 0.1625)
    arrow(mid, 0.135, mid, 0.125)
    stack(0.07, 0.055, f"Reports assessed for eligibility (n = {N['assessed']})")
    ft_text = f"Excluded after reading the full text (n = {N['exft']})\n" + "\n".join(f"{FTLAB.get(k, k)} (n = {v})" for k, v in FT.items())
    box(RX, 0.0, RW, 0.125, ft_text)
    arrow(LX + LW, 0.0975, RX, 0.0975)
    arrow(mid, 0.07, mid, 0.06)
    stack(0.005, 0.055, f"Studies in the synthesis set (n = {N['l3']})", bold=True)
    out = STAGE / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"Fig_PRISMA.{ext}", metadata={"CreationDate": None} if ext == "pdf" else None)  # byte-reproducible
    plt.close(fig)
    print("PRISMA written", N)


if __name__ == "__main__":
    main()
