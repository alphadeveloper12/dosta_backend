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
    cleaned = cleaned.replace("(Hot)", "")
    return cleaned.strip()

def populate():
    print("Starting Indian Menu (260 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Indian")
    # ...

    # 2. Setup Budget Option (260 AED)
    budget = BudgetOption.objects.filter(price_range="260 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="260 AED",
            label="Grand",
            min_price=Decimal("260.00"),
            max_price=Decimal("260.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    menu_structure = {
        "Chaats": [
            "Aloo Chaat",
            "Dahi Wada, Dhokla", 
            "Rajma Chaat, Channa Chaat",
            "Tomato & Onion Raita",
            "Fruit Chaat",
            "Pickles & Chutneys",
            "Vegetables Samosas"
        ],
        "Salads": [
            "Hummus / Mutable",
            "Oriental Salad / Tabbouleh",
            "Fresh Salad Bar with dressings: Cucumbers, Carrots, Tomatoes & Lettuce leaves"
        ],
        "Main Courses": [
            "Indian Mutton Biryani",
            "Chicken Fajitas",
            "Green Masala Chicken Kebab",
            "Fish Makani",
            "Maa Ki Dhal",
            "Lamb Chops Masala",
            "Mixed Vegetable Korma",
            "Gobi Szechwan",
            "Steamed Rice",
            "Paratha, Roti, Papadums"
        ],
        "Live Stations": [
            "Indian Mix Grill (Shish Lamb Kebab, Chicken Tikka)"
        ],
        "Desserts": [
            "Ras Malai",
            "Jalabi",
            "Gulab Jamun",
            "Mango cake",
            "Gajer Halwa",
            "Dark & White Chocolate Mousse",
            "Fresh cut Fruit",
            "Whole Fruit Display"
        ],
        "Beverages": [
            "Water & Soft Drinks"
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
            item, i_created = MenuItem.objects.get_or_create(
                name=item_name,
                course=course,
                cuisine=cuisine,
                defaults={
                    "description": "", 
                    "image": placeholder_image
                }
            )
            item.budget_options.add(budget)
            if not item.image:
                item.image = placeholder_image
                item.save()
            
            if i_created:
                print(f"    Created Item: {item.name}")
            
            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "Indian Grand Menu"
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
