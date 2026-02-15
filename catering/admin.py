from django.contrib import admin
from .models import (
    EventType, EventName, ProviderType, ServiceStyle, ServiceStylePrivate, ServiceStylePrivateChef, Cuisine,
    Course, MenuItem, Location, BudgetOption, Pax, CateringPlan,
    CoffeeBreakRotation, CoffeeBreakItem, PlatterItem, BoxedMealItem, LiveStationItem,
    FixedCateringMenu, AmericanMenu, AmericanMenuItem, RamadanMenu, RamadanMenuCourse, RamadanMenuItem
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
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [AmericanMenuItemInline]
safe_register(AmericanMenu, AmericanMenuAdmin)



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
    list_display = ('name', 'cuisine', 'budget_option')
    list_filter = ('cuisine', 'budget_option')
    filter_horizontal = ('courses', 'items')
    search_fields = ('name',)

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

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

class ServiceStylePrivateChefAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_pax', 'description')
    search_fields = ('name', 'description')
    filter_horizontal = ('cuisines', 'budget_options')
safe_register(ServiceStylePrivateChef, ServiceStylePrivateChefAdmin)

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
    filter_horizontal = ('service_styles', 'service_styles_private', 'service_styles_private_chef')
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

from .models import CateringMasterItem, CanapeItem

@admin.register(CateringMasterItem)
class CateringMasterItemAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)

@admin.register(CoffeeBreakItem)
class CoffeeBreakItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'category', 'rotation')
    list_filter = ('rotation', 'category')
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']

@admin.register(PlatterItem)
class PlatterItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'description')
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']

@admin.register(BoxedMealItem)
class BoxedMealItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']

@admin.register(LiveStationItem)
class LiveStationItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'price')
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']

@admin.register(CanapeItem)
class CanapeItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']

@admin.register(AmericanMenuItem)
class AmericanMenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'category', 'menu')
    list_filter = ('menu', 'category')
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']
    
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'cuisine', 'course')
    list_filter = ('cuisine', 'course')
    search_fields = ('name', 'master_item__name')
    filter_horizontal = ('budget_options',)
    autocomplete_fields = ['master_item']

# ========== RAMADAN MENU ADMIN ==========

class RamadanMenuItemInline(admin.TabularInline):
    model = RamadanMenuItem
    extra = 1
    autocomplete_fields = ['master_item']
    fields = ('master_item', 'name', 'quantity', 'display_order')
    readonly_fields = ('name',)

class RamadanMenuCourseInline(admin.TabularInline):
    model = RamadanMenuCourse
    extra = 1
    fields = ('course', 'display_order')
    show_change_link = True

@admin.register(RamadanMenu)
class RamadanMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_style', 'budget_option', 'is_active', 'created_at')
    list_filter = ('service_style', 'budget_option', 'is_active')
    search_fields = ('name', 'description')
    inlines = [RamadanMenuCourseInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Menu Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Service Configuration', {
            'fields': ('service_style', 'budget_option')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RamadanMenuCourse)
class RamadanMenuCourseAdmin(admin.ModelAdmin):
    list_display = ('menu', 'course', 'display_order')
    list_filter = ('menu__service_style', 'course')
    search_fields = ('menu__name', 'course__name')
    inlines = [RamadanMenuItemInline]
    fields = ('menu', 'course', 'display_order')

@admin.register(RamadanMenuItem)
class RamadanMenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'get_menu', 'get_course', 'quantity', 'display_order')
    list_filter = ('menu_course__menu__service_style', 'menu_course__course')
    search_fields = ('name', 'master_item__name', 'menu_course__menu__name')
    autocomplete_fields = ['master_item']
    readonly_fields = ('name', 'description', 'image')
    
    def get_menu(self, obj):
        return obj.menu_course.menu.name
    get_menu.short_description = 'Menu'
    get_menu.admin_order_field = 'menu_course__menu__name'
    
    def get_course(self, obj):
        return obj.menu_course.course.name
    get_course.short_description = 'Course'
    get_course.admin_order_field = 'menu_course__course__name'

