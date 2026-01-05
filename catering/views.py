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

        # 2. Filter by Courses
        course_ids = request.query_params.get('course_ids')
        if course_ids:
            try:
                ids = [int(id) for id in course_ids.split(',')]
                menu_items = menu_items.filter(course__id__in=ids)
            except ValueError:
                pass

        # 3. Filter/Prefetch Variants by Budget
        # We need to return the item, but specifically with the PRICE for the selected budget.
        # This is slightly complex because an item might have multiple variants.
        # We want to attach the correct price to the serialized output.
        
        budget_id = request.query_params.get('budget_id')
        is_private = request.query_params.get('is_private', 'false').lower() == 'true'

        results = []
        for item in menu_items:
            # Find the matching variant
            matched_variant = None
            if budget_id:
                try:
                    if is_private:
                        matched_variant = item.variants.filter(budget_option_private_id=budget_id).first()
                    else:
                        matched_variant = item.variants.filter(budget_option_id=budget_id).first()
                except ValueError:
                    pass

            # If we found a variant, or if we just want to list items (maybe show base price? Logic TBD)
            # For now, let's include the item if it has a variant for this budget, OR if no budget filtered.
            # But the user asked for "variants according to prices".
            
            # Optimization: If budget is selected, only show items available for that budget?
            # Or show all, but null price? Let's assume we want valid items.
            
            if budget_id and not matched_variant:
                 continue # Skip items not available in this budget (optional, but good for "menu per budget")

            serializer = MenuItemSerializer(item, context={'request': request})
            data = serializer.data
            
            # Manually inject the active price if a budget was selected
            if matched_variant:
                data['active_price'] = matched_variant.price
            
            results.append(data)
            
        return Response(results)

class LocationListView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access the API

    def get(self, request):
        locations = Location.objects.all()  # Get all locations
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)

class BudgetOptionPrivateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        budget_options = BudgetOptionPrivate.objects.all()
        serializer = BudgetOptionPrivateSerializer(budget_options, many=True)
        return Response(serializer.data)

class PaxListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pax_options = Pax.objects.all()
        serializer = PaxSerializer(pax_options, many=True)
        return Response(serializer.data)

class PaxPrivateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pax_options = PaxPrivate.objects.all()
        serializer = PaxPrivateSerializer(pax_options, many=True)
        return Response(serializer.data)
    
class BudgetOptionListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this API (optional)

    def get(self, request):
        budget_options = BudgetOption.objects.all()  # Get all BudgetOption objects
        serializer = BudgetOptionSerializer(budget_options, many=True)
        return Response(serializer.data)