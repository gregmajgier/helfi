"""Builds app/recipes/data/curated_recipes.json from the staple foods table.

Ingredient nutrition is computed from common_foods_seed.json, so recipe totals
always add up. Salt, pepper and dried spices are deliberately not tracked.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "app"
FOODS = {f["id"]: f for f in json.loads((ROOT / "db/data/common_foods_seed.json").read_text())}
OUT = ROOT / "recipes/data/curated_recipes.json"
FIELDS = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "saturated_fat_g", "sodium_mg")

# (slug, name, meal_types, servings, prep_minutes, [(food slug, amount)], [steps])
RECIPES = [
    ("overnight-oats", "Overnight oats with banana", ["breakfast"], 1, 5,
     [("oats", 50), ("milk", 150), ("banana", 118), ("chia-seeds", 10), ("honey", 10)],
     ["Stir the oats, milk and chia seeds together in a jar.", "Refrigerate overnight.", "Top with sliced banana and honey."]),
    ("yogurt-berry-bowl", "Greek yogurt berry bowl", ["breakfast", "snack"], 1, 3,
     [("greek-yogurt", 170), ("blueberries", 80), ("granola", 30), ("honey", 10)],
     ["Spoon the yogurt into a bowl.", "Add the blueberries and granola.", "Drizzle with honey."]),
    ("veggie-omelette", "Spinach and tomato omelette", ["breakfast"], 1, 10,
     [("egg", 150), ("spinach", 40), ("tomato", 60), ("mozzarella", 20), ("olive-oil", 5)],
     ["Whisk the eggs.", "Soften the spinach and tomato in the oil.", "Pour in the eggs, add the cheese and fold when set."]),
    ("pb-banana-toast", "Peanut butter banana toast", ["breakfast", "snack"], 1, 5,
     [("whole-wheat-bread", 56), ("peanut-butter", 32), ("banana", 118)],
     ["Toast the bread.", "Spread with peanut butter.", "Top with sliced banana."]),
    ("cottage-berries", "Cottage cheese with berries and walnuts", ["breakfast", "snack"], 1, 3,
     [("cottage-cheese", 150), ("strawberries", 100), ("walnuts", 15)],
     ["Put the cottage cheese in a bowl.", "Top with sliced strawberries and chopped walnuts."]),
    ("avocado-egg-toast", "Avocado and egg toast", ["breakfast"], 1, 10,
     [("whole-wheat-bread", 56), ("avocado", 75), ("egg", 100), ("tomato", 40)],
     ["Toast the bread and mash the avocado on top.", "Cook the eggs to your liking.", "Add the eggs and sliced tomato."]),
    ("skyr-smoothie-bowl", "Skyr and raspberry smoothie bowl", ["breakfast"], 1, 5,
     [("skyr", 150), ("banana", 118), ("raspberries", 80), ("oats", 30), ("almond-milk", 100)],
     ["Blend the skyr, banana, half the raspberries and the almond milk.", "Pour into a bowl.", "Top with the oats and remaining raspberries."]),
    ("chicken-rice-bowl", "Chicken and rice bowl", ["lunch", "dinner"], 1, 25,
     [("chicken-breast", 150), ("white-rice", 150), ("broccoli", 100), ("olive-oil", 10)],
     ["Cook the rice and steam the broccoli.", "Slice the cooked chicken.", "Serve together with a drizzle of oil."]),
    ("tuna-chickpea-salad", "Tuna and chickpea salad", ["lunch"], 1, 10,
     [("tuna-canned", 100), ("chickpeas", 120), ("cucumber", 80), ("tomato", 100), ("onion", 20), ("olive-oil", 10), ("lettuce", 40)],
     ["Chop the vegetables and shred the lettuce.", "Combine with the tuna and chickpeas.", "Dress with the olive oil."]),
    ("quinoa-veggie-bowl", "Quinoa vegetable bowl", ["lunch"], 1, 20,
     [("quinoa", 150), ("chickpeas", 100), ("bell-pepper", 80), ("cucumber", 60), ("feta", 30), ("olive-oil", 10)],
     ["Cook the quinoa and let it cool slightly.", "Dice the vegetables.", "Toss everything together and crumble the feta on top."]),
    ("turkey-hummus-wraps", "Turkey and hummus wraps", ["lunch"], 1, 8,
     [("tortilla", 90), ("turkey-breast", 100), ("hummus", 40), ("lettuce", 40), ("tomato", 60)],
     ["Spread the hummus over the tortillas.", "Layer the turkey, lettuce and tomato.", "Roll up and slice in half."]),
    ("lentil-soup", "Tomato lentil soup", ["lunch", "dinner"], 2, 30,
     [("lentils", 400), ("carrot", 160), ("onion", 100), ("tomato-passata", 300), ("olive-oil", 20)],
     ["Soften the onion and carrot in the oil.", "Add the passata, lentils and a cup of water.", "Simmer for 15 minutes and blend if you like it smooth."]),
    ("tofu-stir-fry", "Tofu stir-fry with brown rice", ["lunch", "dinner"], 1, 25,
     [("tofu", 150), ("brown-rice", 150), ("broccoli", 100), ("bell-pepper", 80), ("soy-sauce", 15), ("olive-oil", 10)],
     ["Brown the cubed tofu in the oil.", "Add the vegetables and cook until tender.", "Stir in the soy sauce and serve over the rice."]),
    ("greek-salad", "Greek salad", ["lunch", "snack"], 1, 8,
     [("tomato", 150), ("cucumber", 100), ("feta", 40), ("olive-oil", 10), ("onion", 20)],
     ["Chop the tomato and cucumber into chunks.", "Slice the onion thinly.", "Top with feta and olive oil."]),
    ("black-bean-bowl", "Black bean burrito bowl", ["lunch", "dinner"], 1, 15,
     [("black-beans", 120), ("white-rice", 120), ("sweet-corn", 60), ("avocado", 50), ("tomato", 80)],
     ["Warm the beans and corn.", "Spoon over the rice.", "Top with diced tomato and avocado."]),
    ("salmon-sweet-potato", "Baked salmon with sweet potato", ["dinner"], 1, 30,
     [("salmon", 150), ("sweet-potato", 200), ("asparagus", 100), ("olive-oil", 10)],
     ["Roast the sweet potato wedges at 200C for 15 minutes.", "Add the salmon and asparagus with the oil.", "Roast for 12 more minutes."]),
    ("chicken-noodle-stir-fry", "Chicken noodle stir-fry", ["dinner"], 1, 20,
     [("chicken-breast", 150), ("rice-noodles", 150), ("bell-pepper", 80), ("green-beans", 80), ("soy-sauce", 15), ("olive-oil", 10)],
     ["Stir-fry the chicken in the oil.", "Add the vegetables, then the noodles.", "Season with soy sauce."]),
    ("steak-potato-skillet", "Steak and potato skillet", ["dinner"], 1, 30,
     [("beef-steak", 150), ("potato", 200), ("green-beans", 100), ("olive-oil", 10)],
     ["Roast the potato chunks until golden.", "Sear the steak and rest it.", "Serve with steamed green beans."]),
    ("pasta-bolognese", "Pasta with beef and tomato", ["dinner"], 1, 30,
     [("pasta", 200), ("ground-beef", 100), ("tomato-passata", 150), ("onion", 40), ("parmesan", 10)],
     ["Brown the beef with the onion.", "Add the passata and simmer for 15 minutes.", "Toss with the pasta and finish with parmesan."]),
    ("shrimp-couscous", "Shrimp and zucchini with couscous", ["dinner"], 1, 15,
     [("shrimp", 150), ("zucchini", 150), ("couscous", 150), ("olive-oil", 10)],
     ["Saute the zucchini in the oil.", "Add the shrimp until pink.", "Serve over the couscous."]),
    ("cod-roast-veg", "Cod with roasted vegetables", ["dinner"], 1, 35,
     [("cod", 180), ("potato", 200), ("carrot", 100), ("zucchini", 100), ("olive-oil", 10)],
     ["Roast the potato and carrot for 20 minutes.", "Add the zucchini and cod.", "Roast 10 more minutes until the fish flakes."]),
    ("chickpea-spinach-stew", "Chickpea and spinach stew", ["lunch", "dinner"], 2, 25,
     [("chickpeas", 250), ("spinach", 100), ("tomato-passata", 200), ("onion", 60), ("olive-oil", 10)],
     ["Soften the onion in the oil.", "Add the chickpeas and passata and simmer 10 minutes.", "Stir in the spinach until wilted."]),
    ("chicken-bulgur", "Chicken thigh with bulgur and cabbage", ["dinner"], 1, 30,
     [("chicken-thigh", 150), ("bulgur", 150), ("cabbage", 100), ("olive-oil", 5)],
     ["Cook the bulgur.", "Saute the cabbage in the oil.", "Serve with the sliced cooked chicken."]),
    ("apple-pb", "Apple with peanut butter", ["snack"], 1, 2,
     [("apple", 182), ("peanut-butter", 32)],
     ["Slice the apple.", "Serve with the peanut butter for dipping."]),
    ("hummus-carrots", "Hummus with carrot sticks", ["snack"], 1, 3,
     [("hummus", 60), ("carrot", 120)],
     ["Cut the carrots into sticks.", "Serve with the hummus."]),
    ("cottage-pear", "Cottage cheese with pear", ["snack"], 1, 2,
     [("cottage-cheese", 100), ("pear", 178)],
     ["Slice the pear.", "Serve with the cottage cheese."]),
    ("trail-mix", "Nut and chocolate trail mix", ["snack"], 1, 2,
     [("almonds", 15), ("cashews", 15), ("raisins", 20), ("dark-chocolate", 10)],
     ["Mix everything in a small container."]),
    ("rice-cake-almond", "Rice cakes with almond butter and banana", ["snack"], 1, 3,
     [("rice-cake", 18), ("almond-butter", 16), ("banana", 60)],
     ["Spread the almond butter on the rice cakes.", "Top with sliced banana."]),
    ("skyr-berries", "Skyr with strawberries", ["snack", "breakfast"], 1, 2,
     [("skyr", 150), ("strawberries", 80), ("honey", 5)],
     ["Spoon the skyr into a bowl.", "Top with sliced strawberries and honey."]),
    ("eggs-cucumber", "Boiled eggs with cucumber", ["snack"], 1, 12,
     [("egg", 100), ("cucumber", 100)],
     ["Boil the eggs for 9 minutes and cool them.", "Serve with sliced cucumber."]),
    ("banana-protein-shake", "Banana protein shake", ["snack", "breakfast"], 1, 3,
     [("whey-protein", 30), ("almond-milk", 250), ("banana", 60)],
     ["Blend everything until smooth."]),
]


def ingredient(slug: str, amount: float) -> dict:
    food = FOODS[f"common-{slug}"]
    factor = amount / food["serving_size"]
    nutrients = {}
    for field in FIELDS:
        source = "calories_per_serving" if field == "calories" else field
        nutrients[field] = round(float(food.get(source, 0) or 0) * factor, 1)
    return {"name": food["name"], "amount": amount, "unit": food["serving_unit"], "food_id": food["id"], **nutrients}


def main() -> None:
    out = []
    for slug, name, meal_types, servings, prep, items, steps in RECIPES:
        out.append(
            {
                "id": f"curated-{slug}",
                "name": name,
                "meal_types": meal_types,
                "servings": servings,
                "prep_minutes": prep,
                "ingredients": [ingredient(s, a) for s, a in items],
                "instructions": steps,
            }
        )
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(len(out), "recipes")


if __name__ == "__main__":
    main()
