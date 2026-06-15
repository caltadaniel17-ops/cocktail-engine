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
_APERITIF_ALCO_SUB_KW = ["vermouth", "quinquina", "aperitif", "amaro"]
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
    background-color: #FFFFFF;
    border: 1px solid #E9ECEF !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    margin-bottom: 12px;
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
</style>
""",
    unsafe_allow_html=True,
)

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
            st.markdown(format_variant(r))
            why = format_why_box(r)
            if why:
                st.markdown(why, unsafe_allow_html=True)
            bridges = format_bridge_inserts(r)
            if bridges:
                st.markdown(bridges)
            note_key = f"note_{i}"
            saved_key = f"saved_{i}"
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
                st.markdown(format_variant(r))
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

