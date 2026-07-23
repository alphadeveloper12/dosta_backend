import os
import django
from django.db.models import Min, Max

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Cuisine

def migrate_prices_to_cuisine():
    cuisines = Cuisine.objects.all()
    print(f"Checking {cuisines.count()} cuisines...")
    
    for c in cuisines:
        # Get all linked budget options
        budgets = c.budget_options.all()
        
        if budgets.exists():
            # Calculate min and max from linked budgets
            # We want the lowest min_price and highest max_price to cover the full range
            aggregated = budgets.aggregate(
                lowest_min=Min('min_price'),
                highest_max=Max('max_price')
            )
            
            new_min = aggregated['lowest_min']
            new_max = aggregated['highest_max']
            
            if new_min is not None:
                c.min_price = new_min
            if new_max is not None:
                c.max_price = new_max
                
            c.save()
            print(f"Updated '{c.name}': Min={c.min_price}, Max={c.max_price} (Derived from {budgets.count()} budgets)")
        else:
            print(f"Skipped '{c.name}': No linked budget options.")

if __name__ == "__main__":
    migrate_prices_to_cuisine()
