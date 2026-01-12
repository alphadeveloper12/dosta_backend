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
    print("Starting International Menu (100 AED) Population [Correction]...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="International")
    
    # 2. Setup Budget Option (100 AED)
    budget = BudgetOption.objects.filter(price_range="100 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="100 AED",
            label="Feast",
            min_price=Decimal("100.00"),
            max_price=Decimal("100.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    # Corrected typos from user input (KOFAT -> Kofta, BACKED -> Baked, etc.)
    menu_structure = {
        "Salads": [
            "HUMMOUS",
            "MUTABLE",
            "FATOUCH",
            "PASTA & TUNA SALAD",
            "CEASAR SALAD WITH CHICKEN",
            "SELECTION OF SALAD LEAVES",
            "FRESH SALAD BAR: DRESSINGS AND CONDIMENTS",
            "SELECTION OF INTERNATIONAL BREAD"
        ],
        "Soups": [
            "Cream of Tomato"
        ],
        "Under The Heating Lamp": [
            "Crispy Fried Samosa"
        ],
        "Main Course": [
            "GRILLED FISH WITH LEMON BUTTER SAUCE",
            "MIX GRILL (Kofta, Shish Tawook)", # Corrected spelling
            "BUTTER CHICKEN",
            "LAMB BIRYANI",
            "WHITE RICE",
            "EGGPLANT MOUSSAKA", # Corrected spelling
            "HERBS, ROASTED POTATO",
            "GRILLED VEGETABLES WITH BALSAMIC"
        ],
        "Dessert": [
            "MINI CARROTS CAKE",
            "MANGO MOHALABIEH",
            "BAKED CHEESE CAKE", # Corrected spelling
            "MARBLE DRY CAKE",
            "FRESH FRUITS CUT"
        ],
        "Beverages": [
            "Soft Drinks / Water"
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
            
            # Robust Get or Create logic
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

            item.budget_options.add(budget)
            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "International Feast Menu"
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
