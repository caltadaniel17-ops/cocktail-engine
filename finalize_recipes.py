import copy
import flavor_data

TARGET_ML = 90
ROUND_STEP = 5
MICRO_STEP = 2.5

spirit_name = "aged_rum"
key_name = "pineapple"

base_variants = [
    ("Variant 1 (bright + floral)", ["yuzu", "elderflower", "ginger"]),
    ("Variant 2 (tropical punch)", ["passion_fruit", "mango"]),
    ("Variant 3 (signature twist)", ["lime", "honey", "oyster_shell"]),
]

spirit_fams = flavor_data.ALCOHOL_SUBCATEGORIES[spirit_name]
key_fams = flavor_data.INGREDIENT_BY_NAME[key_name]["families"]

def relation(a, b):
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

def pair_score(a, b) -> int:
    _, p1, _ = relation(a, b)
    _, p2, _ = relation(b, a)
    return p1 + p2

def best_bridge_ingredient(fam_a, fam_b, bridge_family, excluded_names):
    best = None
    best_score = -10**9
    for ing in flavor_data.INGREDIENTS:
        if ing["name"] in excluded_names:
            continue
        if bridge_family not in ing["families"]:
            continue
        s = 0
        for f in ing["families"]:
            s += pair_score(fam_a, f)
            s += pair_score(fam_b, f)
        if "bridge" in ing["roles"]:
            s += 2
        if s > best_score:
            best_score = s
            best = ing["name"]
    return best

def find_bridge_needs(extras):
    present_families = set()
    for n in extras:
        present_families.update(flavor_data.INGREDIENT_BY_NAME[n]["families"])

    bridges = []
    for e in extras:
        efams = flavor_data.INGREDIENT_BY_NAME[e]["families"]
        for sf in spirit_fams:
            for ef in efams:
                rtype, _, br = relation(sf, ef)
                if rtype == "bridgeable":
                    bridges.append((sf, ef, br))
        for kf in key_fams:
            for ef in efams:
                rtype, _, br = relation(kf, ef)
                if rtype == "bridgeable":
                    bridges.append((kf, ef, br))

    unique = []
    seen = set()
    for a, b, br in bridges:
        sig = (a, b, br)
        if sig in seen:
            continue
        seen.add(sig)
        if br in present_families:
            continue
        unique.append((a, b, br))
    return unique

def first_sweet_in_recipe(extras):
    for n in extras:
        if "sweet" in flavor_data.INGREDIENT_BY_NAME[n]["roles"]:
            return n
    return None

def round_to_step(x: float, step: float) -> float:
    return round(x / step) * step

def classify(extras):
    acids, sweets, accents, supports = [], [], [], []
    for n in extras:
        roles = set(flavor_data.INGREDIENT_BY_NAME[n]["roles"])
        if "acid" in roles:
            acids.append(n)
        elif "sweet" in roles:
            sweets.append(n)
        elif "accent" in roles:
            accents.append(n)
        else:
            supports.append(n)
    return acids, sweets, supports, accents

def base_allocate(extras):
    """
    Simple bar-friendly base allocation (before micro bridges).
    spirit dominant. Pre-dilution.
    """
    acids, sweets, supports, accents = classify(extras)

    # Start profile (you tuned this already via balance):
    # spirit 40-50, key 20, acid ~10, sweet 15-20 depending
    # We'll do a simple role-based baseline, then normalize to TARGET.
    ml = {"spirit": 0, "key": 0}

    ml["key"] = 20  # keep key stable for now (pineapple entity)
    # acid
    for a in acids:
        ml[a] = 10
    # sweet
    for s in sweets:
        ml[s] = 15
    # support
    for s in supports:
        ml[s] = 5
    # accent
    for a in accents:
        ml[a] = 2.5

    # spirit is the rest
    total_non_spirit = ml["key"] + sum(ml[n] for n in extras)
    ml["spirit"] = TARGET_ML - total_non_spirit

    return ml

def apply_micro_bridge(extras, ml, inserted):
    """
    Inserted entries are tuples (fam_a, fam_b, bridge_family, ingredient_name, micro, existing_sweet)
    If micro True: set bridge ingredient to 2.5ml and subtract 2.5 from existing sweet.
    """
    for (_a, _b, _br, name, micro, existing_sweet) in inserted:
        if not micro:
            ml[name] = 5
            continue

        ml[name] = 2.5
        if existing_sweet and existing_sweet in ml:
            ml[existing_sweet] = max(0, ml[existing_sweet] - 2.5)

    # re-balance spirit to keep total exact
    total = ml["key"] + sum(ml[n] for n in extras) + sum(ml.get(x[3], 0) for x in inserted)
    ml["spirit"] = TARGET_ML - total
    return ml

def finalize_rounding(extras, ml):
    """
    Round:
    - accent or micro-sized things stay 2.5 step
    - others to 5 ml
    Then fix diff into spirit.
    """
    rounded = {}
    rounded["key"] = round_to_step(ml["key"], ROUND_STEP)

    # We don't know here which were micro bridges; just keep <=2.5 on MICRO_STEP
    for n in extras:
        roles = set(flavor_data.INGREDIENT_BY_NAME[n]["roles"])
        if "accent" in roles or ml[n] <= 2.5:
            rounded[n] = round_to_step(ml[n], MICRO_STEP)
        else:
            rounded[n] = round_to_step(ml[n], ROUND_STEP)

    rounded["spirit"] = round_to_step(ml["spirit"], MICRO_STEP)

    # final correction to hit target
    total = rounded["key"] + rounded["spirit"] + sum(rounded[n] for n in extras)
    rounded["spirit"] += (TARGET_ML - total)
    return rounded

def auto_insert_bridges(extras):
    extras2 = copy.deepcopy(extras)
    inserted = []

    needs = find_bridge_needs(extras2)
    if not needs:
        return extras2, inserted

    excluded = set(extras2) | {key_name}
    existing_sweet = first_sweet_in_recipe(extras2)

    for fam_a, fam_b, bridge_family in needs:
        candidate = best_bridge_ingredient(fam_a, fam_b, bridge_family, excluded)
        if not candidate:
            continue
        if candidate in extras2:
            continue
        roles = set(flavor_data.INGREDIENT_BY_NAME[candidate]["roles"])
        micro = "sweet" in roles  # sweet bridges become micro
        extras2.append(candidate)
        excluded.add(candidate)
        inserted.append((fam_a, fam_b, bridge_family, candidate, micro, existing_sweet))

    return extras2, inserted

def print_recipe(title, extras, amounts, inserted):
    print("\n" + "="*60)
    print(title)
    print("="*60)
    print(f"Target: {TARGET_ML} ml (pre-dilution)")
    print(f"- {spirit_name}: {amounts['spirit']} ml (STRUCTURE)")
    print(f"- {key_name}: {amounts['key']} ml (IDENTITY)")
    for n in extras:
        ing = flavor_data.INGREDIENT_BY_NAME[n]
        roles = ", ".join(ing["roles"][:2])
        print(f"- {n}: {amounts[n]} ml ({roles})")
    total = amounts["spirit"] + amounts["key"] + sum(amounts[n] for n in extras)
    print("Total:", total, "ml")

    if inserted:
        print("\nBRIDGE INSERTS:")
        for a, b, br, name, micro, existing_sweet in inserted:
            tag = "micro 2.5ml" if micro else "5ml"
            print(f"- {a} ↔ {b} (bridge {br}) → {name} [{tag}]")
            if micro and existing_sweet:
                print(f"  (ubráno 2.5 ml z {existing_sweet})")

for title, extras in base_variants:
    # 1) auto insert bridges
    new_extras, inserted = auto_insert_bridges(extras)

    # 2) base allocate ml
    ml = base_allocate(new_extras)

    # 3) apply micro bridge adjustments
    ml = apply_micro_bridge(new_extras, ml, inserted)

    # 4) rounding + final correction
    amounts = finalize_rounding(new_extras, ml)

    # 5) print
    print_recipe(title, new_extras, amounts, inserted)
