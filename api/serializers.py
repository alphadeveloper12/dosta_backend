import os
import pyotp
import random
import string
from twilio.rest import Client
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Address, PaymentMethod



class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(write_only=True, required=False)
    two_factor_enabled = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'phone_number', 'otp', 'two_factor_enabled']

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        phone_number = validated_data.get('phone_number')
        two_factor_enabled = validated_data.get('two_factor_enabled', False)

        # ✅ Generate unique username (avoid UNIQUE constraint errors)
        base_username = email.split('@')[0]
        username = base_username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{''.join(random.choices(string.digits, k=3))}"

        # ✅ Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # ✅ Ensure profile exists (created automatically by signal)
        profile = user.profile
        profile.phone_number = phone_number
        profile.otp_secret = pyotp.random_base32()
        profile.two_factor_enabled = two_factor_enabled
        profile.save()

        # ✅ If 2FA is enabled, generate and send OTP
        if two_factor_enabled:
            otp = pyotp.TOTP(profile.otp_secret).now()
            self.send_otp_to_phone(phone_number, otp)

        return user

    def send_otp_to_phone(self, phone_number, otp):
        """
        Sends OTP using Twilio API.
        """
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')

            if not all([account_sid, auth_token, from_number]):
                print("⚠️ Twilio environment variables are missing.")
                return

            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"Your OTP code is: {otp}",
                from_=from_number,
                to=phone_number
            )
        except Exception as e:
            print("⚠️ Twilio sending error:", e)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)



# --------------------------
# Profile Serializer
# --------------------------
class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "user_email",
            "full_name",
            "company",
            "phone_number",
            "two_factor_enabled",
            "email_notifications",
        ]


# --------------------------
# Address Serializer
# --------------------------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "address_line_1",
            "address_line_2",
            "city",
            "country",
            "zone",
            "is_default",
        ]


# --------------------------
# Payment Method Serializer
# --------------------------
class PaymentMethodSerializer(serializers.ModelSerializer):
    masked_card = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "masked_card",
            "card_number",
            "expiration",
            "cvc",
            "cardholder_name",
            "is_default",
        ]
        extra_kwargs = {
            "cvc": {"write_only": True},
            "card_number": {"write_only": True},
        }

    def get_masked_card(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"