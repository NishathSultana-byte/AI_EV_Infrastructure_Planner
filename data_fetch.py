import requests
import pandas as pd
 
print("script started")
# 🔑 Replace with your actual API key
API_KEY = "94e99859-99e2-43f1-98b8-bac7fa9f2087"

url = "https://api.openchargemap.io/v3/poi/"

params = {
    "output": "json",
    "countrycode": "IN",     # India
    "maxresults": 1000,      # Fetch up to 1000 stations
    "compact": "true",
    "verbose": "false",
    "key": API_KEY
}

print("Fetching EV charging station data for India...")

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Total stations fetched: {len(data)}")
else:
    print("Error fetching data:", response.status_code)
    exit()

records = []

for item in data:
    if item.get("AddressInfo"):
        address = item["AddressInfo"]
        connections = item.get("Connections", [])

        power = 0
        if connections:
            power = connections[0].get("PowerKW", 0)

        records.append({
            "Station_Name": address.get("Title"),
            "Latitude": address.get("Latitude"),
            "Longitude": address.get("Longitude"),
            "State": address.get("StateOrProvince"),
            "Town": address.get("Town"),
            "Power_kW": power
        })

df = pd.DataFrame(records)

df.to_csv("india_ev_stations.csv", index=False)

print("Data saved successfully as india_ev_stations.csv")