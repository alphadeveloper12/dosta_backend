import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import MenuItem, BudgetOption, Course, Cuisine

def verify_menu_budget():
    print("--- Setting up Menu Item Budget Test ---")
    
    # helper to get dummy course/cuisine
    c = Course.objects.first()
    cu = Cuisine.objects.first()

    # Create Budgets
    # Budget 100 (Min 100, Max 100)
    b_100, _ = BudgetOption.objects.get_or_create(label="Budget 100", defaults={'price_range': '100', 'min_price': 100, 'max_price': 100})
    b_100.min_price = 100
    b_100.max_price = 100
    b_100.save()

    # Budget 120 (Min 120, Max 120)
    b_120, _ = BudgetOption.objects.get_or_create(label="Budget 120", defaults={'price_range': '120', 'min_price': 120, 'max_price': 120})
    b_120.min_price = 120
    b_120.max_price = 120
    b_120.save()

    # Create Menu Items
    # Item A: Linked to Budget 120
    item_120, _ = MenuItem.objects.get_or_create(name="Item 120", defaults={'course': c, 'cuisine': cu})
    item_120.budget_options.clear()
    item_120.budget_options.add(b_120)

    # Item B: Linked to Budget 100
    item_100, _ = MenuItem.objects.get_or_create(name="Item 100", defaults={'course': c, 'cuisine': cu})
    item_100.budget_options.clear()
    item_100.budget_options.add(b_100)

    print("\n--- Test: Filter by Budget 100 (Min 100) ---")
    # Should include Item 120 (120 >= 100) AND Item 100 (100 >= 100)
    
    selected = b_100
    qs = MenuItem.objects.filter(budget_options__max_price__gte=selected.min_price).distinct()
    ids = [i.name for i in qs]
    print(f"Results for 100 filter: {ids}")

    if "Item 120" in ids and "Item 100" in ids:
        print("SUCCESS: Filter 100 shows both items.")
    else:
        print("FAILURE: Filter 100 missing items.")

    print("\n--- Test: Filter by Budget 120 (Min 120) ---")
    # Should include Item 120 (120 >= 120).
    # Should EXCLUDE Item 100 (100 < 120).
    
    selected = b_120
    qs = MenuItem.objects.filter(budget_options__max_price__gte=selected.min_price).distinct()
    ids = [i.name for i in qs]
    print(f"Results for 120 filter: {ids}")

    if "Item 120" in ids and "Item 100" not in ids:
        print("SUCCESS: Filter 120 shows only Item 120.")
    else:
        print("FAILURE: Filter 120 logic incorrect.")

if __name__ == "__main__":
    verify_menu_budget()
