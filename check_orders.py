import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import Order

orders = Order.objects.all().order_by('-id')[:5]
for order in orders:
    print(f"Order ID: {order.id}")
    print(f"  Pickup Code: {order.pickup_code}")
    print(f"  QR Code URL: {order.qr_code_url}")
    print(f"  Status: {order.status}")
    print("-" * 20)
