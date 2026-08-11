import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

# Fixed base URL path with /etf2l/ included
base_url = "https://etf2l.org/etf2l/bans/{}/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_PATTERN = re.compile(
    r"cheat|wallhack|\besp\b|aimbot|triggerbot|speedhack|multihack", 
    re.IGNORECASE
)

BASE_STEAM64 = 76561197960265728

def convert_steam3_to_64(steam3_str):
    """Converts a Steam3 ID like 'U:1:1473595211' to SteamID64."""
    match = re.search(r"U:1:(\d+)", steam3_str)
    if match:
        account_id = int(match.group(1))
        return str(BASE_STEAM64 + account_id)
    return steam3_str

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

all_bans = []
seen_players = set()
first_page_first_player = None
page = 1

print("Scraping ban list from ETF2L...")

while True:
    url = base_url.format(page)
    
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

    # Stop if ETF2L redirects an out-of-bounds page request back to page 1
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

    # Safety check: if page > 1 matches the first row of page 1, we looped back
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

output_file = "etf2l_cheating_bans.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_bans, f, indent=4)

print(f"Saved {len(all_bans)} total cheating bans to {output_file}.")