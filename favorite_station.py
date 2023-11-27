import pandas as pd
from radios import RadioBrowser
import asyncio
import sys
import re
import os
import argparse
from passwd_data import *
parser = argparse.ArgumentParser(description='Favorite radio stations!')

parser.add_argument('--radiourl', help="URL belonging to  (new) favorite station", type=str, default=None)
parser.add_argument('--database', help="Which dataset should be used? (def: 'favorites')", type=str, default="favorites")
parser.add_argument('-r', '--remove', action='store_true', help="Remove the URL from the database")
parser.add_argument('-l', '--list', action='store_true', help="List Database")
parser.add_argument('-a', '--add', action='store_true',help="Add the URL to the database")

parser.add_argument('--db', help="Debug", type=int, default=0)

input_args = parser.parse_args()
radiourl = input_args.radiourl
db = input_args.db
remove = input_args.remove
list = input_args.list
add = input_args.add

database = input_args.database


checksum = sum([int(i) for i in [remove, add, list]])
assert(checksum <= 1, "Conflicting options when calling radio_random")
if checksum == 0:
    list = True





here = sys.path[0]

def rm_fave():
    try:
        favorite_stations = pd.read_pickle(here + "/" + database + ".pickle")
        print("Stored list " + database + " found, opened database!")
    except:
        print("Stored list " + database + " not found!")
        return
    favs = favorite_stations.drop(favorite_stations[favorite_stations['url'] == radiourl].index)
    favs = favs.reset_index(drop=True)
    favs.to_pickle(here + "/"  + database + ".pickle")
    print("Succesfully removed station!")
    return

def list_fave():
    try:
        favorite_stations = pd.read_pickle(here + "/" + database + ".pickle")
        print("Stored list " + database + " found, opened database!")
    except:
        print("Stored list " + database + " not found!")
        return
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(favorite_stations)
    return


async def add_fave():
    # Not TOO happy with this, and a strong cause for a shift to SQL. While RadioBrowser can filter for URLs, this seems
    # to be broken here
    async with RadioBrowser(user_agent="random_radios/1.0.0") as radios:
        stations = await radios.stations()
        countries = await radios.countries()

    station_dict = [i.__dict__ for i in stations]
    for i in reversed(range(len(station_dict))):
        stationurl = station_dict[i]['url']
        if stationurl == radiourl:
            print("Found Radio Station!")
            try:
                station_dict[i]['friendly_name'] = re.sub('[^a-zA-Z0-9 \n\.]', '', station_dict[i]['name'])
                thiscountry = next((item.name for item in countries if item.code == station_dict[i]['country_code']),
                                   'Unknown')
                station_dict[i]['country'] = re.sub('[^a-zA-Z0-9 \n\.]', '', thiscountry)
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

            new_favorite = pd.DataFrame.from_dict(station_dict[i], 'index').T
            try:
                favorite_stations = pd.read_pickle(here  + "/" + database + ".pickle")
                print("Stored list " + database + " found, opened database!")
            except Exception as e:
                print(e)
                print("Stored list " + database + " not found, building new database.")
                favorite_stations = new_favorite
            favs = pd.concat([new_favorite, favorite_stations])
            print("Concatenated databases.!")
            favs = favs.drop_duplicates(subset=['url'])
            favs = favs.reset_index(drop=True)
            favs.to_pickle(here + "/" + database + ".pickle")
            return
    print("Could not find radio url " + radiourl)
    sys.exit(4)


if __name__ == "__main__":
    if remove:
        if radiourl is None:
            print('No Radio url found :(')
            sys.exit(4)
        rm_fave()
    elif add:
        if radiourl is None:
            print('No Radio url found :(')
            sys.exit(4)
        asyncio.run(add_fave())
    else:
        list_fave()