import pandas as pd
from radios import RadioBrowser
import asyncio
import sys
import re
import os
import argparse
from passwd_data import *
parser = argparse.ArgumentParser(description='Favorite radio stations!')

parser.add_argument('--radiourl', help="URL belonging to new favorite station", type=str, default=None)
input_args = parser.parse_args()
radiourl = input_args.radiourl
if radiourl is None:
    print('No Radio url found :(')

here = sys.path[0]
async def add_fave():
    async with RadioBrowser(user_agent="MyAwesomeApp/1.0.0") as radios:
        print('Building radio database from all over the world!')
        stations = await radios.stations()

    station_dict = [i.__dict__ for i in stations]
    for i in reversed(range(len(station_dict))):
        stationurl = station_dict[i]['url']
        if stationurl == radiourl:
            print("Found Radio Station!")
            try:
                station_dict[i]['friendly_name'] = re.sub('[^a-zA-Z0-9 \n\.]', '', station_dict[i]['name'])
                station_dict[i]['country'] = re.sub('[^a-zA-Z0-9 \n\.]', '', station_dict[i]['country'])
            except:
                print("Could not set friendly names: ")
                try:
                    print(station_dict[i]['friendly_name'])
                    print(station_dict[i]['friendly_name'])
                except:
                    pass
            new_favorite = pd.DataFrame.from_records(station_dict)

            try:
                favorite_stations = pd.read_pickle(here  + "favorites.pickle")
                favs = pd.concat([new_favorite, favorite_stations])
                favs.drop_duplicates()
            except:
                print("No favorites found, building new database!")
                favs = new_favorite
            favs.to_pickle(here + "favorites.pickle")
            return
    print("Could not find radio url " + radiourl)
    sys.exit(4)


if __name__ == "__main__":
    asyncio.run(add_fave())