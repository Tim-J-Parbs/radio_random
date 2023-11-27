import random
import pandas
import requests
import sys
import re
import os
import argparse
from passwd_data import *
import build_radio_database
parser = argparse.ArgumentParser(description='Random radio stations!')


parser.add_argument('--ent_url', help="Homeassistant entity for radio URL", type=str, default='input_text.radiourl')
parser.add_argument('--ent_country', help="Homeassistant entity for radio URL", type=str, default='input_text.radiocountry')
parser.add_argument('--ent_name', help="Homeassistant entity for radio URL", type=str, default='input_text.radioname')
parser.add_argument('--favorites', help="Pull from favorites? def: False",  default=False, type=lambda x: (str(x).lower() == 'true'))
parser.add_argument('--database', help="Which dataset should be used for favorites? (def: 'favorites')", type=str, default="favorites")
parser.add_argument('--verbosity', help="Print output and information to console?def: False",  default=False, type=lambda x: (str(x).lower() == 'true'))
input_args = parser.parse_args()



MACHINE_URL = 'http://localhost:8123'

SET_STATE = '{}/api/states/{{}}'.format(MACHINE_URL)
HEADERS = {
    'Authorization': PASSWORD,
    'content-type': 'application/json'}
debug = True

entities = [input_args.ent_url, input_args.ent_country, input_args.ent_name]
getfavorites = input_args.favorites
database = input_args.database
verbosity = input_args.verbosity
def vprint(msg):
    if verbosity:
        print(msg)

here = sys.path[0]
def get_global_station(here):
    def get_random_country():
        thisfile = random.choice(os.listdir(here + "/countries/"))
        return pandas.read_pickle(here + '/countries/' + thisfile)
    try:
        associated_stations = get_random_country()
    except: #Should only happen if the database has not been built
        print('Database not found.')
        build_radio_database.build()
        associated_stations = get_random_country()
    this_radio = associated_stations.sample(n=1, weights="logpop").iloc[0]
    return this_radio

def main() -> None:
    if getfavorites:
        print('Choosing from good? stations')
        try:
            associated_stations = pandas.read_pickle(here + '/' + database + '.pickle')
            this_radio = associated_stations.sample(n=1).iloc[0]
        except:
            print('Cant load from ' + database + '.pickle. Just getting something else.')
            this_radio = get_global_station(here)
    else:
        this_radio = get_global_station(here)
    print("Chosen station {} and url {} from {}".format(this_radio['name'],this_radio['url'],this_radio['country']))
    newname = re.sub('[^a-zA-Z0-9 \n\.]', '', this_radio['name'])
    data_bits = [ this_radio['url'], this_radio['country'], newname]
    try:
        for chunk, ent in zip(data_bits, entities):
            data = '{{"state": "{}"}}'.format(chunk)
            if debug:
                print('posting ' + data + ' to ' + ent)
            try:
                requests.post(SET_STATE.format(ent), data=data, headers=HEADERS)
            except:
                print('Writing state ' + chunk + ' to HA entitiy ' + ent + ' failed')
                sys.exit(4)
    except:
        print('Iterating over data failed.', file=sys.stderr)
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()