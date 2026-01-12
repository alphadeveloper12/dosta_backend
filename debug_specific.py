import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import FixedCateringMenu, Cuisine, BudgetOption

def debug():
    print("Checking Cuisines...")
    cuisines = Cuisine.objects.all()
    for c in cuisines:
        print(f"ID: {c.id} | Name: '{c.name}'")

    print("\nChecking 'International Premium Menu' (120 AED)...")
    menu120 = FixedCateringMenu.objects.filter(budget_option__price_range__icontains="120", cuisine__name__icontains="International").first()
    if menu120:
        print(f"FOUND: ID {menu120.id} | Name: {menu120.name} | Budget: {menu120.budget_option.price_range}")
    else:
        print("NOT FOUND: 'International Premium Menu' (120 AED)")
        # Check by name
        m_name = FixedCateringMenu.objects.filter(name="International Premium Menu").first()
        if m_name:
             print(f"FOUND BY NAME: ID {m_name.id} | Budget: {m_name.budget_option.price_range}")

    print("\nChecking 'International Standard Menu' (90 AED)...")
    menu90 = FixedCateringMenu.objects.filter(name="International Standard Menu").first()
    if menu90:
        print(f"FOUND: ID {menu90.id} | Budget: {menu90.budget_option.price_range}")
    else:
        print("NOT FOUND: 'International Standard Menu'")

if __name__ == "__main__":
    debug()
