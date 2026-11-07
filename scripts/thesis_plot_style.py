"""Shared figure style for the thesis: Computer Modern text to match the LaTeX body, thin axes, greyscale palette, and
vector PDF output (crisp at any zoom) with a 300 dpi PNG copy for previews. Used by every thesis_* figure script."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, GRID, SHADE, SHADE2, LIGHT = "#1a1a1a", "#5f5f5f", "#e4e4e4", "#ececec", "#d2d2d2", "#a3a3a3"


def apply() -> None:
    matplotlib.rcParams.update({
        "font.family": "serif", "font.serif": ["cmr10"], "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5, "axes.linewidth": 0.6, "axes.edgecolor": INK, "axes.labelcolor": INK,
        "xtick.color": INK, "ytick.color": INK, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 3, "ytick.major.size": 3, "axes.spines.top": False, "axes.spines.right": False,
        "lines.antialiased": True, "lines.solid_joinstyle": "round", "lines.solid_capstyle": "round",
        "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    })


def save(fig, stem: Path) -> None:
    """Write stem.pdf (vector, used by the thesis) and stem.png (300 dpi preview); no timestamps, so builds repeat."""
    stem = Path(stem)
    fig.savefig(stem.with_suffix(".pdf"), metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    plt.close(fig)
    print("saved", stem.with_suffix(".pdf"))
