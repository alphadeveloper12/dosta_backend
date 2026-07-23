import os
import sys
import django
import requests
from io import BytesIO
from django.core.files import File
from urllib.parse import urlparse

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import Menu, MenuItem, DayOfWeek

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        if hasattr(pip, 'main'):
            pip.main(['install', package])
        else:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    finally:
        globals()[package] = importlib.import_module(package)

try:
    import pandas as pd
except ImportError:
    print("Pandas not found. Installing...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas', 'openpyxl'])
        import pandas as pd
    except Exception as e:
        print(f"Failed to install pandas: {e}")
        sys.exit(1)

def parse_week(week_str):
    """Parses 'Week 1' to 1"""
    try:
        return int(str(week_str).lower().replace('week', '').strip())
    except:
        return 1

def import_menu_data(file_path):
    print(f"Reading file: {file_path}")
    
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            print("Unsupported file format. Please use .csv or .xlsx")
            return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Normalize columns
    df.columns = [c.strip() for c in df.columns]
    
    # Detect Mode
    has_week_day = "Week" in df.columns and "Day" in df.columns
    has_item_price = "Item" in df.columns and "Price" in df.columns
    
    if not has_item_price:
        print("Error: 'Item' and 'Price' columns are required.")
        return

    is_price_update_mode = not has_week_day
    if is_price_update_mode:
        print("Mode: PRICE UPDATE ONLY (Week/Day columns missing). Will update existing items globally.")
    else:
        print("Mode: FULL IMPORT (Creating/Updating Menu Items per Week/Day).")

    added_count = 0
    skipped_count = 0

    print("Starting import process...")

    item_metadata_map = {}
    
    for index, row in df.iterrows():
        try:
            item_name = row.get("Item", "").strip()
            if not item_name:
                continue

            # Cleanup numeric fields (remove 'kcal', 'g', etc if present)
            def clean_num(val):
                if pd.isna(val) or val == "":
                    return 0
                if isinstance(val, (int, float)):
                    return val
                s = ''.join(c for c in str(val) if c.isdigit() or c == '.')
                try:
                    return float(s) if s else 0
                except:
                    return 0

            # Extract Data
            price = row.get("Price", 0)
            description = row.get("Description", "")
            calories = row.get("Calories", 0)
            protein = row.get("Protein", 0)
            carbs = row.get("Carbs", 0)
            fats = row.get("Fats", 0)
            image_url = row.get("Picture", "")

            final_data = {
                'price': float(clean_num(price)),
                'description': description if pd.notna(description) else "",
                'calories': int(clean_num(calories)),
                'protein': float(clean_num(protein)),
                'carbs': float(clean_num(carbs)),
                'fats': float(clean_num(fats))
            }
            
            if is_price_update_mode:
                # Direct capture for global update
                item_metadata_map[item_name] = final_data
                print(f"Captured update for '{item_name}': {final_data['price']}")
                continue

            # --- FULL IMPORT MODE LOGIC ---
            week_num = parse_week(row.get("Week", 1))
            day_str = row.get("Day", "").strip().title()

            if not day_str or day_str not in DayOfWeek.values:
                print(f"Skipping row {index}: Invalid Day '{day_str}'")
                continue

            # 1. Get or Create Menu
            menu, created = Menu.objects.get_or_create(
                week_number=week_num,
                day_of_week=day_str
            )

            # 2. Get or Create MenuItem
            item, created = MenuItem.objects.get_or_create(
                menu=menu,
                name=item_name,
                defaults=final_data
            )

            # 3. Update fields if it already existed
            if not created:
                item.price = final_data['price']
                item.description = final_data['description']
                item.calories = final_data['calories']
                item.protein = final_data['protein']
                item.carbs = final_data['carbs']
                item.fats = final_data['fats']
                print(f"Updating existing item: {item_name} (Week {week_num}, {day_str})")
            else:
                print(f"Added new item: {item_name} (Week {week_num}, {day_str})")

            # 4. Handle Image Download
            if image_url and pd.notna(image_url) and str(image_url).startswith('http'):
                try:
                    print(f"Downloading image for {item_name}...")
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        img_name = os.path.basename(urlparse(image_url).path)
                        if not img_name: img_name = f"{item_name.replace(' ', '_')}.jpg"
                        item.image.save(img_name, File(BytesIO(response.content)), save=False)
                except Exception as e:
                    print(f"Failed to download image: {e}")

            item.save()
            
            # Store metadata for Final Global Pass
            # The last row processed for "Item Name" determines the final global values.
            item_metadata_map[item_name] = final_data

            added_count += 1

        except Exception as e:
            print(f"Error processing row {index}: {e}")

    # -------------------------------------------------------
    # PASS 2: Global Consistency Update
    # -------------------------------------------------------
    print("\nStarting Global Consistency Update...")
    updated_groups = 0
    for name, data in item_metadata_map.items():
        # Update ALL instances of this item name with the final captured data
        count = MenuItem.objects.filter(name=name).update(**data)
        if count > 0:
            updated_groups += 1
            # Optional: Detailed log
            # print(f"Synced '{name}' -> Price: {data['price']} ({count} items)")

    print(f"Global Update Completed. Synced {updated_groups} unique item groups.")

    print("\n-----------------------------------")
    print(f"Import Summary:")
    print(f"Added New Items: {added_count}")
    print(f"Skipped Existing: {skipped_count}")
    print("-----------------------------------")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_menu.py <path_to_excel_or_csv>")
        # Default to a likely filename if exists, for testing
        default_file = "weekly_menu_sample.csv"
        if os.path.exists(default_file):
            print(f"No file specified. Using default: {default_file}")
            import_menu_data(default_file)
        else:
             print("Please provide a file path.")
    else:
        import_menu_data(sys.argv[1])
