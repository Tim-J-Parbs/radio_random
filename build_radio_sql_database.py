from radios import RadioBrowser
import asyncio
import sys
import re
import os
import numpy as np
from tqdm import tqdm
import sqlite3 as sql
if 'win32' in sys.platform:
    # Windows specific event-loop policy & cmd
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

here = sys.path[0]
allowed_codecs = ['MP3', 'AAC+', 'AAC', 'OGG']#, 'UNKOWN']


async def async_build():
    debug = True
    if debug: print('Connecting to database.')
    conn = sql.connect('radios.db')
    cursor = conn.cursor()
    if debug: print('Connected.')

    cursor.execute('DROP TABLE IF EXISTS radiosites')
    cursor.execute('''
        CREATE TABLE radiosites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            country TEXT,
            popularity BIGINT,
            codec TEXT
        )
    ''')
    conn.commit()
    if debug: print('Created necessary table.')
    """Build a local copy of the RadioBrowser database"""

    assert(os.access(here, os.W_OK), 'Unable to write to ' + here + ', please check permissions')
    if debug: print('Connecting to Radio database.')
    async with RadioBrowser(user_agent="random_radio/1.0.0") as radios:
        print('Building radio database from all over the world!')
        countries = await radios.countries()
        stations = await radios.stations()
        if debug: print(f'Got {len(stations)} stations.')
        # For each country, build a dictionary of stations, fix broken name strings and remove known bad codecs
        station_dict = [i.__dict__ for i in stations]
        for i in tqdm(range(len(station_dict))):
            stationcodecs = station_dict[i]['codec'].split(',')
            if any(j in stationcodecs for j in allowed_codecs):
                friendly_name = re.sub('[^a-zA-Z0-9 ]', '', station_dict[i]['name'])
                thiscountry = next((item.name for item in countries if item.code == station_dict[i]['country_code']), 'Unknown')
                cleancountry = re.sub('[^a-zA-Z0-9 ]', '', thiscountry)
                popularity = station_dict[i]['click_count']
                url = station_dict[i]['url']
                codec = station_dict[i]['codec']
                cursor.execute('''
                        INSERT INTO radiosites (name, url, country, popularity, codec)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (friendly_name, url, cleancountry, popularity, codec))
                conn.commit()
            else:
                print('Removed {} with codec(s) {}.'.format( station_dict[i]['name'], station_dict[i]['codec']))


        cursor.execute('SELECT COUNT(DISTINCT url) FROM radiosites')
        unique_websites_count = cursor.fetchone()[0]


        cursor.execute('SELECT DISTINCT country FROM radiosites')
        unique_countries = cursor.fetchall()
        print(f'Got {unique_websites_count} stations from {len(unique_countries)} in here!')
        conn.close()
        return

def build():

    asyncio.run(async_build())
    return

if __name__ == "__main__":
    build()