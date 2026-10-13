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

# ======================== Fig. 7 — calibration: what spatial R2 to expect (small multiples) =======
SHOW = ["clustered", "regular_grid", "probability_random"]
fig = plt.figure(figsize=(180 * MM, 112 * MM))
gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1], hspace=0.62, wspace=0.12)
for j, k in enumerate(SHOW):
    ax = fig.add_subplot(gs[0, j])
    p = calp[calp.sampling_h == k]
    c = calc[calc.sampling_h == k]
    ax.fill_between(c.vr, c.vr - c.gap_pi_hi, c.vr - c.gap_pi_lo, color=DESIGN[k], alpha=0.10, lw=0, label="95% prediction interval")
    ax.fill_between(c.vr, c.vr - c.gap_hi, c.vr - c.gap_lo, color=DESIGN[k], alpha=0.32, lw=0, label="95% confidence interval")
    ax.scatter(p.vr, p.vs, s=5, color=DESIGN[k], alpha=0.55, lw=0)
    ax.plot(c.vr, c.vr - c.gap, color=DESIGN[k], lw=1.6, label="Expected spatial-CV $R^2$")
    ax.plot([0, 1], [0, 1], ls="--", color="#555", lw=0.6, label="1:1 (no difference)")
    ax.set_xlim(0.3, 1); ax.set_ylim(-0.4, 1.02)
    ax.set_title(f"{DLAB[k]}  ({p.record_id.nunique()} studies)", loc="left", fontsize=7.5, color=DESIGN[k], fontweight="bold")
    ax.set_xlabel("$R^2$ under random CV")
    if j == 0:
        ax.set_ylabel("$R^2$ under spatial CV"); panel(ax, "a", x=-0.28)
    else:
        ax.set_yticklabels([])
h, l = ax.get_legend_handles_labels()
fig.legend([h[i] for i in (2, 1, 0, 3)], [l[i] for i in (2, 1, 0, 3)], frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 0.465), fontsize=6.5)
ax = fig.add_subplot(gs[1, :])
pts = [0.6, 0.7, 0.8, 0.9]
off = {"clustered": -0.018, "regular_grid": 0.0, "probability_random": 0.018}
for k in SHOW:
    c = calc[calc.sampling_h == k].copy(); c["vr"] = c.vr.round(2); c = c[c.vr.isin(pts)]
    ax.errorbar(c.vr + off[k], c.vr - c.gap, yerr=[c.gap_hi - c.gap, c.gap - c.gap_lo], fmt="o", color=DESIGN[k],
                ms=4, mfc="white", mew=1.1, elinewidth=1.1, capsize=0, label=DLAB[k])
ax.plot(pts, pts, "k_", ms=14, mew=1.2, label="Reported random-CV $R^2$")
for x0 in pts:
    ax.axvline(x0, color="#EEE", lw=6, zorder=0)
ax.set_xticks(pts); ax.set_xlim(0.55, 0.95); ax.set_ylim(0.3, 0.95)
ax.set_xlabel("Reported $R^2$ under random CV"); ax.set_ylabel("Expected $R^2$ under spatial CV")
ax.legend(frameon=False, loc="upper left", ncol=4, fontsize=6.5)
panel(ax, "b", x=-0.08)
save(fig, "Fig7_calibration_R2")

# ======================== Fig. 6 — which estimate is closer to an independent test? ==============
TYPE = {"probability_sample": "Probability sample", "other": "Other hold-out", "temporal": "Later period", "other_region": "Other region"}
d = ind[ind.metric.isin(["R2", "accuracy", "AUC"])].copy()
d["type"] = d.ind_type.map(TYPE).fillna("Other hold-out")
sd_ = d.groupby(["type", "record_id"]).agg(r=("opt_random", "median"), s=("opt_spatial", "median"), k=("opt_random", "size")).reset_index()
order_t = [t for t in TYPE.values() if t in set(sd_.type)]
sd_["type"] = pd.Categorical(sd_.type, order_t)
sd_ = sd_.sort_values(["type", "r"]).reset_index(drop=True)
RC, SC = "#1A1A1A", "#CC79A7"
fig = plt.figure(figsize=(180 * MM, 92 * MM))
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], wspace=0.5)
ax = fig.add_subplot(gs[0, 0])
ypos, y, ticks, groups = [], 0, [], []
for t in order_t:
    sub = sd_[sd_.type == t]
    ys = np.arange(y, y + len(sub)); ypos.extend(ys); groups.append((t, y, y + len(sub) - 1)); y += len(sub) + 1.2
ax.axvline(0, color="#555", lw=0.7, ls="--", zorder=0)
for yy, (_, r) in zip(ypos, sd_.iterrows()):
    closer_spatial = abs(r.s) < abs(r.r)
    ax.plot([r.r, r.s], [yy, yy], color=SC if closer_spatial else RC, lw=1.0, alpha=0.6)
    ax.scatter(r.r, yy, s=14, color=RC, zorder=3)
    ax.scatter(r.s, yy, s=16, facecolor="white", edgecolor=SC, lw=1.1, zorder=3)
for t, y0, y1 in groups:
    ax.axhspan(y0 - 0.6, y1 + 0.6, color="#F4F4F4" if order_t.index(t) % 2 == 0 else "white", zorder=-1, lw=0)
    ax.text(ax.get_xlim()[0] if False else -0.36, (y0 + y1) / 2, t, ha="right", va="center", fontsize=6.8, fontweight="bold")
ax.set_xlim(-0.33, 0.62); ax.set_ylim(max(ypos) + 1, -1); ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xlabel("Deviation from the independent test\n($R^2$, AUC or accuracy; > 0 = optimistic, < 0 = pessimistic)")
ax.text(0.6, -0.6, "optimistic", fontsize=6.3, color="#555", ha="right"); ax.text(-0.31, -0.6, "pessimistic", fontsize=6.3, color="#555")
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=RC, ms=4, label="Random CV"),
                   Line2D([], [], marker="o", ls="", mfc="white", mec=SC, mew=1.1, ms=4.5, label="Spatial CV")],
          frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.93), fontsize=6.5)
panel(ax, "a", x=-0.33)
ax = fig.add_subplot(gs[0, 1])
allm = ind.copy(); allm["type"] = allm.ind_type.map(TYPE).fillna("Other hold-out")
sh = allm.groupby("type").agg(sp=("abs_gap", lambda v: (v > 0).mean() * 100), n=("abs_gap", "size"),
                               st=("record_id", "nunique")).reindex(order_t)
yb = np.arange(len(order_t))
ax.barh(yb, sh.sp, color=SC, height=0.58)
ax.barh(yb, 100 - sh.sp, left=sh.sp, color=RC, height=0.58)
for i, (v, n, st_) in enumerate(zip(sh.sp, sh.n, sh.st)):
    ax.text(2, i, f"{v:.0f}%", va="center", color="white", fontsize=6.5, fontweight="bold")
    ax.text(98, i, f"{100 - v:.0f}%", va="center", ha="right", color="white", fontsize=6.5, fontweight="bold")
    ax.text(50, i + 0.42, f"{st_} studies, {n} comparisons", ha="center", va="center", fontsize=5.8, color="#444")
ax.axvline(50, color="white", lw=0.8)
ax.set_yticks(yb); ax.set_yticklabels(order_t); ax.invert_yaxis(); ax.set_xlim(0, 100)
ax.set_xlabel("Comparisons in which each design\nwas closer to the independent test (%)")
ax.legend(handles=[mpl.patches.Patch(color=SC, label="Spatial CV closer"), mpl.patches.Patch(color=RC, label="Random CV closer")],
          frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.5)
panel(ax, "b", x=-0.42)
save(fig, "Fig6_independent_validation")

# ======================== Fig. 5 — moderators: small-multiple forest plots across metrics ==========
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
cols = {"dR2": "$\\Delta R^2$", "lnRR_RMSE": "lnRR RMSE", "dAUC": "$\\Delta$AUC", "dAccuracy": "$\\Delta$accuracy"}
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
    ax.axvspan(o.ci_lb, o.ci_ub, color="#E8E8E8", lw=0, zorder=0)
    ax.axvline(o.estimate, color="#888", lw=0.7, zorder=1)
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
        ax.plot([r.ci_lb, r.ci_ub], [i, i], color=GCOL[g], lw=1.2)
        ax.scatter(r.estimate, i, s=7 + 2.2 * np.sqrt(r.k_studies) * 3, color=GCOL[g], edgecolor="white", lw=0.4, zorder=3)
    ax.set_title(title, fontsize=8)
    ax.set_ylim(ny - 0.4, -0.8)
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(4))
    # moderator p-value per metric
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
fig.text(0.5, 0.045, "Subgroup estimate (positive = random CV more favourable); grey band: pooled estimate and 95% CI; point size ∝ number of studies",
         ha="center", fontsize=6.3, color="#444")
save(fig, "Fig5_moderators")
