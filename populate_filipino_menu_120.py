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
    # Remove (V), (N) etc at the end
    cleaned = re.sub(r'\([A-Za-z,\.\s]+\)$', '', name.strip())
    # Convert to Title Case
    cleaned = cleaned.title()
    return cleaned.strip()

def populate():
    print("Starting Filipino Menu (120 AED) Population...")

    # 1. Setup Cuisine - Handle potential typo from previous data
    cuisine = Cuisine.objects.filter(name__iexact="philipino").first()
    if cuisine:
        print(f"Found existing cuisine 'philipino', renaming to 'Filipino'...")
        cuisine.name = "Filipino"
        cuisine.save()
    else:
        cuisine = Cuisine.objects.filter(name__iexact="Filipino").first()
        if not cuisine:
            cuisine = Cuisine.objects.create(name="Filipino")
            print(f"Created Cuisine: {cuisine.name}")
        else:
             print(f"Found Cuisine: {cuisine.name}")

    if not cuisine.image:
        cuisine.image = "menu_items/placeholder.svg"
        cuisine.save()

    # 2. Setup Budget Option (120 AED)
    budget = BudgetOption.objects.filter(price_range="120 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="120 AED",
            label="Premium",
            min_price=Decimal("120.00"),
            max_price=Decimal("120.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    menu_structure = {
        "Salads": [
            "Glass Noodles Salad With Chicken",
            "Mix Green Salad",
            "Macaroni Salad",
            "Mango Prawn Salad",
            "Fresh Salad Bar"
        ],
        "Bread": [
            "Selection Of Bread"
        ],
        "Soups": [
            "Seafood Tom Yum"
        ],
        "Under The Light": [
            "Crispy Fried Spring Rolls – Sweet Chili"
        ],
        "Main Course": [
            "Stir Fried Beef With Broccoli In Oyster Sauce",
            "Roasted Fish With Soya Ginger Sauce",
            "Satay Beef & Chicken Skewers",
            "Kung Pao Chicken", # Corrected from Kung Poa
            "Chicken Noodles",
            "White Steamed Rice",
            "Vegetable Chopsuey", # Corrected from Vegetables Choup Choue
            "Roasted Potato With Herbs"
        ],
        "Dessert": [
            "Rice Pudding",
            "Cream Caramel",
            "Fresh Fruits", # Corrected from Fresh Fruit Fruits
            "Assorted Dry Cake",
            "Assorted Mousse"
        ],
        "Beverages": [
            "Soft Drinks / Water"
        ]
    }

    placeholder_image = "menu_items/placeholder.svg"

    all_courses = []
    all_items = []

    for course_name, items_list in menu_structure.items():
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

        for raw_name in items_list:
            item_name = clean_name(raw_name)
            
            # Check for existing item
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
    menu_name = "Filipino Premium Menu"
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
