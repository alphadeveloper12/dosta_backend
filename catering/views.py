from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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

        budget_id = request.query_params.get('budget_id')
        if budget_id:
            try:
                budget_id = int(budget_id)
                selected_budget = BudgetOption.objects.get(id=budget_id)
                # Filter cuisines where model's max_price >= selected_budget.min_price
                # This assumes we have migrated data to the Cuisine model
                cuisines = cuisines.filter(max_price__gte=selected_budget.min_price).distinct()
            except (ValueError, BudgetOption.DoesNotExist):
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
        # We now filter using the M2M fields directly.
        
        budget_id = request.query_params.get('budget_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'

        if budget_id:
            try:
                budget_id = int(budget_id)
                menu_items = menu_items.filter(budget_options__id=budget_id)
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
        
        if service_style_id:
            try:
                service_style_id = int(service_style_id)
                pax_options = pax_options.filter(service_styles__id=service_style_id)
            except ValueError:
                pass
        
        serializer = PaxSerializer(pax_options, many=True)
        return Response(serializer.data)
    
class BudgetOptionListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this API (optional)

    def get(self, request):
        budget_options = BudgetOption.objects.all()  # Get all BudgetOption objects
        
        service_style_id = request.query_params.get('service_style_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'

        if service_style_id:
            try:
                if is_private:
                    budget_options = budget_options.filter(service_styles_private__id=service_style_id)
                else:
                    budget_options = budget_options.filter(service_styles__id=service_style_id)
            except ValueError:
                pass
                
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