import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta_backend.settings')
django.setup()

from catering.models import ServiceStyle

def update_min_pax():
    try:
        buffet = ServiceStyle.objects.get(name__icontains="Buffet")
        buffet.min_pax = 20
        buffet.save()
        print(f"Successfully updated '{buffet.name}' min_pax to {buffet.min_pax}")
    except ServiceStyle.DoesNotExist:
        print("Buffet service style not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_min_pax()
