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
    path('accounts/', views.AccountsDashboardView.as_view(), name='accounts_dashboard'),
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
    path('master-items/vending/create/', views.vending_master_item_create_view, name='vending_master_item_create'),
    path('master-items/vending/<int:pk>/edit/', views.vending_master_item_edit_view, name='vending_master_item_edit'),
    path('master-items/vending/<int:pk>/delete/', views.vending_master_item_delete_view, name='vending_master_item_delete'),
    path('master-items/vending/<int:pk>/schedule/', views.vending_master_schedule_api, name='vending_master_schedule_api'),
    path('master-items/vending/sync/', views.sync_vending_master_items, name='sync_vending_master'),
    path('master-items/vending/category/create/', views.vending_category_create_view, name='vending_category_create'),
    path('master-items/vending/categorize/', views.vending_categorize_items_view, name='vending_categorize'),
    path('master-items/catering/', views.CateringMasterListView.as_view(), name='catering_master_list'),
    path('master-items/catering/create/', views.catering_master_item_create_view, name='catering_master_item_create'),
    path('master-items/catering/sync/', views.sync_catering_master_items, name='sync_catering_master'),
    
    # Fulfillment management
    path('order/<int:order_id>/retry-fulfillment/', views.kitchen_retry_fulfillment, name='retry_fulfillment'),
    path('order/<int:order_id>/mark-qr-used/', views.kitchen_mark_qr_used, name='mark_qr_used'),

    # Locations
    path('locations/', views.locations_view, name='locations'),
    path('locations/manage/', views.locations_manage, name='locations_manage'),

    # Location-based item prices (per-machine pricing)
    path('location-prices/', views.location_based_prices_view, name='location_based_prices'),
    path('location-prices/set/', views.location_price_set, name='location_price_set'),
    path('location-prices/bulk-save/', views.location_prices_bulk_save, name='location_prices_bulk_save'),
    path('location-prices/restore/', views.location_prices_restore, name='location_prices_restore'),
    path('location-prices/source-data/', views.location_prices_source_data, name='location_prices_source_data'),
    path('location-prices/copy-from/', views.location_prices_copy_from, name='location_prices_copy_from'),
    path('location-prices/clear/', views.location_price_clear, name='location_price_clear'),

    # Beit Nahla panel (single-page AJAX CRUD)
    path('beit-nahla/', views.beit_nahla_panel_view, name='beit_nahla_panel'),
    path('beit-nahla/api/settings/', views.beit_nahla_settings_api, name='bn_settings_api'),
    path('beit-nahla/api/tiers/create/', views.beit_nahla_tier_create_api, name='bn_tier_create'),
    path('beit-nahla/api/tiers/<int:pk>/update/', views.beit_nahla_tier_update_api, name='bn_tier_update'),
    path('beit-nahla/api/tiers/<int:pk>/delete/', views.beit_nahla_tier_delete_api, name='bn_tier_delete'),
    path('beit-nahla/api/boxes/create/', views.beit_nahla_meal_box_create_api, name='bn_box_create'),
    path('beit-nahla/api/boxes/<int:pk>/update/', views.beit_nahla_meal_box_update_api, name='bn_box_update'),
    path('beit-nahla/api/boxes/<int:pk>/delete/', views.beit_nahla_meal_box_delete_api, name='bn_box_delete'),
    path('beit-nahla/api/categories/create/', views.beit_nahla_category_create_api, name='bn_cat_create'),
    path('beit-nahla/api/categories/<int:pk>/update/', views.beit_nahla_category_update_api, name='bn_cat_update'),
    path('beit-nahla/api/categories/<int:pk>/delete/', views.beit_nahla_category_delete_api, name='bn_cat_delete'),
    path('beit-nahla/api/items/create/', views.beit_nahla_item_create_api, name='bn_item_create'),
    path('beit-nahla/api/items/<int:pk>/update/', views.beit_nahla_item_update_api, name='bn_item_update'),
    path('beit-nahla/api/items/<int:pk>/delete/', views.beit_nahla_item_delete_api, name='bn_item_delete'),

    # Beit Nahla orders
    path('beit-nahla/orders/', views.beit_nahla_orders_view, name='bn_orders'),
    path('beit-nahla/api/orders/<int:pk>/status/', views.beit_nahla_order_status_api, name='bn_order_status'),
    path('beit-nahla/api/active-orders/', views.get_active_beit_nahla_orders_api, name='bn_active_orders_api'),

    # Logout
    path('logout/', views.kitchen_logout_view, name='logout'),
]
