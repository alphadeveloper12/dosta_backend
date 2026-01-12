import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Cuisine, BudgetOption, ServiceStyle

def verify_cumulative_budget():
    # Setup Data
    print("Setting up data...")
    
    # Test 1: Filter by 120 (Min 120)
    print("\n--- Test 1: Filter by 120 (Min 120) ---")

    # Set up data again
    cuisine_african, _ = Cuisine.objects.get_or_create(name="African Cuisine")
    # DIRECTLY SET PRICES ON CUISINE
    cuisine_african.min_price = 70
    cuisine_african.max_price = 135
    cuisine_african.save()

    cuisine_american, _ = Cuisine.objects.get_or_create(name="American Cuisine")
    cuisine_american.min_price = 125
    cuisine_american.max_price = 125
    cuisine_american.save()
    
    # Filter 120
    budget_filter_120, _ = BudgetOption.objects.get_or_create(label="Filter 120", defaults={'price_range': '120', 'min_price': 120, 'max_price': 120})
    budget_filter_120.min_price = 120
    budget_filter_120.save()

    selected_budget = budget_filter_120
    # USE THE NEW FILTER LOGIC: Cuisine.max_price >= filter.min_price
    qs = Cuisine.objects.filter(max_price__gte=selected_budget.min_price).distinct()
    
    results = [c.name for c in qs]
    print(f"Result (Filter 120): {results}")
    
    if "American Cuisine" in results and "African Cuisine" in results:
        print("SUCCESS: 120 filter includes both (African fits because max 135 >= 120).")
    else:
        print("FAILURE: Should include both.")

    # Test 2: Filter by 140
    print("\n--- Test 2: Filter by 140 (Min 140) ---")
    budget_filter_140, _ = BudgetOption.objects.get_or_create(label="Filter 140", defaults={'price_range': '140', 'min_price': 140, 'max_price': 140})
    budget_filter_140.min_price = 140
    budget_filter_140.save()

    selected_budget = budget_filter_140
    qs_140 = Cuisine.objects.filter(max_price__gte=selected_budget.min_price).distinct()
    results_140 = [c.name for c in qs_140]
    print(f"Result (Filter 140): {results_140}")

    if "African Cuisine" not in results_140 and "American Cuisine" not in results_140:
        print("SUCCESS: 140 filter excludes both.")
    else:
        print("FAILURE: Should exclude strictly cheaper options.")

if __name__ == "__main__":
    verify_cumulative_budget()
