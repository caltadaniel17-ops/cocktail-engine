import flavor_data

REQUIRED_KEYS = ["name", "families", "intensity", "roles", "taste", "temperature"]
TASTE_KEYS = ["sweet", "acid", "bitter", "umami", "spice", "fat"]
ALLOWED_TEMPS = {"fresh", "neutral", "warm"}

errors = []

names = []
for idx, ing in enumerate(flavor_data.INGREDIENTS):
    # keys present
    for k in REQUIRED_KEYS:
        if k not in ing:
            errors.append(f"[{idx}] missing key '{k}' in {ing.get('name')}")
    # types
    if "name" in ing and not isinstance(ing["name"], str):
        errors.append(f"[{idx}] name not str: {ing}")
    if "families" in ing and not isinstance(ing["families"], list):
        errors.append(f"[{idx}] families not list: {ing.get('name')}")
    if "roles" in ing and not isinstance(ing["roles"], list):
        errors.append(f"[{idx}] roles not list: {ing.get('name')}")
    if "intensity" in ing and not isinstance(ing["intensity"], int):
        errors.append(f"[{idx}] intensity not int: {ing.get('name')}")
    if "taste" in ing and not isinstance(ing["taste"], dict):
        errors.append(f"[{idx}] taste not dict: {ing.get('name')}")
    if "temperature" in ing and ing.get("temperature") not in ALLOWED_TEMPS:
        errors.append(f"[{idx}] bad temperature '{ing.get('temperature')}' in {ing.get('name')}")

    # taste keys
    if "taste" in ing and isinstance(ing["taste"], dict):
        for tk in TASTE_KEYS:
            if tk not in ing["taste"]:
                errors.append(f"[{idx}] taste missing '{tk}' in {ing.get('name')}")
            else:
                v = ing["taste"][tk]
                if not isinstance(v, int):
                    errors.append(f"[{idx}] taste['{tk}'] not int in {ing.get('name')}: {v}")

    # duplicates
    if "name" in ing:
        names.append(ing["name"])

dups = sorted({n for n in names if names.count(n) > 1})
if dups:
    errors.append(f"Duplicate ingredient names: {dups}")

print(f"INGREDIENTS count: {len(flavor_data.INGREDIENTS)}")
print(f"ALCOHOL_SUBCATEGORIES count: {len(flavor_data.ALCOHOL_SUBCATEGORIES)}")

if errors:
    print("\n❌ DB integrity FAIL:")
    for e in errors:
        print("-", e)
else:
    print("\n✅ DB integrity OK (all ingredients have required fields)")

