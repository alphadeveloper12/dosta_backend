from rest_framework import serializers
from .models import (
    VendingLocation,
    UserLocationSelection,
    Menu,
    MenuItem,
    Offer,
    PickupTimeSlot,
    Order,
    OrderItem,
    Cart,
    CartItem,
    MealPlan,
    MealPlanItem,
    FavoriteMenuItem
)

# -----------------------------------------------------------
# LOCATION SERIALIZERS
# -----------------------------------------------------------

class VendingLocationSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()

    class Meta:
        model = VendingLocation
        fields = ['id', 'name', 'info', 'hours', 'position', 'is_active', 'serial_number']

    def get_position(self, obj):
        return {"lat": float(obj.latitude), "lng": float(obj.longitude)}


class UserLocationSelectionSerializer(serializers.ModelSerializer):
    location = VendingLocationSerializer()

    class Meta:
        model = UserLocationSelection
        fields = ['id', 'location', 'is_selected', 'selected_at']


# -----------------------------------------------------------
# MENU SERIALIZERS
# -----------------------------------------------------------

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['id', 'description', 'valid_until']


class MenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    offers = OfferSerializer(many=True, read_only=True)
    heating = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'price',
            'description',
            'offer',
            'terms_and_conditions',
            'image_url',
            'offers',
            'heating'
        ]

    def get_heating(self, obj):
        return "yes" if obj.heating else "no"

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class MenuSerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = ['id', 'day_of_week', 'date', 'items']


# -----------------------------------------------------------
# PICKUP TIME SLOTS
# -----------------------------------------------------------

class PickupTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupTimeSlot
        fields = ['id', 'label', 'start_time', 'end_time', 'is_active']


# -----------------------------------------------------------
# ORDER SERIALIZERS
# -----------------------------------------------------------

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'quantity', 'day_of_week', 'week_number', 
            'vending_good_uuid', 'heating_requested', 'status', 'pickup_code',
            'plan_type', 'plan_subtype'
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    location = VendingLocationSerializer(read_only=True)
    pickup_slot = PickupTimeSlotSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'location',
            'plan_type',
            'plan_subtype',
            'pickup_type',
            'pickup_date',
            'pickup_slot',
            'status',
            'current_step',
            'total_amount',
            'pickup_code',
            'qr_code_url',
            'items',
            'created_at'
        ]


# -----------------------------------------------------------
# CART SERIALIZERS
# -----------------------------------------------------------

class CartItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'menu_item', 'quantity', 'day_of_week', 'week_number', 
            'subtotal', 'vending_good_uuid', 'plan_type', 'plan_subtype',
            'pickup_type', 'pickup_date', 'pickup_slot', 'heating_requested'
        ]

    def get_subtotal(self, obj):
        return obj.subtotal


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    location = VendingLocationSerializer(read_only=True)
    pickup_slot = PickupTimeSlotSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 
            'location',
            'plan_type',
            'plan_subtype',
            'pickup_type',
            'pickup_date',
            'pickup_slot',
            'total_price', 
            'current_step',
            'is_checked_out', 
            'created_at', 
            'updated_at', 
            'items'
        ]


# -----------------------------------------------------------
# MEAL PLAN SERIALIZERS
# -----------------------------------------------------------

class MealPlanItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer()

    class Meta:
        model = MealPlanItem
        fields = ['id', 'menu_item', 'quantity', 'day_of_week', 'week_number']


class MealPlanSerializer(serializers.ModelSerializer):
    items = MealPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlan
        fields = ['id', 'name', 'kind', 'is_default', 'is_global', 'items']


# -----------------------------------------------------------
# FAVORITES
# -----------------------------------------------------------

class FavoriteMenuItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer()

    class Meta:
        model = FavoriteMenuItem
        fields = ['id', 'menu_item', 'created_at']
