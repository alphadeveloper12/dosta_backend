import requests
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.authtoken.models import Token
from .serializers import SignupSerializer, LoginSerializer
from .models import Profile, Address, PaymentMethod
from .serializers import ProfileSerializer, AddressSerializer, PaymentMethodSerializer
from rest_framework import generics
import pyotp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8080/signin"
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        id_token = request.data.get('id_token')
        access_token = request.data.get('access_token')

        # If it's One Tap flow (has id_token but no access_token)
        if id_token and not access_token:
            verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            try:
                resp = requests.get(verify_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    email = data.get('email')
                    if email:
                        # Find or create user
                        user, created = User.objects.get_or_create(
                            email=email, 
                            defaults={'username': email.split('@')[0]}
                        )
                        # Ensure user has a profile if it's new
                        if created and not hasattr(user, 'profile'):
                            Profile.objects.create(user=user)
                        
                        token, _ = Token.objects.get_or_create(user=user)
                        return Response({
                            "key": token.key,
                            "token": token.key,
                            "user": {
                                "id": user.id,
                                "email": user.email,
                                "username": user.username
                            }
                        })
                return Response({"error": "Invalid ID Token"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Fallback to standard flow for access_token
        return super().post(request, *args, **kwargs)


# ✅ Signup View

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        phone_number = request.data.get('phone_number')
        two_factor_enabled = request.data.get('two_factor_enabled', False)

        if not email or not password:
            return Response({"message": "Email and password are required."}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"message": "User already exists."}, status=400)

        user = User.objects.create_user(username=email, email=email, password=password)

        # ✅ Use the profile created by the signal
        profile = user.profile
        profile.phone_number = phone_number
        profile.two_factor_enabled = two_factor_enabled
        profile.otp_secret = pyotp.random_base32()
        profile.save()

        if two_factor_enabled:
            # ✅ Generate OTP and send via Twilio
            otp = pyotp.TOTP(profile.otp_secret).now()
            # self.send_otp_to_phone(phone_number, otp) # Placeholder
            return Response({"message": "User created. Please verify OTP."}, status=201)

        # ✅ If 2FA is false, log them in immediately
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": ProfileSerializer(profile).data
        }, status=201)


# ✅ Login View

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(username=email, password=password)

        if user:
            profile = user.profile
            if profile.two_factor_enabled:
                otp = pyotp.TOTP(profile.otp_secret).now()
                # self.send_otp_to_phone(profile.phone_number, otp) # Placeholder
                return Response({"message": "OTP sent."}, status=200)

            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user": ProfileSerializer(profile).data}, status=200)

        return Response({"message": "Invalid email or password."}, status=401)


# ✅ Verify OTP View

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        try:
            user = User.objects.get(email=email)
            profile = user.profile
            totp = pyotp.TOTP(profile.otp_secret)

            if totp.verify(otp):
                token, _ = Token.objects.get_or_create(user=user)
                return Response({"token": token.key, "user": ProfileSerializer(profile).data}, status=200)

            return Response({"message": "Invalid OTP."}, status=401)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=404)


# ✅ Profile View

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# ✅ Address Views

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


# ✅ Payment Method Views

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


# ✅ Delete Account View
# Required by Apple App Store guideline 5.1.1(v): apps that support account
# creation must offer in-app account deletion.
class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        confirmation = (request.data.get('confirmation') or '').strip().upper()
        password = request.data.get('password') or ''

        if confirmation != 'DELETE':
            return Response(
                {"message": "Please type DELETE to confirm account deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Users created via Google OAuth have no usable password — for them
        # the typed "DELETE" confirmation alone is sufficient. Anyone with a
        # local password must re-enter it to authorize the deletion.
        if user.has_usable_password():
            if not password or not user.check_password(password):
                return Response(
                    {"message": "Incorrect password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            Token.objects.filter(user=user).delete()
            user.delete()

        return Response(
            {"message": "Account deleted successfully."},
            status=status.HTTP_200_OK,
        )