import json
import unicodedata
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript/supplementary"
OUT.mkdir(parents=True, exist_ok=True)

def tex(x):
    s = "" if pd.isna(x) else str(x)
    s = unicodedata.normalize("NFKC", s).replace("\u2009", " ").replace("\u202f", " ").replace("\u2013", "--").replace("\u2014", "---")
    s = "".join(c if ord(c) < 256 else ("'" if c in "\u2018\u2019" else '"' if c in "\u201c\u201d" else "") for c in s)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s

prisma = [
    ("Title", "1", "Identify the report as a systematic review.", "Title"),
    ("Abstract", "2", "See the PRISMA 2020 for Abstracts checklist (Table S2).", "Abstract"),
    ("Introduction", "3", "Rationale for the review in the context of existing knowledge.", "Section 1, paragraphs 1--5"),
    ("", "4", "Explicit statement of the objectives or questions.", "Section 1, last paragraph (questions i--iii, H1--H4)"),
    ("Methods", "5", "Inclusion and exclusion criteria and how studies were grouped for the syntheses.", "Section 2.2; groups by metric in 2.6"),
    ("", "6", "Information sources and the date each was last searched.", "Section 2.3; Table 1; Table S3"),
    ("", "7", "Full search strategies for all databases, including filters and limits.", "Table 1; Section S2"),
    ("", "8", "Methods used to decide whether a study met the inclusion criteria.", "Section 2.4"),
    ("", "9", "Methods used to collect data from reports.", "Section 2.5; Section S4"),
    ("", "10a", "Outcomes for which data were sought.", "Sections 2.5--2.6"),
    ("", "10b", "Other variables for which data were sought.", "Section 2.5; Section S4"),
    ("", "11", "Methods used to assess risk of bias in the included studies.", "Section 2.10; Section S5"),
    ("", "12", "Effect measures used in the synthesis.", "Section 2.6"),
    ("", "13a", "Processes used to decide which studies were eligible for each synthesis.", "Sections 2.5--2.6"),
    ("", "13b", "Methods required to prepare the data for synthesis.", "Section 2.6 (rescaling, variance approximation)"),
    ("", "13c", "Methods used to tabulate or display results.", "Sections 2.7--2.9; Figs. 3--7"),
    ("", "13d", "Methods used to synthesize results and rationale.", "Section 2.7"),
    ("", "13e", "Methods used to explore heterogeneity.", "Section 2.7 (meta-regression)"),
    ("", "13f", "Sensitivity analyses.", "Section 2.10; Tables S6 and S7"),
    ("", "14", "Methods used to assess risk of bias due to missing results (reporting biases).", "Section 2.10"),
    ("", "15", "Methods used to assess certainty (or confidence) in the body of evidence.", "Sections 2.10 and 4.6 (GRADE, adapted to methodological outcomes)"),
    ("Results", "16a", "Results of the search and selection process, with a flow diagram.", "Section 3.1; Fig. 1"),
    ("", "16b", "Studies that appeared to meet the criteria but were excluded, and why.", "Table S11"),
    ("", "17", "Cite each included study and present its characteristics.", "Table 2; Fig. 2; Tables S8 and S10"),
    ("", "18", "Risk of bias for each included study.", "Section S5; file TableS5\\_risk\\_of\\_bias.csv"),
    ("", "19", "For all outcomes, summary statistics and effect estimates for each study.", "Fig. 3; database workbook, sheet 5\\_Effect\\_sizes"),
    ("", "20a", "Characteristics and risk of bias among contributing studies for each synthesis.", "Table 2; Section S5"),
    ("", "20b", "Results of all statistical syntheses (estimate, CI, heterogeneity).", "Section 3.3; Table 3"),
    ("", "20c", "Results of investigations of possible causes of heterogeneity.", "Section 3.4; Figs. 4--5; Fig. S2"),
    ("", "20d", "Results of sensitivity analyses.", "Sections 3.5 and 3.7; Tables S6 and S7"),
    ("", "21", "Assessments of risk of bias due to missing results.", "Section 3.7; Fig. S1"),
    ("", "22", "Assessments of certainty in the body of evidence.", "Section 4.6 (GRADE)"),
    ("Discussion", "23a", "General interpretation of the results in the context of other evidence.", "Sections 4.1--4.4"),
    ("", "23b", "Limitations of the evidence included in the review.", "Section 4.6"),
    ("", "23c", "Limitations of the review processes used.", "Section 4.6"),
    ("", "23d", "Implications for practice, policy and future research.", "Sections 4.4--4.5; Fig. 8"),
    ("Other information", "24a", "Registration information (name and number).", "Section 2.1 (OSF, osf.io/6p8ym)"),
    ("", "24b", "Where the protocol can be accessed.", "Section 2.1 (OSF registration)"),
    ("", "24c", "Amendments to the protocol.", "Section 2.11"),
    ("", "25", "Sources of financial or non-financial support.", "Funding statement"),
    ("", "26", "Competing interests.", "Declaration of competing interest"),
    ("", "27", "Availability of data, code and other materials.", "Data and code availability"),
]
abstract_items = [
    ("Title", "1", "Identify the report as a systematic review.", "Yes"),
    ("Objectives", "2", "Main objective(s) or question(s).", "Yes"),
    ("Eligibility criteria", "3", "Inclusion and exclusion criteria.", "Yes (same model and data, both designs)"),
    ("Information sources", "4", "Databases and date last searched.", "Yes (Scopus, Web of Science); date in Methods"),
    ("Risk of bias", "5", "Methods used to assess risk of bias.", "No (word limit); see Section 2.10"),
    ("Synthesis of results", "6", "Methods used to present and synthesize results.", "Yes (multilevel meta-analysis)"),
    ("Included studies", "7", "Number of included studies and participants (observations).", "Yes (266 studies, 1,102 effects)"),
    ("Synthesis of results", "8", "Results for main outcomes, with CIs.", "Yes"),
    ("Limitations of evidence", "9", "Brief summary of limitations.", "Partly (independent tests limited)"),
    ("Interpretation", "10", "General interpretation and implications.", "Yes"),
    ("Funding", "11", "Primary source of funding.", "No funding (stated in back matter)"),
    ("Registration", "12", "Register name and number.", "Yes (OSF link)"),
]

fd = pd.read_csv(ROOT / "fulltext/fulltext_decisions.csv")
inc_ids = set(fd.loc[fd.ft_decision == "include", "record_id"])
ex = pd.read_csv(ROOT / "extraction/extraction_template.csv", low_memory=False)
ex = ex[ex.record_id.isin(inc_ids) & (ex.primary == "yes")]
scr = pd.read_csv(ROOT / "screening/screening_decisions_public.csv")
ov = pd.read_csv(ROOT / "analysis/results/overall_effects.csv")
qc = json.load(open(ROOT / "qc/qc_agreement.json"))
st = pd.read_csv(ROOT / "manuscript/supplementary/TableS1_included_studies.csv")
st = st[st.record_id.isin(inc_ids)].sort_values(["first_author", "year"])

num = lambda v: pd.to_numeric(v, errors="coerce")
g = ex.groupby("record_id")
rob = pd.DataFrame({
    "sampling_design_reported": g.sampling_design.first().ne("unknown"),
    "values_from_text_or_tables": g.digitised.apply(lambda v: not (v == "yes").any()),
    "cv_uncertainty_reported": g.sd_random.apply(lambda v: num(v).notna().any()),
    "block_or_buffer_size_reported": g.block_or_buffer_size_m.apply(lambda v: num(v).notna().any()),
    "autocorrelation_range_reported": g.autocorrelation_range_m.apply(lambda v: num(v).notna().any()),
    "independent_test": g.independent_validation.apply(lambda v: (v == "yes").any()),
    "open_data": g.open_data.first().eq("yes"),
}).reset_index()
rob.to_csv(OUT / "TableS5_risk_of_bias.csv", index=False)
rob_lab = {"sampling_design_reported": "Sampling design described", "values_from_text_or_tables": "All values taken from text or tables (none digitised)",
           "cv_uncertainty_reported": "Uncertainty of CV estimates reported", "block_or_buffer_size_reported": "Block or buffer size reported",
           "autocorrelation_range_reported": "Autocorrelation range reported", "independent_test": "Independent test reported",
           "open_data": "Data openly available"}

searches = [
    ("Scopus v1", "2026-10-09", "scopus_query.txt", "153"),
    ("Scopus v2", "2026-10-09", "scopus_query_v2.txt", "751"),
    ("Scopus v3", "2026-10-09", "scopus_query_v3.txt", "1,027"),
    ("Scopus v4 (citation-based)", "2026-10-09", "scopus_query_v4_citation.txt", "2,557 exported (2,723 displayed)"),
    ("Web of Science Core Collection", "2026-10-09", "wos_query.txt", "1,043"),
]

L = []
A = L.append
A(r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage{lmodern}
\usepackage[margin=2cm]{geometry}\usepackage{longtable,booktabs,array,graphicx,pdflscape}
\usepackage{natbib}\usepackage[hidelinks]{hyperref}\usepackage{amsmath}
\renewcommand{\thetable}{S\arabic{table}}\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\thesection}{S\arabic{section}}
\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}
\begin{document}
\begin{center}{\Large\bfseries Supplementary Material}\\[4pt]
Random cross-validation overestimates the accuracy of machine-learning environmental maps: a meta-analysis of 266 studies\\[4pt]
Richar Andre Vilca-Solorzano, Fred Torres-Cruz\end{center}
\tableofcontents\newpage
""")
A(r"\section{PRISMA 2020 checklists}")
A(r"\small\begin{longtable}{p{2.3cm}p{0.8cm}p{7.2cm}p{5.6cm}}\caption{PRISMA 2020 checklist \citep{page2021}. Locations refer to the main text unless marked S (this document).}\\\toprule Section & Item & Checklist item & Location \\\midrule\endfirsthead\toprule Section & Item & Checklist item & Location \\\midrule\endhead")
for s_, i, t, loc in prisma:
    A(f"{tex(s_)} & {i} & {tex(t)} & {loc} \\\\")
A(r"\bottomrule\end{longtable}")
A(r"\begin{longtable}{p{2.8cm}p{0.8cm}p{6.6cm}p{5.6cm}}\caption{PRISMA 2020 for Abstracts checklist.}\\\toprule Section & Item & Checklist item & Reported \\\midrule")
for s_, i, t, loc in abstract_items:
    A(f"{tex(s_)} & {i} & {tex(t)} & {tex(loc)} \\\\")
A(r"\bottomrule\end{longtable}\normalsize")

A(r"\section{Search strategies}")
A(r"All searches were run on 9 October 2026 in titles, abstracts and keywords (Scopus: TITLE-ABS-KEY; Web of Science: TS), limited to articles in English published from 2010 onwards. The Web of Science search was run with institutional access by the second author. Exported records were de-duplicated by DOI and normalised title.")
A(r"\begin{table}[h]\centering\small\caption{Searches, dates and records retrieved.}\begin{tabular}{lll}\toprule Search & Date & Records \\\midrule")
for n, d, f, k in searches:
    A(f"{tex(n)} & {d} & {tex(k)} \\\\")
A(r"\bottomrule\end{tabular}\end{table}")
for n, d, f, k in searches:
    q = (ROOT / "search" / f).read_text().strip()
    q = re.sub(r"\s+", " ", q)
    A(r"\paragraph{" + tex(n) + r"}{\footnotesize\ttfamily\raggedright " + tex(q) + r"\par}")

A(r"\section{Eligibility criteria and selection}")
A(r"Inclusion: (I1) original peer-reviewed research article; (I2) machine-learning model mapping or predicting a spatially distributed environmental or agricultural variable; (I3) the same model and data evaluated with both random cross-validation (or a random split) and spatial cross-validation; (I4) at least one numeric metric for both designs; (I5) English, 2010--2026. Exclusion: (E1) not original research; (E2) one validation design only, designs applied to different data, or temporal versus spatial validation only; (E3) no machine learning; (E4) not spatial or outside the environmental and agricultural domain, including mineral prospectivity and lithology; (E5) metrics not extractable; (E6) duplicate publication.")
A(r"Title and abstract screening and full-text assessment were based on proposals by a large language model that applied these criteria and recorded a reason for each record; each proposal was checked and accepted or corrected by the first author. A blind second review of a random 10\% sample of full-text decisions (27 included, 12 excluded studies) gave " +
  f"{qc['decision_agreement']*100:.0f}\\% agreement (Cohen's $\\kappa = {qc['cohen_kappa']:.2f}$); {qc['value_pairs_matching']} of {qc['value_pairs_checked']} extracted value pairs agreed within $\\max(0.02, 5\\%)$. Disagreements were resolved by re-reading the full text; one study (R0409) was excluded after reconciliation.")

A(r"\section{Data items}")
A(r"\small\begin{longtable}{p{4cm}p{11.5cm}}\caption{Extracted variables (one row = one model $\times$ metric $\times$ data set).}\\\toprule Variable & Description \\\midrule")
items = [("Metric values", "Value under random CV and under spatial CV; standard deviations when reported; value on an independent test set when reported"),
         ("Metric", "R2, RMSE, MAE, AUC, overall or balanced accuracy, kappa, F1, TSS, CCC (only R2, RMSE, AUC and accuracy were pooled)"),
         ("Validation designs", "Type of random CV (k-fold, split, leave-one-out, out-of-bag) and of spatial CV (blocks, clusters, leave-location-out, buffered leave-one-out, NNDM/kNNDM); number of folds and repeats; block or buffer size"),
         ("Data", "Number of observations, study area, sampling design (clustered, probability, regular grid, not reported), reported autocorrelation range"),
         ("Model and task", "Model family, regression or classification, application domain, target variable"),
         ("Provenance", "Table, figure or page of each value; digitised from figure (yes/no); primary or secondary model version"),
         ("Openness", "Data and code availability")]
for a, b in items:
    A(f"{tex(a)} & {tex(b)} \\\\")
A(r"\bottomrule\end{longtable}\normalsize")

A(r"\section{Risk of bias and reporting quality}")
A(r"Formal tools such as PROBAST were developed for clinical prediction models and do not map directly onto comparisons of validation designs. We therefore recorded seven review-specific items that affect how much the reported difference can be trusted. Study-level values are given in the file TableS5\_risk\_of\_bias.csv.")
A(r"\begin{table}[h]\centering\small\caption{Proportion of included studies meeting each item (n = " + str(len(rob)) + r").}\begin{tabular}{lr}\toprule Item & Studies (\%) \\\midrule")
for c, lab in rob_lab.items():
    A(f"{tex(lab)} & {int(rob[c].sum())} ({100*rob[c].mean():.0f}) \\\\")
A(r"\bottomrule\end{tabular}\end{table}")

A(r"\section{Sensitivity analyses}")
lab = {"dR2": r"$\Delta R^2$", "lnRR_RMSE": "lnRR RMSE", "dAUC": r"$\Delta$AUC", "dAccuracy": r"$\Delta$accuracy"}
A(r"\begin{table}[h]\centering\small\caption{Pooled estimates under alternative analytic choices.}\begin{tabular}{lccccc}\toprule Effect & Main model & Unweighted & Without imputed $n$ & Without digitised values & Robust $p$ \\\midrule")
for _, r in ov.iterrows():
    A(f"{lab[r.effect]} & {r.estimate:.3f} ({r.ci_lb:.3f}, {r.ci_ub:.3f}) & {r.unweighted_estimate:.3f} & {r.estimate_without_imputed_n:.3f} & "
      f"{r.estimate_without_digitised:.3f} ({r.ci_lb_without_digitised:.3f}, {r.ci_ub_without_digitised:.3f}); {int(r.k_studies_without_digitised)} studies & "
      f"{'$<$0.001' if r.robust_p < 0.001 else f'{r.robust_p:.3f}'} \\\\")
A(r"\bottomrule\end{tabular}\end{table}")
rp = pd.read_csv(ROOT / "analysis/results/robustness_pooled.csv").set_index("analysis")
ri = pd.read_csv(ROOT / "analysis/results/robustness_independent_tests.csv").set_index("quantity")
A(r"\begin{table}[h]\centering\small\caption{Robustness checks. Higher-quality studies: sampling design described, all values from text or tables, sample size reported. Leave-one-out: range of the estimate when each study is left out in turn.}\begin{tabular}{lccc}\toprule Quantity & All studies & Higher-quality studies & Leave-one-out range \\\midrule")
for k, l in (("dR2", r"$\Delta R^2$"), ("lnRR_RMSE", "lnRR RMSE")):
    r = rp.loc[k]
    A(f"{l} & {r.full_estimate:.3f} & {r.hq_estimate:.3f} ({r.hq_lo:.3f}, {r.hq_hi:.3f}); {int(r.hq_studies)} studies & {r.loso_min:.3f}--{r.loso_max:.3f} \\\\")
ivs = pd.read_csv(ROOT / "analysis/results/independent_validation_summary.csv")
ivs = ivs[ivs.scale == "difference"].set_index("quantity")
for k, l in (("optimism_random", "Optimism of random CV vs independent test"), ("optimism_spatial", "Optimism of spatial CV vs independent test"),
             ("share_spatial_closer", "Share of comparisons with spatial CV closer")):
    r = ri.loc[k]
    extra = "" if pd.isna(r.max_p) else (f" (largest $p$ = {r.max_p:.3f})" if k == "optimism_random" else f" (smallest $p$ = {r.min_p:.3f})")
    A(f"{l} & {ivs.loc[k, 'mean']:.3f} & -- & {r.loso_min:.3f}--{r.loso_max:.3f}{extra} \\\\")
A(r"\bottomrule\end{tabular}\end{table}")
A(r"Egger-type regression slopes for small-study effects: " + ", ".join(f"{lab[r.effect]} $p = {r.egger_slope_p:.2f}$" for _, r in ov.iterrows()) + ". Funnel plots are shown in Fig.~S1.")
A(r"\begin{figure}[h]\centering")
for e in ["dR2", "lnRR_RMSE", "dAUC", "dAccuracy"]:
    A(r"\includegraphics[width=0.45\textwidth]{../../analysis/results/figures/funnel_" + e + r".png}")
A(r"\caption{Funnel plots for (top left to bottom right) $\Delta R^2$, lnRR RMSE, $\Delta$AUC and $\Delta$accuracy.}\end{figure}")

A(r"\section{Validation practice and study-level moderators}")
A(r"\begin{figure}[h]\centering\includegraphics[width=\textwidth]{../../figures/FigS2_validation_practice.pdf}\caption{How validation was applied in the included studies. (a) Random cross-validation used as baseline. (b) Source of the response data by task. (c) Study-level moderators of $\Delta R^2$: estimates and 95\% confidence intervals, number of studies, and test of differences between subgroups; grey band, pooled estimate.}\end{figure}")
prof = pd.read_csv(ROOT / "analysis/results/validation_practice_profile.csv")
A(r"\small\begin{longtable}{p{4cm}p{6cm}rr}\caption{Validation practice in the 266 included studies (second, study-level extraction).}\\\toprule Variable & Level & Studies & \% \\\midrule\endfirsthead\toprule Variable & Level & Studies & \% \\\midrule\endhead")
for v, g in prof.groupby("variable", sort=False):
    for _, r in g.sort_values("studies", ascending=False).iterrows():
        A(f"{tex(v)} & {tex(r.level)} & {int(r.studies)} & {100*r.share:.0f} \\\\")
A(r"\bottomrule\end{longtable}")
slm = pd.read_csv(ROOT / "analysis/results/study_level_moderators.csv")
A(r"\begin{longtable}{p{2cm}p{3.6cm}p{3.6cm}rrr}\caption{Study-level moderators (three-level meta-regression; subgroups with at least three studies).}\\\toprule Effect & Moderator & Level & Estimate (95\% CI) & Studies & $p$ \\\midrule\endfirsthead\toprule Effect & Moderator & Level & Estimate (95\% CI) & Studies & $p$ \\\midrule\endhead")
for _, r in slm.iterrows():
    A(f"{tex(r.effect)} & {tex(r.moderator)} & {tex(r.level)} & {r.estimate:.2f} ({r.ci_lb:.2f}, {r.ci_ub:.2f}) & {int(r.k_studies)} & {r.p_between:.3f} \\\\")
A(r"\bottomrule\end{longtable}\normalsize")
A(r"\clearpage\section{Included studies}")
A(r"\begin{landscape}\scriptsize\begin{longtable}{p{0.9cm}p{2.6cm}p{0.7cm}p{4.2cm}p{2.6cm}p{2cm}p{3.6cm}p{3.6cm}}\caption{Included studies (n = " + str(len(st)) + r"). DOIs are given in the data repository.}\\\toprule ID & First author & Year & Journal & Domain & Sampling & Models & Spatial CV \\\midrule\endfirsthead\toprule ID & First author & Year & Journal & Domain & Sampling & Models & Spatial CV \\\midrule\endhead")
for _, r in st.iterrows():
    yr = "" if pd.isna(r.year) else str(int(float(r.year)))
    A(f"{r.record_id} & {tex(r.first_author)} & {yr} & {tex(r.journal)} & {tex(r.domain)} & {tex(r.sampling_design)} & {tex(str(r.models)[:70])} & {tex(str(r.spatial_cv)[:60])} \\\\")
A(r"\bottomrule\end{longtable}\end{landscape}")

A(r"\section{Full texts excluded and not retrieved}")
exc = fd[fd.ft_decision != "include"].merge(scr[["record_id", "Year", "Title", "DOI"]], on="record_id", how="left").sort_values(["ft_decision", "ft_reason", "record_id"])
A(r"\scriptsize\begin{longtable}{p{0.9cm}p{0.6cm}p{0.8cm}p{10.4cm}p{3.2cm}}\caption{Full texts excluded at eligibility assessment, with reasons (E1--E6, Section S3), and reports not retrieved.}\\\toprule ID & Year & Reason & Title & DOI \\\midrule\endfirsthead\toprule ID & Year & Reason & Title & DOI \\\midrule\endhead")
for _, r in exc.iterrows():
    yr = "" if pd.isna(r.Year) else str(int(r.Year))
    reason = "NR" if r.ft_decision == "not_retrieved" else tex(r.ft_reason)
    A(f"{r.record_id} & {yr} & {reason} & {tex(r.Title)} & {tex(r.DOI)} \\\\")
A(r"\bottomrule\end{longtable}\normalsize")
A(r"In addition, 55 eligible reports could not be obtained (no institutional access); they are listed in the data repository (fulltext\_log.csv).")
A(r"\bibliographystyle{elsarticle-harv}\bibliography{../references}\end{document}")
(OUT / "supplementary.tex").write_text("\n".join(L), encoding="utf-8")
print("written", OUT / "supplementary.tex", "| included", len(st), "| excluded/not retrieved", len(exc))
