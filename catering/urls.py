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
    path('budget-options-private/', BudgetOptionPrivateListView.as_view(), name='budget-option-private-list'),
    path('pax/', PaxListView.as_view(), name='pax-list'),
    path('pax-private/', PaxPrivateListView.as_view(), name='pax-private-list'),

    
]
