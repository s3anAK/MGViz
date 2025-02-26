import sys
import re
import requests
import json


API_URL = 'http://localhost:8888/api'

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

sources = {'comb': 'Combination',
           'jpl': 'JPL',
           'sopac': 'SOPAC'}

filters = {'flt': 'Filter',
           'clean': 'Clean',
           'raw': 'Raw'}

sites_json = ''
url = API_URL + '/mgviz/coseismic?id=' + coseismic_id
try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    sites_json = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error retrieving sites JSON data: {e}")
    sys.exit()

features = []
for site in sites_json['sites']:
    metadata_url = f'{API_URL}/eseses/site/{site['site_id']}/{source}/{fil}/{ttype}'
    # print(metadata_url)
    # print(site['time_utc'])
    date_format = "%Y-%m-%d"
    date_utc = site['time_utc'].split('T')[0]

    try:
        response = requests.get(metadata_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        metadata_json = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving metadata JSON data: {e}")
        sys.exit()

    north_movement = ''
    east_movement = ''
    for component_terms, value in metadata_json['Component Terms'].items():
        c_source, c_fil = component_terms.split(' - ')
        # ignore offsets that don't match input parameters
        if c_source != sources[source] or c_fil != filters[fil]:
            continue
        for direction, coseismic in value.items():
            if 'Offset (coseismic)' in coseismic:
                # print('\n' + direction)
                for offset in coseismic['Offset (coseismic)']:
                    # Define the pattern for movement, error, and date
                    pattern = r"(-?\d+\.\d+)  \+\/-\   (-?\d+\.\d+) mm \((\d{4}-\d{2}-\d{2} \[\d{4}\.\d{4,5}\])"
                    # Use the re.search function to find the first occurrence of the pattern in the string
                    match = re.search(pattern, offset)
                    if match:
                        movement = float(match.group(1))
                        error = float(match.group(2))
                        date_str = match.group(3).split()[0]

                        # Get coseismic that matches the day
                        if date_str == date_utc:
                            # print(f"Movement: {movement}")
                            # print(f"Error: {error} mm")
                            # print(f"Date: {date_str}")
                            if direction == 'North':
                                north_movement = movement
                                error_north = error
                            if direction == 'East':
                                east_movement = movement
                                error_east = error
    feature = {
            "type": "Feature",
            "properties": {
                "site": site['site_id'],
                "x": site['x'],
                "y": site['y'],
                "e_vel": east_movement,
                "n_vel": north_movement,
                "u_vel": "",
                "time_utc": site['time_utc']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [site['x'], site['y']]
            }
        }
    features.append(feature)

# Define the data as a dictionary
data = {
    "type": "FeatureCollection",
    "name": "coseismic_vectors",
    "features": []
}
data['features'] = features

# Convert the dictionary to a JSON object and print
print(json.dumps(data))
sys.exit()
