
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import MenuItem

def verify_new():
    targets = [
        "Lasagna Bolognese", 
        "Kung Pao Chicken", 
        "BEEF STROGANOFF" 
    ]
    
    print("Verifying New Menu Items...")
    for t in targets:
        item = MenuItem.objects.filter(name__iexact=t).first()
        if item:
            status = "OK" if item.image else "NO IMAGE"
            if item.image:
                if not os.path.exists(item.image.path):
                    status = "IMAGE FILE MISSING"
            print(f"Item: {t} | Found | Image: {status}")
        else:
             print(f"Item: {t} | NOT FOUND")

if __name__ == "__main__":
    verify_new()
