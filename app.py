"""Interactive World Bank + OWID geographic analytics. No simulated observations."""
import pandas as pd
import plotly.express as px
import streamlit as st

from atlas.data import INDICATORS, countries, indicator, co2_per_capita, combine

st.set_page_config(page_title='Global Development Atlas', page_icon='🌍', layout='wide')
st.markdown('''<style>
.stApp{background:linear-gradient(130deg,#080e1c,#111e32 60%,#0b1423);color:#e8f1fc}
.block-container{max-width:1500px;padding-top:2rem}
[data-testid="stMetric"]{background:#172840;border:1px solid #294766;border-radius:16px;padding:16px}
h1{letter-spacing:-.045em!important;font-weight:800!important}
</style>''', unsafe_allow_html=True)
st.caption('WORLD DATA LAB  /  VERIFIED PUBLIC OBSERVATIONS')
st.title('🌍 Global Development Atlas')
st.markdown('**Economies, people and emissions — one connected geographic intelligence workspace.**')


@st.cache_data(ttl=86400, show_spinner='Retrieving real-world observations…')
def load():
    return countries(), {code: indicator(code) for code in INDICATORS}, co2_per_capita()


try:
    meta, wb, owid = load()
except Exception as exc:
    st.error(f'Live data could not be retrieved: {exc}')
    st.info(
        'This application deliberately does not fall back to synthetic or fabricated data. '
        'Check internet connectivity and source availability.'
    )
    st.stop()

with st.sidebar:
    st.header('Explore the data')
    code = st.selectbox(
        'World Bank indicator',
        list(INDICATORS),
        format_func=lambda x: INDICATORS[x],
    )
    mode = st.radio('Geographic metric', ['World Bank indicator', 'CO₂ per capita'])
    st.caption('CO₂ data: Our World in Data · GDP and development: World Bank')

try:
    df = combine(meta, wb[code], owid)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

all_years = sorted(df.year.unique().tolist())
with st.sidebar:
    year = st.select_slider('Year', options=all_years, value=all_years[-1])
    regions = st.multiselect(
        'Regions', sorted(df.region.unique()), default=sorted(df.region.unique())
    )
    selected = st.multiselect(
        'Compare countries',
        sorted(df.country.unique()),
        default=[
            c for c in ['Pakistan', 'India', 'United States', 'China', 'Germany']
            if c in df.country.unique()
        ],
    )
    st.caption(
        f'Actual joined observations: {len(df):,} country-years · '
        f'{df.iso3.nunique()} countries · {df.year.min()}–{df.year.max()}'
    )

subset = df[df.region.isin(regions)]
current = subset[subset.year.eq(year)]
metric = 'value_wb' if mode == 'World Bank indicator' else 'value_co2'
label = INDICATORS[code] if mode == 'World Bank indicator' else 'CO₂ per capita (tonnes)'
if current.empty:
    st.warning('No observations match these filters.')
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric('COUNTRIES IN VIEW', f'{current.iso3.nunique():,}')
c2.metric('OBSERVED COUNTRY-YEARS', f'{len(subset):,}')
c3.metric('LATEST SELECTED YEAR', str(year))
c4.metric('REGIONS COVERED', str(current.region.nunique()))

st.subheader('Geographic intelligence')
fig = px.choropleth(
    current, locations='iso3', color=metric, hover_name='country',
    color_continuous_scale='Tealgrn', projection='natural earth',
    labels={metric: label}, template='plotly_dark',
)
fig.update_layout(
    height=510, margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor='rgba(0,0,0,0)',
    geo=dict(bgcolor='rgba(0,0,0,0)', showframe=False),
)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns([1.35, 1])
with left:
    st.subheader('Historical trajectories')
    trends = subset[subset.country.isin(selected)]
    if trends.empty:
        st.info('Select countries in the sidebar to compare trends.')
    else:
        line = px.line(
            trends, x='year', y=metric, color='country', markers=False,
            labels={metric: label, 'year': 'Year'}, template='plotly_dark',
        )
        line.update_layout(height=390, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(line, use_container_width=True)
with right:
    st.subheader('Economic / environmental relationship')
    scatter = px.scatter(
        current, x='value_wb', y='value_co2', color='region',
        hover_name='country',
        labels={
            'value_wb': INDICATORS[code],
            'value_co2': 'CO₂ per capita (tonnes)',
        },
        template='plotly_dark',
    )
    scatter.update_layout(height=390, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(scatter, use_container_width=True)

st.subheader('Observed records and export')
st.dataframe(
    current[['country', 'iso3', 'region', 'income', 'year', 'value_wb', 'value_co2']]
    .sort_values('country'),
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    'Download filtered, joined observations (CSV)',
    subset.to_csv(index=False).encode(),
    file_name='development_atlas_real_observations.csv',
    mime='text/csv',
)
st.caption(
    'Source provenance: World Bank Indicators API and Our World in Data Grapher. '
    'Values are observed/published series; missing pairs are excluded, not invented. '
    'The inner join may reduce country-year coverage.'
)
