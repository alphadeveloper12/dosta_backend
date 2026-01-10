import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course, MenuItem

def check_status():
    print("Checking 'Main Courses' status...")
    
    # Check Course
    courses = Course.objects.filter(name__icontains="Main")
    print(f"Main Courses found: {[c.name for c in courses]}")
    
    # Check a sample Item that should be in Main Courses
    sample_items = ["Mutton Biryani", "Butter Chicken", "Mix Grill (Kofta, Shish Tawok)"]
    for name in sample_items:
        exists = MenuItem.objects.filter(name=name).exists()
        print(f"Item '{name}' exists: {exists}")

if __name__ == "__main__":
    check_status()
