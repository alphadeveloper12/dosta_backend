from django.core.management.base import BaseCommand
from ai_agents.models import ScraperSchedule
from ai_agents.scraper.lead_scraper import scrape_leads_with_progress
import datetime
import time

class Command(BaseCommand):
    help = 'Runs the automated lead scraper if it is the scheduled time'

    def handle(self, *args, **options):
        self.stdout.write("[*] Checking Lead Scraper Schedule...")
        
        schedule, _ = ScraperSchedule.objects.get_or_create(id=1)
        if not schedule.is_enabled:
            self.stdout.write("[-] Scraper is disabled in settings.")
            return

        now = datetime.datetime.now()
        current_time = now.time()
        
        # Check if it's around the scheduled time (within 1 hour window)
        # and it hasn't run today yet
        window_start = datetime.datetime.combine(now.date(), schedule.run_time)
        window_end = window_start + datetime.timedelta(hours=1)
        
        if window_start <= now <= window_end:
            if schedule.last_automated_run and schedule.last_automated_run.date() == now.date():
                self.stdout.write("[-] Scraper already ran today.")
                return
            
            self.stdout.write(f"[*] Starting Scheduled Scraping Run (Time: {now.strftime('%H:%M')})...")
            
            # Update last run time before starting to avoid double-triggers
            schedule.last_automated_run = now
            schedule.save()
            
            try:
                scrape_leads_with_progress(status_id=1)
                self.stdout.write(self.style.SUCCESS("[+] Scheduled scraping task completed."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[!] Scraper failed: {e}"))
        else:
            self.stdout.write(f"[-] Not time yet. Scheduled for: {schedule.run_time.strftime('%H:%M')}")
