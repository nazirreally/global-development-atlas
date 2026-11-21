# Independent R analysis of real World Bank observations.
# Requirements: install.packages(c("jsonlite", "dplyr", "ggplot2"))
# Run from repository root: Rscript r/geospatial_analysis.R
suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(ggplot2)
})
url <- 'https://api.worldbank.org/v2/country/all/indicator/SP.DYN.LE00.IN?format=json&per_page=20000&date=1990:2026'
raw <- fromJSON(url, flatten=TRUE)
if (length(raw) != 2 || is.null(raw[[2]])) stop('Data source unavailable; no synthetic fallback')
observations <- raw[[2]]
stopifnot(all(c('countryiso3code', 'date', 'value') %in% names(observations)))
df <- observations %>%
  transmute(iso3=countryiso3code, year=as.integer(date), life_expectancy=as.numeric(value)) %>%
  filter(grepl('^[A-Z]{3}$', iso3), !is.na(life_expectancy))
if (nrow(df) == 0) stop('No genuine observations retrieved')
if (anyDuplicated(df[c('iso3','year')])) stop('Duplicate country-year records')
latest <- df %>% group_by(iso3) %>%
  slice_max(year, n=1, with_ties=FALSE) %>% ungroup()
plot <- ggplot(latest, aes(x=life_expectancy)) +
  geom_histogram(bins=32, fill='#2dd4bf', color='#0c1728') +
  labs(
    title='Latest reported life expectancy by country',
    subtitle='Real World Bank published observations; reporting years vary',
    x='Years', y='Countries'
  ) +
  theme_minimal(base_size=13)
dir.create('outputs', showWarnings=FALSE)
ggsave('outputs/life_expectancy_distribution.png', plot, width=11, height=6, dpi=160)
write.csv(latest, 'outputs/life_expectancy_observed.csv', row.names=FALSE)
cat(sprintf('Processed %d real observations across %d countries\n',
            nrow(df), n_distinct(df$iso3)))
