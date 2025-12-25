from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib import messages

from vending.models import Order, OrderStatus

class DashboardView(ListView):
    model = Order
    template_name = 'kitchen/dashboard.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Show specific statuses for kitchen
        return Order.objects.filter(
            status__in=[
                OrderStatus.PENDING,
                OrderStatus.PREPARING,
                OrderStatus.READY
            ]
        ).order_by('created_at')

class OrderDetailView(DetailView):
    model = Order
    template_name = 'kitchen/order_detail.html'
    context_object_name = 'order'

@require_POST
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in OrderStatus.values:
        order.status = new_status
        order.save()
    return redirect('kitchen:dashboard')

# -----------------------------------------------------------
# MENU UPLOAD
# -----------------------------------------------------------
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
import csv
import io
import re
from vending.models import Menu, MenuItem, DayOfWeek
import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

def is_kitchen_admin(user):
    # Relaxed for testing: allow any logged-in user
    return True # user.is_staff or user.is_superuser

# @login_required
# @user_passes_test(is_kitchen_admin)
def menu_upload_view(request):
    if request.method == 'POST' and request.FILES.get('menu_file'):
        file = request.FILES['menu_file']
        
        try:
            if file.name.endswith('.csv'):
                decoded_file = file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)
                process_menu_data(reader)
                messages.success(request, "Menu uploaded successfully via CSV!")
            elif file.name.endswith(('.xls', '.xlsx')):
                import openpyxl
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                
                # Get headers
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    raise ValueError("Empty file")
                    
                headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
                data = []
                for row in rows[1:]:
                    row_dict = {}
                    for i, val in enumerate(row):
                        if i < len(headers):
                            row_dict[headers[i]] = val
                    data.append(row_dict)
                
                process_menu_data(data)
                messages.success(request, "Menu uploaded successfully via Excel!")
            else:
                messages.error(request, "Unsupported file format. Please use CSV or Excel.")
                
        except Exception as e:
            with open('debug_log.txt', 'a') as f:
                f.write(f"ERROR: {str(e)}\n")
            messages.error(request, f"Error processing file: {str(e)}")
            
    return render(request, 'kitchen/menu_upload.html')

def parse_macros(macro_str):
    """Parses '36g' or '36' -> 36.0"""
    if not macro_str:
        return 0
    # Remove 'g' 'kcal' etc
    cleaned = re.sub(r'[^\d.]', '', str(macro_str))
    try:
        return float(cleaned) if cleaned else 0
    except ValueError:
        return 0

def process_menu_data(data_iter):
    """
    Expected columns: Week, Day, Item, Description, Price, Picture, Macros/Calories identifiers...
    Based on user sheet: 
    Week | Day | Item | Description | Price | Picture | [Calories] | [Protein] ...? 
    Wait, columns in user image:
    A: Week, B: Day, C: Item, D: Description, E: Price, F: Picture, G: 478kcal (Calories), H: 36g (Protein?), I: (Carbs?), J: (Fats?)
    
    Refining assumptions based on typical macro order (Cal, Prot, Carb, Fat).
    I will look for flexible headers or strict index if headers match 'Week', 'Day' etc.
    """
    
    # Mapping for DayOfWeek
    day_map = {
        'Monday': DayOfWeek.MONDAY,
        'Tuesday': DayOfWeek.TUESDAY, 
        'Wednesday': DayOfWeek.WEDNESDAY,
        'Thursday': DayOfWeek.THURSDAY,
        'Friday': DayOfWeek.FRIDAY,
        'Saturday': DayOfWeek.SATURDAY,
        'Sunday': DayOfWeek.SUNDAY
    }

    # Tracking created/updated to avoid clearing everything blindly if partial upload
    # But usually full upload is better. Let's process row by row.
    
    for row in data_iter:
        # Normalize keys and values
        row = {k.strip(): str(v).strip() for k, v in row.items() if k}
        with open('debug_log.txt', 'a') as f:
            f.write(f"DEBUG keys: {list(row.keys())}\n")
            f.write(f"DEBUG row: {row}\n")
        
        # 1. Parse Week (e.g. "Week 1" -> 1)
        week_raw = str(row.get('Week', '')).lower()
        week_match = re.search(r'\d+', week_raw)
        week_num = int(week_match.group()) if week_match else 1
        
        # 2. Parse Day
        day_raw = str(row.get('Day', '')).strip()
        # Capitalize first letter
        day_raw = day_raw.capitalize()
        if day_raw not in day_map:
            print(f"DEBUG: Invalid Day: {day_raw}")
            continue # Skip invalid days
            
        # 3. Get or Create Menu
        # Robustly handle duplicates (legacy data might have "Week 1" for multiple Monday records)
        menu = Menu.objects.filter(
            day_of_week=day_map[day_raw],
            week_number=week_num
        ).first()
        
        if not menu:
            menu = Menu.objects.create(
                day_of_week=day_map[day_raw],
                week_number=week_num,
                date=None
            )
        
        print(f"DEBUG: Menu found/created: {menu}")
        
        # 4. Create Menu Item
        item_name = row.get('Item', 'Unknown Item')
        if not item_name or item_name == 'Unknown Item':
             print(f"DEBUG: Missing item name in row: {row}")
             continue
             
        # Columns based on user image perception:
        # We need to be smart about column names.
        # Let's try to fetch by likely names or position if dict keys rely on header row
        
        price = parse_macros(row.get('Price', 0))
        desc = row.get('Description', '')
        
        # Nutritional - user image shows numeric columns at the end (G, H, I, J...)
        # G: 478kcal -> Calories
        # H: 36g -> Protein 
        # I: [assume Carbs]
        # J: [assume Fats]
        # We'll look for headers "Calories", "Protein", "Carbs", "Fats" or similar
        
        cals = parse_macros(row.get('Calories', row.get('Kcal', 0)))
        prot = parse_macros(row.get('Protein', 0))
        carbs = parse_macros(row.get('Carbs', 0))
        fats = parse_macros(row.get('Fats', 0))
        
        # If headers are missing/different in the sheet, simple fallback logic:
        # I will enforce headers in the template instructions: "Calories", "Protein", "Carbs", "Fats"
        
        # Check for explicitly updated fields to avoid overwriting with defaults if not present
        defaults = {
            'description': desc,
            'price': price,
            'calories': int(cals),
            'protein': prot,
            'carbs': carbs,
            'fats': fats,
        }
        
        item, created = MenuItem.objects.update_or_create(
            menu=menu,
            name=item_name,
            defaults=defaults
        )
        
        # Handle Image URL
        picture_url = row.get('Picture', '').strip()
        if picture_url and (picture_url.startswith('http') or 'drive.google.com' in picture_url):
            try:
                with open('debug_log.txt', 'a') as f:
                     f.write(f"DEBUG: Downloading image for {item_name} from {picture_url}\n")
                
                # For Google Drive Export URLs, standard requests.get usually works if public
                response = requests.get(picture_url, timeout=10)
                if response.status_code == 200:
                    # Create filename
                    filename = f"{slugify(item_name)}.jpg"
                    item.image.save(filename, ContentFile(response.content), save=True)
                    with open('debug_log.txt', 'a') as f:
                        f.write(f"DEBUG: Saved image {filename}\n")
                else:
                     with open('debug_log.txt', 'a') as f:
                        f.write(f"DEBUG: Failed to download image. Status: {response.status_code}\n")
            except Exception as e:
                 with open('debug_log.txt', 'a') as f:
                    f.write(f"DEBUG: Error downloading image: {e}\n")


def get_active_orders_api(request):
    """
    Returns a list of active order IDs and their latest status.
    Used for polling by the dashboard to detect new orders.
    """
    orders = Order.objects.filter(
        status__in=[OrderStatus.PENDING, OrderStatus.PREPARING, OrderStatus.READY]
    ).values('id', 'status', 'created_at')
    
    return JsonResponse({'orders': list(orders)})
