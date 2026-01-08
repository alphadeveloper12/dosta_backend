import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Pax, ServiceStylePrivate

def check_pax_data():
    print("--- Checking Pax Data ---")
    pax_all = Pax.objects.all()
    for p in pax_all:
        private_styles = p.service_styles_private.all()
        private_names = [s.name for s in private_styles]
        print(f"Pax: {p.label} ({p.number}) -> Linked Private Styles: {private_names}")

    print("\n--- Checking Private Service Styles ---")
    styles = ServiceStylePrivate.objects.all()
    for s in styles:
        print(f"ID: {s.id}, Name: {s.name}")

if __name__ == "__main__":
    check_pax_data()
