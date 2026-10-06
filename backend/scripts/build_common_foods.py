"""Regenerates app/db/data/common_foods_seed.json.

Values are typical USDA-style figures per 100 g/ml, rounded, scaled to each
food's natural serving. They are approximate staples data, good enough for
logging, and should be spot-checked before a public release. Existing record
ids and macro values are preserved; only the extended nutrients are added.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "db" / "data" / "common_foods_seed.json"

# slug: (name, serving_size, unit, kcal, protein, carbs, fat, fiber, sugar, sat_fat, sodium_mg) all per 100 g/ml
NEW = {
    "turkey-breast": ("Turkey breast, roasted", 100, "g", 135, 30, 0, 1, 0, 0, 0.3, 55),
    "pork-loin": ("Pork loin, cooked", 100, "g", 195, 27, 0, 9, 0, 0, 3.2, 60),
    "beef-steak": ("Beef sirloin steak, cooked", 100, "g", 206, 30, 0, 9, 0, 0, 3.5, 60),
    "bacon": ("Bacon, cooked", 100, "g", 541, 37, 1.4, 42, 0, 0, 14, 1717),
    "ham": ("Ham, sliced", 100, "g", 145, 21, 1.5, 5.5, 0, 1, 1.8, 1203),
    "tuna-canned": ("Tuna, canned in water", 100, "g", 116, 26, 0, 1, 0, 0, 0.2, 247),
    "cod": ("Cod, cooked", 100, "g", 105, 23, 0, 0.9, 0, 0, 0.2, 78),
    "shrimp": ("Shrimp, cooked", 100, "g", 99, 24, 0.2, 0.3, 0, 0, 0.1, 111),
    "egg-white": ("Egg white", 33, "g", 52, 11, 0.7, 0.2, 0, 0.7, 0, 166),
    "cottage-cheese": ("Cottage cheese, low-fat", 100, "g", 72, 12.4, 2.7, 1, 0, 2.7, 0.6, 406),
    "mozzarella": ("Mozzarella cheese", 28, "g", 280, 28, 3.1, 17, 0, 1, 10.9, 627),
    "parmesan": ("Parmesan cheese, grated", 10, "g", 431, 38, 4.1, 29, 0, 0.9, 19, 1529),
    "feta": ("Feta cheese", 28, "g", 264, 14, 4, 21, 0, 4, 15, 917),
    "butter": ("Butter", 14, "g", 717, 0.9, 0.1, 81, 0, 0.1, 51, 11),
    "olive-oil": ("Olive oil", 14, "g", 884, 0, 0, 100, 0, 0, 13.8, 2),
    "yogurt-whole": ("Yogurt, plain, whole milk", 170, "g", 61, 3.5, 4.7, 3.3, 0, 4.7, 2.1, 46),
    "skyr": ("Skyr, plain", 150, "g", 63, 11, 4, 0.2, 0, 4, 0.1, 40),
    "whey-protein": ("Whey protein powder", 30, "g", 400, 80, 8, 6, 0, 4, 3, 200),
    "almond-milk": ("Almond milk, unsweetened", 240, "ml", 13, 0.4, 0.3, 1.1, 0.2, 0, 0.1, 67),
    "oat-milk": ("Oat milk", 240, "ml", 48, 1, 7, 1.5, 0.8, 4, 0.2, 40),
    "soy-milk": ("Soy milk, unsweetened", 240, "ml", 33, 2.9, 1.7, 1.8, 0.4, 0.4, 0.2, 51),
    "hummus": ("Hummus", 30, "g", 166, 8, 14, 9.6, 6, 0.3, 1.4, 379),
    "lentils": ("Lentils, cooked", 100, "g", 116, 9, 20, 0.4, 7.9, 1.8, 0.1, 2),
    "chickpeas": ("Chickpeas, cooked", 100, "g", 164, 8.9, 27, 2.6, 7.6, 4.8, 0.3, 7),
    "kidney-beans": ("Kidney beans, cooked", 100, "g", 127, 8.7, 23, 0.5, 6.4, 0.3, 0.1, 1),
    "green-peas": ("Green peas, cooked", 100, "g", 84, 5.4, 15.6, 0.2, 5.5, 5.9, 0, 3),
    "quinoa": ("Quinoa, cooked", 100, "g", 120, 4.4, 21, 1.9, 2.8, 0.9, 0.2, 7),
    "couscous": ("Couscous, cooked", 100, "g", 112, 3.8, 23, 0.2, 1.4, 0.1, 0, 5),
    "bulgur": ("Bulgur, cooked", 100, "g", 83, 3.1, 18.6, 0.2, 4.5, 0.1, 0, 5),
    "bread-white": ("Bread, white", 28, "g", 266, 9, 49, 3.2, 2.7, 5, 0.7, 491),
    "bread-rye": ("Bread, rye", 32, "g", 259, 8.5, 48, 3.3, 5.8, 3.9, 0.5, 660),
    "tortilla": ("Tortilla, flour", 45, "g", 304, 8, 50, 8, 3, 3, 2.5, 700),
    "bagel": ("Bagel, plain", 105, "g", 250, 10, 49, 1.5, 2.3, 6, 0.3, 440),
    "cornflakes": ("Cornflakes", 30, "g", 357, 7, 84, 0.4, 3.3, 10, 0.1, 730),
    "granola": ("Granola", 50, "g", 471, 10, 64, 20, 7, 24, 3.7, 26),
    "muesli": ("Muesli", 50, "g", 340, 10, 66, 6, 8, 15, 1, 100),
    "pasta-whole-wheat": ("Pasta, whole wheat, cooked", 100, "g", 124, 5.3, 26.5, 0.5, 3.9, 0.8, 0.1, 3),
    "rice-noodles": ("Rice noodles, cooked", 100, "g", 108, 0.9, 25, 0.2, 1, 0, 0, 1),
    "rice-cake": ("Rice cake", 9, "g", 387, 8, 82, 2.8, 4, 0.9, 0.5, 29),
    "popcorn": ("Popcorn, air-popped", 100, "g", 387, 13, 78, 4.5, 14.5, 0.9, 0.6, 8),
    "carrot": ("Carrot, raw", 100, "g", 41, 0.9, 9.6, 0.2, 2.8, 4.7, 0, 69),
    "cucumber": ("Cucumber", 100, "g", 15, 0.7, 3.6, 0.1, 0.5, 1.7, 0, 2),
    "tomato": ("Tomato", 100, "g", 18, 0.9, 3.9, 0.2, 1.2, 2.6, 0, 5),
    "bell-pepper": ("Bell pepper, red", 100, "g", 31, 1, 6, 0.3, 2.1, 4.2, 0.1, 4),
    "onion": ("Onion", 100, "g", 40, 1.1, 9.3, 0.1, 1.7, 4.2, 0, 4),
    "lettuce": ("Lettuce, romaine", 100, "g", 17, 1.2, 3.3, 0.3, 2.1, 1.2, 0, 8),
    "cauliflower": ("Cauliflower, cooked", 100, "g", 23, 1.8, 4.1, 0.5, 2.3, 2, 0.1, 15),
    "zucchini": ("Zucchini", 100, "g", 17, 1.2, 3.1, 0.3, 1, 2.5, 0.1, 8),
    "mushrooms": ("Mushrooms", 100, "g", 22, 3.1, 3.3, 0.3, 1, 2, 0, 5),
    "green-beans": ("Green beans, cooked", 100, "g", 35, 1.9, 7.9, 0.3, 3.2, 1.6, 0.1, 1),
    "cabbage": ("Cabbage", 100, "g", 25, 1.3, 5.8, 0.1, 2.5, 3.2, 0, 18),
    "kale": ("Kale", 100, "g", 49, 4.3, 8.8, 0.9, 3.6, 2.3, 0.1, 38),
    "sweet-corn": ("Sweet corn, cooked", 100, "g", 96, 3.4, 21, 1.5, 2.4, 4.5, 0.2, 1),
    "beetroot": ("Beetroot, cooked", 100, "g", 44, 1.7, 10, 0.2, 2, 8, 0, 77),
    "asparagus": ("Asparagus, cooked", 100, "g", 22, 2.4, 4.1, 0.2, 2, 1.3, 0.1, 14),
    "pumpkin": ("Pumpkin, cooked", 100, "g", 20, 0.7, 4.9, 0.1, 1.1, 2, 0.1, 1),
    "eggplant": ("Eggplant, cooked", 100, "g", 35, 0.8, 8.7, 0.2, 2.5, 3.2, 0, 1),
    "tomato-passata": ("Tomato passata", 100, "g", 32, 1.5, 6.6, 0.2, 1.7, 4.8, 0, 150),
    "strawberries": ("Strawberries", 100, "g", 32, 0.7, 7.7, 0.3, 2, 4.9, 0, 1),
    "blueberries": ("Blueberries", 100, "g", 57, 0.7, 14.5, 0.3, 2.4, 10, 0, 1),
    "grapes": ("Grapes", 100, "g", 69, 0.7, 18, 0.2, 0.9, 16, 0.1, 2),
    "watermelon": ("Watermelon", 100, "g", 30, 0.6, 7.6, 0.2, 0.4, 6.2, 0, 1),
    "pineapple": ("Pineapple", 100, "g", 50, 0.5, 13, 0.1, 1.4, 9.9, 0, 1),
    "mango": ("Mango", 100, "g", 60, 0.8, 15, 0.4, 1.6, 13.7, 0.1, 1),
    "pear": ("Pear", 178, "g", 57, 0.4, 15.2, 0.1, 3.1, 9.8, 0, 1),
    "peach": ("Peach", 150, "g", 39, 0.9, 9.5, 0.3, 1.5, 8.4, 0, 0),
    "kiwi": ("Kiwi", 69, "g", 61, 1.1, 14.7, 0.5, 3, 9, 0, 3),
    "raspberries": ("Raspberries", 100, "g", 52, 1.2, 11.9, 0.7, 6.5, 4.4, 0, 1),
    "dates": ("Dates, Medjool", 24, "g", 277, 1.8, 75, 0.2, 6.7, 66, 0, 1),
    "raisins": ("Raisins", 30, "g", 299, 3.1, 79, 0.5, 3.7, 59, 0.1, 11),
    "dried-apricots": ("Dried apricots", 30, "g", 241, 3.4, 63, 0.5, 7.3, 53, 0, 10),
    "walnuts": ("Walnuts", 28, "g", 654, 15, 14, 65, 6.7, 2.6, 6.1, 2),
    "cashews": ("Cashews", 28, "g", 553, 18, 30, 44, 3.3, 6, 7.8, 12),
    "peanuts": ("Peanuts", 28, "g", 567, 26, 16, 49, 8.5, 4, 6.8, 18),
    "chia-seeds": ("Chia seeds", 12, "g", 486, 17, 42, 31, 34, 0, 3.3, 16),
    "flaxseed": ("Flaxseed, ground", 10, "g", 534, 18, 29, 42, 27, 1.6, 3.7, 30),
    "sunflower-seeds": ("Sunflower seeds", 28, "g", 584, 21, 20, 51, 8.6, 2.6, 4.5, 9),
    "almond-butter": ("Almond butter", 32, "g", 614, 21, 19, 56, 10, 4.4, 4.2, 7),
    "dark-chocolate": ("Dark chocolate", 20, "g", 598, 7.8, 46, 43, 11, 24, 24, 20),
    "milk-chocolate": ("Milk chocolate", 25, "g", 535, 7.7, 59, 30, 3.4, 52, 18, 79),
    "honey": ("Honey", 21, "g", 304, 0.3, 82, 0, 0.2, 82, 0, 4),
    "sugar": ("Sugar", 4, "g", 387, 0, 100, 0, 0, 100, 0, 1),
    "jam": ("Jam", 20, "g", 250, 0.4, 65, 0.1, 1, 48, 0, 32),
    "ketchup": ("Ketchup", 17, "g", 101, 1, 27, 0.1, 0.3, 22, 0, 907),
    "mayonnaise": ("Mayonnaise", 14, "g", 680, 1, 0.6, 75, 0, 0.6, 11, 635),
    "soy-sauce": ("Soy sauce", 15, "ml", 53, 8, 4.9, 0.6, 0.8, 0.4, 0.1, 5493),
    "cola": ("Cola", 330, "ml", 42, 0, 10.6, 0, 0, 10.6, 0, 4),
    "orange-juice": ("Orange juice", 240, "ml", 45, 0.7, 10.4, 0.2, 0.2, 8.4, 0, 1),
    "coffee": ("Coffee, black", 240, "ml", 1, 0.1, 0, 0, 0, 0, 0, 2),
    "beer": ("Beer, regular", 330, "ml", 43, 0.5, 3.6, 0, 0, 0, 0, 4),
    "red-wine": ("Red wine", 150, "ml", 85, 0.1, 2.6, 0, 0, 0.6, 0, 4),
    "pizza-slice": ("Pizza slice, margherita", 107, "g", 266, 11, 33, 10, 2.3, 3.6, 4.5, 598),
    "french-fries": ("French fries", 100, "g", 312, 3.4, 41, 15, 3.8, 0.3, 2.3, 210),
    "potato-chips": ("Potato chips", 28, "g", 536, 7, 53, 35, 4.8, 0.3, 3.4, 525),
    "ice-cream": ("Ice cream, vanilla", 66, "g", 207, 3.5, 24, 11, 0.7, 21, 6.8, 80),
}

# Extended nutrients (fiber, sugar, sat fat, sodium mg) per 100 g for the original 25 records.
EXTENDED_FOR_EXISTING = {
    "common-chicken-breast": (0, 0, 1.0, 74),
    "common-chicken-thigh": (0, 0, 3.0, 95),
    "common-ground-beef": (0, 0, 4.9, 72),
    "common-salmon": (0, 0, 3.1, 61),
    "common-egg": (0, 0.4, 3.1, 124),
    "common-white-rice": (0.4, 0, 0.1, 1),
    "common-brown-rice": (1.6, 0.2, 0.2, 4),
    "common-oats": (10.6, 1, 1.2, 2),
    "common-whole-wheat-bread": (6, 5.7, 0.8, 450),
    "common-pasta": (1.8, 0.6, 0.2, 1),
    "common-potato": (2.2, 1.2, 0, 10),
    "common-sweet-potato": (3.3, 6.5, 0.1, 36),
    "common-banana": (2.6, 12.2, 0.1, 1),
    "common-apple": (2.4, 10.4, 0, 1),
    "common-orange": (2.4, 12.2, 0, 0),
    "common-avocado": (6.7, 0.7, 2.1, 7),
    "common-broccoli": (3.3, 1.4, 0, 41),
    "common-spinach": (2.2, 0.4, 0.1, 79),
    "common-almonds": (12.5, 4.4, 1.1, 1),
    "common-peanut-butter": (6, 9, 3.3, 430),
    "common-greek-yogurt": (0, 3.6, 0.4, 36),
    "common-milk": (0, 4.8, 1.9, 43),
    "common-cheddar-cheese": (0, 0.5, 6, 621),
    "common-black-beans": (8.7, 0.3, 0.1, 1),
    "common-tofu": (2.3, 0.6, 1.3, 14),
}


def _scaled(value: float, size: float) -> float:
    return round(value * size / 100, 1)


def main() -> None:
    existing = json.loads(OUT.read_text())
    records = []
    for rec in existing:
        if rec["id"] not in EXTENDED_FOR_EXISTING:
            records.append(rec)
            continue
        fiber, sugar, sat, sodium = EXTENDED_FOR_EXISTING[rec["id"]]
        size = rec["serving_size"]
        records.append(
            {
                **rec,
                "fiber_g": _scaled(fiber, size),
                "sugar_g": _scaled(sugar, size),
                "saturated_fat_g": _scaled(sat, size),
                "sodium_mg": round(sodium * size / 100),
            }
        )
    known = {r["id"] for r in records}
    for slug, (name, size, unit, kcal, p, c, f, fiber, sugar, sat, sodium) in NEW.items():
        rid = f"common-{slug}"
        if rid in known:
            continue
        records.append(
            {
                "id": rid,
                "name": name,
                "serving_size": size,
                "serving_unit": unit,
                "calories_per_serving": round(kcal * size / 100),
                "protein_g": _scaled(p, size),
                "carbs_g": _scaled(c, size),
                "fat_g": _scaled(f, size),
                "fiber_g": _scaled(fiber, size),
                "sugar_g": _scaled(sugar, size),
                "saturated_fat_g": _scaled(sat, size),
                "sodium_mg": round(sodium * size / 100),
            }
        )
    OUT.write_text(json.dumps(records, indent=1) + "\n")
    print(len(records), "records")


if __name__ == "__main__":
    main()
