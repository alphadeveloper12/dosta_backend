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
    print("Starting Asian Menu (120 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Asian")
    if created:
        print(f"Created Cuisine: {cuisine.name}")
        if not cuisine.image:
             cuisine.image = "menu_items/placeholder.svg"
             cuisine.save()
    else:
        print(f"Found Cuisine: {cuisine.name}")

    # 2. Setup Budget Option (120 AED)
    # Check for existing 120 AED budget regardless of label to avoid dupes
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
    # Map visual names to canonical DB names where possible
    # "MAIN COURSE" -> "Main Courses"
    # "DESSERT" -> "Desserts"
    
    menu_structure = {
        "Salads": [
            "Quinoa Avocado with Prawn",
            "Sprout Salad",
            "Thai Beef Papaya",
            "Selection of Salad Leaves",
            "Fresh Salad Bar"
        ],
        "Selection of International Bread": [
            # Using the course name as the item itself or just a course? 
            # The user listed "SELECTION OF INTERNATIONAL BREAD" as a section header but no items under it except empty space?
            # Or is it an item under Salads? 
            # In previous International menu it was items under Salads.
            # Here it looks like a separate section or item.
            # Let's treat "Selection of International Bread" as a Course with one item "Selection of International Bread" for safety.
            "Selection of International Bread" 
        ],
        "Soups": [
            "Seafood Tom Yum"
        ],
        "Under The Light": [
            "Stickey Chilli Chicken Wings"
        ],
        "Live Stations": [
            "Stir Fried Noodles & Rice",
            "Egg noodle, White Rice, mushroom, Pak choy, chili paste",
            "Condiments"
        ],
        "Main Courses": [ # Mapped from MAIN COURSE
            "Stir Fried Squid with Broccoli in Oyster Sauce",
            "Black Pepper Beef",
            "Kung Poa Chicken",
            "Chicken Ball Munchorian",
            "Jasmine Rice",
            "Malaysian Lamb",
            "Sweet and Sour Fish",
            "Teriyaki Glazed Baby Corn and Pak Choy"
        ],
        "Desserts": [ # Mapped from DESSERT
            "Rice Puddings",
            "Thai Coconut Fruit Salad",
            "Carrots Cake",
            "Fresh Fruits Cut"
        ],
        "Beverages": [
            "Soft Drinks / Water"
        ]
    }

    placeholder_image = "menu_items/placeholder.svg"

    all_courses = []
    all_items = []

    for course_name, item_names in menu_structure.items():
        # Get or Create Course - Handle duplicates by taking the first one
        # Try to find existing canonical first
        course = Course.objects.filter(name__iexact=course_name).first()
        if not course:
            # Special handling for plurals if needed, but here we used canonical keys in dict
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

        for item_name in item_names:
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
            
            # NEW: Image sourcing
            source_folder = os.path.join(django.conf.settings.MEDIA_ROOT, 'source_images', 'Asian', '1')
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

            all_items.append(item)

    # 4. Create FixedCateringMenu
    menu_name = "Asian Premium Menu"
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
