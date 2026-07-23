import os
import json
import openai
from django.core.management.base import BaseCommand
from ai_agents.services.meta_ads_service import MetaAdsService
from ai_agents.services.google_ads_service import GoogleAdsService
from ai_agents.models import MarketingReport

class Command(BaseCommand):
    help = 'Runs the daily marketing AI analysis by fetching cross-platform ad stats.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[*] Starting Daily Marketing AI Report...'))

        # 1. Fetch Stats from APIs
        self.stdout.write('[*] Fetching Meta Ads performance...')
        meta_stats = MetaAdsService.get_daily_performance()
        
        self.stdout.write('[*] Fetching Google/YouTube Ads performance...')
        google_stats = GoogleAdsService.get_daily_performance()

        # 2. Prepare Data for AI Agent
        raw_data = {
            "Meta": meta_stats,
            "Google": google_stats
        }
        
        system_prompt = """
        You are the 'Dosta Creative Marketer', a senior digital marketing analyst for a luxury catering and smart vending company in the UAE.
        Your task is to review the raw daily performance metrics from our Meta (Facebook/WhatsApp/Instagram) and Google/YouTube ad campaigns.
        
        Based on the data provided, write a concise, professional 2-3 paragraph 'Daily Briefing' for the executive team.
        Highlight the total spend, best performing campaigns, and provide 1-2 strategic recommendations based on the Cost Per Click/View and Conversions.
        Do not use markdown headers, just plain text paragraphs.
        """

        openai.api_key = os.getenv("OPENAI_API_KEY")

        try:
            self.stdout.write('[*] Sending data to AI Marketing Agent for analysis...')
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is today's raw ad performance data in JSON format:\n\n{json.dumps(raw_data, indent=2)}"}
                ],
                max_tokens=500,
                temperature=0.4
            )
            analysis_text = response.choices[0].message.content.strip()

            # 3. Save to Database
            meta_spend = meta_stats.get('spend', 0.0) if meta_stats.get('status') != 'error' else 0.0
            google_spend = google_stats.get('spend', 0.0) if google_stats.get('status') != 'error' else 0.0

            report = MarketingReport.objects.create(
                meta_spend=meta_spend,
                google_spend=google_spend,
                ai_analysis_text=analysis_text
            )

            self.stdout.write(self.style.SUCCESS(f'[+] Successfully generated and saved Marketing Report ID: {report.id}'))
            
            # 4. Automaticaly suggest a new ad if Meta stats are available
            if meta_stats.get('status') != 'error':
                self.stdout.write('[*] Generating AI Ad Suggestion based on today\'s performance...')
                draft = MetaAdsService.generate_draft(meta_stats)
                if draft:
                    self.stdout.write(self.style.SUCCESS(f'[+] New ad draft suggested for Admin approval: {draft.headline}'))
            
            self.stdout.write(f"\n--- AI BRIEFING ---\n{analysis_text}\n-------------------")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[!] Failed to generate AI report: {str(e)}'))
