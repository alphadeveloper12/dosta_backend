
import os
import django
import sys

sys.path.append(r'c:\Users\User\Desktop\main\dosta_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import BudgetOption, Cuisine, ServiceStyle

def verify_filter():
    print("Verifying Budget Filter Logic...")
    
    # 1. Get all budgets
    all_budgets = BudgetOption.objects.all()
    print(f"Total Budgets: {all_budgets.count()}")
    
    # 2. Simulate Service Style Filter (e.g., Buffet)
    # Finding Buffet style
    buffet = ServiceStyle.objects.filter(name__icontains='buffet').first()
    if not buffet:
        print("Buffet service style not found.")
        return

    print(f"Service Style: {buffet.name} (ID: {buffet.id})")
    
    # Filter by service style (assuming corporate/not private for simplicity, or check both)
    # The view does: filter(service_styles__id=...)
    filtered_by_style = all_budgets.filter(service_styles__id=buffet.id)
    print(f"Budgets after Service Style Filter: {filtered_by_style.count()}")
    
    # 3. Simulate Cuisine Filter
    # Let's find 'Asian' or any cuisine with links
    cuisines = Cuisine.objects.all()
    for c in cuisines:
        if c.budget_options.exists():
            print(f"\nTesting Cuisine: {c.name} (ID: {c.id})")
            ids = [c.id]
            # THE EXACT LINE FROM views.py
            final_result = filtered_by_style.filter(cuisines__id__in=ids).distinct()
            
            print(f"  - Linked Budgets count: {final_result.count()}")
            for b in final_result:
                print(f"    - {b.label} (ID: {b.id})")
                
            # Verification
            linked_count = c.budget_options.count()
            print(f"  - Actual M2M count on Cuisine model: {linked_count}")
            
            if final_result.count() != linked_count:
                print("  MISMATCH DETECTED!")
                # Check intersection logic
                # Maybe linked budgets are NOT in the service style?
                linked_ids = set(c.budget_options.values_list('id', flat=True))
                style_ids = set(filtered_by_style.values_list('id', flat=True))
                intersection = linked_ids.intersection(style_ids)
                print(f"  - Intersection of Linked & Style-Available: {len(intersection)}")


if __name__ == '__main__':
    verify_filter()
