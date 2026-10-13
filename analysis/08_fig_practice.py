"""Fig. 9 — validation practice in the included studies and study-level moderators (600 dpi).
Run after 07_study_level_moderators.R:  .venv/bin/python analysis/08_fig_practice.py
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
mpl.rcParams.update({"font.family": "Helvetica", "font.size": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 0.5, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42, "savefig.dpi": 600})
MM = 1 / 25.4
sl = pd.read_csv(ROOT / "extraction/study_level.csv", dtype=str)
mods = pd.read_csv(ROOT / "analysis/results/study_level_moderators.csv")
num = lambda s: pd.to_numeric(s, errors="coerce")


def panel(ax, l, x=-0.3, y=1.03):
    ax.text(x, y, l, transform=ax.transAxes, fontsize=9, fontweight="bold")


# random-CV scheme detail
def rscheme(r):
    s, k, tr = r.random_cv_scheme, num(pd.Series([r.random_k]))[0], num(pd.Series([r.random_train_pct]))[0]
    if s in ("kfold", "nested_kfold"):
        return "10-fold" if k == 10 else "5-fold" if k == 5 else "Other k-fold"
    if s == "repeated_kfold":
        return "Repeated k-fold"
    if s == "holdout_split":
        return f"{int(tr)}/{int(100 - tr)} split" if tr in (70, 75, 80) else "Other split"
    if s in ("LOO", "OOB"):
        return "LOO / OOB"
    return "Other"


sl["rs"] = sl.apply(rscheme, axis=1)
order_rs = ["10-fold", "5-fold", "Other k-fold", "Repeated k-fold", "80/20 split", "70/30 split", "75/25 split", "Other split", "LOO / OOB", "Other"]
col_rs = {"10-fold": "#0072B2", "5-fold": "#56B4E9", "Other k-fold": "#9ECAE1", "Repeated k-fold": "#3A6EA5",
          "80/20 split": "#D55E00", "70/30 split": "#E69F00", "75/25 split": "#F0C27B", "Other split": "#F6DDB4",
          "LOO / OOB": "#CC79A7", "Other": "#BBBBBB"}
src = {"in_situ_samples": "Field samples", "remote_sensing_labels": "Remote-sensing labels", "monitoring_stations": "Monitoring stations",
       "survey_inventory": "Surveys / inventories", "gridded_product": "Gridded products", "compiled_database": "Compiled databases",
       "occurrence_records": "Occurrence records", "mixed": "Mixed", "simulated": "Simulated"}
sl["src"] = sl.data_source.map(src)

fig = plt.figure(figsize=(180 * MM, 178 * MM))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.6], hspace=0.35, wspace=0.75)

# (a) random-CV schemes
ax = fig.add_subplot(gs[0, 0])
c = sl.rs.value_counts().reindex(order_rs).fillna(0)
ax.barh(c.index, c.values, color=[col_rs[k] for k in c.index], height=0.65)
for y, v in enumerate(c.values):
    ax.text(v + 1, y, f"{int(v)} ({100 * v / len(sl):.0f}%)", va="center", fontsize=6.2)
ax.invert_yaxis(); ax.set_xlabel("Studies"); ax.set_xlim(0, c.max() * 1.35)
ax.set_title("Random CV used as baseline", loc="left", fontsize=7.5, fontweight="bold")
panel(ax, "a", x=-0.38)

# (b) data source by task
ax = fig.add_subplot(gs[0, 1])
t = sl.assign(task=sl.task.replace({"both": "regression"})).pivot_table(index="src", columns="task", values="record_id", aggfunc="count").fillna(0)
t = t.loc[t.sum(axis=1).sort_values().index]
ax.barh(t.index, t.get("regression", 0), color="#0072B2", height=0.65, label="Regression")
ax.barh(t.index, t.get("classification", 0), left=t.get("regression", 0), color="#E69F00", height=0.65, label="Classification")
ax.set_xlabel("Studies"); ax.legend(frameon=False, loc="lower right")
ax.set_title("Response data source and task", loc="left", fontsize=7.5, fontweight="bold")
panel(ax, "b", x=-0.62)

# (c) study-level moderators of the R2 gap
ax = fig.add_subplot(gs[1, :])
keep = {"Block size justified by": {"autocorrelation_range": "Autocorrelation range", "expert_choice": "Expert choice", "not_justified": "Not justified"},
        "Random-CV scheme": {"LOO/OOB": "LOO / OOB", "Hold-out split": "Hold-out split", "k-fold": "k-fold"},
        "Number of observations": {"<200": "< 200", "200-1k": "200–1,000", "1k-5k": "1,000–5,000", "5k-50k": "5,000–50,000", ">50k": "> 50,000"},
        "Data source": {k: k for k in ["Compiled databases", "Surveys/inventories", "Field samples", "Monitoring stations",
                                       "Remote-sensing labels", "Gridded products"]}}
gcol = {"Block size justified by": "#009E73", "Random-CV scheme": "#CC79A7", "Number of observations": "#0072B2", "Data source": "#7F7F7F"}
rows = []
for g, lv in keep.items():
    rows.append(("h", g, None))
    for l in lv:
        rows.append(("r", g, l))
m = mods[mods.effect == "dR2"]
for i, (kind, g, l) in enumerate(rows):
    if kind == "h":
        p = m[m.moderator == g].p_between
        ptxt = "" if not len(p) else ("p < 0.001" if p.iloc[0] < 0.001 else f"p = {p.iloc[0]:.3f}")
        ax.text(-0.36, i, f"{g}  ({ptxt})", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=7,
                fontweight="bold", color=gcol[g])
        continue
    r = m[(m.moderator == g) & (m.level == l)]
    if not len(r):
        continue
    r = r.iloc[0]
    ax.plot([r.ci_lb, r.ci_ub], [i, i], color=gcol[g], lw=1.3)
    ax.scatter(r.estimate, i, s=10 + 3 * r.k_studies ** 0.5 * 3, color=gcol[g], edgecolor="white", lw=0.4, zorder=3)
    ax.text(0.62, i, f"{r.estimate:.2f}  ({int(r.k_studies)} studies)", va="center", fontsize=6.2, color="#333")
ax.axvline(0, color="black", lw=0.6, ls="--")
ax.axvline(0.209, color="#999", lw=0.7); ax.axvspan(0.168, 0.250, color="#EEE", zorder=0)
ax.set_yticks(range(len(rows))); ax.set_yticklabels(["" if k == "h" else keep[g][l] for k, g, l in rows])
ax.tick_params(axis="y", length=0); ax.set_ylim(len(rows) - 0.4, -0.7); ax.set_xlim(-0.15, 0.78)
ax.set_xlabel("$\\Delta R^2$ (random − spatial CV); grey band: pooled estimate and 95% CI")
panel(ax, "c", x=-0.38, y=1.01)
for ext, kw in (("png", {}), ("pdf", {}), ("tiff", {"pil_kwargs": {"compression": "tiff_lzw"}})):
    fig.savefig(OUT / f"Fig9_validation_practice.{ext}", bbox_inches="tight", dpi=600, facecolor="white", **kw)
print("saved Fig9_validation_practice")
