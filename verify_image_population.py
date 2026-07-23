import os
import django
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import MenuItem, CanapeItem, Cuisine

def verify():
    print("--- Verification Report ---")
    
    # 1. African
    african_cuisine = Cuisine.objects.filter(name__icontains="African").first()
    if african_cuisine:
        total = MenuItem.objects.filter(cuisine=african_cuisine).count()
        with_image = MenuItem.objects.filter(cuisine=african_cuisine).exclude(image='').count()
        print(f"African Menu: {with_image}/{total} items have images.")
    else:
        print("African Cuisine not found in DB.")

    # 2. Turkish
    turkish_cuisine = Cuisine.objects.filter(name__icontains="Turkish").first()
    if turkish_cuisine:
        total = MenuItem.objects.filter(cuisine=turkish_cuisine).count()
        with_image = MenuItem.objects.filter(cuisine=turkish_cuisine).exclude(image='').count()
        print(f"Turkish Menu: {with_image}/{total} items have images.")
    else:
        print("Turkish Cuisine not found in DB.")

    # 3. Canapes
    # Categories
    categories = [
        'Cold', 'Hot', 'Arabic', 'Sweet', 'Vegetarian', 'Cold Beverages', 'Hot Beverages'
    ]
    
    print("\n--- Canapes ---")
    for cat in categories:
        total = CanapeItem.objects.filter(category__icontains=cat).count()
        with_image = CanapeItem.objects.filter(category__icontains=cat).exclude(image='').count()
        print(f"  {cat}: {with_image}/{total} items have images.")

if __name__ == "__main__":
    verify()
