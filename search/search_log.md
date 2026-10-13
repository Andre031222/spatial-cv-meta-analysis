# Search log (PRISMA-S)

| Date | Database | Query file | Filters | Records | Exported file |
|---|---|---|---|---|---|
| 2026-10-09 | Scopus | `scopus_query.txt` (v1) | DOCTYPE(ar), 2010–2026, English | 153 | `exports/scopus_v1_20261009.csv` |
| 2026-10-09 | Scopus | `scopus_query_v2.txt` (v2, sin bloque de comparación) | DOCTYPE(ar), 2010–2026, English | 751 | `exports/scopus_v2_20261009.csv` |
| 2026-10-09 | Scopus | `scopus_query_v3.txt` (v3: +sinónimos de CV espacial — leave-one-site/field/region/group-out, NNDM/kNNDM, area of applicability, spatial hold-out, geographic/cluster CV, SAC W/5 validation; +ML: LightGBM, CatBoost, MaxEnt, kNN, QRF; +dominios: biomass, carbon, groundwater, water quality, air pollution/PM2.5, landslide, flood, wildfire, ecology) | DOCTYPE(ar), 2010–2026, English | 1027 (all Article) | `exports/scopus_v3_20261009.csv` |
| 2026-10-09 | Scopus (citation-based, REF field) | `scopus_query_v4_citation.txt` (papers whose reference lists cite 15 key spatial-CV method papers: Roberts 2017, blockCV, sperrorest, Ploton 2020, Meyer 2018/2019/2021, Schratz 2019, Le Rest 2014, Pohjankukka 2017, Wadoux 2021, NNDM, kNNDM, Karasiak 2022, Kattenborn 2022) AND ML block AND domain block | DOCTYPE(ar), 2010–2026, English | 2,723 shown / 2,557 exported (unique EIDs) | `exports/scopus_v4_citation_20261009.csv` |
| 2026-10-09 | Web of Science Core Collection (run by a colleague with institutional access) | `wos_query.txt` (v3 translated to TS=, NEAR/5) | intended: Article, English, 2010–2026 (only partly applied at export) | 1,043 (1000 + 43, two Excel exports) | `exports/wos_part1_20261009.xls`, `exports/wos_part2_20261009.xls` → `exports/wos_combined_20261009.tsv` |
| YYYY-MM-DD | IEEE Xplore | (adapt) | Journals | — | `exports/ieee_YYYYMMDD.csv` |

**Scopus export fields:** Authors, Title, Year, Source title, DOI, Link, Abstract, Author keywords,
Index keywords, Document type, Open access, Affiliations, Cited by. Format: CSV.

Notes: run the query exactly as saved; if you edit it, save a new version (`scopus_query_v2.txt`) and log why.

v3 contains all 751 v2 records (superset) → +276 new unique records.
v4 vs v1–v3: 413 duplicates → +2,144 new unique records. Scopus displayed 2,723 but the CSV contains 2,557 unique EIDs (export of all 1–2723 requested).
WoS: 924 duplicates of Scopus records (≈89% overlap); 63 removed by eligibility filters applied after export (Proceedings Paper/Review/Data-only types, 3 non-English, 5 published before 2010); +56 new unique originals.
