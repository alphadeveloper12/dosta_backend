import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import LiveStationItem
from decimal import Decimal

def populate_live_stations():
    # Clear existing data
    LiveStationItem.objects.all().delete()
    print("Existing Live Station Items deleted.")

    live_stations_data = [
        {
            "name": "Sushi Station",
            "price": 135,
            "setup": "A chef prepares sushi on-site, allowing guests to choose their fillings.",
            "ingredients": "Various types of fish, vegetables, rice, and seaweed."
        },
        {
            "name": "Pasta Bar",
            "price": 120,
            "setup": "Guests select from different types of pasta and sauces.",
            "ingredients": "A variety of pastas, sauces (like marinara, Alfredo), and toppings."
        },
        {
            "name": "Taco Station",
            "price": 125,
            "setup": "Guests build their own tacos with various fillings.",
            "ingredients": "Tortillas, meats (chicken, beef, vegetarian), toppings (salsa, guacamole, cheese)."
        },
        {
            "name": "Carving Station",
            "price": 165,
            "setup": "A chef carves meats like roast beef or turkey for guests.",
            "ingredients": "A selection of meats, sauces, and sides."
        },
        {
            "name": "Dessert Station",
            "price": 135,
            "setup": "Guests can create their own desserts, like sundaes or cupcakes.",
            "ingredients": "Ice cream, toppings, and baked goods."
        },
        {
            "name": "Grilled Cheese Station",
            "price": 145,
            "setup": "Guests choose from various breads and cheeses, with optional add-ins.",
            "ingredients": "Different types of bread, cheeses, and toppings like tomatoes, bacon, or avocado."
        },
        {
            "name": "Salad Bar",
            "price": 120,
            "setup": "A variety of greens and toppings for guests to customize their salads.",
            "ingredients": "Mixed greens, vegetables, proteins (chicken, tofu), nuts, and dressings."
        },
        {
            "name": "Dim Sum Station",
            "price": 145,
            "setup": "A chef prepares and serves various dim sum dishes.",
            "ingredients": "Dumplings, buns, and spring rolls, with dipping sauces."
        },
        {
            "name": "Crepe Station",
            "price": 120,
            "setup": "Freshly made crepes filled with sweet or savory ingredients.",
            "ingredients": "Batter, fillings like Nutella, fruits, ham, and cheese."
        },
        {
            "name": "Beverage Station",
            "price": 120,
            "setup": "Guests mix their own drinks or choose from a selection.",
            "ingredients": "A variety of spirits, mixers, garnishes, and non-alcoholic options."
        },
        {
            "name": "BBQ Station",
            "price": 165,
            "setup": "Grilled meats and vegetables prepared on-site.",
            "ingredients": "Ribs, chicken, seasonal veggies, and BBQ sauces."
        },
        {
            "name": "Popcorn Bar",
            "price": 120,
            "setup": "Guests can customize their popcorn with various seasonings.",
            "ingredients": "Plain popcorn, toppings like cheese, caramel, and spices."
        },
        {
            "name": "Bagel Station",
            "price": 125,
            "setup": "Guests choose from different types of bagels and spreads.",
            "ingredients": "Different types of bread and spreads." 
        }
    ]
    
    print("Populating Live Stations...")
    for data in live_stations_data:
        item = LiveStationItem.objects.create(
            name=data['name'],
            price=Decimal(data['price']),
            setup=data['setup'],
            ingredients=data['ingredients']
        )
        print(f"Created: {item.name}")

    print("Population complete.")

if __name__ == '__main__':
    populate_live_stations()
