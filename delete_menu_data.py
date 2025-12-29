import os
import django
from django.db.models import ProtectedError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import Menu, MenuItem, OrderItem, CartItem, MealPlanItem, Offer

def delete_menus():
    print("Checking for existing data...")
    menus_count = Menu.objects.count()
    menu_items_count = MenuItem.objects.count()
    order_items_count = OrderItem.objects.count()
    cart_items_count = CartItem.objects.count()
    meal_plan_items_count = MealPlanItem.objects.count()
    offers_count = Offer.objects.count()

    print(f"Menus: {menus_count}")
    print(f"Menu Items: {menu_items_count}")
    print(f"Order Items: {order_items_count}")
    print(f"Cart Items: {cart_items_count}")
    print(f"Meal Plan Items: {meal_plan_items_count}")
    print(f"Offers: {offers_count}")

    if menus_count == 0 and menu_items_count == 0:
        print("No menu data found to delete.")
        return

    # Delete dependent data first
    try:
        if order_items_count > 0:
            print(f"Deleting {order_items_count} OrderItems...")
            OrderItem.objects.all().delete()
        
        if cart_items_count > 0:
            print(f"Deleting {cart_items_count} CartItems...")
            CartItem.objects.all().delete()

        if meal_plan_items_count > 0:
            print(f"Deleting {meal_plan_items_count} MealPlanItems...")
            MealPlanItem.objects.all().delete()

        # Deleting Menus
        deleted_count, _ = Menu.objects.all().delete()
        print(f"Successfully deleted {deleted_count} Menu items (including cascaded MenuItems and Offers).")
        
        # Check if any MenuItems remain
        remaining_items = MenuItem.objects.count()
        if remaining_items > 0:
             deleted_items, _ = MenuItem.objects.all().delete()
             print(f"Deleted {deleted_items} orphaned MenuItems.")

        print("\nAll menu data deleted successfully.")

    except ProtectedError as e:
        print(f"\nError: Could not delete data due to protected references: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == '__main__':
    delete_menus()
