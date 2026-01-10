from django.db import models
from django.contrib.auth.models import User

# ========== ADMIN-SIDE MODELS (Dynamic Options) ==========

class EventType(models.Model):
    name = models.CharField(max_length=100)
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
    
    def __str__(self):
        return f"{self.label} ({self.number})"



class FixedCateringMenu(models.Model):
    name = models.CharField(max_length=200)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE, related_name='fixed_menus')
    budget_option = models.ForeignKey(BudgetOption, on_delete=models.CASCADE, related_name='fixed_menus')
    courses = models.ManyToManyField(Course, related_name='fixed_menus', blank=True)
    items = models.ManyToManyField('MenuItem', related_name='fixed_menus', blank=True)

    def __str__(self):
        return f"{self.name} - {self.cuisine.name} ({self.budget_option.label})"

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
    
    def __str__(self):
        return self.name

class CoffeeBreakItem(models.Model):
    rotation = models.ForeignKey(CoffeeBreakRotation, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100) # Salads, Sandwiches, etc.
    image = models.FileField(upload_to='coffee_break/', blank=True)
    
    def __str__(self):
        return self.name

class PlatterItem(models.Model):
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
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.FileField(upload_to='boxed_meals/', blank=True)
    
    def __str__(self):
        return self.name

class LiveStationItem(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Per Person
    setup = models.TextField()
    ingredients = models.TextField()
    image = models.FileField(upload_to='live_stations/', blank=True)
    
    def __str__(self):
        return self.name

class AmericanMenu(models.Model):
    name = models.CharField(max_length=100) # e.g., "Buffet Menu 1: Southern Comfort"
    
    def __str__(self):
        return self.name

class AmericanMenuItem(models.Model):
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
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.FileField(upload_to='canapes/', blank=True)

    def __str__(self):
        return self.name
