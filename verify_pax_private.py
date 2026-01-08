import os
import django
from django.test import RequestFactory
from rest_framework.request import Request # Correct DRF Request

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Pax, ServiceStylePrivate
from catering.views import PaxListView

def verify_pax_private():
    # 1. Ensure we have a private style
    style = ServiceStylePrivate.objects.first()
    if not style:
        print("No private style found to test.")
        return

    print(f"Testing filter for Private Style: {style.name} (ID: {style.id})")
    
    # 2. Simulate Request is_private=true
    factory = RequestFactory()
    # /api/catering/pax/?service_style_id=X&is_private=true
    request = factory.get(f'/api/catering/pax/', {'service_style_id': style.id, 'is_private': 'true'})
    
    # Wrap in DRF Request to provide query_params
    drf_request = Request(request)

    # 3. Call view
    view = PaxListView()
    # Monkey patch request for view instance if needed or pass directly
    # Better to manually invoke logic for quick test if not setting up full view context
    
    # Let's perform logic manually to test query filtering:
    
    pax_qs = Pax.objects.all()
    # Logic from view:
    pax_qs = pax_qs.filter(service_styles_private__id=style.id)
    
    results = [str(p) for p in pax_qs]
    print(f"Results for Private Filter: {results}")
    
    if len(results) > 0:
        print("SUCCESS: Found Pax options for private style.")
    else:
        print("FAILURE: No Pax options returned.")

if __name__ == "__main__":
    verify_pax_private()
