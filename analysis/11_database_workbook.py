from pathlib import Path

import geopandas as gpd
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "analysis/results"
OUT = ROOT / "data/spatial_cv_meta_analysis_database.xlsx"
OUT.parent.mkdir(exist_ok=True)

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="1F3A5F")
SUB_FILL = PatternFill("solid", fgColor="DCE6F1")
NOTE = Font(name=FONT, size=9, italic=True, color="555555")
THIN = Border(bottom=Side(style="thin", color="BBBBBB"))

scr = pd.read_csv(ROOT / "screening/screening_decisions_public.csv", dtype=str)
ft = pd.read_csv(ROOT / "fulltext/fulltext_decisions.csv", dtype=str)
ft = ft.merge(scr[["record_id", "Year", "Title", "Source title", "DOI"]], on="record_id", how="left")
ex = pd.read_csv(ROOT / "extraction/extraction_template.csv", dtype=str)
sl = pd.read_csv(ROOT / "extraction/study_level.csv", dtype=str)
inc = ft.loc[ft.ft_decision == "include", "record_id"]
ex = ex[ex.record_id.isin(inc)]
first = ex.groupby("record_id").agg(first_author=("first_author", "first"), year=("year", "first"), journal=("journal", "first"),
                                    doi=("doi", "first"), domain=("domain", "first"),
                                    sampling_design=("sampling_design", "first")).reset_index()
sl["country_iso3"] = sl.country_iso3.fillna("").str.replace(",", ";").str.replace(" ", "")
world = gpd.read_file(f"zip://{ROOT}/data_external/naturalearth/ne_110m_admin_0_countries.zip")
cname = dict(zip(world.ADM0_A3, world.NAME)) | dict(zip(world.ISO_A3, world.NAME))
cname.update({"USA": "United States", "TWN": "Taiwan", "KOR": "South Korea", "ATA": "Antarctica", "SGP": "Singapore",
              "HKG": "Hong Kong", "MLT": "Malta", "MUS": "Mauritius", "REU": "Réunion", "GLOBAL": "Global", "MULTI": "Multiple"})
ccont = dict(zip(world.ADM0_A3, world.CONTINENT))
sl["country_names"] = sl.country_iso3.apply(lambda v: "; ".join(cname.get(c, c) for c in v.split(";") if c))
studies = first.merge(sl, on="record_id", how="right")
cols = ["record_id", "first_author", "year", "journal", "doi", "country_iso3", "country_names"] + \
       [c for c in sl.columns if c not in ("record_id", "country_iso3", "country_names")] + ["domain", "sampling_design"]
studies = studies[cols]
studies["year"] = pd.to_numeric(studies.year, errors="coerce")

eff = []
for e in ("dR2", "lnRR_RMSE", "dAUC", "dAccuracy"):
    d = pd.read_csv(RES / f"effects_{e}.csv"); d.insert(0, "effect", e); eff.append(d)
eff = pd.concat(eff)
overall = pd.read_csv(RES / "overall_effects.csv")
mods = pd.read_csv(RES / "moderators.csv")
mods.insert(0, "key", mods.effect + "|" + mods.moderator + "|" + mods.level.astype(str))
slm = pd.read_csv(RES / "study_level_moderators.csv")
slm.insert(0, "key", slm.effect + "|" + slm.moderator + "|" + slm.level.astype(str))
ind = pd.read_csv(RES / "independent_validation_rows.csv")
ind_sum = pd.read_csv(RES / "independent_validation_summary.csv")
cal = pd.read_csv(RES / "calibration_curve.csv")
cal = cal[cal.vr.round(2).isin([0.5, 0.6, 0.7, 0.8, 0.9])].copy()
rob = pd.read_csv(RES / "risk_of_bias_studies.csv") if (RES / "risk_of_bias_studies.csv").exists() else None

wb = Workbook()

def style_header(ws, row=1):
    for c in ws[row]:
        if c.value is None:
            continue
        c.font = Font(name=FONT, bold=True, color="FFFFFF", size=10)
        c.fill = HEAD_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")

def widths(ws, df=None, default=14, cap=45):
    for i, col in enumerate(ws.iter_cols(min_row=1, max_row=min(ws.max_row, 300)), 1):
        n = max((len(str(c.value)) for c in col if c.value is not None), default=default)
        ws.column_dimensions[get_column_letter(i)].width = max(8, min(cap, n + 2))

def data_sheet(name, df, note):
    ws = wb.create_sheet(name)
    ws.append(list(df.columns))
    for r in df.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and pd.isna(v)) else v for v in r])
    style_header(ws)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT, size=9)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    widths(ws)
    ws.sheet_properties.tabColor = "7F7F7F" if name.startswith(("1", "2", "3", "4")) else "1F3A5F"
    notes[name] = note
    return ws

notes = {}
readme = wb.active
readme.title = "README"

data_sheet("1_Screening", scr, "All 3,227 records screened on title and abstract, with decision and reason (raw).")
data_sheet("2_Full_text", ft, "390 full texts assessed (+2 not retrieved): include (266) or exclude with reason E1-E6 (raw).")
data_sheet("3_Extraction_raw", ex, "Every extracted row (model x metric x data set) of the included studies, values as reported (raw).")
ws_st = data_sheet("4_Studies", studies, "One row per included study (266): country, data source, sampling design and validation schemes (raw, second pass).")
data_sheet("5_Effect_sizes", eff, "Effect sizes used in the meta-analysis (processed): yi = random minus spatial (lnRR for RMSE), vi = sampling variance.")
data_sheet("6_Pooled", overall, "Pooled three-level random-effects estimates per metric, with sensitivity analyses (processed).")
data_sheet("7_Moderators", mods, "Subgroup estimates by sampling design, model, domain and spatial-CV type (processed).")
data_sheet("8_Study_moderators", slm, "Subgroup estimates by study-level variables: data source, random-CV scheme, block-size justification, n, continent (processed).")
data_sheet("9_Independent_tests", ind, "Cross-validation estimates compared with independent test data (processed). opt_* > 0: optimistic.")
data_sheet("10_Calibration", cal, "Expected spatial-CV R2 for a reported random-CV R2 (vr), by sampling design (processed).")

col = {c: get_column_letter(i + 1) for i, c in enumerate(studies.columns)}
N = len(studies) + 1
rng = lambda c: f"'4_Studies'!${col[c]}$2:${col[c]}${N}"

def summary_block(ws, r, title, column, levels, labels=None, note=None):
    ws.cell(r, 1, title).font = Font(name=FONT, bold=True, size=11, color="1F3A5F")
    r += 1
    for j, h in enumerate(["Level", "Studies", "% of 266"], 1):
        ws.cell(r, j, h)
    style_header(ws, r)
    r0 = r + 1
    for lv in levels:
        r += 1
        ws.cell(r, 1, (labels or {}).get(lv, lv)).font = Font(name=FONT, size=10)
        ws.cell(r, 2, f'=COUNTIF({rng(column)},"{lv}")').font = Font(name=FONT, size=10)
        ws.cell(r, 3, f"=B{r}/COUNTA({rng('record_id')})").number_format = "0.0%"
        ws.cell(r, 3).font = Font(name=FONT, size=10)
    if note:
        r += 1
        ws.cell(r, 1, note).font = NOTE
    return r + 2

ws = wb.create_sheet("S1_Validation_practice", 1)
ws.sheet_properties.tabColor = "009E73"
ws["A1"] = "Which validation designs are used, and on what data (counts recalculate from sheet 4_Studies)"
ws["A1"].font = Font(name=FONT, bold=True, size=13)
r = 3
r = summary_block(ws, r, "Random cross-validation used as baseline", "random_cv_scheme",
                  ["kfold", "repeated_kfold", "nested_kfold", "holdout_split", "LOO", "OOB", "other"],
                  {"kfold": "k-fold", "repeated_kfold": "Repeated k-fold", "nested_kfold": "Nested k-fold", "holdout_split": "Hold-out split",
                   "LOO": "Leave-one-out", "OOB": "Out-of-bag", "other": "Other"})
r = summary_block(ws, r, "Number of folds (k-fold studies)", "random_k", ["5", "10", "4", "15"], {"5": "5-fold", "10": "10-fold", "4": "4-fold", "15": "15-fold"})
r = summary_block(ws, r, "Hold-out split (training %)", "random_train_pct", ["80", "70", "75", "60", "90"],
                  {"80": "80/20", "70": "70/30", "75": "75/25", "60": "60/40", "90": "90/10"})
r = summary_block(ws, r, "Stratified random folds", "random_stratified", ["yes", "no"])
r = summary_block(ws, r, "Spatial cross-validation used", "spatial_cv_scheme",
                  ["leave_location_out", "blocks", "kmeans_clusters", "buffered_LOO", "NNDM_kNNDM", "other"],
                  {"leave_location_out": "Leave-location-out", "blocks": "Spatial blocks", "kmeans_clusters": "k-means clusters",
                   "buffered_LOO": "Buffered leave-one-out", "NNDM_kNNDM": "NNDM / kNNDM", "other": "Other"})
r = summary_block(ws, r, "How the block or buffer size was chosen", "block_size_justified",
                  ["autocorrelation_range", "expert_choice", "not_justified"],
                  {"autocorrelation_range": "From the autocorrelation range", "expert_choice": "Expert choice", "not_justified": "Not justified"})
r = summary_block(ws, r, "Sampling design of the data", "sampling_design", ["clustered", "regular_grid", "probability_random", "unknown"],
                  {"clustered": "Clustered", "regular_grid": "Regular grid", "probability_random": "Probability sample", "unknown": "Not reported"})
r = summary_block(ws, r, "Source of the response data", "data_source",
                  ["in_situ_samples", "remote_sensing_labels", "monitoring_stations", "survey_inventory", "gridded_product",
                   "compiled_database", "occurrence_records", "mixed", "simulated"],
                  {"in_situ_samples": "Field samples", "remote_sensing_labels": "Labels from imagery", "monitoring_stations": "Monitoring stations",
                   "survey_inventory": "Surveys / inventories", "gridded_product": "Gridded products", "compiled_database": "Compiled databases",
                   "occurrence_records": "Species occurrences", "mixed": "Mixed", "simulated": "Simulated"})
r = summary_block(ws, r, "Data geometry", "data_geometry", ["points", "raster_pixels", "polygons", "mixed"])
r = summary_block(ws, r, "Task", "task", ["regression", "classification", "both"])
r = summary_block(ws, r, "Independent test reported", "independent_test",
                  ["none", "separate_holdout", "later_period", "other_region", "probability_sample", "other"])
ws.column_dimensions["A"].width = 38; ws.column_dimensions["B"].width = 10; ws.column_dimensions["C"].width = 10

ws = wb.create_sheet("S2_Countries", 2)
ws.sheet_properties.tabColor = "009E73"
ws["A1"] = "Where the studies were carried out (counts recalculate from sheet 4_Studies; multi-country studies count once per country)"
ws["A1"].font = Font(name=FONT, bold=True, size=13)
cnt = {}
for v in studies.country_iso3:
    if not v or "GLOBAL" in v or "MULTI" in v:
        continue
    for c in v.split(";"):
        cnt[c] = cnt.get(c, 0) + 1
order = sorted(cnt, key=lambda c: (-cnt[c], c))
for j, h in enumerate(["Rank", "ISO3", "Country", "Continent", "Studies", "% of 266"], 1):
    ws.cell(3, j, h)
style_header(ws, 3)
for i, c in enumerate(order):
    r = 4 + i
    ws.cell(r, 1, f"=RANK(E{r},$E$4:$E${3 + len(order)})")
    ws.cell(r, 2, c); ws.cell(r, 3, cname.get(c, c)); ws.cell(r, 4, ccont.get(c, ""))
    ws.cell(r, 5, f'=COUNTIF({rng("country_iso3")},"*{c}*")')
    ws.cell(r, 6, f"=E{r}/COUNTA({rng('record_id')})").number_format = "0.0%"
    for j in range(1, 7):
        ws.cell(r, j).font = Font(name=FONT, size=10, bold=(c == "PER"), color=("B2182B" if c == "PER" else "000000"))
r = 4 + len(order)
ws.cell(r, 3, "Global or several continents").font = Font(name=FONT, size=10, italic=True)
ws.cell(r, 5, f'=COUNTIF({rng("country_iso3")},"*GLOBAL*")+COUNTIF({rng("country_iso3")},"*MULTI*")')
ws.cell(r + 1, 3, "Countries with at least one study").font = Font(name=FONT, size=10, bold=True)
ws.cell(r + 1, 5, f"=COUNTIF(E4:E{r - 1},\">0\")").font = Font(name=FONT, size=10, bold=True)
ws.cell(r + 3, 1, "Continents").font = Font(name=FONT, bold=True, size=11, color="1F3A5F")
for j, h in enumerate(["", "", "Continent", "", "Studies", "% of 266"], 1):
    ws.cell(r + 4, j, h or None)
style_header(ws, r + 4)
for k, ct in enumerate(["Asia", "Europe", "North America", "South America", "Africa", "Oceania", "Global", "Multiple", "Antarctica"]):
    rr = r + 5 + k
    ws.cell(rr, 3, ct); ws.cell(rr, 5, f'=COUNTIF({rng("continent")},"{ct}")')
    ws.cell(rr, 6, f"=E{rr}/COUNTA({rng('record_id')})").number_format = "0.0%"
ws.freeze_panes = "A4"
for c, w in zip("ABCDEF", (7, 8, 30, 16, 10, 10)):
    ws.column_dimensions[c].width = w

ws = wb.create_sheet("S3_When_to_use", 3)
ws.sheet_properties.tabColor = "D55E00"
ws["A1"] = "How large is the gap, and which validation to use (values linked to sheets 6, 7, 8 and 9)"
ws["A1"].font = Font(name=FONT, bold=True, size=13)
hdr = ["Situation", "R2 random minus spatial", "RMSE higher under spatial (%)", "Studies (R2)", "What to do"]
for j, h in enumerate(hdr, 1):
    ws.cell(3, j, h)
style_header(ws, 3)
M = "'7_Moderators'"
lk = lambda key, colname, sheet=M, frame=mods: (f"INDEX({sheet}!${get_column_letter(list(frame.columns).index(colname) + 1)}:"
                                                f"${get_column_letter(list(frame.columns).index(colname) + 1)},"
                                                f"MATCH(\"{key}\",{sheet}!$A:$A,0))")
rows = [
    ("All studies (pooled)", "='6_Pooled'!D2", "=100*(EXP('6_Pooled'!D3)-1)", "='6_Pooled'!C2",
     "Expect random CV to look better; report both designs."),
    ("Clustered sample (roads, stations, plots)", "=" + lk("dR2|sampling_h|clustered", "estimate"),
     "=100*(EXP(" + lk("lnRR_RMSE|sampling_h|clustered", "estimate") + ")-1)", "=" + lk("dR2|sampling_h|clustered", "k_studies"),
     "Use spatial CV (blocks at least as wide as the autocorrelation range, or kNNDM); random CV is an upper bound."),
    ("Regular grid", "=" + lk("dR2|sampling_h|regular_grid", "estimate"),
     "=100*(EXP(" + lk("lnRR_RMSE|sampling_h|regular_grid", "estimate") + ")-1)", "=" + lk("dR2|sampling_h|regular_grid", "k_studies"),
     "Report both; a moderate gap is expected."),
    ("Sampling design not reported", "=" + lk("dR2|sampling_h|unknown", "estimate"),
     "=100*(EXP(" + lk("lnRR_RMSE|sampling_h|unknown", "estimate") + ")-1)", "=" + lk("dR2|sampling_h|unknown", "k_studies"),
     "Treat as clustered; describe how the data were collected."),
    ("Probability sample of the mapped area", "=" + lk("dR2|sampling_h|probability_random", "estimate"),
     "=100*(EXP(" + lk("lnRR_RMSE|sampling_h|probability_random", "estimate") + ")-1)", "=" + lk("dR2|sampling_h|probability_random", "k_studies"),
     "Random CV is adequate for the accuracy of the whole map."),
]
S = "'8_Study_moderators'"
for lab, key, todo in [("Block size from the autocorrelation range", "dR2|Block size justified by|autocorrelation_range", "Size blocks from the semivariogram range; the gap measured is then about 2.7 times larger."),
                       ("Block size not justified", "dR2|Block size justified by|not_justified", "Gap is underestimated; justify the block size."),
                       ("Random baseline: leave-one-out / out-of-bag", "dR2|Random-CV scheme|LOO/OOB", "Most optimistic baseline; avoid as the reference."),
                       ("Random baseline: k-fold", "dR2|Random-CV scheme|k-fold", "5 or 10 folds give the same gap."),
                       ("Random baseline: hold-out split", "dR2|Random-CV scheme|Hold-out split", "70/30 and 80/20 give the same gap.")]:
    rows.append((lab, "=" + lk(key, "estimate", S, slm), None, "=" + lk(key, "k_studies", S, slm), todo))
for i, (a, b, c, d, e) in enumerate(rows):
    r = 4 + i
    for j, v in enumerate((a, b, c, d, e), 1):
        cell = ws.cell(r, j, v); cell.font = Font(name=FONT, size=10); cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(r, 2).number_format = "0.00"; ws.cell(r, 3).number_format = "0"
r = 4 + len(rows) + 1
ws.cell(r, 1, "Agreement with independent test data").font = Font(name=FONT, bold=True, size=11, color="1F3A5F")
for j, h in enumerate(["Quantity", "Mean", "95% CI low", "95% CI high", "p"], 1):
    ws.cell(r + 1, j, h)
style_header(ws, r + 1)
iq = "'11_Independent_summary'"
for k, (lab, q) in enumerate([("Optimism of random CV (R2, AUC, accuracy)", 2), ("Optimism of spatial CV (R2, AUC, accuracy)", 3),
                              ("Share of comparisons where spatial CV was closer", 5)]):
    rr = r + 2 + k
    ws.cell(rr, 1, lab)
    for j, colL in enumerate("CDEF" if k < 2 else "C", 2):
        ws.cell(rr, j, f"={iq}!{colL}{q}").number_format = "0.000" if k < 2 else "0%"
ws.cell(r + 6, 1, "Positive optimism: cross-validation estimate better than the independent test. Values recalculate if sheets 6-11 are updated.").font = NOTE
for c, w in zip("ABCDE", (44, 14, 16, 12, 70)):
    ws.column_dimensions[c].width = w
ws.freeze_panes = "A4"
data_sheet("11_Independent_summary", ind_sum, "Mean optimism of each design relative to independent tests, and share of comparisons where spatial CV was closer.")
data_sheet("13_Robustness", pd.concat([pd.read_csv(RES / "robustness_pooled.csv"), pd.read_csv(RES / "robustness_independent_tests.csv").rename(columns={"quantity": "analysis"})], ignore_index=True), "Leave-one-study-out ranges and estimates restricted to higher-quality studies (processed).")
if rob is not None:
    data_sheet("12_Risk_of_bias", rob, "Risk-of-bias and reporting items per study (PROBAST-based).")

ws = readme
ws["A1"] = "Random versus spatial cross-validation in machine-learning environmental maps: database of the systematic review and meta-analysis"
ws["A1"].font = Font(name=FONT, bold=True, size=13)
ws["A2"] = "Vilca-Solorzano, R.A. & Torres-Cruz, F. Universidad Nacional del Altiplano, Puno, Peru. Data: https://doi.org/10.17605/OSF.IO/S8Y5H · Protocol: https://doi.org/10.17605/OSF.IO/6P8YM"
ws["A2"].font = Font(name=FONT, size=10)
ws["A4"], ws["B4"], ws["C4"] = "Sheet", "Type", "Content"
style_header(ws, 4)
order_sheets = ["S1_Validation_practice", "S2_Countries", "S3_When_to_use"] + [s for s in wb.sheetnames if s[0].isdigit()]
desc = {"S1_Validation_practice": "Summary tables (formulas): validation schemes, folds, splits, block-size choice, sampling design, data source.",
        "S2_Countries": "Summary table (formulas): studies per country and continent, ranked.",
        "S3_When_to_use": "Summary table (linked formulas): size of the gap per situation and which validation to use."}
for i, s in enumerate(order_sheets):
    r = 5 + i
    kind = "Summary" if s.startswith("S") else ("Raw" if s[0] in "1234" and s[1] == "_" else "Processed")
    ws.cell(r, 1, s).hyperlink = f"#'{s}'!A1"
    ws.cell(r, 1).font = Font(name=FONT, size=10, color="0563C1", underline="single")
    ws.cell(r, 2, kind).font = Font(name=FONT, size=10, bold=True)
    ws.cell(r, 3, desc.get(s, notes.get(s, ""))).font = Font(name=FONT, size=10)
r = 6 + len(order_sheets)
for line in ["Codes. yi > 0 means random cross-validation gave the more favourable value. lnRR = ln(RMSE spatial / RMSE random); % higher = 100*(exp(lnRR)-1).",
             "sampling_h: clustered, regular_grid, probability_random, unknown (not reported). Rows in 3_Extraction_raw with primary = yes were analysed.",
             "Raw sheets are as extracted; processed sheets are outputs of analysis/01, 04 and 07 (R, metafor). Summary sheets use COUNTIF/INDEX formulas and update when the data change.",
             "Abstracts and full texts are not included (copyright)."]:
    ws.cell(r, 1, line).font = NOTE; r += 1
for c, w in zip("ABC", (26, 12, 120)):
    ws.column_dimensions[c].width = w
wb.move_sheet("README", offset=-wb.index(wb["README"]))
wb.save(OUT)
print("saved", OUT)
