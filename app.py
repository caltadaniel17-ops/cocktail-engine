import streamlit as st
import flavor_data
import engine

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

if "results" not in st.session_state:
    st.session_state.results = []

if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = None

st.title("🍸 Signature Cocktail Generator")
st.caption("Vyber spirit + klíčovou ingredienci (+ volitelně druhou) a cílový objem. Dostaneš varianty podle stylu.")

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

def _cz_ingredient(name):
    return flavor_data.CZ_INGREDIENT_NAME.get(name, name.replace("_", " ").title())

def _cz_ingredient_cat(cat):
    return flavor_data.CZ_INGREDIENT_CATEGORY.get(cat, cat.replace("_", " ").title())

def format_variant(result):
    # result is VariantResult dataclass from engine.py
    lines = []
    core = f"**Spirit:** {_pretty(result.spirit)} | **Klíčová ingredience:** {_cz_ingredient(result.key1)}"
    if result.key2:
        core += f" | **Key 2:** {_cz_ingredient(result.key2)}"
    lines.append(core)
    lines.append(f"**Příprava:** {result.preparation}")
    lines.append("")
    lines.append("**Recept (ml):**")
    lines.append(f"- **{_pretty(result.spirit)}**: {result.amounts_ml['spirit']} ml")
    lines.append(f"- **{_cz_ingredient(result.key1)}**: {result.amounts_ml['key1']} ml")
    if result.key2:
        lines.append(f"- **{_cz_ingredient(result.key2)}**: {result.amounts_ml.get('key2', 0)} ml")
    for n in result.extras:
        lines.append(f"- {_cz_ingredient(n)}: {result.amounts_ml[n]} ml")

    lines.append("")
    lines.append("**PROČ TO FUNGUJE:**")
    for n in result.notes:
        lines.append(f"- {n}")

    if result.bridge_inserts:
        lines.append("")
        lines.append("**BRIDGE INSERTS:**")
        for fam_a, fam_b, br, name, micro, reduced in result.bridge_inserts:
            tag = "micro 2.5ml" if micro else "5ml"
            if reduced:
                lines.append(f"- {fam_a} ↔ {fam_b} (bridge {br}) → **{name}** [{tag}] (ubráno 2.5 ml z {reduced})")
            else:
                lines.append(f"- {fam_a} ↔ {fam_b} (bridge {br}) → **{name}** [{tag}]")

    return "\n".join(lines)

# -------- Sidebar inputs --------
st.sidebar.header("Nastavení")

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
    flavor_data.UI_INGREDIENT_CATEGORY_BY_NAME.keys(),
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
    ]

    key1 = st.sidebar.selectbox(
        "Hlavní ingredience",
        options=matching_ingredients if matching_ingredients else all_ingredients,
        format_func=_cz_ingredient,
    )

else:
    ingredient_categories = list(grouped_ingredients.keys())

    default_key1 = "green_apple"

    default_key1_category = flavor_data.UI_INGREDIENT_CATEGORY_BY_NAME.get(
        default_key1,
        ingredient_categories[0],
    )

    ingredient_category = st.sidebar.selectbox(
        "Kategorie ingredience",
        options=ingredient_categories,
        index=ingredient_categories.index(default_key1_category)
        if default_key1_category in ingredient_categories
        else 0,
        format_func=_cz_ingredient_cat,
    )

    available_ingredients = grouped_ingredients[ingredient_category]

    key1 = st.sidebar.selectbox(
        "Hlavní ingredience",
        options=available_ingredients,
        index=available_ingredients.index(default_key1)
        if default_key1 in available_ingredients
        else 0,
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
generate_clicked = col1.button("Generovat varianty")
more_clicked = col2.button("Generovat další")

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
            st.markdown(format_variant(r))

if do_generate:
    try:
        results = run_generation(increment_seed=inc)
        st.divider()
        for i, r in enumerate(results, start=1):
            style = r.title[r.title.find("(")+1:r.title.rfind(")")] if "(" in r.title else r.title
            with st.expander(f"Variant {i}: {style}", expanded=(i == 1)):
                st.markdown(format_variant(r))
    except Exception as e:
        st.error(f"Něco se pokazilo: {type(e).__name__}: {e}")

st.divider()
st.caption("Tip: později sem přidáme vyhledávání, lepší popisy, a ukládání feedbacku (good/bad match).")

