#!/usr/bin/env python3

import argparse
import psycopg2
import getpass
from pathlib import Path
from datetime import datetime, timedelta, timezone
import calendar
import time
import gzip


def convert_seconds_to_date(seconds_since_2000):
    # Define the start date: January 1, 2000
    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    # Calculate the new date by adding the seconds
    new_date = start_date + timedelta(seconds=seconds_since_2000)
    formatted_date = new_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    return formatted_date


def ingest_tropo(input_dir, conn, limit):
    cur = conn.cursor()
    idx = 0
    for path in sorted(Path(input_dir).rglob('*')):
        if path.is_file():
            if limit == idx:
                break
            idx += 1
            print('Ingesting', path)
            source = tro2read(str(path))
            site = list(source.keys())[0]
            times = source[site]
            for tm, val in times.items():
                site = site.lower()
                time_utc = convert_seconds_to_date(tm)
                trotot = val.get('TROTOT', 'NULL')
                trototstdev = val.get('TROTOTSTDEV', 'NULL')
                trodry = val.get('TRODRY', 'NULL')
                trodrystdev = val.get('TRODRYSTDEV', 'NULL')
                trowet = val.get('TROWET', 'NULL')
                trowetstdev = val.get('TROWETSTDEV', 'NULL')
                tgnwet = val.get('TGNWET', 'NULL')
                tgnwetstdev = val.get('TROTOTSTDEV', 'NULL')
                tgewet = val.get('TGEWT', 'NULL')
                tgewetstdev = val.get('TROTOTSTDEV', 'NULL')
                iwv = val.get('TWV', 'NULL')
                press = val.get('PRESS', 'NULL')
                temdry = val.get('TEMDRY', 'NULL')

                sql = '''
                INSERT INTO troposphere (site, time_utc, trotot, trototstdev, trodry, trodrystdev, trowet, trowetstdev, tgnwet, tgnwetstdev, tgewet, tgewetstdev, iwv, press, temdry)
                VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (site, time_utc) DO UPDATE
                SET time_utc = excluded.time_utc,
                    trotot = excluded.trotot,
                    trototstdev = excluded.trototstdev,
                    trodry = excluded.trodry,
                    trodrystdev = excluded.trodrystdev,
                    trowet = excluded.trowet,
                    trowetstdev = excluded.trowetstdev,
                    tgnwet = excluded.tgnwet,
                    tgnwetstdev = excluded.tgnwetstdev,
                    tgewet = excluded.tgewet,
                    tgewetstdev = excluded.tgewetstdev,
                    iwv = excluded.iwv,
                    press = excluded.press,
                    temdry = excluded.temdry;
                ''' % (site, time_utc, trotot, trototstdev, trodry, trodrystdev, trowet, trowetstdev, tgnwet, tgnwetstdev, tgewet, tgewetstdev, iwv, press, temdry)
                cur.execute(sql)
                conn.commit()
            print('Inserted %i tropospheric records' % idx)


def tro2read(fn):
    trop = {}
    solutionBlock = False
    if fn.endswith('gz'):
        f = gzip.open(fn, 'r')
    else:
        f = open(fn, 'r')
    for ln in f:
        line = ln.decode('UTF-8')
        if line.startswith('*'):
            continue
        if not solutionBlock:
            if 'TROPO PARAMETER NAMES' in line:
                troParams = line.split()[3:]
                for p in range(len(troParams)):
                    if 'STDEV' in troParams[p]:
                        troParams[p] = troParams[p-1]+'STDEV'
            elif 'TROPO PARAMETER UNITS' in line:
                troUnits = line.split()[3:]
            elif '+TROP/SOLUTION' in line:
                solutionBlock = True
        elif '-TROP/SOLUTION' in line:
            break
        else:
            cols = line.split()
            e = cols[1]
            yy = e[:2]
            doy = e[3:6]
            sec = e[7:12]

            [hh, mm, ss] = str(timedelta(seconds=int(sec))).split(':')
            epoch = calendar.timegm(time.strptime(' '.join(
                [yy, doy, hh, mm, ss]), "%y %j %H %M %S"))-calendar.timegm(
                  time.strptime("2000 01 01 00 00", "%Y %m %d %H %M"))

            if cols[0] not in trop:
                trop[cols[0]] = {}
            trop[cols[0]][epoch] = {}
            for field in range(len(troParams)):
                candidate = float(cols[field+2])
                if candidate > -99.9:
                    trop[cols[0]][epoch][troParams[field]] = float(
                        cols[field+2])/float(troUnits[field])
    return (trop)


parser = argparse.ArgumentParser(description='Parses sites data and insert into MGViz tables.')
parser.add_argument(
    '--nopass',
    dest='nopass',
    default=False,
    action='store_true',
    help='Do use a password')
parser.add_argument(
    '--i',
    dest='input_dir',
    default='../Troposphere',
    help='Input data for tropospheric data',
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
    ingest_tropo(args.input_dir, conn, int(args.limit))
finally:
    conn.close()
    print('Exiting')
