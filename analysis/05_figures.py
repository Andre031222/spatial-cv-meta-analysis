"""Publication figures, redesigned (matplotlib + seaborn), 600 dpi PNG/TIFF + vector PDF.

Run after 01_meta_analysis.R and 04_additional_analyses.R:
    .venv/bin/python analysis/05_figures.py
"""
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

# ---- style ------------------------------------------------------------------------------------
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


# ---- data ---------------------------------------------------------------------------------------
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

# ======================== Fig. 2 — evidence map: where, when and how well reported ================
world = gpd.read_file(f"zip://{ROOT}/data_external/naturalearth/ne_110m_admin_0_countries.zip")
names = {}
for _, r in world.iterrows():
    for k in ("NAME", "NAME_LONG", "ADMIN", "NAME_EN"):
        if isinstance(r.get(k), str):
            names[r[k].lower()] = r["ADMIN"]
alias = {"usa": "United States of America", "us": "United States of America", "united states": "United States of America",
         "conus": "United States of America", "uk": "United Kingdom", "england": "United Kingdom", "scotland": "United Kingdom",
         "czech republic": "Czechia", "south korea": "South Korea", "korea": "South Korea", "russia": "Russia",
         "tanzania": "United Republic of Tanzania", "ivory coast": "Ivory Coast", "côte d'ivoire": "Ivory Coast",
         "dr congo": "Democratic Republic of the Congo", "drc": "Democratic Republic of the Congo",
         "republic of the congo": "Republic of the Congo", "hong kong": "China", "taiwan": "Taiwan", "iran": "Iran",
         "vietnam": "Vietnam", "laos": "Laos", "the netherlands": "Netherlands", "brasil": "Brazil", "méxico": "Mexico"}
scope = {"global": 0, "multi": 0}


def countries_of(s):
    if not isinstance(s, str):
        return []
    s0 = re.sub(r"\(.*?\)", "", s).lower()
    if any(w in s0 for w in ("global", "world", "worldwide", "ocean", "continental", "europe-wide", "pan-")):
        scope["global"] += 1
        return []
    found = []
    for tok in re.split(r"[;,/&]| and ", s0):
        t = tok.strip(" .-")
        hit = alias.get(t) or names.get(t)
        if not hit:
            hit = next((v for k, v in {**names, **alias}.items() if len(k) > 3 and re.search(rf"\b{re.escape(k)}\b", t)), None)
        if hit and hit not in found:
            found.append(hit)
    if len(found) > 1:
        scope["multi"] += 1
    return found


cnt = pd.Series([c for s in st.country for c in countries_of(s)]).value_counts()
world["studies"] = world.ADMIN.map(cnt).fillna(0)

fig = plt.figure(figsize=(180 * MM, 118 * MM))
gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], width_ratios=[1.25, 1], hspace=0.32, wspace=0.62)
ax = fig.add_subplot(gs[0, :])
cmap = sns.color_palette("rocket_r", as_cmap=True)
world[world.studies == 0].plot(ax=ax, color="#EEEEEE", edgecolor="white", linewidth=0.25)
bins = [0.5, 1.5, 3.5, 7.5, 15.5, 1e6]
world["bin"] = pd.cut(world.studies, bins, labels=["1", "2–3", "4–7", "8–15", ">15"])
pal = sns.color_palette("rocket_r", 6)[1:]
for b, col in zip(world["bin"].cat.categories, pal):
    world[world.bin == b].plot(ax=ax, color=col, edgecolor="white", linewidth=0.25)
ax.set_axis_off(); ax.set_xlim(-170, 180); ax.set_ylim(-58, 84)
ax.legend(handles=[mpl.patches.Patch(color=c, label=l) for c, l in zip(pal, world["bin"].cat.categories)],
          title="Studies per country", loc="lower left", frameon=False, ncol=1, title_fontsize=6.5)
ax.text(0.99, 0.02, f"+ {scope['global']} global/continental studies", transform=ax.transAxes, ha="right", fontsize=6.5, color="#444")
panel(ax, "a", x=0.0, y=0.98)

ax = fig.add_subplot(gs[1, 0])
yr = st.dropna(subset=["year"]).assign(year=lambda d: d.year.clip(upper=2026).astype(int))
tab = yr.pivot_table(index="year", columns="sd", values="record_id", aggfunc="count").reindex(columns=ORDER).fillna(0)
tab = tab.reindex(range(int(tab.index.min()), 2027), fill_value=0)
bottom = np.zeros(len(tab))
for k in ORDER:
    ax.bar(tab.index, tab[k], bottom=bottom, color=DESIGN[k], width=0.8, label=DLAB[k], linewidth=0)
    bottom += tab[k].values
ax.set_xlabel("Publication year"); ax.set_ylabel("Included studies")
ax.legend(frameon=False, loc="upper left", title="Sampling design", title_fontsize=6.5)
ax.set_xticks(tab.index[::2])
panel(ax, "b")

ax = fig.add_subplot(gs[1, 1])
lab = {"sampling_reported": "Sampling design", "open_data": "Open data", "open_code": "Open code",
       "block_size_reported": "Block/buffer size", "sd_reported": "Uncertainty (SD) of CV",
       "independent_validation": "Independent test set", "range_reported": "Autocorrelation range"}
a = audit.assign(lbl=audit.item.map(lab)).sort_values("share")
ax.barh(a.lbl, a.share * 100, color="#4D4D4D", height=0.6)
for y, v in enumerate(a.share * 100):
    ax.text(v + 1.5, y, f"{v:.0f}%", va="center", fontsize=6.5)
ax.set_xlim(0, 100); ax.set_xlabel("Studies reporting (%)")
panel(ax, "c", x=-0.55)
save(fig, "Fig2_evidence_map")

# ======================== Fig. 3 — dumbbell: every study, random -> spatial R2 =====================
r2 = ex[ex.metric == "R2"].copy()
for c in ("value_random", "value_spatial"):
    r2[c] = pd.to_numeric(r2[c], errors="coerce")
r2 = r2.dropna(subset=["value_random", "value_spatial"])
r2.loc[r2.value_random > 1.5, ["value_random", "value_spatial"]] /= 100
s = r2.groupby("record_id").agg(rand=("value_random", "median"), spat=("value_spatial", "median"),
                                sd=("sampling_design", "first")).reset_index()
s["sd"] = s.sd.where(s.sd.isin(ORDER[:-1]), "unknown")
s = s.sort_values("rand").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(180 * MM, 82 * MM))
for i, r in s.iterrows():
    ax.plot([i, i], [r.spat, r.rand], color=DESIGN[r.sd], lw=0.9, alpha=0.8, solid_capstyle="round")
ax.scatter(s.index, s.rand, s=6, color="black", zorder=3, label="Random CV")
ax.scatter(s.index, s.spat, s=9, facecolor="white", edgecolor=[DESIGN[k] for k in s.sd], lw=0.7, zorder=3, label="Spatial CV")
ax.axhline(0, color="#999", lw=0.4, ls=":")
ax.set_xlim(-1, len(s)); ax.set_ylim(max(-1.05, s.spat.min() - 0.05), 1.03)
ax.set_xticks([]); ax.set_xlabel(f"Studies ordered by random-CV $R^2$ (n = {len(s)})"); ax.set_ylabel("$R^2$ (study median)")
h = [Line2D([], [], marker="o", ls="", color="black", ms=3, label="Random CV"),
     Line2D([], [], marker="o", ls="", mfc="white", mec="black", ms=3.5, label="Spatial CV")]
h += [Line2D([], [], color=DESIGN[k], lw=1.5, label=DLAB[k]) for k in ORDER]
ax.legend(handles=h, frameon=False, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.2))
drop = (s.rand - s.spat)
ax.text(0.01, 0.04, f"Median drop {drop.median():.2f}; spatial < random in {100*(drop > 0).mean():.0f}% of studies;"
        f" spatial $R^2$ < 0 in {int((s.spat < 0).sum())} studies", transform=ax.transAxes, fontsize=6.5)
save(fig, "Fig3_dumbbell_R2")

# ======================== Fig. 4 — raincloud by sampling design + subgroup estimates ===============
def rain(ax, e, nm, xlabel, clip):
    e = e.copy(); e["sd"] = pd.Categorical(e.sampling_h, ORDER)
    e = e[(e.yi > clip[0]) & (e.yi < clip[1])]
    m = mods[(mods.effect == nm) & (mods.moderator == "sampling_h")].copy()
    m["lvl"] = m.level.str.replace("sampling_h", "", regex=False)
    for j, k in enumerate(ORDER):
        v = e.loc[e.sd == k, "yi"].values
        if len(v) < 3:
            continue
        kde = sns.kdeplot(x=v, ax=ax, bw_adjust=0.8, clip=clip).get_lines()[-1]
        xs, ys = kde.get_data(); kde.remove()
        ys = ys / ys.max() * 0.38
        ax.fill_between(xs, j + 0.05, j + 0.05 + ys, color=DESIGN[k], alpha=0.55, lw=0)
        jit = np.random.default_rng(1).uniform(-0.28, -0.06, len(v))
        ax.scatter(v, j + jit, s=1.6, color=DESIGN[k], alpha=0.55, lw=0)
        r = m[m.lvl == k]
        if len(r):
            ax.errorbar(r.estimate, j - 0.02, xerr=[[r.estimate.iloc[0] - r.ci_lb.iloc[0]], [r.ci_ub.iloc[0] - r.estimate.iloc[0]]],
                        fmt="o", color="black", ms=3.2, mfc="white", mew=0.8, elinewidth=1.1, capsize=0)
            ax.text(clip[1], j + 0.18, f"{int(r.k_studies.iloc[0])} studies", ha="right", fontsize=6, color="#444")
    ax.axvline(0, color="#777", lw=0.5, ls="--")
    est = overall.loc[overall.effect == nm, "estimate"].iloc[0]
    ax.axvline(est, color="black", lw=0.6)
    ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([DLAB[k] for k in ORDER])
    ax.set_xlabel(xlabel); ax.set_ylabel(""); ax.set_ylim(-0.45, len(ORDER) - 0.4); ax.set_xlim(clip)
    p = m.QM_p_heterogeneity_between_levels.iloc[0]
    ax.set_title(f"Between-design difference: {'p < 0.001' if p < 0.001 else f'p = {p:.3f}'}", loc="left", fontsize=7)


fig, axs = plt.subplots(1, 2, figsize=(180 * MM, 78 * MM), sharey=True)
rain(axs[0], eR2, "dR2", "$\\Delta R^2$ (random − spatial)", (-0.6, 1.2)); panel(axs[0], "a", x=-0.22)
rain(axs[1], eRM, "lnRR_RMSE", "ln(RMSE$_{spatial}$ / RMSE$_{random}$)", (-0.6, 1.3)); panel(axs[1], "b", x=-0.05)
save(fig, "Fig4_raincloud_sampling")

# ======================== Fig. 5 — calibration: what spatial R2 to expect =========================
fig, axs = plt.subplots(1, 2, figsize=(180 * MM, 80 * MM), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axs[0]
for k in ("clustered", "regular_grid", "probability_random"):
    p = calp[calp.sampling_h == k]
    ax.scatter(p.vr, p.vs, s=4, color=DESIGN[k], alpha=0.35, lw=0)
    c = calc[calc.sampling_h == k]
    ax.plot(c.vr, c.vr - c.gap, color=DESIGN[k], lw=1.4, label=DLAB[k])
    ax.fill_between(c.vr, c.vr - c.gap_hi, c.vr - c.gap_lo, color=DESIGN[k], alpha=0.18, lw=0)
ax.plot([0, 1], [0, 1], ls="--", color="#666", lw=0.6)
ax.text(0.93, 0.99, "1:1", fontsize=6, color="#666", va="top")
ax.set_xlim(0.3, 1); ax.set_ylim(-0.2, 1); ax.set_aspect("equal")
ax.set_xlabel("$R^2$ under random CV"); ax.set_ylabel("Expected $R^2$ under spatial CV")
ax.legend(frameon=False, loc="lower right", title="Sampling design", title_fontsize=6.5)
panel(ax, "a")
ax = axs[1]
tbl = calc[calc.vr.round(2).isin([0.6, 0.7, 0.8, 0.9]) & calc.sampling_h.isin(["clustered", "regular_grid", "probability_random"])].copy()
tbl["vr"] = tbl.vr.round(2)
piv = tbl.pivot(index="sampling_h", columns="vr", values="expected_spatial_r2").reindex(["clustered", "regular_grid", "probability_random"])
sns.heatmap(piv, annot=True, fmt=".2f", cmap="mako", vmin=0.2, vmax=0.95, cbar_kws={"label": "Expected spatial-CV $R^2$", "shrink": 0.7},
            linewidths=0.6, linecolor="white", ax=ax, annot_kws={"fontsize": 7})
ax.set_yticklabels([DLAB[k] for k in piv.index], rotation=0); ax.set_ylabel("")
ax.set_xlabel("Reported random-CV $R^2$")
panel(ax, "b", x=-0.45)
save(fig, "Fig7_calibration_R2")

# ======================== Fig. 6 — which estimate is closer to an independent test? ==============
d = ind[ind.metric.isin(["R2", "accuracy", "AUC"])].copy()
d["type"] = d.ind_type.map({"probability_sample": "Probability sample", "temporal": "Later period",
                             "other_region": "Other region", "other": "Other hold-out"}).fillna("Other hold-out")
long = pd.concat([d.assign(scheme="Random CV", opt=d.opt_random), d.assign(scheme="Spatial CV", opt=d.opt_spatial)])
order_t = ["Probability sample", "Other hold-out", "Later period", "Other region"]
order_t = [t for t in order_t if t in set(d.type)]
fig, axs = plt.subplots(1, 2, figsize=(180 * MM, 76 * MM), gridspec_kw={"width_ratios": [1.5, 1]})
ax = axs[0]
sns.stripplot(data=long, x="opt", y="type", hue="scheme", order=order_t, dodge=True, size=2.6, alpha=0.6, jitter=0.18,
              palette={"Random CV": "#000000", "Spatial CV": "#CC79A7"}, ax=ax, legend=False)
sns.pointplot(data=long, x="opt", y="type", hue="scheme", order=order_t, dodge=0.42, estimator=np.median, errorbar=None,
              markers="D", markersize=4, linestyles="none", palette={"Random CV": "#000000", "Spatial CV": "#CC79A7"}, ax=ax)
ax.axvline(0, color="#555", lw=0.6, ls="--")
ax.set_xlabel("CV estimate − independent estimate\n($R^2$, AUC or accuracy; > 0 = optimistic)"); ax.set_ylabel("")
ax.legend(frameon=False, loc="lower right", title=None)
for i, t in enumerate(order_t):
    sub = d[d.type == t]
    ax.text(1.0, 1 - (i + 0.15) / len(order_t), f"{sub.record_id.nunique()} studies", transform=ax.transAxes, ha="right", fontsize=6, color="#444")
panel(ax, "a", x=-0.3)
ax = axs[1]
allm = ind.copy()
allm["closer"] = np.where(allm.abs_gap > 0, "Spatial CV closer", "Random CV closer")
allm["type"] = allm.ind_type.map({"probability_sample": "Probability sample", "temporal": "Later period",
                                  "other_region": "Other region", "other": "Other hold-out"}).fillna("Other hold-out")
sh = allm.groupby("type").closer.apply(lambda v: (v == "Spatial CV closer").mean() * 100).reindex(order_t)
ax.barh(sh.index, sh.values, color="#CC79A7", height=0.55)
ax.barh(sh.index, 100 - sh.values, left=sh.values, color="#000000", height=0.55)
for i, v in enumerate(sh.values):
    ax.text(v / 2, i, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=6.5)
ax.axvline(50, color="white", lw=0.6)
ax.set_xlim(0, 100); ax.invert_yaxis(); ax.set_xlabel("Effect sizes where each CV is closer (%)")
ax.set_yticklabels([])
ax.legend(handles=[mpl.patches.Patch(color="#CC79A7", label="Spatial CV closer"), mpl.patches.Patch(color="#000000", label="Random CV closer")],
          frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.42), ncol=2)
panel(ax, "b", x=-0.05)
save(fig, "Fig6_independent_validation")

# ======================== Fig. 7 — moderator heatmap across metrics ===============================
m = mods[mods.moderator.isin(["sampling_h", "model_h", "cv_h", "domain_h"])].copy()
m["level"] = [l.replace(mo, "") for l, mo in zip(m.level, m.moderator)]
pretty = {**DLAB, "RF": "Random forest", "boosting": "Boosting", "neural_net": "Neural network", "SVM": "SVM", "other_ML": "Other ML",
          "block": "Spatial blocks", "cluster": "Clusters", "leave_location_out": "Leave-location-out", "buffer_LOO": "Buffered LOO",
          "other": "Other", "soil": "Soil", "crop": "Crop", "forest_biomass": "Forest/biomass", "vegetation_landcover": "Vegetation/land cover",
          "species": "Species", "hydrology": "Hydrology", "climate_air": "Climate/air", "hazards": "Hazards"}
grp = {"sampling_h": "Sampling design", "model_h": "Model family", "cv_h": "Spatial CV type", "domain_h": "Domain"}
m = m[m.k_studies >= 3]
m["row"] = m.moderator.map(grp) + ": " + m.level.map(pretty).fillna(m.level)
# express everything as % of the overall effect of that metric, to compare across metrics
ov = overall.set_index("effect").estimate
m["rel"] = m.apply(lambda r: r.estimate / ov[r.effect] * 100, axis=1)
m["txt"] = m.apply(lambda r: f"{r.estimate:.2f}\n({int(r.k_studies)})", axis=1)
cols = {"dR2": "$\\Delta R^2$", "lnRR_RMSE": "lnRR RMSE", "dAUC": "$\\Delta$AUC", "dAccuracy": "$\\Delta$Accuracy"}
groups = [g for g in grp.values() if (m.row.str.startswith(g)).any()]
sizes = [int(m.row.str.startswith(g).sum()) for g in groups]
fig, axes = plt.subplots(len(groups), 1, figsize=(120 * MM, 160 * MM), gridspec_kw={"height_ratios": sizes, "hspace": 0.12}, sharex=True)
for ax, g in zip(axes, groups):
    sub = m[m.row.str.startswith(g)]
    order_r = sub[sub.effect == "dR2"].sort_values("estimate", ascending=False).row.tolist()
    order_r += [r for r in sub.row.unique() if r not in order_r]
    H = sub.pivot(index="row", columns="effect", values="rel").reindex(index=order_r, columns=list(cols))
    T = sub.pivot(index="row", columns="effect", values="txt").reindex(index=order_r, columns=list(cols))
    sns.heatmap(H, annot=T, fmt="", cmap="RdBu_r", center=100, vmin=0, vmax=200, linewidths=0.6, linecolor="white",
                cbar=False, annot_kws={"fontsize": 5.5}, ax=ax)
    ax.set_yticklabels([r.split(": ", 1)[1] for r in order_r], rotation=0); ax.set_ylabel(g, fontweight="bold", fontsize=7)
    ax.set_xlabel(""); ax.tick_params(axis="x", length=0)
axes[-1].set_xticklabels([cols[c] for c in cols], rotation=0)
cax = fig.add_axes([0.93, 0.35, 0.025, 0.3])
fig.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.TwoSlopeNorm(vmin=0, vcenter=100, vmax=200), cmap="RdBu_r"), cax=cax,
             label="Subgroup effect as % of overall effect")
save(fig, "Fig5_moderator_heatmap")
