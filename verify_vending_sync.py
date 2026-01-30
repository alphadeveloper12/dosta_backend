import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import MenuItem, MasterItem

def verify_sync():
    print("Verifying MasterItem -> MenuItem synchronization...")
    
    # 1. Pick a test MasterItem
    master = MasterItem.objects.first()
    if not master:
        print("No MasterItems found! Run population script first.")
        return

    original_name = master.name
    print(f"Testing with MasterItem: '{original_name}'")
    
    # Get linked items count
    linked_count = master.menu_items.count()
    print(f"It has {linked_count} linked MenuItems.")
    
    if linked_count == 0:
        print("Warning: No linked items to test sync.")
        
    # 2. Modify MasterItem name
    new_name = original_name + " (UPDATED)"
    print(f"Renaming MasterItem to '{new_name}'...")
    master.name = new_name
    master.save() # This should trigger the signal
    
    # 3. Verify Children
    # We need to refresh them from DB
    children = master.menu_items.all()
    all_matched = True
    for child in children:
        if child.name != new_name:
            print(f"FAIL: Child {child.id} name is '{child.name}', expected '{new_name}'")
            all_matched = False
        else:
            # print(f"OK: Child {child.id} updated.")
            pass
            
    if all_matched:
        print("SUCCESS: All linked MenuItems were updated!")
        
    # 4. Revert
    print(f"Reverting name to '{original_name}'...")
    master.name = original_name
    master.save()
    
    # Verify revert works too
    children = master.menu_items.all()
    all_reverted = True
    for child in children:
        if child.name != original_name:
            all_reverted = False
            
    if all_reverted:
        print("SUCCESS: Revert complete.")
    else:
        print("FAIL: Revert failed.")

if __name__ == '__main__':
    verify_sync()
