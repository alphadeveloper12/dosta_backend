from rest_framework import serializers
from .models import (
    VendingLocation,
    UserLocationSelection,
    Menu,
    MenuItem,
    MasterItem,
    Offer,
    PickupTimeSlot,
    Order,
    OrderItem,
    Cart,
    CartItem,
    MealPlan,
    MealPlanItem,
    FavoriteMenuItem,
    resolve_master_price,
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
    image2_url = serializers.SerializerMethodField()
    offers = OfferSerializer(many=True, read_only=True)
    heating = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

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
            'image2_url',
            'offers',
            'heating'
        ]

    def get_price(self, obj):
        loc_id = self.context.get('location_id')
        if getattr(obj, 'master_item', None):
            return str(resolve_master_price(obj.master_item, loc_id))
        return str(obj.price)

    def get_heating(self, obj):
        return "yes" if obj.heating else "no"

    def get_image_url(self, obj):
        request = self.context.get('request')
        target = None
        if obj.image:
            try:
                if obj.image.url: target = obj.image
            except: pass
        if not target and getattr(obj, 'master_item', None) and obj.master_item.image:
            try:
                if obj.master_item.image.url: target = obj.master_item.image
            except: pass
        if target:
            try:
                url = target.url
                if request: return request.build_absolute_uri(url)
                return url
            except: return None
        return None

    def get_image2_url(self, obj):
        """Returns image2 from the linked MasterItem, falling back to image."""
        request = self.context.get('request')
        # Prefer master_item.image2 → master_item.image → obj.image
        master = getattr(obj, 'master_item', None)
        if master and master.image2:
            target = master.image2
        elif master and master.image:
            target = master.image
        else:
            target = obj.image  # fallback to MenuItem's own image

        if target and request:
            return request.build_absolute_uri(target.url)
        elif target:
            return target.url
        return None


class MenuSerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = ['id', 'day_of_week', 'date', 'items']


class MasterItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image2_url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    heating = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()

    class Meta:
        model = MasterItem
        fields = ['id', 'name', 'price', 'description', 'image_url', 'image2_url', 'offers', 'heating', 'maximum_heating']

    def get_price(self, obj):
        loc_id = self.context.get('location_id')
        return str(resolve_master_price(obj, loc_id))

    def get_heating(self, obj):
        return "yes" if obj.heating else "no"

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None

    def get_image2_url(self, obj):
        """Returns image2 URL, falling back to image URL when image2 is not set."""
        request = self.context.get('request')
        # Use image2 if available, otherwise fall back to image
        target = obj.image2 if obj.image2 else obj.image
        if target and request:
            return request.build_absolute_uri(target.url)
        elif target:
            return target.url
        return None

    def get_offers(self, obj):
        return []


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
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'quantity', 'day_of_week', 'week_number', 
            'vending_good_uuid', 'heating_requested', 'status', 'pickup_code',
            'qr_code_url', 'plan_type', 'plan_subtype'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.menu_item and instance.master_item:
            master = instance.master_item
            request = self.context.get('request')
            image_url = None
            if master.image:
                image_url = request.build_absolute_uri(master.image.url) if request else master.image.url
            # image2_url falls back to image_url when image2 is not set
            image2_target = master.image2 if master.image2 else master.image
            image2_url = None
            if image2_target:
                image2_url = request.build_absolute_uri(image2_target.url) if request else image2_target.url
            order_loc_id = instance.order.location_id if instance.order_id else None
            effective_price = instance.item_price_snapshot
            if effective_price is None:
                effective_price = resolve_master_price(master, order_loc_id)
            data['menu_item'] = {
                'id': master.id,
                'name': master.name,
                'price': str(effective_price),
                'description': master.description or '',
                'image_url': image_url,
                'image2_url': image2_url,
                'heating': 'yes' if master.heating else 'no',
                'maximum_heating': master.maximum_heating,
                'offers': []
            }
        elif not instance.menu_item and instance.sweets_item:
            sweets = instance.sweets_item
            variation = instance.sweets_variation
            request = self.context.get('request')
            image_url = None
            image = sweets.image or (sweets.master_item.image if sweets.master_item else None)
            if image:
                image_url = request.build_absolute_uri(image.url) if request else image.url

            name = f"{sweets.name} ({variation.weight})" if variation else sweets.name
            price = str(variation.price) if variation else str(sweets.price)

            data['menu_item'] = {
                'id': sweets.id,
                'name': name,
                'price': price,
                'description': sweets.master_item.description if sweets.master_item else (sweets.description or ''),
                'image_url': image_url,
                'heating': 'no',
                'offers': []
            }
            if variation:
                data['variation_id'] = variation.id
        return data
    def get_qr_code_url(self, obj):
        if obj.pickup_code:
            return f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={obj.pickup_code}"
        return None


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
            'qr_used',
            'fulfillment_attempts',
            'city',
            'delivery_charge',
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.menu_item and instance.master_item:
            master = instance.master_item
            request = self.context.get('request')
            image_url = None
            if master.image:
                image_url = request.build_absolute_uri(master.image.url) if request else master.image.url
            # image2_url falls back to image_url when image2 is not set
            image2_target = master.image2 if master.image2 else master.image
            image2_url = None
            if image2_target:
                image2_url = request.build_absolute_uri(image2_target.url) if request else image2_target.url
            cart_loc_id = instance.cart.location_id if instance.cart_id else None
            effective_price = resolve_master_price(master, cart_loc_id)
            data['menu_item'] = {
                'id': master.id,
                'name': master.name,
                'price': str(effective_price),
                'description': master.description or '',
                'image_url': image_url,
                'image2_url': image2_url,
                'heating': 'yes' if master.heating else 'no',
                'maximum_heating': master.maximum_heating,
                'offers': []
            }
        elif not instance.menu_item and instance.sweets_item:
            sweets = instance.sweets_item
            variation = instance.sweets_variation
            request = self.context.get('request')
            image_url = None
            image = sweets.image or (sweets.master_item.image if sweets.master_item else None)
            if image:
                image_url = request.build_absolute_uri(image.url) if request else image.url

            name = f"{sweets.name} ({variation.weight})" if variation else sweets.name
            price = str(variation.price) if variation else str(sweets.price)

            data['menu_item'] = {
                'id': sweets.id,
                'name': name,
                'price': price,
                'description': sweets.master_item.description if sweets.master_item else (sweets.description or ''),
                'image_url': image_url,
                'heating': 'no',
                'offers': []
            }
            if variation:
                data['variation_id'] = variation.id
        return data


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
            'city',
            'delivery_charge',
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
