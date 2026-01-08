from rest_framework import serializers
from .models import *

class EventTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = EventType
        fields = ['id', 'name', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None

class EventNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventName
        fields = ['id', 'name']

class ProviderTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProviderType
        fields = ['id', 'name', 'description', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None

class ServiceStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStyle
        fields = ['id', 'name']
        
class ServiceStylePrivateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStylePrivate
        fields = ['id', 'name']

class CuisineSerializer(serializers.ModelSerializer):
    # Use SerializerMethodField to create the dynamic image URL
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Cuisine
        fields = ['id', 'name', 'image_url', 'budget_options']

    def get_image_url(self, obj):
        request = self.context.get('request')  # Get the request context
        if obj.image and request:
            # Build the absolute URL for the image
            return request.build_absolute_uri(obj.image.url)
        return None
    
    
class CourseSerializer(serializers.ModelSerializer):
    # Add the SerializerMethodField for image_url
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'image_url']  # Include 'image_url' here

    def get_image_url(self, obj):
        request = self.context.get('request')  # Get the request context
        if obj.image and request:
            # Build the absolute URL for the image
            return request.build_absolute_uri(obj.image.url)
        return None

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name']
        
class BudgetOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetOption
        fields = ['id', 'label', 'price_range', 'max_price']

class PaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pax
        fields = ['id', 'label', 'number']

class MenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'image_url', 'course', 'cuisine']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class CoffeeBreakItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CoffeeBreakItem
        fields = ['id', 'name', 'category', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class CoffeeBreakRotationSerializer(serializers.ModelSerializer):
    items = CoffeeBreakItemSerializer(many=True, read_only=True)

    class Meta:
        model = CoffeeBreakRotation
        fields = ['id', 'name', 'items']

class PlatterItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PlatterItem
        fields = ['id', 'name', 'description', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class BoxedMealItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BoxedMealItem
        fields = ['id', 'name', 'category', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class LiveStationItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LiveStationItem
        fields = ['id', 'name', 'price', 'setup', 'ingredients', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

