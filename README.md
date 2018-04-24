# Running With Rifles Stats (RWRS)

<img src="static/images/icon_round_dark_256.png" style="max-width: 150px" align="right">

Players statistics, servers list and more for the [Running With Rifles](http://www.runningwithrifles.com/wp/) (RWR) game
and its Pacific DLC. Available at [rwrstats.com](https://rwrstats.com/).

## Features

  - Players
    - Support stats for both the official invasion (vanilla RWR) servers and official Pacific servers
    - Search for a player
    - View player stats (as well as next rank progression, unlocks, on which server he's playing on, etc)
    - Compare two players stats
    - Friends list (easily know on which server your friends are playing on. There's no need to create a user account or whatever)
    - Players list (leaderboard)
  - Public servers
    - Real servers location
    - Real maps name
    - Official invasion (ranked) servers are highlighted
    - Game mode (coop, PvPvE, etc) and type (vanilla RWR, Pacific DLC, etc)
    - Public server details (players list with link to their profile, current map preview and mapview, etc)
    - Filtering capabilities
  - Online servers count (+ the active ones)
  - Total players count (+ online ones + number of playing friends)
  - Charts (for the past week)
    - Number of online players
    - Number of online servers (+ the active ones)
    - Number of players on a server
  - Root RWR servers status (online multiplayer)
  - Discord bot able to give several kind of information. Available on the [RWR Discord Server](https://discord.gg/010ixMlfmhK5BhYOv). [Commands documentation](doc/discord_bot.md)
  - Maps gallery with details (spawn points, stashes, special crates, vehicles, etc)

## Prerequisites

  - Should work on any Python 3.x version. Feel free to test with another Python version and give me feedback
  - A modern web browser (which optionally support localStorage)
  - (Optional, but recommended) A [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/)-capable web server
  - (Optional) Running With Rifles, if you need to extract images

## Installation

  1. Clone this repo somewhere
  2. `pip install -r requirements.txt`
  3. `set FLASK_APP=rwrs.py`
  4. `flask db upgrade`

## Configuration

Copy the `config.example.py` file to `config.py` and fill in the configuration parameters.

Available configuration parameters are:

  - `SECRET_KEY` Set this to a complex random value
  - `DEBUG` Enable/disable debug mode
  - `SERVER_NAME` The IP or hostname where RWRS will be available

More informations on the three above can be found [here](http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values).

  - `BETA` Whether or not to enable the beta mode
  - `GAUGES_SITE_ID` A [Gauges](https://gaug.es/) site ID used to track visits on RWRS (optional)
  - `CACHE_THRESHOLD` The maximum number of items the cache will store before it starts deleting some (see [here](https://pythonhosted.org/Flask-Cache/#configuring-flask-cache) for more configuration parameters related to Flask-Cache)
  - `SERVERS_CACHE_TIMEOUT` Cache duration of the servers list (in seconds)
  - `PLAYERS_CACHE_TIMEOUT` Cache duration of the players list as well as data for a single player (in seconds)
  - `GRAPHS_DATA_CACHE_TIMEOUT` Cache duration of the graphs data, both the players and the servers ones (in seconds)
  - `STEAM_PLAYERS_CACHE_TIMEOUT` Cache duration of the total number of players (in seconds)
  - `BETA_USERS` The credentials required to access the app when beta mode is enabled. You can specify multiple ones. **It is highly recommended to serve RWRS through HTTPS** because it uses [HTTP basic auth](https://en.wikipedia.org/wiki/Basic_access_authentication)
  - `STEAM_API_KEY` A [Steam API](https://steamcommunity.com/dev) key
  - `PACIFIC_PLAYERS_RANKS_COUNTRY` Ranks image / name to show for the Pacific players stats (`us`, `jp`)
  - `DISCORD_BOT_TOKEN` Authentication token used by the RWRS Discord bot
  - `DISCORD_BOT_CHANNEL_ID` The Discord channel ID the bot is allowed to talk in

I'll let you search yourself about how to configure a web server along uWSGI.

## Usage

  - Standalone

Run the internal web server, which will be accessible at `http://localhost:8080`:

```
python local.py
```

Edit this file and change the interface/port as needed.

  - uWSGI

The uWSGI file you'll have to set in your uWSGI configuration is `uwsgi.py`. The callable is `app`.

  - Others

You'll probably have to hack with this application to make it work with one of the solutions described
[here](http://flask.pocoo.org/docs/0.12/deploying/). Send me a pull request if you make it work.

### Extracting ranks data and images

The Flask command `flask extract_ranks` is used to extract and save all ranks data to a JSON file located at `storage/data/ranks.json`.
It also retrieve, process (the actual images content isn't centered) and save all the RWR ranks images. They are saved
at `static/images/ranks/{country}/{rank ID}.png` and `static/images/ranks/{country}/{rank ID}_icon.png`.

  1. `pip install -r requirements-dev.txt`
  2. `set FLASK_APP=rwrs.py`
  3. `flask extract_ranks --steamdir="{path to the Steam root directory}"`

This command requires the game to be installed.

### Extracting maps data

The Flask command `flask extract_maps_data` is used to extract and save all maps data to a JSON file located at `storage/data/maps.json`.

  1. `set FLASK_APP=rwrs.py`
  2. `flask extract_maps_data --steamdir="{path to the Steam root directory}"`

This command requires the game to be installed.

### Extracting mapviews

The Flask command `flask extract_mapviews` is used to extract mapviews (the ones displayed when pressing on
<kbd>TAB</kbd>). They are saved at `static/images/maps/mapviews/{game type}/{map ID}.png`.

  1. `pip install -r requirements-dev.txt`
  2. `set FLASK_APP=rwrs.py`
  3. `flask extract_mapviews --steamdir="{path to the Steam root directory}"`

This command requires the game to be installed.

### Clearing cache

  1. `set FLASK_APP=rwrs.py`
  2. `flask cc`

### Clearing old graphs data

Data older than one week old will be deleted.

  1. `set FLASK_APP=rwrs.py`
  2. `flask clean_players_count`

### Storing actual number of players (for graphs)

Will save the current number of Steam players which have RWR running, and the current number of players playing online.

  1. `set FLASK_APP=rwrs.py`
  2. `flask get_players_count`

### Migrating the database

  1. `set FLASK_APP=rwrs.py`
  2. `flask db upgrade`

### Saving RWR root servers status

Will ping RWR root servers and store their status (up or down).

  1. `set FLASK_APP=rwrs.py`
  2. `flask get_root_rwr_servers_status`

### Running the RWRS Discord bot

  1. `set FLASK_APP=rwrs.py`
  2. `flask run_discord_bot`

### Generating the maps tiles for the maps gallery

They are saved at `static/images/maps/tiles/{game type}/{map ID}/{z}/{x}/{y}.png`.

  1. `pip install -r requirements-dev.txt`
  2. `set FLASK_APP=rwrs.py`
  3. `flask generate_maps_tiles --steamdir="{path to the Steam root directory}"`

### Updating the MaxMind GeoLite2 City database

More information in the script comments.

`sh scripts/geolite2_city_updater.sh`

### Updating RWRS

More information in the script comments.

`sh scripts/rwrs_updater.sh [DOMAIN, default=rwrstats.com]`

### Backup SQLite databases

More information in the script comments.

`sh scripts/backup_databases.sh`

## How it works

This project is mainly powered by [Flask](http://flask.pocoo.org/) (Python) for the backend.

Data is fetched from the [official servers list](http://rwr.runningwithrifles.com/rwr_server_list/view_servers.php) page
(which sucks) as well from the [official players list](http://rwr.runningwithrifles.com/rwr_stats/view_players.php?sort=score)
page (which sucks, too). Data is cached so there isn't many requests sent to the server who hosts these lists.

As the provided servers location is most of the time either missing or invalid, RWRS makes its own look up using a
[GeoLite2](https://dev.maxmind.com/geoip/geoip2/geolite2/) database.

## Credits

  - RWRS icon by [goodware std.](https://www.iconfinder.com/icons/2760623/army_bomb_grenade_military_navy_tank_weapon_icon#size=256) (CC BY 3.0)
  - Font by [Typesgal](https://www.dafont.com/fr/top-secret-kb.font) (freeware)
  - Flag icons by [Flag Sprites](https://www.flag-sprites.com/en/) and [GoSquared](https://www.gosquared.com/resources/flag-icons/) (freeware)
  - Maps previews comes from the [official RWR wiki](https://runningwithrifles.gamepedia.com/Running_with_Rifles_Wiki)
  - This project uses GeoLite2 data created by MaxMind, available from [www.maxmind.com](https://www.maxmind.com/)
  - All Running With Rifles assets © 2015 - 2018 Osumia Games
  - This project is not affiliated with Osumia Games

## End words

If you have questions or problems, you can either:

  - Submit an issue [here on GitHub](https://github.com/EpocDotFr/rwrs/issues)
  - Post a message in [this topic](http://www.runningwithrifles.com/phpBB3/viewtopic.php?f=12&t=3376) on the official RWR forums
  - Post a message in [this Steam topic](https://steamcommunity.com/app/270150/discussions/0/1520386297704428050/)