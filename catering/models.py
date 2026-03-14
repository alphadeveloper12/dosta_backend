from django.db import models
from django.contrib.auth.models import User

# ========== ADMIN-SIDE MODELS (Dynamic Options) ==========

class EventType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to='event_types/')
    
    def __str__(self):
        return self.name



class EventName(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class ProviderType(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to='providers/', blank=True, null=True)  # ✅ allows SVG
    description = models.CharField(max_length=100, blank=True, null=True)  # ✅ short sentence field

    def __str__(self):
        return self.name



class ServiceStyle(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default="Dummy description") # Added description
    min_pax = models.PositiveIntegerField(default=0)
    cuisines = models.ManyToManyField('Cuisine', blank=True, related_name='service_styles')
    budget_options = models.ManyToManyField('BudgetOption', blank=True, related_name='service_styles')
    
    def __str__(self):
        return self.name


class ServiceStylePrivate(models.Model):
    name = models.CharField(max_length=100)
    min_pax = models.PositiveIntegerField(default=0)
    cuisines = models.ManyToManyField('Cuisine', blank=True, related_name='service_styles_private')
    budget_options = models.ManyToManyField('BudgetOption', blank=True, related_name='service_styles_private')
    
    def __str__(self):
        return self.name


class ServiceStylePrivateChef(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default="Dummy description")
    min_pax = models.PositiveIntegerField(default=0)
    cuisines = models.ManyToManyField('Cuisine', blank=True, related_name='service_styles_private_chef')
    budget_options = models.ManyToManyField('BudgetOption', blank=True, related_name='service_styles_private_chef')
    
    def __str__(self):
        return self.name


class Cuisine(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to='cuisines/')
    budget_options = models.ManyToManyField('BudgetOption', blank=True, related_name='cuisines')
    
    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to='courses/')
    cuisines = models.ManyToManyField(Cuisine, related_name='courses', blank=True)
    budget_options = models.ManyToManyField('BudgetOption', related_name='courses', blank=True)
    
    def __str__(self):
        return self.name 






class Location(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name


class BudgetOption(models.Model):
    label = models.CharField(max_length=100)  # e.g., "Economy", "Premium", etc.
    price_range = models.CharField(max_length=100)  # e.g., "$500–$1000"
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.label} ({self.price_range})"


class Pax(models.Model):
    label = models.CharField(max_length=100) # e.g., "Small Group"
    number = models.CharField(max_length=100) # e.g., "10-20"
    service_styles = models.ManyToManyField(ServiceStyle, blank=True, related_name='pax_options')
    service_styles_private = models.ManyToManyField('ServiceStylePrivate', blank=True, related_name='pax_options')
    service_styles_private_chef = models.ManyToManyField('ServiceStylePrivateChef', blank=True, related_name='pax_options')
    
    def __str__(self):
        return f"{self.label} ({self.number})"



class FixedCateringMenu(models.Model):
    name = models.CharField(max_length=200)
    # description field removed per refactor
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE, related_name='fixed_menus')
    budget_option = models.ForeignKey(BudgetOption, on_delete=models.CASCADE, related_name='fixed_menus')
    courses = models.ManyToManyField(Course, related_name='fixed_menus', blank=True)
    items = models.ManyToManyField('MenuItem', related_name='fixed_menus', blank=True)

    def __str__(self):
        return f"{self.name} - {self.cuisine.name} ({self.budget_option.label})"

class CateringMasterItem(models.Model):
    """
    Unified Master Item for all Catering services.
    "Change once, update everywhere."
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to='master_catering_images/', blank=True, null=True)
    
    # Nutritional / Extra info could be added here later
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ========== USER-SIDE MODEL (Catering Planning Form) ==========

class CateringPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='catering_plans')
    
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True)
    guest_count = models.PositiveIntegerField()
    event_date = models.DateField()
    event_time = models.TimeField()
    
    provider_type = models.ForeignKey(ProviderType, on_delete=models.SET_NULL, null=True)
    service_styles = models.ManyToManyField(ServiceStyle, blank=True)
    cuisines = models.ManyToManyField(Cuisine, blank=True)
    courses = models.ManyToManyField(Course, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    budget = models.ForeignKey(BudgetOption, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} - {self.event_type.name if self.event_type else 'No Event'}"


class MenuItem(models.Model):
    master_item = models.ForeignKey(CateringMasterItem, related_name='menu_items', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to='menu_items/', blank=True, null=True)
    # price removed, using MenuItemPrice model
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='menu_items')
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE, related_name='menu_items')
    budget_options = models.ManyToManyField(BudgetOption, blank=True, related_name='menu_items')

    def __str__(self):
        return self.name




class CoffeeBreakRotation(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default="Dummy description")
    
    def __str__(self):
        return self.name

class CoffeeBreakItem(models.Model):
    master_item = models.ForeignKey(CateringMasterItem, related_name='coffee_items', on_delete=models.PROTECT, null=True, blank=True)
    rotation = models.ForeignKey(CoffeeBreakRotation, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100) # Salads, Sandwiches, etc.
    image = models.FileField(upload_to='coffee_break/', blank=True)
    
    def __str__(self):
        return self.name

class PlatterItem(models.Model):
    master_item = models.ForeignKey(CateringMasterItem, related_name='platter_items', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to='platter_items/', blank=True)
    
    def __str__(self):
        return self.name

class BoxedMealItem(models.Model):
    CATEGORY_CHOICES = [
        ('Salads', 'Salads'),
        ('Soup', 'Soup'),
        ('Mains', 'Mains'),
        ('Soft Drink', 'Soft Drink'),
    ]
    master_item = models.ForeignKey(CateringMasterItem, related_name='boxed_items', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.FileField(upload_to='boxed_meals/', blank=True)
    
    def __str__(self):
        return self.name

class LiveStationItem(models.Model):
    master_item = models.ForeignKey(CateringMasterItem, related_name='live_station_items', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, default="Dummy description")
    price = models.DecimalField(max_digits=10, decimal_places=2) # Per Person
    setup = models.TextField()
    ingredients = models.TextField()
    image = models.FileField(upload_to='live_stations/', blank=True)
    
    def __str__(self):
        return self.name

class AmericanMenu(models.Model):
    name = models.CharField(max_length=100) # e.g., "Buffet Menu 1: Southern Comfort"
    # description field removed per refactor
    
    def __str__(self):
        return self.name

class AmericanMenuItem(models.Model):
    master_item = models.ForeignKey(CateringMasterItem, related_name='american_items', on_delete=models.PROTECT, null=True, blank=True)
    menu = models.ForeignKey(AmericanMenu, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100) # Starters, Salads, Main Dishes, Sides, Desserts
    image = models.FileField(upload_to='american_menus/', blank=True)
    
    def __str__(self):
        return self.name

class CanapeItem(models.Model):
    CATEGORY_CHOICES = [
        ('Cold', 'Cold Canapes'),
        ('Hot', 'Hot Canapes'),
        ('Arabic', 'Arabic Canapes'),
        ('Sweet', 'Sweet Canapes'),
        ('Vegetarian', 'Vegetarian Canapes'),
        ('Cold Beverages', 'Cold Beverages'),
        ('Hot Beverages', 'Hot Beverages'),
    ]
    master_item = models.ForeignKey(CateringMasterItem, related_name='canape_items', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.FileField(upload_to='canapes/', blank=True)

    def __str__(self):
        return self.name

class SweetsItem(models.Model):
    master_item = models.ForeignKey(CateringMasterItem, related_name='sweets_items', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, default="Dummy description")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.FileField(upload_to='sweets_items/', blank=True)
    
    def __str__(self):
        return self.name

class SweetsItemImage(models.Model):
    sweets_item = models.ForeignKey(SweetsItem, related_name='images', on_delete=models.CASCADE)
    image = models.FileField(upload_to='sweets_items/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.sweets_item.name} - Image {self.order}"

class SweetsItemVariation(models.Model):
    sweets_item = models.ForeignKey(SweetsItem, related_name='variations', on_delete=models.CASCADE)
    weight = models.CharField(max_length=50, help_text="e.g., 1kg, 0.5kg, 250g")
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.sweets_item.name} - {self.weight} ({self.price} AED)"

# ========== RAMADAN MENU SYSTEM (Iftar & Sohour) ==========

class RamadanMenu(models.Model):
    """
    Dynamic menu for Ramadan service styles (Iftar Menu, Sohour Menu).
    Each menu is linked to a specific service style and budget option.
    Multiple menus can exist for the same service style/budget combination.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    service_style = models.ForeignKey(
        ServiceStyle, 
        on_delete=models.CASCADE, 
        related_name='ramadan_menus',
        help_text="Select Iftar Menu or Sohour Menu"
    )
    budget_option = models.ForeignKey(
        BudgetOption, 
        on_delete=models.CASCADE, 
        related_name='ramadan_menus'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['service_style', 'budget_option', 'name']
        verbose_name = 'Ramadan Menu'
        verbose_name_plural = 'Ramadan Menus'
    
    def __str__(self):
        return f"{self.name} - {self.service_style.name} ({self.budget_option.label})"


class RamadanMenuCourse(models.Model):
    """
    Junction table linking a RamadanMenu to Courses.
    Allows ordering of courses within a menu.
    """
    menu = models.ForeignKey(
        RamadanMenu, 
        on_delete=models.CASCADE, 
        related_name='menu_courses'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='ramadan_menu_courses'
    )
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['menu', 'display_order', 'course']
        unique_together = ['menu', 'course']
        verbose_name = 'Ramadan Menu Course'
        verbose_name_plural = 'Ramadan Menu Courses'
    
    def __str__(self):
        return f"{self.menu.name} - {self.course.name}"


class RamadanMenuItem(models.Model):
    """
    Links catering master items to courses within a Ramadan menu.
    Allows multiple items per course with ordering.
    """
    menu_course = models.ForeignKey(
        RamadanMenuCourse, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    master_item = models.ForeignKey(
        CateringMasterItem, 
        on_delete=models.PROTECT, 
        related_name='ramadan_menu_items'
    )
    name = models.CharField(max_length=200)  # Synced from master_item
    description = models.TextField(blank=True, null=True)  # Synced from master_item
    image = models.FileField(upload_to='ramadan_menu_items/', blank=True, null=True)  # Synced from master_item
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Number of servings or pieces"
    )
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['menu_course', 'display_order', 'name']
        verbose_name = 'Ramadan Menu Item'
        verbose_name_plural = 'Ramadan Menu Items'
    
    def __str__(self):
        return f"{self.name} ({self.menu_course.menu.name})"


# ========== ORDER SYSTEM ==========

class CateringOrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PREPARING = 'PREPARING', 'Preparing'
    READY = 'READY', 'Ready'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class CateringOrder(models.Model):
    order_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='catering_orders')
    status = models.CharField(max_length=20, choices=CateringOrderStatus.choices, default=CateringOrderStatus.PENDING)
    
    # Snapshot of Event Details
    event_type = models.CharField(max_length=100)
    guest_count = models.PositiveIntegerField()
    event_date = models.DateField()
    event_time = models.TimeField()
    provider_type = models.CharField(max_length=100, blank=True, null=True)
    service_style = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            import uuid
            self.order_id = f"CAT-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.user.username}"

class CateringOrderItem(models.Model):
    order = models.ForeignKey(CateringOrder, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    course = models.CharField(max_length=100) # e.g. "Main Course", "Starter", "Live Station"
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} x {self.quantity} ({self.order.order_id})"

# -----------------------------------------------------------
# CATERING SIGNALS
# -----------------------------------------------------------
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# 1. Update CHILDREN when MASTER changes
@receiver(post_save, sender=CateringMasterItem)
def propagate_catering_master_changes(sender, instance, created, **kwargs):
    if created: return

    # Helper to update fields if they exist on the child model
    def update_children(files_queryset):
        if not files_queryset.exists():
            return
            
        model = files_queryset.model
        updates = {'name': instance.name}
        
        # Only update description if the model has it
        if any(f.name == 'description' for f in model._meta.fields):
            updates['description'] = instance.description
            
        # Only update image if the model has it and master has one
        if instance.image and any(f.name == 'image' for f in model._meta.fields):
            updates['image'] = instance.image
            
        files_queryset.update(**updates)

    update_children(instance.menu_items.all())
    update_children(instance.coffee_items.all())
    # ... rest is same
    update_children(instance.platter_items.all())
    update_children(instance.boxed_items.all())
    update_children(instance.live_station_items.all())
    update_children(instance.american_items.all())
    update_children(instance.canape_items.all())
    update_children(instance.ramadan_menu_items.all())
    update_children(instance.sweets_items.all())


# 2. Link/Create MASTER when CHILD is saved
# We need a generic handler or one for each model. One for each is safer/clearer.

def generic_link_catering_master(instance):
    if not instance.name: return
    clean_name = instance.name.strip()
    
    if not instance.master_item:
        master = CateringMasterItem.objects.filter(name__iexact=clean_name).first()
        if master:
            instance.master_item = master
            instance.name = master.name
            if hasattr(instance, 'description'):
                instance.description = master.description or instance.description
        else:
            # Create new Master
            desc = getattr(instance, 'description', '')
            img = getattr(instance, 'image', None)
            master = CateringMasterItem.objects.create(
                name=clean_name,
                description=desc,
                image=img
            )
            instance.master_item = master
            
    # Sync if linked
    if instance.master_item and instance.name != instance.master_item.name:
        instance.name = instance.master_item.name

@receiver(pre_save, sender=MenuItem)
def link_menu_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=CoffeeBreakItem)
def link_coffee_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=PlatterItem)
def link_platter_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=BoxedMealItem)
def link_boxed_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=LiveStationItem)
def link_live_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=AmericanMenuItem)
def link_american_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=CanapeItem)
def link_canape_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=RamadanMenuItem)
def link_ramadan_menu_item(sender, instance, **kwargs): generic_link_catering_master(instance)

@receiver(pre_save, sender=SweetsItem)
def link_sweets_item(sender, instance, **kwargs): generic_link_catering_master(instance)

# ========== IFTAR BOXES MENU SYSTEM ==========

class IftarBoxMenu(models.Model):
    """
    Menu for Iftar Boxes service style.
    Each menu is linked to a budget option and specifies an image only.
    """
    name = models.CharField(max_length=200, blank=True, null=True, help_text="Optional name for this Iftar Box Menu")
    budget_option = models.ForeignKey(
        BudgetOption, 
        on_delete=models.CASCADE, 
        related_name='iftar_box_menus'
    )
    image = models.FileField(upload_to='iftar_box_menus/', help_text="Upload the image containing the Iftar Box Menu")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['budget_option', 'name']
        verbose_name = 'Iftar Box Menu'
        verbose_name_plural = 'Iftar Box Menus'
    
    def __str__(self):
        return f"{self.name or 'Iftar Box Menu'} - {self.budget_option.label}"
