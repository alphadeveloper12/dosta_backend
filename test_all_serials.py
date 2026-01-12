import requests
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from vending.models import VendingLocation

def test_all_machines():
    token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
    token_params = {
        "userName": "C202405128888",
        "password": "8888"
    }
    
    print("Fetching token...")
    token_response = requests.get(token_url, params=token_params, timeout=10)
    token_data = token_response.json()
    token = token_data.get("data")
    
    if not token:
        print("Failed to get token")
        return

    goods_url = "http://www.hnzczy.cn:8087/customgoods/querymachinegoods"
    headers = {"Authorization": token}
    
    # Add 155 to the list
    serials = list(VendingLocation.objects.exclude(serial_number__isnull=True).values_list('serial_number', flat=True))
    serials.append("155")
    
    for sn in serials:
        print(f"Testing machineUuid='{sn}'...")
        params = {"machineUuid": sn}
        try:
            res = requests.get(goods_url, params=params, headers=headers, timeout=5)
            data = res.json()
            if data.get("result") == "200":
                print(f"✅ SUCCESS for {sn}!")
                # print(data)
                return sn
            else:
                print(f"❌ Failed for {sn}: {data.get('resultDesc')}")
        except Exception as e:
            print(f"⚠️ Error for {sn}: {e}")

if __name__ == "__main__":
    test_all_machines()
