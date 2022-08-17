from radios import FilterBy, Order, RadioBrowser
import pandas
import asyncio
import sys
import re
import argparse
import numpy as np
if 'win32' in sys.platform:
    # Windows specific event-loop policy & cmd
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

dontsend = True

debug = True

allowed_codecs = ['MP3', 'AAC+', 'AAC']
async def async_build():
    """Show example on how to query the Radio Browser API."""
    async with RadioBrowser(user_agent="MyAwesomeApp/1.0.0") as radios:
        print('Building radio database from all over the world!')
        countries = await radios.countries()

        stations = await radios.stations()
        station_dict = [i.__dict__ for i in stations]
        for i in range(len(station_dict)):
            station_dict[i]['friendly_name'] = re.sub('[^a-zA-Z0-9 \n\.]', '', station_dict[i]['name'])
            thiscountry = next((item.name for item in countries if item.code == station_dict[i]['country_code']), 'Unknown')
            station_dict[i]['country'] = re.sub('[^a-zA-Z0-9 \n\.]', '', thiscountry)

        df = pandas.DataFrame.from_records(station_dict)
        df['logpop'] = df['click_count'].apply(np.log)
        unique_countries = df['country'].unique().tolist()
        for this_country in unique_countries:
            associated_stations = df[df['country'] == this_country].copy()
            print("Created station dataframe for {} with {} recorded stations!".format(this_country, len(associated_stations)))
            df.to_pickle('./countries/' + this_country + '.pickle')

        return

def build():
    asyncio.run(async_build())
    return

if __name__ == "__main__":
    asyncio.run(async_build())