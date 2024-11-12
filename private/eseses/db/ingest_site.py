#!/usr/bin/env python3

import argparse
import urllib.request
import psycopg2
import getpass
import json

SITES_URL = "http://localhost:8888/api/eseses/psite"


def get_sites(sites_url):
    print('Retrieving', sites_url)
    with urllib.request.urlopen(sites_url) as url:
        data = json.load(url)
        return data


def ingest_sites(sites, conn, limit):
    cur = conn.cursor()
    total = 0
    for idx, site in enumerate(sites['features']):
        if limit == idx:
            break
        total = idx
        id = site['properties']['site']
        x = site['properties']['x']
        y = site['properties']['y']
        sql = '''
        INSERT INTO site (id, x, y)
        VALUES ('%s', %f, %f)
        ON CONFLICT (id) DO UPDATE
        SET x = excluded.x,
            y = excluded.y;
        ''' % (id, x, y)
        cur.execute(sql)
        conn.commit()
    print('Inserted %i sites' % total)


parser = argparse.ArgumentParser(description='Parses sites data and insert into MGViz tables.')
parser.add_argument(
    '--nopass',
    dest='nopass',
    default=False,
    action='store_true',
    help='Do use a password')
parser.add_argument(
    '--sites_url',
    dest='sites_url',
    default=SITES_URL,
    help='URL to obtain site data',
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

# Download data    
sites = get_sites(args.sites_url)

# Connect to database
conn_string = str('host=%s dbname=%s user=%s port=%s password=%s' % (args.host,
                                                                     args.dbname,
                                                                     args.user,
                                                                     args.port,
                                                                     password))
conn = psycopg2.connect(conn_string)

# Parse data and insert into the database
try:
    ingest_sites(sites, conn, int(args.limit))
finally:
    conn.close()
    print('Exiting')
