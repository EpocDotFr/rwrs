# Running With Rifles Stats (RWRS)

<img src="static/images/icon_round_dark_256.png" align="right">

Players statistics, servers list and more for the [Running With Rifles](http://www.runningwithrifles.com/wp/) (RWR) game
as well as its Pacific and Edelweiss DLCs.

[Website](https://rwrstats.com/) • [Discord](https://discord.gg/runningwithrifles) • [Steam Discussions](https://steamcommunity.com/app/270150/discussions/0/1520386297704428050/)

## Prerequisites

  - Python >= 3.8
  - A modern web browser
  - An SQLAlchemy-supported DBMS
  - (Optional, but recommended) A WSGI-capable web server
  - (Optional) Running With Rifles, if you need to extract data from the game files

## Installation

  1. Clone this repo somewhere
  2. Copy `.env.local` to `.env`, then fill in the required/desired variables
  3. `pip install -r requirements-dev.txt`
  4. `flask db upgrade`
  5. `bash scripts/geolite2_city_updater.sh {license key}`

## Credits

You'll find credits and legal mentions [here](https://rwrstats.com/about#credits).

## Feedback

If you have suggestions or problems you can submit an issue [here on GitHub](https://github.com/EpocDotFr/rwrs/issues) or
head over [thhere](https://rwrstats.com/feedback).