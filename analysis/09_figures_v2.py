"""Figs 2, 4, 6 and 7 (600 dpi PNG/TIFF + vector PDF).

Run after 01_meta_analysis.R, 04_additional_analyses.R and 07_study_level_moderators.R:
    .venv/bin/python analysis/09_figures_v2.py
Flags (data_external/flags/<ISO3>.png) come from flagcdn.com (public domain flag images).
"""
import collections
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "analysis/results", ROOT / "figures"
mpl.rcParams.update({"font.family": "Helvetica", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 0.5,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "savefig.dpi": 600})
MM = 1 / 25.4
DESIGN = {"clustered": "#D55E00", "regular_grid": "#009E73", "probability_random": "#0072B2", "unknown": "#9A9A9A"}
DLAB = {"clustered": "Clustered", "regular_grid": "Regular grid", "probability_random": "Probability", "unknown": "Not reported"}
RC, SC = "#1A1A1A", "#CC79A7"


def save(fig, name):
    for ext, kw in (("png", {}), ("pdf", {}), ("tiff", {"pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", dpi=600, facecolor="white", **kw)
    plt.close(fig); print("saved", name)


def panel(ax, l, x=-0.1, y=1.03):
    ax.text(x, y, l, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom")


overall = pd.read_csv(RES / "overall_effects.csv").set_index("effect")
mods = pd.read_csv(RES / "moderators.csv")
sl = pd.read_csv(ROOT / "extraction/study_level.csv", dtype=str)
audit = pd.read_csv(RES / "reporting_audit_summary.csv")

# ================================ Fig. 2 — where the evidence comes from ===========================
codes = collections.Counter()
for v in sl.country_iso3.fillna(""):
    if any(k in v for k in ("GLOBAL", "MULTI")) or not v:
        continue
    for c in v.replace(",", ";").split(";"):
        if c.strip():
            codes[c.strip()] += 1
n_global = int(sl.country_iso3.fillna("").str.contains("GLOBAL|MULTI").sum())
world = gpd.read_file(f"zip://{ROOT}/data_external/naturalearth/ne_110m_admin_0_countries.zip")
world["n"] = world.ADM0_A3.map(codes).fillna(world.ISO_A3.map(codes)).fillna(0)
name = dict(zip(world.ADM0_A3, world.NAME))
name.update({"USA": "United States", "TWN": "Taiwan", "KOR": "South Korea"})

fig = plt.figure(figsize=(180 * MM, 165 * MM))
gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 1], width_ratios=[1.1, 0.95, 0.85], hspace=0.12, wspace=0.95)
ax = fig.add_subplot(gs[0, :])
world[world.n == 0].plot(ax=ax, color="#EDEDED", edgecolor="white", linewidth=0.3)
cmap = mpl.colormaps["YlOrRd"]
norm = mpl.colors.LogNorm(vmin=1, vmax=max(codes.values()))
world[world.n > 0].plot(ax=ax, column="n", cmap=cmap, norm=norm, edgecolor="white", linewidth=0.3)
pts = world[world.n > 0].copy()
pts["pt"] = pts.geometry.representative_point()
for _, r in pts.sort_values("n").iterrows():
    ax.scatter(r.pt.x, r.pt.y, s=6 + r.n * 5.5, facecolor="none", edgecolor="#3B3B3B", lw=0.6, zorder=3)
LBL = {"CHN": (150, 52), "USA": (-150, 22), "CAN": (-140, 74), "DEU": (35, 74), "FRA": (-30, 62), "ESP": (-42, 30),
       "AUS": (160, -42), "BRA": (-15, -22), "PER": (-118, -22), "IND": (62, 0)}
for iso, (tx, ty) in LBL.items():
    r = pts[pts.ADM0_A3 == iso]
    if len(r):
        r = r.iloc[0]
        ax.annotate(f"{name.get(iso, iso)} ({int(r.n)})", (r.pt.x, r.pt.y), xytext=(tx, ty), textcoords="data",
                    fontsize=6.4, ha="center", va="center", fontweight="bold" if iso in ("CHN", "USA", "PER") else "normal",
                    color="#B2182B" if iso == "PER" else "#222", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
                    arrowprops=dict(arrowstyle="-", color="#555", lw=0.5, shrinkA=0, shrinkB=2))
ax.set_axis_off(); ax.set_xlim(-170, 180); ax.set_ylim(-58, 84)
cax = ax.inset_axes([0.02, 0.10, 0.18, 0.035])
cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
cb.set_ticks([1, 2, 5, 10, 20, 50]); cb.set_ticklabels(["1", "2", "5", "10", "20", "50"]); cb.ax.tick_params(labelsize=5.8, length=2)
cb.set_label("Studies per country (circle size proportional)", fontsize=6.2)
ax.set_title(f"{len(codes)} countries; {n_global} further studies were global or spanned several continents", fontsize=7, color="#444")
panel(ax, "a", x=0.0, y=0.98)

# (b) top countries with flags
ax = fig.add_subplot(gs[1, 0])
top = codes.most_common(15)
if "PER" not in dict(top):
    top.append(("PER", codes["PER"]))
top = top[::-1]
ys = np.arange(len(top))
cols = ["#B2182B" if k == "PER" else "#E08214" if k in ("CHN", "USA") else "#7F7F7F" for k, _ in top]
ax.barh(ys, [v for _, v in top], color=cols, height=0.68)
for y, (k, v) in zip(ys, top):
    ax.text(v + 0.8, y, str(v), va="center", fontsize=6.2)
    f = ROOT / f"data_external/flags/{k}.png"
    if f.exists():
        img = plt.imread(f)
        ab = AnnotationBbox(OffsetImage(img, zoom=0.11), (-1.2, y), xycoords=("data", "data"), frameon=True, pad=0.05, box_alignment=(1, 0.5),
                            bboxprops=dict(ec="#BBBBBB", lw=0.3, fc="white"))
        ax.add_artist(ab)
ax.set_yticks(ys); ax.set_yticklabels([name.get(k, k) for k, _ in top]); ax.tick_params(axis="y", pad=17, length=0)
ax.set_xlim(0, max(v for _, v in top) * 1.18); ax.set_xlabel("Studies")
ax.set_title("Most studied countries", loc="left", fontsize=7.5, fontweight="bold")
panel(ax, "b", x=-0.55)

# (c) continents by sampling design
ax = fig.add_subplot(gs[1, 1])
c = sl.continent.replace({"Multiple": "Global", "Antarctica": "Global"}).fillna("Global")
sd = pd.read_csv(ROOT / "extraction/extraction_template.csv", low_memory=False).groupby("record_id").sampling_design.first()
tab = pd.crosstab(c.values, sl.record_id.map(sd).where(lambda s: s.isin(list(DESIGN)), "unknown").values)
tab = tab.reindex(columns=list(DESIGN)).fillna(0)
tab = tab.loc[tab.sum(axis=1).sort_values().index]
left = np.zeros(len(tab))
for k in DESIGN:
    ax.barh(tab.index, tab[k], left=left, color=DESIGN[k], height=0.65, label=DLAB[k]); left += tab[k].values
for y, v in enumerate(tab.sum(axis=1)):
    ax.text(v + 1.5, y, f"{int(v)} ({100 * v / len(sl):.0f}%)", va="center", fontsize=6)
ax.set_xlim(0, tab.sum(axis=1).max() * 1.75); ax.set_xlabel("Studies")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=2, fontsize=5.8, title="Sampling design", title_fontsize=6)
ax.set_title("Continents", loc="left", fontsize=7.5, fontweight="bold")
panel(ax, "c", x=-0.5)

# (d) reporting audit
ax = fig.add_subplot(gs[1, 2])
lab = {"sampling_reported": "Sampling design", "open_data": "Open data", "open_code": "Open code", "block_size_reported": "Block/buffer size",
       "sd_reported": "CV uncertainty", "independent_validation": "Independent test", "range_reported": "Autocorr. range"}
a = audit.assign(lbl=audit.item.map(lab)).sort_values("share")
ax.barh(a.lbl, a.share * 100, color="#4D4D4D", height=0.6)
for y, v in enumerate(a.share * 100):
    ax.text(v + 2, y, f"{v:.0f}%", va="center", fontsize=6.2)
ax.set_xlim(0, 100); ax.set_xlabel("Studies reporting (%)")
ax.set_title("What studies report", loc="left", fontsize=7.5, fontweight="bold")
panel(ax, "d", x=-0.95)
save(fig, "Fig2_evidence_map")

# ================================ Fig. 4 — sampling design: distributions + estimates =============
e2 = pd.read_csv(RES / "effects_dR2.csv")
em = pd.read_csv(RES / "effects_lnRR_RMSE.csv"); em["yi"] = 100 * (np.exp(em.yi) - 1)
ORDER = ["clustered", "regular_grid", "unknown", "probability_random"]


def half_violin(ax, e, nm, xlab, clip, to_pct=False):
    m = mods[(mods.effect == nm) & (mods.moderator == "sampling_h")].copy()
    m["lvl"] = m.level.str.replace("sampling_h", "", regex=False)
    conv = (lambda v: 100 * (np.exp(v) - 1)) if to_pct else (lambda v: v)
    for j, k in enumerate(ORDER):
        v = e.loc[e.sampling_h == k, "yi"].clip(*clip).values
        y0 = len(ORDER) - 1 - j
        if len(v) > 2:
            vp = ax.violinplot(v, positions=[y0], vert=False, widths=0.85, showextrema=False)
            for b in vp["bodies"]:
                b.set_facecolor(DESIGN[k]); b.set_alpha(0.35); b.set_edgecolor("none")
                pth = b.get_paths()[0]; pth.vertices[:, 1] = np.clip(pth.vertices[:, 1], y0, None)
            ax.scatter(v, y0 - 0.12 - np.random.default_rng(3).uniform(0, 0.18, len(v)), s=1.5, color=DESIGN[k], alpha=0.5, lw=0)
        r = m[m.lvl == k]
        if len(r):
            r = r.iloc[0]
            est, lo, hi = conv(r.estimate), conv(r.ci_lb), conv(r.ci_ub)
            ax.plot([lo, hi], [y0 + 0.06, y0 + 0.06], color="black", lw=1.6, solid_capstyle="butt")
            ax.scatter(est, y0 + 0.06, s=26, color="white", edgecolor="black", lw=1, zorder=4)
            ax.text(clip[1], y0 + 0.28, f"{est:.2f}" if not to_pct else f"+{est:.0f}%", ha="right", fontsize=6.5, fontweight="bold")
            ax.text(clip[1], y0 + 0.08, f"{int(r.k_studies)} studies", ha="right", fontsize=5.8, color="#555")
    ov = overall.loc[nm]
    ax.axvspan(conv(ov.ci_lb), conv(ov.ci_ub), color="#E6E6E6", zorder=0)
    ax.axvline(0, color="#555", lw=0.6, ls="--")
    ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([DLAB[k] for k in ORDER[::-1]])
    ax.set_ylim(-0.5, len(ORDER) - 0.35); ax.set_xlim(clip); ax.set_xlabel(xlab)
    p = m.QM_p_heterogeneity_between_levels.iloc[0]
    ax.set_title(f"Test of difference between designs: {'p < 0.001' if p < 0.001 else f'p = {p:.2f}'}", loc="right", fontsize=6.5, color="#444")


fig, axs = plt.subplots(1, 2, figsize=(180 * MM, 82 * MM), sharey=True, gridspec_kw={"wspace": 0.08})
half_violin(axs[0], e2, "dR2", "$R^2$ under random CV minus $R^2$ under spatial CV", (-0.5, 1.0)); panel(axs[0], "a", x=-0.2)
half_violin(axs[1], em, "lnRR_RMSE", "RMSE under spatial CV relative to random CV (% higher)", (-50, 180), to_pct=True); panel(axs[1], "b", x=-0.03)
axs[0].legend(handles=[Line2D([], [], marker="o", ls="-", color="black", mfc="white", ms=4, label="Estimate and 95% CI"),
                       mpl.patches.Patch(color="#E6E6E6", label="Pooled estimate (95% CI)")], frameon=False, loc="upper center", bbox_to_anchor=(1.0, -0.17), ncol=2, fontsize=6.3)
save(fig, "Fig4_raincloud_sampling")

# ================================ Fig. 6 — agreement with independent tests =======================
ind = pd.read_csv(RES / "independent_validation_rows.csv")
TYPE = {"probability_sample": "Probability\nsample", "other": "Other\nhold-out", "temporal": "Later\nperiod", "other_region": "Other\nregion"}
ind["type"] = ind.ind_type.map(TYPE).fillna("Other\nhold-out")
order_t = [t for t in TYPE.values() if t in set(ind.type)]
d = ind[ind.metric.isin(["R2", "accuracy", "AUC"])]
fig, axs = plt.subplots(1, 3, figsize=(180 * MM, 74 * MM), gridspec_kw={"width_ratios": [1.6, 1, 1], "wspace": 0.45})
ax = axs[0]
for i, t in enumerate(order_t):
    sub = d[d.type == t]
    for j, (col, c) in enumerate((("opt_random", RC), ("opt_spatial", SC))):
        x = i + (-0.18 if j == 0 else 0.18)
        v = sub[col].values
        if len(v):
            ax.boxplot(v, positions=[x], widths=0.28, vert=True, patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor=c, alpha=0.25, edgecolor=c, lw=0.8), medianprops=dict(color=c, lw=1.4),
                       whiskerprops=dict(color=c, lw=0.8), capprops=dict(color=c, lw=0.8))
            ax.scatter(x + np.random.default_rng(i * 2 + j).uniform(-0.08, 0.08, len(v)), v, s=5, color=c, alpha=0.7, lw=0, zorder=3)
    ax.text(i, ax.get_ylim()[0] if False else -0.38, f"{sub.record_id.nunique()} st.", ha="center", fontsize=5.8, color="#555")
ax.axhline(0, color="#555", lw=0.6, ls="--")
ax.set_xticks(range(len(order_t))); ax.set_xticklabels(order_t, fontsize=6.3); ax.set_ylim(-0.42, 0.62); ax.set_xlim(-0.85, len(order_t) - 0.4)
ax.set_ylabel("CV estimate minus independent estimate\n($R^2$, AUC, accuracy)")
ax.text(-0.72, 0.3, "CV optimistic", rotation=90, fontsize=6, color="#555", ha="center", va="center")
ax.text(-0.72, -0.2, "CV pessimistic", rotation=90, fontsize=6, color="#555", ha="center", va="center")
ax.legend(handles=[mpl.patches.Patch(color=RC, alpha=0.6, label="Random CV"), mpl.patches.Patch(color=SC, alpha=0.6, label="Spatial CV")],
          frameon=False, loc="upper left", fontsize=6.2)
panel(ax, "a", x=-0.3)
summ = pd.read_csv(RES / "independent_validation_summary.csv")
ax = axs[1]
for g, sc in enumerate(("difference", "log ratio")):
    s_ = summ[summ.scale == sc]
    for j, (q, c) in enumerate((("optimism_random", RC), ("optimism_spatial", SC))):
        r = s_[s_.quantity == q].iloc[0]; x = g + (j - 0.5) * 0.36
        ax.bar(x, r["mean"], color=c, alpha=0.85, width=0.34)
        ax.errorbar(x, r["mean"], yerr=[[r["mean"] - r.lo], [r.hi - r["mean"]]], color="black", lw=0.8, capsize=2)
        ax.text(x + (j - 0.5) * 0.12, r.hi + 0.015, f"{r['mean']:+.2f}\n{'p < 0.01' if r.p < 0.01 else f'p = {r.p:.2f}'}", ha="center", fontsize=5.6)
    ax.text(g, -0.27, f"{int(s_.studies.iloc[0])} studies", ha="center", fontsize=5.8, color="#555")
ax.axhline(0, color="#555", lw=0.6)
ax.set_xticks([0, 1]); ax.set_xticklabels(["$R^2$, AUC,\naccuracy", "RMSE, MAE\n(log ratio)"], fontsize=6.3); ax.set_ylim(-0.3, 0.6)
ax.set_ylabel("Mean optimism (95% CI)")
ax.set_title("Average over all tests", fontsize=7, loc="left")
panel(ax, "b", x=-0.45)
ax = axs[2]
sh = ind.groupby("type").agg(sp=("abs_gap", lambda v: (v > 0).mean() * 100)).reindex(order_t)
yb = np.arange(len(order_t))
ax.barh(yb, sh.sp, color=SC, height=0.6)
ax.barh(yb, 100 - sh.sp, left=sh.sp, color=RC, height=0.6)
for i, v in enumerate(sh.sp):
    ax.text(3, i, f"{v:.0f}%", va="center", color="white", fontsize=6.3, fontweight="bold")
    ax.text(97, i, f"{100 - v:.0f}%", va="center", ha="right", color="white", fontsize=6.3, fontweight="bold")
ax.axvline(50, color="white", lw=0.8)
ax.set_yticks(yb); ax.set_yticklabels(order_t, fontsize=6.3); ax.set_xlim(0, 100)
ax.set_xlabel("Comparisons where each\nCV is closer (%)")
ax.set_title("Which CV is closer to the test?", fontsize=7, loc="left")
ax.text(25, -0.75, "Spatial", ha="center", fontsize=6, color=SC, fontweight="bold")
ax.text(75, -0.75, "Random", ha="center", fontsize=6, color=RC, fontweight="bold")
ax.set_ylim(len(order_t) - 0.5, -0.95)
panel(ax, "c", x=-0.5)
save(fig, "Fig6_independent_validation")

# ================================ Fig. 7 — expected spatial R2 (calibration), one panel =========
# Each row is a reported random-CV R2; coloured points show the R2 expected under spatial CV.
calc = pd.read_csv(RES / "calibration_curve.csv")
SHOW = ["clustered", "regular_grid", "probability_random"]
ROWS = [0.9, 0.8, 0.7, 0.6]
OFF = {"clustered": 0.18, "regular_grid": 0.0, "probability_random": -0.18}
fig, ax = plt.subplots(figsize=(150 * MM, 88 * MM))
for i, v in enumerate(ROWS):
    y = len(ROWS) - 1 - i
    ax.axhspan(y - 0.42, y + 0.42, color="#F4F4F4" if i % 2 == 0 else "white", lw=0, zorder=0)
    lo = min(float((calc[(calc.sampling_h == k) & (calc.vr.round(2) == v)].vr - calc[(calc.sampling_h == k) & (calc.vr.round(2) == v)].gap_hi).iloc[0]) for k in SHOW)
    for k in SHOW:
        r = calc[(calc.sampling_h == k) & (calc.vr.round(2) == v)].iloc[0]
        e, a, b = r.vr - r.gap, r.vr - r.gap_hi, r.vr - r.gap_lo
        yy = y + OFF[k]
        ax.annotate("", xy=(e, yy), xytext=(v, yy), arrowprops=dict(arrowstyle="-|>", color=DESIGN[k], lw=1.1, mutation_scale=7, shrinkA=3, shrinkB=4))
        ax.plot([a, b], [yy, yy], color=DESIGN[k], lw=3.2, alpha=0.25, solid_capstyle="butt")
        ax.scatter(e, yy, s=28, color=DESIGN[k], zorder=4, edgecolor="white", lw=0.5)
        ax.text(a - 0.008, yy, f"{e:.2f}", ha="right", va="center", fontsize=6.6, color=DESIGN[k], fontweight="bold")
    ax.scatter(v, y, s=46, color="black", zorder=5, marker="D")
    ax.text(v + 0.012, y, f"{v:.1f}", ha="left", va="center", fontsize=7, fontweight="bold")
ax.set_yticks(range(len(ROWS))); ax.set_yticklabels([f"Reported $R^2$ = {v:.1f}" for v in ROWS[::-1]], fontsize=7)
ax.tick_params(axis="y", length=0)
ax.set_xlim(0.2, 0.97); ax.set_ylim(-0.6, len(ROWS) - 0.4)
ax.set_xlabel("$R^2$  (black diamond: reported with random CV; coloured point: expected with spatial CV)")
ax.spines[["left", "top", "right"]].set_visible(False)
ax.grid(axis="x", color="#E3E3E3", lw=0.5); ax.set_axisbelow(True)
from matplotlib.lines import Line2D as _L
h = [_L([], [], marker="o", ls="-", color=DESIGN[k], ms=4, lw=1.1, label=DLAB[k]) for k in SHOW]
h.append(mpl.patches.Patch(color="#999999", alpha=0.35, label="95% confidence interval"))
ax.legend(handles=h, title="Sampling design of the data", frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=4, fontsize=6.6, title_fontsize=6.8)
save(fig, "Fig7_calibration_R2")
