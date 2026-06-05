import flavor_data

spirit_name = "aged_rum"
key_name = "pineapple"

variants = [
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
    # symmetric-ish scoring using both directions
    t1, p1, _ = relation(a, b)
    t2, p2, _ = relation(b, a)
    return p1 + p2

def best_bridge_ingredient(fam_a: str, fam_b: str, bridge_family: str, excluded_names: set[str]):
    """
    Find ingredient containing bridge_family that best connects fam_a and fam_b.
    Score: (fam_a ↔ ing_fams) + (fam_b ↔ ing_fams), bonus if ingredient has bridge role.
    """
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

        # small bonuses / penalties
        if "bridge" in ing["roles"]:
            s += 2
        if "accent" in ing["roles"] and ing["intensity"] >= 4:
            s -= 3  # avoid heavy accents as bridges

        if s > best_score:
            best_score = s
            best = (ing["name"], ing["families"], ing["roles"], ing["intensity"], best_score)

    return best

def analyze_variant(title, extras):
    print("\n" + "="*60)
    print(title)
    print("="*60)

    total_score = 0
    breakdown = []
    bridges = []
    conflicts = []

    for e in extras:
        efams = flavor_data.INGREDIENT_BY_NAME[e]["families"]

        # Spirit vs Extra
        for sf in spirit_fams:
            for ef in efams:
                rtype, pts, bridge = relation(sf, ef)
                total_score += pts
                if pts != 0:
                    breakdown.append((pts, f"spirit:{sf} → {e}:{ef}", rtype, bridge))
                if rtype == "bridgeable":
                    bridges.append((sf, ef, bridge))
                if rtype == "conflict":
                    conflicts.append((sf, ef))

        # Key vs Extra
        for kf in key_fams:
            for ef in efams:
                rtype, pts, bridge = relation(kf, ef)
                total_score += pts
                if pts != 0:
                    breakdown.append((pts, f"key:{kf} → {e}:{ef}", rtype, bridge))
                if rtype == "bridgeable":
                    bridges.append((kf, ef, bridge))
                if rtype == "conflict":
                    conflicts.append((kf, ef))

    print("\nCORE:")
    print("-", spirit_name, spirit_fams)
    print("-", key_name, key_fams)

    print("\nEXTRAS:")
    for e in extras:
        ing = flavor_data.INGREDIENT_BY_NAME[e]
        print("-", e, ing["families"], "roles=", ing["roles"])

    print("\nWHY IT WORKS:")
    print("✅ Bez tvrdých konfliktů." if not conflicts else "⚠️ Konflikt detekován.")
    direct_count = len([x for x in breakdown if x[2] == "direct"])
    bridge_count = len(bridges)
    print(f"- Direct synergie: {direct_count}")
    print(f"- Bridge vazby: {bridge_count}")

    breakdown.sort(reverse=True, key=lambda x: x[0])
    print("\nTOP SYNERGIE:")
    for pts, desc, rtype, bridgefam in breakdown[:10]:
        if bridgefam:
            print(f"{pts:+}  {desc}  [{rtype}]  bridge→{bridgefam}")
        else:
            print(f"{pts:+}  {desc}  [{rtype}]")

    print("\nTOTAL HARMONY SCORE:", total_score)

    # NEW: suggest specific bridge ingredients + COVERED logic
    if bridges:
        print("\n🌉 DOPORUČENÉ BRIDGE INGREDIENCE (konkrétně):")

        excluded = set(extras) | {key_name}
        seen = set()

        # families already present in current extras (covered bridges)
        present_families = set()
        for n in extras:
            present_families.update(flavor_data.INGREDIENT_BY_NAME[n]["families"])

        for fam_a, fam_b, bridge_family in bridges:
            key_sig = (fam_a, fam_b, bridge_family)
            if key_sig in seen:
                continue
            seen.add(key_sig)

            # If bridge family is already in the recipe, we don't need to add another bridge ingredient
            if bridge_family in present_families:
                print(f"- pro {fam_a} ↔ {fam_b} (bridge {bridge_family}) → už COVERED existující ingrediencí")
                continue

            suggestion = best_bridge_ingredient(fam_a, fam_b, bridge_family, excluded)
            if suggestion:
                n, fams, roles, intensity, s = suggestion
                print(
                    f"- pro {fam_a} ↔ {fam_b} (bridge {bridge_family}) → {n}  "
                    f"fams={fams} roles={roles} intensity={intensity} (bridgeScore={s})"
                )
            else:
                print(f"- pro {fam_a} ↔ {fam_b} (bridge {bridge_family}) → (nenalezeno v DB)")

for title, extras in variants:
    analyze_variant(title, extras)
