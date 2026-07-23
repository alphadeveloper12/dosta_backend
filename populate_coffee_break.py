import os
import sys
import django

# Add the project directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dosta.settings")
django.setup()

from catering.models import CoffeeBreakRotation, CoffeeBreakItem

coffee_break_rotations = [
  {
    "id": 1,
    "name": "Rotation 1",
    "categories": [
      {
        "category": "Salads",
        "items": ["Mini Tabbouleh", "Mini Russian Salad", "Mini Beetroot Salad"]
      },
      {
        "category": "Cold Appetizers",
        "items": ["Mini Hummus", "Mini Muhammara", "Stuffed Vine Leaves"]
      },
      {
        "category": "Hot Appetizers",
        "items": ["Kibbeh", "Cheese Roll", "Sujuk"]
      },
      {
        "category": "Sandwiches",
        "items": [
          "Mini Chicken Shawarma Sandwich",
          "Mini Halloumi Pesto Sandwich",
          "Mini Turkey Ham Sandwich"
        ]
      },
      {
        "category": "Desserts",
        "items": ["Walnut Mamoul", "Basbousa", "Carrot Cake"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Lemon & Mint Juice", "Orange Juice", "Water"]
      }
    ]
  },
  {
    "id": 2,
    "name": "Rotation 2",
    "categories": [
      {
        "category": "Cold Appetizers",
        "items": ["Mini Baba Ganoush", "Mini Muhammara", "Stuffed Vine Leaves"]
      },
      {
        "category": "Salads",
        "items": ["Mini Fattoush", "Mini Greek Salad", "Mini Mixed Green Salad"]
      },
      {
        "category": "Hot Appetizers",
        "items": [
          "Sambousek",
          "Esh El Bulbul",
          "Hot Dog Sausages",
          "Spinach Fatayer"
        ]
      },
      {
        "category": "Sandwiches",
        "items": [
          "Mini Fajita Chicken Sandwich",
          "Mini Falafel Sandwich",
          "Mini Shish Tawook Sandwich"
        ]
      },
      {
        "category": "Desserts",
        "items": ["Date Mamoul", "Cookies", "Cheesecake", "Black Forest Cake"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Watermelon Juice", "Strawberry Juice", "Water"]
      }
    ]
  },
  {
    "id": 3,
    "name": "Rotation 3",
    "categories": [
      {
        "category": "Salads",
        "items": [
          "Potato & Tahini Salad",
          "Rocca Salad",
          "Fattoush Salad with Zaatar",
          "Quinoa and Black Bean Bowl"
        ]
      },
      {
        "category": "Appetizers & Sides",
        "items": [
          "Hummus",
          "Stuffed Vine Leaves",
          "Spring Roll",
          "Sautéed Tomatoes with Herbs"
        ]
      },
      {
        "category": "Main Dishes",
        "items": ["Chicken Teriyaki Skewers", "Lentil Kabab"]
      },
      {
        "category": "Sandwiches",
        "items": ["Labneh Sandwich"]
      },
      {
        "category": "Desserts & Snacks",
        "items": ["Vegan Basbousa", "Chia Pudding", "Oats and Berries"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Lemon & Mint Juice", "Orange Juice", "Water"]
      }
    ]
  },
  {
    "id": 4,
    "name": "Rotation 4",
    "categories": [
      {
        "category": "Salads",
        "items": [
          "White Beans and Parsley Salad",
          "Eggplant Salad",
          "Mediterranean Chickpea Salad",
          "Whole Grain Couscous with Dried Fruits"
        ]
      },
      {
        "category": "Appetizers & Sides",
        "items": ["Hummus", "Edamame", "Vegan Kibbeh"]
      },
      {
        "category": "Main Dishes",
        "items": ["Chicken Teriyaki Skewers", "Spring Roll"]
      },
      {
        "category": "Sandwiches",
        "items": ["Vegan Burger Sandwich"]
      },
      {
        "category": "Desserts & Snacks",
        "items": ["Vegan Mamoul", "Vegan Mohalabiya", "Chia Pudding"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Watermelon Juice", "Strawberry Juice", "Water"]
      }
    ]
  },
  {
    "id": 5,
    "name": "Rotation 5",
    "categories": [
      {
        "category": "Salads",
        "items": [
          "Beetroot Salad",
          "Green Salad",
          "Oriental salad",
          "Couscous salad"
        ]
      },
      {
        "category": "Appetizers & Sides",
        "items": ["Hummus avocado", "Moutabel"]
      },
      {
        "category": "Sandwiches",
        "items": [
          "Mini chicken mortadella",
          "Mini turkey hum",
          "Mini beef shawarma",
          "Mini Dynamite shrimp sandwich"
        ]
      },
      {
        "category": "Hot Appetizers",
        "items": ["Chicken Teriyaki Skewers", "Spring Roll", "Vegan Kibbeh"]
      },
      {
        "category": "Desserts",
        "items": ["Rice pudding", "Warbat qishta", "Mushabak"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Lemonade Juice", "Orange Juice", "Water"]
      }
    ]
  },
  {
    "id": 6,
    "name": "Rotation 6",
    "categories": [
      {
        "category": "Salads",
        "items": [
          "Greek Salad",
          "Chicken Caesar Salad",
          "Watermelon and feta salad",
          "Soban salad"
        ]
      },
      {
        "category": "Appetizers & Sides",
        "items": ["Hummus", "Labnah zater"]
      },
      {
        "category": "Sandwiches",
        "items": [
          "Mini smoke salmon",
          "Mini vegtabel",
          "Mini pepperoni",
          "Mini Dynamite shrimp sandwich"
        ]
      },
      {
        "category": "Hot Appetizers",
        "items": ["Chicken shish tawok Skewers", "Veg samosa", "Fraed Kibbeh"]
      },
      {
        "category: ": "Desserts",
        "items": ["Mohalabiya", "Opera cake", "Red velvet cake"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Lemonada Juice", "Orange Juice", "Water"]
      }
    ]
  },
  {
    "id": 7,
    "name": "Rotation 7",
    "categories": [
      {
        "category": "Salads",
        "items": [
          "Rocca Salad",
          "Mini Mixed Green Salad",
          "Mini Tabbouleh",
          "Armania salad"
        ]
      },
      {
        "category": "Appetizers & Sides",
        "items": ["Hummus", "Baba ganosh", "Labnah mint"]
      },
      {
        "category": "Sandwiches",
        "items": [
          "Mini chicken mayo",
          "Mini veg tacos",
          "Mini fish and chips sandwich",
          "Mini philadelphia beef sandwich"
        ]
      },
      {
        "category": "Hot Appetizers",
        "items": ["Esh El Bulbul", "Chees samosa", "Fraed Kibbeh"]
      },
      {
        "category": "Desserts",
        "items": ["Date Mamoul", "Carrot cake", "Éclair chocolate"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Lemonada Juice", "Orange Juice", "Water"]
      }
    ]
  },
  {
    "id": 8,
    "name": "Rotation 8",
    "categories": [
      {
        "category": "Salads",
        "items": ["Nicois Salad", "Shrimp caesar Salad", "Gawrda salad"]
      },
      {
        "category": "Appetizers & Sides",
        "items": ["Hummus", "Moutabel", "Olaiv salad"]
      },
      {
        "category": "Sandwiches",
        "items": [
          "Mini Turkey Ham Sandwich",
          "Mini Falafel Sandwich",
          "Mini halum sandwich"
        ]
      },
      {
        "category": "Hot Appetizers",
        "items": ["Chicken samosa", "Chees roll", "Fraed Kibbeh"]
      },
      {
        "category": "Desserts",
        "items": ["Finger pistachio", "Crème caramel", "Brownie"]
      },
      {
        "category": "Hot & Cold Beverages Station",
        "items": ["Tea & Coffee Station"]
      },
      {
        "category": "Fresh Juices",
        "items": ["Lemonada Juice", "Orange Juice", "Water"]
      }
    ]
  }
]

print("Starting Population...")

# Clear existing ? Optional. Let's assume clear.
CoffeeBreakRotation.objects.all().delete()
CoffeeBreakItem.objects.all().delete()

for rot_data in coffee_break_rotations:
    rotation = CoffeeBreakRotation.objects.create(name=rot_data['name'])
    print(f"Created {rotation.name}")
    
    for cat_data in rot_data['categories']:
        # Fix for typo in 'category: ' in source if any
        category = cat_data.get('category') or cat_data.get('category: ')
        if not category: continue

        for item_name in cat_data['items']:
            CoffeeBreakItem.objects.create(
                rotation=rotation,
                name=item_name,
                category=category
            )

print("Done!")
