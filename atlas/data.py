"""Reproducible, real-source data integration; no simulated analytical observations."""
from __future__ import annotations

import io
import pandas as pd
import requests

WB = 'https://api.worldbank.org/v2'
OWID = 'https://ourworldindata.org/grapher/co2-per-capita.csv'
INDICATORS = {
    'NY.GDP.MKTP.CD': 'GDP (current USD)',
    'SP.POP.TOTL': 'Population',
    'NY.GDP.PCAP.CD': 'GDP per capita (USD)',
    'SP.DYN.LE00.IN': 'Life expectancy (years)',
    'EG.ELC.RNEW.ZS': 'Renewable electricity (%)',
}


def get_json(url: str, params: dict) -> list:
    response = requests.get(url, params=params, timeout=45)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or len(data) != 2 or not isinstance(data[0], dict):
        raise ValueError('Unexpected World Bank response')
    return data


def countries() -> pd.DataFrame:
    records = []
    page = 1
    while True:
        metadata, rows = get_json(
            f'{WB}/country',
            {'format': 'json', 'per_page': 300, 'page': page},
        )
        records.extend(rows or [])
        if page >= int(metadata['pages']):
            break
        page += 1
    result = pd.DataFrame([
        {
            'iso3': r['id'],
            'country': r['name'],
            'region': r['region']['value'],
            'income': r['incomeLevel']['value'],
        }
        for r in records if r['region']['value'] != 'Aggregates'
    ])
    if result.empty or result.iso3.duplicated().any():
        raise ValueError('Country metadata missing or duplicated')
    return result


def indicator(code: str, start: int = 1990) -> pd.DataFrame:
    if code not in INDICATORS:
        raise ValueError('Unsupported indicator')
    records = []
    page = 1
    while True:
        metadata, rows = get_json(
            f'{WB}/country/all/indicator/{code}',
            {'format': 'json', 'date': f'{start}:2026', 'per_page': 20000, 'page': page},
        )
        records.extend(rows or [])
        if page >= int(metadata['pages']):
            break
        page += 1
    df = pd.DataFrame([
        {'iso3': r['countryiso3code'], 'year': int(r['date']), 'value': r['value']}
        for r in records
        if r.get('countryiso3code') and r.get('value') is not None
    ])
    if df.empty:
        raise ValueError(f'No observed records for {code}')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])
    if df.duplicated(['iso3', 'year']).any():
        raise ValueError(f'Duplicate country-year for {code}')
    return df


def co2_per_capita() -> pd.DataFrame:
    response = requests.get(OWID, timeout=60)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content))
    required = {'Entity', 'Code', 'Year'}
    if not required.issubset(df.columns):
        raise ValueError('OWID column contract changed')
    measures = [c for c in df.columns if c not in required]
    if len(measures) != 1:
        raise ValueError('OWID measure column ambiguous')
    result = df.rename(
        columns={'Code': 'iso3', 'Year': 'year', measures[0]: 'value'}
    )[['iso3', 'year', 'value']]
    result = result[result.iso3.astype(str).str.fullmatch(r'[A-Z]{3}')].copy()
    result['value'] = pd.to_numeric(result['value'], errors='coerce')
    result = result.dropna(subset=['value'])
    if result.duplicated(['iso3', 'year']).any():
        raise ValueError('Duplicate OWID country-year')
    if result.empty:
        raise ValueError('OWID data is empty')
    return result


def combine(meta: pd.DataFrame, wb: pd.DataFrame, owid: pd.DataFrame) -> pd.DataFrame:
    if wb.duplicated(['iso3', 'year']).any() or owid.duplicated(['iso3', 'year']).any():
        raise ValueError('Input country-year key not unique')
    joined = wb.merge(
        owid, on=['iso3', 'year'], how='inner',
        suffixes=('_wb', '_co2'), validate='one_to_one',
    )
    joined = joined.merge(meta, on='iso3', how='inner', validate='many_to_one')
    if joined.empty:
        raise ValueError('No overlapping real-world country-year observations')
    return joined
