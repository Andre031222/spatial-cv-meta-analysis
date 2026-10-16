from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "analysis/results", ROOT / "figures"
mpl.rcParams.update({"font.family": "Helvetica", "pdf.fonttype": 42, "axes.linewidth": 0.6})
DESIGN = {"clustered": ("#D55E00", "Clustered"), "regular_grid": ("#009E73", "Regular grid"), "probability_random": ("#0072B2", "Probability")}
mods = pd.read_csv(RES / "moderators.csv")
overall = pd.read_csv(RES / "overall_effects.csv").set_index("effect")
summ = pd.read_csv(RES / "independent_validation_summary.csv")
summ = summ[summ.scale == "difference"].set_index("quantity")
m = mods[(mods.effect == "lnRR_RMSE") & (mods.moderator == "sampling_h")].copy()
m["lvl"] = m.level.str.replace("sampling_h", "", regex=False)
pct = lambda v: 100 * (np.exp(v) - 1)

fig = plt.figure(figsize=(13 / 2.54 * 1.6, 5 / 2.54 * 1.6))
gs = fig.add_gridspec(1, 3, width_ratios=[0.8, 1.25, 1.0], wspace=0.5, left=0.02, right=0.98, top=0.78, bottom=0.27)
fig.text(0.5, 0.94, "Random versus spatial cross-validation in machine-learning environmental maps", ha="center", fontsize=11, fontweight="bold")

ax = fig.add_subplot(gs[0]); ax.set_axis_off()
for y, big, small in ((0.86, "266", "studies, 86 countries"), (0.55, "1,102", "paired effect sizes"), (0.24, "25", "studies with an\nindependent test")):
    ax.text(0.05, y, big, fontsize=17, fontweight="bold", color="#333", va="center")
    ax.text(0.05, y - 0.15, small, fontsize=7.5, color="#555", va="center")
ax.set_title("Same model, same data,\nrandom vs spatial CV", fontsize=8, loc="left", color="#333")

ax = fig.add_subplot(gs[1])
for i, (k, (c, lab)) in enumerate(DESIGN.items()):
    r = m[m.lvl == k].iloc[0]
    ax.barh(i, pct(r.estimate), color=c, height=0.62)
    ax.errorbar(pct(r.estimate), i, xerr=[[pct(r.estimate) - pct(r.ci_lb)], [pct(r.ci_ub) - pct(r.estimate)]], color="black", lw=0.8, capsize=2)
    ax.text(pct(r.ci_ub) + 2, i, f"+{pct(r.estimate):.0f}%", va="center", fontsize=8.5, fontweight="bold", color=c)
ax.invert_yaxis(); ax.set_yticks(range(3)); ax.set_yticklabels([v[1] for v in DESIGN.values()], fontsize=7.5); ax.set_xlim(0, 70)
ax.tick_params(axis="y", length=0)
ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
ax.set_xlabel("RMSE higher under spatial CV (%)", fontsize=7.5)
ax.set_title(f"Gap depends on sampling design\n(overall $R^2$ {overall.loc['dR2', 'estimate']:.2f} higher with random CV)", fontsize=8, loc="left", color="#333")

ax = fig.add_subplot(gs[2])
for i, (q, c, lab) in enumerate((("optimism_random", "#1A1A1A", "Random CV"), ("optimism_spatial", "#CC79A7", "Spatial CV"))):
    r = summ.loc[q]
    ax.bar(i, r["mean"], color=c, width=0.55)
    ax.errorbar(i, r["mean"], yerr=[[r["mean"] - r.lo], [r.hi - r["mean"]]], color="black", lw=0.8, capsize=2)
    ax.text(i, r.hi + 0.02, f"{r['mean']:+.2f}", ha="center", fontsize=8.5, fontweight="bold")
ax.axhline(0, color="#555", lw=0.6)
ax.set_xticks([0, 1]); ax.set_xticklabels(["Random CV", "Spatial CV"], fontsize=7.5); ax.tick_params(axis="y", labelsize=7)
ax.set_ylim(-0.08, 0.34); ax.spines[["top", "right"]].set_visible(False)
ax.set_ylabel("Optimism vs independent test", fontsize=7.5)
ax.set_title("Spatial CV is closer to\nindependent accuracy", fontsize=8, loc="left", color="#333")
fig.text(0.5, 0.03, "Use spatial CV unless the data are a probability sample of the mapped area; report the sampling design and block size.",
         ha="center", fontsize=7.8, color="white", fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.4", fc="#333333", ec="none"))
for ext, kw in (("png", {}), ("pdf", {}), ("tiff", {"pil_kwargs": {"compression": "tiff_lzw"}})):
    fig.savefig(OUT / f"Graphical_abstract.{ext}", dpi=600, facecolor="white", **kw)
print("saved Graphical_abstract")
