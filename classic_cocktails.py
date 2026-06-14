"""
classic_cocktails.py — database of classic cocktails used as ml-allocation templates.

Each cocktail provides absolute ml amounts per role. The engine matches a generated
variant (by style + spirit type) against this database and uses the averaged amounts
as a template for role-based ml allocation, so generated drinks land on bartender-
realistic proportions instead of generic role defaults.

`style` must exactly match the style names used in engine.py variant titles:
    "Sour", "Highball / Swizzle", "Signature Twist", "Spritz", "Short Cocktail"

`amounts` keys are roles with absolute ml values:
    spirit, acid, sweet, modifier, top_up, other, egg_white
"""

from typing import Dict, List


CLASSIC_COCKTAILS: List[Dict] = [
    # -----------------------------------------------------------------
    # SOUR  (target ~90 ml)
    # -----------------------------------------------------------------
    {"name": "Daiquiri",      "style": "Sour", "spirit_type": "rum",
     "amounts": {"spirit": 45, "acid": 20, "sweet": 15, "egg_white": 10}},
    {"name": "Gin Sour",      "style": "Sour", "spirit_type": "gin",
     "amounts": {"spirit": 45, "acid": 20, "sweet": 15, "egg_white": 10}},
    {"name": "Whiskey Sour",  "style": "Sour", "spirit_type": "whisky",
     "amounts": {"spirit": 45, "acid": 20, "sweet": 15, "egg_white": 10}},
    {"name": "Margarita",     "style": "Sour", "spirit_type": "tequila",
     "amounts": {"spirit": 45, "acid": 22, "sweet": 15, "modifier": 8}},
    {"name": "Pisco Sour",    "style": "Sour", "spirit_type": "brandy",
     "amounts": {"spirit": 45, "acid": 22, "sweet": 15, "egg_white": 8}},
    {"name": "Cosmopolitan",  "style": "Sour", "spirit_type": "vodka",
     "amounts": {"spirit": 36, "acid": 18, "sweet": 18, "modifier": 18}},
    {"name": "Gimlet",        "style": "Sour", "spirit_type": "gin",
     "amounts": {"spirit": 50, "acid": 22, "sweet": 18}},
    {"name": "Amaretto Sour", "style": "Sour", "spirit_type": "aperitif",
     "amounts": {"spirit": 45, "acid": 22, "sweet": 13, "egg_white": 10}},
    {"name": "Clover Club",   "style": "Sour", "spirit_type": "gin",
     "amounts": {"spirit": 40, "acid": 18, "sweet": 18, "other": 14}},

    # -----------------------------------------------------------------
    # HIGHBALL  (target ~150 ml)
    # -----------------------------------------------------------------
    {"name": "Gin & Tonic",   "style": "Highball / Swizzle", "spirit_type": "gin",
     "amounts": {"spirit": 45, "top_up": 105}},
    {"name": "Moscow Mule",    "style": "Highball / Swizzle", "spirit_type": "vodka",
     "amounts": {"spirit": 45, "acid": 15, "top_up": 90}},
    {"name": "Dark & Stormy",  "style": "Highball / Swizzle", "spirit_type": "rum",
     "amounts": {"spirit": 45, "acid": 8, "top_up": 97}},
    {"name": "Mojito",         "style": "Highball / Swizzle", "spirit_type": "rum",
     "amounts": {"spirit": 45, "acid": 15, "sweet": 15, "top_up": 75}},
    {"name": "Tom Collins",    "style": "Highball / Swizzle", "spirit_type": "gin",
     "amounts": {"spirit": 45, "acid": 20, "sweet": 15, "top_up": 70}},
    {"name": "Paloma",         "style": "Highball / Swizzle", "spirit_type": "tequila",
     "amounts": {"spirit": 45, "acid": 15, "top_up": 90}},
    {"name": "Rum & Cola",     "style": "Highball / Swizzle", "spirit_type": "rum",
     "amounts": {"spirit": 45, "top_up": 105}},
    {"name": "Horse's Neck",   "style": "Highball / Swizzle", "spirit_type": "whisky",
     "amounts": {"spirit": 45, "top_up": 105}},
    {"name": "Whisky Soda",    "style": "Highball / Swizzle", "spirit_type": "whisky",
     "amounts": {"spirit": 45, "top_up": 105}},

    # -----------------------------------------------------------------
    # SIGNATURE TWIST  (target ~100 ml)
    # -----------------------------------------------------------------
    {"name": "Negroni",      "style": "Signature Twist", "spirit_type": "gin",
     "amounts": {"spirit": 33, "modifier": 33, "sweet": 34}},
    {"name": "Manhattan",    "style": "Signature Twist", "spirit_type": "whisky",
     "amounts": {"spirit": 67, "modifier": 33}},
    {"name": "Old Fashioned","style": "Signature Twist", "spirit_type": "whisky",
     "amounts": {"spirit": 60, "sweet": 5, "other": 5}},
    {"name": "Boulevardier", "style": "Signature Twist", "spirit_type": "whisky",
     "amounts": {"spirit": 40, "modifier": 30, "sweet": 30}},
    {"name": "Paper Plane",  "style": "Signature Twist", "spirit_type": "whisky",
     "amounts": {"spirit": 25, "modifier": 25, "acid": 25, "sweet": 25}},
    {"name": "Last Word",    "style": "Signature Twist", "spirit_type": "gin",
     "amounts": {"spirit": 25, "modifier": 25, "acid": 25, "sweet": 25}},
    {"name": "Jungle Bird",  "style": "Signature Twist", "spirit_type": "rum",
     "amounts": {"spirit": 35, "modifier": 20, "acid": 20, "sweet": 15, "other": 10}},
    {"name": "Penicillin",   "style": "Signature Twist", "spirit_type": "whisky",
     "amounts": {"spirit": 50, "acid": 20, "sweet": 20, "other": 10}},

    # -----------------------------------------------------------------
    # SPRITZ  (target ~150 ml)
    # -----------------------------------------------------------------
    {"name": "Aperol Spritz",     "style": "Spritz", "spirit_type": "aperitif",
     "amounts": {"modifier": 50, "top_up": 75, "other": 25}},
    {"name": "Campari Spritz",    "style": "Spritz", "spirit_type": "aperitif",
     "amounts": {"modifier": 50, "top_up": 75, "other": 25}},
    {"name": "Hugo Spritz",       "style": "Spritz", "spirit_type": "aperitif",
     "amounts": {"modifier": 40, "top_up": 90, "sweet": 20}},
    {"name": "Lillet Spritz",     "style": "Spritz", "spirit_type": "aperitif",
     "amounts": {"modifier": 60, "top_up": 75, "other": 15}},
    {"name": "Elderflower Spritz","style": "Spritz", "spirit_type": "aperitif",
     "amounts": {"modifier": 40, "sweet": 20, "top_up": 90}},

    # -----------------------------------------------------------------
    # SHORT COCKTAIL  (target ~75 ml)
    # -----------------------------------------------------------------
    {"name": "Martini",     "style": "Short Cocktail", "spirit_type": "gin",
     "amounts": {"spirit": 60, "modifier": 15}},
    {"name": "Sazerac",     "style": "Short Cocktail", "spirit_type": "whisky",
     "amounts": {"spirit": 60, "sweet": 8, "other": 7}},
    {"name": "Rob Roy",     "style": "Short Cocktail", "spirit_type": "whisky",
     "amounts": {"spirit": 50, "modifier": 25}},
    {"name": "Martinez",    "style": "Short Cocktail", "spirit_type": "gin",
     "amounts": {"spirit": 38, "modifier": 30, "sweet": 7}},
    {"name": "Bamboo",      "style": "Short Cocktail", "spirit_type": "aperitif",
     "amounts": {"modifier": 38, "sweet": 37}},
    {"name": "Hanky Panky", "style": "Short Cocktail", "spirit_type": "gin",
     "amounts": {"spirit": 38, "modifier": 30, "sweet": 7}},
]


# Maps a raw spirit name (any of the canonical engine spirit keys or fuzzy input)
# onto one of the seven template spirit types. Checked as substrings, in order.
_SPIRIT_TYPE_KEYWORDS: List[tuple] = [
    ("gin",      ("gin",)),
    ("rum",      ("rum", "rhum")),
    ("whisky",   ("bourbon", "whiskey", "whisky", "rye", "scotch", "irish", "japanese")),
    ("tequila",  ("tequila", "mezcal", "sotol")),
    ("vodka",    ("vodka",)),
    ("brandy",   ("cognac", "brandy", "calvados", "armagnac", "pisco", "fruit_eau_de_vie")),
    ("aperitif", ("amaro", "aperitif", "vermouth", "campari", "gentian",
                  "quinquina", "lillet", "cocchi", "byrrh")),
]


def get_spirit_type(spirit: str) -> str:
    """Map a spirit name onto one of: gin / rum / whisky / tequila / vodka / brandy / aperitif.

    Falls back to the lowercased input when nothing matches, so that
    find_best_template() degrades to the style-average template.
    """
    s = (spirit or "").lower()
    for spirit_type, keywords in _SPIRIT_TYPE_KEYWORDS:
        if any(kw in s for kw in keywords):
            return spirit_type
    return s


def _average_amounts(cocktails: List[Dict]) -> Dict[str, float]:
    """Average the per-role amounts across a list of cocktails (missing role = 0)."""
    keys = set()
    for c in cocktails:
        keys.update(c["amounts"].keys())
    n = len(cocktails)
    return {k: sum(c["amounts"].get(k, 0) for c in cocktails) / n for k in keys}


def find_best_template(style: str, spirit_type: str) -> Dict[str, float]:
    """Return averaged template amounts for the best-matching classic cocktails.

    1. Prefer cocktails with the same style AND spirit_type.
    2. Fall back to the average of all cocktails of the same style.
    3. Return {} if the style is unknown.
    """
    same_style = [c for c in CLASSIC_COCKTAILS if c["style"] == style]
    if not same_style:
        return {}

    matching = [c for c in same_style if c["spirit_type"] == spirit_type]
    if matching:
        return _average_amounts(matching)

    return _average_amounts(same_style)
