from rest_framework import serializers
from .models import *

class EventTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = EventType
        fields = ['id', 'name', 'description', 'image_url']

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
        fields = ['id', 'name', 'description', 'min_pax']
        
class ServiceStylePrivateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStylePrivate
        fields = ['id', 'name', 'min_pax']

class ServiceStylePrivateChefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStylePrivateChef
        fields = ['id', 'name', 'description', 'min_pax']

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
        fields = ['id', 'name', 'description', 'items']


# ========== CATERING ORDER SERIALIZERS ==========

class CateringOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CateringOrderItem
        fields = ['id', 'name', 'course', 'quantity', 'price', 'description']

class CateringOrderSerializer(serializers.ModelSerializer):
    items = CateringOrderItemSerializer(many=True)

    class Meta:
        model = CateringOrder
        fields = [
            'id', 'order_id', 'user', 'status', 
            'event_type', 'guest_count', 'event_date', 'event_time',
            'provider_type', 'service_style', 'location', 
            'total_amount', 'created_at', 'items'
        ]
        read_only_fields = ['order_id', 'user', 'created_at', 'status']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Check for payment verification flag in the initial data (from request)
        is_paid = self.initial_data.get('is_payment_verified') is True or \
                  self.initial_data.get('is_payment_verified') == 'true'
                  
        status_val = CateringOrderStatus.CONFIRMED if is_paid else CateringOrderStatus.PENDING
        
        order = CateringOrder.objects.create(
            user=user, 
            status=status_val,
            **validated_data
        )
        
        for item_data in items_data:
            CateringOrderItem.objects.create(order=order, **item_data)
            
        return order

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
        fields = ['id', 'name', 'description', 'price', 'setup', 'ingredients', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class FixedCateringMenuSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    items = MenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = FixedCateringMenu
        fields = ['id', 'name', 'cuisine', 'budget_option', 'courses', 'items']


class AmericanMenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AmericanMenuItem
        fields = ['id', 'name', 'description', 'category', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class AmericanMenuSerializer(serializers.ModelSerializer):
    items = AmericanMenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = AmericanMenu
        fields = ['id', 'name', 'items']

class CanapeItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CanapeItem
        fields = ['id', 'name', 'description', 'category', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class SweetsItemVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SweetsItemVariation
        fields = ['id', 'weight', 'price']

class SweetsItemImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SweetsItemImage
        fields = ['id', 'image_url', 'alt_text', 'order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class SweetsItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    images = SweetsItemImageSerializer(many=True, read_only=True)
    variations = SweetsItemVariationSerializer(many=True, read_only=True)

    class Meta:
        model = SweetsItem
        fields = ['id', 'name', 'description', 'price', 'image_url', 'images', 'variations']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ========== BEIT NAHLA SERIALIZERS ==========

class BeitNahlaDistanceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeitNahlaDistanceTier
        fields = ['id', 'label', 'min_km', 'max_km', 'service_charge', 'delivery_charge']


class BeitNahlaSettingsSerializer(serializers.ModelSerializer):
    tiers = serializers.SerializerMethodField()

    class Meta:
        model = BeitNahlaSettings
        fields = [
            'order_now_price', 'weekly_price',
            'restaurant_name', 'restaurant_latitude', 'restaurant_longitude',
            'max_deliverable_km',
            'opening_time', 'closing_time',
            'tiers',
        ]

    def get_tiers(self, obj):
        tiers = BeitNahlaDistanceTier.objects.filter(is_active=True).order_by('min_km')
        return BeitNahlaDistanceTierSerializer(tiers, many=True).data


class BeitNahlaMealBoxImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BeitNahlaMealBoxImage
        fields = ['id', 'image_url', 'alt_text', 'order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        if obj.image:
            return obj.image.url
        return None


class BeitNahlaMealBoxSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    images = BeitNahlaMealBoxImageSerializer(many=True, read_only=True)

    class Meta:
        model = BeitNahlaMealBox
        fields = ['id', 'name', 'description', 'image_url', 'images', 'display_order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        if obj.image:
            return obj.image.url
        return None


class BeitNahlaOptionItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BeitNahlaOptionItem
        fields = ['id', 'name', 'description', 'image_url', 'display_order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        if obj.image:
            return obj.image.url
        return None


class BeitNahlaOptionCategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = BeitNahlaOptionCategory
        fields = ['id', 'name', 'description', 'display_order', 'items']

    def get_items(self, obj):
        items = obj.items.filter(is_active=True).order_by('display_order', 'name')
        return BeitNahlaOptionItemSerializer(items, many=True, context=self.context).data


# ========== RAMADAN MENU SERIALIZERS ==========

class RamadanMenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    master_item_name = serializers.CharField(source='master_item.name', read_only=True)
    
    class Meta:
        model = RamadanMenuItem
        fields = ['id', 'master_item', 'master_item_name', 'name', 'description', 'image_url', 'quantity', 'display_order']
        read_only_fields = ['name', 'description', 'image_url']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        image = obj.image
        if not image and obj.master_item:
            image = obj.master_item.image
            
        if image and request:
            return request.build_absolute_uri(image.url)
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get('name') and instance.master_item:
            data['name'] = instance.master_item.name
        if not data.get('description') and instance.master_item:
            data['description'] = instance.master_item.description
        return data



class RamadanMenuCourseSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_image_url = serializers.SerializerMethodField()
    items = RamadanMenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = RamadanMenuCourse
        fields = ['id', 'course', 'course_name', 'course_image_url', 'display_order', 'items']
    
    def get_course_image_url(self, obj):
        request = self.context.get('request')
        if obj.course.image and request:
            return request.build_absolute_uri(obj.course.image.url)
        return None


class RamadanMenuSerializer(serializers.ModelSerializer):
    service_style_name = serializers.CharField(source='service_style.name', read_only=True)
    budget_option_label = serializers.CharField(source='budget_option.label', read_only=True)
    budget_option_price_range = serializers.CharField(source='budget_option.price_range', read_only=True)
    menu_courses = RamadanMenuCourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = RamadanMenu
        fields = [
            'id', 'name', 'description', 'service_style', 'service_style_name',
            'budget_option', 'budget_option_label', 'budget_option_price_range',
            'is_active', 'created_at', 'updated_at', 'menu_courses'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RamadanMenuListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views without nested courses/items"""
    service_style_name = serializers.CharField(source='service_style.name', read_only=True)
    budget_option_label = serializers.CharField(source='budget_option.label', read_only=True)
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RamadanMenu
        fields = [
            'id', 'name', 'service_style', 'service_style_name',
            'budget_option', 'budget_option_label',
            'is_active', 'courses_count', 'created_at'
        ]
    
    def get_courses_count(self, obj):
        return obj.menu_courses.count()

# ========== IFTAR BOX MENU SERIALIZERS ==========

class IftarBoxMenuSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    budget_option = BudgetOptionSerializer(read_only=True)

    class Meta:
        model = IftarBoxMenu
        fields = ['id', 'name', 'budget_option', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None



