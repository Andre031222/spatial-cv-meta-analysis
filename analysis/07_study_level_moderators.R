suppressPackageStartupMessages({ library(metafor) })
sl <- read.csv("extraction/study_level.csv", stringsAsFactors = FALSE, na.strings = c("NA", ""))
num <- function(v) suppressWarnings(as.numeric(v))
sl$n_obs <- num(sl$n_observations)
sl$n_class <- cut(sl$n_obs, c(0, 200, 1000, 5000, 50000, Inf), labels = c("<200", "200-1k", "1k-5k", "5k-50k", ">50k"), right = FALSE)
src <- c(in_situ_samples = "Field samples", monitoring_stations = "Monitoring stations", remote_sensing_labels = "Remote-sensing labels",
         survey_inventory = "Surveys/inventories", gridded_product = "Gridded products", compiled_database = "Compiled databases",
         occurrence_records = "Occurrence records", mixed = "Mixed", simulated = "Simulated")
sl$source_h <- unname(src[sl$data_source])
sl$random_h <- ifelse(sl$random_cv_scheme %in% c("kfold", "repeated_kfold", "nested_kfold"), "k-fold",
               ifelse(sl$random_cv_scheme == "holdout_split", "Hold-out split",
               ifelse(sl$random_cv_scheme %in% c("LOO", "OOB"), "LOO/OOB", NA)))
sl$split_h <- ifelse(sl$random_cv_scheme == "holdout_split" & num(sl$random_train_pct) %in% c(70, 75, 80),
                     paste0(num(sl$random_train_pct), "/", 100 - num(sl$random_train_pct)), NA)
sl$k_h <- ifelse(sl$random_h == "k-fold" & num(sl$random_k) %in% c(5, 10), paste0(num(sl$random_k), "-fold"), NA)
sl$scale_h <- ifelse(sl$spatial_scale %in% c("field", "local"), "Field/local",
              ifelse(sl$spatial_scale == "regional", "Regional",
              ifelse(sl$spatial_scale == "national", "National", ifelse(sl$spatial_scale %in% c("continental", "global"), "Continental/global", NA))))
sl$geom_h <- ifelse(sl$data_geometry %in% c("points", "raster_pixels", "polygons"), sl$data_geometry, NA)
sl$continent_h <- ifelse(sl$continent %in% c("Asia", "Europe", "North America", "South America", "Africa", "Oceania"), sl$continent, ifelse(sl$continent %in% c("Global", "Multiple"), "Global/multiple", NA))
sl$block_just <- ifelse(sl$block_size_justified %in% c("autocorrelation_range", "expert_choice", "not_justified"), sl$block_size_justified, NA)

mods <- c(source_h = "Data source", geom_h = "Data geometry", scale_h = "Spatial scale", random_h = "Random-CV scheme",
          split_h = "Hold-out proportion", k_h = "Number of folds", random_stratified = "Stratified random CV",
          block_just = "Block size justified by", n_class = "Number of observations", continent_h = "Continent")
out <- list()
for (eff in c("dR2", "lnRR_RMSE", "dAUC", "dAccuracy")) {
  e <- read.csv(sprintf("analysis/results/effects_%s.csv", eff))
  e <- merge(e, sl, by.x = "study", by.y = "record_id", all.x = TRUE)
  for (mv in names(mods)) {
    x <- e[!is.na(e[[mv]]), ]
    keep <- names(which(tapply(x$study, x[[mv]], function(s) length(unique(s))) >= 3))
    x <- x[x[[mv]] %in% keep, ]
    if (length(unique(x[[mv]])) < 2) next
    x$lvl <- factor(x[[mv]])
    m0 <- try(rma.mv(yi, vi, mods = ~ 0 + lvl, random = ~ 1 | study / es_id, data = x, method = "REML", sparse = TRUE), silent = TRUE)
    m1 <- try(rma.mv(yi, vi, mods = ~ lvl, random = ~ 1 | study / es_id, data = x, method = "REML", sparse = TRUE), silent = TRUE)
    if (inherits(m0, "try-error")) next
    lv <- sub("^lvl", "", rownames(m0$b))
    out[[paste(eff, mv)]] <- data.frame(effect = eff, moderator = mods[[mv]], level = lv, estimate = m0$b[, 1],
      ci_lb = m0$ci.lb, ci_ub = m0$ci.ub, k_studies = sapply(lv, function(l) length(unique(x$study[x$lvl == l]))),
      k_effects = sapply(lv, function(l) sum(x$lvl == l)), p_between = if (inherits(m1, "try-error")) NA else m1$QMp)
  }
}
res <- do.call(rbind, out)
write.csv(res, "analysis/results/study_level_moderators.csv", row.names = FALSE)

tab <- function(v, name) { t <- table(v, useNA = "no"); data.frame(variable = name, level = names(t), studies = as.vector(t), share = as.vector(t) / sum(t)) }
desc <- rbind(tab(sl$task, "Task"), tab(sl$source_h, "Data source"), tab(sl$data_geometry, "Data geometry"), tab(sl$spatial_scale, "Spatial scale"),
              tab(sl$continent, "Continent"), tab(unlist(strsplit(gsub(",", ";", sl$country_iso3[!is.na(sl$country_iso3) & !grepl("GLOBAL|MULTI", sl$country_iso3)]), ";")), "Country (ISO3)"), tab(sl$random_cv_scheme, "Random-CV scheme"), tab(sl$random_k, "Random k"),
              tab(ifelse(is.na(num(sl$random_train_pct)), NA, paste0(num(sl$random_train_pct), "/", 100 - num(sl$random_train_pct))), "Hold-out split"),
              tab(sl$random_stratified, "Stratified"), tab(sl$spatial_cv_scheme, "Spatial-CV scheme"), tab(sl$block_size_justified, "Block size justified"),
              tab(sl$independent_test, "Independent test"), tab(sl$class_balance, "Class balance"), tab(as.character(sl$n_class), "Observations"))
write.csv(desc, "analysis/results/validation_practice_profile.csv", row.names = FALSE)
q <- quantile(sl$n_obs, c(.1, .25, .5, .75, .9), na.rm = TRUE)
cat("n observations quantiles:", round(q), " | studies with n:", sum(!is.na(sl$n_obs)), "\n")
print(res[res$effect %in% c("dR2", "lnRR_RMSE"), c("effect", "moderator", "level", "estimate", "ci_lb", "ci_ub", "k_studies", "p_between")], digits = 3, row.names = FALSE)
