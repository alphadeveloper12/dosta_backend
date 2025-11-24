from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinLengthValidator


# --------------------------
# Profile Model
# --------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Personal Info
    full_name = models.CharField(max_length=150, blank=True, null=True)
    company = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # 2FA
    otp_secret = models.CharField(max_length=255, null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)

    # Email notification preferences (JSON array)
    email_notifications = models.JSONField(
        default=list,
        help_text=(
            "Array of selected notifications. Options: "
            "['new_deals', 'password_changes', 'new_restaurants', 'special_offers', "
            "'order_statuses', 'newsletters']"
        ),
    )

    def __str__(self):
        return self.user.username


# --------------------------
# Address Model (One-to-Many)
# --------------------------
class Address(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, help_text="e.g., Home, Work, Other")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zone = models.CharField(max_length=100, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.label} - {self.city}"


# --------------------------
# Payment Method Model (One-to-Many)
# --------------------------
class PaymentMethod(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="payment_methods")
    card_number = models.CharField(
        max_length=16, validators=[MinLengthValidator(12)], help_text="Enter only last 12-16 digits"
    )
    expiration = models.CharField(max_length=7, help_text="MM/YYYY format")
    cvc = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=150)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return f"**** **** **** {self.card_number[-4:]} ({self.cardholder_name})"


# --------------------------
# Profile Signal (Auto Create/Update)
# --------------------------
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensures a Profile is created or updated for every User automatically.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
