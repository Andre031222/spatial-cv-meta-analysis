# Analysis plan (R: metafor, clubSandwich)

1. Effect sizes: ΔR², ΔAUC, lnRR_RMSE = ln(RMSE_spatial/RMSE_random).
2. Multilevel random-effects model (effects nested in studies), REML; 95% CI and prediction interval.
3. Heterogeneity: τ², I² (by level).
4. Meta-regression moderators: domain, model family, task, log(n_samples), spatial_cv_type,
   block_size / autocorrelation_range, year.
5. Robustness: robust variance estimation, leave-one-study-out, exclude digitised values.
6. Small-study effects: funnel plot, Egger-type test (multilevel).
7. Outputs: forest plot, orchard plot, moderator plots, PRISMA flow diagram.
