from django.contrib import admin
from .models import (
    Menu, MenuItem, Offer,
    VendingLocation, UserLocationSelection,
    PickupTimeSlot,
    Order, OrderItem,
    Cart, CartItem,
    MealPlan, MealPlanItem,
    FavoriteMenuItem
)

# -----------------------------------------------------------
# MENU
# -----------------------------------------------------------

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("day_of_week", "date")
    list_filter = ("day_of_week",)
    search_fields = ("day_of_week",)
    ordering = ("date",)
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "menu", "offer")
    search_fields = ("name",)
    list_filter = ("menu__day_of_week",)
    ordering = ("name",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "description", "valid_until")
    search_fields = ("menu_item__name",)
    ordering = ("-valid_until",)


# -----------------------------------------------------------
# VENDING LOCATOR
# -----------------------------------------------------------

@admin.register(VendingLocation)
class VendingLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "info", "hours", "latitude", "longitude", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "info")
    ordering = ("name",)


@admin.register(UserLocationSelection)
class UserLocationSelectionAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "is_selected", "selected_at")
    list_filter = ("is_selected",)
    search_fields = ("user__username", "location__name")
    ordering = ("-selected_at",)


# -----------------------------------------------------------
# PICKUP TIME SLOTS
# -----------------------------------------------------------

@admin.register(PickupTimeSlot)
class PickupTimeSlotAdmin(admin.ModelAdmin):
    list_display = ("label", "start_time", "end_time", "location", "is_active")
    list_filter = ("is_active", "location")
    search_fields = ("label",)
    ordering = ("start_time",)


# -----------------------------------------------------------
# ORDERS
# -----------------------------------------------------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "location",
        "plan_type",
        "plan_subtype",
        "status",
        "pickup_date",
        "total_amount",
        "created_at"
    )
    list_filter = ("status", "plan_type", "plan_subtype", "location")
    search_fields = ("user__username",)
    ordering = ("-created_at",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "menu_item", "quantity", "day_of_week", "week_number")
    search_fields = ("menu_item__name",)
    ordering = ("order",)


# -----------------------------------------------------------
# CART
# -----------------------------------------------------------

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "total_price", "is_checked_out", "created_at", "updated_at")
    list_filter = ("is_checked_out", "location")
    search_fields = ("user__username",)
    ordering = ("-updated_at",)
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "menu_item", "quantity", "added_at")
    search_fields = ("menu_item__name",)
    ordering = ("-added_at",)


# -----------------------------------------------------------
# SAVED MEAL PLANS (Weekly / Monthly)
# -----------------------------------------------------------

class MealPlanItemInline(admin.TabularInline):
    model = MealPlanItem
    extra = 0
    fields = ("menu_item", "quantity", "day_of_week", "week_number")
    autocomplete_fields = ["menu_item"]
    show_change_link = True


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "kind",
        "user",
        "location",
        "is_default",
        "is_global",
        "created_at",
    )
    list_filter = (
        "kind",
        "is_default",
        "is_global",
        "location",
        "created_at",
    )
    search_fields = ("name", "user__username", "location__name")
    ordering = ("-created_at",)
    inlines = [MealPlanItemInline]
    list_per_page = 20

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "kind",
                "user",
                "location",
                "is_default",
                "is_global",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("created_at",)


@admin.register(MealPlanItem)
class MealPlanItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "meal_plan",
        "menu_item",
        "quantity",
        "day_of_week",
        "week_number",
    )
    list_filter = ("day_of_week", "week_number")
    search_fields = ("meal_plan__name", "menu_item__name", "meal_plan__user__username")
    ordering = ("meal_plan",)
    autocomplete_fields = ["menu_item", "meal_plan"]


# -----------------------------------------------------------
# FAVORITES
# -----------------------------------------------------------

@admin.register(FavoriteMenuItem)
class FavoriteMenuItemAdmin(admin.ModelAdmin):
    list_display = ("user", "menu_item", "created_at")
    search_fields = ("user__username", "menu_item__name")
    ordering = ("-created_at",)
