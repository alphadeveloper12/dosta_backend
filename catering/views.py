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
        courses = Course.objects.all()  # Get all courses
        serializer = CourseSerializer(courses, many=True, context={'request': request})  # Pass request context
        return Response(serializer.data)

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