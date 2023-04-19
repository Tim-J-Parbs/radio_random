# radio_random
Random Radio stations! This little python program publishes pseudo-randomly selected radio URLs from a global webradio database to a REST api.
Originally built for home assistant, and publishes to the endpoints

`http://localhost:8123/api/states/input_text.radiourl` --> URL for selected station

`http://localhost:8123/api/states/input_text.radiocountry` --> Its country

`http://localhost:8123/api/states/input_text.radioname` --> The stations name

Those point to `input_text` objects inside homeassistant. The URL can then be used in a media player inside homeassistant (or just published to mopidy) to play the station.

Right now, the program uses pandas for its database, which I will change in the future to support a SQL database, which is probably much nicer. I could also allow more flexibility in choosing API options, or wrap the whole thing in a homeassistant integration.

The program comes in three parts: 
# Build the database
Because accessing the online database takes time (and bandwith), we build a local copy to a subfolder `./countries` using `pandas`. Takes around 17MB of space.

## Example call:
### `python3 build_radio_database.py`
Builds (or updates) the database. It might be a good idea to run this from time to time (via cron for example) to keep the database up to date.
The database is saved in a subfolder `./countries`, in which stations are grouped by their originating country, each with its own file.

# Define favorite lists
By default, a random station from around the world will be chosen. Optionally, you can define custom lists of stations.
`favorite_station.py` : used to define and update databases of favorite radio stations. 

## Example calls
### `python3 favorite_station.py --radiourl 'http://www.gabberworld.io/gabber.mp4' --database 'Gabber'`
Inserts the URL 'http://www.gabberworld.io/gabber.mp4' into a database called 'Gabber', creating the database if it not already exists.

### `python3 favorite_station.py --radiourl 'http://www.gabberworld.io/gabber.mp4' --database 'Gabber' --remove 1`
Removes the URL 'http://www.gabberworld.io/gabber.mp4' from the database called 'Gabber'.

# Get your radio station
The heart of this operation: `random_radio.py` sets a random radio station to your REST API.
## Example calls
### `python3 random_radio.py` 
Posts a random station from a random country radio database found in './countries' to the REST API endpoints specified above. Runs build_radio_database.py  if no database is found.
If using the global database, the random selection is weighted by the log10 of the popularity of the station (measured by its clicks), favoring more popular stations.
(Also outputs to console right now, but this is bound to change.)

### `python3 random_radio.py --favorites 'True' --database 'Gabber'`
Posts a random station from the database called 'Gabber', which can be created using favorite_station.py. When pulling from a favorites database, the station is chosen without the log10 weighting of the global pull.
If no such database is found, choose a station from the global database.

### `python3 random_radio.py --ent_url 'this' --ent_country 'those' --ent_name 'these'`
Publishes a random radio station, overriding the default endpoints. This call would publish the URL to 'http://localhost:8123/api/states/this', for example.


To function correctly, a valid REST API Bearer Token has to be supplied in the provided passwd_data.py. Just replace the '...' with your token.
