import os
import sys
import django
import requests
import phonenumbers
from bs4 import BeautifulSoup
import re
import time

# Set up Django environment so we can use models
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dosta.settings")
django.setup()

from ai_agents.models import ScrapedLead, ScraperStatus

def extract_phone_numbers(text):
    """Extract UAE phone numbers from text (mobile and landline)."""
    numbers = set()
    try:
        # First try phonenumbers library
        for match in phonenumbers.PhoneNumberMatcher(text, "AE"):
            formatted = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
            numbers.add(formatted)
            
        # Regex for common UAE formats
        # Mobile: 050, 052, 054, 055, 056, 058
        # Landline: 04 (Dubai), 02 (Abu Dhabi), 03 (Al Ain), 06 (Sharjah/Ajman/UAQ), 07 (RAK), 09 (Fujairah)
        patterns = [
            r'\b(05[024568][0-9]{7})\b',   # Mobile
            r'\b(0[234679][0-9]{7})\b',    # Landline
            r'\+971[ ]?[2-9][0-9]{7,8}\b', # International format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for num in matches:
                # Basic normalization
                clean_num = num.replace(" ", "")
                if clean_num.startswith('0'):
                    clean_num = f"+971{clean_num[1:]}"
                elif not clean_num.startswith('+'):
                    clean_num = f"+971{clean_num}"
                numbers.add(clean_num)
                
    except Exception as e:
        print(f"Error extracting numbers: {e}")
    return list(numbers)

def scrape_leads(category="construction", num_results=100, status_obj=None, current_progress=0, max_progress=100):
    print(f"[*] Starting Lead Generation Scraper for YellowPages UAE (Category: {category}, Target: {num_results})")
    
    new_leads_found = 0
    duplicate_leads = 0
    page = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

    while new_leads_found < num_results:
        # Correct pagination: ?page=X
        if page == 1:
            url = f"https://www.yellowpages-uae.com/uae/{category}"
        else:
            url = f"https://www.yellowpages-uae.com/uae/{category}?page={page}"
            
        print(f"[-] Fetching: {url}")
        
        if status_obj:
            status_obj.current_source = f"YP: {category} (p{page})"
            status_obj.save()

        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"[!] Reached end of category or hit rate limit (Status {res.status_code}).")
                break
            soup = BeautifulSoup(res.text, 'html.parser')
        except Exception as e:
            print(f"[!] Error fetching directory: {e}")
            break

        # Refined block selector for YellowPages UAE
        # Listings are usually in div.box.row or similar
        blocks = soup.select('div.row.box, div.search-listing, div.item-listing')
        if not blocks:
            # Fallback to older regex if structure varies
            blocks = soup.find_all('div', class_=re.compile(r'item|card|listing', re.I))
            
        if not blocks:
            print("[!] Warning: No listing blocks found on page.")
            blocks = []
            
        page_leads_found = 0
        for block in blocks:
            # Find the company name in h3
            title_el = block.find('h3')
            if not title_el:
                title_el = block.find(['h2', 'a'], class_=re.compile(r'title|link', re.I))
            
            if not title_el:
                continue
                
            title = title_el.get_text(strip=True)
            # Clean "More Info" or other common suffixes
            title = re.sub(r'(More Info|Contact Details|Send Enquiry|Read More).*$', '', title, flags=re.I).strip()
            
            if len(title) < 2:
                continue
                
            # Extract phone numbers from tel: links AND text
            phone_numbers = set()
            
            # Explicitly look for tel: links which we know contain full numbers
            for a in block.find_all('a', href=re.compile(r'^tel:')):
                tel_num = a['href'].replace('tel:', '').strip()
                if tel_num:
                    # Normalize tel_num
                    if tel_num.startswith('0'):
                        tel_num = f"+971{tel_num[1:]}"
                    elif not tel_num.startswith('+'):
                        tel_num = f"+971{tel_num}"
                    phone_numbers.add(tel_num)
            
            # Fallback to text extraction
            text_content = block.get_text()
            phone_numbers.update(extract_phone_numbers(text_content))
            
            for phone in list(phone_numbers):
                # Check if lead already exists
                if not ScrapedLead.objects.filter(phone_number=phone).exists():
                    ScrapedLead.objects.create(
                        company_name=title[:250],
                        phone_number=phone,
                        status='New',
                        source=f"YellowPages UAE ({category.replace('-', ' ').title()})"
                    )
                    print(f"[+] SUCCESS! New lead saved: {title[:50]} | Phone: {phone}")
                    new_leads_found += 1
                    page_leads_found += 1
                    
                    if status_obj:
                        status_obj.leads_found += 1
                        status_obj.save()
                else:
                    duplicate_leads += 1
                    
                if new_leads_found >= num_results:
                    break
            if new_leads_found >= num_results:
                break
        
        if page_leads_found == 0 and page > 1:
            print(f"[*] No new leads on page {page}. Switching categories soon.")
            break
                
        # Move to next page for more results
        page += 1
        time.sleep(2)  # Polite delay

    return new_leads_found, duplicate_leads

def scrape_google_search(keyword="construction dubai", num_results=20, status_obj=None):
    """Simple scraper that uses Google Search to find business leads with phone numbers."""
    print(f"[*] Starting Google Search Lead Discovery (Keyword: {keyword})")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
    
    # Use queries that target aggregators or business profiles
    queries = [
        f"{keyword} contact number",
        f"{keyword} google maps",
        f"site:linkedin.com/company {keyword}",
        f"site:facebook.com {keyword} dubai number"
    ]
    
    new_leads = 0
    import random
    session = requests.Session()
    
    for query in queries:
        if new_leads >= num_results:
            break
            
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        if status_obj:
            status_obj.current_source = f"Google: {query}"
            status_obj.save()
            
        try:
            # Add a small random delay before each query
            time.sleep(random.uniform(1, 3))
            res = session.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"[!] Google search blocked (Status {res.status_code}).")
                # Try to use a different search engine fallback if Google blocks
                if res.status_code == 429:
                    print("[*] Google rate limited. Switching to Bing fallback...")
                    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
                    res = session.get(url, headers=headers, timeout=15)
                
                if res.status_code != 200:
                    continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            # Look for all text content and extract phone numbers
            # Google results are usually in 'div.g' or similar, but we can just grab all text
            all_text = soup.get_text(separator=' | ')
            phones = extract_phone_numbers(all_text)
            
            # For each phone found, try to find the surrounding text as a company name
            for phone in phones:
                if not ScrapedLead.objects.filter(phone_number=phone).exists():
                    # Find where this phone is in the text
                    idx = all_text.find(phone)
                    # Get ~100 chars before the phone as the context
                    context = all_text[max(0, idx-100):idx].strip()
                    # A company name is usually at the end of the context before the phone
                    # Split by common separators like ' | ' or ' - ' or '\n'
                    parts = re.split(r' \| | - |\n', context)
                    name = parts[-1].strip() if parts else f"Google Lead: {keyword}"
                    
                    if len(name) < 3: name = f"Google Lead: {keyword}"
                    
                    ScrapedLead.objects.create(
                        company_name=name[:100],
                        phone_number=phone,
                        source=f"Google: {query}"
                    )
                    print(f"[+] SUCCESS! Google lead saved: {name} | Phone: {phone}")
                    new_leads += 1
                    if status_obj:
                        status_obj.leads_found += 1
                        status_obj.save()
                if new_leads >= num_results:
                    break
        except Exception as e:
            print(f"[!] Google Scrape Error: {e}")
            
        time.sleep(random.uniform(2, 4))
    return new_leads

def scrape_leads_with_progress(status_id=1):
    """Refactored main loop that reports progress to the database."""
    status_obj, _ = ScraperStatus.objects.get_or_create(id=status_id)
    status_obj.is_running = True
    status_obj.progress_percentage = 0
    status_obj.leads_found = 0
    status_obj.save()

    try:
        # 1. Start with YellowPages (High Quality)
        industries = [
            "construction", "real-estate", "hotels", "medical-centers", "schools",
            "logistics", "hospitals", "it-companies", "factories", "offices"
        ]
        import random
        random.shuffle(industries)
        
        total_new = 0
        target_per_run = 100
        
        for i, industry in enumerate(industries):
            if total_new >= target_per_run:
                break
            
            status_obj.progress_percentage = int((i / (len(industries) + 2)) * 100)
            status_obj.save()
            
            found, dupes = scrape_leads(category=industry, num_results=20, status_obj=status_obj)
            total_new += found
            
        # 2. Broaden with Google Search (Google Maps/LinkedIn Simulation)
        if total_new < target_per_run:
            status_obj.progress_percentage = 80
            status_obj.save()
            
            found = scrape_google_search(keyword="dubai business", num_results=(target_per_run - total_new), status_obj=status_obj)
            total_new += found

        status_obj.progress_percentage = 100
        status_obj.is_running = False
        status_obj.save()
        print(f"[*] Scraping run completed. Total New: {total_new}")

    except Exception as e:
        print(f"[!] Scraper Error: {e}")
        status_obj.is_running = False
        status_obj.error_message = str(e)
        status_obj.save()

if __name__ == "__main__":
    # If "test" is in arguments, run a very quick test
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("[*] RUNNING SCRAPER TEST MODE...")
        # Test YellowPages
        found, dupes = scrape_leads(category="construction", num_results=5)
        print(f"[YP TEST] Found: {found}, Dupes: {dupes}")
        # Test Google
        found = scrape_google_search(keyword="catering dubai", num_results=5)
        print(f"[GOOGLE TEST] Found: {found}")
        sys.exit(0)

    # ... existing industries code ...

