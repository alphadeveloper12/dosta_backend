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
    print("Starting African Menu (120 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="African") # New Cuisine
    if created:
        print(f"Created Cuisine: {cuisine.name}")
        if not cuisine.image:
             cuisine.image = "menu_items/placeholder.svg"
             cuisine.save()
    else:
        print(f"Found Cuisine: {cuisine.name}")

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
    # Handling comma separated strings manually where needed
    menu_structure = {
        "Salads & Starters": [
            "Spinach & Shrimps Salad", "Spicy Cassava Salad",
            "Hummus", "Green Salads", "Three Beans Salad",
            "Fresh Salad Bar with Dressings"
        ],
        "Soup": [
            "Roasted Pumpkin Creamy Soup"
        ],
        "Hot Appetizers": [
            "Vegetables Spring Rolls with Sweet Chili Sauce"
        ],
        "Main Dish": [
            "Lamb Stew with White Beans",
            "Shredded Beef pie with green peas and Pepper Sauce",
            "Spicy Chicken Skewers. Served with light garlic sauce",
            "Grilled Fish with Tomato Sauce",
            "Roasted Potato with Herbs",
            "Grilled Mix Vegetables",
            "Steamed Rice"
        ],
        "Dessert": [
            "Milk Cake",
            "Fruits Tart",
            "Cream Caramel",
            "Assorted French Pastries",
            "Fresh Fruits Salads"
        ],
        "Beverages": [
            "Water, Tea & Coffee"
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
    menu_name = "African Premium Menu"
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
