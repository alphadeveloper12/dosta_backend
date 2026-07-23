import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Pax, ServiceStylePrivate

def fix_pax_private():
    print("Fixing Pax for Private Service Styles...")
    
    # Get all private styles
    private_styles = ServiceStylePrivate.objects.all()
    print(f"Found {private_styles.count()} private service styles.")
    
    # Get all Pax options
    pax_options = Pax.objects.all()
    print(f"Found {pax_options.count()} pax options.")

    if private_styles.count() == 0:
        print("No private service styles found. Creating some dummy ones if needed? (Skipping for now, assuming they exist)")

    # Link all Pax to all Private Styles (assuming generic compatibility)
    for p in pax_options:
        print(f"Linking '{p.label}' to all private styles...")
        for s in private_styles:
            p.service_styles_private.add(s)
        p.save()
        
    print("Done linking Pax to Private Service Styles.")

if __name__ == "__main__":
    fix_pax_private()
