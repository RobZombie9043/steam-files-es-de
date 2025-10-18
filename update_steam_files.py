import os
import re
import json
import hashlib
import requests

STEAM_APPS_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
OUTPUT_DIR = "steam"


def sanitize_filename(name, max_length=100):
    """
    GitHub-safe filename:
    - Removes / and null bytes
    - Normalizes spaces
    - Truncates long names and appends hash to avoid filename-too-long errors
    """
    name = name.strip()
    name = name.replace("/", "-")
    name = name.replace("\0", "")
    name = re.sub(r"\s+", " ", name)

    if len(name) > max_length:
        hash_suffix = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
        name = f"{name[:50]}…{hash_suffix}{name[-20:]}"

    return name


def main():
    print("📥 Downloading Steam app list...")
    response = requests.get(STEAM_APPS_URL, timeout=60)
    response.raise_for_status()
    data = response.json()
    apps = data.get("applist", {}).get("apps", [])

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

        # Determine subfolder: only A-Z, everything else -> 0-9+
        first_char = safe_name[0].upper()
        if first_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            subfolder = first_char
        else:
            subfolder = "0-9+"

        folder_path = os.path.join(OUTPUT_DIR, subfolder)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, f"{safe_name}.steam")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(appid))

        total_written += 1

    # Save all apps as JSON reference
    with open(os.path.join(OUTPUT_DIR, "steam_app_list.json"), "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2)

    print(f"✅ Done! Created {total_written} .steam files in '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()
