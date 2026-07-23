import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import FixedCateringMenu, MenuItem

def check_menus():
    print("Checking FixedCateringMenu objects...")
    menus = FixedCateringMenu.objects.all()
    count = menus.count()
    print(f"Total Menus: {count}")
    
    if count == 0:
        print("WARNING: No FixedCateringMenu objects found!")
        return

    for menu in menus:
        print(f"ID: {menu.id} | Name: {menu.name}")
        print(f"  Cuisine: {menu.cuisine.name} | Budget: {menu.budget_option.price_range} ({menu.budget_option.label})")
        print(f"  Courses Count: {menu.courses.count()}")
        print(f"  Items Count: {menu.items.count()}")
        print("-" * 40)

if __name__ == "__main__":
    check_menus()
