import copy
import flavor_data

spirit_name = "aged_rum"
key_name = "pineapple"

variants = [
    ("Variant 1 (bright + floral)", ["yuzu", "elderflower", "ginger"]),
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
            best = (ing["name"], best_score, ing["families"], ing["roles"], ing["intensity"])
    return best

def find_bridge_needs(extras):
    # families present in current recipe extras
    present_families = set()
    for n in extras:
        present_families.update(flavor_data.INGREDIENT_BY_NAME[n]["families"])

    found_bridgeables = []  # for debug

    bridges = []
    for e in extras:
        efams = flavor_data.INGREDIENT_BY_NAME[e]["families"]

        # spirit vs extra families
        for sf in spirit_fams:
            for ef in efams:
                rtype, _, bridge_family = relation(sf, ef)
                if rtype == "bridgeable":
                    found_bridgeables.append(("spirit", sf, e, ef, bridge_family))
                    bridges.append((sf, ef, bridge_family))

        # key vs extra families
        for kf in key_fams:
            for ef in efams:
                rtype, _, bridge_family = relation(kf, ef)
                if rtype == "bridgeable":
                    found_bridgeables.append(("key", kf, e, ef, bridge_family))
                    bridges.append((kf, ef, bridge_family))

    # Unique + only not covered
    unique_needs = []
    seen = set()
    for a, b, br in bridges:
        sig = (a, b, br)
        if sig in seen:
            continue
        seen.add(sig)
        if br in present_families:
            continue  # covered already by existing extras
        unique_needs.append((a, b, br))

    return found_bridgeables, unique_needs, present_families

def first_sweet_in_recipe(extras):
    for n in extras:
        if "sweet" in flavor_data.INGREDIENT_BY_NAME[n]["roles"]:
            return n
    return None

def auto_insert_bridge(extras):
    extras2 = copy.deepcopy(extras)
    inserted = []

    found, needs, present_families = find_bridge_needs(extras2)

    # DEBUG PRINTS
    print("DEBUG present_families:", sorted(present_families))
    print("DEBUG found bridgeables:")
    for src, a, e, b, br in found:
        print(f"  - {src}: {a} → {e}:{b}  bridge={br}")
    print("DEBUG needs (not covered):", needs)

    if not needs:
        return extras2, inserted

    excluded = set(extras2) | {key_name}
    existing_sweet = first_sweet_in_recipe(extras2)

    for fam_a, fam_b, bridge_family in needs:
        cand = best_bridge_ingredient(fam_a, fam_b, bridge_family, excluded)
        if not cand:
            continue

        name, score, fams, roles, intensity = cand

        if name in extras2:
            continue

        micro = "sweet" in set(roles)  # sweet bridges become micro by default

        extras2.append(name)
        excluded.add(name)
        inserted.append((fam_a, fam_b, bridge_family, name, micro, existing_sweet, score))

    return extras2, inserted

for title, extras in variants:
    print("\n" + "="*60)
    print(title)
    print("ORIGINAL EXTRAS:", extras)

    new_extras, inserted = auto_insert_bridge(extras)

    print("UPDATED  EXTRAS:", new_extras)
    if inserted:
        print("INSERTED BRIDGES:")
        for a, b, br, name, micro, existing_sweet, score in inserted:
            tag = "micro(2.5ml)" if micro else "5ml"
            print(f"- {a} ↔ {b} (bridge {br}) → {name} [{tag}] score={score}")
            if micro and existing_sweet:
                print(f"  BALANCE NOTE: přidej {name} jako 2.5 ml a uber 2.5 ml z {existing_sweet}.")
    else:
        print("INSERTED BRIDGES: none")
