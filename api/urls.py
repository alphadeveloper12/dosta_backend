from django.urls import path
from .views import (
    SignupView,
    LoginView,
    VerifyOTPView,
    ProfileView,
    AddressListCreateView,
    AddressDetailView,
    PaymentMethodListCreateView,
    PaymentMethodDetailView,
)

urlpatterns = [
    # Auth
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # Profile
    path('profile/', ProfileView.as_view(), name='user-profile'),

    # Addresses
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),

    # Payment Methods
    path('payment-methods/', PaymentMethodListCreateView.as_view(), name='payment-list-create'),
    path('payment-methods/<int:pk>/', PaymentMethodDetailView.as_view(), name='payment-detail'),
]
