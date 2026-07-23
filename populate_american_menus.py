import sys
import os
import django

# Add current directory to path so 'dosta' package is resolvable
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import AmericanMenu, AmericanMenuItem

MENUS = [
    {
        "name": "Buffet Menu 1: Southern Comfort",
        "items": [
            {"category": "Starters", "name": "Fried Green Tomatoes", "description": "Served with a zesty remoulade."},
            {"category": "Starters", "name": "Shrimp Cocktail", "description": "Chilled shrimp with cocktail sauce."},
            {"category": "Salads", "name": "Southern Potato Salad", "description": "Creamy dressing with mustard and hard-boiled eggs."},
            {"category": "Salads", "name": "Chickpea Salad", "description": "Tossed with red onions, tomatoes, and herbs."},
            {"category": "Main Dishes", "name": "Chicken Fried Steak", "description": "Breaded and fried, served with gravy."},
            {"category": "Main Dishes", "name": "Pulled Beef BBQ", "description": "Tender beef served with slider buns."},
            {"category": "Sides", "name": "Collard Greens", "description": "Slow-cooked with olive oil."},
            {"category": "Sides", "name": "Biscuit Basket", "description": "Fluffy biscuits with honey butter."},
            {"category": "Sides", "name": "Cornbread", "description": "Sweet Southern cornbread."},
            {"category": "Desserts", "name": "Pecan Pie", "description": "Rich pie with a buttery crust."},
            {"category": "Desserts", "name": "Banana Pudding", "description": "Layers of bananas, pudding, and vanilla wafers."},
        ]
    },
    {
        "name": "Buffet Menu 2: Diner Delights",
        "items": [
            {"category": "Starters", "name": "Onion Rings", "description": "Crispy and golden, served with dipping sauce."},
            {"category": "Starters", "name": "Deviled Eggs", "description": "Classic recipe garnished with paprika."},
            {"category": "Salads", "name": "Tossed Garden Salad", "description": "Mixed greens, cucumbers, and cherry tomatoes."},
            {"category": "Salads", "name": "Cauliflower Salad", "description": "Dressed with a tangy mustard vinaigrette."},
            {"category": "Main Dishes", "name": "Homestyle Meatloaf", "description": "Served with a savory glaze."},
            {"category": "Main Dishes", "name": "Grilled Cheese Sandwiches", "description": "Classic American grilled cheese cut into triangles."},
            {"category": "Sides", "name": "French Fries", "description": "Crispy fries with various seasonings."},
            {"category": "Sides", "name": "Steamed Broccoli", "description": "Seasoned with lemon zest."},
            {"category": "Desserts", "name": "Milkshakes", "description": "Vanilla, chocolate, and strawberry options."},
            {"category": "Desserts", "name": "Brownie Sundaes", "description": "Topped with chocolate sauce."},
        ]
    },
    {
        "name": "Buffet Menu 3: Grill Out",
        "items": [
            {"category": "Starters", "name": "Fresh Veggie Platter", "description": "Assortment of seasonal vegetables with dip."},
            {"category": "Starters", "name": "Stuffed Jalapeños", "description": "Jalapeños filled with cheese and baked."},
            {"category": "Salads", "name": "Coleslaw", "description": "Creamy dressing with shredded cabbage."},
            {"category": "Salads", "name": "Greek Salad", "description": "Feta, olives, and cucumbers dressed in olive oil and vinegar."},
            {"category": "Main Dishes", "name": "Grilled Burgers", "description": "Customizable with toppings."},
            {"category": "Main Dishes", "name": "BBQ Grilled Chicken", "description": "Marinated and grilled to perfection."},
            {"category": "Sides", "name": "Potato Wedges", "description": "Seasoned and served warm."},
            {"category": "Sides", "name": "Corn Salad", "description": "Fresh corn with peppers and lime dressing."},
            {"category": "Desserts", "name": "S'mores Bar", "description": "Graham crackers, chocolate, and marshmallows."},
            {"category": "Desserts", "name": "Apple Crisp", "description": "Served warm with whipped cream."},
        ]
    },
    {
        "name": "Buffet Menu 4: Classic American Feast",
        "items": [
            {"category": "Starters", "name": "Meat and Cheese Platter", "description": "Assorted cured meats and cheeses."},
            {"category": "Starters", "name": "Spinach Dip", "description": "Served with chips and bread."},
            {"category": "Salads", "name": "Caesar Salad", "description": "Crisp Romaine lettuce with Caesar dressing."},
            {"category": "Salads", "name": "Quinoa Salad", "description": "Light and refreshing with veggies and lemon dressing."},
            {"category": "Main Dishes", "name": "Baked Ziti", "description": "Pasta with marinara and melted cheese."},
            {"category": "Main Dishes", "name": "Roasted Chicken", "description": "Herb-seasoned and served with gravy."},
            {"category": "Sides", "name": "Wild Rice Pilaf", "description": "Flavored with herbs and spices."},
            {"category": "Sides", "name": "Green Beans Almondine", "description": "Fresh green beans with toasted almonds."},
            {"category": "Desserts", "name": "Brownie Bites", "description": "Chocolatey treats cut into bite-sized pieces."},
            {"category": "Desserts", "name": "Carrot Cake", "description": "Moist cake topped with cream cheese frosting."},
        ]
    },
    {
        "name": "Buffet Menu 5: Coastal Classics",
        "items": [
            {"category": "Starters", "name": "Clam Chowder", "description": "Creamy soup with clams and potatoes."},
            {"category": "Starters", "name": "Fish Tacos", "description": "Served with cabbage slaw."},
            {"category": "Salads", "name": "Greek Pasta Salad", "description": "Pasta with olives, tomatoes, and feta cheese."},
            {"category": "Salads", "name": "Caprese Salad", "description": "Fresh mozzarella, tomatoes, and basil."},
            {"category": "Main Dishes", "name": "Baked Salmon", "description": "Lemony and herb-seasoned."},
            {"category": "Main Dishes", "name": "Fried Shrimp", "description": "Golden and crispy, served with cocktail sauce."},
            {"category": "Sides", "name": "Coconut Rice", "description": "Fluffy rice infused with coconut milk."},
            {"category": "Sides", "name": "Steamed Asparagus", "description": "Lightly seasoned."},
            {"category": "Desserts", "name": "Key Lime Pie", "description": "Tangy pie with a graham cracker crust."},
            {"category": "Desserts", "name": "Pineapple Upside-Down Cake", "description": "Served warm with vanilla ice cream."},
        ]
    }
]

def populate():
    # Clear existing
    AmericanMenu.objects.all().delete()
    print("Cleared existing American Menus.")

    base_image_path = os.path.join(django.conf.settings.MEDIA_ROOT, 'source_images', 'american')

    for index, menu_data in enumerate(MENUS):
        menu_number = index + 1
        menu = AmericanMenu.objects.create(name=menu_data["name"])
        print(f"Created Menu: {menu.name}")
        
        menu_image_folder = os.path.join(base_image_path, str(menu_number))
        
        for item_data in menu_data["items"]:
            item = AmericanMenuItem.objects.create(
                menu=menu,
                name=item_data["name"],
                description=item_data["description"],
                category=item_data["category"]
            )

            # Try to find image
            if os.path.exists(menu_image_folder):
                # Search for file with case-insensitive match
                found_image = None
                target_name = item_data["name"].lower().replace(" ", "") # Remove spaces for looser matching if needed, or just lower
                
                # Let's try exact name first, then different variations
                # Get all files in the folder
                try:
                    files = os.listdir(menu_image_folder)
                    for filename in files:
                        name_without_ext = os.path.splitext(filename)[0].lower()
                        # Normalize item name for comparison
                        item_name_norm = item_data["name"].lower()
                        
                        # Check logic: Exact match or simple variations
                        if name_without_ext == item_name_norm:
                            found_image = filename
                            break
                        # Fallback: check if item name is in filename
                        if item_name_norm in name_without_ext:
                            found_image = filename
                            # Don't break yet, keep looking for exact match? 
                            # Actually, first match is probably fine for now.
                            break
                            
                    if found_image:
                        source_path = os.path.join(menu_image_folder, found_image)
                        with open(source_path, 'rb') as f:
                            from django.core.files import File
                            item.image.save(found_image, File(f), save=True)
                            print(f"  Attached image to: {item.name}")
                    else:
                        print(f"  No image found for: {item.name} in {menu_image_folder}")

                except Exception as e:
                    print(f"  Error accessing folder {menu_image_folder}: {e}")
            else:
                print(f"  Image folder not found: {menu_image_folder}")

    print("Done!")

if __name__ == "__main__":
    populate()
