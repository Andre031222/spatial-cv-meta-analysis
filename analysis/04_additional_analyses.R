# Additional analyses that extend the core meta-analysis (run after 01_meta_analysis.R):
#   A. Which estimate is closer to an independent validation? (random vs spatial CV bias)
#   B. Calibration ("deflation") model: expected spatial-CV R2 given random-CV R2 and sampling design
#   C. Block/buffer size and publication year as moderators
#   D. Reporting audit
#   Rscript analysis/04_additional_analyses.R
suppressPackageStartupMessages({ library(metafor); library(clubSandwich) })
dir.create("analysis/results", showWarnings = FALSE, recursive = TRUE)
ft <- read.csv("fulltext/fulltext_decisions.csv", stringsAsFactors = FALSE)
inc <- ft$record_id[ft$ft_decision == "include"]
x <- read.csv("extraction/extraction_template.csv", stringsAsFactors = FALSE, na.strings = c("NA", ""))
x <- x[x$record_id %in% inc & x$primary == "yes", ]
num <- function(v) suppressWarnings(as.numeric(v))
x$vr <- num(x$value_random); x$vs <- num(x$value_spatial); x$vi_ind <- num(x$value_independent)
pct <- x$metric %in% c("R2", "AUC", "accuracy", "balanced_accuracy") & (x$vr > 1.5 | x$vs > 1.5)
pct[is.na(pct)] <- FALSE
x$vr[pct] <- x$vr[pct] / 100; x$vs[pct] <- x$vs[pct] / 100
x$vi_ind[pct & !is.na(x$vi_ind) & x$vi_ind > 1.5] <- x$vi_ind[pct & !is.na(x$vi_ind) & x$vi_ind > 1.5] / 100
x$n <- num(x$n_samples); x$n[is.na(x$n) | x$n < 10] <- median(x$n, na.rm = TRUE)
x$sampling_h <- ifelse(x$sampling_design %in% c("clustered", "probability_random", "regular_grid"), x$sampling_design, "unknown")
x$es_id <- seq_len(nrow(x))
out <- list()

# ---- A. distance of each CV estimate to an independent test set --------------------------------
# For R2/accuracy/AUC higher = better: optimism = CV - independent. For RMSE/MAE: optimism = ln(independent/CV)
A <- x[!is.na(x$vi_ind) & !is.na(x$vr) & !is.na(x$vs) & x$metric %in% c("R2", "RMSE", "MAE", "accuracy", "AUC"), ]
up <- A$metric %in% c("R2", "accuracy", "AUC")
A$opt_random  <- ifelse(up, A$vr - A$vi_ind, log(A$vi_ind / A$vr))
A$opt_spatial <- ifelse(up, A$vs - A$vi_ind, log(A$vi_ind / A$vs))
A$abs_gap <- abs(A$opt_random) - abs(A$opt_spatial)          # > 0: spatial CV closer to independent estimate
A$scale <- ifelse(up, "difference", "log ratio")
A$ind_type <- ifelse(is.na(A$independent_type), "other", A$independent_type)
write.csv(A[, c("record_id", "metric", "model", "sampling_h", "ind_type", "vr", "vs", "vi_ind", "opt_random", "opt_spatial", "abs_gap")],
          "analysis/results/independent_validation_rows.csv", row.names = FALSE)
summ <- function(v, s) { m <- lm(v ~ 1); r <- coef_test(m, vcov = "CR2", cluster = s)
  c(mean = mean(v), lo = mean(v) - qt(.975, r$df_Satt) * r$SE, hi = mean(v) + qt(.975, r$df_Satt) * r$SE, p = r$p_Satt) }
resA <- do.call(rbind, lapply(split(A, A$scale), function(d) {
  rbind(data.frame(scale = d$scale[1], quantity = "optimism_random", t(summ(d$opt_random, d$record_id)), k = nrow(d), studies = length(unique(d$record_id))),
        data.frame(scale = d$scale[1], quantity = "optimism_spatial", t(summ(d$opt_spatial, d$record_id)), k = nrow(d), studies = length(unique(d$record_id))),
        data.frame(scale = d$scale[1], quantity = "abs_random_minus_abs_spatial", t(summ(d$abs_gap, d$record_id)), k = nrow(d), studies = length(unique(d$record_id))),
        data.frame(scale = d$scale[1], quantity = "share_spatial_closer", mean = mean(d$abs_gap > 0), lo = NA, hi = NA, p = NA, k = nrow(d), studies = length(unique(d$record_id))))
}))
byType <- do.call(rbind, lapply(split(A, A$ind_type), function(d) data.frame(ind_type = d$ind_type[1], k = nrow(d),
  studies = length(unique(d$record_id)), share_spatial_closer = mean(d$abs_gap > 0),
  median_opt_random = median(d$opt_random), median_opt_spatial = median(d$opt_spatial))))
write.csv(resA, "analysis/results/independent_validation_summary.csv", row.names = FALSE)
write.csv(byType, "analysis/results/independent_validation_by_type.csv", row.names = FALSE)

# ---- B. calibration model for R2: spatial R2 as a function of random R2 and sampling design --------
B <- x[x$metric == "R2" & !is.na(x$vr) & !is.na(x$vs) & x$vr > 0 & x$vr <= 1 & x$vs >= -1, ]
B$yi <- B$vr - B$vs
var_r2 <- function(r2, n) { r <- pmin(pmax(r2, 0.001), 0.999); 4 * r * (1 - r)^2 / n }
B$vi <- var_r2(B$vr, B$n) + var_r2(B$vs, B$n)
B$vr_c <- B$vr - 0.8
mB <- rma.mv(yi, vi, mods = ~ vr_c * sampling_h, random = ~ 1 | record_id / es_id, data = B, method = "REML", sparse = TRUE)
rob <- coef_test(mB, vcov = "CR2", cluster = B$record_id)
write.csv(data.frame(term = rownames(mB$b), estimate = mB$b[, 1], robust_se = rob$SE, robust_p = rob$p_Satt),
          "analysis/results/calibration_model_coefficients.csv", row.names = FALSE)
grid <- expand.grid(vr = seq(0.3, 0.99, by = 0.01), sampling_h = c("clustered", "probability_random", "regular_grid", "unknown"))
grid$vr_c <- grid$vr - 0.8
Xn <- model.matrix(~ vr_c * sampling_h, data = cbind(grid, yi = 0))[, -1]
pr <- predict(mB, newmods = Xn)
grid$gap <- pr$pred; grid$gap_lo <- pr$ci.lb; grid$gap_hi <- pr$ci.ub; grid$gap_pi_lo <- pr$pi.lb; grid$gap_pi_hi <- pr$pi.ub
grid$expected_spatial_r2 <- grid$vr - grid$gap
write.csv(grid, "analysis/results/calibration_curve.csv", row.names = FALSE)
write.csv(B[, c("record_id", "sampling_h", "vr", "vs", "yi", "vi", "n")], "analysis/results/calibration_points.csv", row.names = FALSE)

# ---- C. block size and year ---------------------------------------------------------------------
eR2 <- read.csv("analysis/results/effects_dR2.csv")
eRM <- read.csv("analysis/results/effects_lnRR_RMSE.csv")
meta <- x[, c("es_id", "record_id", "year", "block_or_buffer_size_m", "block_size_unit")]
addmeta <- function(e) {
  # effects files carry study and value columns; join by study and values
  m <- merge(e, unique(x[, c("record_id", "year")]), by.x = "study", by.y = "record_id", all.x = TRUE)
  bs <- aggregate(num(block_or_buffer_size_m) ~ record_id, data = x[!is.na(num(x$block_or_buffer_size_m)) & x$block_size_unit %in% c("m", "km", NA), ], FUN = median)
  names(bs)[2] <- "block_m"
  merge(m, bs, by.x = "study", by.y = "record_id", all.x = TRUE)
}
modC <- list()
for (nm in c("dR2", "lnRR_RMSE")) {
  e <- addmeta(if (nm == "dR2") eR2 else eRM); e$year <- num(e$year)
  my <- rma.mv(yi, vi, mods = ~ I(year - 2024), random = ~ 1 | study / es_id, data = e[!is.na(e$year), ], method = "REML", sparse = TRUE)
  eb <- e[!is.na(e$block_m) & e$block_m > 0, ]
  mb <- rma.mv(yi, vi, mods = ~ log10(block_m), random = ~ 1 | study / es_id, data = eb, method = "REML", sparse = TRUE)
  modC[[nm]] <- rbind(data.frame(effect = nm, moderator = "year (per year)", slope = my$b[2], lo = my$ci.lb[2], hi = my$ci.ub[2], p = my$pval[2], studies = length(unique(e$study[!is.na(e$year)]))),
                      data.frame(effect = nm, moderator = "log10 block/buffer size (m)", slope = mb$b[2], lo = mb$ci.lb[2], hi = mb$ci.ub[2], p = mb$pval[2], studies = length(unique(eb$study))))
}
write.csv(do.call(rbind, modC), "analysis/results/year_blocksize_moderators.csv", row.names = FALSE)

# ---- D. reporting audit (study level) ------------------------------------------------------------
st <- do.call(rbind, lapply(split(x, x$record_id), function(d) data.frame(record_id = d$record_id[1], year = num(d$year[1]),
  sampling_reported = d$sampling_h[1] != "unknown", range_reported = any(!is.na(num(d$autocorrelation_range_m))),
  block_size_reported = any(!is.na(num(d$block_or_buffer_size_m))), sd_reported = any(!is.na(num(d$sd_random))),
  independent_validation = any(d$independent_validation == "yes", na.rm = TRUE),
  open_data = isTRUE(d$open_data[1] == "yes"), open_code = isTRUE(d$open_code[1] == "yes"))))
write.csv(st, "analysis/results/reporting_audit_studies.csv", row.names = FALSE)
aud <- colMeans(st[, -(1:2)], na.rm = TRUE)
write.csv(data.frame(item = names(aud), share = aud, n = nrow(st)), "analysis/results/reporting_audit_summary.csv", row.names = FALSE)

print(resA, digits = 3); print(byType, digits = 3)
print(read.csv("analysis/results/calibration_model_coefficients.csv"), digits = 3)
print(do.call(rbind, modC), digits = 3); print(round(aud, 3))
g <- grid[grid$vr %in% c(0.5, 0.7, 0.8, 0.9), c("vr", "sampling_h", "expected_spatial_r2", "gap_pi_lo", "gap_pi_hi")]
print(g[order(g$sampling_h, g$vr), ], digits = 3)
