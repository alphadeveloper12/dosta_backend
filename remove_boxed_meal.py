import sys
import os
import django

# Add current directory to path so 'dosta' package is resolvable
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import ServiceStyle, FixedCateringMenu, Course, MenuItem

def remove_boxed_meal():
    print("Starting Boxed Meal Removal...")
    
    # 1. Find the ServiceStyle
    # Searching case-insensitive to be sure
    services = ServiceStyle.objects.filter(name__icontains="boxed")
    
    if not services.exists():
        print("No ServiceStyle found matching 'boxed'.")
    
    for service in services:
        print(f"Found ServiceStyle: {service.name} (ID: {service.id})")
        
        # 2. Find associated FixedCateringMenus?
        # FixedCateringMenu usually links to Cuisine/Budget, but might implicitly belong to a service style
        # In this project, it seems FixedCateringMenu doesn't directly link to ServiceStyle in the models I've seen in snippets,
        # but typically the frontend filters Service -> Cuisine -> Menu.
        # If there are menus specifically for boxed meals, they might be named explicitly or linked if the model supports it.
        # Let's check for menus with 'boxed' in the name.
        
        menus = FixedCateringMenu.objects.filter(name__icontains="boxed")
        for menu in menus:
            print(f"  Deleting FixedCateringMenu: {menu.name} (ID: {menu.id})")
            menu.delete()
            
        print(f"Deleting ServiceStyle: {service.name}")
        service.delete()
        print("Deletion complete.")

if __name__ == "__main__":
    remove_boxed_meal()
