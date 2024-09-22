import random
import pandas
import requests
import sys
import re
import os
import argparse
import numpy as np
from passwd_data import *
import sqlite3 as sql
import build_radio_sql_database
import paho.mqtt.client as mqtt


conn = sql.connect('radios.db')
cursor = conn.cursor()

def get_global_station():
    def get_random_country():
        cursor.execute('SELECT DISTINCT country FROM radiosites')
        unique_countries = cursor.fetchall()
        thiscountry = random.choice(unique_countries)
        return thiscountry
    try:
        chosen_country = get_random_country()
        if len(chosen_country) == 0:
            print("No country here. ")
            raise
    except: #Should only happen if the database has not been built
        print('Database not found.')
        build_radio_sql_database.build()
        chosen_country = get_random_country()

    cursor.execute('SELECT name, url, country, popularity FROM radiosites WHERE country=(?)', (chosen_country))
    radios = cursor.fetchall()

    # Step 2: Calculate the total sum of click counts
    total_log_clicks = sum(np.log(radio[3] + 1) for radio in radios)
    random_click_sum = random.uniform(0, total_log_clicks)

    cumulative_sum = 0
    selected_radio = None

    for radio in radios:
        cumulative_sum += np.log(radio[3] + 1)  # Use the logarithm of the click count
        if random_click_sum <= cumulative_sum:
            selected_radio = radio
            break
    this_radio_dict = {'name':selected_radio[0], 'url':selected_radio[1], 'country':selected_radio[2]}
    return this_radio_dict

class radio_backend():
    def __init__(self):
        # MQTT Settings
        self.MQTT_BROKER = MQTT_IP
        self.MQTT_PORT = MQTT_PORT
        self.MQTT_REQUEST_TOPIC = "home-assistant/radio/radio_request"
        self.MQTT_URL_TOPIC = "home-assistant/radio/radio_url"
        self.MQTT_NAME_TOPIC = "home-assistant/radio/radio_name"
        self.MQTT_COUNTRY_TOPIC = "home-assistant/radio/radio_country"
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_message = self.on_message
        # Connect to the MQTT broker
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.subscribe(self.MQTT_REQUEST_TOPIC)
        self.client.loop_start()
    def on_message(self, client, userdata, message):
        # Decode the incoming message
        payload = message.payload.decode("utf-8").split(',')
        command = payload[0]
        database = payload[1]
        if command == 'request':

            # Message is really simple - only the name of a favorites list or 'global' to sample from all available
            # stations

            this_radio = get_global_station()

            print("Chosen station {} and url {} from {}".format(this_radio['name'], this_radio['url'], this_radio['country']))
            newname = re.sub('[^a-zA-Z0-9 \n\.]', '', this_radio['name'])

            self.client.publish(self.MQTT_NAME_TOPIC , newname)
            self.client.publish(self.MQTT_URL_TOPIC,  this_radio['url'])
            self.client.publish(self.MQTT_COUNTRY_TOPIC, this_radio['country'])
        elif command == 'add':
            print('soon')
        elif command == 'remove':
            print('soon')
def main() -> None:
    radio = radio_backend()
    return

if __name__ == "__main__":
    main()