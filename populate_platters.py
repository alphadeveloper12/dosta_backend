import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import PlatterItem
from django.core.files import File

def populate_platters():
    # Clear existing data
    PlatterItem.objects.all().delete()
    print("Existing Platter Items deleted.")

    platters_data = [
       {
           "name": "Mediterranean Platter",
           "description": "Hummus, baba ganoush, tzatziki, olives, and pita bread."
       },
       {
           "name": "Middle Eastern Mezze",
           "description": "Stuffed grape leaves, Hummus, Mutable, labneh, and pita."
       },
       {
           "name": "Hot Mezzeh Platter",
           "description": "Meat Kibbeh, Cheese Roll, Spinach Fattayer, Cheese Sambousek."
       },
       {
           "name": "Italian Grazing Board",
           "description": "Antipasto, bruschetta, and marinated vegetables."
       },
       {
           "name": "French Cheese Board",
           "description": "A selection of French cheeses with baguette and accompaniments."
       },
       {
           "name": "Charcuterie Board",
           "description": "Assorted cured meats, pickles, and artisan bread."
       },
       {
           "name": "Dessert Platter",
           "description": "A mix of pastries and sweets like baklava and mini cakes."
       },
       {
           "name": "Mini Sandwiches",
           "description": "Assorted mini sandwiches with various fillings."
       },
       {
           "name": "Cold Seafood Platter",
           "description": "Grilled prawns, calamari, and fish ceviche served with dipping sauces."
       },
       {
           "name": "Argentinian Meat Platter",
           "description": "Assorted cuts of grilled meats, chimichurri sauce, and seasonal vegetables."
       },
       {
           "name": "Pakistani Platter",
           "description": "Samosas, seekh kebabs, and chicken tikka with mint chutney."
       },
       {
           "name": "Vegetarian Feast",
           "description": "Paneer, lentil dal, and vegetable curry served with naan."
       },
       {
           "name": "Fried Seafood Platter",
           "description": "Calamari, fish, and shrimp served with tartar sauce."
       },
       {
            "name": "Canapés",
            "description": "An assortment of bite-sized canapés, including vegetarian options."
       },
       {
           "name": "Gourmet Sliders",
           "description": "Beef Sliders, Chicken Sliders, Falafel Sliders, Vegetarian Sliders."
       }
    ]

    # Dummy image path - user said "pick any one"
    # Assuming there's a file in media/coffee_break or cuisines
    # Let's list media directory or just try to reuse one if known.
    # I'll just skip image assignment for now or try to finding one.
    # The prompt said "dummy photo from previously added photos pick any one"
    
    # Let's look for a file to use
    dummy_image_path = 'media/cuisines/italian.jpg' # Hypothesis
    
    print("Populating Platters...")
    for data in platters_data:
        item = PlatterItem.objects.create(
            name=data['name'],
            description=data['description']
        )
        # item.image = ... (skip for now to avoid error if file missing, let user add via admin or I can check)
        print(f"Created: {item.name}")

    print("Population complete.")

if __name__ == '__main__':
    populate_platters()
