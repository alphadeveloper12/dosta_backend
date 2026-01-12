import sys
import os
import django
from decimal import Decimal

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

def populate():
    print("Starting Indian Menu Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Indian")
    if created:
        print(f"Created Cuisine: {cuisine.name}")
        # Assign a default placeholder if needed or handle manually later
        # cuisine.image = ... 
        # cuisine.save()
    else:
        print(f"Found Cuisine: {cuisine.name}")

    # 2. Setup Budget Option (100 AED)
    # Check if a budget with '100' in price_range or label exists, else create one
    budget, created = BudgetOption.objects.get_or_create(
        price_range="100 AED",
        defaults={
            "label": "Standard",
            "min_price": Decimal("100.00"),
            "max_price": Decimal("100.00")
        }
    )
    if created:
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    # Structure: Course Name -> List of Item Names
    menu_structure = {
        "Salads & Chaats": [
            "Aloo Chaat",
            "Bhoondi Raita",
            "Chana Chaat",
            "Hummus",
            "Oriental Salad",
            "Fresh Bar Salad with dressings: Cucumbers Carrots, Tomatoes & Lettuce leaves"
        ],
        "Main Courses": [
            "Mutton Biryani",
            "Fish Curry",
            "Yellow Dhal",
            "Butter Chicken",
            "Aloo Mutter",
            "Bagan Masala",
            "Steamed Rice",
            "Paratha & Papadums"
        ],
        "Desserts": [
            "Assorted Indian sweets",
            "Rice Kheer",
            "Fresh cut fruit",
            "Gulab Jamun (Hot)"
        ],
        "Hot Beverages": [
            "Freshly Brewed Coffee or Tea"
        ]
    }

    # Placeholder image path (relative to MEDIA_ROOT)
    placeholder_image = "menu_items/placeholder.svg"

    all_courses = []
    all_items = []

    for course_name, item_names in menu_structure.items():
        # Get or Create Course - Handle duplicates by taking the first one
        course = Course.objects.filter(name=course_name).first()
        if not course:
            course = Course.objects.create(name=course_name)
            print(f"  Created Course: {course.name}")
        else:
            print(f"  Found Course: {course.name}")
        c_created = False # Since we handled it manually
        
        # Link Course to Cuisine and Budget if not already
        course.cuisines.add(cuisine)
        course.budget_options.add(budget)
        all_courses.append(course)

        for item_name in item_names:
            # Create MenuItem
            # We use get_or_create to avoid duplicates if run multiple times
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
            
            # If it was created, or if we want to enforce the placeholder if missing:
            if not item.image:
                item.image = placeholder_image
                item.save()
            
            if i_created:
                print(f"    Created Item: {item.name}")
            
            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "Indian Feast Menu"
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
