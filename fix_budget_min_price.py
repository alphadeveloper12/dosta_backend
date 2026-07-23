import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import BudgetOption

def parse_price_range(range_str):
    # Regex to find numbers (including decimals)
    # Looks for simple numbers like 50, 50.00, or 70 in "70-135"
    numbers = re.findall(r"(\d+(?:\.\d{1,2})?)", str(range_str))
    if not numbers:
        return 0, 0
    
    # Convert matches to floats
    values = [float(n) for n in numbers]
    
    if len(values) == 1:
        # If only "120", then min=120, max=120
        return values[0], values[0]
    
    # If "70-135", min=70, max=135
    # Just in case they are reversed or unordered, sort them
    values.sort()
    return values[0], values[-1]

def fix_budget_min_prices():
    budgets = BudgetOption.objects.all()
    print(f"Checking {budgets.count()} budget options...")
    
    for b in budgets:
        old_min = b.min_price
        old_max = b.max_price
        
        parsed_min, parsed_max = parse_price_range(b.price_range)
        
        # Override min_price with parsed value
        # Optional: We could also update max_price if it was missing
        b.min_price = parsed_min
        
        # If max_price was 0 or incorrect, we could update it too, 
        # but let's focus on min_price for now as that's critical for the filter.
        if b.max_price == 0 and parsed_max > 0:
             b.max_price = parsed_max
             
        b.save()
        print(f"Updated '{b.label}': Range='{b.price_range}' -> Min={b.min_price} (was {old_min}), Max={b.max_price}")

if __name__ == "__main__":
    fix_budget_min_prices()
