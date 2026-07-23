
import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\User\Desktop\main\dosta_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import BudgetOption, Cuisine

def check_relationships():
    print("Checking BudgetOption - Cuisine relationships...")
    cuisines = Cuisine.objects.all()
    for c in cuisines:
        budgets = c.budget_options.all()
        print(f"Cuisine: {c.name} (ID: {c.id}) linked to {budgets.count()} budgets:")
        for b in budgets:
            print(f"  - {b.label} (ID: {b.id})")

    print("\nChecking reverse from BudgetOption...")
    budgets = BudgetOption.objects.all()
    for b in budgets:
        related_cuisines = b.cuisines.all()
        print(f"Budget: {b.label} (ID: {b.id}) linked to {related_cuisines.count()} cuisines:")
        for c in related_cuisines:
             print(f"  - {c.name} (ID: {c.id})")

if __name__ == '__main__':
    check_relationships()
