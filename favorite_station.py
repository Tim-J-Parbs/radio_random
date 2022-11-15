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
parser.add_argument('--db', help="Debug", type=int, default=0)
input_args = parser.parse_args()
radiourl = input_args.radiourl
db = input_args.db

if radiourl is None:
    print('No Radio url found :(')
    sys.exit(4)

here = sys.path[0]
async def add_fave():
    async with RadioBrowser(user_agent="MyAwesomeApp/1.0.0") as radios:
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
                    print(station_dict[i]['country'])
                except Exception as e:
                    print(e)
                    pass

            for key, value in station_dict[i].items():
                if isinstance(value, list):
                    station_dict[i][key] = tuple(value)
            if db:
                for key, value in station_dict[i].items():
                    print('Key: ' + key)
                    print('Value type: ' + str(type(value)))
                    try:
                        print(value)
                    except:
                        print('Could not print value')
                    print('-----------------------')

            new_favorite = pd.DataFrame.from_dict(station_dict[i])
            try:
                favorite_stations = pd.read_pickle(here  + "/favorites.pickle")
                print("Favorites found, opened database!")
            except Exception as e:
                print(e)
                print("No favorites found, building new database!")
                favorite_stations = new_favorite
            favs = pd.concat([new_favorite, favorite_stations])
            print("Concatenated databases.!")
            favs.drop_duplicates()
            favs.to_pickle(here + "favorites.pickle")
            return
    print("Could not find radio url " + radiourl)
    sys.exit(4)


if __name__ == "__main__":
    asyncio.run(add_fave())