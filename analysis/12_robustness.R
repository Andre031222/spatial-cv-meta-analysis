suppressPackageStartupMessages({ library(metafor); library(clubSandwich) })
x <- read.csv("extraction/extraction_template.csv", stringsAsFactors = FALSE, na.strings = c("NA", ""))
x <- x[x$primary == "yes", ]
dig <- tapply(x$digitised == "yes", x$record_id, function(v) any(v, na.rm = TRUE))
smp <- tapply(x$sampling_design, x$record_id, function(v) v[1] != "unknown")
hq <- intersect(names(dig)[!dig], names(smp)[smp %in% TRUE])
fit <- function(e) {
  m <- rma.mv(yi, vi, random = ~ 1 | study / es_id, data = e, method = "REML", sparse = TRUE)
  r <- coef_test(m, vcov = "CR2", cluster = e$study)
  c(estimate = m$b[1], lo = m$b[1] - qt(.975, r$df_Satt) * r$SE, hi = m$b[1] + qt(.975, r$df_Satt) * r$SE, p = r$p_Satt,
    studies = length(unique(e$study)))
}
out <- list()
for (eff in c("dR2", "lnRR_RMSE")) {
  e <- read.csv(sprintf("analysis/results/effects_%s.csv", eff), stringsAsFactors = FALSE)
  full <- fit(e)
  h <- e[e$study %in% hq & !e$n_imputed, ]
  hqf <- fit(h)
  loso <- sapply(unique(e$study), function(s) fit(e[e$study != s, ])["estimate"])
  out[[eff]] <- data.frame(analysis = eff,
    full_estimate = full["estimate"], hq_estimate = hqf["estimate"], hq_lo = hqf["lo"], hq_hi = hqf["hi"], hq_p = hqf["p"],
    hq_studies = hqf["studies"], loso_min = min(loso), loso_max = max(loso), loso_n = length(loso))
}
summ <- function(v, s) { m <- lm(v ~ 1); r <- coef_test(m, vcov = "CR2", cluster = s)
  c(mean = mean(v), p = r$p_Satt) }
A <- read.csv("analysis/results/independent_validation_rows.csv", stringsAsFactors = FALSE)
A <- A[A$metric %in% c("R2", "accuracy", "AUC"), ]
st <- unique(A$record_id)
lr <- t(sapply(st, function(s) { d <- A[A$record_id != s, ]
  c(summ(d$opt_random, d$record_id), summ(d$opt_spatial, d$record_id), share = mean(d$abs_gap > 0)) }))
colnames(lr) <- c("rand_mean", "rand_p", "spat_mean", "spat_p", "share")
out$independent <- data.frame(analysis = "independent_tests_difference_scale",
  full_estimate = mean(A$opt_random), hq_estimate = NA, hq_lo = NA, hq_hi = NA, hq_p = NA, hq_studies = NA,
  loso_min = min(lr[, "rand_mean"]), loso_max = max(lr[, "rand_mean"]), loso_n = length(st))
ind <- data.frame(quantity = c("optimism_random", "optimism_spatial", "share_spatial_closer"),
  loso_min = c(min(lr[, "rand_mean"]), min(lr[, "spat_mean"]), min(lr[, "share"])),
  loso_max = c(max(lr[, "rand_mean"]), max(lr[, "spat_mean"]), max(lr[, "share"])),
  max_p = c(max(lr[, "rand_p"]), max(lr[, "spat_p"]), NA), min_p = c(min(lr[, "rand_p"]), min(lr[, "spat_p"]), NA))
res <- do.call(rbind, out)
write.csv(res, "analysis/results/robustness_pooled.csv", row.names = FALSE)
write.csv(ind, "analysis/results/robustness_independent_tests.csv", row.names = FALSE)
print(res, digits = 3, row.names = FALSE)
print(ind, digits = 3, row.names = FALSE)
