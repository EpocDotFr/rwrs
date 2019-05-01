# Running With Rifles Stats (RWRS)

<img src="static/images/icon_round_dark_256.png" style="max-width: 150px" align="right">

Players statistics, servers list and more for the [Running With Rifles](http://www.runningwithrifles.com/wp/) (RWR) game
and its Pacific DLC. Available at [rwrstats.com](https://rwrstats.com/).

> Your everyday RWR companion tool!

## Prerequisites

  - Should work on any Python 3.x version. Feel free to test with another Python version and give me feedback
  - A modern web browser (which optionally support localStorage)
  - A MySQL-compatible DBMS (MySQL, MariaDB, Percona, etc)
  - (Optional, but recommended) A [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/)-capable web server
  - (Optional) Running With Rifles, if you need to extract data by using the commands below

## Installation

  1. Clone this repo somewhere
  2. Copy `.env.local` to `.env`
  3. `pip install -r requirements-dev.txt`
  4. `flask db upgrade`
  5. `bash scripts/geolite2_city_updater.sh`

## Configuration

Copy the `config.example.py` file to `config.py` and fill in the configuration parameters.

Available configuration parameters are:

  - `SECRET_KEY` Set this to a complex random value
  - `SERVER_NAME` The IP or hostname where RWRS will be available

More informations on the three above can be found [here](http://flask.pocoo.org/docs/1.0/config/#builtin-configuration-values).

  - `DB_USERNAME` Username to access the DBMS
  - `DB_PASSWORD` Password to access the DBMS
  - `DB_UNIX_SOCKET` If set, `DB_HOST` and `DB_PORT` will be ignored in favor of using this Unix socket to communicate with the DBMS
  - `DB_HOST` Host of the DBMS
  - `DB_PORT` Port of the DBMS
  - `DB_NAME` Name of the database to use
  - `GAUGES_SITE_ID` A [Gauges](https://gaug.es/) site ID used to track visits on RWRS (optional)
  - `BUGSNAG_API_KEY` A [Bugsnag](https://www.bugsnag.com/) API key so that unhandled exceptions are automatically sent to Bugsnag in production env (optional)
  - `CACHE_THRESHOLD` The maximum number of items the cache will store before it starts deleting some (see [here](https://pythonhosted.org/Flask-Cache/#configuring-flask-cache) for more configuration parameters related to Flask-Cache)
  - `SERVERS_CACHE_TIMEOUT` Cache duration of the servers list (in seconds)
  - `PLAYERS_CACHE_TIMEOUT` Cache duration of the players list as well as data for a single player (in seconds)
  - `GRAPHS_DATA_CACHE_TIMEOUT` Cache duration of the graphs data, both the players and the servers ones (in seconds)
  - `STEAM_PLAYERS_CACHE_TIMEOUT` Cache duration of the total number of players (in seconds)
  - `STEAM_API_KEY` A [Steam API](https://steamcommunity.com/dev) key
  - `PACIFIC_PLAYERS_RANKS_COUNTRY` Ranks image / name to show for the Pacific players stats (`us`, `jp`)
  - `MY_DISCORD_ID` My Discord user ID (snowflake)
  - `DISCORD_BOT_TOKEN` Authentication token used by the RWRS Discord bot
  - `DISCORD_BOT_CHANNEL_ID` The Discord channel ID the bot is allowed to talk in
  - `DISCORD_BOT_ADMINS` A list of Discord user IDs (snowflakes) allowed to use hidden bot commands
  - `DISCORD_BOT_GUILD_ID` A Discord guild (server) ID the bot will be allowed to listen for commands from
  - `MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR` How many players should RWRS track the stats for (top players storted by XP)
  - `ENABLE_SIGN_IN` Enable the "Sign in via Steam" feature
  - `ENABLE_PLAYER_CLAIMING` Enable the "claim player" feature
  - `PLAYER_CLAIM_DELAY` Maximum amount of minutes users are allowed to finalize an RWR account claim procedure

I'll let you search yourself about how to configure a web server along uWSGI.

## Usage

  - Standalone

Run the internal web server, which will be accessible at `http://localhost:8080`:

```
flask run
```

Edit this file and change the interface/port as needed.

  - uWSGI

The uWSGI file you'll have to set in your uWSGI configuration is `uwsgi.py`. The callable is `app`.

  - Others

You'll probably have to hack with this application to make it work with one of the solutions described
[here](http://flask.pocoo.org/docs/1.0/deploying/). Send me a pull request if you make it work.

### Extracting ranks data and images

The Flask command `flask extract-ranks` is used to extract and save all ranks data to a JSON file located at `storage/data/ranks.json`.
It also retrieve, process (the actual images content isn't centered) and save all the RWR ranks images. They are saved
at `static/images/ranks/{country}/{rank ID}.png` and `static/images/ranks/{country}/{rank ID}_icon.png`.

  1. `pip install -r requirements-dev.txt`
  2. `flask extract-ranks --steamdir="{path to the Steam root directory}"`

This command requires the game to be installed.

### Extracting maps data

The Flask command `flask extract-maps-data` is used to extract and save all maps data to a JSON file located at `storage/data/maps.json`.

```
flask extract-maps-data --steamdir="{path to the Steam root directory}"
```

This command requires the game to be installed.

### Extracting minimaps

The Flask command `flask extract-minimaps` is used to extract minimaps (the ones displayed when pressing on
<kbd>TAB</kbd>). They are saved at `static/images/maps/minimap/{map ID}.png` and `static/images/maps/minimap/{map ID}_thumb.png`.

  1. `pip install -r requirements-dev.txt`
  2. `flask extract-minimaps --steamdir="{path to the Steam root directory}"`

This command requires the game to be installed.

### Clearing cache

```
flask cc
```

### Clearing old graphs data

Data older than one week old will be deleted.

```
flask clean-players-count
```

### Computing promotions for all players

```
flask compute-promotions
```

### Storing actual number of players (for graphs)

Will save the current number of Steam players which have RWR running, and the current number of players playing online.

```
flask get-players-count
```

### Migrating the database

```
flask db upgrade
```

### Running the RWRS Discord bot

```
flask run-discord-bot
```

### Updating the MaxMind GeoLite2 City database

More information in the script comments.

```
bash scripts/geolite2_city_updater.sh
```

### Updating RWRS

More information in the script comments.

```
bash scripts/rwrs_updater.sh [TYPE, default=fast, fast|full]
```

### Generating RWRS REST API documentation

More information in the script comments.

```
bash scripts/api_doc_generator.sh
```

### Retrieve and save the players stats in DB

```
flask save-players-stats [--reset]
```

### Retrieve and save the ranked servers admins

```
flask save-ranked-servers-admins
```

### Import rwrtrack data

```
flask import-rwrtrack-data --directory="{path to the rwrtrack data directory}" [--reset]
```

## Credits

You'll find credits and legal mentions [here](https://rwrstats.com/about#credits).

## Feedback

If you have suggestions or problems you can submit an issue [here on GitHub](https://github.com/EpocDotFr/rwrs/issues) or
head over [here](https://rwrstats.com/feedback).