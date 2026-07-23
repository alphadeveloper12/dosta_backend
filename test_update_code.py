import requests

url = "http://localhost:8000/api/vending/order/update-pickup-code/"
# Need a token. I'll try to get one from the database for the user of order 151.
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()
from vending.models import Order
from rest_framework.authtoken.models import Token

order = Order.objects.get(id=151)
user = order.user
token, _ = Token.objects.get_or_create(user=user)

headers = {"Authorization": f"Token {token.key}"}
data = {"order_id": 151, "pickup_code": "485450"}

response = requests.post(url, json=data, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
