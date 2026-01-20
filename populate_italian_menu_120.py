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
    print("Starting Italian Menu (120 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Italian")
    
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
    # Structure: CourseName -> List of tuples (ItemName, Description)
    menu_structure = {
        "Salads & Antipasto": [
            ("Caprese Salad", "Fresh mozzarella, tomatoes, basil, and balsamic drizzle."),
            ("Arugula Salad", "Arugula with parmesan, pine nuts, and lemon vinaigrette."),
            ("Panzanella Salad", "Bread salad with tomatoes, cucumbers, and red onions."),
            ("Antipasto Platter", "Cured meats, cheeses, olives, and marinated vegetables."),
            ("Fresh Bar Salad with dressings", "Mixed greens, cucumbers, carrots, and cherry tomatoes.")
        ],
        "Main Courses": [
            ("Lasagna", "Traditional meat lasagna with béchamel and marinara sauce."),
            ("Chicken Piccata", "Chicken breast in a lemon-caper sauce."),
            ("Eggplant Parmesan", "Layered eggplant with marinara sauce and mozzarella."),
            ("Risotto Primavera", "Creamy risotto with seasonal vegetables."),
            ("Grilled Shrimp Scampi", "Shrimp sautéed in garlic and white wine."),
            ("Penne Arrabbiata", "Penne pasta in a spicy tomato sauce."),
            ("Garlic Bread", "")
        ],
        "Desserts": [
            ("Tiramisu", "Classic Italian dessert with coffee-soaked ladyfingers."),
            ("Panna Cotta", "Creamy dessert served with berry coulis."),
            ("Cannoli", "Crispy pastry filled with sweet ricotta cream."),
            ("Chocolate Mousse", ""),
            ("Fresh Cut Fruit", "")
        ],
        "Beverages": [
            ("Water & Soft Drinks", "")
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

            # NEW: Image sourcing
            source_folder = os.path.join(django.conf.settings.MEDIA_ROOT, 'source_images', 'Italian', '120')
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
    menu_name = "Italian Premium Menu"
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
