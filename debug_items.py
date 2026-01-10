import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course, MenuItem, FixedCateringMenu

def debug_linkage():
    print("Debugging Item Linkages...")
    
    # 1. Find all Main Courses
    mains = Course.objects.filter(name__icontains="Main")
    print(f"Found {mains.count()} 'Main' related courses:")
    for c in mains:
        item_count = MenuItem.objects.filter(course=c).count()
        menu_count = c.fixed_menus.count() # Reverse related name 'fixed_menus'
        print(f"  ID: {c.id}, Name: '{c.name}', Items: {item_count}, Linked Menus: {menu_count}")
        
    # 2. Check specific items
    sample_items = ["Mutton Biryani", "Butter Chicken", "Chicken Tikka Masala"]
    print("\nChecking sample items:")
    for name in sample_items:
        items = MenuItem.objects.filter(name=name)
        if items.exists():
            for item in items:
                print(f"  Item '{item.name}' (ID: {item.id}) -> Course: {item.course.name} (ID: {item.course.id})")
        else:
            print(f"  Item '{name}' NOT FOUND")

    # 3. Check what's on the menus
    print("\nChecking Menus for Main Courses:")
    menus = FixedCateringMenu.objects.all()
    for menu in menus:
        menu_mains = menu.courses.filter(name__icontains="Main")
        print(f"  Menu: {menu.name}")
        if menu_mains.exists():
            for mm in menu_mains:
                print(f"    -> Has Course: {mm.name} (ID: {mm.id})")
        else:
            print("    -> No Main Course linked!")

if __name__ == "__main__":
    debug_linkage()
