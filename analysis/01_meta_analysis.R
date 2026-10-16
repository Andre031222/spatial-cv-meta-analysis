suppressPackageStartupMessages({ library(metafor); library(clubSandwich) })

dir.create("analysis/results/figures", recursive = TRUE, showWarnings = FALSE)
d <- read.csv("extraction/extraction_template.csv", stringsAsFactors = FALSE, na.strings = c("NA", ""))
ft <- read.csv("fulltext/fulltext_decisions.csv", stringsAsFactors = FALSE)
d <- d[d$primary == "yes" & d$record_id %in% ft$record_id[ft$ft_decision == "include"], ]
d$value_random  <- as.numeric(d$value_random)
d$value_spatial <- as.numeric(d$value_spatial)
d <- d[!is.na(d$value_random) & !is.na(d$value_spatial), ]
pct <- d$metric %in% c("R2", "AUC", "accuracy", "balanced_accuracy", "F1", "kappa", "TSS", "CCC") &
       (d$value_random > 1.5 | d$value_spatial > 1.5)
d$rescaled_from_percent <- pct
d$value_random[pct] <- d$value_random[pct] / 100; d$value_spatial[pct] <- d$value_spatial[pct] / 100
cat("Rows rescaled from percent:", sum(pct), "\n")
d$n <- suppressWarnings(as.numeric(d$n_samples))
d$n_imputed <- is.na(d$n) | d$n < 10
d$n[d$n_imputed] <- median(d$n[!d$n_imputed], na.rm = TRUE)
d$study <- d$record_id
d$es_id <- seq_len(nrow(d))
d$digitised_flag <- !is.na(d$digitised) & d$digitised == "yes"

dom <- tolower(d$domain)
d$domain_h <- ifelse(grepl("soil", dom), "soil",
              ifelse(grepl("crop|yield|agri", dom), "crop",
              ifelse(grepl("biomass|forest|canopy|tree", dom), "forest_biomass",
              ifelse(grepl("veg|land|cover|lulc", dom), "vegetation_landcover",
              ifelse(grepl("species|sdm|biodiv", dom), "species",
              ifelse(grepl("hydro|water|flood|groundwater", dom), "hydrology",
              ifelse(grepl("climat|air|temp|pm|ozone|no2|pollut|precip", dom), "climate_air",
              ifelse(grepl("hazard|landslide|fire|erosion|gully", dom), "hazards", "other"))))))))
mod <- tolower(d$model)
d$model_h <- ifelse(grepl("^rf|random", mod), "RF",
             ifelse(grepl("xgb|gbm|boost|lightgbm|catboost|brt", mod), "boosting",
             ifelse(grepl("cnn|ann|mlp|deep|lstm|neural|gnn|unet|transformer", mod), "neural_net",
             ifelse(grepl("svm|svr|support", mod), "SVM", "other_ML"))))
d$sampling_h <- ifelse(d$sampling_design %in% c("clustered", "probability_random", "regular_grid"), d$sampling_design, "unknown")
cvt <- tolower(d$spatial_cv_type)
d$cv_h <- ifelse(grepl("block", cvt), "block",
          ifelse(grepl("buffer", cvt), "buffer_LOO",
          ifelse(grepl("leave|location|site|region|field", cvt), "leave_location_out",
          ifelse(grepl("cluster", cvt), "cluster", "other"))))

clip <- function(x, lo, hi) pmin(pmax(x, lo), hi)
var_r2  <- function(r2, n) { r <- clip(r2, 0.001, 0.999); 4 * r * (1 - r)^2 / n }
var_auc <- function(a, n) { a <- clip(a, 0.501, 0.999); n1 <- n / 2; n2 <- n / 2
  q1 <- a / (2 - a); q2 <- 2 * a^2 / (1 + a)
  (a * (1 - a) + (n1 - 1) * (q1 - a^2) + (n2 - 1) * (q2 - a^2)) / (n1 * n2) }

es <- list()
r2 <- d[d$metric == "R2", ]
r2$yi <- r2$value_random - r2$value_spatial
r2$vi <- var_r2(r2$value_random, r2$n) + var_r2(r2$value_spatial, r2$n)
es$dR2 <- r2
rm <- d[d$metric == "RMSE" & d$value_random > 0 & d$value_spatial > 0, ]
rm$yi <- log(rm$value_spatial / rm$value_random)
rm$vi <- 2 / (2 * (rm$n - 1))
es$lnRR_RMSE <- rm
au <- d[d$metric == "AUC", ]
au$yi <- au$value_random - au$value_spatial
au$vi <- var_auc(au$value_random, au$n) + var_auc(au$value_spatial, au$n)
es$dAUC <- au
ac <- d[d$metric %in% c("accuracy", "balanced_accuracy"), ]
ac$yi <- ac$value_random - ac$value_spatial
ac$vi <- with(ac, clip(value_random, .01, .99) * (1 - clip(value_random, .01, .99)) / n +
                  clip(value_spatial, .01, .99) * (1 - clip(value_spatial, .01, .99)) / n)
es$dAccuracy <- ac

fit_ml <- function(x) rma.mv(yi, vi, random = ~ 1 | study / es_id, data = x, method = "REML", sparse = TRUE)
i2_ml <- function(m, x) {
  W <- diag(1 / x$vi); X <- model.matrix(m)
  P <- W - W %*% X %*% solve(t(X) %*% W %*% X) %*% t(X) %*% W
  tot <- sum(m$sigma2) + (m$k - m$p) / sum(diag(P))
  c(I2_total = 100 * sum(m$sigma2) / tot, I2_between = 100 * m$sigma2[1] / tot, I2_within = 100 * m$sigma2[2] / tot)
}
overall <- list(); mods <- list()
for (nm in names(es)) {
  x <- es[[nm]]
  if (length(unique(x$study)) < 3) next
  m <- fit_ml(x)
  rob <- coef_test(m, vcov = "CR2", cluster = x$study)
  pr <- predict(m)
  un <- rma.mv(yi, 1, random = ~ 1 | study / es_id, data = x, method = "REML")
  sens_n <- if (sum(!x$n_imputed) > 5 && length(unique(x$study[!x$n_imputed])) >= 3) fit_ml(x[!x$n_imputed, ]) else NULL
  xd <- x[!x$digitised_flag, ]
  sens_d <- if (length(unique(xd$study)) >= 3) fit_ml(xd) else NULL
  overall[[nm]] <- data.frame(effect = nm, k_effects = m$k, k_studies = length(unique(x$study)),
    estimate = m$b[1], ci_lb = m$ci.lb, ci_ub = m$ci.ub, pi_lb = pr$pi.lb, pi_ub = pr$pi.ub,
    p = m$pval, robust_se = rob$SE, robust_p = rob$p_Satt,
    tau2_between = m$sigma2[1], tau2_within = m$sigma2[2], t(i2_ml(m, x)),
    share_positive = mean(x$yi > 0), unweighted_estimate = un$b[1],
    estimate_without_imputed_n = if (is.null(sens_n)) NA else sens_n$b[1],
    estimate_without_digitised = if (is.null(sens_d)) NA else sens_d$b[1],
    ci_lb_without_digitised = if (is.null(sens_d)) NA else sens_d$ci.lb,
    ci_ub_without_digitised = if (is.null(sens_d)) NA else sens_d$ci.ub,
    k_studies_without_digitised = length(unique(xd$study)), k_effects_without_digitised = nrow(xd),
    share_effects_digitised = mean(x$digitised_flag))
  for (mv in c("sampling_h", "domain_h", "model_h", "cv_h", "task")) {
    xx <- x[!is.na(x[[mv]]), ]
    if (length(unique(xx[[mv]])) < 2) next
    mm <- try(rma.mv(yi, vi, mods = as.formula(paste("~ 0 +", mv)), random = ~ 1 | study / es_id,
                     data = xx, method = "REML", sparse = TRUE), silent = TRUE)
    if (inherits(mm, "try-error")) next
    tab <- data.frame(effect = nm, moderator = mv, level = sub(mv, "", rownames(mm$b)),
                      estimate = mm$b[, 1], ci_lb = mm$ci.lb, ci_ub = mm$ci.ub,
                      k_effects = as.vector(table(xx[[mv]])[sub(mv, "", rownames(mm$b))]),
                      k_studies = sapply(sub(mv, "", rownames(mm$b)), function(l) length(unique(xx$study[xx[[mv]] == l]))),
                      QM_p_heterogeneity_between_levels = NA)
    mt <- try(rma.mv(yi, vi, mods = as.formula(paste("~", mv)), random = ~ 1 | study / es_id, data = xx,
                     method = "REML", sparse = TRUE), silent = TRUE)
    if (!inherits(mt, "try-error")) tab$QM_p_heterogeneity_between_levels <- mt$QMp
    mods[[paste(nm, mv)]] <- tab
  }
  ln <- try(rma.mv(yi, vi, mods = ~ log(n), random = ~ 1 | study / es_id, data = x[!x$n_imputed, ],
                   method = "REML", sparse = TRUE), silent = TRUE)
  if (!inherits(ln, "try-error")) mods[[paste(nm, "logn")]] <- data.frame(effect = nm, moderator = "log(n)",
    level = "slope", estimate = ln$b[2], ci_lb = ln$ci.lb[2], ci_ub = ln$ci.ub[2], k_effects = ln$k,
    k_studies = length(unique(x$study[!x$n_imputed])), QM_p_heterogeneity_between_levels = ln$QMp)
  eg <- try(rma.mv(yi, vi, mods = ~ sqrt(vi), random = ~ 1 | study / es_id, data = x, method = "REML", sparse = TRUE), silent = TRUE)
  if (!inherits(eg, "try-error")) overall[[nm]]$egger_slope_p <- eg$pval[2]
  agg <- aggregate(cbind(yi, vi) ~ study, data = x, FUN = mean)
  agg <- agg[order(agg$yi), ]
  png(sprintf("analysis/results/figures/forest_%s.png", nm), width = 1600, height = 300 + 28 * nrow(agg), res = 150)
  forest(agg$yi, agg$vi, slab = agg$study, xlab = nm, cex = 0.6, header = c("Study", "Estimate [95% CI]"))
  abline(v = m$b[1], lty = 2, col = "firebrick"); dev.off()
  png(sprintf("analysis/results/figures/funnel_%s.png", nm), width = 1200, height = 1000, res = 150)
  funnel(m, xlab = nm); dev.off()
}
res <- do.call(rbind, lapply(overall, function(z) { z[setdiff(c(names(overall[[1]]), "egger_slope_p"), names(z))] <- NA; z }))
write.csv(res, "analysis/results/overall_effects.csv", row.names = FALSE)
write.csv(do.call(rbind, mods), "analysis/results/moderators.csv", row.names = FALSE)
for (nm in names(es)) write.csv(es[[nm]][, c("study", "es_id", "metric", "model_h", "domain_h", "sampling_h", "cv_h", "n", "n_imputed", "value_random", "value_spatial", "yi", "vi")],
                               sprintf("analysis/results/effects_%s.csv", nm), row.names = FALSE)
print(res[, c("effect", "k_studies", "k_effects", "estimate", "ci_lb", "ci_ub", "pi_lb", "pi_ub", "robust_p", "I2_total", "unweighted_estimate")], digits = 3)
cat("\nModerators (sampling design):\n")
mm <- do.call(rbind, mods); print(mm[mm$moderator == "sampling_h", c("effect", "level", "estimate", "ci_lb", "ci_ub", "k_studies", "QM_p_heterogeneity_between_levels")], digits = 3)
