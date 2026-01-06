from django.contrib import admin
from .models import (
    EventType, EventName, ProviderType, ServiceStyle, ServiceStylePrivate, Cuisine,
    Course, MenuItem, Location, BudgetOption, BudgetOptionPrivate, Pax, PaxPrivate, CateringPlan
)

# ...




@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'course')
    list_filter = ('cuisine', 'course')
    search_fields = ('name',)
    filter_horizontal = ('budget_options', 'budget_options_private')


# ========== INLINE CONFIGS (Optional) ==========
# If you want to show many-to-many fields inline in CateringPlan admin,
# we’ll use TabularInline (useful for quick overview)
class CateringPlanServiceStyleInline(admin.TabularInline):
    model = CateringPlan.service_styles.through
    extra = 1


class CateringPlanCuisineInline(admin.TabularInline):
    model = CateringPlan.cuisines.through
    extra = 1


class CateringPlanCourseInline(admin.TabularInline):
    model = CateringPlan.courses.through
    extra = 1


# ========== ADMIN MODELS FOR DYNAMIC ITEMS ==========

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(EventName)
class EventNameAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProviderType)
class ProviderTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ServiceStyle)
class ServiceStyleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ServiceStylePrivate)
class ServiceStylePrivateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('cuisines',)  # ✅ Easy selection of cuisines in Admin





@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(BudgetOption)
class BudgetOptionAdmin(admin.ModelAdmin):
    list_display = ('label', 'price_range', 'max_price')
    search_fields = ('label', 'price_range')


@admin.register(BudgetOptionPrivate)
class BudgetOptionPrivateAdmin(admin.ModelAdmin):
    list_display = ('label', 'price_range', 'max_price')
    search_fields = ('label', 'price_range')


@admin.register(Pax)
class PaxAdmin(admin.ModelAdmin):
    list_display = ('label', 'number')
    search_fields = ('label', 'number')


@admin.register(PaxPrivate)
class PaxPrivateAdmin(admin.ModelAdmin):
    list_display = ('label', 'number')
    search_fields = ('label', 'number')


# ========== MAIN USER SUBMISSION ADMIN ==========

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
