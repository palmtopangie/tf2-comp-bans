import requests
import json
import time
from datetime import datetime, timezone

# API and Output configuration
API_URL = "https://api.rgl.gg/v0/bans/paged"
OUTPUT_FILE = "bans/playerlist.rglbans.json"
BASE_STEAM64 = 76561197960265728

def steam64_to_steam3(steam64_str):
    """Converts a SteamID64 string into Steam3 ID format [U:1:XXXXXXXX]."""
    try:
        account_id = int(steam64_str) - BASE_STEAM64
        return f"[U:1:{account_id}]"
    except (ValueError, TypeError):
        return None

def iso_to_unix(iso_str):
    """Converts an ISO 8601 string to a Unix integer timestamp."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except (ValueError, TypeError, AttributeError):
        return int(datetime.now(timezone.utc).timestamp())

print("Fetching RGL bans from API...")

all_cheating_bans = []
page = 1
page_size = 100

while True:
    params = {
        "take": page_size,
        "skip": (page - 1) * page_size
    }
    
    response = requests.get(API_URL, params=params)
    
    # Handle rate limiting
    if response.status_code == 429:
        print(f"Rate limited on page {page}, delaying...")
        time.sleep(2)
        continue
        
    if response.status_code != 200:
        print(f"Failed to fetch page {page}. Status code: {response.status_code}")
        break
        
    data = response.json()
    bans = data if isinstance(data, list) else data.get("items", [])

    if not bans:
        break
        
    # Filter for cheating bans
    cheating_bans = [
        ban for ban in bans 
        if ban.get("reason") and "cheating" in ban.get("reason").lower()
    ]
    
    all_cheating_bans.extend(cheating_bans)
    print(f"Fetched page {page} ({len(bans)} records scanned, {len(cheating_bans)} matched)...")

    if len(bans) < page_size:
        break
        
    page += 1
    time.sleep(0.5)

# Initialize TF2 Bot Detector structure
tfbd_list = {
    "$schema": "https://raw.githubusercontent.com/PazerOP/tf2_bot_detector/master/schemas/v3/playerlist.schema.json",
    "file_info": {
        "authors": [
            "palmtopangie"
        ],
        "description": "RGL Cheating Bans list converted for TF2 Bot Detector",
        "title": "RGL Cheating Bans",
        "update_url": "https://raw.githubusercontent.com/palmtopangie/TF2-comp-bans/main/bans/playerlist.rglbans.json"
    },
    "players": []
}

for item in all_cheating_bans:
    steam64 = item.get("steamId")
    steam3 = steam64_to_steam3(steam64)
    
    if not steam3:
        continue

    alias = item.get("alias", "")
    reason = item.get("reason", "Cheating")
    created_at = item.get("createdAt", "")
    
    unix_time = iso_to_unix(created_at)

    player_entry = {
        "attributes": [
            "cheater"
        ],
        "last_seen": {
            "player_name": alias,
            "time": unix_time
        },
        "proof": [
            f"RGL Ban: {reason}"
        ],
        "steamid": steam3
    }
    
    tfbd_list["players"].append(player_entry)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(tfbd_list, f, indent=4)

print(f"Successfully generated {OUTPUT_FILE} with {len(tfbd_list['players'])} player entries.")