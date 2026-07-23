import os
import django
import shutil
from django.core.files import File
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import MenuItem, CanapeItem

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_ROOT = r"C:\Users\User\Desktop\main\Dosta Website Images\Country Menu"
MEDIA_ROOT = settings.MEDIA_ROOT

def match_and_update_menu_item(image_path, cuisine_name=None):
    filename = os.path.basename(image_path)
    name_no_ext = os.path.splitext(filename)[0].strip()
    
    # Try to find matching MenuItem
    # We can rely on unique names or filter by cuisine if provided
    query = MenuItem.objects.filter(name__iexact=name_no_ext)
    
    if cuisine_name:
        query = query.filter(cuisine__name__iexact=cuisine_name)
        
    items = query.all()
    
    if not items.exists():
        print(f"Skipping: No MenuItem found for '{name_no_ext}'")
        return

    # Target directory
    target_dir = os.path.join(MEDIA_ROOT, 'menu_items')
    os.makedirs(target_dir, exist_ok=True)
    
    for item in items:
        print(f"Updating MenuItem: {item.name}")
        
        # Copy file to media
        # We need to open it and save it to the field to handle duplicate names correctly
        # or just copy and set path. Using File() is safer for Django.
        
        with open(image_path, 'rb') as f:
            item.image.save(filename, File(f), save=True)
        print(f"  - Image saved: {item.image.name}")

def match_and_update_canape(image_path, category=None):
    filename = os.path.basename(image_path)
    name_no_ext = os.path.splitext(filename)[0].strip()
    
    # Map folder category to model choices if needed
    # Folders: "Arabic Canapés", "Cold Beverages", etc.
    # Choices: 'Arabic', 'Cold Beverages', etc.
    
    # Heuristic mapping
    db_category = None
    if category:
        if "Arabic" in category: db_category = "Arabic"
        elif "Cold Canapés" in category: db_category = "Cold"
        elif "Hot Canapés" in category: db_category = "Hot"
        elif "Sweet" in category: db_category = "Sweet"
        elif "Vegetarian" in category: db_category = "Vegetarian"
        elif "Cold Beverages" in category: db_category = "Cold Beverages"
        elif "Hot Beverages" in category: db_category = "Hot Beverages"
    
    query = CanapeItem.objects.filter(name__iexact=name_no_ext)
    if db_category:
        query = query.filter(category=db_category)
        
    items = query.all()
    
    if not items.exists():
        # Fallback: try without category if not found
        query = CanapeItem.objects.filter(name__iexact=name_no_ext)
        items = query.all()
        if not items.exists():
             print(f"Skipping: No CanapeItem found for '{name_no_ext}'")
             return

    # Target directory
    target_dir = os.path.join(MEDIA_ROOT, 'canapes')
    os.makedirs(target_dir, exist_ok=True)

    for item in items:
        print(f"Updating CanapeItem: {item.name}")
        with open(image_path, 'rb') as f:
            item.image.save(filename, File(f), save=True)
        print(f"  - Image saved: {item.image.name}")


def process_folder(folder_path, handler_func, **kwargs):
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return
        
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                full_path = os.path.join(root, file)
                handler_func(full_path, **kwargs)

def run():
    print("Starting image population...")
    
    # 1. African Menu
    print("\n--- Processing African Menu ---")
    african_path = os.path.join(SOURCE_ROOT, "African")
    process_folder(african_path, match_and_update_menu_item, cuisine_name="African")
    
    # 2. Turkish Menu
    print("\n--- Processing Turkish Menu ---")
    turkish_path = os.path.join(SOURCE_ROOT, "Turkish")
    process_folder(turkish_path, match_and_update_menu_item, cuisine_name="Turkish")
    
    # 3. Canapes
    print("\n--- Processing Canapes ---")
    canape_root = os.path.join(SOURCE_ROOT, "Canape Options - Dosta")
    
    # Iterate subfolders for categories
    if os.path.exists(canape_root):
        for entry in os.scandir(canape_root):
            if entry.is_dir():
                print(f"Scanning category folder: {entry.name}")
                process_folder(entry.path, match_and_update_canape, category=entry.name)
    else:
        print(f"Canape root not found: {canape_root}")

    print("\nDone.")

if __name__ == '__main__':
    run()
