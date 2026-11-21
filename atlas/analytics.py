"""Pure, observed-data-only transformations for the Atlas dashboard.

No synthetic observations, filling, interpolation, or imputed geography.
"""
from __future__ import annotations

import pandas as pd

CO2 = "co2_per_capita"


def build_panel(meta: pd.DataFrame, wb: dict[str, pd.DataFrame], owid: pd.DataFrame) -> pd.DataFrame:
    """Outer-join real country-year observations, then keep official country metadata.

    Missing observations remain NaN; no fabricated values are generated.
    """
    if not wb:
        raise ValueError("At least one World Bank indicator is required")
    if meta.duplicated("iso3").any():
        raise ValueError("Duplicate country metadata identifiers")
    frames = []
    for code, frame in wb.items():
        if frame.duplicated(["iso3", "year"]).any():
            raise ValueError(f"Duplicate country-year observations for {code}")
        frames.append(frame[["iso3", "year", "value"]].rename(columns={"value": code}).set_index(["iso3", "year"]))
    panel = pd.concat(frames, axis=1, join="outer").reset_index()
    if owid.duplicated(["iso3", "year"]).any():
        raise ValueError("Duplicate OWID country-year observations")
    carbon = owid[["iso3", "year", "value"]].rename(columns={"value": CO2})
    panel = panel.merge(carbon, on=["iso3", "year"], how="outer", validate="one_to_one")
    panel = panel.merge(meta, on="iso3", how="inner", validate="many_to_one")
    panel = panel[panel["year"].between(1990, 2026)].copy()
    if panel.empty:
        raise ValueError("No valid real-world observations after country matching")
    panel["year"] = panel["year"].astype(int)
    return panel.sort_values(["year", "iso3"]).reset_index(drop=True)


def best_coverage_year(panel: pd.DataFrame, metric: str, threshold: float = 0.8) -> int:
    """Latest observed year covering at least threshold of maximum annual coverage."""
    coverage = panel.loc[panel[metric].notna()].groupby("year")["iso3"].nunique()
    if coverage.empty:
        raise ValueError(f"No observed data for {metric}")
    candidate_years = coverage[coverage >= coverage.max() * threshold]
    return int(candidate_years.index.max())


def indexed_comparison(panel: pd.DataFrame, metric: str, base_year: int) -> pd.DataFrame:
    """Return indexed (base=100) observations only for countries with real baseline."""
    observed = panel.loc[panel[metric].notna(), ["iso3", "country", "year", metric]].copy()
    baseline = observed.loc[observed.year.eq(base_year), ["iso3", metric]].rename(columns={metric: "baseline"})
    baseline = baseline[baseline.baseline.ne(0)]
    result = observed.merge(baseline, on="iso3", how="inner", validate="many_to_one")
    result["index"] = 100 * result[metric] / result["baseline"]
    return result


def annual_change(panel: pd.DataFrame, metric: str, year: int) -> pd.DataFrame:
    """Compute year-over-year changes only from two actually observed adjacent years."""
    now = panel.loc[panel.year.eq(year) & panel[metric].notna(), ["iso3", "country", metric]]
    prev = panel.loc[panel.year.eq(year - 1) & panel[metric].notna(), ["iso3", metric]]
    prev = prev.rename(columns={metric: "previous"})
    paired = now.merge(prev, on="iso3", validate="one_to_one")
    paired = paired.loc[paired.previous.ne(0)].copy()
    paired["change_pct"] = 100 * (paired[metric] / paired.previous - 1)
    return paired


def coverage_by_year(panel: pd.DataFrame, metric: str) -> pd.DataFrame:
    return (panel.loc[panel[metric].notna()].groupby("year")["iso3"]
            .nunique().rename("countries").reset_index())
