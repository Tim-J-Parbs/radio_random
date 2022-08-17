import numpy as np
import random
import pandas
import requests
import sys
import re
import os
import argparse
import build_radio_database
parser = argparse.ArgumentParser(description='Random radio stations!')

parser.add_argument('--ent_url', help="Homeassistant entity for radio URL", type=str, default='input_text.radiourl')
parser.add_argument('--ent_country', help="Homeassistant entity for radio URL", type=str, default='input_text.radiocountry')
parser.add_argument('--ent_name', help="Homeassistant entity for radio URL", type=str, default='input_text.radioname')
input_args = parser.parse_args()


dontsend = False
URL = 'http://localhost:8123'
PASSWORD = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJkZTMwNWI0YmVhNmM0N2Q4YjMxMzYyOTBmNTlhNDVhNyIsImlhdCI6MTY2MDYwNDI5OSwiZXhwIjoxOTc1OTY0Mjk5fQ.3mImhLhrzY42BN2iyJoq4JSabRpYWyfU2T7g70L7eyg'

SET_STATE = '{}/api/states/{{}}'.format(URL)
HEADERS = {
    'Authorization': PASSWORD,
    'content-type': 'application/json'}
debug = True

entities = [input_args.ent_url, input_args.ent_country, input_args.ent_name]
here = sys.path[0]
def main() -> None:

    try:
        thisfile = random.choice(os.listdir(here + "/countries/"))  # change dir name to whatever
        associated_stations = pandas.read_pickle('./countries/' + thisfile)
    except:
        print('Database not found.')
        build_radio_database.build()
        thisfile = random.choice(os.listdir(here + "/countries/"))  # change dir name to whatever
        associated_stations = pandas.read_pickle('./countries/' + thisfile)

    this_radio = associated_stations.sample(n=1, weights="logpop").iloc[0]
    print("Chosen station {} and url {} from {}".format(this_radio['name'],this_radio['url'],this_radio['country']))
    newname = re.sub('[^a-zA-Z0-9 \n\.]', '', this_radio['name'])
    data_bits = [ this_radio['url'], this_radio['country'], newname]
    try:
        for chunk, ent in zip(data_bits, entities):
            data = '{{"state": "{}"}}'.format(chunk)
            if debug:
                print('posting ' + data + ' to ' + ent)
            try:
                if not dontsend:
                    requests.post(SET_STATE.format(ent), data=data, headers=HEADERS)
            except:
                print(SET_STATE.format(ent))
                print('Writing state ' + chunk + ' to HA entitiy ' + ent + ' failed')

                sys.exit(4)
    except:
        print('Iterating over data failed.', file=sys.stderr)
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()