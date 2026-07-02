"""
Google Sheets integration for saving and loading favourite cocktail variants.

Authentication priority:
  1. Streamlit secrets (production / Streamlit Cloud)
  2. Local service-account JSON file at the path in env var GOOGLE_SA_JSON
     or the default path './gcp_service_account.json' (for local dev)
"""

import json
import os
from datetime import date

import gspread
from google.oauth2.service_account import Credentials

import flavor_data

SHEET_ID = "1GPdrz21ChuJ0UY7vWmqZx1g3cBwKYHjv452QtvXUzwU"
WORKSHEET_NAME = "Favourites"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = ["Datum", "Spirit", "Key1", "Key2", "Extra alkohol", "Název", "Recept", "Příprava", "Poznámka"]


def _creds_from_streamlit_secrets():
    """Build Credentials from st.secrets['gcp_service_account']."""
    import streamlit as st
    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=SCOPES)


def _creds_from_local_json():
    """Build Credentials from a local service-account JSON file."""
    path = os.environ.get("GOOGLE_SA_JSON", "gcp_service_account.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Service-account JSON not found at '{path}'. "
            "Set GOOGLE_SA_JSON env var or place gcp_service_account.json in the project root."
        )
    with open(path) as f:
        info = json.load(f)
    return Credentials.from_service_account_info(info, scopes=SCOPES)


def get_sheet() -> gspread.Worksheet:
    """Connect to Google Sheets and return the Favourites worksheet."""
    try:
        creds = _creds_from_streamlit_secrets()
    except Exception:
        creds = _creds_from_local_json()

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)

    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)

    # Ensure header row exists
    first_row = ws.row_values(1)
    if first_row != HEADERS:
        ws.insert_row(HEADERS, 1)

    return ws


def _cz_name(name: str) -> str:
    return flavor_data.CZ_INGREDIENT_NAME.get(name, name.replace("_", " ").title())


def _build_recipe_text(result) -> str:
    """Return a plain-text recipe summary for storage."""
    parts = [f"{_cz_name(result.spirit)}: {result.amounts_ml['spirit']}ml"]
    parts.append(f"{_cz_name(result.key1)}: {result.amounts_ml['key1']}ml")
    if result.key2:
        parts.append(f"{_cz_name(result.key2)}: {result.amounts_ml.get('key2', 0)}ml")
    if getattr(result, "extra_alcohol", None):
        parts.append(f"{_cz_name(result.extra_alcohol)}: {result.amounts_ml.get('extra_alcohol', 0)}ml")
    for name in result.extras:
        parts.append(f"{_cz_name(name)}: {result.amounts_ml[name]}ml")
    return ", ".join(parts)


def save_favourite(result, note: str = "") -> None:
    """Append a variant row to the Favourites worksheet."""
    ws = get_sheet()
    row = [
        date.today().isoformat(),
        result.spirit.replace("_", " ").title(),
        result.key1.replace("_", " ").title(),
        result.key2 or "",
        (result.extra_alcohol or "").replace("_", " ").title(),
        result.title,
        _build_recipe_text(result),
        result.preparation,
        note,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


def load_favourites() -> list[dict]:
    """Return all saved favourites as a list of dicts (skips header row)."""
    ws = get_sheet()
    records = ws.get_all_records(expected_headers=HEADERS)
    return records
