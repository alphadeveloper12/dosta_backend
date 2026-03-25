from django.urls import path
from . import views

app_name = 'kitchen'

from catering.views import CateringKitchenDashboardView, CateringOrderDetailView

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('tracking/', views.TrackingView.as_view(), name='tracking_dashboard'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('api/active-orders/', views.get_active_orders_api, name='active_orders_api'),
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('order-item/<int:pk>/update-status/', views.update_item_status, name='update_item_status'),
    path('menu-upload/', views.menu_upload_view, name='menu_upload'),
    path('vending-prices/', views.vending_prices_view, name='vending_prices'),
    path('vending-machine-items/', views.vending_machine_items_view, name='vending_machine_items'),
    path('update-vending-stock/', views.update_vending_stock, name='update_vending_stock'),
    path('daily-orders/', views.daily_orders_view, name='daily_orders'),
    path('agents/', views.agent_dashboard_view, name='agent_dashboard'),
    path('agents/api/', views.agent_dashboard_api, name='agent_dashboard_api'),
    path('agents/ad-draft/<int:pk>/approve/', views.approve_ad_draft, name='approve_ad_draft'),
    path('agents/ad-draft/<int:pk>/reject/', views.reject_ad_draft, name='reject_ad_draft'),
    
    # Catering Dashboard
    path('catering/', CateringKitchenDashboardView.as_view(), name='catering_dashboard'),
    path('catering/order/<int:pk>/', CateringOrderDetailView.as_view(), name='catering_order_detail'),

    # Master Items Management
    path('master-items/vending/', views.VendingMasterListView.as_view(), name='vending_master_list'),
    path('master-items/vending/weekly/', views.WeeklyVendingAssignmentView.as_view(), name='vending_weekly_assignment'),
    path('master-items/vending/weekly/save/', views.save_weekly_vending_assignment, name='save_vending_weekly_assignment'),
    path('master-items/vending/monthly/', views.MonthlyVendingAssignmentView.as_view(), name='vending_monthly_assignment'),
    path('master-items/vending/monthly/save/', views.save_monthly_vending_assignment, name='save_vending_monthly_assignment'),
    path('master-items/vending/<int:pk>/edit/', views.vending_master_item_edit_view, name='vending_master_item_edit'),
    path('master-items/vending/<int:pk>/schedule/', views.vending_master_schedule_api, name='vending_master_schedule_api'),
    path('master-items/vending/sync/', views.sync_vending_master_items, name='sync_vending_master'),
    path('master-items/catering/', views.CateringMasterListView.as_view(), name='catering_master_list'),
    path('master-items/catering/sync/', views.sync_catering_master_items, name='sync_catering_master'),
    
    # Logout
    path('logout/', views.kitchen_logout_view, name='logout'),
]
