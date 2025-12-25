from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('api/active-orders/', views.get_active_orders_api, name='active_orders_api'),
    path('menu-upload/', views.menu_upload_view, name='menu_upload'),
]
