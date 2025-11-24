from django.urls import path
from .views import *

urlpatterns = [
    path('event-types/', EventTypeListView.as_view(), name='event-type-list'),
    path('provider-types/', ProviderTypeListView.as_view(), name='provider-type-list'),
    path('service-styles/', ServiceStyleListView.as_view(), name='service-style-list'),
    path('cuisines/', CuisineListView.as_view(), name='cuisine-list'),
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('locations/', LocationListView.as_view(), name='location-list'),
    path('budget-options/', BudgetOptionListView.as_view(), name='budget-option-list'),

    
]
