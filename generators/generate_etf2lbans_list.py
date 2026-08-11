import requests
import json
from datetime import datetime, timezone

# Source URL for your raw ETF2L bans
SOURCE_URL = "https://raw.githubusercontent.com/palmtopangie/tf2-comp-bans/refs/heads/main/bans/etf2l_cheating_bans.json"
OUTPUT_FILE = "playerlist.etf2lbans.json"

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

print("Fetching ETF2L bans from GitHub...")
response = requests.get(SOURCE_URL)

if response.status_code != 200:
    print(f"Failed to fetch source file. Status code: {response.status_code}")
    exit(1)

raw_bans = response.json()

tfbd_list = {
    "$schema": "https://raw.githubusercontent.com/PazerOP/tf2_bot_detector/master/schemas/v3/playerlist.schema.json",
    "file_info": {
        "authors": [
            "palmtopangie"
        ],
        "description": "ETF2L Cheating Bans list converted for TF2 Bot Detector",
        "title": "ETF2L Cheating Bans",
        "update_url": "https://raw.githubusercontent.com/palmtopangie/TF2-comp-bans/main/bans/playerlist.etf2lbans.json"
    },
    "players": []
}

for item in raw_bans:
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
            f"ETF2L Ban: {reason}"
        ],
        "steamid": steam3
    }
    
    tfbd_list["players"].append(player_entry)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(tfbd_list, f, indent=4)

print(f"Successfully generated {OUTPUT_FILE} with {len(tfbd_list['players'])} player entries.")