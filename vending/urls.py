from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendingLocationViewSet,
    PlanTypeOptionsView,
    PickupOptionsView,
    MenuByTypeView,
    PlanOptionsView,
    PlanMenuView,
    SavedPlansView,
    ConfirmOrderView,
    OrderProgressView,
    CartView,
    UserOrdersView,
)

# -----------------------------------------------------------
# ROUTER: For read-only ViewSets
# -----------------------------------------------------------
router = DefaultRouter()
router.register(r'locations', VendingLocationViewSet, basename='locations')

# -----------------------------------------------------------
# CUSTOM API ENDPOINTS
# -----------------------------------------------------------
urlpatterns = [
    # router endpoints
    path('', include(router.urls)),

    # step-based workflow endpoints
    path('plan-types/', PlanTypeOptionsView.as_view(), name='plan-types'),
    path('pickup-options/', PickupOptionsView.as_view(), name='pickup-options'),
    path('menu/<str:plan_type>/', MenuByTypeView.as_view(), name='menu-by-type'),
    path('menu/plan/<str:subtype>/', PlanMenuView.as_view(), name='plan-menu'),
    path('plan-options/', PlanOptionsView.as_view(), name='plan-options'),
    path('saved-plans/', SavedPlansView.as_view(), name='saved-plans'),
    path('order/confirm/', ConfirmOrderView.as_view(), name='order-confirm'),
    path('order/progress/', OrderProgressView.as_view(), name='order-progress'),
    path('orders/', UserOrdersView.as_view(), name='user-orders'),
    path('cart/', CartView.as_view(), name='cart'),
]
