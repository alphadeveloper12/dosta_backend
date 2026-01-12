import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import Order, OrderItem, VendingMachineStock, OrderStatus, MenuItem, Menu, DayOfWeek, VendingLocation
from django.contrib.auth.models import User

def test_stock_decrement():
    # 1. Setup
    user, _ = User.objects.get_or_create(username='testuser', email='test@example.com')
    location, _ = VendingLocation.objects.get_or_create(name='Test Location', latitude=0, longitude=0)
    menu, _ = Menu.objects.get_or_create(day_of_week=DayOfWeek.MONDAY, week_number=1)
    menu_item, _ = MenuItem.objects.get_or_create(menu=menu, name='Test Item', price=10)
    
    # Create stock
    vending_uuid = "1064053" # Butter Chicken from user example
    stock, _ = VendingMachineStock.objects.get_or_create(
        vending_good_uuid=vending_uuid,
        defaults={'goods_name': 'Butter Chicken*', 'quantity': 10}
    )
    stock.quantity = 10
    stock.save()
    
    print(f"Initial stock for {stock.goods_name}: {stock.quantity}")
    
    # Create order
    order = Order.objects.create(
        user=user,
        location=location,
        plan_type='ORDER_NOW',
        status=OrderStatus.PENDING
    )
    
    OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=2,
        vending_good_uuid=vending_uuid
    )
    
    # 2. Trigger UpdatePickupCodeView logic (simulated)
    from vending.views import UpdatePickupCodeView
    from rest_framework.test import APIRequestFactory, force_authenticate
    
    factory = APIRequestFactory()
    request = factory.post('/api/vending/order/update-pickup-code/', {
        'order_id': order.id,
        'pickup_code': 'TEST-CODE'
    })
    force_authenticate(request, user=user)
    
    view = UpdatePickupCodeView.as_view()
    response = view(request)
    
    print(f"Response status: {response.status_code}")
    
    # 3. Verify
    stock.refresh_from_db()
    print(f"Final stock for {stock.goods_name}: {stock.quantity}")
    
    if stock.quantity == 8:
        print("SUCCESS: Stock decremented correctly.")
    else:
        print(f"FAILURE: Stock is {stock.quantity}, expected 8.")

if __name__ == "__main__":
    test_stock_decrement()
