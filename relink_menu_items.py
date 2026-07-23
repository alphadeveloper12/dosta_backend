import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import FixedCateringMenu, Course, MenuItem

def relink_menu_items():
    print("Relinking Menu Items...")
    
    menus = FixedCateringMenu.objects.all()
    for menu in menus:
        print(f"Processing Menu: {menu.name}")
        # Identify the Main Course for this menu
        # We assume ID 44 is the one we want as it's linked
        main_course = menu.courses.filter(name="Main Courses").first()
        
        if main_course:
            # Find items that belong to this Menu's Cuisine (and Budget ideally) AND the Main Course
            # Note: Items are filtered by Cuisine in population, but let's be safe.
            items = MenuItem.objects.filter(
                course=main_course,
                cuisine=menu.cuisine
                # We can filter by budget too if needed, but Cuisine match is primary for ensuring the right items per menu type
            )
            
            # Since items are shared by budget? Actually items have M2M budget options.
            # But FixedCateringMenu has a specific budget option.
            # So we should filter items that have THIS budget option.
            
            budget = menu.budget_option
            items = items.filter(budget_options=budget)
            
            count = items.count()
            if count > 0:
                print(f"  Found {count} items for {menu.name}. Linking...")
                menu.items.add(*items)
            else:
                print(f"  [WARNING] No items found for Main Course in this menu configuration.")
        else:
             print("  No Main Course linked to this menu.")

    print("Relink Complete.")

if __name__ == "__main__":
    relink_menu_items()
