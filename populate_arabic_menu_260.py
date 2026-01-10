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
    # Remove things like (D), (G), (N), (D, N)
    # Match parens that contain only uppercase letters, commas, spaces, and dot, with length limit to avoid killing descriptions
    # e.g. (D) or (D, N) -> Matches. (Shish Tawook...) -> Should hopefully fail if strictly looking for allergen codes.
    # But user pattern is inconsistent.
    # Logic: Look for parens at the END of string usually, or specific tags.
    # Let's clean specific known tags.
    
    cleaned = re.sub(r'\([DGNV,.\s]+\)$', '', name.strip()) # Matches (D), (N), (G, N) at end
    cleaned = re.sub(r'\s*\(\.\.\.\)$', '', cleaned)
    
    # Also handle tags inside names if any, but usually they are at end.
    # For safety on "Arabic Mix Grill (Shish...)", that is a description, keep it.
    
    # Specific cleanups for this request:
    if "Mohalabieh" in name: return "Mohalabieh"
    if "Crème Caramel" in name: return "Crème Caramel"
    if "Fresh Fruit Cut" in name: return "Fresh Fruit Cut"
    if "Um Ali" in name: return "Um Ali"
    
    return cleaned.strip()

def populate():
    print("Starting Arabic Menu (260 AED) Population...")

    # 1. Setup Cuisine
    cuisine, created = Cuisine.objects.get_or_create(name="Arabic")
    if created:
        print(f"Created Cuisine: {cuisine.name}")
        if not cuisine.image:
             cuisine.image = "menu_items/placeholder.svg"
             cuisine.save()
    else:
        print(f"Found Cuisine: {cuisine.name}")

    # 2. Setup Budget Option (260 AED)
    budget = BudgetOption.objects.filter(price_range="260 AED").first()
    if not budget:
        budget = BudgetOption.objects.create(
            price_range="260 AED",
            label="Grand", # Maps to 260
            min_price=Decimal("260.00"),
            max_price=Decimal("260.00")
        )
        print(f"Created BudgetOption: {budget}")
    else:
        print(f"Found BudgetOption: {budget}")

    # 3. Define Courses and Items
    menu_structure = {
        "Salads": [
            "Hummus / Mutable / Mohammara",
            "Tabbouleh Salad",
            "Fattouch Salad",
            "Okra Bil Zait",
            "Fresh Salad Bar: Mix Lettuce, Tomato, Cucumber, Lemon, Green Chili, Red Onion, pickles, sauces",
            "Arabic bread Basket"
        ],
        "Soups": [
            "Lentil Soup with Condiments",
            "Lamb Harira Soup"
        ],
        "Starters": [
            "Lamb Kibbeh",
            "Cheese Roll"
        ],
        "Live Stations": [
            "Arabic Mix Grill (Shish Tawook, Lamb Kofta, Chicken Wings)"
        ],
        "Main Courses": [
            "Fish Filet with Harrah Sauce",
            "Roasted Chicken on Freekeh",
            "Kussa Bil Laban",
            "Dawod Basha",
            "Eggplant Moussaka",
            "Assorted Steamed Vegetables",
            "Roasted Potatoes with Sumac",
            "Vermicelli Rice"
        ],
        "Desserts": [
            "Mix Arabic Sweets",
            "Assorted French Sweet",
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
    menu_name = "Arabic Grand Menu"
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
