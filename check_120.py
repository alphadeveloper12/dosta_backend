import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import FixedCateringMenu

def check_120():
    print("Checking for 120 AED Menus...")
    menus = FixedCateringMenu.objects.filter(budget_option__price_range__icontains="120")
    
    if not menus.exists():
        print("No 120 AED menus found.")
    
    for menu in menus:
        print(f"FOUND: ID {menu.id} | {menu.name} | {menu.cuisine.name} | {menu.budget_option.price_range}")

if __name__ == "__main__":
    check_120()
