import pandas as pd
import pytest

from atlas.analytics import (
    CO2, annual_change, best_coverage_year, build_panel, coverage_by_year,
    indexed_comparison,
)


def _sources():
    meta = pd.DataFrame([
        {'iso3':'PAK','country':'Pakistan','region':'South Asia','income':'Lower middle income'},
        {'iso3':'DEU','country':'Germany','region':'Europe & Central Asia','income':'High income'},
    ])
    wb = {'metric':pd.DataFrame([
        {'iso3':'PAK','year':2020,'value':10.0},
        {'iso3':'PAK','year':2021,'value':12.0},
        {'iso3':'DEU','year':2020,'value':40.0},
    ])}
    owid = pd.DataFrame([
        {'iso3':'PAK','year':2021,'value':1.0},
        {'iso3':'DEU','year':2021,'value':8.0},
    ])
    return meta, wb, owid


def test_panel_preserves_unmatched_observations_without_filling():
    panel = build_panel(*_sources())
    assert len(panel) == 4
    assert panel.loc[panel.iso3.eq('DEU') & panel.year.eq(2021), 'metric'].isna().all()
    assert panel.loc[panel.iso3.eq('DEU') & panel.year.eq(2020), CO2].isna().all()


def test_rejects_duplicate_country_year_observations():
    meta, wb, owid = _sources()
    wb['metric'] = pd.concat([wb['metric'], wb['metric'].iloc[:1]])
    with pytest.raises(ValueError, match='Duplicate'):
        build_panel(meta, wb, owid)


def test_best_coverage_year_uses_later_eligible_year():
    panel = build_panel(*_sources())
    assert best_coverage_year(panel, 'metric', threshold=.5) == 2021
    assert best_coverage_year(panel, 'metric', threshold=.8) == 2020


def test_indexed_comparison_requires_observed_baseline():
    panel = build_panel(*_sources())
    result = indexed_comparison(panel, 'metric', 2020)
    assert result.loc[result.iso3.eq('PAK') & result.year.eq(2021), 'index'].iloc[0] == 120
    assert not result[result.iso3.eq('DEU') & result.year.eq(2021)].shape[0]


def test_annual_change_uses_only_adjacent_observed_years():
    panel = build_panel(*_sources())
    change = annual_change(panel, 'metric', 2021)
    assert list(change.iso3) == ['PAK']
    assert round(change.change_pct.iloc[0]) == 20


def test_coverage_excludes_missing_values():
    panel = build_panel(*_sources())
    observed = coverage_by_year(panel, 'metric')
    assert dict(zip(observed.year, observed.countries)) == {2020:2, 2021:1}
