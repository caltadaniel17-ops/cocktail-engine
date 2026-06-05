import flavor_data

used = set()

# families used by ingredients
for ing in flavor_data.INGREDIENTS:
    for f in ing["families"]:
        used.add(f)

# families used by spirits
for fams in flavor_data.ALCOHOL_SUBCATEGORIES.values():
    for f in fams:
        used.add(f)

compat_keys = set(flavor_data.COMPATIBILITY.keys())

missing = sorted(list(used - compat_keys))
extra = sorted(list(compat_keys - used))

print("Used families (ingredients + spirits):", len(used))
print("COMPATIBILITY families:", len(compat_keys))

if missing:
    print("\n❌ Families used but missing in COMPATIBILITY:")
    for f in missing:
        print("-", f)
else:
    print("\n✅ All used families exist in COMPATIBILITY")

# Extra keys are not an error, but informative:
if extra:
    print("\nℹ️ Families in COMPATIBILITY but not currently used:")
    for f in extra:
        print("-", f)

