# engine.py
# MVP Signature Cocktail Engine (pre-dilution)
# - Input: spirit + key1 (+ optional key2)
# - Output: top 3 variants (3–5 ingredients) + ml recipe + bridge inserts + simple why/score

from __future__ import annotations

import random
import copy
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import flavor_data

def get_category_build_rule(title: str) -> dict:
    for category, rule in flavor_data.CATEGORY_BUILD_RULES.items():
        if category.lower() in title.lower():
            return rule

    return {
        "target_ml": 90,
        "target_abv": 18,
    }

STYLE_TARGET_ML = {
    "Sour": 90,
    "Highball": 180,
    "Swizzle": 180,
    "Spritz": 160,
    "Signature": 90,
}

# -----------------------------
# Input resolving (substring + aliases)
# -----------------------------

def _norm(s: str) -> str:
    """Normalize user input for matching."""
    s = (s or "").strip().lower()
    # common separators
    s = s.replace("-", " ").replace("_", " ")
    # collapse whitespace
    s = " ".join(s.split())
    return s

# You can extend this over time (UX gold).
INGREDIENT_ALIASES = {
    "apple": "green_apple",
    "apple juice": "green_apple",
    "green apple": "green_apple",

    "lime juice": "lime",
    "lemon juice": "lemon",
    "grapefruit juice": "grapefruit",
    "orange juice": "orange",

    "mint leaves": "mint",
    "fresh mint": "mint",
    "basil leaves": "basil",
    "coriander": "coriander_leaf",
    "cilantro": "coriander_leaf",

    "berries tea": "red_berries_tea",
    "red berries tea": "red_berries_tea",
    "fruit tea": "red_berries_tea",
}

SPIRIT_ALIASES = {
    "gin": "london_dry_gin",          # default choice
    "london dry gin": "london_dry_gin",
    "new western gin": "new_western_gin",

    "rum": "aged_rum",
    "dark rum": "aged_rum",
    "white rum": "white_rum",
    "vodka": "neutral_vodka",

    "tequila": "tequila_blanco",
    "mezcal": "mezcal",

    "bourbon": "bourbon",
    "rye": "rye_whiskey",

    "brandy": "aged_brandy",
    "vermouth dry": "dry_vermouth",
    "vermouth sweet": "sweet_vermouth",
    "amaro": "amaro_bitter_aperitif",
    "aperitif": "amaro_bitter_aperitif",
}

def resolve_ingredient_name(user_input: str) -> str:
    """
    Resolve user input to an ingredient name from flavor_data.INGREDIENTS
    using: exact -> alias -> substring -> token match.
    Returns the original input (normalized) if nothing found.
    """
    s = _norm(user_input)
    if not s:
        return s

    # exact DB match (by normalized)
    if s in flavor_data.INGREDIENT_BY_NAME:
        return s

    # alias match
    if s in INGREDIENT_ALIASES:
        return INGREDIENT_ALIASES[s]

    # substring match against ingredient names
    # (e.g. 'apple' should hit 'green_apple')
    names = [i["name"] for i in flavor_data.INGREDIENTS]
    # prefer longest name match to avoid too-generic collisions
    candidates = [n for n in names if _norm(n) in s or s in _norm(n)]
    if candidates:
        # choose the longest candidate name (more specific)
        return sorted(candidates, key=len, reverse=True)[0]

    # token-based fallback: if user types "apple juice" try each token
    tokens = [t for t in s.split() if t not in {"juice", "fresh"}]
    for t in tokens:
        if t in INGREDIENT_ALIASES:
            return INGREDIENT_ALIASES[t]
        # token substring
        token_hits = [n for n in names if t in _norm(n)]
        if token_hits:
            return sorted(token_hits, key=len, reverse=True)[0]

    return s

def resolve_spirit_name(user_input: str) -> str:
    """
    Resolve user input to a classic spirit key OR alcoholic ingredient.
    """
    s = _norm(user_input)
    if not s:
        return s

    s_key = s.replace(" ", "_")

    # classic spirit exact match
    if s in flavor_data.ALCOHOL_SUBCATEGORIES:
        return s

    if s_key in flavor_data.ALCOHOL_SUBCATEGORIES:
        return s_key

    # alcoholic ingredient exact match
    if (
        s in flavor_data.INGREDIENT_BY_NAME
        and flavor_data.INGREDIENT_BY_NAME[s].get("alcohol_type") in ["base", "modifier", "light"]
    ):
        return s

    if (
        s_key in flavor_data.INGREDIENT_BY_NAME
        and flavor_data.INGREDIENT_BY_NAME[s_key].get("alcohol_type") in ["base", "modifier", "light"]
    ):
        return s_key

    # alias match
    if s in SPIRIT_ALIASES:
        return SPIRIT_ALIASES[s]

    # substring match in classic spirits
    keys = list(flavor_data.ALCOHOL_SUBCATEGORIES.keys())
    candidates = [k for k in keys if _norm(k) in s or s in _norm(k)]
    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]

    # substring match in alcoholic ingredients
    ingredient_alcohols = [
        i["name"] for i in flavor_data.INGREDIENTS
        if i.get("alcohol_type") in ["base", "modifier", "light"]
    ]
    candidates = [n for n in ingredient_alcohols if _norm(n) in s or s in _norm(n)]
    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]

    return s

    # substring match
    keys = list(flavor_data.ALCOHOL_SUBCATEGORIES.keys())
    candidates = [k for k in keys if _norm(k) in s or s in _norm(k)]
    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]

    return s

TARGET_ML_DEFAULT = 90
ROUND_STEP = 5.0
MICRO_STEP = 2.5

CATEGORY_BIAS_PENALTIES = {
    "wine": -12,
    "fortified_wine": -9,
    "aperitif": -8,
    "liqueur": -5,
}

ALCOHOL_STACKING_PENALTY = -10

def get_ingredient_category(name: str) -> Optional[str]:
    """
    Lightweight category detection based on ingredient name.
    Keeps flavor_data untouched.
    """

    # wines
    if any(x in name for x in ["sauvignon", "chardonnay", "riesling", "prosecco", "champagne"]):
        return "wine"

    # fortified wines (vermouth, port, sherry...)
    if any(x in name for x in ["vermouth", "port", "sherry", "madeira"]):
        return "fortified_wine"

    # aperitifs (campari-style etc.)
    if any(x in name for x in ["campari", "aperol", "amaro"]):
        return "aperitif"

    # liqueurs
    if any(x in name for x in ["liqueur", "triple_sec", "cointreau", "curaçao"]):
        return "liqueur"

    return None

def is_alcoholic_ingredient(name: str) -> bool:
    return ing(name).get("alcohol_type") in ["base", "modifier", "light"]

def get_alcohol_type(name: str) -> str:
    """
    Distinguish between strong base spirits and soft/modifier alcohols.
    """

    # base spirits (hard alcohol)
    if name in flavor_data.ALCOHOL_SUBCATEGORIES:
        return "base"

    # fortified wines / aperitifs
    if any(x in name for x in ["vermouth", "sherry", "port", "amaro", "aperol", "campari"]):
        return "modifier"

    # liqueurs
    if any(x in name for x in ["liqueur", "triple_sec", "cointreau", "curaçao"]):
        return "modifier"

    # wine (still treat as alcohol but lighter role)
    if any(x in name for x in ["sauvignon", "chardonnay", "riesling", "prosecco", "champagne"]):
        return "light"

    return "other"

_PREPARATION_MAP = {
    "Sour": "Shake",
    "Highball": "Build",
    "Swizzle": "Build",
    "Signature": "Shake",
    "Spritz": "Build",
    "Short": "Stir",
}

def _preparation_for(title: str) -> str:
    for keyword, method in _PREPARATION_MAP.items():
        if keyword in title:
            return method
    return "Shake"


@dataclass
class VariantResult:
    title: str
    spirit: str
    key1: str
    key2: Optional[str]
    extras: List[str]                 # includes any auto-insert bridges
    amounts_ml: Dict[str, float]      # keys: "spirit", "key1", "key2"(optional), plus extras
    harmony_score: int
    direct_count: int
    bridge_count: int
    conflicts_count: int
    bridge_inserts: List[Tuple[str, str, str, str, bool, Optional[str]]]  # (fam_a, fam_b, bridge_family, ingredient, micro, reduced_sweet)
    notes: List[str]
    preparation: str = ""


# -----------------------------
# Compatibility / Scoring
# -----------------------------

def relation(a: str, b: str) -> Tuple[str, int, Optional[str]]:
    rel = flavor_data.COMPATIBILITY.get(a, {})
    if b in rel.get("direct", []):
        return ("direct", 5, None)
    if b in rel.get("bridge", {}):
        return ("bridgeable", 4, rel["bridge"][b])
    if b in rel.get("conflict", []):
        return ("conflict", -8, None)
    if b in rel.get("conditional", []):
        return ("conditional", 1, None)
    return ("neutral", 0, None)

def pair_score(a: str, b: str) -> int:
    # symmetric-ish robustness
    _, p1, _ = relation(a, b)
    _, p2, _ = relation(b, a)
    return p1 + p2


# -----------------------------
# Ingredient helpers
# -----------------------------

def ing(name: str) -> flavor_data.Ingredient:
    return flavor_data.INGREDIENT_BY_NAME[name]

def has_role(name: str, role: str) -> bool:
    return role in set(ing(name)["roles"])

def families_of(name: str) -> List[str]:
    return ing(name)["families"]

def taste_of(name: str) -> Dict[str, int]:
    return ing(name)["taste"]

def intensity_of(name: str) -> int:
    return ing(name)["intensity"]

def round_to_step(x: float, step: float) -> float:
    return round(x / step) * step


# -----------------------------
# Candidate scoring vs core
# -----------------------------

def ingredient_score_vs_core(ingredient_name: str, core_families: List[str], spirit: str, key_names: set[str]) -> int:
    score = 0
    if ingredient_name in key_names:
        return score
    for f in families_of(ingredient_name):
        for cf in core_families:
            # direction cf -> f
            _, pts, _ = relation(cf, f)
            score += pts

    # Soft anti-tropical bias for gin styles
    if "gin" in spirit.lower():
        tropic_names = {"pineapple", "passion_fruit", "mango", "banana"}
        if ingredient_name in tropic_names:
            score -= 12

    # --- Category bias penalty ---
    category = get_ingredient_category(ingredient_name)
    if category in CATEGORY_BIAS_PENALTIES:
        score += CATEGORY_BIAS_PENALTIES[category]

    # --- Alcohol stacking (smart) ---
    if is_alcoholic_ingredient(ingredient_name):
        alcohol_type = get_alcohol_type(ingredient_name)

        if alcohol_type == "base":
            score += ALCOHOL_STACKING_PENALTY  # strong penalty

        elif alcohol_type == "modifier":
            score -= 2  # small penalty (vermouth, liqueur are OK)

        elif alcohol_type == "light":
            score -= 4  # wine still discouraged, but less than base spirit

    return score

def is_too_wild_for_now(name: str) -> bool:
    # MVP: keep avant-garde out unless explicitly chosen as key
    fams = set(families_of(name))
    if "umami_fermented" in fams or "umami_vegetal" in fams:
        return True
    if name in {"miso", "black_garlic", "seaweed", "tomato"}:
        return True
    return False


# -----------------------------
# Role buckets
# -----------------------------

def bucket_role(name: str) -> str:
    roles = set(ing(name)["roles"])
    if "acid" in roles:
        return "acid"
    if "sweet" in roles:
        return "sweet"
    if "accent" in roles:
        return "accent"
    # support/aromatic/bridge/dry etc.
    if "aromatic" in roles or "support" in roles or "bridge" in roles or "dry" in roles:
        return "support"
    return "other"


def build_buckets(core_families: List[str], exclude_names: set[str], spirit: str) -> Dict[str, List[Tuple[int, str]]]:
    buckets = {"acid": [], "sweet": [], "support": [], "accent": []}

    for item in flavor_data.INGREDIENTS:
        name = item["name"]
        if name in exclude_names:
            continue
        if is_too_wild_for_now(name):
            continue

        b = bucket_role(name)
        if b in buckets:
            buckets[b].append((ingredient_score_vs_core(name, core_families, spirit, exclude_names), name))
    for b in buckets:
        buckets[b].sort(reverse=True, key=lambda x: x[0])

    return buckets

# -----------------------------
# Variant building (Top 3)
# -----------------------------

def pick_from(bucket: List[Tuple[int, str]], avoid: set[str], n_pool: int) -> Optional[str]:
    pool = [name for _s, name in bucket[:n_pool] if name not in avoid]
    return random.choice(pool) if pool else None


def generate_base_variants(spirit: str, key1: str, key2: Optional[str]) -> List[Tuple[str, List[str]]]:
    """
    Returns list of (title, extras) where extras exclude spirit and keys.
    """
    if spirit in flavor_data.ALCOHOL_SUBCATEGORIES:
        spirit_fams = flavor_data.ALCOHOL_SUBCATEGORIES[spirit]
    else:
        spirit_fams = families_of(spirit)

    core_fams = spirit_fams + families_of(key1) + (families_of(key2) if key2 else [])
    exclude = {key1} | ({key2} if key2 else set())

    buckets = build_buckets(core_fams, exclude_names=exclude, spirit=spirit)

    # Build cocktail style variants:
    # 1) Sour
    # 2) Highball / Swizzle
    # 3) signature twist
    # 4) Spritz
    # 5) Short Cocktail

    variants: List[Tuple[str, List[str]]] = []

    # V1 – Sour

    # true sour component only
    sour_pool = [
        name for name in ["lemon", "lime", "yuzu", "calamansi", "bergamot", "grapefruit"]
        if name not in exclude
    ]

    v1_acid = random.choice(sour_pool) if sour_pool else None

    # sweet only NON-alcoholic AND real sweeteners
    sweet_pool = [
        name for _s, name in buckets["sweet"]
        if (not is_alcoholic_ingredient(name)) and ("identity" not in set(ing(name)["roles"]))
    ]

    v1_sweet = sweet_pool[0] if sweet_pool else None

    # egg white is mandatory for Sour
    v1_egg_white = "egg_white" if "egg_white" not in exclude else None

    extras1 = [x for x in [v1_acid, v1_sweet, v1_egg_white] if x]

    variants.append(("Variant 1 (Sour)", extras1))

    # V2 – Highball / Swizzle

    # acid (light citrus)
    v2_acid = pick_from(buckets["acid"], avoid=set(), n_pool=5)

    # sweet (light, fresh — klidně může být i lehký fruit)
    sweet_pool = [
    name for _s, name in buckets["sweet"]
    if not is_alcoholic_ingredient(name)
    ]

    v2_sweet = random.choice(sweet_pool[:5]) if sweet_pool else None

    # fresh / cooling / herbal element (KLÍČ)
    fresh_candidates = [
    item["name"] for item in flavor_data.INGREDIENTS
    if item["name"] not in exclude
    and not is_alcoholic_ingredient(item["name"])
    and any(f in item["families"] for f in ["green_leafy", "terpene_herbal", "menthol_cooling"])
    ]

    v2_fresh = random.choice(fresh_candidates[:8]) if fresh_candidates else None
    extras2 = [x for x in [v2_acid, v2_sweet, v2_fresh] if x]

    variants.append(("Variant 2 (Highball / Swizzle)", extras2))

    # V3
    v3_acid = pick_from(buckets["acid"], avoid=set(), n_pool=5)
    v3_sweet = pick_from(buckets["sweet"], avoid=set(), n_pool=5)
    # accent (prefer intensity <=4)
    # accent – controlled selection

    accent_candidates = []

    for _s, name in buckets["accent"][:15]:
        if is_alcoholic_ingredient(name):
            continue

        # skip too dominant accents
        if intensity_of(name) > 4:
            continue

        # skip problematic families (hard to control)
        fams = set(families_of(name))
        if "sulfuric_pungent" in fams:
            continue

        accent_candidates.append(name)

    v3_accent = random.choice(accent_candidates) if accent_candidates else None
    extras3 = [x for x in [v3_acid, v3_sweet, v3_accent] if x]
    variants.append(("Variant 3 (Signature Twist)", extras3))

    # V4 – Spritz

    # soft/modifier alcohol: aperitif, liqueur, fortified wine
    spritz_modifier_pool = [
        item["name"] for item in flavor_data.INGREDIENTS
        if item["name"] not in exclude
        and item.get("alcohol_type") == "modifier"
        and any(f in item["families"] for f in ["terpene_citrus", "floral_ionone", "ester_fruity"])
        and not any(f in item["families"] for f in ["umami_fermented", "pyrazine_roasted"])
    ]

    v4_modifier = random.choice(spritz_modifier_pool[:8]) if spritz_modifier_pool else None

    # sparkling wine component
    sparkling_pool = [
    item["name"] for item in flavor_data.INGREDIENTS
    if item["name"] not in exclude
    and item.get("alcohol_type") == "light"
    and any(x in item["name"] for x in ["prosecco", "champagne", "cava", "cremant", "sparkling", "pet_nat"])
    ]

    v4_sparkling = random.choice(sparkling_pool) if sparkling_pool else None

    # citrus / fresh lift
    v4_citrus = pick_from(buckets["acid"], avoid=set(), n_pool=5)

    extras4 = [x for x in [v4_modifier, v4_sparkling, v4_citrus] if x]

    variants.append(("Variant 4 (Spritz)", extras4))

    # V5 – Short Cocktail

    # modifier alcohol: vermouth / aperitif / liqueur / fortified
    short_modifier_pool = [
        item["name"] for item in flavor_data.INGREDIENTS
        if item["name"] not in exclude
        and item.get("alcohol_type") == "modifier"
    ]

    v5_modifier = random.choice(short_modifier_pool[:10]) if short_modifier_pool else None

    # bitter / aromatic / accent element, non-fruit, non-acid
    short_accent_pool = [
        item["name"] for item in flavor_data.INGREDIENTS
        if item["name"] not in exclude
        and not is_alcoholic_ingredient(item["name"])
        and (
            "accent" in item["roles"]
            or "aromatic" in item["roles"]
            or item["taste"].get("bitter", 0) >= 2
        )
        and "acid" not in item["roles"]
        and "sweet" not in item["roles"]
        and "identity" not in item["roles"]
    ]

    v5_accent = random.choice(short_accent_pool[:10]) if short_accent_pool else None

    extras5 = [x for x in [v5_modifier, v5_accent] if x]

    variants.append(("Variant 5 (Short Cocktail)", extras5))

    # de-duplicate within each variant
    cleaned = []
    for title, extras in variants:
        seen = set()
        uniq = []
        for e in extras:
            if e not in seen:
                uniq.append(e)
                seen.add(e)
        cleaned.append((title, uniq))

    return cleaned

# -----------------------------
# Bridge detection + micro insert
# -----------------------------

def find_bridge_needs(spirit_fams: List[str], key_fams: List[str], extras: List[str]) -> List[Tuple[str, str, str]]:
    present_families = set()
    for n in extras:
        present_families.update(families_of(n))

    bridges = []
    for e in extras:
        efams = families_of(e)

        for sf in spirit_fams:
            for ef in efams:
                rtype, _pts, br = relation(sf, ef)
                if rtype == "bridgeable" and br:
                    bridges.append((sf, ef, br))

        for kf in key_fams:
            for ef in efams:
                rtype, _pts, br = relation(kf, ef)
                if rtype == "bridgeable" and br:
                    bridges.append((kf, ef, br))

    # unique + not covered
    uniq = []
    seen = set()
    for a, b, br in bridges:
        sig = (a, b, br)
        if sig in seen:
            continue
        seen.add(sig)
        if br in present_families:
            continue
        uniq.append((a, b, br))
    return uniq

def best_bridge_ingredient(fam_a: str, fam_b: str, bridge_family: str, excluded: set[str]) -> Optional[str]:
    best_name = None
    best_score = -10**9

    for item in flavor_data.INGREDIENTS:
        name = item["name"]
        if name in excluded:
            continue
        if bridge_family not in item["families"]:
            continue

        s = 0
        for f in item["families"]:
            s += pair_score(fam_a, f)
            s += pair_score(fam_b, f)

        if "bridge" in item["roles"]:
            s += 2
        if "accent" in item["roles"] and item["intensity"] >= 4:
            s -= 3

        if s > best_score:
            best_score = s
            best_name = name

    return best_name

def first_sweet_in_recipe(extras: List[str]) -> Optional[str]:
    # Prefer sweet modifiers over identity-sweets (e.g., prefer agave/honey over mango)
    sweet_modifiers = []
    sweet_any = []
    for n in extras:
        roles = set(ing(n)["roles"])
        if "sweet" in roles:
            sweet_any.append(n)
            if "identity" not in roles:
                sweet_modifiers.append(n)
    if sweet_modifiers:
        return sweet_modifiers[0]
    return sweet_any[0] if sweet_any else None

    return None

def auto_insert_bridges(spirit_fams: List[str], key_fams: List[str], key_names: set[str], extras: List[str]) -> Tuple[List[str], List[Tuple[str, str, str, str, bool, Optional[str]]]]:
    extras2 = copy.deepcopy(extras)
    inserted: List[Tuple[str, str, str, str, bool, Optional[str]]] = []

    needs = find_bridge_needs(spirit_fams, key_fams, extras2)
    if not needs:
        return extras2, inserted

    excluded = set(extras2) | set(key_names)
    existing_sweet = first_sweet_in_recipe(extras2)
    micro_sweet_used = False

    for fam_a, fam_b, bridge_family in needs:
        cand = best_bridge_ingredient(fam_a, fam_b, bridge_family, excluded)
        if not cand:
            continue
        if cand in extras2:
            continue
        # block alcoholic bridges if recipe is Sour (no alcohol in extras)
        if all(not is_alcoholic_ingredient(e) for e in extras2):
            if is_alcoholic_ingredient(cand):
                continue

        micro = has_role(cand, "sweet")  # sweet bridges become micro by default
        if micro and micro_sweet_used:
            continue

        extras2.append(cand)
        excluded.add(cand)

        # if micro and we already have sweet, we will later subtract 2.5 from that sweet
        reduced_sweet = existing_sweet if (micro and existing_sweet) else None
        inserted.append((fam_a, fam_b, bridge_family, cand, micro, reduced_sweet))
        if micro:
            micro_sweet_used = True

    return extras2, inserted


# -----------------------------
# Harmony analysis (counts + score)
# -----------------------------

def analyze_harmony(spirit_fams: List[str], key_fams: List[str], extras: List[str]) -> Tuple[int, int, int, int]:
    total = 0
    direct = 0
    bridgeable = 0
    conflicts = 0

    for e in extras:
        efams = families_of(e)
        for sf in spirit_fams:
            for ef in efams:
                rtype, pts, _br = relation(sf, ef)
                total += pts
                if rtype == "direct":
                    direct += 1
                elif rtype == "bridgeable":
                    bridgeable += 1
                elif rtype == "conflict":
                    conflicts += 1

        for kf in key_fams:
            for ef in efams:
                rtype, pts, _br = relation(kf, ef)
                total += pts
                if rtype == "direct":
                    direct += 1
                elif rtype == "bridgeable":
                    bridgeable += 1
                elif rtype == "conflict":
                    conflicts += 1

    # --- Structure / balance penalties ---
    acid_count = sum(1 for e in extras if has_role(e, "acid"))
    sweet_count = sum(1 for e in extras if has_role(e, "sweet"))
    accent_count = sum(1 for e in extras if has_role(e, "accent"))

    if acid_count > 1:
        total -= 8

    if sweet_count == 0:
        total -= 10

    if accent_count > 1:
        total -= 4

    return total, direct, bridgeable, conflicts


# -----------------------------
# ml allocation (pre-dilution)
# -----------------------------

def base_allocate_ml(extras: List[str], target_ml: int) -> Dict[str, float]:
    """
    Simple bar-friendly allocation you tuned:
    - key1 fixed at 20 ml (entity-level)
    - acid 10 ml each
    - sweet 15 ml each
    - support 5 ml each
    - accent 2.5 ml each
    - spirit = rest
    """
    ml: Dict[str, float] = {}
    acids = [n for n in extras if has_role(n, "acid")]
    sweets = [n for n in extras if has_role(n, "sweet")]
    accents = [n for n in extras if has_role(n, "accent")]
    supports = [n for n in extras if n not in acids and n not in sweets and n not in accents]

    for a in acids:
        ml[a] = 10.0
    for s in sweets:
        roles = set(ing(s)["roles"])
        ml[s] = 15.0 if "identity" in roles else 10.0
    for s in supports:
        ml[s] = 5.0
    for a in accents:
        ml[a] = 2.5

    return ml

def apply_micro_bridge_adjustments(extras: List[str], ml: Dict[str, float], inserted, target_ml: int) -> Dict[str, float]:
    """
    If we inserted a sweet bridge as micro(2.5), subtract 2.5 from an existing sweet (if present).
    """
    for fam_a, fam_b, br, name, micro, reduced_sweet in inserted:
        if micro:
            ml[name] = 2.5
            if reduced_sweet and reduced_sweet in ml:
                ml[reduced_sweet] = max(0.0, ml[reduced_sweet] - 2.5)
        else:
            ml[name] = 5.0
    return ml

def finalize_rounding(spirit_ml: float, key1_ml: float, key2_ml: float, extras: List[str], extras_ml: Dict[str, float], target_ml: int) -> Dict[str, float]:
    rounded: Dict[str, float] = {}
    rounded["spirit"] = round_to_step(spirit_ml, MICRO_STEP)
    rounded["key1"] = round_to_step(key1_ml, ROUND_STEP)
    if key2_ml > 0:
        rounded["key2"] = round_to_step(key2_ml, ROUND_STEP)

    for n in extras:
        v = extras_ml.get(n, 0.0)
        if has_role(n, "accent") or v <= 2.5:
            rounded[n] = round_to_step(v, MICRO_STEP)
        else:
            rounded[n] = round_to_step(v, ROUND_STEP)

    # do not correct remainder into spirit
    return rounded

def recalc_amounts_ml(
    spirit: str,
    key1: str,
    key2: Optional[str],
    extras: List[str],
    target_ml: int,
    bridge_inserts,
) -> Dict[str, float]:
    """
    Recompute amounts_ml for an already-chosen variant (same extras),
    when the user changes target_ml in UI.
    """
    # base role allocations for extras
    extras_ml = base_allocate_ml(extras, target_ml)

    # spirit/key fixed allocations (key1=20, key2=10 if present) then spirit = rest
    key1_ml = 20.0
    key2_ml = 10.0 if key2 else 0.0

    # apply micro-bridge adjustments (subtract 2.5 from existing sweet if needed)
    extras_ml = apply_micro_bridge_adjustments(extras, extras_ml, bridge_inserts, target_ml)

    # compute spirit remainder
    spirit_ml = float(target_ml) - key1_ml - key2_ml - sum(extras_ml.values())
    if spirit_ml < 0:
        spirit_ml = 0.0

    # round to steps and return final dict with all items
    final = finalize_rounding(
        spirit_ml=spirit_ml,
        key1_ml=key1_ml,
        key2_ml=key2_ml,
        extras=extras,
        extras_ml=extras_ml,
        target_ml=target_ml,
    )
    return final

# -----------------------------
# ABV-based spirit volume
# -----------------------------

def calc_spirit_ml(spirit: str, build_rule: dict, title: str = "") -> float:
    """
    Calculate spirit volume so the drink hits target ABV.
    Formula: spirit_ml = (target_abv% * target_ml) / spirit_abv%
    Clamped to [15, 60] ml and rounded to 2.5 ml steps.
    """
    if spirit in flavor_data.ALCOHOL_ABV:
        spirit_abv = flavor_data.ALCOHOL_ABV[spirit]
    elif spirit in flavor_data.INGREDIENT_BY_NAME:
        spirit_abv = float(flavor_data.INGREDIENT_BY_NAME[spirit].get("abv", 40.0))
    else:
        spirit_abv = 40.0

    # modifier alcohol in Highball → fixed 45 ml
    if "Highball" in title and spirit_abv < 30:
        return 45.0

    target_abv = float(build_rule.get("target_abv", 18))
    target_ml = float(build_rule.get("target_ml", 90))

    raw = (target_abv / 100.0 * target_ml) / (spirit_abv / 100.0)
    return max(15.0, min(60.0, round_to_step(raw, MICRO_STEP)))


# -----------------------------
# Top-up selection
# -----------------------------

def pick_top_up(spirit: str, title: str, spirit_families: List[str]) -> Optional[str]:
    if "Spritz" in title:
        return "soda_water"
    if "Highball" in title:
        s = spirit.lower()
        if "gin" in s:
            return "tonic_water"
        if "rum" in s or "tequila" in s:
            return "ginger_beer"
        if "whisky" in s or "whiskey" in s or "bourbon" in s:
            return "ginger_ale"
        return "soda_water"
    return None


# -----------------------------
# Public function
# -----------------------------

def generate(spirit: str, key1: str, key2: Optional[str] = None, target_ml: int = TARGET_ML_DEFAULT, seed: Optional[int] = None) -> List[VariantResult]:
   
    # Resolve user-friendly inputs (substring + aliases)
    spirit = resolve_spirit_name(spirit)
    key1 = resolve_ingredient_name(key1)
    key2 = resolve_ingredient_name(key2) if key2 else None

    if seed is not None:
        random.seed(seed)

    spirit_is_classic = spirit in flavor_data.ALCOHOL_SUBCATEGORIES
    spirit_is_ingredient_alcohol = (
        spirit in flavor_data.INGREDIENT_BY_NAME
        and ing(spirit).get("alcohol_type") in ["base", "modifier", "light"]
    )

    if not spirit_is_classic and not spirit_is_ingredient_alcohol:
        raise ValueError(f"Unknown spirit/core alcohol: {spirit}")

    if key1 not in flavor_data.INGREDIENT_BY_NAME:
        raise ValueError(f"Unknown key1 ingredient: {key1}")

    if key2 and key2 not in flavor_data.INGREDIENT_BY_NAME:
        raise ValueError(f"Unknown key2 ingredient: {key2}")

    if spirit_is_classic:
        spirit_fams = flavor_data.ALCOHOL_SUBCATEGORIES[spirit]
    else:
        spirit_fams = families_of(spirit)

    key_fams = families_of(key1) + (families_of(key2) if key2 else [])
    key_names = {key1} | ({key2} if key2 else set())

    base_variants = generate_base_variants(spirit, key1, key2)

    _MODIFIER_KEYWORDS = ("vermouth", "amaro", "aperitif", "campari", "aperol", "quinquina", "gentian")
    spirit_is_modifier = (
        (
            spirit in flavor_data.INGREDIENT_BY_NAME
            and ing(spirit).get("alcohol_type") == "modifier"
        )
        or any(kw in spirit for kw in _MODIFIER_KEYWORDS)
    )

    results: List[VariantResult] = []
    for title, extras in base_variants:
        build_rule = get_category_build_rule(title)

        target_ml_local = int(build_rule.get("target_ml", target_ml))
        target_abv_local = float(build_rule["target_abv"])

        # HARD rule for Sour: no alcohol in extras
        if "Sour" in title:
            extras = [e for e in extras if not is_alcoholic_ingredient(e)]

        # 1) auto bridge insert
        extras2, inserts = auto_insert_bridges(spirit_fams, key_fams, key_names, extras)

        # Spritz cleanup: remove non-sparkling light alcohol (still wines)
        if "Spritz" in title:
            extras2 = [
                n for n in extras2
                if not (
                    ing(n).get("alcohol_type") == "light"
                    and not any(x in n for x in ["champagne", "prosecco", "cava", "pet_nat", "cremant"])
                )
            ]

            # Spritz rule: allow only one sparkling component
            sparkling = [
                n for n in extras2
                if any(x in n for x in ["champagne", "prosecco", "cava", "pet_nat", "cremant"])
            ]

            if len(sparkling) > 1:
                keep = sparkling[0]
                extras2 = [n for n in extras2 if n not in sparkling or n == keep]

        # HARD rule for Sour: remove any alcohol after bridges
        if "Sour" in title:
            extras2 = [e for e in extras2 if not is_alcoholic_ingredient(e)]

        # 2) ml allocation
        key1_ml = 20.0
        if not key2:
            key2_ml = 0.0
        else:
            r = set(ing(key2)["roles"])
            # aromatic/accent key2 (mint/basil/pepper) should be small in volume
            key2_ml = 5.0 if ("accent" in r or "aromatic" in r) else 10.0

        if "Spritz" in title:
            extras_ml = {}

            for n in extras2:
                alcohol_type = ing(n).get("alcohol_type")

                if alcohol_type == "modifier":
                    extras_ml[n] = 15.0
                elif alcohol_type == "light":
                    extras_ml[n] = 30.0
                elif has_role(n, "acid"):
                    extras_ml[n] = 5.0
                elif has_role(n, "accent"):
                    extras_ml[n] = 2.5
                else:
                    extras_ml[n] = 5.0
        else:
            extras_ml = base_allocate_ml(extras2, target_ml_local)
            extras_ml = apply_micro_bridge_adjustments(extras2, extras_ml, inserts, target_ml_local) 

        # compute spirit from category build rule
        non_spirit_total = key1_ml + key2_ml + sum(extras_ml.get(n, 0.0) for n in extras2)

        if "Spritz" in title:
            if spirit in flavor_data.ALCOHOL_ABV:
                _spirit_abv = flavor_data.ALCOHOL_ABV[spirit]
            elif spirit in flavor_data.INGREDIENT_BY_NAME:
                _spirit_abv = float(flavor_data.INGREDIENT_BY_NAME[spirit].get("abv", 40.0))
            else:
                _spirit_abv = 40.0
            spirit_ml = 0.0 if _spirit_abv < 35.0 else 30.0
        else:
            spirit_ml = calc_spirit_ml(spirit, {**build_rule, "target_ml": float(target_ml_local)}, title)

        # rounding
        amounts = finalize_rounding(spirit_ml, key1_ml, key2_ml, extras2, extras_ml, target_ml_local)

        if "Spritz" in title and spirit_is_modifier:
            amounts["modifier_ml"] = 45.0

        # top-up fill for Highball and Spritz
        current_total = sum(amounts.values())
        missing_ml = round(float(target_ml_local) - current_total, 6)

        if missing_ml > 5 and ("Highball" in title or "Spritz" in title):
            top_up_name = pick_top_up(spirit, title, spirit_fams)
            if top_up_name:
                amounts[top_up_name] = amounts.get(top_up_name, 0.0) + missing_ml
                if top_up_name not in extras2:
                    extras2.append(top_up_name)

        # Universal total correction: ensure amounts sum exactly to target_ml_local
        current_total = sum(amounts.values())
        diff = round(float(target_ml_local) - current_total, 6)

        if abs(diff) >= 0.001:
            if "Spritz" in title:
                sparkling_items = [
                    k for k in amounts
                    if any(x in k for x in ["prosecco", "champagne", "cava", "cremant", "sparkling", "pet_nat"])
                ]
                adjust_key = sparkling_items[0] if sparkling_items else max(amounts, key=lambda k: amounts[k])
            elif "Highball" in title and diff > 0:
                top_up_name = pick_top_up(spirit, title, spirit_fams)
                adjust_key = top_up_name if (top_up_name and top_up_name in amounts) else max(amounts, key=lambda k: amounts[k])
            else:
                adjust_key = max(amounts, key=lambda k: amounts[k])
            amounts[adjust_key] = round(amounts[adjust_key] + diff, 6)

        # 3) harmony analysis (on final extras)
        harmony, direct, bridgeable, conflicts = analyze_harmony(spirit_fams, key_fams, extras2)

        notes = []

        notes.append(f"Target volume: {target_ml_local} ml")
        notes.append(f"Target ABV: {target_abv_local:.1f} %")

        if conflicts == 0:
            notes.append("✅ Bez tvrdých konfliktů.")
        else:
            notes.append("⚠️ Detekován konflikt (v dalším kroku lze léčit bridge).")

        results.append(
            VariantResult(
                title=title,
                spirit=spirit,
                key1=key1,
                key2=key2,
                extras=extras2,
                amounts_ml=amounts,
                harmony_score=harmony,
                direct_count=direct,
                bridge_count=bridgeable,
                conflicts_count=conflicts,
                bridge_inserts=inserts,
                notes=notes,
                preparation=_preparation_for(title),
            )
        )

    return results
