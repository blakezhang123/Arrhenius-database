"""Publication-grade Arrhenius figure (matplotlib), Origin style.

Fixes vs the old inline code:
- log scale is set BEFORE limits, and both y axes are forced to the SAME
  integer number of decades, so left/right major ticks always align.
- Major tick labels use an explicit 10^n formatter; minor ticks are
  located with a plain LogLocator and never labelled.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter, FuncFormatter

GROUP_EN = {"CoCrFeNi系高熵": "CoCrFeNi HEA", "CoCrFeMnNi系高熵": "CoCrFeMnNi HEA",
            "AlCoCrFeNi系高熵": "AlCoCrFeNi HEA", "BCC难熔高熵": "BCC refractory HEA",
            "HCP高熵": "HCP HEA", "Fe-Ni-Cr系": "Fe-Ni-Cr", "Fe-Ni系": "Fe-Ni",
            "Fe-Cr系": "Fe-Cr", "Ni-Cr系": "Ni-Cr", "Ni-Co系": "Ni-Co",
            "Cu系合金": "Cu alloys", "Ni-Al系": "Ni-Al", "Ti-Al系": "Ti-Al",
            "Co-Ga系": "Co-Ga", "Al-Sc系": "Al-Sc", "非晶合金": "metallic glass"}
STRUCT_EN = {"σ相": "sigma", "FCC+B2双相": "FCC+B2", "金红石型": "rutile", "非晶": "amorphous"}


def _en(text, mapping):
    if text in mapping:
        return mapping[text]
    return "".join(ch for ch in str(text) if ord(ch) < 128) or str(text)


R = 8.314
PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf",
           "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#393b79", "#637939"]


def _decade_formatter(y, _pos):
    if y <= 0:
        return ""
    n = int(round(np.log10(y)))
    if abs(10 ** n - y) / y > 1e-6:
        return ""
    return rf"$10^{{{n}}}$"


def _align_span(lo, hi, target_span):
    """Return (lo, hi) integer exponents spanning exactly target_span decades,
    keeping the [lo, hi] centre as close as possible."""
    centre = (lo + hi) / 2.0
    new_hi = int(np.ceil(centre + target_span / 2.0))
    return new_hi - target_span, new_hi


def build_publication_fig(rows, view_tmin, view_tmax,
                          p_exp_range=None, d_exp_range=None, t_ticks=None):
    """rows: list of dicts with keys tracer, matrix_group, matrix, structure,
    channel, D0_v_m2_s, D0_gb_m2_s, P0_m3_s, Q_kJ_mol, Tmin_K, Tmax_K, reference.
    p_exp_range / d_exp_range: (lo, hi) integer exponents or None for auto.
    Returns a matplotlib Figure."""
    def _ok(v):
        return v is not None and v == v and v != ""

    has_p = any(_ok(r.get("P0_m3_s")) for r in rows)
    has_d = any(_ok(r.get("D0_v_m2_s")) or _ok(r.get("D0_gb_m2_s")) for r in rows)

    def auto_range(kind):
        vals = []
        for r in rows:
            if not (_ok(r.get("Tmin_K")) and _ok(r.get("Tmax_K")) and _ok(r.get("Q_kJ_mol"))):
                continue
            cols = ("P0_m3_s",) if kind == "P" else ("D0_v_m2_s", "D0_gb_m2_s")
            for c in cols:
                if _ok(r.get(c)):
                    T = np.linspace(r["Tmin_K"], r["Tmax_K"], 40)
                    vals.extend(r[c] * np.exp(-(r["Q_kJ_mol"] * 1000) / (R * T)))
        if not vals:
            return (-30, -20) if kind == "P" else (-25, -15)
        return int(np.floor(np.log10(min(vals)))), int(np.ceil(np.log10(max(vals))))

    p_lo, p_hi = p_exp_range if p_exp_range else auto_range("P")
    d_lo, d_hi = d_exp_range if d_exp_range else auto_range("D")
    if has_p and has_d:
        span = max(p_hi - p_lo, d_hi - d_lo) + 1
        p_lo, p_hi = _align_span(p_lo, p_hi, span)
        d_lo, d_hi = _align_span(d_lo, d_hi, span)

    fig, ax_left = plt.subplots(figsize=(10, 7))
    ax_right = ax_left.twinx() if (has_p and has_d) else None
    ax_p = ax_left if has_p else None
    ax_d = (ax_right if ax_right is not None else ax_left) if has_d else None

    x_min, x_max = 10000.0 / view_tmax, 10000.0 / view_tmin
    T_full = np.linspace(view_tmax, view_tmin, 200)
    X_full = 10000.0 / T_full

    lines = []
    for i, r in enumerate(rows):
        if not (_ok(r.get("Tmin_K")) and _ok(r.get("Tmax_K"))):
            continue
        color = PALETTE[i % len(PALETTE)]
        label = (f"{r['tracer']} in {_en(r['matrix_group'], GROUP_EN)} "
                 f"({_en(r['structure'], STRUCT_EN)}, {r['channel']})")
        T_exp = np.linspace(r["Tmin_K"], r["Tmax_K"], 100)
        X_exp = 10000.0 / T_exp
        for col, ax_t, ls in (("D0_v_m2_s", ax_d, "-"), ("D0_gb_m2_s", ax_d, "--"),
                              ("P0_m3_s", ax_p, "-.")):
            v = r.get(col)
            if ax_t is None or not _ok(v):
                continue
            y_full = v * np.exp(-(r["Q_kJ_mol"] * 1000) / (R * T_full))
            ax_t.plot(X_full, y_full, color=color, lw=1.2, ls=ls, alpha=0.30)
            y_exp = v * np.exp(-(r["Q_kJ_mol"] * 1000) / (R * T_exp))
            line, = ax_t.plot(X_exp, y_exp, color=color, lw=2.8, ls=ls, label=label)
            lines.append(line)

    for ax_t, lo, hi, lab in ((ax_p, p_lo, p_hi, r"$P$ (m$^3$/s)"),
                              (ax_d, d_lo, d_hi, r"$D_v$, $D_{gb}$ (m$^2$/s)")):
        if ax_t is None:
            continue
        ax_t.set_yscale("log")                      # scale first …
        ax_t.set_ylim(10.0 ** lo, 10.0 ** hi)       # … then integer-decade limits
        ax_t.set_ylabel(lab, fontsize=15, fontweight="bold")
        ax_t.yaxis.set_major_locator(LogLocator(base=10.0, numticks=30))
        ax_t.yaxis.set_major_formatter(FuncFormatter(_decade_formatter))
        ax_t.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=30))
        ax_t.yaxis.set_minor_formatter(NullFormatter())
        ax_t.tick_params(axis="y", which="major", direction="in", length=8, width=1.4, labelsize=12)
        ax_t.tick_params(axis="y", which="minor", direction="in", length=4, width=1.0)

    ax_left.set_xlim(x_min, x_max)
    ax_left.set_xlabel(r"10000 / $T$ (10$^{-4}$ K$^{-1}$)", fontsize=15, fontweight="bold")
    ax_left.tick_params(axis="x", which="major", direction="in", length=8, width=1.4, labelsize=12)

    if not t_ticks:
        start = int(np.floor(view_tmax / 100.0) * 100)
        end = int(np.ceil(view_tmin / 100.0) * 100)
        cand = list(range(start, end - 1, -100))
        t_ticks, last_x = [], None
        for t in cand:  # keep top labels from crowding in 10000/T space
            x = 10000.0 / t
            if last_x is None or abs(x - last_x) >= 0.45:
                t_ticks.append(t); last_x = x
    secax = ax_left.secondary_xaxis(
        "top", functions=(lambda x: 10000.0 / np.where(x == 0, np.inf, x),
                          lambda t: 10000.0 / np.where(t == 0, np.inf, t)))
    secax.set_xlabel("$T$ (K)", fontsize=15, fontweight="bold", labelpad=10)
    secax.set_xticks([float(t) for t in t_ticks])  # secondary-axis units are K
    secax.set_xticklabels([str(t) for t in t_ticks])
    secax.tick_params(axis="x", which="major", direction="in", length=8, width=1.4, labelsize=12)

    for ax_t in (ax_left, ax_right):
        if ax_t is not None:
            for spine in ax_t.spines.values():
                spine.set_linewidth(1.4)
    if lines:
        ax_left.legend(lines, [l.get_label() for l in lines],
                       fontsize=10.5, frameon=True, edgecolor="black", loc="best")
    fig.tight_layout()
    return fig
