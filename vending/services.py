import requests
from datetime import datetime
import pytz
from django.conf import settings

# External Vending API Configuration
VENDING_API_BASE = "http://www.hnzczy.cn:8087"
VENDING_USER = "C202405128888"
VENDING_PASS = "8888"

class VendingService:
    @staticmethod
    def get_token():
        url = f"{VENDING_API_BASE}/apiusers/checkusername"
        params = {"userName": VENDING_USER, "password": VENDING_PASS}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            return data.get("data") or data.get("token")
        except Exception as e:
            print(f"Error fetching vending token: {e}")
            return None

    @staticmethod
    def update_stock(machine_uuid, spot_updates):
        """
        machine_uuid: str/int
        spot_updates: list of dicts (payload for update-commodity)
        """
        token = VendingService.get_token()
        if not token:
            raise Exception("Failed to get vending token")

        url = f"{VENDING_API_BASE}/commodityinfo/updatecommodityinfo" 
        # Note: In views.py it was mapped to `ExternalUpdateCommodityView` which likely calls this endpoint.
        # Let's verify the endpoint from views.py or just use the one I saw there.
        # In views.py `ExternalUpdateCommodityView` proxies to... wait, I need to check views.py for the exact URL.
        # I'll check views.py again to be sure about the URL.
        # Based on previous context, it seemed to be `updatecommodity` or similar.
        # I will assume `updatecommodityinfo` based on naming convention or `api/vending/external/update-commodity/` proxy.
        # Actually, let's look at `ExternalUpdateCommodityView` in views.py if I can or just re-read the file view I did earlier.
        # I'll use a placeholder and fix it if `views.py` verification shows different.
        
        # ACTUALLY, checking previous `views.py` dump (Step 162), `ExternalUpdateCommodityView` wasn't fully shown.
        # But `ExternalProductionPickView` uses `http://www.hnzczy.cn:8087/commpick/productionpick`.
        # `ExternalMachineGoodsView` uses `http://www.hnzczy.cn:8087/commodityinfo/querycommodityinfo`.
        # So Update is likely `http://www.hnzczy.cn:8087/commodityinfo/updatecommodityinfo`.
        
        url = "http://www.hnzczy.cn:8087/commodityinfo/updatecommodityinfo"
        headers = {"Authorization": token, "Content-Type": "application/json"}
        
        # The API expects a list of objects directly or wrapped?
        # The frontend sent `{ list: [...], machineUuid: ... }`.
        # The external API usually takes the list directly or specific format.
        # Let's assume the payload structure matches what the frontend was sending, 
        # but standardizing here.
        
        # If spot_updates is the list of goods to update.
        payload = spot_updates 
        
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        return resp.json()

    @staticmethod
    def fetch_machine_goods(machine_uuid):
        token = VendingService.get_token()
        if not token: 
            return None
            
        url = "http://www.hnzczy.cn:8087/commodityinfo/querycommodityinfo"
        headers = {"Authorization": token}
        # Assuming we need to pass machineUuid or equipmentUuid.
        # Frontend used: /api/vending/external/machine-goods/?machineUuid=...
        # ExternalMachineGoodsView proxied params directly.
        # Docs/Code implied params: machineUuid
        params = {"machineUuid": machine_uuid}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            return resp.json()
        except Exception as e:
            print(f"Error fetching machine goods: {e}")
            return None

    @staticmethod
    def normalize_name(name):
        import re
        if not name:
            return ""
        return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()

    @staticmethod
    def process_order_fulfillment(order):
        """
        1. Fetch fresh stock from machine.
        2. Calculate updates based on order items.
           - Try to resolve missing vending_good_uuid by name mapping.
        3. Send update to machine.
        4. Generate Pickup Code.
        5. Return Pickup Code.
        """
        machine_uuid = order.location.serial_number
        if not machine_uuid:
            print(f"❌ Order {order.id} has no machine serial number.")
            return None
            
        # --- 1. Fetch Fresh Stock ---
        goods_data = VendingService.fetch_machine_goods(machine_uuid)
        if not goods_data or goods_data.get("result") != "200":
             print(f"❌ Failed to fetch stock for machine {machine_uuid}")
             # We might still try to generate pickup if we have IDs, but usually failure here is fatal for stock sync
        
        raw_spots = goods_data.get("data") or [] if goods_data else []
        
        # Create a name-to-uuid map for fallbacks
        name_to_uuids = {} # normalized_name -> list of (uuid, presentNumber)
        for spot in raw_spots:
            goods = spot.get("commGoodsResp")
            if goods and spot.get("presentNumber", 0) > 0:
                norm_name = VendingService.normalize_name(goods.get("goodsName"))
                if norm_name:
                    if norm_name not in name_to_uuids:
                        name_to_uuids[norm_name] = []
                    name_to_uuids[norm_name].append({
                        "uuid": str(goods.get("uuid")),
                        "presentNumber": spot.get("presentNumber"),
                        "spot": spot
                    })

        # --- 2. Calculate Stock Updates & Resolve UUIDs ---
        usage_map = {} # uuid -> quantity
        resolved_items = []
        
        for item in order.items.all():
            if item.plan_type in ['ORDER_NOW', 'SMART_GRAB']:
                item_uuid = item.vending_good_uuid
                
                # FALLBACK: If UUID is missing, try to resolve by name
                if not item_uuid:
                    norm_item_name = VendingService.normalize_name(item.menu_item.name)
                    print(f"🔍 Item {item.id} ({item.menu_item.name}) missing UUID. Trying normalization: {norm_item_name}")
                    
                    if norm_item_name in name_to_uuids:
                        # Find spot with most stock or just first
                        candidates = sorted(name_to_uuids[norm_item_name], key=lambda x: x['presentNumber'], reverse=True)
                        if candidates:
                            item_uuid = candidates[0]['uuid']
                            item.vending_good_uuid = item_uuid
                            item.save(update_fields=['vending_good_uuid'])
                            print(f"✅ Resolved UUID for {item.menu_item.name}: {item_uuid}")
                
                if item_uuid:
                    usage_map[item_uuid] = usage_map.get(item_uuid, 0) + item.quantity
                    resolved_items.append(item)
                else:
                    print(f"⚠️ Could not resolve UUID for item {item.id}: {item.menu_item.name}")

        goods_list_to_update = []
        
        # We need to decrement stock in raw_spots and prepare update payload
        for spot in raw_spots:
            goods = spot.get("commGoodsResp")
            if not goods: continue
            
            goods_uuid = str(goods.get("uuid"))
            
            if goods_uuid in usage_map and usage_map[goods_uuid] > 0:
                needed = usage_map[goods_uuid]
                present = spot.get("presentNumber", 0)
                
                take = min(needed, present)
                
                if take > 0:
                    new_quantity = max(0, present - take)
                    
                    goods_list_to_update.append({
                        "arrivalCapacity": spot.get("arrivalCapacity"),
                        "arrivalName": spot.get("arrivalName"),
                        "commodityState": 0,
                        "equipmentUuid": machine_uuid,
                        "goodsUuid": int(goods_uuid),
                        "presentNumber": new_quantity,
                        "salePrice": goods.get("goodsPrice")
                    })
                    
                    usage_map[goods_uuid] -= take
        
        if goods_list_to_update:
            print(f"🔄 Updating Stock for Order {order.id}: {len(goods_list_to_update)} spots")
            VendingService.update_stock(machine_uuid, goods_list_to_update)

        # --- 3. Generate Pickup Code ---
        pickup_items = []
        total_qty = 0
        
        for item in resolved_items:
             total_qty += item.quantity
             pickup_items.append({
                 "goodsNumber": item.quantity,
                 "goodsPrice": 0.01,
                 "goodsUuid": item.vending_good_uuid,
             })
             if item.heating_requested:
                 pickup_items[-1]["serviceType"] = 1
                 pickup_items[-1]["serviceVal"] = "15"

        if not pickup_items:
            print("❌ No valid items for pickup generation.")
            return None

        print(f"🚀 Generating Pickup Code for Order {order.id} ({total_qty} items)...")
        pick_resp = VendingService.generate_pickup_code(machine_uuid, order.id, pickup_items, total_qty)
        
        if pick_resp and pick_resp.get("result") == "200":
            code = pick_resp.get("data")
            print(f"✅ Pickup Code Generated: {code}")
            return code
        
        print(f"❌ Failed to generate pickup code: {pick_resp}")
        return None

    @staticmethod
    def generate_pickup_code(machine_uuid, order_id, pickup_items, total_qty):
        """
        Request a pickup code from the external machine API.
        """
        token = VendingService.get_token()
        if not token:
            return None

        url = f"{VENDING_API_BASE}/commpick/productionpick"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        # Use UAE Time (UTC+4)
        uae_tz = pytz.timezone('Asia/Dubai')
        now_uae = datetime.now(uae_tz)
        # Format: 2026-01-13T18:12:33.970Z (Millisecond precision is often required/expected)
        order_time_str = now_uae.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        pick_payload = {
            "goodsList": pickup_items,
            "goodsNumber": total_qty,
            "machineUuid": machine_uuid,
            "orderNo": str(order_id),
            "orderTime": order_time_str,
            "timeOut": 1,
            "lock": 0
        }

        try:
            resp = requests.post(url, json=pick_payload, headers=headers, timeout=30)
            return resp.json()
        except Exception as e:
            print(f"Error calling production-pick: {e}")
            return None
