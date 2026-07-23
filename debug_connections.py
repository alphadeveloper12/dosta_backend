import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import FixedCateringMenu, Course

def inspect_menus():
    print("Inspecting Menus and Courses...")
    print("-" * 50)
    
    menus = FixedCateringMenu.objects.all()
    for menu in menus:
        print(f"Menu: {menu.name} (Cuisine: {menu.cuisine.name})")
        courses = menu.courses.all()
        course_names = [c.name for c in courses]
        print(f"  Courses: {course_names}")
        
        # Check specifically for Main Courses
        has_main = any("Main" in c.name for c in courses)
        if not has_main:
            print("  [WARNING] No 'Main' course found in this menu!")
    
    print("-" * 50)
    print("Checking All 'Main' Courses in DB:")
    mains = Course.objects.filter(name__icontains="Main")
    for m in mains:
        print(f"ID: {m.id}, Name: '{m.name}', Image: '{m.image}', Linked Menus: {m.fixed_menus.count()}")

if __name__ == "__main__":
    inspect_menus()
