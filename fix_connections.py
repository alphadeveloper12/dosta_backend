import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import FixedCateringMenu, Course

def fix_connections():
    print("Fixing Menu Connections...")
    
    # Get the Main Course
    # Based on previous output, ID 44 seems to be the target, but let's find it dynamically
    main_course = Course.objects.filter(name="Main Courses").first()
    if not main_course:
        print("ERROR: 'Main Courses' course not found!")
        return

    print(f"Using Main Course: {main_course.name} (ID: {main_course.id})")
    
    menus = FixedCateringMenu.objects.all()
    for menu in menus:
        # Check if it should have Main Courses
        # Generally all our Catering Menus (Indian/International) should.
        # Let's check if it has a 'Main' course.
        courses = menu.courses.all()
        has_main = any("Main" in c.name for c in courses)
        
        if not has_main:
            print(f"Adding Main Course to Menu: {menu.name}")
            menu.courses.add(main_course)
        else:
            print(f"Menu {menu.name} already has a Main Course.")

    print("Fix Complete.")

if __name__ == "__main__":
    fix_connections()
