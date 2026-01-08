from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .serializers import SignupSerializer, LoginSerializer
from .models import Profile, Address, PaymentMethod
from .serializers import ProfileSerializer, AddressSerializer, PaymentMethodSerializer
from rest_framework import generics, permissions
import pyotp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8080/signin"
    client_class = OAuth2Client


# ✅ Signup View

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        phone_number = request.data.get('phone_number')

        if not email or not password:
            return Response({"message": "Email and password are required."}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"message": "User already exists."}, status=400)

        user = User.objects.create_user(username=email, email=email, password=password)

        # ✅ Use the profile created by the signal
        profile = user.profile
        profile.phone_number = phone_number
        profile.save()

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "Signup successful",
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": profile.phone_number,
            },
        }, status=status.HTTP_201_CREATED)

# ✅ Login View
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(username=email, password=password)
            if not user:
                return Response({"message": "Invalid credentials"}, status=401)

            profile = user.profile

            if profile.two_factor_enabled:
                # Send OTP
                otp = pyotp.TOTP(profile.otp_secret).now()
                print(f"DEBUG OTP for {email}: {otp}")  # Remove this in production
                return Response({
                    "message": "2FA required",
                    "two_factor_enabled": True,
                    "email": user.email
                }, status=200)

            # 2FA not enabled → return token directly
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "phone_number": profile.phone_number,
                }
            }, status=200)

        return Response(serializer.errors, status=400)


# ✅ Verify OTP View
class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({"message": "Email and OTP are required."}, status=400)

        try:
            user = User.objects.get(email=email)
            profile = user.profile

            if not profile.two_factor_enabled:
                return Response({"message": "2FA is not enabled for this user."}, status=400)

            totp = pyotp.TOTP(profile.otp_secret)
            if not totp.verify(otp):
                return Response({"message": "Invalid OTP"}, status=400)

            # ✅ OTP verified → return token
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "OTP verified successfully",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "phone_number": profile.phone_number,
                }
            }, status=200)

        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)


# --------------------------
# Profile Detail / Update
# --------------------------
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# --------------------------
# Address Views (CRUD)
# --------------------------
class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.profile.addresses.all()

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.profile.addresses.all()


# --------------------------
# Payment Method Views (CRUD)
# --------------------------
class PaymentMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.profile.payment_methods.all()

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.profile.payment_methods.all()