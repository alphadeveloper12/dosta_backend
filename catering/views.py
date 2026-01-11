from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import *
from .serializers import *

class EventTypeListView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Only logged-in users can access

    def get(self, request):
        event_types = EventType.objects.all()
        serializer = EventTypeSerializer(event_types, many=True, context={'request': request})
        return Response(serializer.data)


class ProviderTypeListView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Only logged-in users

    def get(self, request):
        providers = ProviderType.objects.all()
        serializer = ProviderTypeSerializer(providers, many=True, context={'request': request})
        return Response(serializer.data)
    
class EventNameListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        event_names = EventName.objects.all()
        serializer = EventNameSerializer(event_names, many=True)
        return Response(serializer.data)
    
class ServiceStyleListView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Only authenticated users can access

    def get(self, request):
        service_styles = ServiceStyle.objects.all()
        serializer = ServiceStyleSerializer(service_styles, many=True)
        return Response(serializer.data)
    
class ServiceStylePrivateListView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Only authenticated users can access

    def get(self, request):
        service_styles = ServiceStylePrivate.objects.all()
        serializer = ServiceStylePrivateSerializer(service_styles, many=True)
        return Response(serializer.data)
    
class CuisineListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this endpoint

    def get(self, request):
        cuisines = Cuisine.objects.all()
        
        service_style_id = request.query_params.get('service_style_id')
        event_type = request.query_params.get('event_type_name', '').lower()

        if service_style_id:
            try:
                service_style_id = int(service_style_id)
                # Check if it's a corporate event or private event to decide which model to filter
                if 'corporate' in event_type:
                    cuisines = cuisines.filter(service_styles__id=service_style_id)
                else: 
                     cuisines = cuisines.filter(service_styles_private__id=service_style_id)
            except ValueError:
                pass


        
        serializer = CuisineSerializer(cuisines, many=True, context={'request': request})
        return Response(serializer.data)
    
class CourseListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this endpoint

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access the API

    def get(self, request):
        locations = Location.objects.all()  # Get all locations
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)

class PaxListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pax_options = Pax.objects.all()
        service_style_id = request.query_params.get('service_style_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'
        
        if service_style_id:
            try:
                service_style_id = int(service_style_id)
                if is_private:
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        budget_options = BudgetOption.objects.all()  # Get all BudgetOption objects
        
        service_style_id = request.query_params.get('service_style_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'

        if service_style_id:
            try:
                if is_private:
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

            except (ValueError, ServiceStyle.DoesNotExist, ServiceStylePrivate.DoesNotExist):
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rotations = CoffeeBreakRotation.objects.all().prefetch_related('items')
        serializer = CoffeeBreakRotationSerializer(rotations, many=True, context={'request': request})
        return Response(serializer.data)

class PlatterItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platters = PlatterItem.objects.all()
        serializer = PlatterItemSerializer(platters, many=True, context={'request': request})
        return Response(serializer.data)

class BoxedMealItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = BoxedMealItem.objects.all()
        serializer = BoxedMealItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class LiveStationItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = LiveStationItem.objects.all()
        serializer = LiveStationItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class FixedCateringMenuListView(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]
    queryset = AmericanMenu.objects.all().prefetch_related('items')

class CanapeItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CanapeItem.objects.all()
        serializer = CanapeItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

# ========== CATERING ORDER VENDOR API ==========

from django.views.generic import TemplateView

class CreateCateringOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CateringOrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CateringKitchenDashboardView(TemplateView):
    template_name = 'catering/kitchen_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initial load can just be empty or basic context
        # We'll use API polling for data
        return context

def get_active_catering_orders(request):
    """
    Returns JSON of active orders for the dashboard polling.
    """
    from django.http import JsonResponse
    from django.utils.timesince import timesince
    
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
            'items': items_data
        })
        
    return JsonResponse({'orders': data})