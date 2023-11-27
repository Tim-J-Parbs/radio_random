from radios import RadioBrowser
import pandas
import asyncio
import sys
import re
import os
import numpy as np
if 'win32' in sys.platform:
    # Windows specific event-loop policy & cmd
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

here = sys.path[0]
dir_suffix = 'countries'
folderpath = here + '/' + dir_suffix
allowed_codecs = ['MP3', 'AAC+', 'AAC', 'OGG']#, 'UNKOWN']
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
        for i in reversed(range(len(station_dict))):
            stationcodecs = station_dict[i]['codec'].split(',')
            if any(j in stationcodecs for j in allowed_codecs):
                station_dict[i]['friendly_name'] = re.sub('[^a-zA-Z0-9 \n\.]', '', station_dict[i]['name'])
                thiscountry = next((item.name for item in countries if item.code == station_dict[i]['country_code']), 'Unknown')
                station_dict[i]['country'] = re.sub('[^a-zA-Z0-9 \n\.]', '', thiscountry)
            else:
                tmp = station_dict.pop(i)
                print('Removed {} with codec(s) {}.'.format(tmp['name'], tmp['codec']))

        df = pandas.DataFrame.from_records(station_dict)
        print('Got {} stations in here!'.format(len(df)))
        df['logpop'] = df['click_count'].apply(np.log)
        unique_countries = df['country'].unique().tolist()
        for thiscountry in unique_countries:
            associated_stations = df[df['country'] == thiscountry].copy()
            print("Created station dataframe for {} with {} recorded stations!".format(thiscountry, len(associated_stations)))
            associated_stations.to_pickle(folderpath + '/' + re.sub('[^a-zA-Z0-9]', '', thiscountry) + '.pickle')

        return

def build():
    asyncio.run(async_build())
    return

if __name__ == "__main__":
    build()