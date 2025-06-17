import sys
import os
import os.path
import json
import glob
import re
import requests


API_URL = 'http://localhost:8888/api'


def query_detections(mode, model, site):
    """
    Query detections from the database.
    """
    params = {
        'mode': mode,
        'model': model,
        'site': site
    }
    url = f"{API_URL}/mgviz/detection"
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error querying detections: {response.status_code}')
        sys.exit(1)


path = 'private/eseses/tacls'

# get versions request
if (len(sys.argv) == 2):
    if str(sys.argv[1]).isalnum():   # mode
        path = os.path.join(path, str(sys.argv[1]))
    versions = [item for item in os.listdir(path) if os.path.isdir(os.path.join(path, item))]
    results = {'versions': sorted(versions)}
    print(json.dumps(results))
    sys.exit()

# Get args
if str(sys.argv[1]).isalnum():   # mode
    path = os.path.join(path, str(sys.argv[1]))
if str(sys.argv[2]).isalnum():   # site
    site = sys.argv[2]
if str(sys.argv[3]).isalnum():   # source
    source = sys.argv[3]
if str(sys.argv[4]).isalnum():   # Type
    fil = sys.argv[4]
if str(sys.argv[5]).isalnum():   # Trend/Detrend
    ttype = sys.argv[5]
if str(sys.argv[6]).isalnum():   # n e u
    neu = sys.argv[6]
if not re.search(r'[^a-zA-Z0-9_\-\.]', str(sys.argv[7])):   # version / source directory
    version = re.sub(r'[^a-zA-Z0-9_\-\.]', '', str(sys.argv[7]))
else:
    print('Invalid characters in version')
    sys.exit()

sources = {'comb': 'Comb',
           'combg': 'Combg',
           'jpl': 'JPL',
           'sopac': 'SOPAC',
           'sopacR20': 'SOPACR20'}

filters = {'flt': 'Filter',
           'clean': 'Clean',
           'raw': 'Raw',
           'rawm': 'Raw M'}

types = {'detrend': 'Detrend',
         'trend': 'Trend',
         'resid': 'Resid',
         'strain': 'Strain',
         'raw': 'Raw'}

metadata = []
plotlines = []
plotbands = []
name = site + ': ' + str(sources[source]) + '/' + filters[fil] + '/' + types[ttype] + ' -'
file_list = glob.glob(path + '/' + version + '/' + site + '*.json')
if len(file_list) == 0:
    file_list.append('query/database')
for idx, f in enumerate(sorted(file_list)):
    test_file = f
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            tacls = json.load(f)
            # print('\n' + json.dumps(tacls, indent=4) + '\n')
    else:
        # print(f'{test_file} does not exist...querying database')
        tacls = query_detections(str(sys.argv[1]), version, site)

    palette_line = ["#ffd92f", "#8da0cb", "#e78ac3", "#a6d854", "#377eb8"]
    plotline_dict = {"color": palette_line[idx], "dashStyle": "solid", "width": 2}

    palette_dict = ["rgb(255, 242, 174, 0.5)", "rgb(203, 213, 232, 0.5)", "rgb(244, 202, 228, 0.5)", "#rgb(230, 245, 201, 0.5)", "rgb(179, 205, 227, 0.5)"]
    plotband_dict = {"color": palette_dict[idx]}

    if 'detections' in tacls:
        for detection in tacls['detections']:
            # startdate
            plotline = plotline_dict.copy()
            plotline['value'] = detection['startdate']
            plotlines.append(plotline)
            # enddate
            plotline = plotline_dict.copy()
            plotline['value'] = detection['enddate']
            plotlines.append(plotline)
            # shade
            plotband = plotband_dict.copy()
            plotband['from'] = detection['startdate']
            plotband['to'] = detection['enddate']
            plotbands.append(plotband)

    if 'metadata' in tacls:
        tacls['metadata']['color'] = palette_line[idx]
        metadata.append(tacls['metadata'])

results = {'metadata': metadata, 'plotlines': plotlines, 'plotbands': plotbands}

print(json.dumps(results))
sys.exit()
