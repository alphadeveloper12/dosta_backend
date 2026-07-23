
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import MenuItem

def check_items():
    print("Checking Menu Items...")
    items = MenuItem.objects.all()
    count = 0
    errors = 0
    for item in items:
        try:
            # Accessing fields to ensure they load
            i_id = item.id
            name = item.name
            img = item.image
            
            # Check __str__ as Admin uses this
            str_rep = str(item)

            # Try to resolve path/url if image exists
            img_status = "No Image"
            if img:
                img_path = img.path # Check if file exists on disk
                if os.path.exists(img_path):
                     img_status = f"Image OK: {img.name}"
                else:
                     img_status = f"Image MISSING: {img.name}"
            
            # print(f"ID: {i_id} | OK | {img_status}")
        except Exception as e:
            print(f"ID: {item.id} | ERROR | {e}")
            errors += 1
        count += 1
        if count % 100 == 0:
            print(f"Checked {count} items...")

    print(f"Finished. Total: {count}, Errors: {errors}")

if __name__ == "__main__":
    check_items()
