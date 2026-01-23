from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib import messages

def is_kitchen_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

from django.utils import timezone
from vending.models import Order, OrderStatus, OrderItem, PlanType, PlanSubType

class DashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Order
    template_name = 'kitchen/dashboard.html'
    context_object_name = 'orders'

    def test_func(self):
        return is_kitchen_admin(self.request.user)

    def get_queryset(self):
        # Show specific statuses for kitchen, but only if they have non-Order Now items
        return Order.objects.filter(
            status__in=[
                OrderStatus.PENDING,
                OrderStatus.PREPARING,
                OrderStatus.READY
            ],
            items__plan_type__in=['START_PLAN', 'ORDER_NOW', 'SMART_GRAB'],
            items__pickup_code__isnull=True # Only items that still need fulfillment
        ).distinct().order_by('-created_at')

class TrackingView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Order
    template_name = 'kitchen/tracking.html'
    context_object_name = 'orders'
    
    def test_func(self):
        return is_kitchen_admin(self.request.user)
    ordering = ['-created_at']

    def get_queryset(self):
        # Tracking needs ALL orders
        qs = Order.objects.all().order_by('-created_at')
        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'kitchen/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        return is_kitchen_admin(self.request.user)

@login_required
@user_passes_test(is_kitchen_admin)
@require_POST
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in OrderStatus.values:
        order.status = new_status
        order.save()
    return redirect('kitchen:dashboard')

# -----------------------------------------------------------
# ITEM STATUS UPDATE (Daily Orders)
# -----------------------------------------------------------
@login_required
@user_passes_test(is_kitchen_admin)
@require_POST
def update_item_status(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    # Toggle 'READY' or 'PENDING'
    # Check current status found in item context or just use a query param
    # For now, let's assume we toggle between PENDING and READY
    
    current = item.status
    if current == OrderStatus.READY:
        item.status = OrderStatus.PENDING
    else:
        item.status = OrderStatus.READY
    
    item.save()
    
    # Check if all items in order are ready, then update order status?
    # Optional logic:
    # if not item.order.items.exclude(status=OrderStatus.READY).exists():
    #     item.order.status = OrderStatus.READY
    #     item.order.save()

    # Redirect back to daily orders with same date
    date_str = request.POST.get('date_str')
    url = reverse('kitchen:daily_orders')
    if date_str:
        url += f'?date={date_str}'
    return redirect(url)

# -----------------------------------------------------------
# MENU UPLOAD
# -----------------------------------------------------------
# -----------------------------------------------------------
# MENU UPLOAD
# -----------------------------------------------------------
from django.http import JsonResponse
import csv
import io
import re
from vending.models import Menu, MenuItem, DayOfWeek, VendingMachineStock
import requests
from django.core.files.base import ContentFile


# @login_required
# @user_passes_test(is_kitchen_admin)
@login_required
@user_passes_test(is_kitchen_admin)
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
        
        price = parse_macros(row.get('Price', 0))
        desc = row.get('Description', '')
        
        # Nutritional - user image shows numeric columns at the end (G, H, I, J...)
        
        cals = parse_macros(row.get('Calories', row.get('Kcal', 0)))
        prot = parse_macros(row.get('Protein', 0))
        carbs = parse_macros(row.get('Carbs', 0))
        fats = parse_macros(row.get('Fats', 0))
        
        # Heating
        heating_raw = row.get('Heating', row.get('heating', '')).lower().strip()
        heating = (heating_raw == 'yes')

        # Check for explicitly updated fields to avoid overwriting with defaults if not present
        defaults = {
            'description': desc,
            'price': price,
            'calories': int(cals),
            'protein': prot,
            'carbs': carbs,
            'fats': fats,
            'heating': heating,
        }
        
        item, created = MenuItem.objects.update_or_create(
            menu=menu,
            name=item_name,
            defaults=defaults
        )
        
        # Handle Image URL
        picture_url = row.get('Picture', '').strip()
        
        # Clean Excel formulas e.g. =IMAGE("url")
        if picture_url.startswith('=') or 'IMAGE(' in picture_url:
            # Extract http/https url via regex
            url_match = re.search(r'(https?://[^\s"\'\)]+)', picture_url)
            if url_match:
                picture_url = url_match.group(1)
        
        # Basic cleanup of quotes if any remain
        picture_url = picture_url.strip('"\'')

        if picture_url and (picture_url.startswith('http') or 'drive.google.com' in picture_url):
            # Check if we need to update
            # We update if: 
            # 1. We don't have an image source URL stored (legacy items)
            # 2. The stored source URL is different from the new one
            # 3. The item has no image file associated
            if item.image_source_url != picture_url or not item.image:
                try:
                    with open('debug_log.txt', 'a') as f:
                        f.write(f"DEBUG: Downloading new image for {item_name} from {picture_url}\n")
                    
                    # For Google Drive Export URLs, standard requests.get usually works if public
                    response = requests.get(picture_url, timeout=10)
                    if response.status_code == 200:
                        # Create filename
                        filename = f"{slugify(item_name)}.jpg"
                        # Save image and update source URL
                        item.image.save(filename, ContentFile(response.content), save=False)
                        item.image_source_url = picture_url
                        item.save()
                        
                        with open('debug_log.txt', 'a') as f:
                            f.write(f"DEBUG: Saved image {filename}\n")
                    else:
                        with open('debug_log.txt', 'a') as f:
                            f.write(f"DEBUG: Failed to download image. Status: {response.status_code}\n")
                except Exception as e:
                    with open('debug_log.txt', 'a') as f:
                        f.write(f"DEBUG: Error downloading image: {e}\n")
            else:
                 with open('debug_log.txt', 'a') as f:
                        f.write(f"DEBUG: Image URL unchanged for {item_name}, skipping download.\n")


@login_required
@user_passes_test(is_kitchen_admin)
def get_active_orders_api(request):
    """
    Returns a list of active orders with full details.
    Used for polling by the dashboard to detect and render new orders.
    """
    from django.utils.timesince import timesince
    from django.urls import reverse
    
    orders = Order.objects.filter(
        status__in=[OrderStatus.PENDING, OrderStatus.PREPARING, OrderStatus.READY],
        items__plan_type__in=['START_PLAN', 'ORDER_NOW', 'SMART_GRAB'],
        items__pickup_code__isnull=True
    ).prefetch_related('items__menu_item').distinct().order_by('-created_at')
    
    orders_data = []
    for order in orders:
        # Filter items to only show those that need kitchen preparation
        kitchen_items = order.items.filter(
            plan_type__in=['START_PLAN', 'ORDER_NOW', 'SMART_GRAB'], 
            pickup_code__isnull=True
        )
        
        if not kitchen_items.exists():
            continue

        items_data = []
        for item in kitchen_items[:3]:  # First 3 items like in template
            items_data.append({
                'name': item.menu_item.name,
                'quantity': item.quantity,
                'week': item.week_number,
                'day': item.day_of_week
            })
        
        orders_data.append({
            'id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at.isoformat(),
            'timesince': timesince(order.created_at),
            'pickup_date': str(order.pickup_date) if order.pickup_date else 'Today',
            'pickup_slot': order.pickup_slot.label if order.pickup_slot else None,
            'items_count': order.kitchen_items.count(),
            'items': items_data,
            'detail_url': reverse('kitchen:order_detail', args=[order.id])
        })
    
    return JsonResponse({'orders': orders_data})

# -----------------------------------------------------------
# VENDING PRICES UPDATE
# -----------------------------------------------------------

# @login_required
# @user_passes_test(is_kitchen_admin)
@login_required
@user_passes_test(is_kitchen_admin)
def vending_prices_view(request):
    not_found_items = []
    updated_items = []
    
    if request.method == 'POST' and request.FILES.get('price_file'):
        file = request.FILES['price_file']
        
        try:
            data = []
            if file.name.endswith('.csv'):
                decoded_file = file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)
                data = list(reader)
                
            elif file.name.endswith(('.xls', '.xlsx')):
                import openpyxl
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                
                rows = list(sheet.iter_rows(values_only=True))
                if rows:
                    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
                    for row in rows[1:]:
                        row_dict = {}
                        for i, val in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = val
                        data.append(row_dict)
            else:
                messages.error(request, "Unsupported file format. Please use CSV or Excel.")
                return render(request, 'kitchen/vending_prices.html')

            # Process Data
            if not data:
                with open('debug_log.txt', 'a') as f:
                    f.write("DEBUG: No data found after parsing file.\n")

            # PASS 1: Collect final prices for each item
            price_updates = {} # Map: clean_name -> price_val
            
            for i, row in enumerate(data):
                # Normalize keys slightly to key access
                row_lower = {str(k).lower().strip(): v for k, v in row.items() if k}
                
                if i < 3: # Log first 3 rows
                     with open('debug_log.txt', 'a') as f:
                        f.write(f"DEBUG ROW {i} KEYS: {list(row_lower.keys())}\n")
                        f.write(f"DEBUG ROW {i} VALS: {row_lower}\n")

                # Fetch Name and Price
                # Try 'item', 'item name', 'name'
                raw_name = row_lower.get('item') or row_lower.get('item name') or row_lower.get('name')
                
                # Try 'price', 'new price', 'cost'
                raw_price = row_lower.get('price') or row_lower.get('new price') or row_lower.get('cost')
                
                if not raw_name:
                    continue # Skip empty rows
                
                # Clean Name: Valid name, remove '*', ignore case
                clean_name = str(raw_name).replace('*', '').strip()
                
                # Clean Price
                try:
                     price_val = parse_macros(raw_price) # Reuse parse_macros for float extraction
                except:
                     price_val = 0.0

                if price_val > 0:
                     price_updates[clean_name] = price_val

            # PASS 2: Global Update
            for name, price in price_updates.items():
                qs = MenuItem.objects.filter(name__iexact=name)
                
                if qs.exists():
                    count = qs.update(price=price)
                    updated_items.append({
                        'name': name,
                        'new_price': price,
                        'count': count
                    })
                else:
                    not_found_items.append({
                        'name': name,
                        'price': price
                    })
            
            if updated_items:
                total = sum(item['count'] for item in updated_items)
                messages.success(request, f"Global Update Success: Updated {len(updated_items)} unique items affecting {total} total records.")
            elif not_found_items:
                 messages.warning(request, "Process complete. Some items were not found.")
            else:
                 messages.info(request, "Process complete. No changes needed.")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return render(request, 'kitchen/vending_prices.html', {
        'not_found_items': not_found_items, 
        'updated_items': updated_items
    })

# -----------------------------------------------------------
# VENDING MACHINE ITEMS (STOCK)
# -----------------------------------------------------------

@login_required
@user_passes_test(is_kitchen_admin)
def vending_machine_items_view(request):
    """
    Fetches items from external vending API and structures them by shelf/slot for a visual UI.
    """
    from vending.models import VendingLocation
    
    # 1. Get Active Machines for Selector
    machines = VendingLocation.objects.filter(is_active=True).exclude(serial_number__isnull=True).order_by('name')
    if not machines.exists():
        messages.warning(request, "No active vending machines found in database.")
        return render(request, 'kitchen/vending_machine_items.html', {'machines': [], 'shelves': []})

    # 2. Determine Selected Machine
    selected_uuid = request.GET.get('machine_uuid')
    if not selected_uuid:
        selected_uuid = machines.first().serial_number
    
    current_machine = machines.filter(serial_number=selected_uuid).first()
    
    # 3. Fetch Token
    token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
    token_params = {
        "userName": "C202405128888",
        "password": "8888"
    }
    
    shelves_data = []
    
    try:
        token_response = requests.get(token_url, params=token_params, timeout=10)
        token_data = token_response.json()
        token = token_data.get("data") or token_data.get("token")
        
        if not token:
            messages.error(request, "Could not fetch external vending token.")
        else:
            # 4. Fetch Machine Goods
            goods_url = "http://www.hnzczy.cn:8087/commodityinfo/querycommodityinfo"
            headers = {"Authorization": token}
            
            # Pre-fetch local images to fix broken external URLs
            from vending.models import MenuItem
            import re
            
            def normalize_name(name):
                if not name: return ""
                name = name.replace("&", "and")
                return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

            local_image_map = {}
            for item in MenuItem.objects.exclude(image=''):
                # Map exact name
                if item.image:
                    local_image_map[item.name] = item.image.url
                    # Map normalized name
                    local_image_map[normalize_name(item.name)] = item.image.url
            
            try:
                response = requests.get(goods_url, params={"machineUuid": selected_uuid}, headers=headers, timeout=15)
                api_data = response.json()
                
                if api_data and api_data.get("result") == "200":
                    slots = api_data.get("data") or []
                    shelves_dict = {}
                    
                    for slot in slots:
                        # Group by Tier (Shelf)
                        raw_tier = slot.get("modityTierSeq", 0)
                        try:
                            tier = int(raw_tier)
                        except (ValueError, TypeError):
                            tier = 999 

                        if tier not in shelves_dict:
                            shelves_dict[tier] = {
                                'id': tier,
                                'name': f"Shelf {tier}",
                                'spots_map': {} # Use dict for strict deduplication
                            }
                        
                        goods = slot.get("commGoodsResp")
                        
                        # Normalize Slot ID
                        raw_spot_id = slot.get('arrivalName')
                        spot_id_str = str(raw_spot_id).strip()
                        
                        spot_data = {
                            'arrivalName': spot_id_str,
                            'modityTierNum': slot.get('modityTierNum'), 
                            'capacity': slot.get('arrivalCapacity'),
                            'present': slot.get('presentNumber', 0),
                            'status': 'empty',
                            'item': None
                        }
                        
                        if goods:
                            g_name = goods.get('goodsName')
                            local_img = local_image_map.get(g_name) or local_image_map.get(normalize_name(g_name))
                            
                            spot_data['item'] = {
                                'uuid': goods.get('uuid'),
                                'name': g_name,
                                'price': goods.get('goodsPrice'),
                                'image': local_img if local_img else goods.get('goodsUrl'),
                                'desc': goods.get('goodsDesc')
                            }
                            
                            if slot.get('presentNumber', 0) > 0:
                                spot_data['status'] = 'available'
                            else:
                                spot_data['status'] = 'sold_out'

                        # Deduplication / Merge Logic
                        # If spot exists, only overwrite if current one has item (is better)
                        existing = shelves_dict[tier]['spots_map'].get(spot_id_str)
                        if existing:
                            if spot_data['item'] is not None:
                                shelves_dict[tier]['spots_map'][spot_id_str] = spot_data
                            # Else: keep existing (which might have item or be empty, doesn't matter, we prioritize occupied)
                        else:
                             shelves_dict[tier]['spots_map'][spot_id_str] = spot_data
                    
                    # Convert maps to sorted lists
                    sorted_tiers = sorted(shelves_dict.keys())
                    for tier in sorted_tiers:
                        shelf = shelves_dict[tier]
                        # Flatten spots map values
                        spots_list = list(shelf['spots_map'].values())
                        
                        # Sort spots
                        spots_list.sort(key=lambda x: (int(x['modityTierNum']) if str(x['modityTierNum']).isdigit() else 999, x['arrivalName']))
                        
                        shelf['spots'] = spots_list
                        shelves_data.append(shelf)
                        
                else:
                    messages.warning(request, f"API returned error or empty data: {api_data.get('msg', 'Unknown Error')}")

            except Exception as e:
                print(f"Error fetching machine data: {e}")
                messages.error(request, f"Failed to connect to machine API: {str(e)}")

    except Exception as e:
        messages.error(request, f"Error fetching token: {str(e)}")

    context = {
        'machines': machines,
        'current_machine_uuid': selected_uuid,
        'current_machine': current_machine,
        'shelves': shelves_data
    }
    
    return render(request, 'kitchen/vending_machine_items.html', context)

@login_required
@user_passes_test(is_kitchen_admin)
@require_POST
def update_vending_stock(request):
    """
    Updates the quantity of a vending item.
    """
    uuid = request.POST.get('uuid')
    quantity = request.POST.get('quantity')
    
    if uuid and quantity is not None:
        try:
            stock = VendingMachineStock.objects.get(vending_good_uuid=uuid)
            stock.quantity = int(quantity)
            stock.save()
            messages.success(request, f"Updated stock for {stock.goods_name}")
        except Exception as e:
            messages.error(request, f"Error updating stock: {str(e)}")
            
    machine_uuid = request.POST.get('machine_uuid')
    
    response = redirect('kitchen:vending_machine_items')
    if machine_uuid:
        response['Location'] += f'?machine_uuid={machine_uuid}'
    return response

# @login_required
# @user_passes_test(is_kitchen_admin)
@login_required
@user_passes_test(is_kitchen_admin)
def daily_orders_view(request):
    """
    Shows aggregated orders for a specific day.
    Includes 'Order Now' items for that date and 'Weekly/Monthly' plan items for that day of week.
    """
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    day_name = selected_date.strftime('%A') # e.g. "Tuesday"
    
    # Query items for this day
    # Condition 1: Immediate orders (Order Now / Smart Grab) scheduled for this date
    # Condition 2: Plan orders for this day of week
    
    # We need to capture:
    # A. Plan items (Weekly/Monthly) matching day_of_week
    # B. Daily items (Order Now/Smart Grab) matching pickup_date (or created_today if pickup_date is used)
    
    # Fetch Items (Sorted by Time, then Name)
    items = OrderItem.objects.filter(
        (
            Q(plan_type='START_PLAN', plan_subtype__in=[PlanSubType.WEEKLY, PlanSubType.MONTHLY], day_of_week=day_name)
        ) | (
            Q(plan_type__in=['ORDER_NOW', 'SMART_GRAB'], pickup_date=selected_date)
        )
    ).filter(
        pickup_code__isnull=True, 
        order__status__in=[
            OrderStatus.CONFIRMED, 
            OrderStatus.PREPARING, 
            OrderStatus.READY,
            OrderStatus.PENDING 
        ]
    ).select_related('menu_item', 'order', 'order__user', 'pickup_slot', 'order__pickup_slot').order_by('order__user__username', 'week_number', 'pickup_slot__start_time', 'menu_item__name')

    # Separate into Pending and Ready
    pending_items = []
    ready_items = []
    
    for item in items:
        # Determine slot label for display
        slot_obj = item.pickup_slot or item.order.pickup_slot
        item.slot_label = slot_obj.label if slot_obj else "Standard Pickup"
        item.user_name = f"{item.order.user.first_name} {item.order.user.last_name}".strip() or item.order.user.username
        
        if item.status == OrderStatus.READY:
            ready_items.append(item)
        else:
            pending_items.append(item)

    context = {
        'selected_date': selected_date,
        'day_name': day_name,
        'pending_items': pending_items,
        'ready_items': ready_items,
        'date_str': selected_date.strftime('%Y-%m-%d'),
        'total_orders_count': items.count(),
        'pending_count': len(pending_items),
        'ready_count': len(ready_items)
    }
    return render(request, 'kitchen/daily_orders.html', context)
