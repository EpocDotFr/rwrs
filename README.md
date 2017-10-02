# RWRS (Running With Rifles Stats)

Players statistics for the official [Running With Rifles](http://www.runningwithrifles.com/wp/) (RWR) servers, and more.
Available at [rwrs.epoc.fr](https://rwrs.epoc.fr/).

## Features

  - Web-based
  - Players
    - Search for a player
    - View player stats (as well as next rank progression, which server he's playing on, etc)
    - Compare two players stats
  - Public servers
    - Real servers location
    - Real maps name
    - Maps are linked to their [official RWR wiki](https://runningwithrifles.gamepedia.com/Running_with_Rifles_Wiki) page
    - Official servers are highlighted
    - Public servers list
    - Public server details (players list with link to their profile, current map preview and minimap, etc)

## Prerequisites

  - Should work on any Python 3.x version. Feel free to test with another Python version and give me feedback
  - (Optional, but recommended) A [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/)-capable web server

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

### Downloading ranks images

The Flask command `flask download_ranks_images` is used to download, process (the actual images content isn't centered)
and save all the RWR ranks images. They are saved at `static/images/ranks/{rank ID}.png`.

  1. `set FLASK_APP=rwrs.py`
  2. `flask download_ranks_images`

### Extracting minimaps

The Flask command `flask extract_minimaps` is used to extract minimaps (the ones displayed when pressing on
<kbd>TAB</kbd>). They are saved at `static/images/maps/minimap/{rank ID}.png` and `static/images/maps/minimap/{rank ID}_preview.png`.

  1. `set FLASK_APP=rwrs.py`
  2. `flask extract_minimaps --gamedir="{path to the game root directory}"`

## How it works

This project is powered by [Flask](http://flask.pocoo.org/) (Python) for the backend. The frontend is powered by good ol'
HTML and CSS.

Data is fetched from the [official servers list](http://rwr.runningwithrifles.com/rwr_server_list/view_servers.php) page
(which sucks) as well from the [official players list](http://rwr.runningwithrifles.com/rwr_stats/view_players.php?sort=score)
page (which sucks, too).

As the provided servers location is most of the time either missing or invalid, RWRS makes its own look up using a
[GeoLite2](https://dev.maxmind.com/geoip/geoip2/geolite2/) database.

## Credits

  - RWRS icon by [Dot on Paper](https://www.iconfinder.com/icons/753920/gun_military_shield_war_weapon_weapons_icon) (freeware)
  - Font by [Typesgal](https://www.dafont.com/fr/top-secret-kb.font) (freeware)
  - Flag icons by [Flag Sprites](https://www.flag-sprites.com/en/) and [GoSquared](https://www.gosquared.com/resources/flag-icons/) (freeware)
  - Maps previews comes from the [official RWR wiki](https://runningwithrifles.gamepedia.com/Running_with_Rifles_Wiki)
  - This project uses GeoLite2 data created by MaxMind, available from [www.maxmind.com](https://www.maxmind.com/)
  - RWR logo, ranks images, Running With Rifles © 2015 - 2017 Osumia Games
  - This project isn't supported nor endorsed by Osumia Games

## End words

If you have questions or problems, you can either submit an issue [here on GitHub](https://github.com/EpocDotFr/rwrs/issues)
or in [this Reddit thread](TODO).