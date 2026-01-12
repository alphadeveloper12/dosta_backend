from django.urls import path
from .views import *

urlpatterns = [
    path('event-types/', EventTypeListView.as_view(), name='event-type-list'),
    path('provider-types/', ProviderTypeListView.as_view(), name='provider-type-list'),
    path('event-names/', EventNameListView.as_view(), name='event-name-list'),
    path('service-styles/', ServiceStyleListView.as_view(), name='service-style-list'),
    path('service-styles-private/', ServiceStylePrivateListView.as_view(), name='service-style-private-list'),
    path('cuisines/', CuisineListView.as_view(), name='cuisine-list'),
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('menu-items/', MenuItemListView.as_view(), name='menu-item-list'),
    path('locations/', LocationListView.as_view(), name='location-list'),
    path('budget-options/', BudgetOptionListView.as_view(), name='budget-option-list'),
    path('pax/', PaxListView.as_view(), name='pax-list'),
    path('coffee-break-rotations/', CoffeeBreakRotationListView.as_view(), name='coffee-break-rotation-list'),
    path('platter-items/', PlatterItemListView.as_view(), name='platter-item-list'),
    path('boxed-meal-items/', BoxedMealItemListView.as_view(), name='boxed-meal-item-list'),
    path('live-station-items/', LiveStationItemListView.as_view(), name='live-station-item-list'),
    path('fixed-menus/', FixedCateringMenuListView.as_view(), name='fixed-menu-list'),
    path('american-menus/', AmericanMenuListView.as_view(), name='american-menu-list'),
    path('canape-items/', CanapeItemListView.as_view(), name='canape-item-list'),
    # Catering Orders
    path('orders/create/', CreateCateringOrderView.as_view(), name='create-catering-order'),
    # path('kitchen/dashboard/', CateringKitchenDashboardView.as_view(), name='catering-kitchen-dashboard'), # Moved to kitchen app
    path('kitchen/active-orders/', get_active_catering_orders, name='active-catering-orders-api'),
]
