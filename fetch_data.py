import json
import os
import time
import requests

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
HEADERS = {
    "User-Agent": "medicine-gap-finder/1.0 (ALU student project, Malawi)",
    "Accept": "*/*",
}

# Malawi's bounding box (south, west, north, east)
S, W, N, E = -17.2, 32.6, -9.3, 36.0
BANDS = [(-17.2, -15.6), (-15.6, -14.0), (-14.0, -12.4), (-12.4, -9.3)]


def run(label, body):
    cache = f"cache_{label}.json"
    if os.path.exists(cache):
        print(label, "already downloaded, skipping")
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    query = f"[out:json][timeout:25];({body});out center tags;"
    for attempt in range(1, 4):
        for url in ENDPOINTS:
            print(time.strftime("%H:%M:%S"), label, "trying", url.split("/")[2], flush=True)
            try:
                r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=30)
                if r.status_code == 200:
                    elements = r.json()["elements"]
                    with open(cache, "w", encoding="utf-8") as f:
                        json.dump(elements, f)
                    print("   OK:", len(elements), "items", flush=True)
                    return elements
                print("   status", r.status_code, flush=True)
            except Exception as e:
                print("   error:", type(e).__name__, flush=True)
        print("   round", attempt, "failed, waiting 10 seconds", flush=True)
        time.sleep(10)
    raise SystemExit(label + " failed. Wait a few minutes and run again; finished pieces are saved.")


def point(e):
    if "lat" in e:
        return e["lat"], e["lon"]
    c = e.get("center")
    return (c["lat"], c["lon"]) if c else (None, None)


raw_fac = run(
    "facilities",
    f'node["amenity"~"hospital|clinic|doctors"]({S},{W},{N},{E});way["amenity"~"hospital|clinic|doctors"]({S},{W},{N},{E});',
)

raw_vil = []
for i, (south, north) in enumerate(BANDS, start=1):
    time.sleep(2)
    raw_vil += run(f"villages_{i}", f'node["place"~"village|town|city|hamlet"]({south},{W},{north},{E});')

facilities, villages = [], []
for e in raw_fac:
    lat, lon = point(e)
    if lat is not None:
        facilities.append({
            "name": e.get("tags", {}).get("name", "Unnamed facility"),
            "type": e.get("tags", {}).get("amenity", "clinic"),
            "lat": lat, "lon": lon,
        })
for e in raw_vil:
    lat, lon = point(e)
    name = e.get("tags", {}).get("name")
    if lat is not None and name:
        villages.append({"name": name, "lat": lat, "lon": lon})

with open("data.json", "w", encoding="utf-8") as f:
    json.dump({"fetched": time.strftime("%Y-%m-%d"), "facilities": facilities, "villages": villages}, f)

print("Saved data.json:", len(facilities), "facilities,", len(villages), "named villages")