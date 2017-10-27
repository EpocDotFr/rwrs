# RWRS (Running With Rifles Stats)

Players statistics for the official [Running With Rifles](http://www.runningwithrifles.com/wp/) (RWR) invasion servers,
and more. Available at [rwrstats.com](https://rwrstats.com/).

## Features

  - Players
    - Search for a player
    - View player stats (as well as next rank progression, unlocks, on which server he's playing on, etc). Note that stats only concerns official invasion (ranked) servers
    - Compare two players stats
    - Friends list (easily know on which servers your friends are playing on. There's no need to create a user account or whatever)
  - Public servers
    - Real servers location
    - Real maps name
    - Maps are linked to their [official RWR wiki](https://runningwithrifles.gamepedia.com/Running_with_Rifles_Wiki) page
    - Official invasion (ranked) servers are highlighted
    - Game mode (coop, PvPvE, etc) and type (vanilla RWR, Pacific DLC, etc)
    - Public server details (players list with link to their profile, current map preview and minimap, etc)

## Prerequisites

  - Should work on any Python 3.x version. Feel free to test with another Python version and give me feedback
  - A modern web browser (which optionally support localStorage)
  - (Optional, but recommended) A [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/)-capable web server
  - (Optional) Running With Rifles, if you need to extract images

## Installation

  1. Clone this repo somewhere
  2. `pip install -r requirements.txt`

## Configuration

Copy the `config.example.py` file to `config.py` and fill in the configuration parameters.

Available configuration parameters are:

  - `SECRET_KEY` Set this to a complex random value
  - `DEBUG` Enable/disable debug mode
  - `LOGGER_HANDLER_POLICY` Policy of the default logging handler

More informations on the three above can be found [here](http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values).

  - `GAUGES_SITE_ID` A [Gauges](https://gaug.es/) site ID used to track visits on RWRS (optional)

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

### Extracting ranks images

The Flask command `flask extract_ranks_images` is used to retrieve, process (the actual images content isn't centered)
and save all the RWR ranks images. They are saved at `static/images/ranks/{rank ID}.png`.

  1. `set FLASK_APP=rwrs.py`
  2. `flask extract_ranks_images --gamedir="{path to the game root directory}"`

This command requires the game to be installed.

### Extracting minimaps

The Flask command `flask extract_minimaps` is used to extract minimaps (the ones displayed when pressing on
<kbd>TAB</kbd>). They are saved at `static/images/maps/minimap/{map ID}.png` and `static/images/maps/minimap/{map ID}_thumb.png`.

  1. `set FLASK_APP=rwrs.py`
  2. `flask extract_minimaps --gamedir="{path to the game root directory}"`

This command requires the game to be installed.

## How it works

This project is mainly powered by [Flask](http://flask.pocoo.org/) (Python) for the backend.

Data is fetched from the [official servers list](http://rwr.runningwithrifles.com/rwr_server_list/view_servers.php) page
(which sucks) as well from the [official players list](http://rwr.runningwithrifles.com/rwr_stats/view_players.php?sort=score)
page (which sucks, too). Data is cached so there isn't many requests sent to the server who hosts these lists.

As the provided servers location is most of the time either missing or invalid, RWRS makes its own look up using a
[GeoLite2](https://dev.maxmind.com/geoip/geoip2/geolite2/) database.

## Credits

  - RWRS icon by [Dot on Paper](https://www.iconfinder.com/icons/753920/gun_military_shield_war_weapon_weapons_icon) (freeware)
  - Font by [Typesgal](https://www.dafont.com/fr/top-secret-kb.font) (freeware)
  - Flag icons by [Flag Sprites](https://www.flag-sprites.com/en/) and [GoSquared](https://www.gosquared.com/resources/flag-icons/) (freeware)
  - Maps previews comes from the [official RWR wiki](https://runningwithrifles.gamepedia.com/Running_with_Rifles_Wiki)
  - This project uses GeoLite2 data created by MaxMind, available from [www.maxmind.com](https://www.maxmind.com/)
  - RWR logo, ranks images, items images, Running With Rifles © 2015 - 2017 Osumia Games
  - This project isn't supported nor endorsed by Osumia Games

## End words

If you have questions or problems, you can either:

  - Submit an issue [here on GitHub](https://github.com/EpocDotFr/rwrs/issues)
  - Post a comment in [this Reddit thread](https://www.reddit.com/r/Runningwithrifles/comments/741v7h/introducing_rwrs_running_with_rifles_stats_more/)
  - Post a message in [this topic](http://www.runningwithrifles.com/phpBB3/viewtopic.php?f=12&t=3376) on the official RWR forums
  - Post a message in [this Steam topic](https://steamcommunity.com/app/270150/discussions/0/1520386297704428050/)