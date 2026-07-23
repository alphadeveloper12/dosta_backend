import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course

def inspect_courses():
    print("Inspecting Courses...")
    courses = Course.objects.filter(name__icontains="Dessert")
    for c in courses:
        print(f"ID: {c.id}, Name: '{c.name}', Image: '{c.image}'")

    print("\nInspecting Main Courses...")
    mains = Course.objects.filter(name__icontains="Main")
    for m in mains:
        print(f"ID: {m.id}, Name: '{m.name}', Image: '{m.image}'")
        
    print("\nInspecting Salads...")
    salads = Course.objects.filter(name__icontains="Salad")
    for s in salads:
        print(f"ID: {s.id}, Name: '{s.name}', Image: '{s.image}'")

if __name__ == "__main__":
    inspect_courses()
