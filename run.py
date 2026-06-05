# run.py
# Simple runner for the MVP engine

import engine


def print_result(r):
    print("\n" + "=" * 60)
    print(r.title)
    print("=" * 60)
    print(f"CORE: spirit={r.spirit} | key1={r.key1}" + (f" | key2={r.key2}" if r.key2 else ""))

    print("\nRECIPE (pre-dilution, ml):")
    print(f"- {r.spirit}: {r.amounts_ml['spirit']} ml")
    print(f"- {r.key1}: {r.amounts_ml['key1']} ml")
    if r.key2:
        print(f"- {r.key2}: {r.amounts_ml.get('key2', 0)} ml")

    for n in r.extras:
        print(f"- {n}: {r.amounts_ml[n]} ml")

    print("\nWHY IT WORKS:")
    for note in r.notes:
        print("-", note)

    print(f"- Direct synergie: {r.direct_count}")
    print(f"- Bridge vazby: {r.bridge_count}")
    print(f"- Harmony score: {r.harmony_score}")

    if r.bridge_inserts:
        print("\nBRIDGE INSERTS:")
        for fam_a, fam_b, br, name, micro, reduced in r.bridge_inserts:
            tag = "micro 2.5ml" if micro else "5ml"
            if reduced:
                print(f"- {fam_a} ↔ {fam_b} (bridge {br}) → {name} [{tag}] (ubráno 2.5 ml z {reduced})")
            else:
                print(f"- {fam_a} ↔ {fam_b} (bridge {br}) → {name} [{tag}]")


def main():
    # Nastav si vstupy tady
    spirit = "dry_vermouth"
    key1 = "berries tea"
    key2 = None

    results = engine.generate(
        spirit=spirit,
        key1=key1,
        key2=key2,
        target_ml=90,
        seed=None,
    )

    print("POCET VYSLEDKU:", len(results))

    for r in results:
        print_result(r)


if __name__ == "__main__":
    main()
