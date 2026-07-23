import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course, MenuItem

def move_items():
    print("Moving items to correct Main Course...")
    
    # Target: The course linked to Menus (ID 44 from previous output)
    target_course = Course.objects.get(id=44) # Main Courses
    
    # Source: The course with the items (ID 40 from previous output, "Main Dish")
    # Note: Previous output showed ID 40 as "Main Dish" with 0 linked menus but items should be there?
    # Wait, let's verify the previous output first.
    # Output showed:
    # ID: 40, Name: 'Main Dish', Items: 0 (?) ...
    
    # Let's handle this dynamically based on finding the course WITH items.
    
    mains = Course.objects.filter(name__icontains="Main")
    source_courses = []
    
    for c in mains:
        item_count = MenuItem.objects.filter(course=c).count()
        if c.id != target_course.id and item_count > 0:
            source_courses.append(c)
            
    if not source_courses:
        print("No source courses with items found! Maybe items are deleted?")
        # Check if items exist at all?
        return

    for source in source_courses:
        print(f"Moving items from {source.name} (ID: {source.id}) to {target_course.name} (ID: {target_course.id})...")
        items = MenuItem.objects.filter(course=source)
        count = items.count()
        items.update(course=target_course)
        print(f"  Moved {count} items.")
        
        # Optionally delete the empty source course? 
        # User asked to restore, so let's keep it clean.
        # But wait, if source is 'Main Dish', maybe we should keep it if it's used elsewhere?
        # But for now, we want them in Main Courses.
        
    print("Move Complete.")

if __name__ == "__main__":
    move_items()
