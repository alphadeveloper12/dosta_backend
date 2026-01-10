import os
import django
from django.conf import settings

from dotenv import load_dotenv

load_dotenv()
# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def register():
    # Ensure site exists
    site, created = Site.objects.get_or_create(id=1, defaults={'domain': 'localhost:8000', 'name': 'localhost'})
    if not created:
        site.domain = 'localhost:8000'
        site.name = 'localhost'
        site.save()

    # Register Google App
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in environment.")
        return

    app, created = SocialApp.objects.get_or_create(
        provider='google',
        name='Google Login',
        defaults={
            'client_id': client_id,
            'secret': client_secret,
        }
    )
    if not created:
        app.client_id = client_id
        app.secret = client_secret
        app.save()

    app.sites.add(site)
    print(f"Google Social App registered for site {site.domain}")

if __name__ == "__main__":
    register()
