# Eligibility criteria

## Include
- I1. **Original** peer-reviewed research article (no reviews).
- I2. Machine-learning model for mapping/predicting a spatially distributed environmental or agricultural variable.
- I3. The **same model and dataset** evaluated with **both** random CV/split **and** spatial CV.
- I4. Reports at least one numeric metric for both (R², RMSE, MAE, AUC, accuracy, kappa) in text, tables, figures or supplements.
- I5. English, published 2010–2026.

## Exclude (record the reason code)
- E1. Review, meta-analysis, editorial, commentary, conference abstract, book chapter, thesis.
- E2. Only one validation type (only random or only spatial).
- E3. No machine learning (only geostatistics/kriging or linear regression without ML comparison).
- E4. Not spatial data / not environmental-agricultural domain.
- E5. Metrics not extractable after contacting authors.
- E6. Duplicate publication of the same data.

## Stages
1. Remove duplicates (DOI, then title).
2. Title/abstract screening → `title_abstract_decisions.csv` (id, decision, reason).
3. Full-text eligibility → `fulltext_decisions.csv` (id, decision, reason code).
