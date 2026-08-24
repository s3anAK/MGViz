import sys
import re
import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

API_URL = 'http://localhost:8888/api'
OFFSET_PATTERN = re.compile(
    r"(-?\d+\.\d+)\s+\+/-\s+(-?\d+\.\d+)\s+mm\s+\((\d{4}-\d{2}-\d{2} \[\d{4}\.\d{4,5}\])\)"
)
MAX_WORKERS = 16

if str(sys.argv[1]).isalnum():   # site
    coseismic_id = sys.argv[1]
else:
    print('No coseismic ID provided.')
    sys.exit()
if str(sys.argv[2]).isalnum():
    source = sys.argv[2]
if str(sys.argv[3]).isalnum():
    fil = sys.argv[3]
if str(sys.argv[4]).isalnum():
    ttype = sys.argv[4]

# Match site.py: Component Terms only come from Filter/Clean *Detrend.neu files.
# Raw never contributes offsets there, so vectors stay empty for fil=raw.
filters = {'flt': 'Filter',
           'clean': 'Clean'}

vectors_json = f'Missions/MGViz/Layers/earthquake_vectors/{coseismic_id}/{source}/{fil}/{ttype}.json'


def print_cache_and_exit(path):
    with open(path, 'r') as out:
        print(out.read())
    sys.exit()


# Use cached file if it exists and is less than one day old
if os.path.exists(vectors_json):
    mtime = datetime.fromtimestamp(os.path.getmtime(vectors_json))
    diff = datetime.now() - mtime
    if diff.days == 0:
        print_cache_and_exit(vectors_json)


def parse_coseismic_offsets(neu_file, date_utc):
    """Read .neu header only; return (east_mm, north_mm, up_mm) matching site.py rules."""
    north_movement = ''
    east_movement = ''
    up_movement = ''
    if not os.path.exists(neu_file):
        return east_movement, north_movement, up_movement

    date_utc_dt = datetime.strptime(date_utc, "%Y-%m-%d")
    direction = None
    with open(neu_file, 'r', errors='replace') as f:
        for li in f:
            if not li.startswith('#'):
                break
            if 'Reference' in li:
                continue
            if 'East' in li or 'e component' in li:
                direction = 'East'
            elif 'North' in li or 'n component' in li:
                direction = 'North'
            elif 'Up' in li or 'u component' in li:
                direction = 'Up'
            elif direction in ('North', 'East', 'Up') and 'offset' in li and 'coseismic' not in li:
                # site.py: li[1] == '*' marks coseismic offset
                if len(li) > 1 and li[1] == '*':
                    match = OFFSET_PATTERN.search(li)
                    if match:
                        movement = float(match.group(1))
                        date_str = match.group(3).split()[0]
                        date_difference = abs(
                            date_utc_dt - datetime.strptime(date_str, "%Y-%m-%d")
                        )
                        if date_difference <= timedelta(days=1):
                            if direction == 'North':
                                north_movement = movement
                            elif direction == 'East':
                                east_movement = movement
                            elif direction == 'Up':
                                up_movement = movement
    return east_movement, north_movement, up_movement


def site_feature(site):
    site_id = site['site_id']
    date_utc = site['time_utc'].split('T')[0]
    east_movement = ''
    north_movement = ''
    up_movement = ''

    # site.py only loads Filter/Clean Detrend files for Component Terms
    if fil in filters:
        neu_file = f"private/eseses/data/{source}/{site_id}{filters[fil]}Detrend.neu"
        try:
            east_movement, north_movement, up_movement = parse_coseismic_offsets(
                neu_file, date_utc
            )
        except Exception:
            # Keep empty vectors for this site; do not fail the whole request
            east_movement = ''
            north_movement = ''
            up_movement = ''

    return {
        "type": "Feature",
        "properties": {
            "site": site_id,
            "x": site['x'],
            "y": site['y'],
            # TODO: rename to e_disp/n_disp/u_disp (mm offsets, not velocities);
            # keep *_vel for now so Map_.js Vectors styling can reuse the same keys.
            "e_vel": east_movement,
            "n_vel": north_movement,
            "u_vel": up_movement,
            "time_utc": site['time_utc']
        },
        "geometry": {
            "type": "Point",
            "coordinates": [site['x'], site['y']]
        }
    }


url = API_URL + '/mgviz/coseismic?id=' + coseismic_id
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    sites_json = response.json()
except requests.exceptions.RequestException as e:
    # Prefer stale cache over an error string if a previous build exists
    if os.path.exists(vectors_json):
        print_cache_and_exit(vectors_json)
    print(f"Error retrieving sites JSON data: {e}")
    sys.exit()

sites = sites_json.get('sites', [])
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    features = list(executor.map(site_feature, sites))

data = {
    "type": "FeatureCollection",
    "name": "coseismic_vectors",
    "features": features
}

os.makedirs(os.path.dirname(vectors_json), exist_ok=True)
with open(vectors_json, 'w') as json_file:
    json.dump(data, json_file, indent=4)
print(json.dumps(data))
sys.exit()
