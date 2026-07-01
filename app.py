import streamlit as st
import flavor_data
import engine
import favourites

ALCOHOL_CATEGORIES = [
    "Spirits",
    "Aperitifs & Vermouths",
    "Fortified Wines",
    "Liqueurs",
    "Wines",
    "Sparkling Wines",
]

_SPARKLING_KW = ["prosecco", "champagne", "cava", "cremant", "sparkling", "pet_nat"]
_APERITIF_ALCO_SUB_KW = ["vermouth", "quinquina", "aperitif", "amaro", "campari", "gentian"]
_FORTIFIED_KW = ["sherry", "port", "vermouth"]
_APERITIF_INGR_KW = ["lillet", "cocchi", "quinquina", "byrrh", "aperitif", "amaro"]


def build_new_alcohol_mapping():
    mapping = {cat: [] for cat in ALCOHOL_CATEGORIES}
    seen = set()

    for name in flavor_data.ALCOHOL_SUBCATEGORIES.keys():
        seen.add(name)
        if any(x in name for x in _APERITIF_ALCO_SUB_KW):
            mapping["Aperitifs & Vermouths"].append(name)
        else:
            mapping["Spirits"].append(name)

    for item in flavor_data.INGREDIENTS:
        name = item["name"]
        if name in seen:
            continue
        seen.add(name)
        alc = item.get("alcohol_type")
        if alc == "light":
            if any(x in name for x in _SPARKLING_KW):
                mapping["Sparkling Wines"].append(name)
            else:
                mapping["Wines"].append(name)
        elif alc == "modifier":
            if any(x in name for x in _FORTIFIED_KW):
                mapping["Fortified Wines"].append(name)
            elif any(x in name for x in _APERITIF_INGR_KW):
                mapping["Aperitifs & Vermouths"].append(name)
            else:
                mapping["Liqueurs"].append(name)

    for cat in mapping:
        mapping[cat] = sorted(mapping[cat], key=lambda x: x.lower())

    return mapping



def build_grouped_ingredient_options():
    grouped = {}

    for name, category in flavor_data.UI_INGREDIENT_CATEGORY_BY_NAME.items():
        grouped.setdefault(category, []).append(name)

    for category in grouped:
        grouped[category] = sorted(grouped[category], key=lambda x: x.lower())

    return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))




st.set_page_config(page_title="Signature Cocktail Engine", layout="centered")

# -------- Custom UI theme (modern minimalist) --------
st.markdown(
    """
<style>
/* ---------- Global ---------- */
.stApp {
    background-color: #FFFFFF;
    color: #1A1A1A;
}
.block-container {
    background-color: #FFFFFF;
}

/* ---------- Streamlit top bar ---------- */
header[data-testid="stHeader"] {
    background-color: #FFFFFF;
}
[data-testid="stToolbar"] {
    display: none;
}

/* ---------- Header ---------- */
.main-title {
    color: #1B4332;
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.main-subtitle {
    color: #6C757D;
    font-size: 0.95rem;
    margin-bottom: 1.2rem;
}
h1 {
    color: #1B4332 !important;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #1B4332 !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    border-radius: 8px;
    border: 1px solid #52B788;
}
[data-testid="stSidebar"] .stTextInput input {
    border-radius: 8px;
    border: 1px solid #52B788;
}

/* ---------- Sidebar dropdowns: light style ---------- */
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1.5px solid #52B788 !important;
    border-radius: 8px !important;
}

/* ---------- Sidebar divider (light gray) ---------- */
[data-testid="stSidebar"] hr {
    border: none;
    border-top: 1px solid #E0E0E0;
    margin: 1rem 0;
}

/* ---------- Buttons: base styling ---------- */
.stButton > button {
    background-color: #1B4332 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
}
.stButton > button:hover {
    background-color: #52B788 !important;
}

/* ---------- Buttons: primary (Generovat) ---------- */
.stButton > button[kind="primary"] {
    background-color: #1B4332;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: background-color 0.2s ease;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[kind="primary"]:focus {
    background-color: #52B788;
    color: #FFFFFF;
}

/* ---------- Buttons: secondary / outline (Uložit) ---------- */
.stButton > button[kind="secondary"] {
    background-color: #FFFFFF;
    color: #1B4332;
    border: 1.5px solid #1B4332;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:focus {
    background-color: #52B788;
    color: #FFFFFF;
    border-color: #52B788;
}

/* ---------- Button: "Zobrazit uložené varianty" (outline) ---------- */
.st-key-show_saved button {
    background-color: #FFFFFF !important;
    color: #1B4332 !important;
    border: 1.5px solid #52B788 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.st-key-show_saved button:hover,
.st-key-show_saved button:focus {
    background-color: #52B788 !important;
    color: #FFFFFF !important;
    border-color: #52B788 !important;
}

/* ---------- Variant cards (expander) ---------- */
.st-expander {
    background-color: #F8F9FA !important;
}
[data-testid="stExpander"] {
    background-color: rgba(255,255,255,0.95) !important;
    border: 1px solid #E9ECEF !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    margin-bottom: 12px;
    position: relative !important;
    z-index: 1 !important;
}
[data-testid="stExpander"] summary {
    background-color: #1B4332 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-weight: 700;
    font-size: 1.15rem;
}
[data-testid="stExpander"] summary:hover {
    color: #FFFFFF !important;
}

/* ---------- Ingredient badges (spirit / key ingredient) ---------- */
.badge-row {
    margin: 4px 0 12px 0;
}
.ingredient-badge {
    display: inline-block;
    background-color: #E8F5E9;
    color: #1B4332;
    border-radius: 4px;
    padding: 2px 8px;
    margin-right: 6px;
    margin-bottom: 4px;
    font-size: 0.85rem;
    font-weight: 600;
}

/* ---------- "PROČ TO FUNGUJE" box ---------- */
.why-box {
    background-color: #F8F9FA;
    border-left: 3px solid #52B788;
    padding: 12px 16px;
    border-radius: 4px;
    margin: 10px 0;
}
.why-box .why-title {
    color: #1B4332;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.why-box ul {
    margin: 0;
    padding-left: 18px;
}
.why-box li {
    color: #1A1A1A;
    font-size: 0.9rem;
    margin-bottom: 3px;
}

/* ---------- Hero banner ---------- */
.hero-banner {
    background-color: #1B4332;
    color: #FFFFFF;
    min-height: 120px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 18px 20px;
    margin: 0.5rem 0 1.5rem 0;
}
.hero-banner .hero-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 6px;
    line-height: 1.3;
}
.hero-banner .hero-emojis {
    font-size: 1.5rem;
    letter-spacing: 8px;
    margin-bottom: 8px;
}
.hero-banner .hero-subtitle {
    font-size: 0.9rem;
    font-weight: 400;
    opacity: 0.9;
}

/* ---------- Expander header: light bg, dark green text ---------- */
.streamlit-expanderHeader {
    background-color: #F8F9FA !important;
    color: #1B4332 !important;
    border-radius: 8px !important;
    border: 1px solid #E9ECEF !important;
}

/* ---------- Text input (note): light bg ---------- */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1.5px solid #52B788 !important;
    border-radius: 8px !important;
}

/* ---------- Search input: light bg incl. focus ---------- */
.stTextInput input {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}
.stTextInput input:focus {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
    border-color: #52B788 !important;
}

/* ---------- Autocomplete dropdown / popover: light bg ---------- */
[data-baseweb="popover"] {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}
[data-baseweb="menu"] {
    background-color: #FFFFFF !important;
}
[role="option"] {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}
[data-baseweb="popover"] * {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}
[data-baseweb="list"] {
    background-color: #FFFFFF !important;
}
[data-baseweb="list"] li {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}
[data-baseweb="list"] li:hover {
    background-color: #E8F5E9 !important;
}
ul[role="listbox"] {
    background-color: #FFFFFF !important;
}
ul[role="listbox"] li {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}
ul[role="listbox"] li:hover {
    background-color: #E8F5E9 !important;
}

/* ---------- Checkbox: white box with green border ---------- */
div[data-testid="stCheckbox"] label {
    border: none !important;
    background: none !important;
    padding: 0 !important;
}
div[data-testid="stCheckbox"] input[type="checkbox"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    border: 2px solid #52B788 !important;
    border-radius: 4px !important;
    background-color: #FFFFFF !important;
    cursor: pointer !important;
    flex-shrink: 0 !important;
}
div[data-testid="stCheckbox"] input[type="checkbox"]:checked {
    background-color: #1B4332 !important;
    border-color: #1B4332 !important;
}

/* ---------- Sidebar: force dark text on all elements ---------- */
[data-testid="stSidebar"] * {
    color: #1A1A1A !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}

/* ---------- Autocomplete popover: light bg (final override) ---------- */
div[data-baseweb="popover"] {
    background: white !important;
}
div[data-baseweb="popover"] div {
    background: white !important;
    color: #1A1A1A !important;
}
div[data-baseweb="popover"] ul li {
    background: white !important;
    color: #1A1A1A !important;
}
div[data-baseweb="popover"] ul li:hover {
    background: #E8F5E9 !important;
}

/* ---------- Keep sidebar visible / hide collapse buttons ---------- */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: none !important;
    left: 0 !important;
}
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { min-width: 240px !important; }
button[kind="header"] { display: none !important; }
[data-testid="stAppViewContainer"] > .main {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400'%3E%3Cline x1='80' y1='60' x2='240' y2='100' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='240' y1='100' x2='400' y2='50' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='400' y1='50' x2='540' y2='90' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='80' y1='60' x2='150' y2='200' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='240' y1='100' x2='300' y2='220' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='400' y1='50' x2='440' y2='190' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='540' y1='90' x2='570' y2='210' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='150' y1='200' x2='300' y2='220' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='300' y1='220' x2='440' y2='190' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='440' y1='190' x2='570' y2='210' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='150' y1='200' x2='100' y2='340' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='300' y1='220' x2='280' y2='360' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='440' y1='190' x2='430' y2='355' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Cline x1='570' y1='210' x2='560' y2='350' stroke='%231B4332' stroke-width='0.8' opacity='0.12'/%3E%3Ccircle cx='80' cy='60' r='18' fill='%23FFF9E6' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='80' y='65' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%8B%3C/text%3E%3Ccircle cx='240' cy='100' r='18' fill='%23E8F5E9' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='240' y='105' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8C%BF%3C/text%3E%3Ccircle cx='400' cy='50' r='18' fill='%23FFF3E0' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='400' y='55' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%8A%3C/text%3E%3Ccircle cx='540' cy='90' r='18' fill='%23FFF8E1' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='540' y='95' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%AF%3C/text%3E%3Ccircle cx='150' cy='200' r='18' fill='%23FFF0F0' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='150' y='205' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%93%3C/text%3E%3Ccircle cx='300' cy='220' r='18' fill='%23FFFDE7' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='300' y='225' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%8D%3C/text%3E%3Ccircle cx='440' cy='190' r='18' fill='%23E8F5E9' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='440' y='195' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8C%B1%3C/text%3E%3Ccircle cx='570' cy='210' r='18' fill='%23FCE4EC' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='570' y='215' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%AB%90%3C/text%3E%3Ccircle cx='100' cy='340' r='18' fill='%23F1F8E9' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='100' y='345' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%A5%A5%3C/text%3E%3Ccircle cx='280' cy='360' r='18' fill='%23FFF8E1' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='280' y='365' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%AF%3C/text%3E%3Ccircle cx='430' cy='355' r='18' fill='%23F3E5D5' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='430' y='360' text-anchor='middle' font-size='14' opacity='0.8'%3E%E2%98%95%3C/text%3E%3Ccircle cx='560' cy='350' r='18' fill='%23F1F8E9' stroke='%2352B788' stroke-width='1.2' opacity='0.7'/%3E%3Ctext x='560' y='355' text-anchor='middle' font-size='14' opacity='0.8'%3E%F0%9F%8D%88%3C/text%3E%3C/svg%3E");
    background-repeat: repeat;
    background-size: 600px 400px;
    background-attachment: fixed;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("""
<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;">
<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <line x1="5%" y1="8%" x2="18%" y2="22%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="18%" y1="22%" x2="35%" y2="12%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="35%" y1="12%" x2="52%" y2="28%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="52%" y1="28%" x2="71%" y2="15%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="71%" y1="15%" x2="88%" y2="25%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="5%" y1="8%" x2="12%" y2="42%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="18%" y1="22%" x2="28%" y2="48%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="35%" y1="12%" x2="42%" y2="45%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="52%" y1="28%" x2="58%" y2="52%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="71%" y1="15%" x2="78%" y2="44%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="88%" y1="25%" x2="92%" y2="48%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="12%" y1="42%" x2="28%" y2="48%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="28%" y1="48%" x2="42%" y2="45%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="42%" y1="45%" x2="58%" y2="52%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="58%" y1="52%" x2="78%" y2="44%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="78%" y1="44%" x2="92%" y2="48%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="12%" y1="42%" x2="8%" y2="72%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="28%" y1="48%" x2="22%" y2="75%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="42%" y1="45%" x2="48%" y2="78%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="58%" y1="52%" x2="65%" y2="72%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="78%" y1="44%" x2="82%" y2="70%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="92%" y1="48%" x2="94%" y2="72%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="8%" y1="72%" x2="22%" y2="75%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="22%" y1="75%" x2="35%" y2="88%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="48%" y1="78%" x2="65%" y2="72%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="65%" y1="72%" x2="82%" y2="70%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="82%" y1="70%" x2="90%" y2="88%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="35%" y1="88%" x2="48%" y2="78%" stroke="#1B4332" stroke-width="0.7" opacity="0.15"/>
  <line x1="18%" y1="22%" x2="42%" y2="45%" stroke="#1B4332" stroke-width="0.7" opacity="0.10"/>
  <line x1="52%" y1="28%" x2="78%" y2="44%" stroke="#1B4332" stroke-width="0.7" opacity="0.10"/>
  <line x1="28%" y1="48%" x2="58%" y2="52%" stroke="#1B4332" stroke-width="0.7" opacity="0.10"/>

  <circle cx="5%" cy="8%" r="16" fill="#FFF9E6" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="5%" y="8.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍋</text>
  <circle cx="18%" cy="22%" r="16" fill="#E8F5E9" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="18%" y="22.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🌿</text>
  <circle cx="35%" cy="12%" r="16" fill="#FFF3E0" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="35%" y="12.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍊</text>
  <circle cx="52%" cy="28%" r="16" fill="#FFFDE7" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="52%" y="28.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍍</text>
  <circle cx="71%" cy="15%" r="16" fill="#FFF0F0" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="71%" y="15.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍓</text>
  <circle cx="88%" cy="25%" r="16" fill="#FFF8E1" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="88%" y="25.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🫚</text>
  <circle cx="12%" cy="42%" r="16" fill="#FFF0F6" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="12%" y="42.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🌸</text>
  <circle cx="28%" cy="48%" r="16" fill="#F1F8E9" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="28%" y="48.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🥥</text>
  <circle cx="42%" cy="45%" r="16" fill="#FFF8E1" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="42%" y="45.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍯</text>
  <circle cx="58%" cy="52%" r="16" fill="#F3E5D5" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="58%" y="52.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">☕</text>
  <circle cx="78%" cy="44%" r="16" fill="#F1F8E9" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="78%" y="44.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍈</text>
  <circle cx="92%" cy="48%" r="16" fill="#EAF3DE" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="92%" y="48.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🌱</text>
  <circle cx="8%" cy="72%" r="16" fill="#FFF9E6" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="8%" y="72.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍋</text>
  <circle cx="22%" cy="75%" r="16" fill="#FCE4EC" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="22%" y="75.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🫐</text>
  <circle cx="35%" cy="88%" r="16" fill="#FFF3E0" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="35%" y="88.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍊</text>
  <circle cx="48%" cy="78%" r="16" fill="#E8F5E9" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="48%" y="78.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🌿</text>
  <circle cx="65%" cy="72%" r="16" fill="#FFFDE7" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="65%" y="72.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍍</text>
  <circle cx="82%" cy="70%" r="16" fill="#FFF8E1" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="82%" y="70.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍯</text>
  <circle cx="90%" cy="88%" r="16" fill="#F3E5D5" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="90%" y="88.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">☕</text>
  <circle cx="94%" cy="72%" r="16" fill="#FFF0F0" stroke="#52B788" stroke-width="1.2" opacity="0.75"/>
  <text x="94%" y="72.5%" text-anchor="middle" dominant-baseline="middle" font-size="13" opacity="0.85">🍓</text>
</svg>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<script>
function fixStyles() {
    const style = document.createElement('style');
    style.innerHTML = `
        [data-baseweb="popover"] { background: white !important; }
        [data-baseweb="popover"] div { background: white !important; color: #1A1A1A !important; }
        [data-baseweb="popover"] li { background: white !important; color: #1A1A1A !important; }
        [data-baseweb="popover"] li:hover { background: #E8F5E9 !important; }
        input[type="checkbox"] {
            accent-color: #1B4332 !important;
            width: 16px !important;
            height: 16px !important;
            border: 2px solid #52B788 !important;
            outline: 2px solid #52B788 !important;
        }
    `;
    document.head.appendChild(style);
}
setTimeout(fixStyles, 500);
setTimeout(fixStyles, 1500);
</script>
""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = []

if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = None

st.markdown(
    '<h1 class="main-title">🍸 Signature Cocktail Generator</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="main-subtitle">Vyber spirit + klíčovou ingredienci '
    "(+ volitelně druhou) a cílový objem. Dostaneš varianty podle stylu.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-banner">'
    '<div class="hero-title">Vytvořte signature cocktail na základě '
    "molekulární harmonie ingrediencí</div>"
    '<div class="hero-emojis">🍋 🌿 🍊 🫚 🌸 🍵</div>'
    '<div class="hero-subtitle">Vyberte spirit a klíčovou ingredienci – '
    "engine najde optimální kombinaci</div>"
    "</div>",
    unsafe_allow_html=True,
)

# -------- Helpers --------
def get_ingredient_names():
    return sorted([i["name"] for i in flavor_data.INGREDIENTS])

def get_spirit_names():
    classic_spirits = list(flavor_data.ALCOHOL_SUBCATEGORIES.keys())

    ingredient_alcohols = [
        i["name"] for i in flavor_data.INGREDIENTS
        if i.get("alcohol_type") in ["base", "modifier", "light"]
    ]

    return sorted(set(classic_spirits + ingredient_alcohols))

def _pretty(name):
    return name.replace("_", " ").title()

_ALCOHOL_CAT_TO_KEY = {
    "Spirits":               "spirits",
    "Aperitifs & Vermouths": "aperitifs",
    "Fortified Wines":       "fortified_wines",
    "Liqueurs":              "liqueurs",
    "Wines":                 "wines",
    "Sparkling Wines":       "sparkling_wines",
}

def _cz_alcohol_cat(cat):
    key = _ALCOHOL_CAT_TO_KEY.get(cat)
    return flavor_data.CZ_ALCOHOL_CATEGORY.get(key, cat) if key else cat

# Suffix → jak ho zobrazit v UI. _fresh se zobrazuje bez závorky.
_VARIANT_SUFFIX_LABEL = {
    "_fresh":   None,
    "_juice":   "džus",
    "_cordial": "cordial",
    "_syrup":   "sirup",
    "_tea":     "čaj",
}


def _hidden_originals():
    """Originální ingredience, které mají _fresh variantu, a tak se v UI skrývají."""
    hidden = set()
    for name in flavor_data.INGREDIENT_BY_NAME:
        if name.endswith("_fresh"):
            base = name[: -len("_fresh")]
            if base in flavor_data.INGREDIENT_BY_NAME:
                hidden.add(base)
    return hidden


HIDDEN_ORIGINALS = _hidden_originals()


def _visible_ingredients(names):
    return [n for n in names if n not in HIDDEN_ORIGINALS]


def _cz_ingredient(name):
    # Pokud jde o variantu (např. green_apple_juice), odvoď zobrazení z base názvu.
    for suffix, label in _VARIANT_SUFFIX_LABEL.items():
        if name.endswith(suffix):
            base = name[: -len(suffix)]
            if base in flavor_data.INGREDIENT_BY_NAME:
                base_cz = flavor_data.CZ_INGREDIENT_NAME.get(
                    base, base.replace("_", " ").title()
                )
                return base_cz if label is None else f"{base_cz} ({label})"
    return flavor_data.CZ_INGREDIENT_NAME.get(name, name.replace("_", " ").title())

def _cz_main_cat(key):
    return flavor_data.CZ_MAIN_CATEGORY.get(key, key.replace("_", " ").title())

def _cz_subcat(key):
    return flavor_data.CZ_SUBCATEGORY.get(key, key.replace("_", " ").title())

def format_core_badges(result):
    """Spirit a klíčové ingredience jako barevné tagy/badges."""
    parts = [
        f'<span class="ingredient-badge">{_pretty(result.spirit)}</span>',
        f'<span class="ingredient-badge">{_cz_ingredient(result.key1)}</span>',
    ]
    if result.key2:
        parts.append(
            f'<span class="ingredient-badge">{_cz_ingredient(result.key2)}</span>'
        )
    return '<div class="badge-row">' + "".join(parts) + "</div>"

def format_variant(result):
    # result is VariantResult dataclass from engine.py
    lines = []
    lines.append(f"**Příprava:** {result.preparation}")
    lines.append("")
    lines.append("**Recept (ml):**")
    lines.append(f"- **{_pretty(result.spirit)}**: {result.amounts_ml['spirit']} ml")
    lines.append(f"- **{_cz_ingredient(result.key1)}**: {result.amounts_ml['key1']} ml")
    if result.key2:
        lines.append(f"- **{_cz_ingredient(result.key2)}**: {result.amounts_ml.get('key2', 0)} ml")
    for n in result.extras:
        lines.append(f"- {_cz_ingredient(n)}: {result.amounts_ml[n]} ml")

    return "\n".join(lines)

_glass_svg_counter = 0

# Paleta 8 barev v zelené škále – každá ingredience dostane unikátní barvu
# podle svého pořadí (index % len(palette)).
GLASS_PALETTE = [
    '#1B4332',  # tmavě zelená - spirit
    '#52B788',  # středně zelená - key1
    '#95D5B2',  # světle zelená
    '#D8F3DC',  # velmi světle zelená
    '#B7E4C7',  # světle zelená 2
    '#ECFCCB',  # žlutozelená
    '#FEF9C3',  # světle žlutá
    '#E8F5E9',  # nejsvětlejší zelená
]

def _build_glass_color_map(amounts_ml):
    """Přiřadí každé ingredienci unikátní barvu podle pořadí (index % len(palette))."""
    return {
        name: GLASS_PALETTE[i % len(GLASS_PALETTE)]
        for i, name in enumerate(amounts_ml.keys())
    }

def generate_glass_svg(title, amounts_ml, spirit=None, key1=None, key2=None):
    global _glass_svg_counter

    total = sum(amounts_ml.values())
    if total == 0:
        return ''

    color_map = _build_glass_color_map(amounts_ml)

    def layer_label(name):
        if name == 'spirit':
            return _cz_ingredient(spirit) if spirit else 'spirit'
        if name == 'key1':
            return _cz_ingredient(key1) if key1 else 'key1'
        if name == 'key2':
            return _cz_ingredient(key2) if key2 else 'key2'
        return _cz_ingredient(name)

    # -------- tvar sklenice podle stylu --------
    t = title.lower()
    if 'sour' in t:
        # rocks glass – široký nízký obdélník
        shape = '<rect x="15" y="135" width="120" height="100" rx="4"/>'
        deco = ''
        by, bh = 135, 100
    elif 'highball' in t:
        # highball – úzký vysoký obdélník
        shape = '<rect x="45" y="35" width="60" height="200" rx="4"/>'
        deco = ''
        by, bh = 35, 200
    elif 'signature' in t:
        # coupette – mělká miska s jemně zaobleným dnem na nožce
        shape = '<path d="M25,62 L135,62 Q135,98 80,104 Q25,98 25,62 Z"/>'
        deco = ('<line x1="80" y1="104" x2="80" y2="205" stroke="#1B4332" stroke-width="2"/>'
                '<line x1="52" y1="205" x2="108" y2="205" stroke="#1B4332" stroke-width="2"/>')
        by, bh = 62, 42
    elif 'spritz' in t:
        # wine glass – kulatá miska na nožce
        shape = '<path d="M38,60 L122,60 Q122,138 80,138 Q38,138 38,60 Z"/>'
        deco = ('<line x1="80" y1="138" x2="80" y2="210" stroke="#1B4332" stroke-width="2"/>'
                '<line x1="52" y1="210" x2="108" y2="210" stroke="#1B4332" stroke-width="2"/>')
        by, bh = 60, 78
    else:
        # short cocktail – martini, obrácený trojúhelník na nožce
        shape = '<polygon points="22,55 138,55 80,128"/>'
        deco = ('<line x1="80" y1="128" x2="80" y2="205" stroke="#1B4332" stroke-width="2"/>'
                '<line x1="52" y1="205" x2="108" y2="205" stroke="#1B4332" stroke-width="2"/>')
        by, bh = 55, 73

    _glass_svg_counter += 1
    clip_id = f"glass_clip_{_glass_svg_counter}"

    # -------- vrstvy tekutiny (odspodu nahoru), oříznuté na tvar --------
    layers = []
    draw_order = [(n, ml) for n, ml in reversed(list(amounts_ml.items())) if ml > 0]
    y_offset = by + bh
    for name, ml in draw_order:
        layer_h = ml / total * bh
        y_offset -= layer_h
        layers.append(
            f'<rect x="5" y="{y_offset:.1f}" width="150" height="{layer_h:.1f}" '
            f'fill="{color_map[name]}" clip-path="url(#{clip_id})" opacity="0.9"/>'
        )

    outline = shape.replace('/>', ' fill="none" stroke="#1B4332" stroke-width="1.5"/>', 1)

    # -------- popisky vrstev (odshora dolů) --------
    labels = []
    label_names = [n for n, _ in draw_order][::-1]
    ly = 60
    for name in label_names:
        ml = amounts_ml[name]
        color = color_map[name]
        lbl = layer_label(name)
        labels.append(f'<rect x="148" y="{ly-8}" width="10" height="10" rx="2" fill="{color}" stroke="#1B4332" stroke-width="0.5"/>')
        labels.append(f'<text x="162" y="{ly}" font-size="9" fill="#1B4332">{lbl}: {ml}ml</text>')
        ly += 16

    # Single-line SVG: indentované řádky by Streamlit markdown interpretoval
    # jako code block (SVG kód by se zobrazil jako text).
    svg = (
        f'<svg width="400" height="260" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><clipPath id="{clip_id}">{shape}</clipPath></defs>'
        f'<g transform="translate(30, 0)">'
        f'{"".join(layers)}{deco}{outline}{"".join(labels)}'
        f'</g>'
        f'</svg>'
    )

    # Posun celého SVG doprava (margin-left na wrapperu).
    return f'<div style="margin-left:20px;">{svg}</div>'

def format_why_box(result):
    """'PROČ TO FUNGUJE' jako stylovaný box (světle šedé pozadí, zelený akcent)."""
    if not result.notes:
        return ""
    items = "".join(f"<li>{n}</li>" for n in result.notes)
    return (
        '<div class="why-box">'
        '<div class="why-title">PROČ TO FUNGUJE</div>'
        f"<ul>{items}</ul>"
        "</div>"
    )

def format_bridge_inserts(result):
    if not result.bridge_inserts:
        return ""
    lines = ["**BRIDGE INSERTS:**"]
    for fam_a, fam_b, br, name, micro, reduced in result.bridge_inserts:
        tag = "micro 2.5ml" if micro else "5ml"
        if reduced:
            lines.append(f"- {fam_a} ↔ {fam_b} (bridge {br}) → **{name}** [{tag}] (ubráno 2.5 ml z {reduced})")
        else:
            lines.append(f"- {fam_a} ↔ {fam_b} (bridge {br}) → **{name}** [{tag}]")
    return "\n".join(lines)

# -------- Sidebar inputs --------
st.sidebar.header("Nastavení")

# -------- Oblíbené --------
st.sidebar.divider()
st.sidebar.subheader("Oblíbené")
if st.sidebar.button("📋 Zobrazit uložené varianty", key="show_saved"):
    try:
        saved = favourites.load_favourites()
        if saved:
            st.sidebar.success(f"Načteno {len(saved)} uložených variant.")
            st.sidebar.markdown('<div style="max-height:420px;overflow-y:auto;padding-right:4px;">', unsafe_allow_html=True)
            for row in saved:
                with st.sidebar.expander(f"{row.get('Datum','')} — {row.get('Název','')}"):
                    st.write(f"**Spirit:** {row.get('Spirit','')}")
                    st.write(f"**Key1:** {row.get('Key1','')}")
                    if row.get("Key2"):
                        st.write(f"**Key2:** {row.get('Key2','')}")
                    st.write(f"**Recept:** {row.get('Recept','')}")
                    st.write(f"**Příprava:** {row.get('Příprava','')}")
                    if row.get("Poznámka"):
                        st.write(f"**Poznámka:** {row.get('Poznámka','')}")
            st.sidebar.markdown('</div>', unsafe_allow_html=True)
        else:
            st.sidebar.info("Zatím žádné uložené varianty.")
    except Exception as e:
        st.sidebar.error(f"Chyba při načítání: {e}")
st.sidebar.divider()

alcohol_mapping = build_new_alcohol_mapping()

_spirit_default = "london_dry_gin"
_default_category = next(
    (cat for cat, names in alcohol_mapping.items() if _spirit_default in names),
    ALCOHOL_CATEGORIES[0],
)

alcohol_category = st.sidebar.selectbox(
    "Kategorie alkoholu",
    options=ALCOHOL_CATEGORIES,
    index=ALCOHOL_CATEGORIES.index(_default_category),
    format_func=_cz_alcohol_cat,
)

available_spirits = alcohol_mapping[alcohol_category]

spirit = st.sidebar.selectbox(
    "Alkohol",
    options=available_spirits,
    index=available_spirits.index(_spirit_default) if _spirit_default in available_spirits else 0,
    format_func=_pretty,
)

grouped_ingredients = build_grouped_ingredient_options()

all_ingredients = sorted(
    _visible_ingredients(flavor_data.UI_INGREDIENT_CATEGORY_BY_NAME.keys()),
    key=lambda x: x.lower(),
)

ingredient_search = st.sidebar.text_input(
    "Hledat ingredienci",
    value="",
    placeholder="Např. jablko, sůl, máta...",
)

if ingredient_search.strip():
    search_text = ingredient_search.strip().lower()

    matching_ingredients = [
        name
        for name in all_ingredients
        if search_text in name.lower()
        or search_text in flavor_data.CZ_INGREDIENT_NAME.get(name, "").lower()
    ]

    key1 = st.sidebar.selectbox(
        "Hlavní ingredience",
        options=matching_ingredients if matching_ingredients else all_ingredients,
        format_func=_cz_ingredient,
    )

else:
    _default_key1 = "green_apple_fresh"
    _main_cats = list(flavor_data.SUBCATEGORIES_BY_MAIN.keys())
    _default_main = flavor_data.UI_INGREDIENT_MAIN_CATEGORY.get(_default_key1, _main_cats[0])

    main_cat = st.sidebar.selectbox(
        "Hlavní kategorie",
        options=_main_cats,
        index=_main_cats.index(_default_main) if _default_main in _main_cats else 0,
        format_func=_cz_main_cat,
    )

    _subcats = flavor_data.SUBCATEGORIES_BY_MAIN[main_cat]

    if _subcats is None:
        # Flat category — no subcategory level, go straight to ingredients
        _available = sorted(
            _visible_ingredients(
                n for n, mc in flavor_data.UI_INGREDIENT_MAIN_CATEGORY.items() if mc == main_cat
            ),
            key=lambda x: x.lower(),
        )
        key1 = st.sidebar.selectbox(
            "Hlavní ingredience",
            options=_available,
            format_func=_cz_ingredient,
        )
    else:
        _default_subcat = flavor_data.UI_INGREDIENT_CATEGORY_BY_NAME.get(_default_key1)
        if _default_subcat not in _subcats:
            _default_subcat = _subcats[0]

        subcat = st.sidebar.selectbox(
            "Podkategorie",
            options=_subcats,
            index=_subcats.index(_default_subcat) if _default_subcat in _subcats else 0,
            format_func=_cz_subcat,
        )

        _available = sorted(
            _visible_ingredients(
                n for n, sc in flavor_data.UI_INGREDIENT_CATEGORY_BY_NAME.items() if sc == subcat
            ),
            key=lambda x: x.lower(),
        )

        key1 = st.sidebar.selectbox(
            "Hlavní ingredience",
            options=_available,
            index=_available.index(_default_key1) if _default_key1 in _available else 0,
            format_func=_cz_ingredient,
        )

use_key2 = st.sidebar.checkbox("Přidat druhou ingredienci", value=False)
key2 = None
if use_key2:
    # prevent same as key1
    key2_options = [n for n in all_ingredients if n != key1]
    key2 = st.sidebar.selectbox("Druhá ingredience", key2_options, format_func=_cz_ingredient)

target_ml = 90

current_params = (spirit, key1, key2, target_ml)

if st.session_state.last_inputs is not None and current_params != st.session_state.last_inputs:
    st.info("Parametry se změnily. Klikni na 'Generovat varianty' pro přepočet.")


# Session state for "Generate more"
if "seed" not in st.session_state:
    st.session_state.seed = 0
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = None

col1, col2 = st.columns(2)
generate_clicked = col1.button("Generovat varianty", type="primary", use_container_width=True)
more_clicked = col2.button("Generovat další", type="primary", use_container_width=True)

def run_generation(increment_seed: bool):
    # Use deterministic seed changes so "3 more" gives different results
    if increment_seed:
        st.session_state.seed += 1

    # engine uses random internally; set seed if engine.py exposes it.
    # If not, we can still vary results by temporarily using python's random seed here,
    # but we avoid importing random to keep it simple unless needed.
    results = engine.generate(
        spirit=spirit,
        key1=key1,
        key2=key2,
        target_ml=target_ml,
    )
    return results

# Decide when to generate
do_generate = False
inc = False

if generate_clicked:
    st.session_state.results = []  # reset
    st.session_state.last_inputs = (spirit, key1, key2, target_ml)

    try:
        new_results = run_generation(increment_seed=False)
        st.session_state.results.extend(new_results)
    except Exception as e:
        st.error(f"Něco se pokazilo: {type(e).__name__}: {e}")

if more_clicked:
    if st.session_state.last_inputs == (spirit, key1, key2, target_ml):
        try:
            new_results = run_generation(increment_seed=True)
            st.session_state.results.extend(new_results)
        except Exception as e:
            st.error(f"Něco se pokazilo: {type(e).__name__}: {e}")
    else:
        st.warning("Nejdřív klikni na 'Generovat varianty' se stejnými vstupy, pak můžeš generovat další.")

# ---- render persisted results ----

if st.session_state.results:
    st.divider()
    for i, r in enumerate(st.session_state.results, start=1):
        style = r.title[r.title.find("(")+1:r.title.rfind(")")] if "(" in r.title else r.title
        with st.expander(f"Variant {i}: {style}", expanded=(i == 1)):
            st.markdown(format_core_badges(r), unsafe_allow_html=True)
            col_recipe, col_glass = st.columns([1.5, 1.5])
            with col_recipe:
                st.markdown(format_variant(r))
            with col_glass:
                svg = generate_glass_svg(r.title, r.amounts_ml, r.spirit, r.key1, r.key2)
                st.markdown(svg, unsafe_allow_html=True)
            why = format_why_box(r)
            if why:
                st.markdown(why, unsafe_allow_html=True)
            bridges = format_bridge_inserts(r)
            if bridges:
                st.markdown(bridges)
            note_key = f"note_{i}"
            saved_key = f"saved_{i}"
            st.markdown('<p style="color:#1B4332;font-weight:600;font-size:14px;margin-bottom:4px;">Poznámka (volitelné)</p>', unsafe_allow_html=True)
            note = st.text_input("Poznámka (volitelné)", key=note_key, placeholder="Např. skvělé pro léto...")
            if st.button("⭐ Uložit variantu", key=f"save_{i}", type="secondary", use_container_width=True):
                try:
                    favourites.save_favourite(r, note)
                    st.session_state[saved_key] = True
                except Exception as e:
                    st.error(f"Chyba při ukládání: {e}")
            if st.session_state.get(saved_key):
                st.success("✅ Varianta uložena!")

if do_generate:
    try:
        results = run_generation(increment_seed=inc)
        st.divider()
        for i, r in enumerate(results, start=1):
            style = r.title[r.title.find("(")+1:r.title.rfind(")")] if "(" in r.title else r.title
            with st.expander(f"Variant {i}: {style}", expanded=(i == 1)):
                st.markdown(format_core_badges(r), unsafe_allow_html=True)
                col_recipe, col_glass = st.columns([1.5, 1.5])
                with col_recipe:
                    st.markdown(format_variant(r))
                with col_glass:
                    svg = generate_glass_svg(r.title, r.amounts_ml, r.spirit, r.key1, r.key2)
                    st.markdown(svg, unsafe_allow_html=True)
                why = format_why_box(r)
                if why:
                    st.markdown(why, unsafe_allow_html=True)
                bridges = format_bridge_inserts(r)
                if bridges:
                    st.markdown(bridges)
    except Exception as e:
        st.error(f"Něco se pokazilo: {type(e).__name__}: {e}")

st.markdown("""
<script>
const style = document.createElement('style');
style.innerHTML = `
    [data-baseweb="popover"] { background-color: white !important; }
    [data-baseweb="popover"] * { background-color: white !important; color: #1A1A1A !important; }
`;
document.head.appendChild(style);
</script>
""", unsafe_allow_html=True)

