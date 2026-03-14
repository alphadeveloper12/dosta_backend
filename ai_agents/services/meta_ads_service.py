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
    @classmethod
    def generate_draft(cls, performance_data):
        """
        Uses OpenAI to generate a new ad draft based on past performance data.
        Returns an unsaved AdDraft object.
        """
        import openai
        from ai_agents.models import AdDraft
        
        openai.api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv("OPENAI_API_KEY"))
        
        system_prompt = """
        You are the 'Dosta Creative Marketer'. Based on the provided performance metrics, 
        suggest a NEW ad campaign to improve ROI.
        
        Output MUST be valid JSON with the following fields:
        - headline: Catchy headline (max 40 chars)
        - body_text: Persuasive ad copy (max 125 chars)
        - targeting_summary: A plain-english description of the audience to target.
        - budget: Suggested daily budget in AED (numeric).
        """
        
        try:
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Current performance: {performance_data}"}
                ],
                response_format={ "type": "json_object" }
            )
            
            import json
            suggestion = json.loads(response.choices[0].message.content)
            
            draft = AdDraft(
                platform="Meta",
                headline=suggestion.get('headline', 'Dosta Fresh Catering'),
                body_text=suggestion.get('body_text', 'Order the best catering in UAE.'),
                targeting_summary=suggestion.get('targeting_summary', 'Professionals in Dubai/Abu Dhabi'),
                budget=suggestion.get('budget', 50.00),
                status='Pending Approval'
            )
            draft.save()

            # Notify Admin
            from ai_agents.services.agent_service import AgentService
            admin_phone = getattr(settings, 'ADMIN_PHONE', '971509171092')
            msg = f"📢 *NEW AD DRAFT GENERATED*\n\n*Platform:* {draft.platform}\n*Headline:* {draft.headline}\n*Budget:* ${draft.budget}\n\nPlease review and approve: https://dosta.ae/kitchen/agents/"
            AgentService.send_whatsapp_message(admin_phone, msg)
            
            return draft
        except Exception as e:
            print(f"[!] Error generating draft: {str(e)}")
            return None

    @classmethod
    def publish_ad(cls, draft):
        """
        Publishes the approved AdDraft to Meta via Graph API.
        Sequence: 1. Creative -> 2. AdSet -> 3. Ad
        Returns (success_bool, platform_id_or_error_msg)
        """
        account_id = getattr(settings, 'META_AD_ACCOUNT_ID', None)
        token = getattr(settings, 'META_SYSTEM_USER_TOKEN', None)
        page_id = getattr(settings, 'META_PAGE_ID', '106093452243765') # Fallback if not in settings

        if not account_id or not token:
            print("[*] Meta Ads API credentials missing. Simulating publish.")
            import os
            return True, f"mock_meta_ad_{os.urandom(4).hex()}"

        try:
            headers = cls.get_headers()
            base_url = f"{cls.BASE_URL}/act_{account_id}"

            # STEP 1: Create Ad Creative
            # Note: For now we assume a link ad to the main website
            creative_url = f"{base_url}/adcreatives"
            creative_data = {
                "name": f"Creative for {draft.headline}",
                "object_type": "SHARE",
                "object_story_spec": {
                    "page_id": page_id,
                    "link_data": {
                        "message": draft.body_text,
                        "link": "https://dosta.ae",
                        "caption": "Dosta Fresh Catering",
                        "name": draft.headline,
                    }
                }
            }
            
            print(f"[*] Meta API Step 1: Creating Creative...")
            creative_res = requests.post(creative_url, headers=headers, json=creative_data)
            creative_id = creative_res.json().get('id')
            if not creative_id:
                return False, f"Creative Error: {creative_res.text}"

            # STEP 2: Create Ad Set
            # We create a simple awareness ad set with the draft budget
            adset_url = f"{base_url}/adsets"
            adset_data = {
                "name": f"AdSet: {draft.headline}",
                "optimization_goal": "REACH",
                "billing_event": "IMPRESSIONS",
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "daily_budget": int(draft.budget * 100), # Subunits (fills/cents)
                "campaign_id": "120210202283760565", # Default Awareness Campaign
                "targeting": {
                    "geo_locations": {"countries": ["AE"]},
                    "publisher_platforms": ["facebook", "instagram"]
                },
                "status": "PAUSED" # Keep paused for safety during Phase 2
            }

            print(f"[*] Meta API Step 2: Creating AdSet...")
            adset_res = requests.post(adset_url, headers=headers, json=adset_data)
            adset_id = adset_res.json().get('id')
            if not adset_id:
                return False, f"AdSet Error: {adset_res.text}"

            # STEP 3: Create Ad
            ad_url = f"{base_url}/ads"
            ad_data = {
                "name": f"Ad: {draft.headline}",
                "adset_id": adset_id,
                "creative": {"creative_id": creative_id},
                "status": "PAUSED"
            }

            print(f"[*] Meta API Step 3: Creating Ad...")
            ad_res = requests.post(ad_url, headers=headers, json=ad_data)
            ad_id = ad_res.json().get('id')
            
            if ad_id:
                print(f"✅ Meta Ad Publication Successful. Ad ID: {ad_id}")
                return True, ad_id
            else:
                return False, f"Ad Error: {ad_res.text}"

        except Exception as e:
            print(f"[!] Meta API Critical Failure: {str(e)}")
            return False, str(e)
