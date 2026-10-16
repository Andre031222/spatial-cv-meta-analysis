import re
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "analysis/results", ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "Helvetica", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 0.5,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.dpi": 600, "figure.dpi": 150,
})
MM = 1 / 25.4
DESIGN = {"clustered": "#D55E00", "probability_random": "#0072B2", "regular_grid": "#009E73", "unknown": "#9A9A9A"}
DLAB = {"clustered": "Clustered", "probability_random": "Probability", "regular_grid": "Regular grid", "unknown": "Not reported"}
ORDER = list(DESIGN)

def save(fig, name):
    for ext, kw in (("png", {}), ("pdf", {}), ("tiff", {"pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", dpi=600, facecolor="white", **kw)
    plt.close(fig)
    print("saved", name)

def panel(ax, letter, x=-0.12, y=1.04):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom")

fd = pd.read_csv(ROOT / "fulltext/fulltext_decisions.csv")
inc = set(fd.loc[fd.ft_decision == "include", "record_id"])
ex = pd.read_csv(ROOT / "extraction/extraction_template.csv", low_memory=False)
ex = ex[ex.record_id.isin(inc) & (ex.primary == "yes")].copy()
overall = pd.read_csv(RES / "overall_effects.csv")
mods = pd.read_csv(RES / "moderators.csv")
eR2 = pd.read_csv(RES / "effects_dR2.csv")
eRM = pd.read_csv(RES / "effects_lnRR_RMSE.csv")
audit = pd.read_csv(RES / "reporting_audit_summary.csv")
calc = pd.read_csv(RES / "calibration_curve.csv")
calp = pd.read_csv(RES / "calibration_points.csv")
ind = pd.read_csv(RES / "independent_validation_rows.csv")
st = ex.groupby("record_id").agg(year=("year", "first"), country=("country", "first"), task=("task", "first"),
                                  sd=("sampling_design", "first")).reset_index()
st["year"] = pd.to_numeric(st.year, errors="coerce")
st["sd"] = st.sd.where(st.sd.isin(ORDER[:-1]), "unknown")

r2 = ex[ex.metric == "R2"].copy()
for c in ("value_random", "value_spatial"):
    r2[c] = pd.to_numeric(r2[c], errors="coerce")
r2 = r2.dropna(subset=["value_random", "value_spatial"])
r2.loc[r2.value_random > 1.5, ["value_random", "value_spatial"]] /= 100
s = r2.groupby("record_id").agg(rand=("value_random", "median"), spat=("value_spatial", "median"),
                                sd=("sampling_design", "first")).reset_index()
s["sd"] = s.sd.where(s.sd.isin(ORDER[:-1]), "unknown")
GORD = ["clustered", "regular_grid", "unknown", "probability_random"]
fig = plt.figure(figsize=(180 * MM, 92 * MM))
gs = fig.add_gridspec(1, 2, width_ratios=[2.6, 1], wspace=0.22)
ax = fig.add_subplot(gs[0])
x0, ticks = 0, []
for k in GORD:
    g = s[s.sd == k].sort_values("rand").reset_index(drop=True)
    xs = x0 + np.arange(len(g))
    ax.vlines(xs, g.spat, g.rand, color=DESIGN[k], lw=0.9, alpha=0.85)
    ax.scatter(xs, g.rand, s=6, color="black", zorder=3, lw=0)
    ax.scatter(xs, g.spat, s=9, facecolor="white", edgecolor=DESIGN[k], lw=0.7, zorder=3)
    d = (g.rand - g.spat)
    ax.text(x0 + len(g) / 2, 1.08 + (0.17 if k in ("unknown",) else 0), f"{DLAB[k]} ({len(g)})\ndrop {d.median():.2f}", ha="center", va="bottom",
            fontsize=6.1, color=DESIGN[k], fontweight="bold", linespacing=1.1)
    ax.axvspan(x0 - 0.6, x0 + len(g) - 0.4, color=DESIGN[k], alpha=0.05, lw=0, zorder=0)
    x0 += len(g) + 6
ax.axhline(0, color="#999", lw=0.4, ls=":")
ax.set_xlim(-2, x0 - 2); ax.set_ylim(max(-0.5, s.spat.min() - 0.05), 1.05); ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.set_ylabel("$R^2$ (study median)"); ax.set_xlabel("Studies, ordered by $R^2$ under random CV within each sampling design")
ax.legend(handles=[Line2D([], [], marker="o", ls="", color="black", ms=3, label="Random CV"),
                   Line2D([], [], marker="o", ls="", mfc="white", mec="#555", ms=3.5, label="Spatial CV")],
          frameon=False, loc="lower right", ncol=2)
panel(ax, "a", x=-0.07, y=1.15)
ax = fig.add_subplot(gs[1])
for k in GORD:
    g = s[s.sd == k]
    ax.scatter(g.rand, g.spat, s=10, color=DESIGN[k], alpha=0.8, lw=0.3, edgecolor="white", label=DLAB[k])
ax.plot([-0.5, 1], [-0.5, 1], color="black", lw=0.7, ls="--")
for dlt in (0.2, 0.4):
    ax.plot([-0.5, 1], [-0.5 - dlt, 1 - dlt], color="#BBBBBB", lw=0.5, ls=":")
ax.text(0.55, 0.63, "1:1", fontsize=6, rotation=45)
ax.set_xlim(-0.05, 1.02); ax.set_ylim(max(-0.5, s.spat.min() - 0.05), 1.02); ax.set_aspect("equal", adjustable="box")
ax.set_xlabel("$R^2$ under random CV"); ax.set_ylabel("$R^2$ under spatial CV")
drop = s.rand - s.spat
ax.set_title(f"Spatial lower in {100 * (drop > 0).mean():.0f}% of studies;\nnegative in {int((s.spat < 0).sum())}", fontsize=6.5, loc="left", color="#444")
panel(ax, "b", x=-0.3, y=1.1)
save(fig, "Fig3_dumbbell_R2")

m = mods[mods.moderator.isin(["sampling_h", "model_h", "cv_h", "domain_h"])].copy()
m["level"] = [l.replace(mo, "") for l, mo in zip(m.level, m.moderator)]
pretty = {**DLAB, "RF": "Random forest", "boosting": "Gradient boosting", "neural_net": "Neural network", "SVM": "Support vector machine",
          "other_ML": "Other ML", "block": "Spatial blocks", "cluster": "Clusters", "leave_location_out": "Leave-location-out",
          "buffer_LOO": "Buffered leave-one-out", "other": "Other", "soil": "Soil", "crop": "Crop", "forest_biomass": "Forest/biomass",
          "vegetation_landcover": "Vegetation/land cover", "species": "Species", "hydrology": "Hydrology", "climate_air": "Climate/air",
          "hazards": "Hazards"}
grp = {"sampling_h": "Sampling design", "model_h": "Model family", "cv_h": "Spatial CV type", "domain_h": "Domain"}
GCOL = {"Sampling design": "#D55E00", "Model family": "#0072B2", "Spatial CV type": "#009E73", "Domain": "#7F7F7F"}
m = m[m.k_studies >= 3]
cols = {"dR2": "$R^2$\nrandom minus spatial", "lnRR_RMSE": "RMSE\n% higher under spatial", "dAUC": "AUC\nrandom minus spatial", "dAccuracy": "Accuracy\nrandom minus spatial"}
rows = []
for g in ["sampling_h", "model_h", "cv_h", "domain_h"]:
    sub = m[(m.moderator == g)]
    ordr = sub[sub.effect == "dR2"].sort_values("estimate", ascending=False).level.tolist()
    ordr += [l for l in sub.level.unique() if l not in ordr]
    rows.append(("header", grp[g], None))
    rows += [("row", grp[g], l) for l in ordr]
ny = len(rows)
fig, axes = plt.subplots(1, 4, figsize=(180 * MM, 150 * MM), sharey=True, gridspec_kw={"wspace": 0.08})
for ax, (eff, title) in zip(axes, cols.items()):
    o = overall[overall.effect == eff].iloc[0]
    tf = (lambda v: 100 * (np.exp(v) - 1)) if eff == "lnRR_RMSE" else (lambda v: v)
    for i, (kind, g, l) in enumerate(rows):
        if kind == "row" and i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="#F5F5F5", lw=0, zorder=0)
    ax.axvspan(tf(o.ci_lb), tf(o.ci_ub), color="#DADADA", alpha=0.7, lw=0, zorder=0)
    ax.axvline(tf(o.estimate), color="#888", lw=0.7, zorder=1)
    ax.axvline(0, color="black", lw=0.6, ls="--", zorder=1)
    for i, (kind, g, l) in enumerate(rows):
        if kind == "header":
            if eff == "dR2":
                pval = m[(m.moderator == [k for k, v in grp.items() if v == g][0])].QM_p_heterogeneity_between_levels
            continue
        r = m[(m.effect == eff) & (m.moderator == [k for k, v in grp.items() if v == g][0]) & (m.level == l)]
        if not len(r):
            continue
        r = r.iloc[0]
        ax.plot([tf(r.ci_lb), tf(r.ci_ub)], [i, i], color=GCOL[g], lw=1.2)
        ax.scatter(tf(r.estimate), i, s=7 + 2.2 * np.sqrt(r.k_studies) * 3, color=GCOL[g], edgecolor="white", lw=0.4, zorder=3)
    ax.set_title(title, fontsize=7, fontweight="bold")
    ax.set_ylim(ny - 0.4, -0.8)
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(4))
    for kind, g, l in rows:
        if kind == "header":
            i = rows.index((kind, g, l)); mk = [k for k, v in grp.items() if v == g][0]
            pv = m[(m.effect == eff) & (m.moderator == mk)].QM_p_heterogeneity_between_levels
            if len(pv):
                pv = pv.iloc[0]
                ax.text(0.98, i, "p < 0.001" if pv < 0.001 else f"p = {pv:.2f}", transform=ax.get_yaxis_transform(), ha="right",
                        va="center", fontsize=5.8, color="#333", fontweight="bold" if pv < 0.05 else "normal")
axes[0].set_yticks(range(ny))
axes[0].set_yticklabels([("" if k == "header" else pretty.get(l, l)) for k, g, l in rows])
for i, (k, g, l) in enumerate(rows):
    if k == "header":
        axes[0].text(-0.02, i, g, transform=axes[0].get_yaxis_transform(), ha="right", va="center", fontsize=7, fontweight="bold", color=GCOL[g])
axes[0].tick_params(axis="y", length=0)
for ax in axes[1:]:
    ax.tick_params(axis="y", length=0)
fig.text(0.5, 0.045, "Subgroup estimate (positive = random CV more favourable); grey band: pooled estimate and 95% CI; point size proportional to the number of studies",
         ha="center", fontsize=6.3, color="#444")
save(fig, "Fig5_moderators")
