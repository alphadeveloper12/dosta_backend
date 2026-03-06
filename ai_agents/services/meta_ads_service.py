import os
import requests
from django.conf import settings

class MetaAdsService:
    """Service to interact with Meta/Facebook Graph API for marketing stats"""
    
    BASE_URL = "https://graph.facebook.com/v19.0"

    @classmethod
    def get_headers(cls):
        token = getattr(settings, 'META_SYSTEM_USER_TOKEN', None)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    @classmethod
    def get_daily_performance(cls):
        """
        Fetches daily performance stats (Spend, Impressions, Clicks) 
        from the specified Meta Ad Account.
        Uses mocked data if tokens are not configured.
        """
        account_id = getattr(settings, 'META_AD_ACCOUNT_ID', None)
        token = getattr(settings, 'META_SYSTEM_USER_TOKEN', None)

        # MOCK IMPLEMENTATION FOR DEVELOPMENT
        if not account_id or not token:
            print("[*] Meta Ads API credentials missing. Returning mock data.")
            return {
                "platform": "Meta (Facebook/Instagram)",
                "status": "mocked",
                "spend": 125.50,
                "impressions": 15000,
                "clicks": 450,
                "cpc": 0.28,
                "ctr": "3.00%",
                "top_campaign": "Ramadan Catering 2026"
            }

        # ACTUAL API CALL (Ready for production keys)
        try:
            url = f"{cls.BASE_URL}/act_{account_id}/insights"
            params = {
                "date_preset": "today",
                "fields": "spend,impressions,clicks,cpc,ctr,campaign_name",
                "level": "campaign"
            }
            
            response = requests.get(url, headers=cls.get_headers(), params=params)
            response.raise_for_status()
            data = response.json().get('data', [])
            
            # Aggregate stats
            total_spend = sum(float(item.get('spend', 0)) for item in data)
            total_impressions = sum(int(item.get('impressions', 0)) for item in data)
            total_clicks = sum(int(item.get('clicks', 0)) for item in data)
            
            return {
                "platform": "Meta (Facebook/Instagram)",
                "status": "success",
                "spend": round(total_spend, 2),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "raw_campaigns": data
            }

        except Exception as e:
            print(f"[!] Meta Ads API Error: {str(e)}")
            return {
                "platform": "Meta (Facebook/Instagram)",
                "status": "error",
                "message": str(e)
            }
