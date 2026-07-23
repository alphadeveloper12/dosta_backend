import hashlib
import requests
import json
from django.conf import settings

# Credentials (TODO: Move to settings/env variables in production)
CHECKOUT_HOST = "https://checkout.totalpay.global"
MERCHANT_KEY = "9f2b59d8-faac-11f0-8550-c6e030555838"
MERCHANT_PASSWORD = "252c85da0a226f5cfa5efd93975a15f1"
OPERATION = "purchase"
CURRENCY = "AED"

class TotalPayService:
    @staticmethod
    def _generate_signature(order_number, amount, currency, description):
        """
        Signature = SHA1(MD5(UPPER(order.number + order.amount + order.currency + order.description + merchant.pass)))
        """
        # Ensure amount is formatted correctly (e.g. "100.00")
        # The API docs say: Format for 2-exponent currencies: XX.XX Example: 100.99
        # We need to make sure the amount string used here matches exactly what is sent in the payload.
        
        raw_string = f"{order_number}{amount}{currency}{description}{MERCHANT_PASSWORD}"
        upper_string = raw_string.upper()
        
        md5_hash = hashlib.md5(upper_string.encode('utf-8')).hexdigest()
        sha1_hash = hashlib.sha1(md5_hash.encode('utf-8')).hexdigest()
        
        return sha1_hash

    @staticmethod
    def initiate_session(order, user, billing_address, success_url, cancel_url):
        url = f"{CHECKOUT_HOST}/api/v1/session"
        
        # Format amount to 2 decimal places
        amount_str = "{:.2f}".format(float(order.total_amount))
        description = getattr(order, 'description', f"Order #{order.id}")
        
        signature = TotalPayService._generate_signature(
            order_number=str(order.id),
            amount=amount_str,
            currency=CURRENCY,
            description=description
        )

        country = billing_address.country if billing_address and billing_address.country else "AE"
        
        # Simple mapping for common case (expand if needed)
        # TotalPay strictly requires 2-letter ISO code
        if country.lower() in ["united arab emirates", "uae", "u.a.e"]:
            country = "AE"
        
        # Truncate if somehow longer but not mapped (fallback safety)
        if len(country) > 2:
            country = country[:2].upper()

        payload = {
            "merchant_key": MERCHANT_KEY,
            "operation": OPERATION,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "hash": signature,
            "order": {
                "number": str(order.id),
                "amount": amount_str,
                "currency": CURRENCY,
                "description": description
            },
            "customer": {
                "name": user.profile.full_name or user.username,
                "email": user.email,
            },
            "billing_address": {
                "country": country,
                "city": billing_address.city if billing_address else "Dubai",
                "address": billing_address.address_line_1 if billing_address else "Unknown",
                "zip": billing_address.zone if (billing_address and billing_address.zone) else "00000" # Use zone as zip or default
            }
        }
        
        # Add phone if available
        if user.profile.phone_number:
            payload["customer"]["phone"] = user.profile.phone_number

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and "redirect_url" in response_data:
                return response_data["redirect_url"]
            else:
                # Log error details suitable for debugging but careful with sensitivity
                error_msg = f"TotalPay Error: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(f"Payment Gateway Error: {response_data.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"Payment Exception: {str(e)}")
            raise e
