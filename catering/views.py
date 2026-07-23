from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import *
from .serializers import *
from .serializers import IftarBoxMenuSerializer


def is_catering_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

class EventTypeListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # ✅ Only logged-in users can access

    def get(self, request):
        event_types = EventType.objects.all()
        serializer = EventTypeSerializer(event_types, many=True, context={'request': request})
        return Response(serializer.data)


class ProviderTypeListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # ✅ Only logged-in users

    def get(self, request):
        providers = ProviderType.objects.all()
        serializer = ProviderTypeSerializer(providers, many=True, context={'request': request})
        return Response(serializer.data)
    
class EventNameListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        event_names = EventName.objects.all()
        serializer = EventNameSerializer(event_names, many=True)
        return Response(serializer.data)
    
class ServiceStyleListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # ✅ Only authenticated users can access

    def get(self, request):
        service_styles = ServiceStyle.objects.all()
        serializer = ServiceStyleSerializer(service_styles, many=True)
        return Response(serializer.data)
    
class ServiceStylePrivateListView(APIView):
    permission_classes = [AllowAny]  # ✅ Only authenticated users can access

    def get(self, request):
        service_styles = ServiceStylePrivate.objects.all()
        serializer = ServiceStylePrivateSerializer(service_styles, many=True)
        return Response(serializer.data)
    
class ServiceStylePrivateChefListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # ✅ Only authenticated users can access

    def get(self, request):
        service_styles = ServiceStylePrivateChef.objects.all()
        serializer = ServiceStylePrivateChefSerializer(service_styles, many=True)
        return Response(serializer.data)
    
class CuisineListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # Only authenticated users can access this endpoint

    def get(self, request):
        cuisines = Cuisine.objects.all()
        
        service_style_id = request.query_params.get('service_style_id')
        event_type = request.query_params.get('event_type_name', '').lower()

        if service_style_id:
            try:
                service_style_id = int(service_style_id)
                # Check event type to decide which service style model to filter by
                if 'corporate' in event_type:
                    cuisines = cuisines.filter(service_styles__id=service_style_id)
                elif 'private chef' in event_type or 'private_chef' in event_type:
                    cuisines = cuisines.filter(service_styles_private_chef__id=service_style_id)
                else: 
                    # Private event (not chef)
                    cuisines = cuisines.filter(service_styles_private__id=service_style_id)
            except ValueError:
                pass


        
        serializer = CuisineSerializer(cuisines, many=True, context={'request': request})
        return Response(serializer.data)
    
class CourseListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # Only authenticated users can access this endpoint

    def get(self, request):
        courses = Course.objects.all()
        
        # Filter by cuisine_ids if provided
        cuisine_ids = request.query_params.get('cuisine_ids')
        if cuisine_ids:
            try:
                ids = [int(id) for id in cuisine_ids.split(',')]
                courses = courses.filter(cuisines__id__in=ids).distinct()
            except ValueError:
                pass # Ignore invalid inputs

        # Filter by budget_id if provided (Fixed Menu Logic)
        budget_id = request.query_params.get('budget_id')
        if budget_id:
            try:
                budget_id = int(budget_id)
                courses = courses.filter(budget_options__id=budget_id).distinct()
            except ValueError:
                pass

        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)

class MenuItemListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        menu_items = MenuItem.objects.all()

        # 1. Filter by Cuisines
        cuisine_ids = request.query_params.get('cuisine_ids')
        if cuisine_ids:
            try:
                ids = [int(id) for id in cuisine_ids.split(',')]
                menu_items = menu_items.filter(cuisine__id__in=ids)
            except ValueError:
                pass
        
        print(f"DEBUG: Items after Cuisine Filter: {menu_items.count()}")

        # 2. Filter by Courses
        course_ids = request.query_params.get('course_ids')
        if course_ids:
            try:
                ids = [int(id) for id in course_ids.split(',')]
                menu_items = menu_items.filter(course__id__in=ids)
            except ValueError:
                pass
        
        print(f"DEBUG: Items after Course Filter: {menu_items.count()}")

        # 3. Filter by Budget
        budget_id = request.query_params.get('budget_id')
        if budget_id:
            try:
                budget_id = int(budget_id)
                # Filter items that are linked to the selected budget via M2M
                menu_items = menu_items.filter(budget_options__id=budget_id).distinct()
            except ValueError:
                pass
        
        # Serialize and return
        serializer = MenuItemSerializer(menu_items, many=True, context={'request': request})
        return Response(serializer.data)

class LocationListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # Ensure only authenticated users can access the API

    def get(self, request):
        locations = Location.objects.all()  # Get all locations
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)

class PaxListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        pax_options = Pax.objects.all()
        service_style_id = request.query_params.get('service_style_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'
        is_private_chef = request.query_params.get('is_private_chef', 'false').lower() == 'true'
        
        if service_style_id:
            try:
                service_style_id = int(service_style_id)
                if is_private_chef:
                     # Filter by private chef service style M2M
                     pax_options = pax_options.filter(service_styles_private_chef__id=service_style_id)
                elif is_private:
                     # Filter by private service style M2M
                     pax_options = pax_options.filter(service_styles_private__id=service_style_id)
                else:
                     # Filter by corporate service style M2M
                     pax_options = pax_options.filter(service_styles__id=service_style_id)
            except ValueError:
                pass
        
        serializer = PaxSerializer(pax_options, many=True)
        return Response(serializer.data)
    
    
class BudgetOptionListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        budget_options = BudgetOption.objects.all()  # Get all BudgetOption objects
        
        service_style_id = request.query_params.get('service_style_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'
        is_private_chef = request.query_params.get('is_private_chef', 'false').lower() == 'true'

        if service_style_id:
            try:
                if is_private_chef:
                    style = ServiceStylePrivateChef.objects.get(id=service_style_id)
                    budget_options = budget_options.filter(service_styles_private_chef__id=service_style_id)
                elif is_private:
                    style = ServiceStylePrivate.objects.get(id=service_style_id)
                    budget_options = budget_options.filter(service_styles_private__id=service_style_id)
                else:
                    style = ServiceStyle.objects.get(id=service_style_id)
                    budget_options = budget_options.filter(service_styles__id=service_style_id)
                
                # STRICT CHECK: If Buffet or Set Menu, strict filtering by cuisine is expected.
                # If cuisine_ids is not provided, return NONE (instead of all).
                style_name = style.name.lower()
                if 'buffet' in style_name or 'set menu' in style_name:
                    cuisine_ids = request.query_params.get('cuisine_ids')
                    if not cuisine_ids:
                         budget_options = budget_options.none()

            except (ValueError, ServiceStyle.DoesNotExist, ServiceStylePrivate.DoesNotExist, ServiceStylePrivateChef.DoesNotExist):
                # FAIL SAFE: If service style ID is invalid or lookup fails, return NONE instead of ALL.
                budget_options = budget_options.none()
        
        # Filter by Cuisine (if provided)
        cuisine_ids = request.query_params.get('cuisine_ids')
        if cuisine_ids:
            try:
                ids = [int(id) for id in cuisine_ids.split(',')]
                # Filter budgets that are associated with ANY of the selected cuisines
                # Since relationship is 'cuisines' (related_name on BudgetOption from Cuisine model)
                budget_options = budget_options.filter(cuisines__id__in=ids).distinct()
            except ValueError:
                budget_options = budget_options.none()
                
        serializer = BudgetOptionSerializer(budget_options, many=True)
        return Response(serializer.data)

class CoffeeBreakRotationListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        rotations = CoffeeBreakRotation.objects.all().prefetch_related('items')
        serializer = CoffeeBreakRotationSerializer(rotations, many=True, context={'request': request})
        return Response(serializer.data)

class PlatterItemListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        platters = PlatterItem.objects.all()
        serializer = PlatterItemSerializer(platters, many=True, context={'request': request})
        return Response(serializer.data)

class BoxedMealItemListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        items = BoxedMealItem.objects.all()
        serializer = BoxedMealItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class LiveStationItemListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        items = LiveStationItem.objects.all()
        serializer = LiveStationItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class FixedCateringMenuListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        menus = FixedCateringMenu.objects.all()
        
        # Filter by Cuisine
        cuisine_ids = request.query_params.get('cuisine_ids')
        if cuisine_ids:
            try:
                ids = [int(id) for id in cuisine_ids.split(',')]
                menus = menus.filter(cuisine__id__in=ids)
            except ValueError:
                pass
                
        # Filter by Budget
        budget_id = request.query_params.get('budget_id')
        if budget_id:
            try:
                menus = menus.filter(budget_option__id=int(budget_id))
            except ValueError:
                pass
                
        serializer = FixedCateringMenuSerializer(menus, many=True, context={'request': request})
        return Response(serializer.data)

class AmericanMenuListView(generics.ListAPIView):
    serializer_class = AmericanMenuSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = AmericanMenu.objects.all().prefetch_related('items')

class CanapeItemListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        items = CanapeItem.objects.all()
        serializer = CanapeItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class SweetsItemListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        items = SweetsItem.objects.prefetch_related('images', 'variations').all()
        serializer = SweetsItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

# ========== CATERING ORDER VENDOR API ==========

from django.views.generic import TemplateView, DetailView

class CreateCateringOrderView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CateringOrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CateringKitchenDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'catering/kitchen_dashboard.html'
    
    def test_func(self):
        return is_catering_staff(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initial load can just be empty or basic context
        # We'll use API polling for data
        return context

class CateringOrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CateringOrder
    template_name = 'catering/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        return is_catering_staff(self.request.user)

@login_required
@user_passes_test(is_catering_staff)
def get_active_catering_orders(request):
    """
    Returns JSON of active orders for the dashboard polling.
    """
    from django.http import JsonResponse
    from django.utils.timesince import timesince
    from django.urls import reverse
    
    orders = CateringOrder.objects.filter(
        status__in=[
            CateringOrderStatus.PENDING, 
            CateringOrderStatus.CONFIRMED, 
            CateringOrderStatus.PREPARING, 
            CateringOrderStatus.READY
        ]
    ).order_by('-created_at')
    
    data = []
    for order in orders:
        items_data = []
        for item in order.items.all():
            items_data.append({
                'name': item.name,
                'course': item.course,
                'quantity': item.quantity,
                'description': item.description
            })
            
        data.append({
            'id': order.id,
            'order_id': order.order_id,
            'user': order.user.username,
            'status': order.status,
            'status_display': order.get_status_display(),
            'event_type': order.event_type,
            'guest_count': order.guest_count,
            'event_date': str(order.event_date),
            'event_time': str(order.event_time),
            'location': order.location,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat(),
            'timesince': timesince(order.created_at),
            'items': items_data,
            'detail_url': reverse('kitchen:catering_order_detail', args=[order.id])
        })
        
    return JsonResponse({'orders': data})


# ========== RAMADAN MENU API ==========

class RamadanMenuListView(APIView):
    """
    List all Ramadan menus with optional filtering by service_style and budget_option.
    Query params:
        - service_style_id: Filter by service style (e.g., Iftar Menu, Sohour Menu)
        - budget_option_id: Filter by budget option
        - is_active: Filter by active status (default: true)
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        menus = RamadanMenu.objects.all().prefetch_related(
            'menu_courses__course',
            'menu_courses__items__master_item'
        )
        
        # Filter by service style
        service_style_id = request.query_params.get('service_style_id')
        if service_style_id:
            try:
                menus = menus.filter(service_style__id=int(service_style_id))
            except ValueError:
                pass
        
        # Filter by budget option
        budget_option_id = request.query_params.get('budget_option_id')
        if budget_option_id:
            try:
                menus = menus.filter(budget_option__id=int(budget_option_id))
            except ValueError:
                pass
        
        # Filter by active status (default: only active menus)
        is_active = request.query_params.get('is_active', 'true').lower()
        if is_active == 'true':
            menus = menus.filter(is_active=True)
        elif is_active == 'false':
            menus = menus.filter(is_active=False)
        
        serializer = RamadanMenuListSerializer(menus, many=True, context={'request': request})
        return Response(serializer.data)


class RamadanMenuDetailView(APIView):
    """
    Get detailed information about a specific Ramadan menu including all courses and items.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, menu_id):
        try:
            menu = RamadanMenu.objects.prefetch_related(
                'menu_courses__course',
                'menu_courses__items__master_item'
            ).get(id=menu_id)
            
            serializer = RamadanMenuSerializer(menu, context={'request': request})
            return Response(serializer.data)
        except RamadanMenu.DoesNotExist:
            return Response(
                {'error': 'Menu not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

# ========== IFTAR BOX MENU API ==========

class IftarBoxMenuListView(APIView):
    """
    List Iftar Box Menus with optional filtering by budget_option.
    Query params:
        - budget_option_id: Filter by budget option
        - is_active: Filter by active status (default: true)
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        menus = IftarBoxMenu.objects.all()

        budget_option_id = request.query_params.get('budget_option_id')
        if budget_option_id:
            try:
                menus = menus.filter(budget_option__id=int(budget_option_id))
            except ValueError:
                pass

        is_active = request.query_params.get('is_active', 'true').lower()
        if is_active == 'true':
            menus = menus.filter(is_active=True)
        elif is_active == 'false':
            menus = menus.filter(is_active=False)

        serializer = IftarBoxMenuSerializer(menus, many=True, context={'request': request})
        return Response(serializer.data)


# ========== BEIT NAHLA VIEWS ==========

import math
from datetime import datetime, time as _time, timedelta
from decimal import Decimal

try:
    from zoneinfo import ZoneInfo
    UAE_TZ = ZoneInfo('Asia/Dubai')
except Exception:
    UAE_TZ = None


def _uae_now():
    """Current local time in Asia/Dubai (falls back to UTC+4)."""
    if UAE_TZ:
        return datetime.now(UAE_TZ)
    return datetime.utcnow() + timedelta(hours=4)


def _is_open(opening: _time, closing: _time, now_time: _time):
    """
    Returns True if now_time is within opening..closing.
    Handles overnight windows where closing < opening (e.g. 10:00 -> 02:00).
    """
    if opening == closing:
        return True  # 24/7
    if opening < closing:
        return opening <= now_time < closing
    # Overnight (e.g. open 22:00, close 02:00)
    return now_time >= opening or now_time < closing


def beit_nahla_open_status(cfg=None):
    """Returns dict { is_open_now, current_time, opening_time, closing_time }."""
    if cfg is None:
        cfg = BeitNahlaSettings.load()
    now = _uae_now()
    now_t = now.time().replace(microsecond=0)
    return {
        'is_open_now': _is_open(cfg.opening_time, cfg.closing_time, now_t),
        'current_time': now_t.strftime('%H:%M'),
        'opening_time': cfg.opening_time.strftime('%H:%M'),
        'closing_time': cfg.closing_time.strftime('%H:%M'),
    }


class BeitNahlaConfigView(APIView):
    """GET pricing + restaurant location + distance tiers + open/closed."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        settings_obj = BeitNahlaSettings.load()
        data = BeitNahlaSettingsSerializer(settings_obj, context={'request': request}).data
        data.update(beit_nahla_open_status(settings_obj))
        return Response(data)


class BeitNahlaMealBoxListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        boxes = BeitNahlaMealBox.objects.filter(is_active=True).prefetch_related('images').order_by('display_order', 'name')
        serializer = BeitNahlaMealBoxSerializer(boxes, many=True, context={'request': request})
        return Response(serializer.data)


class BeitNahlaOptionsView(APIView):
    """Return all option categories (with their items) for the selection drawer."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        categories = BeitNahlaOptionCategory.objects.filter(is_active=True).prefetch_related('items').order_by('display_order', 'name')
        serializer = BeitNahlaOptionCategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (fallback when OSRM fails)."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _osrm_distance_km(lat1, lon1, lat2, lon2, timeout=4):
    """Real road distance via public OSRM service. Returns km or None on failure."""
    import requests
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
        resp = requests.get(url, params={'overview': 'false'}, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get('code') != 'Ok' or not data.get('routes'):
            return None
        return data['routes'][0]['distance'] / 1000.0
    except Exception:
        return None


class BeitNahlaCreateOrderView(APIView):
    """
    Create a Beit Nahla order. Used by the cart checkout.
    Expected POST payload:
      {
        "mode": "ORDER_NOW" | "WEEKLY",
        "customer_phone": str,
        "delivery_address": str,
        "latitude": float (optional),
        "longitude": float (optional),
        "distance_km": float (optional),
        "tier_label": str (optional),
        "subtotal": Decimal,
        "vat": Decimal,
        "discount": Decimal,
        "service_charge": Decimal,
        "delivery_charge": Decimal,
        "total_amount": Decimal,
        "items": [
          { "meal_box_id": int, "box_name": str, "unit_price": Decimal,
            "quantity": int, "selections_summary": str }
        ]
      }
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        items_in = data.get('items') or []
        if not isinstance(items_in, list) or len(items_in) == 0:
            return Response({'error': 'At least one meal box is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not data.get('customer_phone'):
            return Response({'error': 'Phone number is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not data.get('delivery_address'):
            return Response({'error': 'Delivery address is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None
        try:
            order = BeitNahlaOrder.objects.create(
                user=user,
                mode=data.get('mode', 'ORDER_NOW'),
                customer_name=data.get('customer_name') or '',
                customer_phone=data['customer_phone'],
                building=data.get('building') or '',
                street=data.get('street') or '',
                appt=data.get('appt') or '',
                delivery_address=data['delivery_address'],
                latitude=data.get('latitude') or None,
                longitude=data.get('longitude') or None,
                distance_km=data.get('distance_km') or None,
                tier_label=data.get('tier_label') or '',
                subtotal=data.get('subtotal') or 0,
                vat=data.get('vat') or 0,
                discount=data.get('discount') or 0,
                service_charge=data.get('service_charge') or 0,
                delivery_charge=data.get('delivery_charge') or 0,
                total_amount=data.get('total_amount') or 0,
                notes=data.get('notes', ''),
            )
            for it in items_in:
                BeitNahlaOrderItem.objects.create(
                    order=order,
                    meal_box_id=it.get('meal_box_id') or None,
                    box_name=it.get('box_name', '')[:200] or 'Meal box',
                    unit_price=it.get('unit_price') or 0,
                    quantity=int(it.get('quantity') or 1),
                    selections_summary=it.get('selections_summary', ''),
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'ok': True,
            'order_id': order.order_id,
            'status': order.status,
            'total_amount': str(order.total_amount),
            'created_at': order.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class BeitNahlaCalculateDeliveryView(APIView):
    """
    POST { user_latitude, user_longitude } -> { distance_km, deliverable,
    service_charge, delivery_charge, total_extra, tier_label }.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user_lat = float(request.data.get('user_latitude'))
            user_lng = float(request.data.get('user_longitude'))
        except (TypeError, ValueError):
            return Response(
                {'error': 'user_latitude and user_longitude are required and must be numeric.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cfg = BeitNahlaSettings.load()
        open_status = beit_nahla_open_status(cfg)
        origin_lat = float(cfg.restaurant_latitude)
        origin_lng = float(cfg.restaurant_longitude)

        distance_km = _osrm_distance_km(origin_lat, origin_lng, user_lat, user_lng)
        used_road_distance = distance_km is not None
        if distance_km is None:
            distance_km = _haversine_km(origin_lat, origin_lng, user_lat, user_lng)

        distance_km = round(distance_km, 2)
        max_km = float(cfg.max_deliverable_km)

        def base_response():
            return {
                'distance_km': distance_km,
                'used_road_distance': used_road_distance,
                'max_deliverable_km': max_km,
                **open_status,
            }

        if distance_km > max_km:
            resp = base_response()
            resp.update({
                'deliverable': False,
                'service_charge': 0,
                'delivery_charge': 0,
                'total_extra': 0,
                'tier_label': None,
                'message': f"Sorry, we do not deliver beyond {max_km} km.",
            })
            return Response(resp)

        tier = (
            BeitNahlaDistanceTier.objects
            .filter(is_active=True, min_km__lte=distance_km, max_km__gte=distance_km)
            .order_by('min_km')
            .first()
        )

        if not tier:
            resp = base_response()
            resp.update({
                'deliverable': False,
                'service_charge': 0,
                'delivery_charge': 0,
                'total_extra': 0,
                'tier_label': None,
                'message': 'No matching delivery tier configured for this distance.',
            })
            return Response(resp)

        service = float(tier.service_charge)
        delivery = float(tier.delivery_charge)
        resp = base_response()
        resp.update({
            'deliverable': True,
            'service_charge': service,
            'delivery_charge': delivery,
            'total_extra': round(service + delivery, 2),
            'tier_label': tier.label or f"{tier.min_km}-{tier.max_km} km",
        })
        if not open_status['is_open_now']:
            resp['message'] = (
                f"We are currently closed. Working hours: "
                f"{open_status['opening_time']} – {open_status['closing_time']}."
            )
        return Response(resp)
