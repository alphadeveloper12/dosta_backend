from django.contrib import admin
from .models import (
    EventType, EventName, ProviderType, ServiceStyle, ServiceStylePrivate, Cuisine,
    Course, MenuItem, Location, BudgetOption, Pax, CateringPlan,
    CoffeeBreakRotation, CoffeeBreakItem, PlatterItem, BoxedMealItem, LiveStationItem,
    FixedCateringMenu, AmericanMenu, AmericanMenuItem
)

# Helper to safely register/unregister
def safe_register(model, admin_class):
    if admin.site.is_registered(model):
        admin.site.unregister(model)
    admin.site.register(model, admin_class)

# ...

class AmericanMenuItemInline(admin.TabularInline):
    model = AmericanMenuItem
    extra = 1

class AmericanMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    inlines = [AmericanMenuItemInline]
safe_register(AmericanMenu, AmericanMenuAdmin)

class AmericanMenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'menu')
    list_filter = ('menu', 'category')
    search_fields = ('name',)
safe_register(AmericanMenuItem, AmericanMenuItemAdmin)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'course')
    list_filter = ('cuisine', 'course')
    search_fields = ('name',)
    filter_horizontal = ('budget_options',)

class CateringPlanServiceStyleInline(admin.TabularInline):
    model = CateringPlan.service_styles.through
    extra = 1

class CateringPlanCuisineInline(admin.TabularInline):
    model = CateringPlan.cuisines.through
    extra = 1

class CateringPlanCourseInline(admin.TabularInline):
    model = CateringPlan.courses.through
    extra = 1

@admin.register(FixedCateringMenu)
class FixedCateringMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'budget_option', 'description')
    list_filter = ('cuisine', 'budget_option')
    filter_horizontal = ('courses', 'items')
    search_fields = ('name', 'description')

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(EventName)
class EventNameAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Helper to safely register/unregister
def safe_register(model, admin_class):
    if admin.site.is_registered(model):
        admin.site.unregister(model)
    admin.site.register(model, admin_class)

@admin.register(ProviderType)
class ProviderTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class ServiceStyleAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_pax', 'description')
    search_fields = ('name', 'description')
    filter_horizontal = ('cuisines', 'budget_options')
safe_register(ServiceStyle, ServiceStyleAdmin)

class ServiceStylePrivateAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_pax')
    search_fields = ('name',)
    filter_horizontal = ('cuisines', 'budget_options')
safe_register(ServiceStylePrivate, ServiceStylePrivateAdmin)

@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('budget_options',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('cuisines', 'budget_options')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class CuisineInline(admin.TabularInline):
    model = Cuisine.budget_options.through
    extra = 1

@admin.register(BudgetOption)
class BudgetOptionAdmin(admin.ModelAdmin):
    list_display = ('label', 'price_range', 'min_price', 'max_price')
    search_fields = ('label', 'price_range')
    inlines = [CuisineInline]

@admin.register(Pax)
class PaxAdmin(admin.ModelAdmin):
    list_display = ('label', 'number')
    search_fields = ('label', 'number')
    filter_horizontal = ('service_styles', 'service_styles_private')
    list_filter = ('service_styles',)

@admin.register(CateringPlan)
class CateringPlanAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'event_type', 'guest_count', 'event_date', 'event_time',
        'provider_type', 'location', 'budget', 'created_at'
    )
    list_filter = ('event_type', 'provider_type', 'location', 'budget')
    search_fields = ('user__username', 'event_type__name', 'location__name')
    date_hierarchy = 'event_date'
    inlines = [CateringPlanServiceStyleInline, CateringPlanCuisineInline, CateringPlanCourseInline]
    readonly_fields = ('created_at',)

    fieldsets = (
        ('User & Event Details', {
            'fields': ('user', 'event_type', 'guest_count', 'event_date', 'event_time')
        }),
        ('Provider & Style', {
            'fields': ('provider_type', 'service_styles')
        }),
        ('Food Preferences', {
            'fields': ('cuisines', 'courses')
        }),
        ('Location & Budget', {
            'fields': ('location', 'budget')
        }),
        ('System Info', {
            'fields': ('created_at',)
        }),
    )

class CoffeeBreakItemInline(admin.TabularInline):
    model = CoffeeBreakItem
    extra = 1

@admin.register(CoffeeBreakRotation)
class CoffeeBreakRotationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    inlines = [CoffeeBreakItemInline]

@admin.register(CoffeeBreakItem)
class CoffeeBreakItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'rotation')
    list_filter = ('rotation', 'category')
    search_fields = ('name',)

@admin.register(PlatterItem)
class PlatterItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(BoxedMealItem)
class BoxedMealItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(LiveStationItem)
class LiveStationItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)
