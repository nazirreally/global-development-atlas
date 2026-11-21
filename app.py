"""Global Development Atlas — interactive real-data country intelligence workbench."""
from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from atlas.analytics import (
    CO2, annual_change, best_coverage_year, build_panel, coverage_by_year,
    indexed_comparison,
)
from atlas.data import INDICATORS, countries, indicator, co2_per_capita

st.set_page_config(
    page_title="Global Development Atlas | Intelligence Studio",
    page_icon="🌍", layout="wide", initial_sidebar_state="expanded",
)

# Palette: ink / electric mint / restrained lilac / cyan. Plotly figures inherit these tokens.
INK = "#08111f"
PANEL = "#101e30"
GRID = "rgba(155,183,214,.12)"
TEXT = "#e7eef9"
MUTED = "#bacde0"
MINT = "#3de2c1"
PALETTE = ["#3de2c1", "#86adff", "#facd8d", "#bca6ff", "#9ae5ff", "#7cdecf"]
METRICS = {**INDICATORS, CO2: "CO₂ emissions per capita"}
SOURCES = {**{key: "World Bank" for key in INDICATORS}, CO2: "Our World in Data"}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--bg:#08111f;--panel:#111e31;--line:#334960;--mint:#3de2c1;--text:#edf6ff;--muted:#baccdf;--control:#12253a}
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(ellipse 900px 550px at 62% -10%,#163b45 0,transparent 72%),radial-gradient(ellipse 680px 600px at 0 30%,#152340 0,transparent 65%),var(--bg);color:var(--text)}
.block-container{padding-top:1.35rem;padding-bottom:3rem;max-width:1560px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0e192b,#0b1423)!important;border-right:1px solid #24354d}
[data-testid="stSidebar"] .block-container{padding-top:2rem}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p{color:#c9d8eb}
[data-testid="stSidebar"] hr{border-color:#26384f}
[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.04em!important}
h2{font-size:1.5rem!important;margin-bottom:.5rem!important}
h3{font-size:1.1rem!important}
.stTabs [data-baseweb="tab-list"]{gap:8px;background:#111f32;border:1px solid #263c50;border-radius:14px;padding:6px;margin-top:14px}
.stTabs [data-baseweb="tab"]{color:#c7d9e9!important;border-radius:10px;padding:11px 17px;font-weight:700;transition:background .2s,color .2s}
.stTabs [aria-selected="true"]{background:#1d3f4b!important;color:#89f6e2!important;box-shadow:inset 0 0 0 1px #347b75}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
[data-testid="stMetric"]{border:1px solid #263c50;background:#122238;border-radius:15px;padding:17px}
[data-testid="stMetricValue"]{color:#edf8ff}
[data-testid="stPlotlyChart"]{border:1px solid #23394e;background:rgba(14,27,44,.52);border-radius:18px;padding:10px 13px}
[data-testid="stDataFrame"]{border:1px solid #263b51;border-radius:12px;overflow:hidden}
div[data-testid="stButton"] button[kind="primary"],div[data-testid="stDownloadButton"] button{background:#3de2c1;color:#071723;border:none;border-radius:10px;font-weight:800}
div[data-testid="stButton"] button[kind="primary"]:hover,div[data-testid="stDownloadButton"] button:hover{background:#88ffdf;color:#071723}
[data-baseweb="select"]>div,[data-baseweb="input"]>div{background:#14263b;border-color:#31506a}
hr{border-color:#203349}
.hero{position:relative;overflow:hidden;display:flex;justify-content:space-between;gap:24px;align-items:center;background:linear-gradient(115deg,rgba(18,42,61,.97),rgba(16,27,48,.94) 70%,rgba(38,57,76,.8));border:1px solid #2c4b5e;border-radius:24px;padding:30px 36px;margin:4px 0 18px;box-shadow:0 18px 55px rgba(0,0,0,.17)}
.hero::after{content:'';position:absolute;right:-70px;top:-145px;width:390px;height:390px;border:1px solid rgba(61,226,193,.14);border-radius:50%;box-shadow:0 0 0 56px rgba(61,226,193,.035),0 0 0 112px rgba(61,226,193,.026);pointer-events:none}
.eyebrow{font-size:11px;letter-spacing:.19em;text-transform:uppercase;color:#67e7d0;font-weight:800;margin-bottom:13px}
.hero h1{font-size:clamp(2.1rem,3.5vw,3.65rem);line-height:1.08;color:#f4f9ff;margin:0 0 14px;letter-spacing:-.065em}
.hero h1 span{background:linear-gradient(90deg,#5defd0,#9bc8ff);background-clip:text;-webkit-background-clip:text;color:transparent}
.hero p{max-width:720px;color:#a9bfd4;font-size:14px;line-height:1.65;margin:0}
.hero-side{flex-shrink:0;z-index:1;display:flex;flex-direction:column;align-items:flex-end;gap:13px}
.live-badge{display:inline-flex;align-items:center;gap:9px;background:#143a38;border:1px solid #2a756b;border-radius:99px;padding:8px 13px;color:#9bf6e1;font-size:11px;font-weight:800;letter-spacing:.055em}
.dot{height:7px;width:7px;display:inline-block;background:#3de2c1;border-radius:99px;box-shadow:0 0 12px #3de2c1}
.hero-foot{font-size:11px;color:#b7c8db;text-align:right}
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:6px 0 16px}
.kpi{background:linear-gradient(150deg,#14273b,#0e1c2e);border:1px solid #294057;border-radius:17px;padding:20px 21px;min-height:124px;position:relative;overflow:hidden}
.kpi::before{content:'';position:absolute;top:0;left:0;width:36%;height:2px;background:#3de2c1;opacity:.8}
.kpi-label{color:#93adc4;font-size:10px;text-transform:uppercase;letter-spacing:.12em;font-weight:800}
.kpi-number{color:#f1f8ff;font-family:'Manrope',sans-serif;font-size:clamp(20px,2.2vw,30px);font-weight:800;letter-spacing:-.045em;margin-top:11px;line-height:1.12}
.kpi-note{font-size:11px;color:#8fa9bf;margin-top:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.section-eyebrow{color:#4fe3cb;font-weight:800;font-size:11px;letter-spacing:.18em;text-transform:uppercase;margin:9px 0 4px}
.section-heading{font-family:'Manrope',sans-serif;font-weight:800;font-size:23px;letter-spacing:-.045em;color:#eef7ff;margin:0 0 14px}
.small-pill{border-radius:8px;background:#163344;border:1px solid #31556a;display:inline-block;padding:6px 11px;font-size:11px;color:#91e9d9;margin:0 6px 8px 0}
.callout{background:#12263a;border:1px solid #315269;border-radius:14px;padding:15px 17px;color:#b2c8da;font-size:12px;line-height:1.7;margin-top:14px}
.sidebar-brand{font-family:'Manrope',sans-serif;font-weight:800;color:#e9f4ff;font-size:17px;letter-spacing:-.03em}
.sidebar-sub{font-size:10px;font-weight:800;color:#4fe3cb;letter-spacing:.18em;margin:5px 0 23px}
.sidebar-foot{font-size:11px;color:#b1c7db;line-height:1.7;margin-top:16px}
@media(max-width:900px){.hero{padding:24px}.hero-side{display:none}.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.kpi{padding:14px;min-height:112px}.hero h1{font-size:2rem}}

/* Studio 03: explicitly style native controls; Streamlit themes alone cannot override every BaseWeb default. */
.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stWidgetLabel"] label,
.stApp [data-testid="stSelectbox"] label,.stApp [data-testid="stMultiSelect"] label,
.stApp [data-testid="stRadio"] label,.stApp [data-testid="stSlider"] label,
.stApp [data-testid="stCheckbox"] label{color:#d5e5f4!important;font-size:13px!important;font-weight:600}
.stApp [data-testid="stCaptionContainer"],.stApp small,.stApp .stCaption{color:#b7cadc!important}
.stApp .stTabs [data-baseweb="tab"] :is(p,span){color:inherit!important;opacity:1!important}
.stApp .stTabs [data-baseweb="tab"]:hover{color:#f1fcff!important;background:#1d3548!important}
.stApp .stTabs [data-baseweb="tab"][aria-selected="true"] :is(p,span){color:#8ffbe4!important}
.stApp [data-baseweb="select"]>div,.stApp [data-baseweb="input"]>div,
.stApp [data-testid="stSelectbox"]>div>div,.stApp [data-testid="stMultiSelect"]>div>div{
 background:#142940!important;border:1px solid #355773!important;color:#eaf5ff!important;border-radius:11px!important;
 box-shadow:0 2px 12px rgba(0,0,0,.09)!important}
.stApp [data-baseweb="select"]>div:hover,.stApp [data-baseweb="input"]>div:hover{border-color:#3ca69e!important}
.stApp [data-baseweb="select"] input,.stApp [data-baseweb="input"] input,
.stApp [data-baseweb="select"] [data-testid="stMarkdownContainer"],
.stApp [data-baseweb="select"] [data-baseweb="select"]{color:#eaf6ff!important;caret-color:#55edcf!important}
.stApp [data-baseweb="select"] :is(span,svg){color:#eaf6ff}
.stApp [data-testid="stMultiSelect"] [data-baseweb="tag"],
.stApp [data-baseweb="tag"]{
 background:#16474c!important;border:1px solid #2d8b87!important;border-radius:7px!important;
 color:#c7fff1!important;box-shadow:none!important}
.stApp [data-baseweb="tag"] :is(span,svg){color:#ddfff6!important;fill:currentColor!important}
.stApp [data-baseweb="tag"] button:hover{background:#216563!important}
[data-baseweb="popover"] [role="listbox"],[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] ul{background:#15263b!important;color:#e8f5ff!important}
[data-baseweb="popover"] [role="option"]:hover{background:#214759!important}
.stApp [data-baseweb="slider"] [role="slider"]{
 background:#53e6cc!important;border:3px solid #0a2838!important;box-shadow:0 0 0 3px rgba(83,230,204,.25)!important}
.stApp [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){color:#75f3dc!important}
.stApp [data-testid="stRadio"] input{accent-color:#3de2c1!important}
.stApp [data-testid="stCheckbox"] input{accent-color:#3de2c1!important}
.stApp [data-testid="stAlert"]{border-radius:13px}
.stApp [data-testid="stDataFrame"],.stApp [data-testid="stDataEditor"]{background:#102338!important}
.stApp [data-testid="stPlotlyChart"]{border-color:#31475d!important;box-shadow:0 12px 38px rgba(0,0,0,.09)}
.stApp :is(button,input,select,textarea):focus-visible{outline:2px solid #5bebd0!important;outline-offset:2px}
.stApp a{color:#78e5de}
.stApp .small-pill{color:#b0f8e9!important}
.stApp .kpi-label{color:#b1cadf}
.stApp .kpi-note{color:#b2c8dc}
.stApp .hero p{color:#c0d0e3}
@media(max-width:650px){.stTabs [data-baseweb="tab"]{padding:9px!important;font-size:11px}.stApp [data-testid="stPlotlyChart"]{padding:4px!important}}
</style>""", unsafe_allow_html=True)


def style_chart(fig: go.Figure, height: int = 380, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans", color=TEXT, size=12),
        hoverlabel=dict(bgcolor="#132a3d", bordercolor="#4edcc9",
                        font=dict(family="DM Sans", size=13, color="#f4fcff"),
                        align="left", namelength=-1),
        hovermode="closest",
        margin=dict(l=16, r=16, t=22, b=24),
        colorway=PALETTE, showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, title_font=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, title_font=dict(color=MUTED))
    return fig


def chart(fig: go.Figure):
    st.plotly_chart(fig, use_container_width=True, theme=None,
                    config={"displaylogo": False, "responsive": True, "scrollZoom": True})


def format_value(value: float, metric: str) -> str:
    if pd.isna(value):
        return "—"
    if metric == "NY.GDP.MKTP.CD":
        for limit, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M")]:
            if abs(value) >= limit:
                return f"${value / limit:,.2f}{suffix}"
        return f"${value:,.0f}"
    if metric == "SP.POP.TOTL":
        if abs(value) >= 1e9:
            return f"{value / 1e9:,.2f}B"
        if abs(value) >= 1e6:
            return f"{value / 1e6:,.1f}M"
        return f"{value:,.0f}"
    if metric == "NY.GDP.PCAP.CD":
        return f"${value:,.0f}"
    if metric == "EG.ELC.RNEW.ZS":
        return f"{value:,.1f}%"
    if metric == "SP.DYN.LE00.IN":
        return f"{value:,.1f} yrs"
    return f"{value:,.2f} t"


def tooltip_rows(title: str, rows: list[tuple[str, str]]) -> str:
    """Generate clean Plotly hover templates from trusted, static field labels.

    Values must be Plotly customdata references, never externally sourced HTML.
    """
    lines = [f"<b>{escape(title)}</b>", "<span style='color:#a7c8dc'>━━━━━━━━━━━━━━━━</span>"]
    for label, reference in rows:
        lines.append(f"<b>{escape(label)}</b>: {reference}")
    return "<br>".join(lines) + "<extra></extra>"


def heading(kicker: str, title: str):
    st.markdown(
        f'<div class="section-eyebrow">{escape(kicker)}</div>'
        f'<div class="section-heading">{escape(title)}</div>',
        unsafe_allow_html=True,
    )


def kpis(cards: list[tuple[str, str, str]]):
    elements = [
        '<div class="kpi"><div class="kpi-label">' + escape(label) +
        '</div><div class="kpi-number">' + escape(value) +
        '</div><div class="kpi-note">' + escape(note) + '</div></div>'
        for label, value, note in cards
    ]
    st.markdown('<div class="kpi-grid">' + ''.join(elements) + '</div>', unsafe_allow_html=True)


@st.cache_data(ttl=86400, show_spinner="Loading verified World Bank and OWID sources…")
def load_real_data() -> pd.DataFrame:
    meta = countries()
    wb = {code: indicator(code) for code in INDICATORS}
    owid = co2_per_capita()
    return build_panel(meta, wb, owid)


st.markdown("""<div class="hero"><div>
<div class="eyebrow">◈ &nbsp; WORLD DATA LAB / INTELLIGENCE STUDIO 02</div>
<h1>Make sense of <span>our world.</span></h1>
<p>Explore the forces shaping countries and communities — economic growth,
health, energy, population and carbon emissions — through real, connected data.</p>
</div><div class="hero-side"><div class="live-badge"><span class="dot"></span> VERIFIED PUBLIC SOURCES</div>
<div class="hero-foot">World Bank &nbsp; / &nbsp; Our World in Data<br>1990—present · Country-year observations</div>
</div></div>""", unsafe_allow_html=True)

try:
    panel = load_real_data()
except Exception as exc:
    st.error(f"Data ingestion failed: {exc}")
    st.info("We do not replace unavailable observations with synthetic or fabricated data. "
            "Please verify the source APIs and refresh the app.")
    st.stop()

with st.sidebar:
    st.markdown('<div class="sidebar-brand">◈ &nbsp; ATLAS CONTROLS</div>'
                '<div class="sidebar-sub">BUILD YOUR DATA STORY</div>', unsafe_allow_html=True)
    primary = st.selectbox("Primary indicator", list(METRICS), index=2,
                           format_func=lambda x: METRICS[x])
    available = sorted(panel.loc[panel[primary].notna(), "year"].unique().tolist())
    year = st.select_slider("Reporting year", options=available,
                            value=best_coverage_year(panel, primary))
    st.markdown("---")
    all_regions = sorted(panel.region.dropna().unique().tolist())
    regions = st.multiselect("Regions", all_regions, default=all_regions)
    all_income = sorted(panel.income.dropna().unique().tolist())
    incomes = st.multiselect("Income groups", all_income, default=all_income)
    st.markdown("---")
    all_countries = sorted(panel.country.dropna().unique().tolist())
    preferred = [c for c in ("Pakistan", "India", "China", "United States", "Germany")
                 if c in all_countries]
    selected_countries = st.multiselect("Country comparison set", all_countries,
                                        default=preferred)
    st.markdown(
        '<div class="sidebar-foot">● All charts use observed data only.<br>'
        '● Unreported years stay missing.<br>● Publisher updates cached for 24h.</div>',
        unsafe_allow_html=True,
    )

scoped = panel[panel.region.isin(regions) & panel.income.isin(incomes)].copy()
observed = scoped.loc[scoped.year.eq(year) & scoped[primary].notna()].copy()
if scoped.empty:
    st.warning("No countries match the selected region and income filters. Try widening the filters.")
    st.stop()

valid_countries = scoped.iso3.nunique()
coverage_pct = 100 * observed.iso3.nunique() / valid_countries if valid_countries else 0
peak = observed.nlargest(1, primary)
peak_label = peak.country.iloc[0] if not peak.empty else "No observations"
change = annual_change(scoped, primary, year)
median_change = change.change_pct.median() if not change.empty else float("nan")
kpis([
    ("Countries reporting", f"{observed.iso3.nunique():,}", f"{coverage_pct:.0f}% of selected countries"),
    ("Observed median", format_value(observed[primary].median(), primary), "Unweighted country median"),
    ("Highest reported value", format_value(peak[primary].iloc[0], primary) if not peak.empty else "—", peak_label),
    ("Median annual change", f"{median_change:+.1f}%" if pd.notna(median_change) else "—",
     f"{len(change)} observed year-over-year pairs"),
])

st.markdown(f'<span class="small-pill">◉ &nbsp; {escape(METRICS[primary])}</span>'
            f'<span class="small-pill">◈ &nbsp; {year}</span>'
            f'<span class="small-pill">◌ &nbsp; {escape(SOURCES[primary])}</span>'
            f'<span class="small-pill">◎ &nbsp; {len(scoped):,} real country-year rows</span>',
            unsafe_allow_html=True)

overview, compare, relationships, lab = st.tabs([
    "◎  World explorer", "⌁  Country studio", "◈  Relationships", "▦  Data lab",
])

with overview:
    heading("01 / GEO INTELLIGENCE", "Explore the world through data")
    opt1, opt2, opt3 = st.columns([1.25, 1, 1])
    with opt1:
        map_mode = st.radio("Map visualization", ["Choropleth", "Proportional circles"],
                            horizontal=True)
    with opt2:
        projection = st.selectbox("Map projection", ["natural earth", "orthographic", "equirectangular"],
                                  format_func=lambda v: v.title())
    with opt3:
        scale = st.selectbox("Color palette", ["Mint / Cyan", "Electric Violet", "Amber / Coral"])
    gradients = {
        "Mint / Cyan": ["#142f48", "#198b98", "#49e5c5", "#b6ffdf"],
        "Electric Violet": ["#1c2550", "#6755a8", "#aa8fff", "#f1ddff"],
        "Amber / Coral": ["#453146", "#c46e6d", "#ffba78", "#ffe1ab"],
    }
    if not observed.empty:
        # Formatting is only for display; every number still comes from published observations.
        observed["hover_value"] = observed[primary].map(lambda v: format_value(v, primary))
        observed["hover_rank"] = observed[primary].rank(method="min", ascending=False).astype(int).map(
            lambda v: f"#{v:,} of {len(observed):,}"
        )
        observed["hover_co2"] = observed[CO2].map(
            lambda v: format_value(v, CO2) if pd.notna(v) else "Not reported"
        )
    if observed.empty:
        st.info("This year has no available observations in the chosen regions or income groups.")
    elif map_mode == "Choropleth":
        world = px.choropleth(
            observed, locations="iso3", color=primary, hover_name="country",
            custom_data=["region", "income", "year", "hover_value", "hover_rank", "hover_co2"],
            color_continuous_scale=gradients[scale],
            labels={primary: METRICS[primary]}, projection=projection,
        )
        world.update_traces(hovertemplate=tooltip_rows("%{hovertext}", [
            ("Selected indicator", "%{customdata[3]}"),
            ("Rank in view", "%{customdata[4]}"),
            ("Region", "%{customdata[0]}"),
            ("Income group", "%{customdata[1]}"),
            ("CO₂ per capita", "%{customdata[5]}"),
            ("Reporting year", "%{customdata[2]}"),
        ]))
        world.update_geos(
            showframe=False, showcoastlines=True, coastlinecolor="#364b62",
            showcountries=True, countrycolor="#15273b", showland=True,
            landcolor="#152437", showocean=True, oceancolor="#0a1627",
            bgcolor="rgba(0,0,0,0)",
        )
        world = style_chart(world, 530)
        world.update_layout(coloraxis_colorbar=dict(thickness=12, len=.7, outlinewidth=0))
        chart(world)
    else:
        circles = observed.loc[observed[primary].gt(0)].copy()
        if circles.empty:
            st.info("Proportional circles require strictly positive observations.")
        else:
            world = px.scatter_geo(
                circles, locations="iso3", size=primary, color=primary,
                hover_name="country", size_max=38, projection=projection,
                custom_data=["region", "income", "year", "hover_value", "hover_rank", "hover_co2"],
                color_continuous_scale=gradients[scale],
                labels={primary: METRICS[primary]},
            )
            world.update_traces(hovertemplate=tooltip_rows("%{hovertext}", [
                ("Selected indicator", "%{customdata[3]}"),
                ("Rank in view", "%{customdata[4]}"),
                ("Region", "%{customdata[0]}"),
                ("Income group", "%{customdata[1]}"),
                ("CO₂ per capita", "%{customdata[5]}"),
                ("Reporting year", "%{customdata[2]}"),
            ]))
            world.update_geos(
                showframe=False, showcoastlines=True, coastlinecolor="#364b62",
                showcountries=True, countrycolor="#1d3044", showland=True,
                landcolor="#152437", showocean=True, oceancolor="#0a1627",
                bgcolor="rgba(0,0,0,0)",
            )
            chart(style_chart(world, 530))
    left, right = st.columns([1.1, 1])
    with left:
        heading("02 / RANKINGS", "Country leaderboard")
        rank_direction = st.radio("Sort countries", ["Highest", "Lowest"], horizontal=True)
        top_n = st.slider("Countries displayed", 5, 25, 12)
        ranked = (observed.nsmallest(top_n, primary) if rank_direction == "Lowest"
                  else observed.nlargest(top_n, primary)).sort_values(primary)
        bars = px.bar(ranked, x=primary, y="country", color=primary,
                      orientation="h", color_continuous_scale=gradients[scale],
                      labels={primary: METRICS[primary], "country": ""},
                      custom_data=["hover_value", "region", "income", "hover_rank"],
                      hover_name="country")
        bars.update_traces(hovertemplate=tooltip_rows("%{y}", [
            ("Observed value", "%{customdata[0]}"),
            ("Rank", "%{customdata[3]}"),
            ("Region", "%{customdata[1]}"),
            ("Income group", "%{customdata[2]}"),
        ]))
        bars.update_layout(coloraxis_showscale=False)
        chart(style_chart(bars, 390, legend=False))
    with right:
        heading("03 / DISTRIBUTION", "Regional spread")
        spread = px.box(observed, x="region", y=primary, color="region",
                        points="outliers", color_discrete_sequence=PALETTE,
                        labels={"region": "Region", primary: METRICS[primary]})
        spread.update_xaxes(tickangle=-25)
        chart(style_chart(spread, 390, legend=False))

with compare:
    heading("04 / TIME SERIES", "Country comparison studio")
    c1, c2 = st.columns([1, 1])
    with c1:
        normalize = st.checkbox("Index countries to a common baseline (100)", value=False)
    with c2:
        historical_start = st.select_slider("Start year", options=available,
                                             value=available[max(0, len(available) - 21)])
    countries_for_trends = [c for c in selected_countries if c in scoped.country.unique()]
    trends = scoped.loc[scoped.country.isin(countries_for_trends)
                        & scoped.year.ge(historical_start) & scoped[primary].notna()].copy()
    if not countries_for_trends:
        st.info("Choose one or more countries in the sidebar to compare their observed trajectories.")
    else:
        if normalize:
            base_year = st.select_slider("Index baseline year", options=[y for y in available if y >= historical_start],
                                         value=historical_start)
            trends = indexed_comparison(trends, primary, base_year)
            ylabel = "Index (baseline = 100)"
            ycolumn = "index"
            if trends.empty:
                st.warning("None of the selected countries have a valid, nonzero observation at that baseline year.")
        else:
            ylabel = METRICS[primary]
            ycolumn = primary
        if not trends.empty:
            trends["hover_value"] = trends[ycolumn].map(
                lambda v: f"{v:,.1f} indexed" if normalize else format_value(v, primary)
            )
            timeline = px.line(trends, x="year", y=ycolumn, color="country", markers=True,
                               color_discrete_sequence=PALETTE,
                               labels={"year": "Year", ycolumn: ylabel, "country": "Country"},
                               custom_data=["country", "year", "hover_value"])
            timeline.update_traces(
                line=dict(width=3), marker=dict(size=5),
                hovertemplate=tooltip_rows("%{customdata[0]}", [
                    ("Year", "%{customdata[1]}"), ("Observed value", "%{customdata[2]}"),
                ]),
            )
            chart(style_chart(timeline, 480))
        heading("05 / MOMENTUM", "Actual year-over-year change")
        movements = annual_change(scoped.loc[scoped.country.isin(countries_for_trends)], primary, year)
        if movements.empty:
            st.info("No adjacent-year observations exist for these countries and this reporting year.")
        else:
            movements["direction"] = movements.change_pct.ge(0).map({True: "Up", False: "Down"})
            deltas = px.bar(movements.sort_values("change_pct"), x="country", y="change_pct",
                            color="direction", color_discrete_map={"Up": MINT, "Down": "#f88f9d"},
                            labels={"change_pct": "Change (%)", "country": "Country"})
            chart(style_chart(deltas, 330, legend=False))

with relationships:
    heading("06 / MULTI-VARIATE RESEARCH", "Discover patterns between indicators")
    r1, r2, r3 = st.columns(3)
    with r1:
        x_metric = st.selectbox("X-axis indicator", list(METRICS), index=2,
                                format_func=lambda x: METRICS[x], key="x_axis")
    with r2:
        y_metric = st.selectbox("Y-axis indicator", list(METRICS),
                                index=len(METRICS) - 1, format_func=lambda x: METRICS[x], key="y_axis")
    with r3:
        bubble_population = st.checkbox("Scale circles by population", value=True)
    fields = [x_metric, y_metric]
    if bubble_population:
        fields.append("SP.POP.TOTL")
    scatter_data = scoped.loc[scoped.year.eq(year)].dropna(subset=list(set(fields))).copy()
    scatter_data = scatter_data[scatter_data[x_metric].notna() & scatter_data[y_metric].notna()]
    scatter_data = scatter_data.loc[scatter_data[x_metric].ne(float("inf")) & scatter_data[y_metric].ne(float("inf"))]
    if bubble_population:
        scatter_data = scatter_data[scatter_data["SP.POP.TOTL"].gt(0)]
    if len(scatter_data) < 3:
        st.info("At least three matching real country-year observations are needed for this comparison.")
    elif x_metric == y_metric:
        st.info("Select two different indicators to explore their relationship.")
    else:
        correlation = scatter_data[[x_metric, y_metric]].corr().iloc[0, 1]
        st.markdown(f'<span class="small-pill">{len(scatter_data)} matched countries</span>'
                    f'<span class="small-pill">Pearson r: {correlation:.3f}</span>'
                    f'<span class="small-pill">{year} reported data</span>',
                    unsafe_allow_html=True)
        args = dict(data_frame=scatter_data, x=x_metric, y=y_metric,
                    color="region", hover_name="country", color_discrete_sequence=PALETTE,
                    labels={x_metric: METRICS[x_metric], y_metric: METRICS[y_metric]},
                    size_max=55)
        if bubble_population:
            args["size"] = "SP.POP.TOTL"
        scatter_data["hover_x"] = scatter_data[x_metric].map(
            lambda v: format_value(v, x_metric))
        scatter_data["hover_y"] = scatter_data[y_metric].map(
            lambda v: format_value(v, y_metric))
        args["custom_data"] = ["country", "region", "income", "hover_x", "hover_y", "year"]
        graph = px.scatter(**args)
        graph.update_traces(
            marker=dict(opacity=.84, line=dict(width=.7, color="#08111f")),
            hovertemplate=tooltip_rows("%{customdata[0]}", [
                (METRICS[x_metric], "%{customdata[3]}"),
                (METRICS[y_metric], "%{customdata[4]}"),
                ("Region", "%{customdata[1]}"),
                ("Income group", "%{customdata[2]}"),
                ("Year", "%{customdata[5]}"),
            ]),
        )
        chart(style_chart(graph, 520))
        st.markdown('<div class="callout"><b>Interpretation notice:</b> Pearson correlation is a descriptive '
                    'association across the currently observed countries. Neither a positive nor negative '
                    'correlation demonstrates causality. All datasets may have different reporting coverage.</div>',
                    unsafe_allow_html=True)

with lab:
    heading("07 / DATA PROVENANCE", "Explore every observation")
    d1, d2, d3 = st.columns(3)
    d1.metric("REAL JOINED COUNTRY-YEARS", f"{len(scoped):,}")
    d2.metric("COUNTRIES IN SCOPE", f"{scoped.iso3.nunique():,}")
    d3.metric("YEARS REPRESENTED", f"{scoped.year.nunique():,}")
    st.markdown("**Source coverage by indicator**")
    coverage_rows = []
    for code, name in METRICS.items():
        nonnull = scoped.loc[scoped[code].notna()]
        coverage_rows.append({"Metric": name, "Publisher": SOURCES[code],
                              "Reported country-years": len(nonnull),
                              "Reporting countries": nonnull.iso3.nunique(),
                              "Earliest year": nonnull.year.min() if len(nonnull) else None,
                              "Latest year": nonnull.year.max() if len(nonnull) else None})
    st.dataframe(pd.DataFrame(coverage_rows), hide_index=True, use_container_width=True)
    heading("08 / OBSERVATION COMPLETENESS", "Reporting coverage over time")
    cover = coverage_by_year(scoped, primary)
    cover_fig = px.area(cover, x="year", y="countries", line_shape="spline",
                        labels={"countries": "Countries reporting", "year": "Year"})
    cover_fig.update_traces(line=dict(color=MINT, width=3), fillcolor="rgba(61,226,193,.13)")
    chart(style_chart(cover_fig, 280, legend=False))
    st.markdown("**Filter and export observed records**")
    data_years = sorted(scoped.year.unique().tolist())
    start, end = st.select_slider("Export year range", options=data_years,
                                  value=(min(data_years), max(data_years)))
    export = scoped[scoped.year.between(start, end)].sort_values(["country", "year"])
    columns = ["country", "iso3", "region", "income", "year"] + list(METRICS)
    st.dataframe(export[columns], use_container_width=True, hide_index=True, height=370)
    st.download_button("↓ Download real observations (CSV)", export[columns].to_csv(index=False).encode(),
                       file_name=f"global_development_atlas_{start}_{end}.csv", mime="text/csv")
    st.markdown("""<div class="callout"><b>Data lineage:</b> World Bank Indicators API
    (GDP, population, GDP per capita, life expectancy, renewable electricity), World Bank country
    metadata (region and income), and Our World in Data Grapher (CO₂ per capita).
    Countries and years are joined by ISO3 and calendar year; missing observations remain missing.
    Published historical values can be revised by their providers.</div>""", unsafe_allow_html=True)

st.markdown("<div style='text-align:center;color:#64829c;font-size:11px;margin:35px 0 8px'>"
            "GLOBAL DEVELOPMENT ATLAS  /  DATA IS REAL · CONTEXT IS EVERYTHING · NO SYNTHETIC OBSERVATIONS"
            "</div>", unsafe_allow_html=True)
