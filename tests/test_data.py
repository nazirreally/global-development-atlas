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
