# Running With Rifles Stats (RWRS)

> [!IMPORTANT]
> This project was hosted at https://rwrstats.com, but no longer has anything to do with the current site and owner since it
> has shutdown. If the current site and/or its owner claim otherwise, do NOT trust them.

<img src="static/images/icon_round_dark_256.png" align="right">

Players statistics, servers list and more for the [Running With Rifles](http://www.runningwithrifles.com/wp/) (RWR) game
as well as its Pacific and Edelweiss DLCs.

[Discord](https://discord.gg/runningwithrifles) • [Steam Discussions](https://steamcommunity.com/app/270150/discussions/0/1520386297704428050/)

## Prerequisites

  - Python >= 3.8
  - A modern web browser
  - An SQLAlchemy-supported DBMS
  - (Optional, but recommended) A WSGI-capable web server
  - (Optional) Running With Rifles, if you need to extract data from the game files

## Installation

  1. Clone this repo somewhere
  2. Copy `.env.example` to `.env`, then fill in the required/desired variables
  3. `pip install -r requirements-dev.txt`
  4. `flask db upgrade`
  5. `bash scripts/geolite2_city_updater.sh`
