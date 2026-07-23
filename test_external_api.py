import requests

def test_api():
    token_url = "http://www.hnzczy.cn:8087/apiusers/checkusername"
    token_params = {
        "userName": "C202405128888",
        "password": "8888"
    }
    
    print("Fetching token...")
    token_response = requests.get(token_url, params=token_params, timeout=10)
    token_data = token_response.json()
    token = token_data.get("data")
    print(f"Token: {token}")
    
    if not token:
        print("Failed to get token")
        return

    goods_url = "http://www.hnzczy.cn:8087/customgoods/querymachinegoods"
    headers = {"Authorization": token}
    
    # Try with machineUuid as string
    print("\nTesting with machineUuid='155'...")
    params1 = {"machineUuid": "155"}
    res1 = requests.get(goods_url, params=params1, headers=headers, timeout=10)
    print(f"Response 1: {res1.json()}")
    
    # Try with machineUuid as integer? (requests will stringify it anyway)
    
    # Try with different parameter name? 
    # The user's JSON had machineUuid: "155"
    
    # Maybe it needs other params?
    
if __name__ == "__main__":
    test_api()
