from rest_framework import viewsets, permissions, filters, status
import os
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from django.db.models import Q, ProtectedError
from django.db import transaction
from django.utils import timezone
import pytz
from datetime import datetime

from .models import (
    VendingLocation,
    UserLocationSelection,
    Menu,
    MenuItem,
    MenuType,
    DayOfWeek,
    PlanType,
    PlanSubType,
    PickupTimeSlot,
    MealPlan,
    MasterItem,
    Order,
    OrderItem,
    OrderStatus,
    Cart,
    CartItem,
    PickupType,
    VendingMachineStock
)
from .serializers import (
    VendingLocationSerializer,
    UserLocationSelectionSerializer,
    MenuSerializer,
    MasterItemSerializer,
    PickupTimeSlotSerializer,
    MealPlanSerializer,
    OrderSerializer,
    CartSerializer
)

# -----------------------------------------------------------
# LOCATION VIEWS
# -----------------------------------------------------------

class VendingLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/locations/?active=true&ids=1,2,3&search=barsha
    """
    serializer_class = VendingLocationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "info"]

    def get_queryset(self):
        qs = VendingLocation.objects.all()
        active = self.request.query_params.get("active")
        if active is None or active.lower() == "true":
            qs = qs.filter(is_active=True)

        ids = self.request.query_params.get("ids")
        if ids:
            id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
            if id_list:
                qs = qs.filter(id__in=id_list)

        return qs.order_by("name")

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Uploads an Excel file containing vending machine locations.
        Expected columns: Location Name, Location, Map URL, Machine Serial No.
        Extracts lat/lng from Google Maps URL.
        """
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import pandas as pd
            import re
            
            # Atomic transaction: If anything fails, rollback.
            with transaction.atomic():
                # 1. Clear existing data
                try:
                    VendingLocation.objects.all().delete()
                except ProtectedError as e:
                    return Response(
                        {"error": f"Cannot replace locations because they are linked to existing orders. Please archive or delete related orders first. Details: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 1. Find Header Row (Dynamic)
                header_row_index = 0
                original_df = pd.read_excel(file, header=None)
                for i in range(min(10, len(original_df))):
                    row_values = [str(val).lower() for val in original_df.iloc[i].values]
                    if any("location" in val for val in row_values) and \
                       (any("serial" in val for val in row_values) or any("map" in val for val in row_values)):
                        header_row_index = i
                        break
                
                file.seek(0)
                df = pd.read_excel(file, header=header_row_index)

                def get_val(row, col_name):
                    val = row.get(col_name)
                    return str(val) if not pd.isna(val) else ""
    
                count = 0
                for index, row in df.iterrows():
                    cols = df.columns
                    
                    # Flexible Column Matching
                    name_col = next((c for c in cols if "name" in c.lower() and "location" in c.lower()), None)
                    
                    info_col = None
                    if "Location" in cols:
                         info_col = "Location"
                    else:
                         info_col = next((c for c in cols if "address" in c.lower() or "info" in c.lower()), None)
                    
                    if not name_col:
                         name_col = next((c for c in cols if c.strip().lower() == "location"), None)
    
                    url_col = next((c for c in cols if "map" in c.lower() or "link" in c.lower()), None)
                    serial_col = next((c for c in cols if "serial" in c.lower() and "machine" in c.lower()), None)
                    if not serial_col:
                         serial_col = next((c for c in cols if "serial" in c.lower()), None)
                    
                    if not name_col:
                        continue 
    
                    name = get_val(row, name_col)
                    info = get_val(row, info_col) if info_col else ""
                    url = get_val(row, url_col) if url_col else ""
                    
                    raw_serial = get_val(row, serial_col) if serial_col else f"UNKNOWN-{index}"
                    serial_number = str(raw_serial).replace("SX2024", "").replace("sx2024", "")
                    
                    latitude = None
                    longitude = None
    
                    if url:
                        match = re.search(r'@([-.\d]+),([-.\d]+)', url)
                        if match:
                            latitude = match.group(1)
                            longitude = match.group(2)
                    
                    if not latitude:
                         lat_col_explicit = next((c for c in cols if "latitude" in c.lower()), None)
                         if lat_col_explicit: cursor_lat = get_val(row, lat_col_explicit)
                         if lat_col_explicit and cursor_lat: latitude = cursor_lat
                    
                    if not longitude:
                         long_col_explicit = next((c for c in cols if "longitude" in c.lower()), None)
                         if long_col_explicit: cursor_long = get_val(row, long_col_explicit)
                         if long_col_explicit and cursor_long: longitude = cursor_long
    
                    if name and latitude and longitude:
                        VendingLocation.objects.create(
                            serial_number=serial_number,
                            name=name,
                            info=info,
                            latitude=latitude,
                            longitude=longitude,
                            is_active=True
                        )
                        count += 1
            
            return Response({"message": f"Successfully replaced all data. Processed {count} new locations."}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------------
# BACKEND PAGE: UPLOAD LOCATIONS
# -----------------------------------------------------------
from django.shortcuts import render
from django.contrib import messages

def data_upload_view(request):
    """
    Backend view to upload vending locations via HTML form.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            import pandas as pd
            import re
            
            # Atomic transaction for file upload
            with transaction.atomic():
                # 1. Clear existing data
                try:
                    VendingLocation.objects.all().delete()
                except ProtectedError as e:
                    messages.error(request, f"Replace failed: Locations are linked to existing orders. {str(e)}")
                    return render(request, 'vending/upload_locations.html')

                # 2. Find Header Row
                original_df = pd.read_excel(file, header=None)
                header_row_index = 0
                
                for i in range(min(10, len(original_df))):
                    row_values = [str(val).lower() for val in original_df.iloc[i].values]
                    if any("location" in val for val in row_values) and \
                       (any("serial" in val for val in row_values) or any("map" in val for val in row_values)):
                        header_row_index = i
                        break
                
                file.seek(0)
                df = pd.read_excel(file, header=header_row_index)
                
                def get_val(row, col_name):
                    val = row.get(col_name)
                    return str(val) if not pd.isna(val) else ""

                count = 0
                for index, row in df.iterrows():
                    cols = df.columns
                    
                    # Flexible Column Matching
                    name_col = next((c for c in cols if "name" in c.lower() and "location" in c.lower()), None)
                    
                    info_col = None
                    if "Location" in cols:
                         info_col = "Location"
                    else:
                         info_col = next((c for c in cols if "address" in c.lower() or "info" in c.lower()), None)
                    
                    if not name_col:
                         name_col = next((c for c in cols if c.strip().lower() == "location"), None)

                    url_col = next((c for c in cols if "map" in c.lower() or "link" in c.lower()), None)
                    serial_col = next((c for c in cols if "serial" in c.lower() and "machine" in c.lower()), None)
                    if not serial_col:
                        serial_col = next((c for c in cols if "serial" in c.lower()), None)
                    
                    if not name_col:
                        print(f"Skipping Row {index}: Name Column not found.")
                        continue

                    name = get_val(row, name_col)
                    info = get_val(row, info_col) if info_col else ""
                    url = get_val(row, url_col) if url_col else ""
                    
                    raw_serial = get_val(row, serial_col) if serial_col else f"UNKNOWN-{index}"
                    serial_number = str(raw_serial).replace("SX2024", "").replace("sx2024", "")

                    latitude = None
                    longitude = None

                    if url:
                        match = re.search(r'@([-.\d]+),([-.\d]+)', url)
                        if match:
                            latitude = match.group(1)
                            longitude = match.group(2)
                    
                    if not latitude:
                        lat_col_explicit = next((c for c in cols if "latitude" in c.lower()), None)
                        if lat_col_explicit: cursor_lat = get_val(row, lat_col_explicit)
                        if lat_col_explicit and cursor_lat: latitude = cursor_lat
                    
                    if not longitude:
                        long_col_explicit = next((c for c in cols if "longitude" in c.lower()), None)
                        if long_col_explicit: cursor_long = get_val(row, long_col_explicit)
                        if long_col_explicit and cursor_long: longitude = cursor_long
                    
                    if name and latitude and longitude:
                        # Create new record (no need for update_or_create as we deleted all)
                        VendingLocation.objects.create(
                            serial_number=serial_number,
                            name=name,
                            info=info,
                            latitude=latitude,
                            longitude=longitude,
                            is_active=True
                        )
                        count += 1
            
            messages.success(request, f"Successfully replaced all data. Processed {count} new locations. (Rows with invalid Map URLs were skipped)")
            
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return render(request, 'vending/upload_locations.html')


# -----------------------------------------------------------
# STEP 1: PLAN TYPE OPTIONS
# -----------------------------------------------------------

class PlanTypeOptionsView(APIView):
    """
    Returns all plan types and next step indicator.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = {
            "options": [
                {"key": "ORDER_NOW", "label": "Order Now"},
                {"key": "START_PLAN", "label": "Start a Plan"},
            ],
            "next_step": "pickup_options"
        }
        return Response(data, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 2: PICKUP OPTIONS
# -----------------------------------------------------------

class PickupOptionsView(APIView):
    """
    Returns pickup types and available time slots for a given location.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        location_id = request.query_params.get("location_id")
        if not location_id:
            return Response({"error": "location_id is required"}, status=400)

        # Fetch slots for specific location OR global slots (location is null)
        slots = PickupTimeSlot.objects.filter(
            Q(location_id=location_id) | Q(location__isnull=True), 
            is_active=True
        ).order_by('start_time')
        serializer = PickupTimeSlotSerializer(slots, many=True)

        return Response({
            "pickup_types": [
                {"key": "TODAY", "label": "Pickup Today"},
            ],
            "time_slots": serializer.data,
            "next_step": "choose_menu"
        })


# -----------------------------------------------------------
# STEP 3: MENU BY PLAN TYPE
# -----------------------------------------------------------

class MenuByTypeView(APIView):
    """
    /api/menu/<plan_type>/?day=Monday
    For ORDER_NOW and SMART_GRAB → daily menus
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, plan_type):
        items = MasterItem.objects.all().order_by('name')
        serializer = MasterItemSerializer(items, many=True, context={'request': request})
        return Response({
            "plan_type": plan_type,
            "menus": [{"id": None, "day_of_week": None, "date": None, "items": serializer.data}],
            "allow_multiple_selection": True,
            "next_step": "confirm_order"
        })


# -----------------------------------------------------------
# STEP 4: START PLAN OPTIONS (WEEKLY / MONTHLY)
# -----------------------------------------------------------

class PlanOptionsView(APIView):
    """
    Returns weekly/monthly subtypes for 'Start a Plan'
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "plan_subtypes": [
                {"key": "WEEKLY", "label": "Weekly Plan"},
                {"key": "MONTHLY", "label": "Monthly Plan"}
            ],
            "next_step": "pickup_time"
        })


class PlanMenuView(APIView):
    """
    /api/menu/plan/<subtype>/
    Fetches menu structure based on Weekly or Monthly plan.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, subtype):
        if subtype == "WEEKLY":
            week_data = {}
            for day, _ in DayOfWeek.choices:
                menu = Menu.objects.filter(day_of_week=day, menu_type=MenuType.WEEKLY).prefetch_related('items__master_item').first()
                week_data[day] = MenuSerializer(menu, context={'request': request}).data if menu else None
            return Response({
                "plan_subtype": "WEEKLY",
                "week_menu": week_data,
                "next_step": "confirm_order"
            })

        elif subtype == "MONTHLY":
            month_data = []
            for week in range(1, 5):
                week_menu = {}
                for day, _ in DayOfWeek.choices:
                    menu = Menu.objects.filter(day_of_week=day, week_number=week, menu_type=MenuType.MONTHLY).prefetch_related('items__master_item').first()
                    week_menu[day] = MenuSerializer(menu, context={'request': request}).data if menu else None
                month_data.append({"week": week, "menu": week_menu})

            return Response({
                "plan_subtype": "MONTHLY",
                "month_menu": month_data,
                "next_step": "confirm_order"
            })

        return Response({"error": "Invalid plan subtype"}, status=400)


# -----------------------------------------------------------
# STEP 5: SAVED MEAL PLANS
# -----------------------------------------------------------

class SavedPlansView(APIView):
    """
    Returns saved meal plans (user + global)
    """
    def get(self, request):
        user = request.user
        plans = MealPlan.objects.filter(Q(user=user) | Q(is_global=True))
        serializer = MealPlanSerializer(plans, many=True, context={'request': request})
        return Response({
            "saved_plans": serializer.data,
            "next_step": "confirm_order"
        })


# -----------------------------------------------------------
# STEP 6: CONFIRM & CREATE ORDER
# -----------------------------------------------------------

class ConfirmOrderView(APIView):
    """
    POST:
    {
        "location_id": 1,
        "plan_type": "ORDER_NOW",
        "plan_subtype": "NONE",
        "pickup_type": "TODAY",
        "pickup_date": "2025-11-12",
        "pickup_slot_id": 3,
        "items": [
            {"menu_item_id": 2, "quantity": 1, "day_of_week": "Monday", "week_number": null}
        ]
    }
    """
    def post(self, request):
        data = request.data

        # ── UAE Order Time Restriction (WEEKLY / MONTHLY / SWEETS) ──────────
        plan_subtype = data.get("plan_subtype", "NONE")
        plan_type = data.get("plan_type", "")
        if plan_subtype in ("WEEKLY", "MONTHLY") or plan_type == "SWEETS":
            from django.utils import timezone
            import pytz
            uae_tz = pytz.timezone("Asia/Dubai")
            uae_now = timezone.now().astimezone(uae_tz)
            # Allow 07:00 (inclusive) → 18:00 (exclusive)
            if uae_now.hour < 7 or uae_now.hour >= 18:
                return Response(
                    {"error": "Weekly, Monthly & Sweets orders can only be placed between 7:00 AM and 6:00 PM UAE time."},
                    status=400,
                )
        # ─────────────────────────────────────────────────────────────────────

        loc_id = data.get("location_id")
        valid_loc_id = loc_id if loc_id and VendingLocation.objects.filter(id=loc_id).exists() else None

        slot_id = data.get("pickup_slot_id")
        valid_slot_id = slot_id if slot_id and PickupTimeSlot.objects.filter(id=slot_id).exists() else None

        order = Order.objects.create(
            user=request.user,
            location_id=valid_loc_id,
            plan_type=data.get("plan_type"),
            plan_subtype=data.get("plan_subtype", "NONE"),
            pickup_type=data.get("pickup_type"),
            pickup_date=data.get("pickup_date"),
            pickup_slot_id=valid_slot_id,
            status=OrderStatus.PENDING,
            current_step=6,
            city=data.get("city"),
            delivery_charge=data.get("delivery_charge", 0.00)
        )

        for item in data.get("items", []):
            item_plan_type = item.get("plan_type") or (order.plan_type if order.plan_type != PlanType.START_PLAN else PlanType.ORDER_NOW)
            
            # Base common kwargs
            item_kwargs = {
                "order": order,
                "quantity": item.get("quantity", 1),
                "day_of_week": item.get("day_of_week"),
                "week_number": item.get("week_number"),
                "vending_good_uuid": item.get("vending_good_uuid"),
                "heating_requested": item.get("heating_requested", False),
                "pickup_date": item.get("pickup_date", order.pickup_date),
                "pickup_slot_id": item.get("pickup_slot_id") or order.pickup_slot_id,
                "plan_type": item_plan_type,
                "plan_subtype": item.get("plan_subtype") or order.plan_subtype or PlanSubType.NONE,
                "pickup_type": item.get("pickup_type") or order.pickup_type,
                "status": OrderStatus.PREPARING if (item.get("plan_type") or order.plan_type) == PlanType.START_PLAN else OrderStatus.PENDING
            }

            if item_plan_type == "SWEETS":
                item_kwargs["sweets_item_id"] = item["menu_item_id"]
                if item.get("variation_id"):
                    item_kwargs["sweets_variation_id"] = item["variation_id"]
            else:
                raw_id = item.get("menu_item_id")
                # Route to correct FK: MasterItem (ORDER_NOW) vs MenuItem (START_PLAN/SMART_GRAB)
                if raw_id and MasterItem.objects.filter(id=raw_id).exists():
                    item_kwargs["master_item_id"] = raw_id
                else:
                    item_kwargs["menu_item_id"] = raw_id

            OrderItem.objects.create(**item_kwargs)

        order.update_total()

        is_payment_verified = data.get("is_payment_verified") is True or data.get("is_payment_verified") == "true"

        if is_payment_verified:
            # Payment verified — confirm order
            order.status = OrderStatus.CONFIRMED
            order.save(update_fields=['status'])

            # Clear the user's active cart: delete all items and mark as checked out
            active_carts = Cart.objects.filter(user=request.user, is_checked_out=False)
            CartItem.objects.filter(cart__in=active_carts).delete()
            active_carts.update(is_checked_out=True, total_price=0)

            # Process vending fulfillment (stock decrement + pickup code)
            from .services import VendingService
            needs_fulfillment = (
                order.plan_type in [PlanType.ORDER_NOW, PlanType.SMART_GRAB] or
                order.items.filter(plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]).exists()
            )

            if needs_fulfillment:
                print(f"🚀 Processing Backend Fulfillment for Order {order.id}")
                pickup_code = None
                order.fulfillment_attempts = 1
                try:
                    pickup_code = VendingService.process_order_fulfillment(order)
                except Exception as fulfillment_err:
                    print(f"❌ Fulfillment Exception for Order {order.id}: {fulfillment_err}")

                if pickup_code:
                    order.pickup_code = pickup_code
                    order.qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pickup_code}"
                    order.status = OrderStatus.READY
                    order.save(update_fields=['pickup_code', 'qr_code_url', 'status', 'fulfillment_attempts'])
                    order.items.filter(plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]).update(
                        status=OrderStatus.READY,
                        pickup_code=pickup_code
                    )
                    print(f"✅ Fulfillment Success for Order {order.id}. Code: {pickup_code}")
                else:
                    # Payment taken but pickup code failed — mark for admin attention
                    order.status = OrderStatus.PENDING_FULFILLMENT
                    order.save(update_fields=['status', 'fulfillment_attempts'])
                    print(f"⚠️ Fulfillment failed for Order {order.id}. Marked as PENDING_FULFILLMENT.")

            serializer = OrderSerializer(order, context={'request': request})
            return Response({
                "order": serializer.data,
                "message": "Order created and confirmed."
            }, status=status.HTTP_201_CREATED)

        # --- Initiate Payment Session (Original Flow) ---
        try:
            from .payment import TotalPayService
            
            # Use user's first address as billing address (simplification)
            billing_address = request.user.profile.addresses.filter(is_default=True).first()
            if not billing_address:
                billing_address = request.user.profile.addresses.first()
            
            # URLs for Redirect (Frontend routes)
            # In production, these should be dynamic or from settings
            base_frontend_url = request.build_absolute_uri('/')[:-1] # Remove trailing slash if any, simplistic
            # Or hardcode if known, e.g. "http://localhost:8080"
            # It's better to use a known frontend URL from settings if possible, but let's try to derive or hardcode consistent with dev.
            # Assuming dev: http://localhost:8080
            frontend_host = os.environ.get('FRONTEND_URL', 'http://localhost:8080')
            
            # success_url includes order_id for verification on Cart Page
            success_url = f"{frontend_host}/vending-home/cart?payment_success=true&order_id={order.id}"
            cancel_url = f"{frontend_host}/vending-home/cart?payment_cancelled=true"
            
            redirect_url = TotalPayService.initiate_session(
                order=order,
                user=request.user,
                billing_address=billing_address,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            serializer = OrderSerializer(order, context={'request': request})
            return Response({
                "order": serializer.data,
                "payment_redirect_url": redirect_url
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # If payment init fails, maybe we should delete the order or mark it as Draft/Failed?
            # For now, let's keep it but return error.
            print(f"Payment Init Failed: {e}")
            return Response(
                {"error": f"Failed to initiate payment: {str(e)}", "order_id": order.id}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InitiatePaymentView(APIView):
    """
    Initiates payment for the current cart without creating an Order record.
    Returns payment_redirect_url.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            user = request.user
            data = request.data
            
            # --- Generic Overrides (for Catering, etc.) ---
            override_amount = data.get("amount")
            override_desc = data.get("description")
            is_generic = override_amount is not None
            
            cart = None
            if not is_generic:
                if not user.is_authenticated:
                    return Response({"error": "Authentication required for vending checkout"}, status=401)
                cart = Cart.objects.filter(user=user, is_checked_out=False).first()
                if not cart or cart.items.count() == 0:
                    return Response({"error": "Cart is empty"}, status=400)

            # Validate Billing Address
            billing_address = None
            if user.is_authenticated:
                billing_address = user.profile.addresses.filter(is_default=True).first()
                if not billing_address:
                    billing_address = user.profile.addresses.first()
            
            # For anonymous/generic, we use data fallbacks or default
            customer_name = data.get("customer_name")
            customer_email = data.get("customer_email")
            customer_phone = data.get("customer_phone")

            if not user.is_authenticated:
                # Create a minimal user-like object for the service
                class GuestUser:
                    def __init__(self, name, email, phone):
                        self.username = name or "Guest"
                        self.email = email or "guest@dosta.ae"
                        self.is_authenticated = False
                        class Profile:
                            def __init__(self, name, phone):
                                self.full_name = name
                                self.phone_number = phone
                        self.profile = Profile(name, phone)
                user = GuestUser(customer_name, customer_email, customer_phone)

            # Prepare Payment Service
            from .payment import TotalPayService
            
            # Numeric reference for display
            if is_generic:
                # For generic/catering, we might not have a cart ID. Use a timestamp-based ID or similar.
                display_order_id = int(datetime.now().timestamp()) % 1000000
                total_price = float(override_amount)
                detailed_desc = override_desc or "Dosta Payment"
                
                # Custom return URLs for catering
                frontend_host = os.environ.get('FRONTEND_URL', 'http://localhost:8080')
                success_url = data.get("success_url") or f"{frontend_host}/vending-home/cart?payment_success=true"
                cancel_url = data.get("cancel_url") or f"{frontend_host}/vending-home/cart?payment_cancelled=true"
            else:
                display_order_id = 900000 + cart.id
                total_price = cart.total_price
                item_count = cart.items.count()
                
                first_item = cart.items.first()
                item_name = "Vending Checkout"
                if first_item:
                    if first_item.menu_item:
                        item_name = first_item.menu_item.name
                    elif first_item.sweets_item:
                        item_name = first_item.sweets_item.name

                detailed_desc = f"Dosta Order - {item_name}" if item_count == 1 else f"Dosta Order ({item_count} items)"
                
                frontend_host = os.environ.get('FRONTEND_URL', 'http://localhost:8080')
                success_url = f"{frontend_host}/vending-home/cart?payment_success=true&cart_id={cart.id}"
                cancel_url = f"{frontend_host}/vending-home/cart?payment_cancelled=true"

            # Create a mock order object for the payment service
            class MockOrder:
                def __init__(self, id_val, amount, desc):
                    self.id = id_val
                    self.total_amount = amount
                    self.description = desc

            mock_order = MockOrder(display_order_id, total_price, detailed_desc)
            
            redirect_url = TotalPayService.initiate_session(
                order=mock_order,
                user=user,
                billing_address=billing_address,
                success_url=success_url,
                cancel_url=cancel_url
            )

            response_data = {
                "payment_redirect_url": redirect_url,
            }
            if cart:
                response_data["cart_id"] = cart.id
                
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Checkout Initialization Failed: {e}")
            return Response({"error": str(e)}, status=500)


# -----------------------------------------------------------
# STEP 7: ORDER PROGRESS TRACKING / RESUME
# -----------------------------------------------------------

class OrderProgressView(APIView):
    """
    GET /api/order/progress/?order_id=10 → current step + context
    PATCH /api/order/progress/ → update current_step
    """
    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response({"error": "order_id required"}, status=400)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        return Response({
            "order_id": order.id,
            "current_step": order.current_step,
            "status": order.status,
            "plan_type": order.plan_type,
            "plan_subtype": order.plan_subtype,
            "pickup_type": order.pickup_type,
            "total_amount": order.total_amount,
            "next_step_hint": self.get_next_step_hint(order.current_step)
        })

    def patch(self, request):
        order_id = request.data.get("order_id")
        step = request.data.get("current_step")

        if not (order_id and step):
            return Response({"error": "order_id and current_step are required"}, status=400)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        order.current_step = step
        order.save(update_fields=["current_step"])
        return Response({"message": f"Order step updated to {step}"})

    def get_next_step_hint(self, current_step):
        steps = {
            1: "select_location",
            2: "choose_plan_type",
            3: "pickup_time",
            4: "choose_menu",
            5: "review_order",
            6: "confirm_order"
        }
        return steps.get(current_step + 1, "completed")


class UpdatePickupCodeView(APIView):
    """
    POST /api/vending/order/update-pickup-code/
    {
        "order_id": 123,
        "pickup_code": "ABC-123"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        pickup_code = request.data.get("pickup_code")

        if not order_id or not pickup_code:
            return Response({"error": "order_id and pickup_code are required"}, status=400)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if not order.pickup_code:
                order.pickup_code = pickup_code
                order.qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pickup_code}"
                order.save()

            # Update only ORDER_NOW / SMART_GRAB items
            instant_items = order.items.filter(
                plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]
            )
            instant_items.update(status=OrderStatus.READY, pickup_code=pickup_code)

            # NEW: Decrement stock for vending items
            for item in instant_items:
                if item.vending_good_uuid:
                    stock = VendingMachineStock.objects.filter(vending_good_uuid=item.vending_good_uuid).first()
                    if stock:
                        if stock.quantity >= item.quantity:
                            stock.quantity -= item.quantity
                        else:
                            stock.quantity = 0
                        stock.save()

            return Response({
                "message": "Pickup code updated successfully",
                "pickup_code": order.pickup_code,
                "qr_code_url": order.qr_code_url
            }, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RetryFulfillmentView(APIView):
    """
    POST /api/vending/order/<order_id>/retry-fulfillment/
    Retries pickup code generation for PENDING_FULFILLMENT orders.
    Allowed for the order owner (user) or kitchen admin.
    Idempotent: if a pickup code already exists, returns existing code without re-generating.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        try:
            # Allow order owner or staff
            if request.user.is_staff or request.user.is_superuser:
                order = Order.objects.get(id=order_id)
            else:
                order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # If pickup code already exists — idempotent, return it
        if order.pickup_code:
            return Response({
                "message": "Pickup code already exists.",
                "pickup_code": order.pickup_code,
                "qr_code_url": order.qr_code_url,
                "status": order.status
            }, status=200)

        # Only retry for appropriate statuses
        if order.status not in [OrderStatus.PENDING_FULFILLMENT, OrderStatus.CONFIRMED, OrderStatus.PENDING]:
            return Response({
                "error": f"Cannot retry fulfillment for order with status '{order.status}'."
            }, status=400)

        # Cap retries to prevent abuse (max 5 attempts)
        MAX_ATTEMPTS = 5
        if order.fulfillment_attempts >= MAX_ATTEMPTS:
            return Response({
                "error": "Maximum retry attempts reached. Please contact support."
            }, status=429)

        # Backfill item_name_snapshot for any items that are missing it
        for item in order.items.filter(item_name_snapshot__isnull=True):
            item.save()  # triggers the save() snapshot logic

        from .services import VendingService
        order.fulfillment_attempts += 1
        order.status = OrderStatus.CONFIRMED
        order.save(update_fields=['fulfillment_attempts', 'status'])

        pickup_code = None
        try:
            pickup_code = VendingService.process_order_fulfillment(order)
        except Exception as e:
            print(f"❌ Retry fulfillment exception for Order {order.id}: {e}")

        if pickup_code:
            order.pickup_code = pickup_code
            order.qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pickup_code}"
            order.status = OrderStatus.READY
            order.save(update_fields=['pickup_code', 'qr_code_url', 'status'])
            order.items.filter(plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]).update(
                status=OrderStatus.READY,
                pickup_code=pickup_code
            )
            serializer = OrderSerializer(order, context={'request': request})
            return Response({
                "message": "Fulfillment successful.",
                "pickup_code": pickup_code,
                "qr_code_url": order.qr_code_url,
                "order": serializer.data
            }, status=200)
        else:
            order.status = OrderStatus.PENDING_FULFILLMENT
            order.save(update_fields=['status'])
            return Response({
                "error": "Fulfillment failed again. Please try later or contact support.",
                "attempts": order.fulfillment_attempts
            }, status=503)


class MarkQRUsedView(APIView):
    """
    POST /api/vending/order/<order_id>/mark-qr-used/
    Called by kitchen/machine when food is dispensed.
    Marks the QR as used and order as COMPLETED so the user sees delivery details.
    Staff only.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.qr_used:
            return Response({"message": "QR already marked as used."}, status=200)

        order.qr_used = True
        order.status = OrderStatus.COMPLETED
        order.save(update_fields=['qr_used', 'status'])
        order.items.filter(plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]).update(
            status=OrderStatus.COMPLETED
        )
        return Response({"message": "QR marked as used. Order completed."}, status=200)


class RecoverOrderView(APIView):
    """
    POST /api/vending/order/<order_id>/recover/
    Admin-only: Re-processes a stuck PENDING order (payment already taken).
    Re-attaches items from the user's cart (if available), recalculates total,
    then runs fulfillment to generate a pickup code.
    Body (optional): { "items": [...] }  — same format as ConfirmOrderView items.
    If body items provided they override cart lookup.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status not in [OrderStatus.PENDING, OrderStatus.PENDING_FULFILLMENT]:
            return Response({"error": f"Order is already in status '{order.status}', no recovery needed."}, status=400)

        from .services import VendingService

        # --- Re-attach items if order has none ---
        provided_items = request.data.get("items", [])
        if not order.items.exists():
            if provided_items:
                for item in provided_items:
                    item_plan_type = item.get("plan_type") or order.plan_type or PlanType.ORDER_NOW
                    item_kwargs = {
                        "order": order,
                        "quantity": item.get("quantity", 1),
                        "day_of_week": item.get("day_of_week"),
                        "week_number": item.get("week_number"),
                        "vending_good_uuid": item.get("vending_good_uuid"),
                        "heating_requested": item.get("heating_requested", False),
                        "pickup_date": item.get("pickup_date", order.pickup_date),
                        "pickup_slot_id": item.get("pickup_slot_id") or order.pickup_slot_id,
                        "plan_type": item_plan_type,
                        "plan_subtype": item.get("plan_subtype") or order.plan_subtype or PlanSubType.NONE,
                        "pickup_type": item.get("pickup_type") or order.pickup_type,
                        "status": OrderStatus.PENDING,
                    }
                    raw_id = item.get("menu_item_id")
                    if raw_id and MasterItem.objects.filter(id=raw_id).exists():
                        item_kwargs["master_item_id"] = raw_id
                    else:
                        item_kwargs["menu_item_id"] = raw_id
                    OrderItem.objects.create(**item_kwargs)
            else:
                # Try to find the user's cart and copy items
                cart = Cart.objects.filter(user=order.user, is_checked_out=False).first()
                if not cart:
                    cart = Cart.objects.filter(user=order.user).order_by('-updated_at').first()
                if cart and cart.items.exists():
                    for ci in cart.items.all():
                        item_kwargs = {
                            "order": order,
                            "quantity": ci.quantity,
                            "day_of_week": ci.day_of_week,
                            "week_number": ci.week_number,
                            "vending_good_uuid": ci.vending_good_uuid,
                            "heating_requested": ci.heating_requested,
                            "pickup_date": ci.pickup_date or order.pickup_date,
                            "pickup_slot_id": ci.pickup_slot_id or order.pickup_slot_id,
                            "plan_type": ci.plan_type or order.plan_type,
                            "plan_subtype": ci.plan_subtype or order.plan_subtype or PlanSubType.NONE,
                            "pickup_type": ci.pickup_type or order.pickup_type,
                            "status": OrderStatus.PENDING,
                        }
                        if ci.master_item_id:
                            item_kwargs["master_item_id"] = ci.master_item_id
                        elif ci.menu_item_id:
                            item_kwargs["menu_item_id"] = ci.menu_item_id
                        elif ci.sweets_item_id:
                            item_kwargs["sweets_item_id"] = ci.sweets_item_id
                            if ci.sweets_variation_id:
                                item_kwargs["sweets_variation_id"] = ci.sweets_variation_id
                        OrderItem.objects.create(**item_kwargs)
                else:
                    return Response(
                        {"error": "Order has no items and no cart found. Provide 'items' in the request body."},
                        status=400
                    )

        order.update_total()
        order.status = OrderStatus.CONFIRMED
        order.save(update_fields=['status'])

        # Run fulfillment
        needs_fulfillment = (
            order.plan_type in [PlanType.ORDER_NOW, PlanType.SMART_GRAB] or
            order.items.filter(plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]).exists()
        )

        if needs_fulfillment:
            order.fulfillment_attempts = (order.fulfillment_attempts or 0) + 1
            pickup_code = None
            try:
                pickup_code = VendingService.process_order_fulfillment(order)
            except Exception as e:
                print(f"❌ Recovery fulfillment error for Order {order.id}: {e}")

            if pickup_code:
                order.pickup_code = pickup_code
                order.qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pickup_code}"
                order.status = OrderStatus.READY
                order.save(update_fields=['pickup_code', 'qr_code_url', 'status', 'fulfillment_attempts'])
                order.items.filter(plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB]).update(
                    status=OrderStatus.READY, pickup_code=pickup_code
                )
                serializer = OrderSerializer(order, context={'request': request})
                return Response({"message": "Recovery successful.", "order": serializer.data}, status=200)
            else:
                order.status = OrderStatus.PENDING_FULFILLMENT
                order.save(update_fields=['status', 'fulfillment_attempts'])
                serializer = OrderSerializer(order, context={'request': request})
                return Response(
                    {"message": "Items re-attached and total fixed, but pickup code generation failed. Order marked PENDING_FULFILLMENT.", "order": serializer.data},
                    status=200
                )
        else:
            order.save()
            serializer = OrderSerializer(order, context={'request': request})
            return Response({"message": "Order recovered (non-fulfillment type).", "order": serializer.data}, status=200)


class KitchenOrderItemCompleteView(APIView):
    """
    POST /api/vending/kitchen/complete-item/
    {
        "order_item_id": 456
    }
    Triggered by kitchen manager when meal is put into machine.
    Calls External Vending API to get pickup code for this specific item.
    """
    permission_classes = [permissions.IsAuthenticated] # Restricted to Staff/Kitchen Admin

    def post(self, request):
        order_item_id = request.data.get("order_item_id")
        if not order_item_id:
            return Response({"error": "order_item_id required"}, status=400)

        try:
            item = OrderItem.objects.get(id=order_item_id)
            if item.status == OrderStatus.READY:
                return Response({"message": "Item already ready", "pickup_code": item.pickup_code})

            order = item.order
            serial_number = order.location.serial_number

            if not serial_number:
                return Response({"error": "Location serial number missing"}, status=400)
            if not item.vending_good_uuid:
                return Response({"error": "Item vending good UUID missing"}, status=400)

            # --- 1. Fetch Token from External API ---
            token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
            token_params = {"userName": "C202405128888", "password": "8888"}
            
            token_response = requests.get(token_url, params=token_params, timeout=10)
            token_data = token_response.json()
            token = token_data.get("data") or token_data.get("token")
            
            if not token:
                return Response({"error": "Failed to fetch vending token"}, status=502)

            # --- 2. Request Pickup Code ---
            url = "http://www.hnzczy.cn:8087/commpick/productionpick"
            headers = {"Authorization": token}
            
            uae_tz = pytz.timezone('Asia/Dubai')
            now_uae = datetime.now(uae_tz)
            order_time_str = now_uae.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            goods_list = [{
                "goodsNumber": item.quantity,
                "goodsPrice": 0.01,
                "goodsUuid": item.vending_good_uuid,
            }]
            
            if item.heating_requested:
                goods_list[0]['serviceType'] = 1
                goods_list[0]['serviceVal'] = "15"

            pick_payload = {
                "goodsList": goods_list,
                "goodsNumber": item.quantity,
                "machineUuid": serial_number,
                "orderNo": f"{order.id}-{item.id}", # Unique sub-order NO
                "orderTime": order_time_str,
                "timeOut": 1,
                "lock": 0,
            }

            pick_res = requests.post(url, json=pick_payload, headers=headers, timeout=30)
            pick_data = pick_res.json()

            if pick_data.get("result") == "200" and pick_data.get("data"):
                new_code = pick_data["data"]
                item.pickup_code = new_code
                item.status = OrderStatus.READY
                item.save()

                return Response({
                    "status": "READY",
                    "pickup_code": new_code,
                    "message": "Fulfillment successful"
                })
            else:
                return Response({
                    "error": "Vending API error",
                    "details": pick_data
                }, status=502)

        except OrderItem.DoesNotExist:
            return Response({"error": "OrderItem not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
# -----------------------------------------------------------
# ORDER HISTORY API
# -----------------------------------------------------------

class UserOrdersView(APIView):
    """
    GET /api/vending/orders/
    Returns all orders for the authenticated user, ordered by newest first.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Sort by id descending as well to guarantee order if created_at is identical
        orders = Order.objects.filter(user=request.user).order_by('-created_at', '-id')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# CART API
# -----------------------------------------------------------

class CartView(APIView):
    """
    GET /api/cart/
    POST /api/cart/
    Syncs the entire cart state (User selected items + Plan context).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get active cart (not checked out)
        cart = Cart.objects.filter(user=request.user, is_checked_out=False).first()
        if not cart:
            return Response({"message": "Cart is empty", "items": []})
        
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        try:
            data = request.data
            user = request.user

            # 1. Get or Create Cart
            cart, created = Cart.objects.get_or_create(user=user, is_checked_out=False)

            # 2. Update Context Fields
            loc_id = data.get("location_id")
            if loc_id and VendingLocation.objects.filter(id=loc_id).exists():
                cart.location_id = loc_id
            else:
                cart.location_id = None

            incoming_plan_type = data.get("plan_type", PlanType.ORDER_NOW)
            incoming_plan_subtype = data.get("plan_subtype", PlanSubType.NONE)
            
            # Support clearing the entire cart
            if data.get("clear_all"):
                cart.items.all().delete()
                cart.is_checked_out = True
                cart.total_price = 0
                cart.save()
                return Response({"message": "Cart cleared."}, status=status.HTTP_200_OK)

            cart.plan_type = incoming_plan_type
            cart.plan_subtype = incoming_plan_subtype
            cart.pickup_type = data.get("pickup_type")
            cart.pickup_date = data.get("pickup_date")

            slot_id = data.get("pickup_slot_id")
            if slot_id and PickupTimeSlot.objects.filter(id=slot_id).exists():
                cart.pickup_slot_id = slot_id
            else:
                cart.pickup_slot_id = None

            cart.current_step = data.get("current_step", 1)  # Save current step
            
            # Only update city and delivery_charge if provided (to avoid overwriting guest data with defaults on partial syncs)
            if "city" in data:
                cart.city = data.get("city")
            if "delivery_charge" in data:
                cart.delivery_charge = data.get("delivery_charge", 0.00)
            
            cart.save()

            # 3. Update Items (Partial Sync Strategy: Clear only items of the same plan type)
            items_data = data.get("items", [])
            if incoming_plan_type == PlanType.START_PLAN:
                if incoming_plan_subtype == PlanSubType.MONTHLY:
                    # Only delete items for the specific weeks being submitted
                    incoming_week_numbers = set(
                        item.get("week_number") for item in items_data if item.get("week_number") is not None
                    )
                    if incoming_week_numbers:
                        cart.items.filter(
                            plan_type=incoming_plan_type,
                            plan_subtype=incoming_plan_subtype,
                            week_number__in=incoming_week_numbers
                        ).delete()
                    else:
                        cart.items.filter(plan_type=incoming_plan_type, plan_subtype=incoming_plan_subtype).delete()
                else:
                    cart.items.filter(plan_type=incoming_plan_type, plan_subtype=incoming_plan_subtype).delete()
            else:
                cart.items.filter(plan_type=incoming_plan_type).delete()
            for item in items_data:
                menu_item_id = item.get("menu_item_id")
                quantity = item.get("quantity", 1)
                day_of_week = item.get("day_of_week")
                week_number = item.get("week_number")
                vending_good_uuid = item.get("vending_good_uuid")
                heating_requested = item.get("heating_requested", False)

                plan_type = item.get("plan_type", incoming_plan_type)

                if menu_item_id:
                    # Common args for update_or_create
                    create_kwargs = {
                        "cart": cart,
                        "quantity": quantity,
                        "day_of_week": day_of_week,
                        "week_number": week_number,
                        "vending_good_uuid": vending_good_uuid,
                        "heating_requested": heating_requested,
                        "plan_type": plan_type,
                        "plan_subtype": item.get("plan_subtype", incoming_plan_subtype),
                        "pickup_type": item.get("pickup_type", cart.pickup_type),
                        "pickup_date": item.get("pickup_date", cart.pickup_date),
                        "pickup_slot_id": item.get("pickup_slot_id") or cart.pickup_slot_id
                    }

                    if plan_type == "SWEETS":
                        variation_id = item.get("variation_id")
                        create_kwargs["sweets_variation_id"] = variation_id
                        CartItem.objects.update_or_create(
                            sweets_item_id=menu_item_id,
                            sweets_variation_id=variation_id,
                            defaults=create_kwargs,
                            cart=cart,
                            plan_type=plan_type,
                            plan_subtype=item.get("plan_subtype", incoming_plan_subtype),
                            day_of_week=day_of_week,
                            week_number=week_number,
                        )
                    elif MenuItem.objects.filter(id=menu_item_id).exists():
                        # Legacy: item is a scheduled MenuItem
                        CartItem.objects.update_or_create(
                            menu_item_id=menu_item_id,
                            defaults=create_kwargs,
                            cart=cart,
                            plan_type=plan_type,
                            plan_subtype=item.get("plan_subtype", incoming_plan_subtype),
                            day_of_week=day_of_week,
                            week_number=week_number,
                        )
                    elif MasterItem.objects.filter(id=menu_item_id).exists():
                        # Item selected from master list (ORDER_NOW / SMART_GRAB)
                        create_kwargs["master_item_id"] = menu_item_id
                        CartItem.objects.update_or_create(
                            master_item_id=menu_item_id,
                            defaults=create_kwargs,
                            cart=cart,
                            plan_type=plan_type,
                            plan_subtype=item.get("plan_subtype", incoming_plan_subtype),
                            day_of_week=day_of_week,
                            week_number=week_number,
                        )

            cart.update_total()
            
            serializer = CartSerializer(cart, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Cart Sync Error: {e}") # Log to terminal
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------------
# EXTERNAL VENDING API PROXIES
# -----------------------------------------------------------

class ExternalCheckUserView(APIView):
    """
    Proxies request to:
    http://www.hnzczy.cn:8087/apiusers/checkusername
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
        params = {
            "userName": "C202405128888",
            "password": "8888"
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            return Response(response.json(), status=response.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExternalMachineGoodsView(APIView):
    """
    Proxies request to:
    http://www.hnzczy.cn:8087/customgoods/querymachinegoods
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # 1. Fetch Token from External API
        token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
        token_params = {
            "userName": "C202405128888",
            "password": "8888"
        }
        
        print(f"DEBUG: Fetching token for MachineGoods from {token_url}")
        try:
            token_response = requests.get(token_url, params=token_params, timeout=8)
            print(f"DEBUG: Token response status: {token_response.status_code}")
            token_data = token_response.json()
            print(f"DEBUG: Token response data: {token_data}")
            token = token_data.get("data") or token_data.get("token")
            print(f"DEBUG: Extracted token: {token}")
            
            if not token:
                return Response({"error": "Could not fetch external vending token", "details": token_data}, status=status.HTTP_502_BAD_GATEWAY)

            # 2. Fetch Machine Goods using the token
            params = request.query_params.dict()
            goods_url = "http://www.hnzczy.cn:8087/commodityinfo/querycommodityinfo"
            headers = {"Authorization": token}
            print(f"DEBUG: Fetching goods from {goods_url} with params {params} and headers {headers}")
            
            response = requests.get(goods_url, params=params, headers=headers, timeout=8)
            api_data = response.json()
            
            # 3. Fetch Stock / Lock Information
            lock_counts = {}
            machine_uuid = params.get("machineUuid")

            # PRIMARY: Try external queryGoodsStock API
            try:
                stock_url = "http://www.hnzczy.cn:8087/commodityinfo/queryGoodsStock"
                stock_res = requests.get(stock_url, params={"machineUuid": machine_uuid}, headers=headers, timeout=8)
                stock_data = stock_res.json()
                print(f"DEBUG: Stock response data: {stock_data}")
                if stock_data.get("result") == "200" and stock_data.get("data"):
                    for stock_item in stock_data["data"]:
                        g_uuid = str(stock_item.get("goodsUuid"))
                        inv = stock_item.get("inventory") or 0
                        avail = stock_item.get("availableInventory") or 0
                        lock = stock_item.get("lockInventory") or 0
                        count_to_lock = max(lock, inv - avail)
                        if count_to_lock > 0:
                            lock_counts[g_uuid] = count_to_lock
                        print(f"DEBUG: Stock Check - UUID: {g_uuid}, Inv: {inv}, Avail: {avail}, Lock: {lock} -> Count to Lock: {count_to_lock}")
                print(f"DEBUG: Final Lock Counts from external API: {lock_counts}")
            except Exception as stock_err:
                print(f"DEBUG: Could not fetch stock info from external API: {stock_err}")

            # FALLBACK: Supplement with our own READY orders (QR generated but not yet collected)
            # This ensures items reserved for a user are shown as locked even if external API is down
            try:
                from django.utils import timezone as tz
                active_location = VendingLocation.objects.filter(serial_number=machine_uuid).first()
                if active_location:
                    ready_items = OrderItem.objects.filter(
                        order__location=active_location,
                        order__status=OrderStatus.READY,
                        order__qr_used=False,
                        plan_type__in=[PlanType.ORDER_NOW, PlanType.SMART_GRAB],
                        vending_good_uuid__isnull=False
                    ).exclude(vending_good_uuid='')
                    for oi in ready_items:
                        g_uuid = str(oi.vending_good_uuid)
                        lock_counts[g_uuid] = lock_counts.get(g_uuid, 0) + oi.quantity
                    print(f"DEBUG: Lock Counts after DB fallback: {lock_counts}")
            except Exception as db_err:
                print(f"DEBUG: Could not fetch DB lock info: {db_err}")

            # Transform the response to match the structure the frontend expects
            if api_data.get("result") == "200" and "data" in api_data:
                slots = api_data.get("data") or []
                shelves = {}
                
                # Diagnostic: Count total slots per product to help debug discrepancies
                product_slot_counts = {}
                for slot in slots:
                    g = slot.get("commGoodsResp")
                    if g:
                        u = str(g.get("uuid"))
                        product_slot_counts[u] = product_slot_counts.get(u, 0) + 1
                print(f"DEBUG: Product occurrences in catalog: {product_slot_counts}")
                
                # Sort slots by shelf and spot number to ensure consistent locking order
                sorted_slots = sorted(slots, key=lambda x: (x.get("modityTierSeq", 0), x.get("modityTierNum", 0)))
                
                for slot in sorted_slots:
                    goods = slot.get("commGoodsResp")
                    shelf_index = slot.get("modityTierSeq", 0)
                    
                    if shelf_index not in shelves:
                        shelves[shelf_index] = []
                    
                    slot_data = {
                        "arrivalName": slot.get("arrivalName"),
                        "presentNumber": slot.get("presentNumber"),
                        "arrivalCapacity": slot.get("arrivalCapacity"),
                        "modityTierSeq": shelf_index,
                        "modityTierNum": slot.get("modityTierNum"),
                    }
                    
                    if goods:
                        uuid_str = str(goods.get("uuid"))
                        
                        # Apply sequential locking
                        is_slot_locked = False
                        budget = lock_counts.get(uuid_str, 0)
                        if budget > 0:
                            is_slot_locked = True
                            lock_counts[uuid_str] -= 1
                        
                        print(f"DEBUG: Slot Processing - UUID: {uuid_str}, Spot: {slot.get('arrivalName')}, Budget Remaining: {lock_counts.get(uuid_str, 0)}, Locked: {is_slot_locked}")
                            
                        slot_data["goods"] = {
                            "uuid": uuid_str,
                            "goodsName": goods.get("goodsName"),
                            "goodsPrice": goods.get("goodsPrice"),
                            "goodsUrl": goods.get("goodsUrl"),
                            "goodsCode": goods.get("goodsCode"),
                            "goodsDesc": goods.get("goodsDesc"),
                            "locked": is_slot_locked
                        }
                    else:
                        slot_data["goods"] = None
                        
                    shelves[shelf_index].append(slot_data)
                
                # Assemble unique goods for the 'goodsList' / catalog
                sorted_shelves = []
                unique_goods = {}
                # Track if a product has ANY unlocked slots
                has_unlocked_slot = {}
                
                for idx in sorted(shelves.keys()):
                    spots = sorted(shelves[idx], key=lambda x: x.get("modityTierNum", 0))
                    sorted_shelves.append({
                        "shelfIndex": idx,
                        "shelfName": f"Shelf {idx + 1}",
                        "spots": spots
                    })
                    
                    for spot in spots:
                        if spot["goods"]:
                            u = spot["goods"]["uuid"]
                            if u not in unique_goods:
                                unique_goods[u] = spot["goods"].copy()
                                has_unlocked_slot[u] = not spot["goods"]["locked"]
                            else:
                                if not spot["goods"]["locked"]:
                                    has_unlocked_slot[u] = True
                
                # Apply the catalog-level lock status: Locked only if NO slots are unlocked
                for u, item in unique_goods.items():
                    item["locked"] = not has_unlocked_slot.get(u, False)
                
                transformed_data = {
                    "result": "200",
                    "resultDesc": "Success",
                    "shelves": sorted_shelves,
                    # Keep legacy format for compatibility
                    "data": [
                        {
                            "commGoodsModel": {"typeName": "Vending Items"},
                            "goodsList": list(unique_goods.values())
                        }
                    ]
                }
                return Response(transformed_data, status=status.HTTP_200_OK)

            return Response(api_data, status=response.status_code)
            
        except Exception as e:
            print(f"DEBUG: Exception in ExternalMachineGoodsView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExternalProductionPickView(APIView):
    """
    Proxies request to:
    http://www.hnzczy.cn:8087/commpick/productionpick
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # 1. Fetch Token from External API
        token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
        token_params = {
            "userName": "C202405128888",
            "password": "8888"
        }
        
        print(f"DEBUG: Fetching token for ProductionPick from {token_url}")
        try:
            token_response = requests.get(token_url, params=token_params, timeout=10)
            print(f"DEBUG: Token response status: {token_response.status_code}")
            token_data = token_response.json()
            print(f"DEBUG: Token response data: {token_data}")
            token = token_data.get("data") or token_data.get("token")
            print(f"DEBUG: Extracted token: {token}")
            
            if not token:
                return Response({"error": "Could not fetch external vending token", "details": token_data}, status=status.HTTP_502_BAD_GATEWAY)

            # 2. Production Pick Request using the token (and set orderTime to UAE time)
            url = "http://www.hnzczy.cn:8087/commpick/productionpick"
            headers = {"Authorization": token}
            
            # Use actual date and time in UAE time zone (UTC+4)
            uae_tz = pytz.timezone('Asia/Dubai')
            now_uae = datetime.now(uae_tz)
            # Format requested: 2026-01-13T18:12:33.970Z
            order_time_str = now_uae.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            
            # Create a copy of the request data and inject/override the orderTime
            pick_payload = request.data.copy()
            pick_payload['orderTime'] = order_time_str
            pick_payload['lock'] = 1
            pick_payload['timeOut'] = 24
            
            # Add heating parameters if requested and calculate total goodsNumber
            total_quantity = 0
            if 'goodsList' in pick_payload:
                for item in pick_payload['goodsList']:
                    qty = item.get('goodsNumber', 1)
                    total_quantity += qty
                    
                    if item.get('heating_requested') is True or item.get('heatingChoice') == 'yes':
                        item['serviceType'] = 1
                        item['serviceVal'] = "15"
            
            pick_payload['goodsNumber'] = total_quantity
            
            
            # --- CLEAR API LOGGING ---
            print("\n" + "="*50)
            print("🚀 SENDING REQUEST TO EXTERNAL VENDING API")
            print(f"URL: {url}")
            print(f"HEADERS: {headers}")
            print(f"PAYLOAD: {pick_payload}")
            print("="*50 + "\n")
            
            # Forward the modified JSON body
            response = requests.post(url, json=pick_payload, headers=headers, timeout=30)
            print(f"DEBUG: Pick response status: {response.status_code}")
            print(f"DEBUG: Pick response data: {response.json()}")
            return Response(response.json(), status=response.status_code)
        except Exception as e:
            print(f"DEBUG: Exception in ExternalProductionPickView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -----------------------------------------------------------
# PAYMENT CALLBACK

# -----------------------------------------------------------

class PaymentCallbackView(APIView):
    """
    Handles callback from TotalPay (success_url or notification_url).
    GET: User Redirect /api/vending/payment/callback/?order_id=...
    POST: Server-to-Server /api/vending/payment/callback/
    """
    permission_classes = [permissions.AllowAny]

    def process_payment_success(self, order_id):
        try:
            order = Order.objects.get(id=order_id)
            if order.status == OrderStatus.CONFIRMED:
                return order # Already processed

            # Update Order Status
            order.status = OrderStatus.CONFIRMED
            order.save(update_fields=['status'])
            
            # Execute Vending Logic (Stock & Pickup)
            from .services import VendingService
            pickup_code = VendingService.process_order_fulfillment(order)
            
            if pickup_code:
                order.pickup_code = pickup_code
                order.qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pickup_code}"
                order.save(update_fields=['pickup_code', 'qr_code_url'])
                
                # Update Items to READY
                order.items.filter(plan_type__in=['ORDER_NOW', 'SMART_GRAB']).update(
                    status=OrderStatus.READY,
                    pickup_code=pickup_code
                )
                
            return order
        except Order.DoesNotExist:
            # Check if it's a CART ID (legacy string format or new numeric format)
            lookup_id = str(order_id)
            cart_id = None

            if lookup_id.startswith("CART-"):
                cart_id = lookup_id.replace("CART-", "")
            elif lookup_id.startswith("900"):
                try:
                    cart_id = int(lookup_id) - 900000
                except: pass
            
            if cart_id:
                try:
                    cart = Cart.objects.get(id=int(cart_id))
                    # Optionally mark cart as "payment_verified" or similar if we had such a field.
                    # For now, we'll rely on the frontend returning with payment_success=true 
                    # and calling confirm-order.
                    return None 
                except:
                    pass
            print(f"Order {order_id} not found during callback processing.")
            return None
        except Exception as e:
            print(f"Error processing payment success for order {order_id}: {e}")
            return None

    def get(self, request):
        """
        User Return URL (Success URL)
        """
        # params: payment_id, order_number, order_status, hash, etc.
        # But wait, success_url params depend on TotalPay config.
        # Assuming we receive: order_id (from our own param) OR order_number (from TotalPay)
        
        order_id = request.query_params.get("order_id")
        # Or TotalPay might send it as 'order_number'
        if not order_id:
             order_id = request.query_params.get("order_number")
             
        # Simplify: If we set success_url to .../order-success?order_id=123
        # then the frontend handles it. 
        # But the User asked "how it will redirect back... place order logic".
        # If Frontend `OrderSuccessPage` calls a backend endpoint "verify-payment", that's safer.
        # Let's use this endpoint as the "verify-payment" called by frontend OR the direct return URL.
        
        if order_id:
            # We should technically validate the HASH from TotalPay here to be secure.
            # For now, let's assume if this endpoint is hit, we verify status=success params.
            
            # Simple Trigger
            self.process_payment_success(order_id)
            
            # Redirect to Frontend Success Page
            # Should be configured in settings
            frontend_base = os.environ.get('FRONTEND_URL', 'http://localhost:8080')
            frontend_url = f"{frontend_base}/vending-home/cart?payment_success=true&order_id={order_id}"
            return Response({"message": "Payment processed", "redirect": frontend_url})
            # OR logic: if called by Frontend (AJAX), return JSON.
            # If called by Browser (Redirect), return HTTP 302.
            
            # Let's assume this is an API called by the Frontend "OrderSuccessPage" to finalize.
            if request.headers.get("Content-Type") == "application/json":
                 return Response({"status": "CONFIRMED", "order_id": order_id})
        
        return Response({"message": "Callback received"}, status=200)

    def post(self, request):
        """
        Server-to-Server Notification
        """
        data = request.data
        order_number = data.get("order_number") or data.get("order", {}).get("number")
        
        if order_number:
            # Validate Hash here (TODO)
            status_val = data.get("status")
            if status_val == "success" or status_val == "settled":
                self.process_payment_success(order_number)
                
        return Response({"result": "ok"}, status=200)


class ExternalUpdateCommodityView(APIView):
    """
    Proxies request to:
    PUT http://www.hnzczy.cn:8087/commodityinfo/updatecommodityinfolist
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        # 1. Fetch Token from External API
        token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
        token_params = {
            "userName": "C202405128888",
            "password": "8888"
        }
        
        print(f"DEBUG: Fetching token for UpdateCommodity from {token_url}")
        try:
            token_response = requests.get(token_url, params=token_params, timeout=10)
            token_data = token_response.json()
            token = token_data.get("data") or token_data.get("token")
            
            if not token:
                return Response({"error": "Could not fetch external vending token", "details": token_data}, status=status.HTTP_502_BAD_GATEWAY)

            # 2. Update Commodity Request using the token (PUT)
            url = "http://www.hnzczy.cn:8087/commodityinfo/updatecommodityinfolist"
            headers = {"Authorization": token}
            print(f"DEBUG: Putting commodity update to {url} with body {request.data}")
            
            # Forward the JSON body via PUT
            response = requests.put(url, json=request.data, headers=headers, timeout=30)
            print(f"DEBUG: Update payload: {request.data}")
            print(f"DEBUG: Update response: {response.status_code} - {response.text}")
            
            try:
                return Response(response.json(), status=response.status_code)
            except:
                return Response({"result": "unknown", "raw": response.text}, status=response.status_code)
            
        except Exception as e:
            print(f"DEBUG: Exception in ExternalUpdateCommodityView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
