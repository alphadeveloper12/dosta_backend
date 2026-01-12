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
    print("Starting International Menu (90 AED) Population [Correction]...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="International")
    
    # 2. Setup Budget Option (90 AED)
    budget = BudgetOption.objects.filter(price_range="90 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="90 AED",
            label="Standard",
            min_price=Decimal("90.00"),
            max_price=Decimal("90.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    # Reverting to the authorized "Standard" menu
    menu_structure = {
        "Salads": [
            "HUMMOUS",
            "FATOUCH",
            "CEASAR SALAD",
            "SELECTION OF SALAD LEAVES",
            "FRESH SALAD BAR: DRESSINGS AND CONDIMENTS",
            "SELECTION OF INTERNATIONAL BREAD"
        ],
        "Main Courses": [
            "MIX GRILL (KOFTA, SHISH TAWOK)",
            "FISH WITH LEMON BUTTER SAUCE",
            "CHICKEN WITH POTATO",
            "MUTTON BIRYANI",
            "WHITE RICE",
            "POTATO GRATIN",
            "STEAMED VEGETABLES"
        ],
        "Dessert": [
            "CREAM CARAMEL",
            "MOHALABIEH",
            "VANILLA SPONGE CAKE",
            "FRESH FRUITS CUT"
        ],
        "Beverages": [
            "SOFT DRINKS / WATER"
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
            
            # Robust Get or Create
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
    menu_name = "International Standard Menu"
    fixed_menu, m_created = FixedCateringMenu.objects.get_or_create(
        name=menu_name,
        cuisine=cuisine,
        budget_option=budget
    )
    
    # Update ManyToMany fields (Sets the items for this menu, replacing previous incorrect ones)
    fixed_menu.courses.set(all_courses)
    fixed_menu.items.set(all_items)
    fixed_menu.save()

    print("Population Complete!")

if __name__ == "__main__":
    populate()
