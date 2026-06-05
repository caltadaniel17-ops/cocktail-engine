# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the project

**Streamlit UI (main interface):**
```bash
streamlit run app.py
```

**CLI runner (quick testing with hardcoded inputs):**
```bash
python run.py
```

**Tests and validation:**
```bash
python smoke_test.py        # DB integrity check (required keys, types, duplicates)
python compat_test.py       # Compatibility graph coverage check
python stress_test.py       # Engine integration tests (5 fixed + 10 random combos)
python test.py              # Manual variant analysis with bridge suggestions
python bridge_insert_test.py  # Bridge auto-insert debug output
python finalize_recipes.py    # ML allocation + rounding pipeline debug
```

## Architecture

This is a **cocktail recipe generation engine** with a Streamlit UI. There is no test framework — all tests are plain Python scripts run directly.

### Core data flow

```
User picks: spirit + key1 (+ optional key2) + target_ml
    ↓
engine.generate()
    ↓
generate_base_variants()  → 5 style variants (Sour, Highball, Signature, Spritz, Short)
    ↓ per variant:
auto_insert_bridges()     → detect flavor gaps, insert bridging ingredients
    ↓
base_allocate_ml()        → role-based ml allocation (acid=10, sweet=10-15, accent=2.5, etc.)
apply_micro_bridge_adjustments()  → adjust sweet amounts when bridge is micro
finalize_rounding()       → round to 5ml / 2.5ml steps
    ↓
analyze_harmony()         → compute harmony score, direct/bridge/conflict counts
    ↓
List[VariantResult]       → rendered by app.py or run.py
```

### Key files

- **`flavor_data.py`** — pure data layer. Contains: `FAMILIES` (19 molecular flavor families), `COMPATIBILITY` (family-to-family compatibility graph with direct/bridge/conditional/conflict), `ALCOHOL_SUBCATEGORIES` (spirit → family list), `INGREDIENTS` (full ingredient DB with families, roles, taste vectors, intensity), and UI lookup dicts (`UI_CATEGORY_BY_NAME`, `UI_SUBCATEGORY_BY_NAME`, `UI_INGREDIENT_CATEGORY_BY_NAME`). **No logic lives here.**

- **`engine.py`** — all generation logic. Public entry point is `engine.generate(spirit, key1, key2, target_ml, seed)` returning `List[VariantResult]`. Also exports `recalc_amounts_ml()` for live target_ml updates in the UI without regenerating variants.

- **`app.py`** — Streamlit UI. Sidebar inputs feed into `engine.generate()`. Stores results in `st.session_state.results` so "Generate more" appends variants. Recalculates ml on target_ml change via `engine.recalc_amounts_ml()` without touching the variant structure.

### Flavor compatibility model

Ingredients are mapped to 1–3 **molecular flavor families** (e.g. `terpene_citrus`, `ester_fruity`). The `COMPATIBILITY` graph defines family-to-family relationships:
- **direct** (+5 pts): flavors work immediately together
- **bridgeable** (+4 pts): flavors need a bridging family to connect
- **conditional** (+1 pt): works only in specific contexts
- **conflict** (−8 pts): flavors clash

**Bridge insertion**: when a spirit family and an extra ingredient family are "bridgeable", the engine finds the best ingredient from the DB that contains the bridge family and auto-inserts it at 2.5ml (micro) or 5ml.

### Ingredient roles

Roles drive ml allocation in `base_allocate_ml()`:
- `acid` → 10ml
- `sweet` + `identity` role → 15ml, otherwise 10ml  
- `accent` → 2.5ml
- `support`/`aromatic`/`bridge`/`dry` → 5ml

Spirit is always the remainder (`target_ml - sum(non-spirit)`).

### Spirit resolution

`resolve_spirit_name()` and `resolve_ingredient_name()` accept fuzzy user input: exact match → alias lookup (`SPIRIT_ALIASES`, `INGREDIENT_ALIASES`) → substring match → token-based fallback. Classic spirits live in `ALCOHOL_SUBCATEGORIES`; alcoholic ingredients (vermouth, liqueurs, wine) live in `INGREDIENTS` with `alcohol_type` field (`"base"`, `"modifier"`, `"light"`).

### Category build rules

`CATEGORY_BUILD_RULES` in `flavor_data.py` stores per-style target volumes and ABV. `get_category_build_rule()` in `engine.py` matches variant title to the rule dict.

### Style-specific hard rules

- **Sour**: no alcohol in extras (enforced before and after bridge insertion)
- **Spritz**: only one sparkling component; spirit_ml=0 if a modifier alcohol is present; top-up added if volume is short
- **Highball**: `top_up` key added to amounts if volume is short
- **Short Cocktail**: modifier alcohol + bitter/aromatic accent, no acid/sweet structure
