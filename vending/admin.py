from django import forms
from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    Menu, MenuItem, Offer,
    VendingLocation, UserLocationSelection,
    PickupTimeSlot,
    Order, OrderItem,
    Cart, CartItem,
    MealPlan, MealPlanItem,
    FavoriteMenuItem, VendingMachineStock,
    LocationItemPrice,
    Category,
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


from .models import MasterItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "item_count", "created_at")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()


class AssignCategoryForm(forms.Form):
    """Intermediate form: pick which category to assign to the selected items.

    The selected item ids ride along as ``_selected_action`` hidden inputs in the
    template, so Django's changelist rebuilds the queryset for us — this form only
    needs to capture the chosen category.
    """
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Assign selected items to category",
    )


@admin.register(MasterItem)
class MasterItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category_list", "calories", "heating", "created_at")
    list_filter = ("categories",)
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("categories",)
    actions = ["assign_to_category"]

    @admin.display(description="Categories")
    def category_list(self, obj):
        return ", ".join(c.name for c in obj.categories.all()) or "—"

    @admin.action(description="Assign selected items to a category…")
    def assign_to_category(self, request, queryset):
        """
        Bulk-categorize workflow: admin selects one or more items, chooses this
        action, then picks the target category on an intermediate page.
        """
        if "apply" in request.POST:
            form = AssignCategoryForm(request.POST)
            if form.is_valid():
                category = form.cleaned_data["category"]
                for item in queryset:
                    item.categories.add(category)
                self.message_user(
                    request,
                    f"Assigned {queryset.count()} item(s) to “{category.name}”.",
                    messages.SUCCESS,
                )
                return redirect(request.get_full_path())
        else:
            form = AssignCategoryForm()

        return render(
            request,
            "admin/vending/assign_category.html",
            {
                "items": queryset,
                "form": form,
                "title": "Assign items to a category",
                "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            },
        )

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "categories", "description", "ingredients")
        }),
        ("Pricing & Nutrition", {
            "fields": ("default_price", "calories", "protein", "carbs", "fats")
        }),
        ("Heating", {
            "fields": ("heating", "maximum_heating")
        }),
        ("Images", {
            "description": "• image = shown on item cards  |  • image2 = shown in the sidebar detail panel (falls back to 'image' if not set)",
            "fields": ("image_source_url", "image", "image2")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "master_item", "price", "menu", "offer")
    search_fields = ("name", "master_item__name")
    list_filter = ("menu__day_of_week",)
    ordering = ("name",)
    autocomplete_fields = ["master_item"] # Enable searching for master items


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


@admin.register(VendingMachineStock)
class VendingMachineStockAdmin(admin.ModelAdmin):
    list_display = ("vending_good_uuid", "goods_name", "quantity", "updated_at")
    search_fields = ("goods_name", "vending_good_uuid")
    ordering = ("goods_name",)


@admin.register(LocationItemPrice)
class LocationItemPriceAdmin(admin.ModelAdmin):
    list_display = ("location", "master_item", "price", "updated_at")
    list_filter = ("location",)
    search_fields = ("location__name", "master_item__name")
    ordering = ("location", "master_item")
    autocomplete_fields = ("location", "master_item")
