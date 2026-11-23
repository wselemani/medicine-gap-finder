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

QUERIES = {
    "Hospitals/clinics": 'node["amenity"~"hospital|clinic|doctors"](area.a);way["amenity"~"hospital|clinic|doctors"](area.a);',
    "Villages/towns": 'node["place"~"village|town|city|hamlet"](area.a);',
}

for label, body in QUERIES.items():
    query = f'[out:json][timeout:90];area["ISO3166-1"="MW"][admin_level=2]->.a;({body});out count;'
    done = False
    for url in ENDPOINTS:
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=120)
            if r.status_code == 200:
                print(label, "->", r.json()["elements"][0]["tags"], "| via", url)
                done = True
                break
            print(label, "-> status", r.status_code, "from", url, r.text[:100])
        except Exception as e:
            print(label, "-> error from", url, ":", e)
    if not done:
        print(label, "-> all servers failed")
    time.sleep(5)
