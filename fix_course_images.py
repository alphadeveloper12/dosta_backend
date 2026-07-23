import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course

def check_and_fix_images():
    print("Checking Course images...")
    courses = Course.objects.all()
    placeholder = "menu_items/placeholder.svg"
    
    for course in courses:
        print(f"Course: {course.name}, Image: '{course.image}'")
        if not course.image:
            print(f"  -> Missing image! Assigning placeholder.")
            course.image = placeholder
            course.save()
        elif str(course.image) == "": # Check for empty string field
             print(f"  -> Empty image string! Assigning placeholder.")
             course.image = placeholder
             course.save()
            
    print("Done.")

if __name__ == "__main__":
    check_and_fix_images()
