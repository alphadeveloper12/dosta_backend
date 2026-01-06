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
    
    def __str__(self):
        return self.name


class ServiceStylePrivate(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class Cuisine(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to='cuisines/')
    
    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to='courses/')
    cuisines = models.ManyToManyField(Cuisine, related_name='courses', blank=True)
    
    def __str__(self):
        return self.name 






class Location(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name


class BudgetOption(models.Model):
    label = models.CharField(max_length=100)  # e.g., "Economy", "Premium", etc.
    price_range = models.CharField(max_length=100)  # e.g., "$500–$1000"
    
    def __str__(self):
        return f"{self.label} ({self.price_range})"


class BudgetOptionPrivate(models.Model):
    label = models.CharField(max_length=100)  # e.g., "Economy", "Premium", etc.
    price_range = models.CharField(max_length=100)  # e.g., "$500–$1000"
    
    def __str__(self):
        return f"{self.label} ({self.price_range})"


class Pax(models.Model):
    label = models.CharField(max_length=100) # e.g., "Small Group"
    number = models.CharField(max_length=100) # e.g., "10-20"
    
    def __str__(self):
        return f"{self.label} ({self.number})"

class PaxPrivate(models.Model):
    label = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.label} ({self.number})"


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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='menu_items')
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE, related_name='menu_items')

    # New M2M fields for budget filtering
    budget_options = models.ManyToManyField(BudgetOption, blank=True, related_name='menu_items')
    budget_options_private = models.ManyToManyField(BudgetOptionPrivate, blank=True, related_name='menu_items')

    def __str__(self):
        return f"{self.name} ({self.cuisine.name} - {self.course.name})"

