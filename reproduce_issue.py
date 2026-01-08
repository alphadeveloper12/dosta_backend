import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Cuisine, BudgetOption, ServiceStyle

def reproduce_issue():
    # Setup Data
    print("Setting up data...")
    
    # Create Budget
    budget_125, _ = BudgetOption.objects.get_or_create(label="125 AED", defaults={'price_range': '125', 'max_price': 125})
    budget_other, _ = BudgetOption.objects.get_or_create(label="Other Budget", defaults={'price_range': '200', 'max_price': 200})

    # Create Service Style
    buffet, _ = ServiceStyle.objects.get_or_create(name="Buffet")

    # Create Cuisines
    american, _ = Cuisine.objects.get_or_create(name="American Cuisine")
    italian, _ = Cuisine.objects.get_or_create(name="Italian Cuisine")
    
    # Assign Service Style to both
    buffet.cuisines.add(american, italian)

    # Assign Budget ONLY to American
    american.budget_options.add(budget_125)
    
    # Clear budget from Italian just in case
    italian.budget_options.clear()
    
    print(f"American Budget Options: {american.budget_options.all()}")
    print(f"Italian Budget Options: {italian.budget_options.all()}")

    # Initial Query: Filter by Service Style ONLY
    qs_service = Cuisine.objects.filter(service_styles__id=buffet.id)
    print(f"\nQuery (Service Style={buffet.id}): {[c.name for c in qs_service]}")
    
    # Secondary Query: Filter by Service Style AND Budget
    qs_budget = qs_service.filter(budget_options__id=budget_125.id)
    print(f"Query (Service Style={buffet.id} AND Budget={budget_125.id}): {[c.name for c in qs_budget]}")

    # Check matches
    if italian in qs_budget:
        print("\nISSUE REPRODUCED: Italian should NOT be here!")
    else:
        print("\nLogic seems correct: Only American matches.")

    # Check distinct query just in case duplicates are causing confusion (though duplicates shouldn't include wrong items)
    # But if Italian was somehow showing up, we need to know why.

if __name__ == "__main__":
    reproduce_issue()
