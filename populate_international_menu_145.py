import sys
import os
import django
from decimal import Decimal
import re

# Add current directory to path so 'dosta' package is resolvable
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import (
    Cuisine, 
    BudgetOption, 
    Course, 
    MenuItem, 
    FixedCateringMenu
)

def clean_name(name):
    cleaned = re.sub(r'\([A-Za-z,\.\s]+\)$', '', name.strip())
    # Convert to Title Case
    cleaned = cleaned.title()
    return cleaned.strip()

def populate():
    print("Starting International Menu (145 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="International")
    # ...

    # 2. Setup Budget Option (145 AED)
    budget = BudgetOption.objects.filter(price_range="145 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="145 AED",
            label="Exclusive",
            min_price=Decimal("145.00"),
            max_price=Decimal("145.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    menu_structure = {
        "Salads": [
            "SEAFOOD SALAD",
            "FATOUCH",
            "HUMMUS / BABAGANOOG",
            "KACHAMBER SALAD",
            "SELECTION OF SALAD LEAVES",
            "FRESH SALAD BAR: DRESSINGS AND CONDIMENTS",
            "SELECTION OF INTERNATIONAL BREAD"
        ],
        "Soup": [
            "Lentil Soup with Condiments"
        ],
        "Under The Light": [
            "Crispy Fried Vegetables Samosa"
        ],
        "Live Stations": [
            "Mix Grill (Shish Tawook, Lamb Kofta)"
        ],
        "Main Course": [
            "Mutton Biryani",
            "Butter Chicken",
            "Grilled Fish Filet with Hara Sauce",
            "Seafood Thermidor",
            "Meat Lasagna",
            "White Rice",
            "Vegetables Korma",
            "Roasted Potato with Herbs"
        ],
        "Dessert": [
            "Assorted French Pastries",
            "Assorted Mousse in Shooters",
            "Assorted Dry Fruits Cake",
            "Mohalabieh in Cups",
            "Thai Coconut Fruits Salad",
            "Birthday Cake",
            "Um Ali"
        ],
        "Beverages": [
            "Chilled Juice / Soft Drinks / Water"
        ]
    }

    placeholder_image = "menu_items/placeholder.svg"

    all_courses = []
    all_items = []

    for course_name, item_names in menu_structure.items():
        course = Course.objects.filter(name__iexact=course_name).first()
        if not course:
            course = Course.objects.create(name=course_name)
            print(f"  Created Course: {course.name}")
        else:
            print(f"  Found Course: {course.name}")
        
        course.cuisines.add(cuisine)
        course.budget_options.add(budget)
        all_courses.append(course)
        
        if not course.image:
            course.image = placeholder_image
            course.save()

        for raw_name in item_names:
            item_name = clean_name(raw_name)
            
            item = MenuItem.objects.filter(
                name=item_name,
                course=course,
                cuisine=cuisine
            ).first()

            if not item:
                item = MenuItem.objects.create(
                    name=item_name,
                    course=course,
                    cuisine=cuisine,
                    description="",
                    image=placeholder_image
                )
                print(f"    Created Item: {item.name}")
            else:
                 if not item.image:
                    item.image = placeholder_image
                    item.save()

            # NEW: Image sourcing
            source_folder = os.path.join(django.conf.settings.MEDIA_ROOT, 'source_images', 'International', '145 AED')
            if os.path.exists(source_folder):
                try:
                    target_name = item.name.lower().strip()
                    files = os.listdir(source_folder)
                    found_image = None
                    
                    for filename in files:
                        name_without_ext = os.path.splitext(filename)[0].lower()
                        if name_without_ext == target_name:
                            found_image = filename
                            break
                        if target_name in name_without_ext:
                            found_image = filename
                            break
                    
                    if found_image:
                        source_path = os.path.join(source_folder, found_image)
                        with open(source_path, 'rb') as f:
                            from django.core.files import File
                            item.image.save(found_image, File(f), save=True)
                            print(f"      Attached image: {found_image}")
                except Exception as e:
                    print(f"      Error attached image: {e}")

            item.budget_options.add(budget)
            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "International Exclusive Menu"
    fixed_menu, m_created = FixedCateringMenu.objects.get_or_create(
        name=menu_name,
        cuisine=cuisine,
        budget_option=budget
    )
    
    fixed_menu.courses.set(all_courses)
    fixed_menu.items.set(all_items)
    fixed_menu.save()

    print("Population Complete!")

if __name__ == "__main__":
    populate()
