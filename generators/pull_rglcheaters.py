import requests
import json
import time

# baseurl
url = "https://api.rgl.gg/v0/bans/paged"

all_bans = []
page = 1
page_size = 100

print("Fetching ban list from RGL.gg...")

while True:
    params = {
        "take": page_size,
        "skip": (page - 1) * page_size
    }
    
    response = requests.get(url, params=params)
    
    # Handle rate limiting
    if response.status_code == 429:
        print(f"Rate limited on page {page}, delaying...")
        time.sleep(2)
        continue  # Retry the same page
        
    if response.status_code != 200:
        print(f"Failed to fetch page {page}. Status code: {response.status_code}")
        print(response.text)
        break
        
    data = response.json()
    bans = data if isinstance(data, list) else data.get("items", [])

    if not bans:
        break
        
    # Filter for bans where "reason" contains "Cheating" (case-insensitive)
    cheating_bans = [
        ban for ban in bans 
        if ban.get("reason") and "cheating" in ban.get("reason").lower()
    ]
    
    all_bans.extend(cheating_bans)
    print(f"Fetched page {page} ({len(bans)} records scanned, {len(cheating_bans)} matched)...")

    if len(bans) < page_size:
        break
        
    page += 1
    time.sleep(0.5)

# Save filtered results
output_file = "rgl_cheating_bans.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_bans, f, indent=4)

print(f"Saved {len(all_bans)} total cheating bans to {output_file}.")