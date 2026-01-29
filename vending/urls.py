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
    UpdatePickupCodeView,
    data_upload_view,
    ExternalCheckUserView,
    ExternalMachineGoodsView,
    ExternalProductionPickView,
    ExternalUpdateCommodityView,
    KitchenOrderItemCompleteView,
    PaymentCallbackView
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

    # Data Upload Page (HTML)
    path('upload-locations/', data_upload_view, name='upload-locations'),

    # step-based workflow endpoints
    path('plan-types/', PlanTypeOptionsView.as_view(), name='plan-types'),
    path('pickup-options/', PickupOptionsView.as_view(), name='pickup-options'),
    path('menu/<str:plan_type>/', MenuByTypeView.as_view(), name='menu-by-type'),
    path('menu/plan/<str:subtype>/', PlanMenuView.as_view(), name='plan-menu'),
    path('plan-options/', PlanOptionsView.as_view(), name='plan-options'),
    path('saved-plans/', SavedPlansView.as_view(), name='saved-plans'),
    path('order/confirm/', ConfirmOrderView.as_view(), name='order-confirm'),
    path('order/update-pickup-code/', UpdatePickupCodeView.as_view(), name='order-update-pickup-code'),
    path('order/progress/', OrderProgressView.as_view(), name='order-progress'),
    path('orders/', UserOrdersView.as_view(), name='user-orders'),
    path('cart/', CartView.as_view(), name='cart'),
    path('kitchen/complete-item/', KitchenOrderItemCompleteView.as_view(), name='kitchen-complete-item'),

    # External Vending API Proxies
    path('external/check-user/', ExternalCheckUserView.as_view(), name='external-check-user'),
    path('external/machine-goods/', ExternalMachineGoodsView.as_view(), name='external-machine-goods'),
    path('external/production-pick/', ExternalProductionPickView.as_view(), name='external-production-pick'),
    path('external/update-commodity/', ExternalUpdateCommodityView.as_view(), name='external-update-commodity'),
    
    path('payment/callback/', PaymentCallbackView.as_view(), name='payment-callback'),
]
