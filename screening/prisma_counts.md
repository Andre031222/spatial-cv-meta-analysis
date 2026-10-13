# PRISMA 2020 counts (update at each stage)

## Identification
- Scopus v1 (`scopus_query.txt`): 153
- Scopus v2 (`scopus_query_v2.txt`): 751
- Scopus v3 (`scopus_query_v3.txt`, broadened keyword query): 1,027
- Scopus v4 (`scopus_query_v4_citation.txt`, citation-based REF() search): 2,557 exported (2,723 displayed)
- Web of Science Core Collection (`wos_query.txt`): 1,043
- Total records identified: 5,531 (Scopus 4,488 + WoS 1,043)
- Duplicates removed (DOI, then normalised title): 2,241  (Scopus internal 1,317: v1 ⊂ v2 ⊂ v3, v4 ∩ v1–v3 = 413; WoS ∩ Scopus = 924)
- Removed before screening for other reasons (WoS records not meeting export filters: non-article types, non-English, pre-2010): 63
- **Records to screen: 3,227** (all original articles)

## Pre-screening triage (automatic, keyword-based — NOT a decision)
- A_both (spatial AND random/non-spatial CV or optimism in abstract): 167 → screen first
- B_spatial_only: 849
- C_low (keyword search, no CV terms in abstract): 83
- D_cites_SCV_mentions_validation (v4; cites spatial-CV papers + abstract mentions validation): 859
- E_cites_SCV_only (v4; cites spatial-CV papers, no validation terms in abstract): 1,257
- X_check_review (title suggests review/meta-analysis → exclude E1 if confirmed): 12

## Screening — title/abstract (COMPLETE, 2026-10-09)
- Records screened: 3,227 (AI-assisted proposals, confirmed by the author; rules: mining/geology = E4; temporal-vs-spatial without random CV = E2)
- Records excluded: 2,780 — E2 only one CV type / no comparison: 2,004 · E4 off-domain: 723 · E1 not original: 32 · E3 no ML: 21
- **Reports sought for retrieval (full text): 447** (249 include + 198 maybe)

## Full text (retrieval closed 2026-10-12)
- Reports sought: 447 · retrieved: 392 (automatic OA 80 · Brave/MDPI etc. 103 · manual by author 209)
- Reports not retrieved: 57 (55 paywalled/no access; 2 retrieved files were not the article)
- Reports assessed for eligibility: 390
- Reports excluded: 124 — E2 90 · E5 23 · E4 8 · E3 2 · E1 1 (incl. 1 changed after QC: R0409)
- **Studies included: 266**; 239 contribute to ≥1 pooled metric (R², RMSE, AUC, accuracy)
- QC (blind 2nd reviewer, 39 records): eligibility agreement 90%, Cohen κ = 0.77; value agreement 95% (63/66 pairs)
