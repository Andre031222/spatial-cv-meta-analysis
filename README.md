# Random versus spatial cross-validation in machine-learning environmental mapping

Data and code for a systematic review and multilevel meta-analysis of studies that evaluated the same
machine-learning model and data with both random and spatial cross-validation (266 studies, 1,102 effect sizes).

Article: *Random cross-validation overestimates the accuracy of machine-learning environmental maps: a meta-analysis of 266 studies* (submitted to Environmental Modelling & Software).

Protocol (OSF registration): <https://doi.org/10.17605/OSF.IO/6P8YM>  
Archived data and code (OSF): <https://doi.org/10.17605/OSF.IO/S8Y5H>

## Contents

| Folder | Content |
|---|---|
| `search/` | Search strings for Scopus (v1–v4) and Web of Science, search log, script that merges WoS exports |
| `screening/` | One row per unique record with title/abstract decision (`screening_decisions_public.csv`), eligibility criteria, PRISMA counts, reviewed screening sheets |
| `fulltext/` | Full-text eligibility decisions, retrieval log and retrieval scripts |
| `extraction/` | Codebook and extraction sheet (one row = model × metric × dataset) |
| `qc/` | Blind double-review sample and second-reviewer extraction |
| `analysis/` | R and Python scripts; `analysis/results/` holds all tables produced by the scripts |
| `figures/` | Figures produced by the scripts (PNG/TIFF 600 dpi, PDF) |
| `references/` | BibTeX file of the cited literature (all entries with DOI) |

Full texts and raw database exports are not included (publisher and database licences).

## Reproducing the analysis

```bash
# Python 3.12+ and R 4.4+
python -m venv .venv && .venv/bin/pip install -r requirements.txt
Rscript -e 'install.packages(c("metafor", "clubSandwich"))'

Rscript analysis/01_meta_analysis.R          # pooled effects, moderators, sensitivity
Rscript analysis/04_additional_analyses.R    # independent test sets, calibration, year/block size, reporting audit
.venv/bin/python analysis/03_qc_agreement.py # agreement between reviewers

# figures (world map needs Natural Earth 1:110m countries)
mkdir -p data_external/naturalearth
curl -L -o data_external/naturalearth/ne_110m_admin_0_countries.zip \
  https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip
# country flags for Fig. 2 (optional; flagcdn.com, public domain)
mkdir -p data_external/flags
for c in cn:CHN us:USA de:DEU ca:CAN au:AUS br:BRA es:ESP fr:FRA pe:PER in:IND tw:TWN jp:JPN id:IDN at:AUT vn:VNM; do
  curl -sL -o data_external/flags/${c#*:}.png https://flagcdn.com/w80/${c%%:*}.png; done
Rscript analysis/07_study_level_moderators.R      # study-level moderators and validation-practice profile
.venv/bin/python analysis/05_figures.py           # Figs 4 and 6
.venv/bin/python analysis/08_fig_practice.py      # Fig. 3
.venv/bin/python analysis/09_figures_v2.py        # Figs 2, 5, 7 and 8
.venv/bin/python analysis/10_graphical_abstract.py # graphical abstract
```
Figs 1 and 9 are TikZ diagrams (`figures/prisma_flow.tex`, `figures/Fig9_decision_guide.tex`).

Tested with R 4.6.1 (metafor 5.2.1, clubSandwich 0.7.0) and the Python versions in `requirements.txt`.

## Licence

Data: CC BY 4.0. Code: MIT. See `LICENSE-DATA.md`.

## Contact

Richar Andre Vilca-Solorzano — Universidad Nacional del Altiplano, Puno, Peru
