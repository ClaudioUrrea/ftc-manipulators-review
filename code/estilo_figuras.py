"""Shared figure style (MDPI template font: TeX Gyre Pagella, 8 pt, TrueType embedding).

TeX Gyre Pagella ships as OpenType (CFF); it is converted once to TrueType
(quadratic outlines) and cached under figuras/_fuente/, so that PDF output embeds
it as Type 42 and pdffonts reports a TrueType font.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

import rs4_comun as c  # noqa: E402

OTF_DIRS = [Path("/usr/share/texmf/fonts/opentype/public/tex-gyre"), Path("/usr/share/texlive/texmf-dist/fonts/opentype/public/tex-gyre"),
            Path("/usr/share/fonts/opentype/tex-gyre")]
CACHE = c.FIG / "_fuente_tt"
FAMILY = "TeX Gyre Pagella TT"  # renamed TrueType copy, distinct from the system OTF
WIDTH_IN = 13.5 / 2.54  # full text width of the MDPI layout, approx. 13.5 cm

# colors (validated reference palette): ordinal blue ramp for evidence, orange accent, inks
E_COLORS = {"E0-E2": "#86b6ef", "E3": "#2a78d6", "E4": "#104281"}
ACCENT = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#d9d8d4"
SEQ = ["#ffffff", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def _ttf(style: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    ttf = CACHE / f"texgyrepagella-{style}.ttf"
    if ttf.exists():
        return ttf
    src = next((d / f"texgyrepagella-{style}.otf" for d in OTF_DIRS if (d / f"texgyrepagella-{style}.otf").exists()), None)
    if src is None:
        raise FileNotFoundError("TeX Gyre Pagella OTF not found")
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont, newTable

    f = TTFont(str(src))
    order = f.getGlyphOrder()
    gs = f.getGlyphSet()
    glyf = newTable("glyf"); glyf.glyphOrder = order; glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(gs)
        gs[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    del f["CFF "]
    if "VORG" in f:
        del f["VORG"]
    f["glyf"] = glyf
    f["loca"] = newTable("loca")
    maxp = f["maxp"]; maxp.tableVersion = 0x00010000
    for k in ["maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs", "maxStackElements",
              "maxSizeOfInstructions", "maxComponentElements", "maxPoints", "maxContours", "maxCompositePoints",
              "maxCompositeContours", "maxComponentDepth"]:
        setattr(maxp, k, 0)
    maxp.maxZones = 1
    f["head"].glyphDataFormat = 0
    post = f["post"]; post.formatType = 2.0; post.extraNames = []; post.mapping = {}; post.glyphOrder = order
    f.sfntVersion = "\x00\x01\x00\x00"
    for rec in f["name"].names:
        if rec.nameID in (1, 3, 4, 6, 16):
            txt = rec.toUnicode()
            txt = txt.replace("TeX Gyre Pagella", FAMILY).replace("TeXGyrePagella", "TeXGyrePagellaTT")
            rec.string = txt
    f.save(str(ttf))
    return ttf


def setup():
    for st in ["regular", "italic", "bold", "bolditalic"]:
        font_manager.fontManager.addfont(str(_ttf(st)))
    plt.rcParams.update({
        "font.family": FAMILY, "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "mathtext.fontset": "custom", "mathtext.rm": FAMILY,
        "mathtext.it": f"{FAMILY}:italic", "mathtext.bf": f"{FAMILY}:bold", "mathtext.cal": FAMILY, "mathtext.sf": FAMILY, "mathtext.tt": FAMILY, "axes.unicode_minus": True,
        "pdf.fonttype": 42, "ps.fonttype": 42, "axes.edgecolor": INK2, "axes.linewidth": 0.6, "axes.labelcolor": INK,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "savefig.dpi": 600,
        "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "hatch.linewidth": 0.5,
    })


def save(fig, name: str):
    for ext in ("pdf", "png"):  # no creation date in the PDF, so that a rerun gives byte-identical files (stage E8-c)
        fig.savefig(c.FIG / f"{name}.{ext}", metadata={"CreationDate": None} if ext == "pdf" else None)
    plt.close(fig)
