import os
import re
import json
import hashlib
import requests

# New endpoint – paginated – requires API key
STEAM_API_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
OUTPUT_DIR = "steam"

def sanitize_filename(name, max_length=100):
    name = name.strip()
    name = name.replace("/", "-")
    name = name.replace("\0", "")
    name = re.sub(r"\s+", " ", name)

    if len(name) > max_length:
        hash_suffix = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
        name = f"{name[:50]}…{hash_suffix}{name[-20:]}"

    return name


def fetch_all_steam_apps(api_key):
    """Fetch the entire Steam app list using paginated IStoreService."""
    apps = []
    last_appid = 0

    print("📥 Fetching app list from IStoreService/GetAppList/v1 ...")

    while True:
        params = {
            "key": api_key,
            "include_games": True,
            "include_dlc": True,
            "include_software": True,
            "include_videos": False,
            "include_demos": True,
            "include_tools": True,
            "include_media": False,
            "include_hardware": False,
            "last_appid": last_appid,
            "max_results": 50000
        }

        response = requests.get(STEAM_API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        page_apps = data.get("response", {}).get("apps", [])
        if not page_apps:
            break

        apps.extend(page_apps)

        # Break if we reached the end
        new_last = page_apps[-1]["appid"]
        if new_last == last_appid:
            break

        last_appid = new_last
        print(f"  → Loaded {len(apps)} apps so far...")

    print(f"✅ Total apps downloaded: {len(apps)}")
    return apps


def main():
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing STEAM_API_KEY environment variable!")

    apps = fetch_all_steam_apps(api_key)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total_written = 0

    for app in apps:
        appid = app.get("appid")
        name = app.get("name", "").strip()
        if not appid or not name:
            continue

        safe_name = sanitize_filename(name)
        if not safe_name:
            continue

        first_char = safe_name[0].upper()
        subfolder = first_char if first_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "0-9+"

        folder_path = os.path.join(OUTPUT_DIR, subfolder)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, f"{safe_name}.steam")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(appid))

        total_written += 1

    with open(os.path.join(OUTPUT_DIR, "steam_app_list.json"), "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2)

    print(f"✅ Done! Created {total_written} .steam files in '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()
