import pandas as pd
import pytest
from atlas.data import combine, indicator, co2_per_capita
from unittest.mock import patch, Mock


def test_join_requires_same_country_and_year():
    meta = pd.DataFrame([
        {'iso3':'PAK','country':'Pakistan','region':'South Asia','income':'Lower middle income'}
    ])
    wb = pd.DataFrame([
        {'iso3':'PAK','year':2020,'value':100.0},
        {'iso3':'PAK','year':2021,'value':120.0},
    ])
    owid = pd.DataFrame([{'iso3':'PAK','year':2021,'value':1.2}])
    result = combine(meta, wb, owid)
    assert len(result) == 1 and result.iloc[0].year == 2021
    assert result.iloc[0].value_wb == 120.0


def test_duplicate_keys_rejected():
    meta = pd.DataFrame([{'iso3':'PAK','country':'Pakistan'}])
    wb = pd.DataFrame([{'iso3':'PAK','year':2020,'value':1}]*2)
    owid = pd.DataFrame([{'iso3':'PAK','year':2020,'value':2}])
    with pytest.raises(ValueError, match='not unique'):
        combine(meta, wb, owid)


def test_unsupported_indicator_rejected():
    with pytest.raises(ValueError, match='Unsupported'):
        indicator('NOT.REAL')


def test_wb_rejects_unexpected_payload():
    from atlas.data import get_json
    with patch('atlas.data.requests.get',
               return_value=Mock(json=lambda: {'bad':'payload'})):
        with pytest.raises(ValueError, match='Unexpected'):
            get_json('https://example.org', {})


def test_owid_contract_rejects_missing_fields():
    with patch('atlas.data.requests.get',
               return_value=Mock(content=b'country,year,co2\nPakistan,2020,1\n')):
        with pytest.raises(ValueError, match='contract'):
            co2_per_capita()


def test_owid_url_matches_published_grapher_slug():
    from atlas.data import OWID
    assert OWID == 'https://ourworldindata.org/grapher/co-emissions-per-capita.csv'


def test_owid_accepts_real_grapher_csv_schema_and_excludes_aggregates():
    csv = (
        'Entity,Code,Year,Annual CO₂ emissions (per capita)\n'
        'Pakistan,PAK,2022,0.95\n'
        'World,OWID_WRL,2022,4.9\n'
        'Germany,DEU,2022,7.6\n'
    ).encode('utf-8')
    with patch('atlas.data.requests.get', return_value=Mock(content=csv)):
        result = co2_per_capita()
    assert set(result.iso3) == {'PAK', 'DEU'}
    assert len(result) == 2
    assert result.loc[result.iso3.eq('PAK'), 'value'].iloc[0] == 0.95
