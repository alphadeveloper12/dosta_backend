import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course, MenuItem, FixedCateringMenu

def deep_inspect():
    print("Deep Inspecting IDs...")
    
    # 1. All Main Courses
    mains = Course.objects.filter(name__icontains="Main")
    print(f"Main Courses in DB:")
    for c in mains:
        item_count = MenuItem.objects.filter(course=c).count()
        print(f"  [Course ID: {c.id}] Name: '{c.name}', Items Linked: {item_count}")

    # 2. Check Menus
    print("\nMenus and their Main Course IDs:")
    menus = FixedCateringMenu.objects.all()
    for menu in menus:
        # Get courses with "Main" in name
        menu_mains = menu.courses.filter(name__icontains="Main")
        ids = [str(c.id) for c in menu_mains]
        print(f"  [Menu: {menu.name}] has Main Course IDs: {', '.join(ids)}")
        
        # Also check items in the menu that are supposed to be Main Course
        # Just check one sample item if possible
        # We can check if the menu even HAS items
        item_count = menu.items.count()
        print(f"    -> Total Items in Menu M2M: {item_count}")

    # 3. Check specific Item
    print("\nChecking specific item 'Mutton Biryani':")
    items = MenuItem.objects.filter(name="Mutton Biryani")
    for item in items:
        print(f"  [Item ID: {item.id}] Name: '{item.name}' -> Linked to Course ID: {item.course.id} ({item.course.name})")

if __name__ == "__main__":
    deep_inspect()
