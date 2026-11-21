"""Presentation regression checks (not analytical observations)."""
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_theme_is_mint_and_dark():
    with (ROOT / ".streamlit" / "config.toml").open("rb") as file:
        theme = tomllib.load(file)["theme"]
    assert theme["base"] == "dark"
    assert theme["primaryColor"].lower() == "#3de2c1"
    assert theme["backgroundColor"].lower() == "#08111f"
    assert theme["textColor"].lower() == "#e7eef9"


def test_selection_and_readability_styles_exist():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '[data-baseweb="tag"]' in app
    assert 'color:#c7d9e9!important' in app
    assert 'background:#16474c!important' in app
    assert '.stApp [data-baseweb="slider"] [role="slider"]' in app
    assert "def tooltip_rows(" in app
