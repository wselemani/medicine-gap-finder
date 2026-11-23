import json
import time
from collections import Counter

with open("export/health_facilities.geojson", encoding="utf-8") as f:
    gj = json.load(f)


def center(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Point":
        return c[1], c[0]
    pts = []

    def walk(x):
        if isinstance(x[0], (int, float)):
            pts.append(x)
        else:
            for y in x:
                walk(y)

    walk(c)
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    return lat, lon


facilities = []
for ft in gj["features"]:
    p = ft["properties"]
    if not ft.get("geometry"):
        continue
    lat, lon = center(ft["geometry"])
    facilities.append({
        "name": p.get("name") or p.get("name_latin") or "Unnamed facility",
        "type": p.get("amenity") or p.get("healthcare") or "health facility",
        "region": p.get("adm1_name") or "Unknown",
        "district": p.get("adm2_name") or "Unknown",
        "lat": round(lat, 5),
        "lon": round(lon, 5),
    })

data = {
    "source": "HOT/HDX Malawi Health Facilities (OpenStreetMap export)",
    "built": time.strftime("%Y-%m-%d"),
    "facilities": facilities,
    "villages": [],
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f)

print("Saved data.json:", len(facilities), "facilities")
print("By region:", dict(Counter(x["region"] for x in facilities)))
print("By type:", dict(Counter(x["type"] for x in facilities)))
print("Unnamed:", sum(1 for x in facilities if x["name"] == "Unnamed facility"))