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
dir_suffix = 'countries'
folderpath = here + '/' + dir_suffix
allowed_codecs = ['MP3', 'AAC+', 'AAC', 'OGG']#, 'UNKOWN']
conn = sql.connect('radios.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS radiosites')
cursor.execute('''
    CREATE TABLE radiosites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        friendly_name TEXT NOT NULL,
        url TEXT NOT NULL,
        country TEXT,
        popularity BIGINT,
        codec TEXT
    )
''')
conn.commit()

async def async_build():
    """Build a local copy of the RadioBrowser database"""
    try:
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
    except Exception as e:
        print('Unable to access or write to ' + folderpath)
        print('Please check write permission of current user to that folder')
    assert(os.access(folderpath, os.W_OK), 'Unable to write to ' + folderpath + ', please check permissions')

    async with RadioBrowser(user_agent="random_radio/1.0.0") as radios:
        print('Building radio database from all over the world!')
        countries = await radios.countries()
        stations = await radios.stations()
        # For each country, build a dictionary of stations, fix broken name strings and remove known bad codecs
        station_dict = [i.__dict__ for i in stations]
        for i in tqdm(range(len(station_dict))):
            stationcodecs = station_dict[i]['codec'].split(',')
            if any(j in stationcodecs for j in allowed_codecs):
                friendly_name = re.sub('[^a-zA-Z0-9 \n\.]', '', station_dict[i]['name'])
                thiscountry = next((item.name for item in countries if item.code == station_dict[i]['country_code']), 'Unknown')
                cleancountry = re.sub('[^a-zA-Z0-9 \n\.]', '', thiscountry)
                popularity = station_dict[i]['click_count']
                url = station_dict[i]['url']
                codec = station_dict[i]['codec']
                cursor.execute('''
                        INSERT INTO radiosites (friendly_name, url, country, popularity, codec)
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