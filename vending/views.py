from rest_framework import viewsets, permissions, filters, status
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
    DayOfWeek,
    PlanType,
    PlanSubType,
    PickupTimeSlot,
    MealPlan,
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
    def get(self, request, plan_type):
        day = request.query_params.get("day")
        qs = Menu.objects.all()
        if day:
            qs = qs.filter(day_of_week=day)

        serializer = MenuSerializer(qs, many=True, context={'request': request})
        return Response({
            "plan_type": plan_type,
            "menus": serializer.data,
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
    def get(self, request, subtype):
        if subtype == "WEEKLY":
            week_data = {}
            # Defaults to Week 1 for weekly rotation unless specified otherwise
            for day, _ in DayOfWeek.choices:
                menu = Menu.objects.filter(day_of_week=day, week_number=1).first()
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
                    menu = Menu.objects.filter(day_of_week=day, week_number=week).first()
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

        order = Order.objects.create(
            user=request.user,
            location_id=data.get("location_id"),
            plan_type=data.get("plan_type"),
            plan_subtype=data.get("plan_subtype", "NONE"),
            pickup_type=data.get("pickup_type"),
            pickup_date=data.get("pickup_date"),
            pickup_slot_id=data.get("pickup_slot_id"),
            status=OrderStatus.PENDING,
            current_step=6
        )

        for item in data.get("items", []):
            OrderItem.objects.create(
                order=order,
                menu_item_id=item["menu_item_id"],
                quantity=item.get("quantity", 1),
                day_of_week=item.get("day_of_week"),
                week_number=item.get("week_number"),
                vending_good_uuid=item.get("vending_good_uuid"),
                heating_requested=item.get("heating_requested", False),
                # Individual plan context
                plan_type=item.get("plan_type", order.plan_type),
                plan_subtype=item.get("plan_subtype", order.plan_subtype),
                pickup_type=item.get("pickup_type", order.pickup_type),
                pickup_date=item.get("pickup_date", order.pickup_date),
                pickup_slot=order.pickup_slot # Slot is usually shared per order
            )

        order.update_total()
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
            order.pickup_code = pickup_code
            # Generate QR code URL using a public API for simplicity
            order.qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pickup_code}"
            order.save()

            # NEW: Decrement stock for vending items
            for item in order.items.all():
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
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
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
            cart.location_id = data.get("location_id")
            incoming_plan_type = data.get("plan_type", PlanType.ORDER_NOW)
            incoming_plan_subtype = data.get("plan_subtype", PlanSubType.NONE)
            
            # Support clearing the entire cart
            if data.get("clear_all"):
                cart.items.all().delete()
                cart.update_total()
                return Response({"message": "Cart cleared successfully"}, status=status.HTTP_200_OK)

            cart.plan_type = incoming_plan_type
            cart.plan_subtype = incoming_plan_subtype
            cart.pickup_type = data.get("pickup_type")
            cart.pickup_date = data.get("pickup_date")
            cart.pickup_slot_id = data.get("pickup_slot_id")
            cart.current_step = data.get("current_step", 1)  # Save current step
            cart.save()

            # 3. Update Items (Partial Sync Strategy: Clear only items of the same plan type)
            if incoming_plan_type == PlanType.START_PLAN:
                cart.items.filter(plan_type=incoming_plan_type, plan_subtype=incoming_plan_subtype).delete()
            else:
                cart.items.filter(plan_type=incoming_plan_type).delete()

            items_data = data.get("items", [])
            for item in items_data:
                menu_item_id = item.get("menu_item_id")
                quantity = item.get("quantity", 1)
                day_of_week = item.get("day_of_week")
                week_number = item.get("week_number")
                vending_good_uuid = item.get("vending_good_uuid")
                heating_requested = item.get("heating_requested", False)

                if menu_item_id:
                    CartItem.objects.create(
                        cart=cart,
                        menu_item_id=menu_item_id,
                        quantity=quantity,
                        day_of_week=day_of_week,
                        week_number=week_number,
                        vending_good_uuid=vending_good_uuid,
                        heating_requested=heating_requested,
                        # Save context per item
                        plan_type=incoming_plan_type,
                        plan_subtype=incoming_plan_subtype,
                        pickup_type=cart.pickup_type,
                        pickup_date=cart.pickup_date,
                        pickup_slot=cart.pickup_slot
                    )

            cart.update_total()
            
            serializer = CartSerializer(cart, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
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
    permission_classes = [permissions.AllowAny]

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
            token_response = requests.get(token_url, params=token_params, timeout=30)
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
            
            response = requests.get(goods_url, params=params, headers=headers, timeout=30)
            api_data = response.json()
            
            # Transform the response to match the structure the frontend expects
            # (Grouped by shelf/tier, including all slots)
            if api_data.get("result") == "200" and "data" in api_data:
                slots = api_data.get("data") or []
                shelves = {}
                
                for slot in slots:
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
                        slot_data["goods"] = {
                            "uuid": str(goods.get("uuid")),
                            "goodsName": goods.get("goodsName"),
                            "goodsPrice": goods.get("goodsPrice"),
                            "goodsUrl": goods.get("goodsUrl"),
                            "goodsCode": goods.get("goodsCode"),
                            "goodsDesc": goods.get("goodsDesc"),
                        }
                    else:
                        slot_data["goods"] = None
                        
                    shelves[shelf_index].append(slot_data)
                
                # Sort shelves by index
                sorted_shelves = []
                unique_goods = {}
                for idx in sorted(shelves.keys()):
                    # Sort spots within shelf by modityTierNum
                    spots = sorted(shelves[idx], key=lambda x: x.get("modityTierNum", 0))
                    sorted_shelves.append({
                        "shelfIndex": idx,
                        "shelfName": f"Shelf {idx + 1}",
                        "spots": spots
                    })
                    
                    for spot in spots:
                        if spot["goods"]:
                            uuid = spot["goods"]["uuid"]
                            if uuid not in unique_goods:
                                unique_goods[uuid] = spot["goods"]
                
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
    permission_classes = [permissions.AllowAny]

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
            
            # Add heating parameters if requested
            if 'goodsList' in pick_payload:
                for item in pick_payload['goodsList']:
                    if item.get('heating_requested') is True or item.get('heatingChoice') == 'yes':
                        item['serviceType'] = 1
                        item['serviceVal'] = "15"
            
            
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


class ExternalUpdateCommodityView(APIView):
    """
    Proxies request to:
    PUT http://www.hnzczy.cn:8087/commodityinfo/updatecommodityinfolist
    """
    permission_classes = [permissions.AllowAny]

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
