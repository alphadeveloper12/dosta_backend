import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Cuisine, BudgetOption

def verify_budget_cuisine():
    # Create or get a budget option
    budget, created = BudgetOption.objects.get_or_create(
        label="Test Budget",
        defaults={'price_range': '$10-20', 'max_price': 20.00}
    )
    print(f"Budget: {budget} (Created: {created})")

    # Create or get a cuisine
    cuisine, created = Cuisine.objects.get_or_create(
        name="Test Cuisine",
        defaults={'image': 'cuisines/test.jpg'}
    )
    print(f"Cuisine: {cuisine} (Created: {created})")

    # Add budget to cuisine
    cuisine.budget_options.add(budget)
    cuisine.save()
    print("Added budget to cuisine.")

    # Verify filtering
    filtered_cuisines = Cuisine.objects.filter(budget_options__id=budget.id)
    if cuisine in filtered_cuisines:
        print("SUCCESS: Cuisine found when filtering by budget id.")
    else:
        print("FAILURE: Cuisine NOT found when filtering by budget id.")

    # Cleanup (optional, but good for reliable tests)
    # cuisine.budget_options.remove(budget)
    # cuisine.delete()
    # budget.delete()

if __name__ == "__main__":
    verify_budget_cuisine()
