import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://etf2l.org/etf2l/bans/{}/"
OUTPUT_FILE = "playerlist.etf2lbans.json"
BASE_STEAM64 = 76561197960265728

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_PATTERN = re.compile(
    r"cheat|wallhack|\besp\b|aimbot|triggerbot|speedhack|multihack", 
    re.IGNORECASE
)

def convert_steam3_to_64(steam3_str):
    """Converts a Steam3 ID like 'U:1:1473595211' to SteamID64."""
    match = re.search(r"U:1:(\d+)", steam3_str)
    if match:
        account_id = int(match.group(1))
        return str(BASE_STEAM64 + account_id)
    return steam3_str

def steam64_to_steam3(steam64_str):
    """Converts a SteamID64 string into Steam3 ID format [U:1:XXXXXXXX]."""
    try:
        account_id = int(steam64_str) - BASE_STEAM64
        return f"[U:1:{account_id}]"
    except (ValueError, TypeError):
        return None

def parse_etf2l_date(date_str):
    """Parses ETF2L date string to ISO 8601 format."""
    clean_str = date_str.strip()
    if clean_str.lower() == "permanent":
        return "9999-12-31T23:59:59.000Z"
    
    try:
        dt = datetime.strptime(clean_str.replace(", ", ","), "%d %b %Y,%H:%M")
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        return clean_str

def iso_to_unix(iso_str):
    """Converts an ISO 8601 string to a Unix integer timestamp."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except (ValueError, TypeError, AttributeError):
        return int(datetime.now(timezone.utc).timestamp())

print("Scraping ban list from ETF2L...")

all_bans = []
seen_players = set()
first_page_first_player = None
page = 1

while True:
    url = BASE_URL.format(page)
    
    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
    except requests.RequestException as e:
        print(f"Network error on page {page}: {e}")
        break
        
    if response.status_code == 404:
        print(f"Reached end of pages (page {page}).")
        break
        
    if response.status_code != 200:
        print(f"Failed to fetch page {page}. Status code: {response.status_code}")
        break

    final_url = response.url.rstrip("/")
    if page > 1 and (final_url.endswith("/etf2l/bans") or final_url.endswith("/bans/page/1")):
        print(f"Redirected to page 1 ({response.url}). Reached end of pagination.")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    
    table = soup.find("table")
    if not table:
        print(f"No ban table found on page {page}. Ending crawl.")
        break

    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
    
    if not rows:
        print(f"No table rows found on page {page}. Ending crawl.")
        break

    current_first_player = rows[0].get_text(strip=True)
    if page == 1:
        first_page_first_player = current_first_player
    elif current_first_player == first_page_first_player:
        print(f"Page {page} content matches Page 1. Reached end of pagination.")
        break

    page_matched = 0

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        row_text = row.get_text(separator=" ", strip=True)

        if SEARCH_PATTERN.search(row_text):
            player_anchor = row.find("a", href=True)
            
            alias = player_anchor.get_text(strip=True) if player_anchor else cols[0].get_text(strip=True)
            raw_steam3 = cols[1].get_text(strip=True)
            raw_created_at = cols[2].get_text(strip=True)
            raw_expires_at = cols[3].get_text(strip=True)
            reason = cols[4].get_text(strip=True)

            steam_id = convert_steam3_to_64(raw_steam3)

            if steam_id in seen_players:
                continue
                
            seen_players.add(steam_id)

            ban_entry = {
                "steamId": steam_id,
                "alias": alias,
                "expiresAt": parse_etf2l_date(raw_expires_at),
                "createdAt": parse_etf2l_date(raw_created_at),
                "reason": reason
            }

            all_bans.append(ban_entry)
            page_matched += 1

    print(f"Fetched page {page} ({len(rows)} records scanned, {page_matched} matched)...")

    page += 1
    time.sleep(1)

# Initialize TF2 Bot Detector structure
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

for item in all_bans:
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