import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dosta.settings")
django.setup()

from vending.models import Order, Cart

def delete_all_data():
    print("Starting deletion process...")

    # Delete Orders
    order_count = Order.objects.count()
    print(f"Found {order_count} Orders. Deleting...")
    Order.objects.all().delete()
    print("All Orders deleted.")

    # Delete Carts
    cart_count = Cart.objects.count()
    print(f"Found {cart_count} Carts. Deleting...")
    Cart.objects.all().delete()
    print("All Carts deleted.")

    print("Deletion process completed successfully.")

if __name__ == "__main__":
    delete_all_data()
