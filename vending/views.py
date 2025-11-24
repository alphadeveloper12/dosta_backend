from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

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
    OrderStatus
)
from .serializers import (
    VendingLocationSerializer,
    UserLocationSelectionSerializer,
    MenuSerializer,
    PickupTimeSlotSerializer,
    MealPlanSerializer,
    OrderSerializer
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
                {"key": "SMART_GRAB", "label": "Smart Grab"}
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

        slots = PickupTimeSlot.objects.filter(location_id=location_id, is_active=True)
        serializer = PickupTimeSlotSerializer(slots, many=True)

        return Response({
            "pickup_types": [
                {"key": "TODAY", "label": "Pickup Today"},
                {"key": "IN_24_HOURS", "label": "Pickup in 24 Hours"}
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
            for day, _ in DayOfWeek.choices:
                menu = Menu.objects.filter(day_of_week=day).first()
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
                    menu = Menu.objects.filter(day_of_week=day).first()
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
                week_number=item.get("week_number")
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
