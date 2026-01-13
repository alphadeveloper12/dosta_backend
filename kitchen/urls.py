from django.urls import path
from . import views

app_name = 'kitchen'

from catering.views import CateringKitchenDashboardView

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('tracking/', views.TrackingView.as_view(), name='tracking_dashboard'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('api/active-orders/', views.get_active_orders_api, name='active_orders_api'),
    path('menu-upload/', views.menu_upload_view, name='menu_upload'),
    path('vending-prices/', views.vending_prices_view, name='vending_prices'),
    path('vending-machine-items/', views.vending_machine_items_view, name='vending_machine_items'),
    path('update-vending-stock/', views.update_vending_stock, name='update_vending_stock'),
    path('daily-orders/', views.daily_orders_view, name='daily_orders'),
    
    # Catering Dashboard
    path('catering/', CateringKitchenDashboardView.as_view(), name='catering_dashboard'),
]
