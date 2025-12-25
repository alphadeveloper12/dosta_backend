import os
import django
import json
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import VendingLocation, Menu, MenuItem, Order, OrderStatus, DayOfWeek

def verify_enhancements():
    print("Setting up test data...")
    User = get_user_model()
    user, _ = User.objects.get_or_create(username='kitchen_tester')
    location, _ = VendingLocation.objects.get_or_create(
        name="Test Loc",
        defaults={'info': "Info", 'latitude': 0.0, 'longitude': 0.0}
    )
    
    # Ensure at least one order exists
    order, _ = Order.objects.get_or_create(
        user=user,
        location=location,
        plan_type="ORDER_NOW",
        status=OrderStatus.PENDING,
        defaults={'total_amount': 15.00}
    )
    
    client = Client()
    
    # 1. Test API Endpoint
    print("Testing /kitchen/api/active-orders/...")
    response = client.get('/kitchen/api/active-orders/')
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✅ API returned 200 OK. Orders count: {len(data['orders'])}")
        found = any(o['id'] == order.id for o in data['orders'])
        if found:
            print("✅ ID found in API response")
        else:
            print("❌ ID NOT found in API response")
    else:
        print(f"❌ API failed: {response.status_code}")

    # 2. Test Dashboard UI
    print("Testing Dashboard UI...")
    response = client.get('/kitchen/')
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if "Kitchen Monitor" in content:
            print("✅ 'Kitchen Monitor' title found (Modern UI)")
        else:
             print("❌ 'Kitchen Monitor' title NOT found")
        
        if "notificationSound" in content:
            print("✅ Notification Audio element found")
        else:
            print("❌ Notification Audio element NOT found")
    else:
        print(f"❌ Dashboard failed: {response.status_code}")

    # 3. Test Menu Upload
    print("Testing Menu Upload...")
    try:
        # Create staff user for upload
        admin_user, _ = User.objects.get_or_create(username='admin_tester', is_staff=True)
        admin_user.set_password('password')
        admin_user.save()
        client.force_login(admin_user)

        with open('weekly_menu_sample.csv', 'rb') as fp:
            response = client.post('/kitchen/menu-upload/', {'menu_file': fp}, follow=True)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if "Menu uploaded successfully via CSV!" in content:
                print("✅ Success message found in response.")
            else:
                print("❌ Success message NOT found. We might be on the login page or error page.")
                print(f"DEBUG: Redirect chain: {response.redirect_chain}")
            
            # Verify DB
            item = MenuItem.objects.filter(name="Chicken Caesar Salad").first()
            if item and item.calories == 478 and item.protein == 36.0:
                 print(f"✅ Verified item '{item.name}' created with Cals:{item.calories}, Prot:{item.protein}g")
                 if item.image:
                     print(f"✅ Image downloaded: {item.image.name}")
                 else:
                     print("❌ Image NOT downloaded.")
            else:
                 if item:
                     print(f"❌ Item mismatched. Found: Name={item.name}, Cal={item.calories} (Expected 478), Prot={item.protein} (Expected 36.0)")
                 else:
                     print("❌ Item not found in DB.")
                 print(f"DEBUG: All MenuItems: {list(MenuItem.objects.values('name', 'calories', 'protein'))}")
        else:
             print(f"❌ Upload failed with status: {response.status_code}")
             
    except Exception as e:
        print(f"❌ Exception during upload test: {e}")

if __name__ == '__main__':
    verify_enhancements()
