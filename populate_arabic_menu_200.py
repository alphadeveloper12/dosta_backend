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
    # Remove things like (D), (G), (N), (...)
    # Regex to match parens with 1-3 chars or dots inside, or just empty parens
    cleaned = re.sub(r'\s*\([A-Za-z,\.\s]+\)', '', name)
    cleaned = re.sub(r'\s*\(\.\.\.\)', '', cleaned)
    return cleaned.strip()

def populate():
    print("Starting Arabic Menu (200 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Arabic")
    if created:
        print(f"Created Cuisine: {cuisine.name}")
        if not cuisine.image:
             cuisine.image = "menu_items/placeholder.svg"
             cuisine.save()
    else:
        print(f"Found Cuisine: {cuisine.name}")

    # 2. Setup Budget Option (200 AED)
    budget = BudgetOption.objects.filter(price_range="200 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="200 AED",
            label="Royal", # Assuming 200 is Royal based on previous context
            min_price=Decimal("200.00"),
            max_price=Decimal("200.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    menu_structure = {
        "Salads": [
            "Hummus / Mutable / Raheb",
            "Tabbouleh Salad",
            "Fattouch Salad",
            "Beetroot Corn Salad",
            "Fresh Salad Bar: Mix Lettuce, Tomato, Cucumber, Lemon, Green Chili, Red Onion, pickles, sauces",
            "Arabic bread Basket"
        ],
        "Soups": [
            "Lentil Soup with Condiments"
        ],
        "Starters": [
            "Cheese Roll",
            "Spinach Fatayer"
        ],
        "Live Stations": [
            "Arabic Mix Grill (Shish Tawook, Lamb Kofta, Chicken Wings)"
        ],
        "Main Courses": [
            "Fish Filet with Harrah Sauce",
            "Chicken Bil Sanyeeh",
            "Lamb Shakrieh",
            "Eggplant Moussaka",
            "Assorted Steamed Vegetables",
            "Roasted Potatoes",
            "Saffron Rice"
        ],
        "Desserts": [
            "Mix Arabic Sweets",
            "Mohalabieh",
            "Crème Caramel",
            "Fresh Fruit Cut",
            "Um Ali"
        ],
        "Beverages": [
            "Soft Drinks / Water/ Tea /Coffee"
        ]
    }

    placeholder_image = "menu_items/placeholder.svg"

    all_courses = []
    all_items = []

    for course_name, item_names in menu_structure.items():
        # Get or Create Course - Handle duplicates by taking the first one
        course = Course.objects.filter(name__iexact=course_name).first()
        if not course:
            course = Course.objects.create(name=course_name)
            print(f"  Created Course: {course.name}")
        else:
            print(f"  Found Course: {course.name}")
        
        # Link Course to Cuisine and Budget
        course.cuisines.add(cuisine)
        course.budget_options.add(budget)
        all_courses.append(course)
        
        # Ensure course has image
        if not course.image:
            course.image = placeholder_image
            course.save()

        for raw_name in item_names:
            item_name = clean_name(raw_name)
            # Create MenuItem
            item, i_created = MenuItem.objects.get_or_create(
                name=item_name,
                course=course,
                cuisine=cuisine,
                defaults={
                    "description": "", 
                    "image": placeholder_image
                }
            )
            
            # Ensure it has the budget option
            item.budget_options.add(budget)
            
            # Update image if missing
            if not item.image:
                item.image = placeholder_image
                item.save()
            
            if i_created:
                print(f"    Created Item: {item.name}")
            
            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "Arabic Royal Menu"
    fixed_menu, m_created = FixedCateringMenu.objects.get_or_create(
        name=menu_name,
        cuisine=cuisine,
        budget_option=budget
    )
    
    # Update ManyToMany fields
    fixed_menu.courses.set(all_courses)
    fixed_menu.items.set(all_items)
    fixed_menu.save()

    if m_created:
        print(f"Created FixedCateringMenu: {fixed_menu.name}")
    else:
        print(f"Updated FixedCateringMenu: {fixed_menu.name}")

    print("Population Complete!")

if __name__ == "__main__":
    populate()
