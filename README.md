# Medicine Access Gap Finder (Malawi)

A web app that shows how far people in Malawi are from the nearest hospital, clinic and pharmacy, so planners, NGOs and communities can see where new clinics and medicine supply points are most needed.

**Author:** Wezzie Selemani (GitHub: wselemani) | ALU Web Infrastructure summative, "Playing Around with APIs"

## Links

- **Live app (through the load balancer):** https://www.malisaweb.tech/gap/
- **Same app by IP (a certificate warning is expected, because the certificate is issued for the domain name):** https://18.132.46.194/gap/
- **Demo video :** https://youtu.be/RIlkcO670hs

**Credentials and API keys:** none are needed. Every API used is open and keyless, and the app has no login.

## The problem

Many people in rural Malawi travel long distances to a government hospital, only to be told there is no medicine. This app tackles the first half of that problem: **where are facilities missing?** Real stock levels of medicine in government hospitals are not published through any public API, so tracking stock-outs is listed below as future work.

## What the app does

- **Check access near a place:** type any place in Malawi. The app finds it with the Nominatim API, then shows the nearest hospital, clinic or health post, and pharmacy with straight-line distances, draws them on the map, and gives a verdict: **Good access** (listed clinic or hospital within 5 km), **Limited** (5 to 10 km), or **Underserved** (over 10 km). It also warns when no pharmacy is within 10 km. The 5 and 10 km cut-offs are a simple rule of thumb, not an official standard.
- **Search** facilities by name.
- **Filter** by type, region and district.
- **Sort** by name, district, or distance from the place you checked.
- **Map** that opens on Malawi, with colour-coded markers and a legend (red hospital, blue clinic or health post, green pharmacy, grey other) and a "Show all of Malawi" button.
- **Screen sizes:** the layout adapts to the screen (map on top and controls below on narrow screens).
- **Error handling:** clear messages when the facility data fails to load, when a place is not found, when the place search is unreachable (for example, no internet), and when filters match nothing.
- **Load balancer proof:** a green bar shows which server answered (`Served by: 7401-web-01` or `7401-web-02`).

## Why this isn't just a Google search

Google Maps can show the nearest clinic to one spot. This app does things a single search does not:

- It shows the nearest hospital, clinic **and** pharmacy together, with distances, and gives one verdict (good access, limited access or underserved). It also warns when no pharmacy is within 10 km, which matters when people travel to a hospital and find no medicine.
- It lets you filter and sort a national list of facilities by type, region, district or distance from a place you choose.
- It turns scattered map points into a gap analysis, which is the question planners ask: where is help missing?

## APIs and data sources

| Source | Used for | Link |
|---|---|---|
| Nominatim (OpenStreetMap) | Live place search (API call from the browser) | https://nominatim.org/release-docs/latest/api/Search/ |
| Malawi Health Facilities (OpenStreetMap export), Humanitarian OpenStreetMap Team via the Humanitarian Data Exchange | 345 facility records (`data.json`) | https://data.humdata.org/dataset/6ff3ff26-bd3a-47b7-87cf-10452147d8e3 |
| OpenStreetMap tiles | Map background | https://www.openstreetmap.org/copyright |
| Leaflet 1.9.4 | Map library | https://leafletjs.com |

Map and place data © OpenStreetMap contributors (ODbL). Thank you to the OpenStreetMap volunteers, HOT, HDX, the Nominatim team and the Leaflet developers.

## Run it locally

1. Install Python 3.
2. Clone the repo and open a terminal in the folder.
3. Start a small web server:
   ```bash
   python -m http.server 8000
   ```
4. Open http://localhost:8000 in your browser.

No installation, build step or API key is needed. An internet connection is required for the map tiles and the place search.

To rebuild `data.json` from the downloaded export (optional): `python build_data.py`.

## How I deployed it

The app is static (HTML, JavaScript and one JSON file), so each web server only needs the files.

1. Copied the files to each web server with `scp`:
   ```bash
   scp index.html data.json ubuntu@<server-ip>:/tmp/
   ```
2. Placed them in their own folder and made them readable by nginx:
   ```bash
   ssh ubuntu@<server-ip> "sudo mkdir -p /var/www/html/gap && sudo mv /tmp/index.html /tmp/data.json /var/www/html/gap/ && sudo chmod -R a+rX /var/www/html/gap"
   ```
3. Did the same on both web-01 (18.170.52.211) and web-02 (18.175.133.12).
4. Checked each server directly:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://18.170.52.211/gap/
   curl -s -o /dev/null -w "%{http_code}\n" http://18.175.133.12/gap/
   ```
   Both returned 200.

## How the load balancer is configured

lb-01 (18.132.46.194) runs HAProxy.

- HAProxy listens on port 80 and redirects HTTP traffic to HTTPS.
- The HTTPS frontend handles secure connections using a Let's Encrypt certificate for www.malisaweb.tech.
- Requests are forwarded to the `web_servers` backend.
- The round-robin algorithm distributes requests between web-01 and web-02.
- Health checks monitor the availability of both web servers.
- Each web server's nginx adds an `X-Served-By` header with its own name, which makes the balancing visible.

```
frontend http_front
    bind *:80
    mode http
    http-request redirect scheme https code 301

frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/www.malisaweb.tech.pem
    mode http
    http-request set-header X-Forwarded-Proto https
    default_backend web_servers

backend web_servers
    mode http
    balance roundrobin
    server web-01 18.170.52.211:80 check
    server web-02 18.175.133.12:80 check
```

**Testing:** requests through the load balancer alternate between the two servers:

```bash
for i in 1 2 3 4; do curl -skL -D - -o /dev/null http://18.132.46.194/gap/data.json | grep -i served; done
```

```
x-served-by: 7401-web-01
x-served-by: 7401-web-02
x-served-by: 7401-web-01
x-served-by: 7401-web-02
```

The `-L` flag follows the HTTP to HTTPS redirect and `-k` accepts the certificate mismatch on the IP address.

## Challenges and how I solved them

1. **API rejected my requests (HTTP 406).** The Overpass API refused Python's default request headers. I added a descriptive `User-Agent` header, and the requests worked.
2. **The free OpenStreetMap servers were overloaded (502 and 504 errors, timeouts).** Large downloads failed repeatedly on three different servers, even after retries and splitting the area into smaller pieces. I switched to the same OpenStreetMap health facility data published as a file by HOT on the Humanitarian Data Exchange, and converted it to a small `data.json` that loads instantly.
3. **No village list.** The village download failed for the same reason. Instead of a fixed list, the app uses the live Nominatim place search, so users can check any place name in Malawi.
4. **Map opened on all of Africa.** My first deployed version did not zoom to Malawi. I changed the code to fit the map to the facility locations, limited zooming out, and added a legend and a reset button.
5. **The load balancer redirects HTTP to HTTPS.** My first check returned 301, so the balancing test needed `-L` to follow the redirect.

## Data limitations (please read)

- OpenStreetMap is built by volunteers. Rural facilities are likely under-mapped, so some places will look more underserved than they are.
- Types are as volunteers tagged them. Many small health centres are tagged "hospital", which affects the "good access" verdict.
- Only 29 pharmacies are in the data, so "no pharmacy within 10 km" can mean "not mapped".
- 52 facilities have no name.
- Distances are straight lines, not walking or road distances.
- The app does **not** show medicine stock. That data is not public.

## Future work

- Real stock-out data from government hospitals, if it is ever published.
- Pharmacy and "double gap" ranking across the whole country, and suggested sites for new clinics or medicine drop-off points.
- Walking-time distances instead of straight lines.
- Chichewa language option.