#!/usr/bin/env python3
"""
Hades' Star White Star (WS) Match Scraper & Incremental Updater.

Features:
- Incremental updates: remembers downloaded match IDs in results_list.txt and skips them.
- Fast multithreaded downloading (20-30 concurrent workers).
- Resumable: if interrupted, rerun it to pick up where it left off.
- Target Corp filtering: filter by specific corps, or leave empty to download everything.
- Zero external dependencies: runs with standard Python 3.
"""

import json
import csv
import os
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
# Leave empty [] to download ALL corporations, or add specific names:
TARGET_CORPS = [
    # "Blood Hounds",
    # "Continuum",
]

# File paths
SAVE_CSV = "global_results.csv"
RESULTS_LIST = "results_list.txt"

# Set concurrency (20-25 workers provides optimal throughput)
MAX_WORKERS = 25

# Max matches to fetch (set to None to download everything)
MAX_MATCHES = None

BUCKET_NAME = "hades-star-public-xq8f-d4rg-v0d9"
BASE_API = f"https://storage.googleapis.com/storage/v1/b/{BUCKET_NAME}/o"

CSV_HEADER = [
    "Key",
    "DateEnded",
    "Corporation1Name",
    "Corporation1Id",
    "Corporation2Name",
    "Corporation2Id",
    "Corporation1Score",
    "Corporation2Score",
    "Winner",
]


def load_known_keys() -> set[str]:
    """Load previously processed match UUIDs from state file and CSV."""
    known = set()
    if os.path.isfile(RESULTS_LIST):
        with open(RESULTS_LIST, "r", encoding="utf-8") as f:
            for line in f:
                k = line.strip()
                if k:
                    known.add(k)

    # Also inspect CSV if results_list was missing
    if os.path.isfile(SAVE_CSV) and not known:
        with open(SAVE_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if row:
                    known.add(row[0].strip())
    return known


def match_contains_corp(match_data: dict, target_corps: list[str]) -> bool:
    """Return True if match involves any of the target corporations."""
    if not target_corps:
        return True

    c1 = (match_data.get("Corporation1Name") or "").lower()
    c2 = (match_data.get("Corporation2Name") or "").lower()

    for target in target_corps:
        t = target.strip().lower()
        if t in c1 or t in c2:
            return True
    return False


def fetch_match_payload(blob_id: str) -> tuple[str, dict | None]:
    """Download and parse an individual match JSON."""
    url = f"https://storage.googleapis.com/download/storage/v1/b/{BUCKET_NAME}/o/{blob_id}?alt=media"
    req = urllib.request.Request(url, headers={"User-Agent": "HadesStarWSScraper/2.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return blob_id, data
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return blob_id, None


def main():
    print("=" * 70)
    print("🛸 Hades' Star White Star Ingestion & Incremental Updater")
    print(f"Target Filter : {TARGET_CORPS if TARGET_CORPS else 'ALL Corporations (Full Archive)'}")
    print(f"Concurrency   : {MAX_WORKERS} workers")
    print(f"Output File   : {SAVE_CSV}")
    print("=" * 70)

    known_keys = load_known_keys()
    print(f"📁 Loaded {len(known_keys):,} existing matches already in local database.")

    # Initialize CSV header if file doesn't exist
    file_exists = os.path.isfile(SAVE_CSV)
    csv_file = open(SAVE_CSV, "a", newline="", encoding="utf-8")
    writer = csv.writer(csv_file, dialect="excel")
    if not file_exists:
        writer.writerow(CSV_HEADER)
        csv_file.flush()

    state_file = open(RESULTS_LIST, "a", encoding="utf-8")

    page_token = None
    total_scanned = 0
    new_added = 0
    skipped_existing = 0

    try:
        while True:
            # Query 1,000 blob names per page (lightweight metadata request)
            params = {
                "maxResults": 1000,
                "fields": "items(name),nextPageToken",
            }
            if page_token:
                params["pageToken"] = page_token

            query_url = f"{BASE_API}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(query_url, headers={"User-Agent": "HadesStarWSScraper/2.0"})

            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    catalog = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"⚠️ Error fetching object list: {e}. Retrying in 2s...")
                time.sleep(2)
                continue

            items = catalog.get("items", [])
            if not items:
                break

            # Identify which items on this page are truly new
            batch_to_download = []
            for item in items:
                blob_id = item["name"]
                total_scanned += 1
                if blob_id in known_keys:
                    skipped_existing += 1
                else:
                    batch_to_download.append(blob_id)

            if MAX_MATCHES is not None:
                needed = MAX_MATCHES - new_added
                if needed <= 0:
                    break
                batch_to_download = batch_to_download[:needed]

            # Download new items concurrently in parallel threads
            if batch_to_download:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    future_to_id = {executor.submit(fetch_match_payload, bid): bid for bid in batch_to_download}
                    for future in as_completed(future_to_id):
                        blob_id, match = future.result()
                        if not match:
                            continue

                        # Mark as known so we never re-request it
                        known_keys.add(blob_id)
                        state_file.write(f"{blob_id}\n")

                        if match_contains_corp(match, TARGET_CORPS):
                            c1_name = match.get("Corporation1Name", "Unknown")
                            c1_score = match.get("Corporation1Score", 0)
                            c2_name = match.get("Corporation2Name", "Unknown")
                            c2_score = match.get("Corporation2Score", 0)
                            date_ended = match.get("DateEnded", "")

                            winner = c1_name if c1_score > c2_score else (c2_name if c2_score > c1_score else "Draw")
                            row = [
                                blob_id,
                                date_ended,
                                c1_name,
                                match.get("Corporation1Id", ""),
                                c2_name,
                                match.get("Corporation2Id", ""),
                                c1_score,
                                c2_score,
                                winner,
                            ]
                            writer.writerow(row)
                            new_added += 1

                            if new_added % 10 == 0 or len(TARGET_CORPS) > 0:
                                d_short = date_ended[:19].replace("T", " ")
                                print(f"🎯 [{d_short}] {c1_name} ({c1_score}) vs {c2_name} ({c2_score}) → {winner}")

                    csv_file.flush()
                    state_file.flush()

            print(f"📊 Progress: {total_scanned:,} cataloged | {skipped_existing:,} skipped | {new_added:,} saved")

            if MAX_MATCHES and new_added >= MAX_MATCHES:
                print(f"\n⏹️ Reached configured limit of {MAX_MATCHES} matches.")
                break

            page_token = catalog.get("nextPageToken")
            if not page_token:
                print("\n🏁 Reached end of public White Star bucket archive.")
                break

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user. All downloaded progress is safely saved.")
    finally:
        csv_file.close()
        state_file.close()
        print("=" * 70)
        print(f"Summary: {new_added:,} new matches added | {skipped_existing:,} skipped (already cached)")
        print(f"Saved in: {SAVE_CSV} and {RESULTS_LIST}")
        print("=" * 70)


if __name__ == "__main__":
    main()
