#!/usr/bin/env python3

import argparse
import psycopg2
import getpass
import json
import os
from pathlib import Path
from datetime import datetime, timedelta


def is_leap_year(year):
    # Check if a year is a leap year
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def convert_decimal_date(decimal_date):
    # Extract the year and the fractional part
    year = int(decimal_date)
    remainder = decimal_date - year

    # Determine the number of days in the year
    days_per_year = 366 if is_leap_year(year) else 365

    # Calculate the number of seconds for the fractional part
    seconds = remainder * days_per_year * 24 * 60 * 60

    # Create a datetime object for January 1st of the given year
    year_start = datetime(year, 1, 1)

    # Add the fractional seconds to the start of the year
    result_date = year_start + timedelta(seconds=seconds)

    return str(result_date)


def convert_seconds_to_date(js_timestamp):
    # Convert to Python datetime
    new_date = datetime.fromtimestamp(js_timestamp/1000)
    return str(new_date)


def ingest_detection(input_dir, conn, limit):
    cur = conn.cursor()
    idx = 0
    model = os.path.basename(os.path.normpath(input_dir))
    mode = os.path.basename(os.path.dirname(os.path.normpath(input_dir)))
    print('Model:', model)
    print('Mode:', mode)

    # Get model ID; if not exists, then add new model
    cur = conn.cursor()
    query = """
                SELECT id
                FROM public.model
                WHERE name=%s AND mode=%s;
            """
    try:
        cur.execute(
            query, (model, mode))
        row = cur.fetchone()
        if row:
            model_id = row[0]
            print(f'Found model {model} with mode {mode} with id: {model_id}')
        else:
            print(f'No matching model found for {model}, mode: {mode}')
            # Insert new model
            sql = '''
            INSERT INTO model (name, mode)
            VALUES (%s, %s)
            RETURNING id;
            '''
            cur.execute(sql, (model, mode))
            model_id = cur.fetchone()[0]
            conn.commit()
            print(f'Inserted new model: {model}, mode: {mode}, id: {model_id}')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        exit(1)

    for path in sorted(Path(input_dir).rglob('*')):
        if path.is_file():
            if limit == idx:
                break
            idx += 1
            print('Ingesting', path)
            try:
                data = json.load(open(path))
            except json.JSONDecodeError as e:
                print(f'Error decoding JSON from {path}: {e}')
                continue
            if data['metadata']['modelid'] != model_id:
                print('Warning: Model ID mismatch:',
                      data['metadata']['modelid'], model_id)
            site_id = data['metadata']['stationid']
            label = data['metadata'].get('label', None)
            eventtype = data['metadata'].get('eventtype', None)
            for detection in data['detections']:
                detection_id = detection['id']
                probability = detection.get('probabilities', None)
                # convert from decimal year or JavaScript seconds
                if '.' in str(detection['startdate']):
                    startdate = convert_decimal_date(detection['startdate'])
                else:
                    startdate = convert_seconds_to_date(detection['startdate'])
                if '.' in str(detection['enddate']):
                    enddate = convert_decimal_date(detection['enddate'])
                else:
                    enddate = convert_seconds_to_date(detection['enddate'])

                sql = '''
                INSERT INTO detection (detection_id, site_id, model_id, label, eventtype,
                                       probability, startdate, enddate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (detection_id, site_id, model_id) DO UPDATE
                SET detection_id = excluded.detection_id,
                    site_id = excluded.site_id,
                    model_id = excluded.model_id,
                    label = excluded.label,
                    eventtype = excluded.eventtype,
                    probability = excluded.probability,
                    startdate = excluded.startdate,
                    enddate = excluded.enddate;
                '''
                cur.execute(sql, (detection_id, site_id, model_id, label, eventtype,
                                  probability, startdate, enddate))
                conn.commit()
            print('Inserted detections from %i files' % idx)


parser = argparse.ArgumentParser(description='Parses TACLS outputs and insert detections into MGViz tables.')
parser.add_argument(
    '--nopass',
    dest='nopass',
    default=False,
    action='store_true',
    help='Do use a password')
parser.add_argument(
    '-i',
    dest='input_dir',
    default='../tacls/geodetic/default',
    help='Input data for detections',
    action='store')
parser.add_argument(
    '-l',
    '--limit',
    default='-1',
    dest='limit',
    help='Limit the number of rows to process',
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
    ingest_detection(args.input_dir, conn, int(args.limit))
finally:
    conn.close()
    print('Exiting')
