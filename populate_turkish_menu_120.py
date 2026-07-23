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
    print("Starting Turkish Menu (120 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Turkish")
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
    menu_structure = {
        "Starters & Appetizers": [
            ("Meze Platter", "A selection of hummus, baba ghanoush, tzatziki, and muhammara served with warm pita bread."),
            ("Stuffed Grape Leaves (Dolma)", "Vine leaves stuffed with rice, herbs, and spices."),
            ("Fattoush Salad", "Mixed greens with tomatoes, cucumbers, radishes, and crispy pita chips tossed in a lemon-sumac dressing."),
            ("Sigara Böreği", "Crispy phyllo rolls filled with feta cheese and herbs.")
        ],
        "Main Courses": [
            ("Lamb Kebab", "Marinated lamb skewers grilled to perfection, served with a side of rice."),
            ("Chicken Shish Kebab", "Tender chicken marinated in spices and grilled on skewers."),
            ("Manti (Turkish Dumplings)", "Dumplings filled with spiced ground meat, served with yogurt and garlic sauce."),
            ("Vegetable Casserole (Börek)", "Layers of phyllo pastry filled with spinach, cheese, and herbs."),
            ("Beef Kofta", "Spiced ground beef patties grilled and served with a tangy sauce.")
        ],
        "Desserts": [
            ("Baklava", "Layers of phyllo pastry filled with nuts and sweetened with honey syrup."),
            ("Künefe", "A sweet cheese pastry soaked in syrup, topped with crushed pistachios."),
            ("Turkish Delight", "A variety of flavored Turkish delight dusted with powdered sugar."),
            ("Fresh Cut Fruit", "A selection of seasonal fresh fruits.")
        ],
        "Beverages": [
            ("Soft Drinks", ""),
            ("Tea", ""),
            ("Water", "")
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
    menu_name = "Turkish Premium Menu"
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
