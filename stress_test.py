import random
import engine
import flavor_data

random.seed(0)

spirits = list(flavor_data.ALCOHOL_SUBCATEGORIES.keys())
ingredient_names = [i["name"] for i in flavor_data.INGREDIENTS]

tests = [
    ("london_dry_gin", "green_apple", "mint"),
    ("aged_rum", "pineapple", None),
    ("tequila_blanco", "grapefruit", None),
    ("bourbon", "honey", None),
    ("mezcal", "tomato", None),
]

# plus 10 random tests
for _ in range(10):
    sp = random.choice(spirits)
    k1 = random.choice(ingredient_names)
    k2 = random.choice([None, random.choice(ingredient_names)])
    if k2 == k1:
        k2 = None
    tests.append((sp, k1, k2))

ok = 0
for sp, k1, k2 in tests:
    try:
        results = engine.generate(spirit=sp, key1=k1, key2=k2, target_ml=90)
        # basic sanity checks
        assert len(results) > 0
        for r in results:
            total = sum(r.amounts_ml.values())
            build_rule = engine.get_category_build_rule(r.title)
            expected_ml = float(build_rule.get("target_ml", 90))
            assert abs(total - expected_ml) < 0.001, f"{r.title}: total={total} expected={expected_ml}"
        ok += 1
    except Exception as e:
        print("\n❌ FAIL:", sp, k1, k2)
        print("   ", type(e).__name__, e)

print(f"\n✅ Stress tests passed: {ok}/{len(tests)}")

