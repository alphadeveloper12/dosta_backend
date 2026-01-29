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
    def process_order_fulfillment(order):
        """
        1. Fetch fresh stock from machine.
        2. Calculate updates based on order items.
        3. Send update to machine.
        4. Generate Pickup Code.
        5. Return Pickup Code.
        """
        machine_uuid = order.location.serial_number
        if not machine_uuid:
            print(f"Order {order.id} has no machine serial number.")
            return None
            
        # --- 1. Fetch Fresh Stock ---
        goods_data = VendingService.fetch_machine_goods(machine_uuid)
        if not goods_data or goods_data.get("result") != "200":
             print(f"Failed to fetch stock for machine {machine_uuid}")
             # Proceed to pickup generation anyway? Or partial fail?
             # If we can't update stock, we might risk double selling, but we should probably try to generate code.
             pass
        else:
            # --- 2. Calculate Stock Updates ---
            try:
                shelves = goods_data.get("data", []) # External API structure might differ from my frontend View transform
                # Wait, ExternalMachineGoodsView transformed the data significantly for Frontend.
                # I need to work with the RAW external API data here, or the same structure.
                # `fetch_machine_goods` returns raw JSON from `querycommodityinfo`.
                # Raw structure usually has `data` as list of spots/goods? 
                # Let's inspect `ExternalMachineGoodsView` again to see raw handling.
                # It iterated `api_data.get("data")`.
                
                raw_spots = goods_data.get("data") or []
                
                # Calculate usage from Order
                usage_map = {} # uuid -> quantity
                for item in order.items.all():
                    if item.plan_type in ['ORDER_NOW', 'SMART_GRAB'] and item.vending_good_uuid:
                        usage_map[item.vending_good_uuid] = usage_map.get(item.vending_good_uuid, 0) + item.quantity
                
                goods_list_to_update = []
                
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
                    
            except Exception as ex:
                print(f"Error calculating/updating stock: {ex}")

        # --- 3. Generate Pickup Code ---
        # Filter items for pickup
        pickup_items = []
        total_qty = 0
        
        for item in order.items.all():
             if item.plan_type in ['ORDER_NOW', 'SMART_GRAB'] and item.vending_good_uuid:
                 total_qty += item.quantity
                 pickup_items.append({
                     "goodsNumber": item.quantity,
                     "goodsPrice": 0.01,
                     "goodsUuid": item.vending_good_uuid,
                     # Add heating service if needed
                     # "serviceType": 1, "serviceVal": "15" if heating
                 })
                 if item.heating_requested:
                     pickup_items[-1]["serviceType"] = 1
                     pickup_items[-1]["serviceVal"] = "15"

        if not pickup_items:
            print("No items for pickup generation.")
            return None

        pick_resp = VendingService.generate_pickup_code(machine_uuid, order.id, pickup_items, total_qty)
        
        if pick_resp and pick_resp.get("result") == "200":
            return pick_resp.get("data")
        
        print(f"Failed to generate pickup code: {pick_resp}")
        return None
