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
    print("Starting Italian Menu (140 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Italian")
    
    # 2. Setup Budget Option (140 AED)
    budget = BudgetOption.objects.filter(price_range="140 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="140 AED",
            label="Exclusive",
            min_price=Decimal("140.00"),
            max_price=Decimal("140.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    menu_structure = {
        "Salads & Antipasto": [
            ("Caesar Salad", "Crisp romaine lettuce with Caesar dressing, croutons, and parmesan."),
            ("Bruschetta Bar", "Toasted bread with toppings like tomato-basil, mushroom, and olive tapenade."),
            ("Mediterranean Chickpea Salad", "Chickpeas, cucumber, tomatoes, red onion, and feta cheese with lemon dressing."),
            ("Roasted Beet Salad", "Roasted beets with goat cheese, walnuts, and arugula."),
            ("Antipasto Platter", "A selection of cured meats, cheeses, marinated vegetables, and olives.")
        ],
        "Main Courses": [
            ("Lasagna Bolognese", "Layered pasta with rich meat sauce, béchamel, and mozzarella."),
            ("Seafood Linguine", "Linguine tossed with shrimp, mussels, and clams in a garlic white wine sauce."),
            ("Eggplant Parmesan", "Breaded and baked eggplant layered with marinara and mozzarella."),
            ("Risotto ai Funghi", "Creamy risotto with wild mushrooms and parmesan."),
            ("Grilled Chicken with Lemon and Herbs", "Marinated grilled chicken served with roasted vegetables."),
            ("Penne Alfredo", "Penne pasta in a creamy Alfredo sauce with parmesan cheese."),
            ("Italian Sausage and Peppers", "Grilled Italian sausages sautéed with bell peppers and onions.")
        ],
        "Desserts": [
            ("Tiramisu", "Classic Italian dessert with layers of coffee-soaked ladyfingers."),
            ("Panna Cotta", "Silky vanilla panna cotta served with berry compote."),
            ("Chocolate Cannoli", "Crispy pastry filled with sweet ricotta and chocolate chips."),
            ("Fresh Cut Fruit", "A selection of seasonal fresh fruits."),
            ("Lemon Tart", "Zesty lemon tart with a buttery crust, served with whipped cream."),
            ("Chocolate Mousse Cups", "Rich chocolate mousse served in individual cups.")
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
            source_folder = os.path.join(django.conf.settings.MEDIA_ROOT, 'source_images', 'Italian', '140')
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
    menu_name = "Italian Exclusive Menu"
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
