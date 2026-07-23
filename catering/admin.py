from django import forms
from django.contrib import admin
from .models import (
    EventType, EventName, ProviderType, ServiceStyle, ServiceStylePrivate, ServiceStylePrivateChef, Cuisine,
    Course, MenuItem, Location, BudgetOption, Pax, CateringPlan,
    CoffeeBreakRotation, CoffeeBreakItem, PlatterItem, BoxedMealItem, LiveStationItem,
    FixedCateringMenu, AmericanMenu, AmericanMenuItem, RamadanMenu, RamadanMenuCourse, RamadanMenuItem,
    IftarBoxMenu, SweetsItem, SweetsItemVariation, SweetsItemImage,
    BeitNahlaSettings, BeitNahlaDistanceTier, BeitNahlaMealBox, BeitNahlaMealBoxImage,
    BeitNahlaOptionCategory, BeitNahlaOptionItem,
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

# ========== IFTAR BOX MENU ADMIN ==========

@admin.register(IftarBoxMenu)
class IftarBoxMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget_option', 'is_active', 'created_at')
    list_filter = ('budget_option', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

# ========== SWEETS ITEM ADMIN ==========

class SweetsItemVariationInline(admin.TabularInline):
    model = SweetsItemVariation
    extra = 1

class SweetsItemImageInline(admin.TabularInline):
    model = SweetsItemImage
    extra = 3
    fields = ('image', 'alt_text', 'order')

@admin.register(SweetsItem)
class SweetsItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_item', 'price')
    search_fields = ('name', 'master_item__name')
    autocomplete_fields = ['master_item']
    inlines = [SweetsItemImageInline, SweetsItemVariationInline]


# ========== BEIT NAHLA ADMIN ==========

class _TwelveHourTimeInput(forms.TextInput):
    """TextInput that renders a TimeField as '9:00 AM' instead of '09:00:00'."""

    def __init__(self, attrs=None):
        merged = {'placeholder': 'e.g. 9:00 AM', 'style': 'width: 10em;'}
        if attrs:
            merged.update(attrs)
        super().__init__(attrs=merged)

    def format_value(self, value):
        if value in (None, ''):
            return ''
        if hasattr(value, 'strftime'):
            # 24h -> 12h with AM/PM, no leading zero on hour
            return value.strftime('%I:%M %p').lstrip('0')
        # Already a string (e.g. from form re-submit) — leave as typed
        return str(value)


# Input formats accepted from the admin form. The first one is the canonical
# 12-hour format; the rest are forgiving fallbacks so e.g. "9 AM", "21:00",
# or "9:00am" all parse correctly.
_TWELVE_HOUR_FORMATS = [
    '%I:%M %p',  # 9:00 AM
    '%I:%M%p',   # 9:00AM
    '%I %p',     # 9 AM
    '%I%p',      # 9AM
    '%H:%M',     # 21:00 (24h still accepted)
    '%H:%M:%S',  # 21:00:00
]


class BeitNahlaSettingsForm(forms.ModelForm):
    opening_time = forms.TimeField(
        input_formats=_TWELVE_HOUR_FORMATS,
        widget=_TwelveHourTimeInput(),
        help_text="Format: HH:MM AM/PM — e.g. 9:00 AM",
    )
    closing_time = forms.TimeField(
        input_formats=_TWELVE_HOUR_FORMATS,
        widget=_TwelveHourTimeInput(),
        help_text="Format: HH:MM AM/PM — e.g. 11:00 PM",
    )

    class Meta:
        model = BeitNahlaSettings
        fields = '__all__'


@admin.register(BeitNahlaSettings)
class BeitNahlaSettingsAdmin(admin.ModelAdmin):
    form = BeitNahlaSettingsForm
    list_display = ('restaurant_name', 'order_now_price', 'weekly_price', 'opening_display', 'closing_display', 'max_deliverable_km', 'updated_at')
    fieldsets = (
        ('Pricing', {
            'fields': ('order_now_price', 'weekly_price'),
        }),
        ('Restaurant Origin', {
            'fields': ('restaurant_name', 'restaurant_latitude', 'restaurant_longitude'),
        }),
        ('Working Hours (Asia/Dubai)', {
            'fields': ('opening_time', 'closing_time'),
            'description': 'Enter times in 12-hour AM/PM format (e.g. 9:00 AM, 11:00 PM). For overnight hours (e.g. 10:00 PM–2:00 AM) set closing_time to a time before opening_time.',
        }),
        ('Delivery Range', {
            'fields': ('max_deliverable_km',),
        }),
    )

    @admin.display(description='Opens', ordering='opening_time')
    def opening_display(self, obj):
        return obj.opening_time.strftime('%I:%M %p').lstrip('0') if obj.opening_time else '-'

    @admin.display(description='Closes', ordering='closing_time')
    def closing_display(self, obj):
        return obj.closing_time.strftime('%I:%M %p').lstrip('0') if obj.closing_time else '-'

    def has_add_permission(self, request):
        # Singleton: only one settings row
        return not BeitNahlaSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BeitNahlaDistanceTier)
class BeitNahlaDistanceTierAdmin(admin.ModelAdmin):
    list_display = ('label', 'min_km', 'max_km', 'service_charge', 'delivery_charge', 'is_active')
    list_editable = ('min_km', 'max_km', 'service_charge', 'delivery_charge', 'is_active')
    ordering = ('min_km',)


class BeitNahlaMealBoxImageInline(admin.TabularInline):
    model = BeitNahlaMealBoxImage
    extra = 3
    fields = ('image', 'alt_text', 'order')


@admin.register(BeitNahlaMealBox)
class BeitNahlaMealBoxAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'display_order', 'updated_at')
    list_editable = ('is_active', 'display_order')
    search_fields = ('name', 'description')
    inlines = [BeitNahlaMealBoxImageInline]


class BeitNahlaOptionItemInline(admin.TabularInline):
    model = BeitNahlaOptionItem
    extra = 2
    fields = ('name', 'description', 'image', 'display_order', 'is_active')


@admin.register(BeitNahlaOptionCategory)
class BeitNahlaOptionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name',)
    inlines = [BeitNahlaOptionItemInline]


@admin.register(BeitNahlaOptionItem)
class BeitNahlaOptionItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'display_order', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name', 'category__name')


