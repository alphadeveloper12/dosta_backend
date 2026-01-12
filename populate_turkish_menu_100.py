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
    print("Starting Turkish Menu (100 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Turkish")
    if created:
        print(f"Created Cuisine: {cuisine.name}")
        if not cuisine.image:
             cuisine.image = "menu_items/placeholder.svg"
             cuisine.save()
    else:
        print(f"Found Cuisine: {cuisine.name}")

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
    menu_structure = {
        "Starters & Appetizers": [
            ("Meze Platter", "A selection of hummus, baba ghanoush, and tzatziki served with warm pita bread."),
            ("Stuffed Grape Leaves (Dolma)", "Vine leaves stuffed with rice, herbs, and spices."),
            ("Tabbouleh Salad", "Fresh parsley, tomatoes, bulgur, and mint dressed in lemon and olive oil."),
            ("Cacık", "Yogurt dip with cucumber, garlic, and dill, served with bread.")
        ],
        "Main Courses": [
            ("Chicken Kebab", "Marinated chicken skewers grilled to perfection, served with a side of rice."),
            ("Lamb Kofta", "Spiced ground lamb patties grilled and served with a tangy sauce."),
            ("Vegetable Moussaka", "Layered eggplant dish baked with tomato sauce and topped with béchamel."),
            ("Pide (Turkish Pizza)", "Flatbread topped with minced meat, cheese, and herbs.")
        ],
        "Desserts": [
            ("Baklava", "Layers of phyllo pastry filled with nuts and sweetened with honey syrup."),
            ("Rice Pudding (Sütlaç)", "Creamy rice pudding garnished with cinnamon."),
            ("Fresh Cut Fruit", "A selection of seasonal fresh fruits.")
        ],
        "Hot Beverages": [
            ("Turkish Tea", ""),
            ("Soft Drinks", "")
        ]
    }

    placeholder_image = "menu_items/placeholder.svg"

    all_courses = []
    all_items = []

    for course_name, items_data in menu_structure.items():
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

        for name_raw, description in items_data:
            item_name = clean_name(name_raw)
            
            # Check for existing item with same name, course, cuisine
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
                    description=description,
                    image=placeholder_image
                )
                print(f"    Created Item: {item.name}")
            else:
                # Update description if provided
                if description and item.description != description:
                    item.description = description
                    item.save()
                    print(f"    Updated Description: {item.name}")

                if not item.image:
                    item.image = placeholder_image
                    item.save()

            item.budget_options.add(budget)
            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "Turkish Feast Menu"
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
