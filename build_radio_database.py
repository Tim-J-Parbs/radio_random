from radios import FilterBy, Order, RadioBrowser
import numpy
import random
import pandas
import asyncio
import requests
import sys
import re
import argparse

if 'win32' in sys.platform:
    # Windows specific event-loop policy & cmd
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

dontsend = True
URL = 'http://localhost:8123'
PASSWORD = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJkZTMwNWI0YmVhNmM0N2Q4YjMxMzYyOTBmNTlhNDVhNyIsImlhdCI6MTY2MDYwNDI5OSwiZXhwIjoxOTc1OTY0Mjk5fQ.3mImhLhrzY42BN2iyJoq4JSabRpYWyfU2T7g70L7eyg'

SET_STATE = '{}/api/states/{{}}'.format(URL)
HEADERS = {
    'Authorization': PASSWORD,
    'content-type': 'application/json'}
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

        print("Created station dataframe with {} recorded stations!".format(len(df)))
        df.to_pickle('./radiostore.pickle')
        return df

def build():
    df = asyncio.run(async_build())
    return df

if __name__ == "__main__":
    asyncio.run(async_build())