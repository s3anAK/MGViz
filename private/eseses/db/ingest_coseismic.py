#!/usr/bin/env python3

import os
import argparse
import psycopg2
import getpass
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

LIST = "./CoseismicOffset_EarthquakeMasterList.csv"
METADATA = '../metadata'


def ingest_coseismics(df, conn, limit):
    cur = conn.cursor()
    total = 0
    skipped = 0

    for idx, row in df.iterrows():
        # Get the Date and Time
        date_str = str(row['Date (UTC)'])
        time = row['Time (UTC)']
        location = row['Location/Local Name']
        magnitude = row['Magnitude']

        # Handle date formats: "%Y-%m-%d" and "%m/%d/%Y"
        try:
            # First try parsing as "%Y-%m-%d"
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            try:
                # If that fails, try parsing as "%m/%d/%Y"
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                print(f'Invalid date format: {date_str}...skipping')
                skipped += 1
                continue

        date_time = formatted_date + ' ' + str(time) + '+00:00'
        latitude = float(str(row['Latitude']).replace('°', ''))
        latdir = row[row.index.get_loc('Latitude')+1]
        longitude = float(str(row['Longitude']).replace('°', ''))
        londir = row[row.index.get_loc('Longitude')+1]

        # Print record
        print(f"Record {idx}: Date = {date_str} -> {formatted_date}, Time = {time}, \
              Lat = {latitude} {latdir}, Lon = {longitude} {londir}, \
              Magnitude = {magnitude}, Location = {location}")

        # Correct lat and lon values
        if latdir == 'S':
            latitude = latitude * -1
        if londir == 'W':
            longitude = longitude * -1

        # Validate final datetime string
        try:
            datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S+00:00')
        except ValueError:
            print(f'Invalid datetime: {date_time}...skipping')
            skipped += 1
            continue

        if limit == idx:
            break
        total = idx
        sql = '''
        INSERT INTO coseismic (time_utc, location, magnitude, geom)
        VALUES (%s, %s, %s, ST_GeomFromText('POINT(%s %s)', 4326))
        ON CONFLICT (time_utc) DO UPDATE
        SET location = excluded.location,
            magnitude = excluded.magnitude,
            geom = excluded.geom;
        '''
        cur.execute(sql, (date_time, location, magnitude, longitude, latitude))
        conn.commit()
    print('Inserted %i coseismic records' % (total - skipped + 1))


def link_sites(metadata_dir, conn):
    print('Linking sites in', metadata_dir)
    namespaces = {'ns': 'http://sopac.ucsd.edu/ns/geodesy/2014'}
    date_format = "%Y-%m-%d"

    for filename in sorted(os.listdir(metadata_dir)):
        if filename.endswith('.xml'):  # Check if file is an XML file
            site = filename.split('.')[0]
            file_path = os.path.join(metadata_dir, filename)
            records = []
            try:
                tree = ET.parse(file_path)  # Parse the XML file into an ElementTree object
                root = tree.getroot()  # Get the root element of the document
                components = root.findall('.//ns:componentTerms', namespaces)
                neu = ''
                for component in components:
                    neu_component = component.find('ns:component', namespaces).text
                    neu += {'north': 'n', 'east': 'e', 'up': 'u'}[neu_component]
                    # Find all "offset" nodes with type="coseismic"
                    offset_nodes = component.findall('.//ns:offset[@type="coseismic"]', namespaces)

                    if offset_nodes:
                        for node in offset_nodes:
                            reference_epoch = node.find('ns:referenceEpoch', namespaces)
                            if reference_epoch is not None:
                                value = reference_epoch.text
                                time_utc = datetime.strptime(value.split('T')[0], date_format)
                                # match if date one day plus/minus
                                date_plus1 = time_utc + timedelta(days=1)
                                date_minus1 = time_utc - timedelta(days=1)

                                cur = conn.cursor()
                                query = """
                                            SELECT *
                                            FROM public.coseismic
                                            WHERE time_utc BETWEEN %s AND %s;
                                        """

                                try:
                                    cur.execute(query, (date_minus1, date_plus1))
                                    rows = cur.fetchall()
                                    for row in rows:
                                        coseismic_id = row[0]
                                        print(f'Coseismic {str(coseismic_id)} found for {value} site: {site}')
                                        record = (site, str(coseismic_id), neu)
                                        records.append(record)
                                        break # match only one coseismic
                                    else:
                                        print(f'No matching coseismic found for {value} site: {site}')
                                except (Exception, psycopg2.DatabaseError) as error:
                                    print(error)
            except ET.ParseError as e:
                print(f'Failed to parse file {file_path}: {e}')

            for record in records:
                # Insert into site_coseismic table
                print(f'Inserting record: {record}')
                try:
                    sql = '''
                    INSERT INTO site_coseismic (site_id, coseismic_id, neu)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (site_id, coseismic_id) DO UPDATE
                    SET neu = excluded.neu;
                    '''
                    cur.execute(sql, record)
                    conn.commit()
                except psycopg2.errors.ForeignKeyViolation as e:
                    print(f'Skipping record due to ForeignKeyViolation: {record}')
                    print(e)
                    conn.rollback()  # Roll back violating record
                    continue  # Skip to next record


parser = argparse.ArgumentParser(description='Parses coseismic data and insert into MGViz tables.')
parser.add_argument(
    '--linkonly',
    dest='linkonly',
    default=False,
    action='store_true',
    help='Do not ingest new coseismic data.')
parser.add_argument(
    '--nolink',
    dest='nolink',
    default=False,
    action='store_true',
    help='Do use link coseismic to sites')
parser.add_argument(
    '--nopass',
    dest='nopass',
    default=False,
    action='store_true',
    help='Do use a password')
parser.add_argument(
    '--filepath',
    dest='filepath',
    default=LIST,
    help='File path to Excel list of coseismic offsets',
    action='store')
parser.add_argument(
    '-l',
    '--limit',
    default='-1',
    dest='limit',
    help='Limit the number of rows to process',
    action='store')
parser.add_argument(
    '-m',
    '--metadata',
    default=METADATA,
    dest='metadata',
    help='Location of metadata files',
    action='store')
parser.add_argument(
    '-n',
    '--dbname',
    default='postgres',
    dest='dbname',
    help='The database name',
    action='store')
parser.add_argument(
    '-p',
    '--port',
    default='5432',
    dest='port',
    help='The database port',
    action='store')
parser.add_argument(
    '-s',
    '--host',
    default='localhost',
    dest='host',
    help='The database server host',
    action='store')
parser.add_argument(
    '-u',
    '--user',
    default='postgres',
    dest='user',
    help='The database user',
    action='store')

args = parser.parse_args()
if args.nopass:
    password = ''
else:
    password = getpass.getpass()


# Connect to database
conn_string = str('host=%s dbname=%s user=%s port=%s password=%s' % (args.host,
                                                                     args.dbname,
                                                                     args.user,
                                                                     args.port,
                                                                     password))
conn = psycopg2.connect(conn_string)

# Parse data and insert into the database
try:
    if not args.linkonly:
        # Parse Excel sheet
        print('Parsing ', args.filepath)
        
        # Check if there's an extra row to skip
        with open(args.filepath, 'r') as file:
            first_line = file.readline().strip()
            if first_line[0:2] == ',,':
                df = pd.read_csv(args.filepath, skiprows=[0,2])
            else:
                df = pd.read_csv(args.filepath)
        print(df.head())
        ingest_coseismics(df, conn, int(args.limit))
    if not args.nolink:
        link_sites(args.metadata, conn)
finally:
    conn.close()
    print('Exiting')
