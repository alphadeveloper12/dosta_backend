import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import MenuItem, MasterItem

def populate_master_items():
    print("Starting MasterItem population...")
    
    # 1. Create MasterItems from unique names
    items = MenuItem.objects.all()
    total = items.count()
    print(f"Found {total} MenuItems.")
    
    processed = 0
    created_masters = 0
    linked_existing = 0
    
    # We can rely on the pre_save signal I added!
    # By simply saving the item, the signal will kick in:
    # - Check for existing MasterItem by name
    # - If not found, create one
    # - Link it
    
    for item in items:
        if item.master_item:
            print(f"Skipping {item.name}, already linked.")
            continue
            
        print(f"Processing {item.name}...")
        try:
            # We don't want to change the item's data, just link it.
            # The signal will link it.
            item.save()
            
            # Check what happened
            if item.master_item:
                 # Check if it was just created or reused (approximate check)
                 # In a real script we'd count better, but this is fine.
                 pass
                 
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed}/{total}...")
                
        except Exception as e:
            print(f"Error processing {item.name}: {e}")

    final_master_count = MasterItem.objects.count()
    print(f"Done! Processed {processed} items.")
    print(f"Total MasterItems in DB: {final_master_count}")

if __name__ == '__main__':
    populate_master_items()
