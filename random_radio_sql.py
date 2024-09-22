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

# prepare database
def table_exists(cursor, table_name):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None
def table_is_empty(cursor, table_name):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    return count == 0

if (not table_exists(cursor, 'radiosites') or table_is_empty(cursor, 'radiosites')):
    build_radio_sql_database.build()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS radio_favorites (
        radio_id INTEGER,
        fave_id INTEGER,
        FOREIGN KEY (radio_id) REFERENCES radiosites(id),
        FOREIGN KEY (fave_id) REFERENCES favorites(id),
        PRIMARY KEY (radio_id, fave_id)
    )
''')
conn.commit()

def get_radio_id(url):
    cursor.execute('SELECT id FROM radiosites WHERE url = ?', (url,))
    radio_result = cursor.fetchone()
    if radio_result is None:
        print(f"Radio '{url}' does not exist.")
        return None
    return radio_result[0]

def get_favorites_id(fave_name):
    cursor.execute('SELECT id FROM favorites WHERE name = ?', (fave_name,))
    fave_result = cursor.fetchone()
    if fave_result is None:
        print(f"Fave list '{fave_name}' does not exist.")
        return None
    return fave_result[0]

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

    cursor.execute('SELECT friendly_name, url, country, popularity FROM radiosites WHERE country=(?)', (chosen_country))
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

def get_favorite_station(favorite_database):
    cursor.execute('''
        SELECT r.name, r.url, r.country
        FROM radiosites r
        JOIN radio_favorites rf ON r.id = rf.radio_id
        JOIN favorites f ON rf.category_id = f.id
        WHERE f.name = ?
    ''', (favorite_database,))
    favorite_radios = cursor.fetchall()
    if favorite_radios is None: return None
    this_radio = random.choice(favorite_radios)
    this_radio_dict = {'name': this_radio[0], 'url': this_radio[1], 'country': this_radio[2]}
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
        self.client.loop_forever()
        self.debug = True
    def on_message(self, client, userdata, message):
        # Decode the incoming message
        payload = message.payload.decode("utf-8").split(',')
        command = payload[0]
        database = payload[1]
        if command == 'request':

            # Message is really simple - only the name of a favorites list or 'global' to sample from all available
            # stations
            this_radio = None
            if database != 'global':
                this_radio = get_favorite_station(database)

            if database == 'global' or this_radio is None:
                this_radio = get_global_station()

            print("Chosen station {} and url {} from {}".format(this_radio['name'], this_radio['url'], this_radio['country']))
            newname = re.sub('[^a-zA-Z0-9 ]', '', this_radio['name'])

            self.client.publish(self.MQTT_NAME_TOPIC , newname)
            self.client.publish(self.MQTT_URL_TOPIC,  this_radio['url'])
            self.client.publish(self.MQTT_COUNTRY_TOPIC, this_radio['country'])
        elif command == 'add':
            # TODO: ERROR HANDLING

            url = payload[2]
            if self.debug: print(f"Adding {url} to {database}")
            cursor.execute('SELECT id FROM favorites WHERE name = ?', (database,))
            result = cursor.fetchone()
            if result is None:
                print(f'Creating category {database}...')
                cursor.execute('''
                            INSERT INTO favorites (name)
                            VALUES (?)
                        ''', (database,))

            radio_id = get_radio_id(url)
            fave_id = get_favorites_id(database)
            cursor.execute('''
                INSERT INTO radio_favorites (radio_id, fave_id)
                VALUES (?, ?)
            ''', (radio_id, fave_id))
            conn.commit()

        elif command == 'remove':
            # Get the radio ID
            url = payload[2]
            radio_id = get_radio_id(url)
            if radio_id is None: return

            # Get the category ID
            fave_id = get_favorites_id(database)
            if fave_id is None: return


            # Delete the association from the website_categories table
            cursor.execute('''
                    DELETE FROM radio_favorites
                    WHERE radio_id = ? AND fave_id = ?
                ''', (radio_id, fave_id))

            # Commit the change
            conn.commit()
            print(f"Association between radio '{url}' and category '{database}' has been removed.")
def main() -> None:
    radio = radio_backend()
    return

if __name__ == "__main__":
    main()