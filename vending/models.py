from django.db import models
from django.conf import settings

# -----------------------------------------------------------
# ENUMS / CHOICES
# -----------------------------------------------------------

class DayOfWeek(models.TextChoices):
    MONDAY = 'Monday', 'Monday'
    TUESDAY = 'Tuesday', 'Tuesday'
    WEDNESDAY = 'Wednesday', 'Wednesday'
    THURSDAY = 'Thursday', 'Thursday'
    FRIDAY = 'Friday', 'Friday'
    SATURDAY = 'Saturday', 'Saturday'
    SUNDAY = 'Sunday', 'Sunday'


class PlanType(models.TextChoices):
    ORDER_NOW = "ORDER_NOW", "Order now"
    START_PLAN = "START_PLAN", "Start a plan"
    SMART_GRAB = "SMART_GRAB", "Smart grab"


class PlanSubType(models.TextChoices):
    NONE = "NONE", "None"
    WEEKLY = "WEEKLY", "Weekly"
    MONTHLY = "MONTHLY", "Monthly"


class PickupType(models.TextChoices):
    TODAY = "TODAY", "Pickup today"
    IN_24_HOURS = "IN_24_HOURS", "Pickup in 24 hours"


class OrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    PREPARING = "PREPARING", "Preparing"
    READY = "READY", "Ready"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


# -----------------------------------------------------------
# MENU MODELS
# -----------------------------------------------------------

class Menu(models.Model):
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)
    week_number = models.PositiveSmallIntegerField(default=1, help_text="Week number (1-4) for monthly rotation")
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Week {self.week_number} - {self.day_of_week}"


class MasterItem(models.Model):
    """
    Unique representation of an item, independent of menu scheduling.
    Used to normalize data so updates (name, macros, image) propagate.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    calories = models.PositiveIntegerField(default=0, help_text="kcal")
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="grams")
    carbs = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="grams")
    fats = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="grams")
    heating = models.BooleanField(default=False)
    image_source_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    menu = models.ForeignKey(Menu, related_name='items', on_delete=models.CASCADE)
    master_item = models.ForeignKey(MasterItem, related_name='menu_items', on_delete=models.PROTECT, null=True, blank=True)
    
    # Denormalized fields (kept for backward compatibility with existing views/scripts)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    ingredients = models.TextField(blank=True, null=True)
    calories = models.PositiveIntegerField(default=0, help_text="kcal")
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="grams")
    carbs = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="grams")
    fats = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="grams")
    offer = models.CharField(max_length=255, blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    heating = models.BooleanField(default=False)
    image_source_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='menu_images/')

    def __str__(self):
        return self.name


class Offer(models.Model):
    menu_item = models.ForeignKey(MenuItem, related_name='offers', on_delete=models.CASCADE)
    description = models.TextField()
    valid_until = models.DateTimeField()

    def __str__(self):
        return f"Offer for {self.menu_item.name}"


# -----------------------------------------------------------
# VENDING LOCATOR
# -----------------------------------------------------------

class VendingLocation(models.Model):
    name = models.CharField(max_length=255)
    info = models.CharField(max_length=255)
    hours = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def position(self):
        return {"lat": float(self.latitude), "lng": float(self.longitude)}


class UserLocationSelection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="vending_location_selections", on_delete=models.CASCADE)
    location = models.ForeignKey(VendingLocation, related_name="user_selections", on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=True)
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "location")

    def __str__(self):
        status = "selected" if self.is_selected else "unselected"
        return f"{self.user} - {self.location.name} ({status})"


# -----------------------------------------------------------
# PICKUP SLOTS
# -----------------------------------------------------------

class PickupTimeSlot(models.Model):
    label = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey(VendingLocation, related_name="pickup_slots", on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.label


# -----------------------------------------------------------
# ORDER SYSTEM
# -----------------------------------------------------------

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    location = models.ForeignKey(VendingLocation, related_name="orders", on_delete=models.PROTECT)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    plan_subtype = models.CharField(max_length=20, choices=PlanSubType.choices, default=PlanSubType.NONE)
    pickup_type = models.CharField(max_length=20, choices=PickupType.choices, null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    pickup_slot = models.ForeignKey(PickupTimeSlot, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    current_step = models.PositiveSmallIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pickup_code = models.CharField(max_length=50, blank=True, null=True)
    qr_code_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"

    @property
    def is_weekly(self):
        return self.plan_subtype == PlanSubType.WEEKLY

    @property
    def is_monthly(self):
        return self.plan_subtype == PlanSubType.MONTHLY

    @property
    def is_single_day(self):
        return self.plan_type in [PlanType.ORDER_NOW, PlanType.SMART_GRAB]

    def update_total(self):
        total = sum(item.menu_item.price * item.quantity for item in self.items.select_related('menu_item'))
        self.total_amount = total
        self.save(update_fields=["total_amount"])

    @property
    def kitchen_items(self):
        """Returns items that require kitchen preparation and aren't fulfilled yet."""
        return self.items.filter(plan_type__in=['START_PLAN', 'ORDER_NOW', 'SMART_GRAB'], pickup_code__isnull=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name="order_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices, null=True, blank=True)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)
    vending_good_uuid = models.CharField(max_length=255, null=True, blank=True) # NEW: Vending Good UUID
    heating_requested = models.BooleanField(default=False, null=True, blank=True)
    
    # Plan Context (Moved to Item level for mixed carts)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices, default=PlanType.ORDER_NOW)
    plan_subtype = models.CharField(max_length=20, choices=PlanSubType.choices, default=PlanSubType.NONE)
    pickup_type = models.CharField(max_length=20, choices=PickupType.choices, null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    pickup_slot = models.ForeignKey(PickupTimeSlot, related_name="order_items", on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, null=True, blank=True)
    pickup_code = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["order", "week_number", "day_of_week"])]

    def __str__(self):
        base = f"{self.menu_item.name} x {self.quantity}"
        if self.week_number:
            return f"{base} (Week {self.week_number}, {self.day_of_week})"
        if self.day_of_week:
            return f"{base} ({self.day_of_week})"
        return base

    @property
    def week_day_display(self):
        """Helper to display 'Week X - Day' or just 'Day'."""
        if self.week_number and self.day_of_week:
            return f"Week {self.week_number} - {self.day_of_week}"
        return self.day_of_week or ""


# -----------------------------------------------------------
# CART SYSTEM
# -----------------------------------------------------------

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="cart", on_delete=models.CASCADE)
    location = models.ForeignKey(VendingLocation, related_name="cart_items", on_delete=models.SET_NULL, null=True, blank=True)
    
    # Context fields (same as Order)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices, default=PlanType.ORDER_NOW)
    plan_subtype = models.CharField(max_length=20, choices=PlanSubType.choices, default=PlanSubType.NONE)
    pickup_type = models.CharField(max_length=20, choices=PickupType.choices, null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    pickup_slot = models.ForeignKey(PickupTimeSlot, related_name="carts", on_delete=models.SET_NULL, null=True, blank=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_step = models.PositiveSmallIntegerField(default=1)
    is_checked_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def update_total(self):
        total = sum(item.menu_item.price * item.quantity for item in self.items.select_related('menu_item'))
        self.total_price = total
        self.save(update_fields=["total_price"])


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name="cart_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    
    # Item context (for weekly/monthly plans)
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices, null=True, blank=True)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)
    vending_good_uuid = models.CharField(max_length=255, null=True, blank=True) # NEW: Vending Good UUID
    heating_requested = models.BooleanField(default=False, null=True, blank=True)
    
    # Plan Context (Moved to Item level for mixed carts)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices, default=PlanType.ORDER_NOW)
    plan_subtype = models.CharField(max_length=20, choices=PlanSubType.choices, default=PlanSubType.NONE)
    pickup_type = models.CharField(max_length=20, choices=PickupType.choices, null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    pickup_slot = models.ForeignKey(PickupTimeSlot, related_name="cart_items_context", on_delete=models.SET_NULL, null=True, blank=True)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "menu_item", "plan_type", "plan_subtype", "day_of_week", "week_number")

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity


# -----------------------------------------------------------
# SAVED MEAL PLANS (Weekly / Monthly)
# -----------------------------------------------------------

class MealPlan(models.Model):
    class PlanKind(models.TextChoices):
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="meal_plans", on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=PlanKind.choices)
    location = models.ForeignKey(VendingLocation, related_name="meal_plans", on_delete=models.CASCADE, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        scope = "Global" if self.is_global else f"{self.user}"
        return f"{self.name} ({self.kind}) [{scope}]"


class MealPlanItem(models.Model):
    meal_plan = models.ForeignKey(MealPlan, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name="meal_plan_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices, null=True, blank=True)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.meal_plan.name}: {self.menu_item.name} x {self.quantity}"


# -----------------------------------------------------------
# FAVORITES (Select Your Favourites)
# -----------------------------------------------------------

class FavoriteMenuItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="favorite_menu_items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name="favorited_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "menu_item")

    def __str__(self):
        return f"{self.user} ❤️ {self.menu_item.name}"

# -----------------------------------------------------------
# VENDING MACHINE STOCK
# -----------------------------------------------------------

class VendingMachineStock(models.Model):
    vending_good_uuid = models.CharField(max_length=255, unique=True)
    goods_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.goods_name} ({self.quantity})"

# -----------------------------------------------------------
# SIGNALS FOR DATA SYNC
# -----------------------------------------------------------

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(post_save, sender=MasterItem)
def propagate_master_changes(sender, instance, created, **kwargs):
    """
    When MasterItem is updated (e.g. fixed typo in name), 
    update all linked MenuItem instances to match.
    """
    if created:
        return # New item, no children to update yet
        
    instance.menu_items.update(
        name=instance.name,
        description=instance.description,
        ingredients=instance.ingredients,
        calories=instance.calories,
        protein=instance.protein,
        carbs=instance.carbs,
        fats=instance.fats,
        heating=instance.heating,
        # We don't necessarily overwrite image/source_url if they are blank in Master
        # but for full sync we often should. Let's do partial updates if not blank.
    )

    # Handle nullable fields cleaner
    if instance.image:
        instance.menu_items.update(image=instance.image)
    if instance.image_source_url:
        instance.menu_items.update(image_source_url=instance.image_source_url)


@receiver(pre_save, sender=MenuItem)
def link_or_create_master_item(sender, instance, **kwargs):
    """
    When a MenuItem is about to be saved:
    1. If it has no MasterItem, try to find one by name.
    2. If found, link it and sync data FROM Master TO Item (Master is source of truth).
    3. If not found, create a new MasterItem using this Item's data.
    4. If it has a MasterItem, ensure the Item's data matches the Master (prevent divergence).
    """
    if not instance.name:
        return

    # Normalize name for lookup
    clean_name = instance.name.strip()
    
    if not instance.master_item:
        # Try to find existing
        master = MasterItem.objects.filter(name__iexact=clean_name).first()
        if master:
            instance.master_item = master
            # Sync to match Master
            instance.name = master.name
            instance.description = master.description or instance.description
            instance.ingredients = master.ingredients or instance.ingredients
            instance.calories = master.calories if master.calories > 0 else instance.calories
            # ... sync other fields if needed, but 'name' is most critical
        else:
            # Create new Master (Auto-creation strategy)
            # Only if this seems to be a valid item (has price etc)
            master = MasterItem.objects.create(
                name=clean_name,
                description=instance.description,
                ingredients=instance.ingredients,
                calories=instance.calories,
                protein=instance.protein,
                carbs=instance.carbs,
                fats=instance.fats,
                heating=instance.heating,
                image=instance.image,
                image_source_url=instance.image_source_url
            )
            instance.master_item = master
    
    # If already linked (or just linked above), ensure compliance
    # This enforces "Master Name rules all"
    if instance.master_item:
        if instance.name != instance.master_item.name:
             instance.name = instance.master_item.name

