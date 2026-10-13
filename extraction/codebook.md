# Extraction codebook

| Field | Description / allowed values |
|---|---|
| record_id | R0001… (link to screening sheet) |
| study_id | S001, S002… (one per independent study/dataset) |
| sampling_design | clustered, probability_random, regular_grid, unknown |
| independent_validation | yes/no — independent probability-sample test set reported (extract its metric too) |
| domain | soil, crop_yield, crop_suitability, climate, vegetation, land_cover, hydrology, species_distribution, other |
| task | regression / classification |
| n_samples | number of observations used for training + validation |
| model | RF, XGB, GBM, SVM, ANN, CNN, Cubist, other (one row per model) |
| random_cv_type | random_kfold, random_split, LOO, OOB, repeated_kfold |
| spatial_cv_type | block, buffer_LOO, cluster, leave_location_out, target_oriented, other |
| block_or_buffer_size_m | size used; NA if not reported |
| autocorrelation_range_m | range of the variogram if reported; NA otherwise |
| metric | R2, RMSE, MAE, AUC, accuracy, kappa |
| value_random / value_spatial | metric under each validation |
| sd_random / sd_spatial | across folds/repeats if reported |
| value_independent | metric on an independent (probability) test set, if reported |
| digitised | yes/no — value read from a figure (WebPlotDigitizer) |
| source_location | table/figure/page where the value was taken |
| open_data / open_code | yes / no |

**One row = one model × one metric × one dataset.** Values read from figures: use WebPlotDigitizer and note it.


**Full-text eligibility** → `fulltext/fulltext_decisions.csv` (record_id, ft_decision include/exclude, ft_reason E2/E3/E4/E5/E6, n_rows_extracted, notes).

## Codebook v2 rules (after pilot of 10 PDFs, 2026-10-09)
1. **Random comparator:** use the random scheme run on the same data as the spatial CV, matched in structure (random k-fold ↔ spatial k-fold; LOO ↔ buffered/spatial LOO). Put any other random scheme in `random_cv_alt` (+ value in notes).
2. **Variants** (feature sets, tuning, data versions): extract all; `primary`=yes for the paper's main/final configuration (all predictors, same tuning in both CVs), `primary`=no for the rest; describe in `variant`. Main analysis uses primary rows; others go to sensitivity.
3. **Block/buffer series** (e.g., buffers 0–150 km): extract each size; `primary`=yes for the size closest to the reported autocorrelation range, otherwise the authors' recommended/largest independent design. `block_size_unit` = m, km, deg, n_clusters, site.
4. **Allowed metrics:** R2, RMSE, MAE, RMSPE, CCC, AUC, accuracy, balanced_accuracy, F1, kappa, TSS. **Models:** ML only (RF, GBM/XGB/LGBM/CatBoost, SVM, ANN/CNN, Cubist, MaxEnt, kNN, QRF, GNN…); GLM/GAM/Lasso rows are not extracted (note them). **Spatial CV types:** block, spatial_kfold_cluster, buffer_LOO, leave_location_out (site/field/region), target_oriented, NNDM, unspecified.
5. `metric_aggregation`: pooled (all held-out predictions) or mean_of_folds; prefer mean_of_folds when both are given.
6. `n_folds_random`, `n_folds_spatial`, `n_repeats` replace `n_folds` (kept for legacy rows).
7. `independent_type`: none, probability_sample, other_region, temporal.
8. `open_data` / `open_code`: yes, no, on_request.
9. `sampling_design`: stratified/simple random or probability designs → probability_random; regular grids → regular_grid; opportunistic, GBIF/literature compilations, road or plantation surveys → clustered; mixed or unclear → unknown (explain in notes).
10. `digitised`: yes when read from a figure; record method (WebPlotDigitizer or visual) and approximate precision in notes.
11. **Preprints:** extract from the peer-reviewed published version when available (`published_doi`); a preprint may be used if numbers are identical — note it.
12. `study_id`: S + 4-digit record number (S0001); several independent datasets in one paper → S0005a, S0005b.
13. **Exclusion codes (full text):** E1 not original research; E2 only one CV type / not same model and data; E3 no ML; E4 off-domain; E5 metrics not extractable (after checking supplements/repository and contacting authors); E6 duplicate publication of same data.
