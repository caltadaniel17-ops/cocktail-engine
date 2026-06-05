# flavor_data.py
# Data layer for Signature Cocktail Engine (MVP)
# - Molecular families
# - Compatibility graph (direct/bridge/conditional/conflict)
# - Alcohol subcategories (1-18)
# - Ingredient database (60 entities)
#
# Note: This file is intentionally "data-only". Engine logic comes later.

from __future__ import annotations

from typing import Dict, List, Tuple, TypedDict, Literal

Family = str
Role = Literal[
    "structure", "identity", "acid", "sweet", "fatty", "dry",
    "aromatic", "accent", "bridge", "support", "structural_modifier"
]
Temperature = Literal["fresh", "warm", "neutral"]

TasteVector = TypedDict(
    "TasteVector",
    {"sweet": int, "acid": int, "bitter": int, "umami": int, "spice": int, "fat": int},
)

class Ingredient(TypedDict):
    name: str
    families: List[Family]         # 1-3 dominant families
    intensity: int                 # 1-5
    roles: List[Role]              # dynamic roles allowed
    taste: TasteVector             # 0-3 per axis
    temperature: Temperature


# -------------------------
# Molecular families (MVP)
# -------------------------

FAMILIES: List[Family] = [
    # original 15
    "ester_fruity",
    "terpene_citrus",
    "terpene_herbal",
    "lactone_creamy",
    "phenolic_smoky",
    "pyrazine_roasted",
    "tannic_dry",
    "sulfuric_pungent",
    "menthol_cooling",
    "floral_ionone",
    "green_leafy",
    "caramelized",
    "aldehyde_fatty",
    "fatty_rich",
    "fermented_alcoholic",
    # new 4
    "umami_vegetal",
    "umami_fermented",
    "mineral_saline",
    "spice_volatile",
]

# Intensity metrics per family: (aroma_dominance, structure_weight, persistence)
FAMILY_INTENSITY: Dict[Family, Tuple[int, int, int]] = {
    "phenolic_smoky": (5, 4, 5),
    "pyrazine_roasted": (4, 4, 4),
    "caramelized": (3, 4, 4),
    "fermented_alcoholic": (3, 3, 3),
    "tannic_dry": (2, 4, 5),

    "ester_fruity": (3, 2, 2),
    "terpene_citrus": (4, 1, 1),
    "lactone_creamy": (2, 3, 3),
    "fatty_rich": (2, 4, 3),

    "terpene_herbal": (4, 1, 2),
    "green_leafy": (3, 1, 1),
    "floral_ionone": (4, 1, 2),

    "menthol_cooling": (5, 1, 3),
    "sulfuric_pungent": (5, 2, 4),
    "aldehyde_fatty": (4, 2, 3),

    # new families
    "umami_vegetal": (3, 3, 3),
    "umami_fermented": (4, 4, 4),
    "mineral_saline": (2, 1, 2),
    "spice_volatile": (5, 1, 3),
}

# -------------------------
# Compatibility model
# -------------------------
# For each family:
# - direct: strong synergy
# - bridge: dict[target_family] = bridge_family
# - conditional: workable only with intensity constraints (engine will handle thresholds)
# - conflict: hard conflicts (engine should try to "save" only if a bridge rule exists)
Compatibility = TypedDict(
    "Compatibility",
    {
        "direct": List[Family],
        "bridge": Dict[Family, Family],
        "conditional": List[Family],
        "conflict": List[Family],
    },
)

COMPATIBILITY: Dict[Family, Compatibility] = {
    "ester_fruity": {
        "direct": ["terpene_citrus", "lactone_creamy", "floral_ionone", "caramelized", "mineral_saline", "spice_volatile"],
        "bridge": {
            "green_leafy": "terpene_citrus",
            "phenolic_smoky": "caramelized",
            "umami_fermented": "terpene_citrus",
        },
        "conditional": ["menthol_cooling", "umami_vegetal"],
        "conflict": ["sulfuric_pungent"],
    },
    "terpene_citrus": {
        "direct": ["ester_fruity", "terpene_herbal", "green_leafy", "fermented_alcoholic", "floral_ionone", "mineral_saline"],
        "bridge": {
            "pyrazine_roasted": "caramelized",
            "umami_fermented": "caramelized",
        },
        "conditional": ["tannic_dry"],
        "conflict": [],
    },
    "terpene_herbal": {
        "direct": ["terpene_citrus", "green_leafy", "ester_fruity", "spice_volatile"],
        "bridge": {
            "lactone_creamy": "ester_fruity",
        },
        "conditional": ["phenolic_smoky"],
        "conflict": [],
    },
    "lactone_creamy": {
        "direct": ["ester_fruity", "caramelized", "pyrazine_roasted"],
        "bridge": {
            "tannic_dry": "caramelized",
            "mineral_saline": "ester_fruity",
            "spice_volatile": "caramelized",
        },
        "conditional": [],
        "conflict": ["sulfuric_pungent"],
    },
    "phenolic_smoky": {
        "direct": ["caramelized", "pyrazine_roasted", "fatty_rich", "umami_fermented"],
        "bridge": {
            "ester_fruity": "caramelized",
            "floral_ionone": "caramelized",
            "umami_vegetal": "caramelized",
            "mineral_saline": "caramelized",
        },
        "conditional": ["terpene_herbal", "menthol_cooling"],
        "conflict": ["sulfuric_pungent"],
    },
    "pyrazine_roasted": {
        "direct": ["caramelized", "lactone_creamy", "fatty_rich", "phenolic_smoky", "umami_fermented", "spice_volatile"],
        "bridge": {
            "floral_ionone": "caramelized",
            "terpene_citrus": "caramelized",
        },
        "conditional": [],
        "conflict": ["menthol_cooling"],
    },
    "tannic_dry": {
        "direct": ["ester_fruity", "caramelized", "fermented_alcoholic", "green_leafy"],
        "bridge": {
            "lactone_creamy": "caramelized",
        },
        "conditional": ["spice_volatile"],
        "conflict": ["menthol_cooling"],
    },
    "sulfuric_pungent": {
        "direct": [],
        "bridge": {},
        "conditional": [],
        "conflict": ["ester_fruity", "lactone_creamy", "phenolic_smoky", "floral_ionone"],
    },
    "menthol_cooling": {
        "direct": [],
        "bridge": {},
        "conditional": ["ester_fruity", "phenolic_smoky"],
        "conflict": ["pyrazine_roasted", "tannic_dry", "spice_volatile"],
    },
    "floral_ionone": {
        "direct": ["ester_fruity", "terpene_citrus", "green_leafy"],
        "bridge": {
            "pyrazine_roasted": "caramelized",
            "phenolic_smoky": "caramelized",
            "umami_vegetal": "terpene_citrus",
            "umami_fermented": "caramelized",
        },
        "conditional": ["aldehyde_fatty"],
        "conflict": ["sulfuric_pungent"],
    },
    "green_leafy": {
        "direct": ["terpene_citrus", "terpene_herbal", "ester_fruity", "umami_vegetal"],
        "bridge": {
            "ester_fruity": "terpene_citrus",
        },
        "conditional": [],
        "conflict": [],
    },
    "caramelized": {
        "direct": ["pyrazine_roasted", "lactone_creamy", "phenolic_smoky", "ester_fruity", "umami_fermented", "spice_volatile", "mineral_saline"],
        "bridge": {},
        "conditional": [],
        "conflict": [],
    },
    "aldehyde_fatty": {
        "direct": ["terpene_citrus"],
        "bridge": {},
        "conditional": ["floral_ionone"],
        "conflict": ["umami_fermented"],
    },
    "fatty_rich": {
        "direct": ["pyrazine_roasted", "phenolic_smoky", "caramelized", "lactone_creamy"],
        "bridge": {},
        "conditional": [],
        "conflict": [],
    },
    "fermented_alcoholic": {
        "direct": ["terpene_citrus", "tannic_dry", "ester_fruity"],
        "bridge": {},
        "conditional": [],
        "conflict": [],
    },

    # New families
    "umami_vegetal": {
        "direct": ["green_leafy", "terpene_herbal", "mineral_saline"],
        "bridge": {
            "phenolic_smoky": "caramelized",
            "floral_ionone": "terpene_citrus",
        },
        "conditional": ["ester_fruity"],
        "conflict": ["menthol_cooling"],
    },
    "umami_fermented": {
        "direct": ["caramelized", "pyrazine_roasted", "phenolic_smoky", "mineral_saline"],
        "bridge": {
            "ester_fruity": "terpene_citrus",
            "floral_ionone": "caramelized",
        },
        "conditional": [],
        "conflict": ["menthol_cooling", "aldehyde_fatty"],
    },
    "mineral_saline": {
        "direct": ["ester_fruity", "terpene_citrus", "umami_vegetal", "caramelized", "umami_fermented"],
        "bridge": {
            "phenolic_smoky": "caramelized",
            "lactone_creamy": "ester_fruity",
        },
        "conditional": [],
        "conflict": ["floral_ionone"],  # high dominance floral + saline can go soapy
    },
    "spice_volatile": {
        "direct": ["caramelized", "pyrazine_roasted", "terpene_herbal", "ester_fruity"],
        "bridge": {
            "floral_ionone": "ester_fruity",
            "lactone_creamy": "caramelized",
        },
        "conditional": [],
        "conflict": ["menthol_cooling"],
    },
}

# -------------------------
# Alcohol subcategories (1-18)
# -------------------------

ALCOHOL_SUBCATEGORIES: Dict[str, List[Family]] = {
    # Whisky
    "bourbon": ["caramelized", "lactone_creamy", "pyrazine_roasted"],
    "rye_whiskey": ["terpene_herbal", "tannic_dry", "caramelized"],
    "peated_whisky": ["phenolic_smoky", "tannic_dry", "caramelized"],

    # Rum
    "white_rum": ["ester_fruity", "fermented_alcoholic", "terpene_citrus"],
    "aged_rum": ["caramelized", "ester_fruity", "lactone_creamy"],
    "overproof_rum": ["ester_fruity", "caramelized", "fermented_alcoholic"],

    # Gin
    "london_dry_gin": ["terpene_herbal", "terpene_citrus", "green_leafy"],
    "new_western_gin": ["floral_ionone", "terpene_citrus", "terpene_herbal"],

    # Tequila / Mezcal
    "tequila_blanco": ["green_leafy", "terpene_citrus", "terpene_herbal"],
    "tequila_anejo": ["caramelized", "lactone_creamy", "green_leafy"],
    "mezcal": ["phenolic_smoky", "green_leafy", "terpene_herbal"],

    # Vodka
    "neutral_vodka": ["fermented_alcoholic", "aldehyde_fatty"],
    "grain_vodka": ["pyrazine_roasted", "fermented_alcoholic", "caramelized"],

    # Brandy
    "young_brandy": ["ester_fruity", "fermented_alcoholic", "floral_ionone"],
    "aged_brandy": ["caramelized", "lactone_creamy", "tannic_dry"],

    # Fortified / aperitif
    "dry_vermouth": ["tannic_dry", "terpene_herbal", "fermented_alcoholic"],
    "sweet_vermouth": ["caramelized", "tannic_dry", "fermented_alcoholic"],
    "amaro_bitter_aperitif": ["tannic_dry", "terpene_herbal", "pyrazine_roasted"],
}

# -------------------------
# Ingredient database (60)
# Entity-level (not juice/syrup forms)
# taste vector: sweet/acid/bitter/umami/spice/fat in range 0-3
# -------------------------

INGREDIENTS: List[Ingredient] = [

    # Citrus backbone  
    {
        "name": "lemon",
        "families": ["terpene_citrus", "aldehyde_fatty"],
        "intensity": 4,
        "roles": ["acid", "bridge", "aromatic"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "lime",
        "families": ["terpene_citrus", "green_leafy"],
        "intensity": 4,
        "roles": ["acid", "bridge"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "grapefruit",
        "families": ["terpene_citrus", "tannic_dry"],
        "intensity": 3,
        "roles": ["acid", "support"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "orange",
        "families": ["terpene_citrus", "ester_fruity"],
        "intensity": 2,
        "roles": ["identity", "sweet"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "yuzu",
        "families": ["terpene_citrus", "floral_ionone"],
        "intensity": 4,
        "roles": ["acid", "aromatic"],
        "taste": {"sweet": 1, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },

    # Citrus expansion
    {
        "name": "bergamot",
        "families": ["terpene_citrus", "floral_ionone"],
        "intensity": 4,
        "roles": ["acid", "aromatic"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "calamansi",
        "families": ["terpene_citrus", "green_leafy"],
        "intensity": 5,
        "roles": ["acid"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "blood_orange",
        "families": ["terpene_citrus", "tannic_dry"],
        "intensity": 3,
        "roles": ["acid", "identity"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    { 
        "name": "mandarin",
        "families": ["terpene_citrus", "ester_fruity"],
        "intensity": 2,
        "roles": ["acid", "sweet"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    { 
        "name": "kaffir_lime",
        "families": ["terpene_citrus", "green_leafy"],
        "intensity": 5,
        "roles": ["acid", "aromatic"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },

    # Tropical fruits
    {
        "name": "pineapple",
        "families": ["ester_fruity", "terpene_citrus"],
        "intensity": 3,
        "roles": ["identity", "sweet", "bridge"],
        "taste": {"sweet": 2, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "mango",
        "families": ["ester_fruity", "lactone_creamy"],
        "intensity": 3,
        "roles": ["identity", "sweet"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
    {
        "name": "passion_fruit",
        "families": ["ester_fruity", "terpene_citrus"],
        "intensity": 4,
        "roles": ["identity", "acid"],
        "taste": {"sweet": 1, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "banana",
        "families": ["ester_fruity", "lactone_creamy"],
        "intensity": 3,
        "roles": ["identity", "fatty"],
        "taste": {"sweet": 2, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
    {
        "name": "coconut_milk",
        "families": ["lactone_creamy", "fatty_rich"],
        "intensity": 3,
        "roles": ["fatty", "bridge", "structural_modifier"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 3},
        "temperature": "warm",
    },

    # Berries & light fruit
    {
        "name": "strawberry",
        "families": ["ester_fruity", "floral_ionone"],
        "intensity": 2,
        "roles": ["identity"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "raspberry",
        "families": ["ester_fruity", "tannic_dry"],
        "intensity": 3,
        "roles": ["identity", "acid"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "blackberry",
        "families": ["ester_fruity", "tannic_dry"],
        "intensity": 3,
        "roles": ["identity", "dry"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "green_apple",
        "families": ["ester_fruity", "green_leafy"],
        "intensity": 2,
        "roles": ["identity", "bridge"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "pear",
        "families": ["ester_fruity", "floral_ionone"],
        "intensity": 2,
        "roles": ["identity"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },

    # Green/ Fresh
    {
        "name": "cucumber",
        "families": ["green_leafy", "aldehyde_fatty"],
        "intensity": 2,
        "roles": ["identity", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "celery",
        "families": ["green_leafy", "mineral_saline"],
        "intensity": 3,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "shiso",
        "families": ["green_leafy", "terpene_herbal"],
        "intensity": 4,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "green_grape",
        "families": ["ester_fruity", "green_leafy"],
        "intensity": 2,
        "roles": ["identity", "sweet"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "parsley",
        "families": ["green_leafy", "terpene_herbal"],
        "intensity": 3,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "watermelon",
        "families": ["green_leafy", "ester_fruity"],
        "intensity": 2,
        "roles": ["identity", "sweet", "bridge"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },

    # Herbs
    {
        "name": "mint",
        "families": ["menthol_cooling", "terpene_herbal"],
        "intensity": 5,
        "roles": ["aromatic", "accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "basil",
        "families": ["terpene_herbal", "green_leafy"],
        "intensity": 3,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "rosemary",
        "families": ["terpene_herbal", "tannic_dry"],
        "intensity": 4,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "thyme",
        "families": ["terpene_herbal", "green_leafy"],
        "intensity": 3,
        "roles": ["aromatic"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "sage",
        "families": ["terpene_herbal", "tannic_dry"],
        "intensity": 4,
        "roles": ["aromatic"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "coriander_leaf",
        "families": ["terpene_herbal", "green_leafy"],
        "intensity": 3,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "fresh",
    },

    # Florals
    {
        "name": "lavender",
        "families": ["floral_ionone", "terpene_herbal"],
        "intensity": 4,
        "roles": ["aromatic", "accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "rose",
        "families": ["floral_ionone"],
        "intensity": 3,
        "roles": ["aromatic"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "hibiscus",
        "families": ["floral_ionone", "tannic_dry"],
        "intensity": 4,
        "roles": ["acid", "aromatic"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "elderflower",
        "families": ["floral_ionone", "ester_fruity"],
        "intensity": 3,
        "roles": ["aromatic", "sweet"],
        "taste": {"sweet": 2, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "orange_blossom",
        "families": ["floral_ionone", "terpene_citrus"],
        "intensity": 4,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "chamomile",
        "families": ["floral_ionone", "lactone_creamy"],
        "intensity": 3,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "jasmine",
        "families": ["floral_ionone", "terpene_herbal"],
        "intensity": 4,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },

    # Teas
    {
        "name": "green_tea",
        "families": ["green_leafy", "tannic_dry"],
        "intensity": 2,
        "roles": ["dry", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "black_tea",
        "families": ["tannic_dry", "pyrazine_roasted"],
        "intensity": 3,
        "roles": ["dry"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 2, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "red_berries_tea",
        "families": ["ester_fruity", "tannic_dry"],
        "intensity": 3,
        "roles": ["aromatic", "support", "bridge"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "oolong",
        "families": ["floral_ionone", "tannic_dry"],
        "intensity": 3,
        "roles": ["dry", "aromatic"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "lapsang_souchong",
        "families": ["phenolic_smoky", "tannic_dry"],
        "intensity": 4,
        "roles": ["identity", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 2, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "warm",
    },

    # Coffee & roasted
    {
        "name": "espresso",
        "families": ["pyrazine_roasted", "tannic_dry"],
        "intensity": 4,
        "roles": ["identity", "dry"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 2, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "cocoa",
        "families": ["pyrazine_roasted", "caramelized"],
        "intensity": 3,
        "roles": ["identity"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 2, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
    {
        "name": "toasted_almond",
        "families": ["pyrazine_roasted", "fatty_rich"],
        "intensity": 3,
        "roles": ["identity", "fatty"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 2},
        "temperature": "warm",
    },

    # Sweeteners & modifiers
    {
        "name": "honey",
        "families": ["floral_ionone", "caramelized"],
        "intensity": 3,
        "roles": ["sweet", "bridge", "structural_modifier"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "maple_syrup",
        "families": ["caramelized", "pyrazine_roasted"],
        "intensity": 3,
        "roles": ["sweet"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "white_sugar",
        "families": ["caramelized"],
        "intensity": 2,
        "roles": ["sweet", "structural_modifier"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "brown_sugar",
        "families": ["caramelized", "pyrazine_roasted"],
        "intensity": 3,
        "roles": ["sweet"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "agave",
        "families": ["ester_fruity", "caramelized"],
        "intensity": 2,
        "roles": ["sweet", "bridge"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },

    # Texture & fat
    {
        "name": "cream",
        "families": ["fatty_rich", "lactone_creamy"],
        "intensity": 3,
        "roles": ["fatty", "structural_modifier"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 3},
        "temperature": "warm",
    },
    {
        "name": "egg_white",
        "families": ["fatty_rich"],
        "intensity": 1,
        "roles": ["structural_modifier"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 1, "spice": 0, "fat": 1},
        "temperature": "neutral",
    },
    {
        "name": "yogurt",
        "families": ["lactone_creamy", "tannic_dry"],
        "intensity": 3,
        "roles": ["fatty", "acid"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 2},
        "temperature": "fresh",
    },
    {
        "name": "olive_oil",
        "families": ["fatty_rich", "green_leafy"],
        "intensity": 4,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 3},
        "temperature": "warm",
    },

    # Nuts & seeds
    {
        "name": "hazelnut",
        "families": ["pyrazine_roasted", "fatty_rich"],
        "intensity": 3,
        "roles": ["identity"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 2},
        "temperature": "warm",
    },
    {
        "name": "sesame",
        "families": ["pyrazine_roasted", "fatty_rich"],
        "intensity": 4,
        "roles": ["identity", "bridge"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 2},
        "temperature": "warm",
    },
    {
        "name": "peanut",
        "families": ["pyrazine_roasted", "fatty_rich"],
        "intensity": 4,
        "roles": ["identity"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 3},
        "temperature": "warm",
    },
    {
        "name": "walnut",
        "families": ["pyrazine_roasted", "tannic_dry"],
        "intensity": 3,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 1, "spice": 0, "fat": 2},
        "temperature": "neutral",
    },

    # Avant-garde / controlled umami
    {
        "name": "tomato",
        "families": ["green_leafy", "umami_vegetal"],
        "intensity": 3,
        "roles": ["identity", "acid"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 0, "umami": 2, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "miso",
        "families": ["pyrazine_roasted", "umami_fermented"],
        "intensity": 5,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 3, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "black_garlic",
        "families": ["caramelized", "umami_fermented"],
        "intensity": 4,
        "roles": ["identity", "bridge"],
        "taste": {"sweet": 2, "acid": 0, "bitter": 0, "umami": 2, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "seaweed",
        "families": ["umami_fermented", "tannic_dry"],
        "intensity": 4,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 3, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },

    # SPICE / VOLATILE

    {
        "name": "cardamom",
        "families": ["spice_volatile", "terpene_herbal"],
        "intensity": 4,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "cinnamon",
        "families": ["spice_volatile", "caramelized"],
        "intensity": 3,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "clove",
        "families": ["spice_volatile", "tannic_dry"],
        "intensity": 4,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "star_anise",
        "families": ["spice_volatile", "terpene_herbal"],
        "intensity": 4,
        "roles": ["accent", "aromatic"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "pink_pepper",
        "families": ["spice_volatile", "terpene_citrus"],
        "intensity": 3,
        "roles": ["accent", "aromatic"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "allspice",
        "families": ["spice_volatile", "caramelized"],
        "intensity": 3,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 0, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "ginger",
        "families": ["terpene_herbal", "spice_volatile"],
        "intensity": 4,
        "roles": ["identity", "bridge"],
        "taste": {"sweet": 0, "acid": 1, "bitter": 0, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "warm",
    },

    # Light bitter elements
    {
        "name": "gentian",
        "families": ["tannic_dry", "pyrazine_roasted"],
        "intensity": 4,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 3, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "dandelion",
        "families": ["green_leafy", "tannic_dry"],
        "intensity": 3,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "grapefruit_zest",
        "families": ["terpene_citrus", "tannic_dry"],
        "intensity": 4,
        "roles": ["aromatic", "accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "cocoa_nib",
        "families": ["pyrazine_roasted", "tannic_dry"],
        "intensity": 4,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 3, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },

    # White wines
    {
        "name": "sauvignon_blanc",
        "families": ["green_leafy", "terpene_citrus", "fermented_alcoholic"],
        "intensity": 4,
        "roles": ["identity", "acid", "aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "riesling_dry",
        "families": ["floral_ionone", "terpene_citrus", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "acid", "aromatic"],
        "taste": {"sweet": 1, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "pinot_grigio",
        "families": ["mineral_saline", "terpene_citrus", "fermented_alcoholic"],
        "intensity": 2,
        "roles": ["dry", "support", "bridge"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "albarino",
        "families": ["terpene_citrus", "mineral_saline", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "acid", "bridge"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "chenin_blanc",
        "families": ["ester_fruity", "floral_ionone", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "acid", "support"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "chardonnay_unoaked",
        "families": ["ester_fruity", "mineral_saline", "fermented_alcoholic"],
        "intensity": 2,
        "roles": ["identity", "support", "dry"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "chardonnay_oaked",
        "families": ["lactone_creamy", "caramelized", "fermented_alcoholic"],
        "intensity": 4,
        "roles": ["identity", "support", "bridge"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "gewurztraminer",
        "families": ["floral_ionone", "terpene_herbal", "fermented_alcoholic"],
        "intensity": 4,
        "roles": ["identity", "aromatic", "support"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },

    # Sparkling wines
    {
        "name": "champagne_brut",
        "families": ["mineral_saline", "tannic_dry", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["dry", "acid", "bridge", "structural_modifier"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "champagne_blanc_de_blancs",
        "families": ["terpene_citrus", "mineral_saline", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["acid", "aromatic", "bridge"],
        "taste": {"sweet": 0, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "champagne_blanc_de_noirs",
        "families": ["ester_fruity", "tannic_dry", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "dry", "bridge"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "prosecco",
        "families": ["ester_fruity", "floral_ionone", "fermented_alcoholic"],
        "intensity": 2,
        "roles": ["identity", "sweet", "aromatic", "bridge"],
        "taste": {"sweet": 2, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "cava_brut",
        "families": ["tannic_dry", "caramelized", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["dry", "bridge", "support"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "pet_nat",
        "families": ["ester_fruity", "green_leafy", "fermented_alcoholic"],
        "intensity": 4,
        "roles": ["identity", "acid", "aromatic"],
        "taste": {"sweet": 1, "acid": 3, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "cremant",
        "families": ["ester_fruity", "tannic_dry", "fermented_alcoholic"],
        "intensity": 2,
        "roles": ["dry", "support", "bridge"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "sparkling_rose",
        "families": ["ester_fruity", "floral_ionone", "tannic_dry"],
        "intensity": 3,
        "roles": ["identity", "aromatic", "bridge"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    # Red wines
    {
        "name": "pinot_noir",
        "families": ["ester_fruity", "tannic_dry", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "dry", "bridge"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "gamay",
        "families": ["ester_fruity", "fermented_alcoholic", "tannic_dry"],
        "intensity": 2,
        "roles": ["identity", "support", "bridge"],
        "taste": {"sweet": 1, "acid": 2, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "merlot",
        "families": ["ester_fruity", "tannic_dry", "caramelized"],
        "intensity": 3,
        "roles": ["identity", "support", "dry"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "cabernet_sauvignon",
        "families": ["tannic_dry", "green_leafy", "caramelized"],
        "intensity": 4,
        "roles": ["identity", "dry", "structure"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "syrah",
        "families": ["tannic_dry", "spice_volatile", "caramelized"],
        "intensity": 4,
        "roles": ["identity", "dry", "bridge"],
        "taste": {"sweet": 0, "acid": 1, "bitter": 2, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "malbec",
        "families": ["ester_fruity", "tannic_dry", "caramelized"],
        "intensity": 4,
        "roles": ["identity", "dry", "support"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "sangiovese",
        "families": ["tannic_dry", "ester_fruity", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "acid", "dry", "bridge"],
        "taste": {"sweet": 0, "acid": 2, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "tempranillo",
        "families": ["tannic_dry", "caramelized", "fermented_alcoholic"],
        "intensity": 3,
        "roles": ["identity", "dry", "support", "bridge"],
        "taste": {"sweet": 0, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },

    # Fortified wines
    {
        "name": "fino_sherry",
        "families": ["tannic_dry", "umami_fermented", "mineral_saline"],
        "intensity": 4,
        "roles": ["dry", "bridge", "accent"],
        "taste": {"sweet": 0, "acid": 1, "bitter": 1, "umami": 2, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "amontillado_sherry",
        "families": ["caramelized", "tannic_dry", "umami_fermented"],
        "intensity": 4,
        "roles": ["identity", "dry", "bridge"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 1, "umami": 2, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "oloroso_sherry",
        "families": ["caramelized", "umami_fermented", "tannic_dry"],
        "intensity": 5,
        "roles": ["identity", "bridge", "support"],
        "taste": {"sweet": 1, "acid": 0, "bitter": 1, "umami": 2, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "port_ruby",
        "families": ["ester_fruity", "caramelized", "fermented_alcoholic"],
        "intensity": 4,
        "roles": ["identity", "sweet", "support"],
        "taste": {"sweet": 3, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "port_tawny",
        "families": ["caramelized", "lactone_creamy", "tannic_dry"],
        "intensity": 4,
        "roles": ["identity", "sweet", "bridge"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "warm",
    },

    # Aperitif wines
    {
        "name": "lillet_blanc",
        "families": ["floral_ionone", "terpene_citrus", "fermented_alcoholic"],
        "intensity": 2,
        "roles": ["aromatic", "sweet", "bridge"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "lillet_rouge",
        "families": ["ester_fruity", "tannic_dry", "caramelized"],
        "intensity": 3,
        "roles": ["identity", "sweet", "bridge"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "cocchi_americano",
        "families": ["terpene_citrus", "tannic_dry", "caramelized"],
        "intensity": 3,
        "roles": ["aromatic", "bitter", "bridge"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "quinquina",
        "families": ["tannic_dry", "terpene_citrus", "caramelized"],
        "intensity": 4,
        "roles": ["bitter", "accent", "bridge"],
        "taste": {"sweet": 1, "acid": 1, "bitter": 3, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "byrrh",
        "families": ["tannic_dry", "caramelized", "ester_fruity"],
        "intensity": 3,
        "roles": ["identity", "bitter", "support"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },

    # Liqueurs
    {
        "name": "triple_sec",
        "families": ["terpene_citrus", "ester_fruity"],
        "intensity": 3,
        "roles": ["sweet", "aromatic", "bridge"],
        "taste": {"sweet": 3, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "curaçao",
        "families": ["terpene_citrus", "tannic_dry"],
        "intensity": 3,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 2, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "green_chartreuse",
        "families": ["terpene_herbal", "spice_volatile", "floral_ionone"],
        "intensity": 5,
        "roles": ["identity", "aromatic", "bridge"],
        "taste": {"sweet": 2, "acid": 0, "bitter": 1, "umami": 0, "spice": 2, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "yellow_chartreuse",
        "families": ["floral_ionone", "terpene_herbal", "caramelized"],
        "intensity": 4,
        "roles": ["identity", "sweet", "bridge"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "benedictine",
        "families": ["caramelized", "terpene_herbal", "spice_volatile"],
        "intensity": 4,
        "roles": ["sweet", "bridge", "support"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "st_germain",
        "families": ["floral_ionone", "ester_fruity"],
        "intensity": 3,
        "roles": ["sweet", "aromatic", "bridge"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "violet_liqueur",
        "families": ["floral_ionone"],
        "intensity": 4,
        "roles": ["aromatic", "accent"],
        "taste": {"sweet": 2, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "maraschino",
        "families": ["ester_fruity", "floral_ionone"],
        "intensity": 3,
        "roles": ["aromatic", "bridge"],
        "taste": {"sweet": 2, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "peach_liqueur",
        "families": ["ester_fruity", "floral_ionone"],
        "intensity": 2,
        "roles": ["sweet", "identity"],
        "taste": {"sweet": 3, "acid": 1, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "blackcurrant_liqueur",
        "families": ["ester_fruity", "tannic_dry"],
        "intensity": 3,
        "roles": ["identity", "sweet", "bridge"],
        "taste": {"sweet": 3, "acid": 1, "bitter": 1, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "coffee_liqueur",
        "families": ["pyrazine_roasted", "caramelized"],
        "intensity": 4,
        "roles": ["identity", "sweet"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 2, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "warm",
    },
    {
        "name": "chocolate_liqueur",
        "families": ["pyrazine_roasted", "lactone_creamy"],
        "intensity": 3,
        "roles": ["sweet", "identity"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
    {
        "name": "amaretto",
        "families": ["pyrazine_roasted", "lactone_creamy"],
        "intensity": 3,
        "roles": ["sweet", "identity", "bridge"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 1, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
    {
        "name": "frangelico",
        "families": ["pyrazine_roasted", "fatty_rich"],
        "intensity": 3,
        "roles": ["sweet", "identity"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
    {
        "name": "drambuie",
        "families": ["caramelized", "spice_volatile", "floral_ionone"],
        "intensity": 4,
        "roles": ["sweet", "bridge", "support"],
        "taste": {"sweet": 3, "acid": 0, "bitter": 0, "umami": 0, "spice": 1, "fat": 0},
        "temperature": "warm",
    },
    # Mineral / saline
    {
        "name": "sea_salt",
        "families": ["mineral_saline"],
        "intensity": 3,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "saline_solution",
        "families": ["mineral_saline"],
        "intensity": 2,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "mineral_water",
        "families": ["mineral_saline"],
        "intensity": 1,
        "roles": ["structural_modifier"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 0, "umami": 0, "spice": 0, "fat": 0},
        "temperature": "fresh",
    },
    {
        "name": "oyster_shell",
        "families": ["mineral_saline", "tannic_dry"],
        "intensity": 3,
        "roles": ["accent"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 1, "spice": 0, "fat": 0},
        "temperature": "neutral",
    },
    {
        "name": "white_sesame_salt",
        "families": ["mineral_saline", "pyrazine_roasted"],
        "intensity": 4,
        "roles": ["accent", "bridge"],
        "taste": {"sweet": 0, "acid": 0, "bitter": 1, "umami": 1, "spice": 0, "fat": 1},
        "temperature": "warm",
    },
]


# -------------------------
# Quick helper indices (optional for later engine use)
# -------------------------

INGREDIENT_BY_NAME: Dict[str, Ingredient] = {i["name"]: i for i in INGREDIENTS}
