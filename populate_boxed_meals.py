import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import BoxedMealItem
from django.core.files import File

def populate_boxed_meals():
    # Clear existing data
    BoxedMealItem.objects.all().delete()
    print("Existing Boxed Meal Items deleted.")

    boxed_meals_data = [
       {"name": "Greek", "category": "Salads"},
       {"name": "Fattouch", "category": "Salads"},
       
       {"name": "Lentil", "category": "Soup"},
       {"name": "Cream of Mushroom", "category": "Soup"},
       
       {"name": "Kofta Bil Saynieh with Rice", "category": "Mains"},
       {"name": "Chicken Makloubieh with Rice", "category": "Mains"},
       {"name": "Fish Sayadieh with Rice", "category": "Mains"},
       {"name": "Lamb Biryani + Ritha", "category": "Mains"},
       {"name": "Jordanian Mansaf", "category": "Mains"},
       {"name": "Chicken Mandi", "category": "Mains"},
       {"name": "Butter Chicken + White Rice", "category": "Mains"},
       {"name": "Chicken Biryani + Ritha", "category": "Mains"},
       {"name": "Lamb Okra + Rice", "category": "Mains"},
       {"name": "Dawood Basha + Rice", "category": "Mains"},
       {"name": "Chicken with Potato + Rice", "category": "Mains"},
       {"name": "Chicken Adobo + Rice", "category": "Mains"},
       
       {"name": "Soft Drink", "category": "Soft Drink"},
    ]
    
    print("Populating Boxed Meals...")
    for data in boxed_meals_data:
        item = BoxedMealItem.objects.create(
            name=data['name'],
            category=data['category']
        )
        print(f"Created: {item.name} ({item.category})")

    print("Population complete.")

if __name__ == '__main__':
    populate_boxed_meals()
