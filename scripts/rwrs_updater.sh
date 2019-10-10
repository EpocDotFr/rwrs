#!/usr/bin/env bash
#
# RWRS updater
#
# Well, this script updates everything in RWRS, i.e source code, database schema, dependencies, etc.

set -e # Makes any subsequent failing commands to exit the script immediately

TYPE=${1:-fast}

if [ -f maintenance ]; then
    MAINTENANCE_ALREADY_ENABLED=true
else
    MAINTENANCE_ALREADY_ENABLED=false
fi

echo "## Initializing ($TYPE update)"

. venv/bin/activate
export FLASK_APP=rwrs.py

if [ "$MAINTENANCE_ALREADY_ENABLED" = false ]; then
    echo "## Enabling maintenance mode"

    touch maintenance
fi

echo "## Pulling latest code version"

git pull

if [ $TYPE = "full" ]; then
    echo "## Updating dependencies"

    pip install --upgrade --no-cache -r requirements.txt
    pip install --upgrade --no-cache uwsgi

    echo "## Migrating DB"

    venv/bin/flask db upgrade

    echo "## Clearing cache"

    venv/bin/flask cc
fi

echo "## Restarting services"

chown -R www-data:www-data ./

supervisorctl restart rwrstats.com discordbot.rwrstats.com

if [ "$MAINTENANCE_ALREADY_ENABLED" = false ]; then
    echo "## Disabling maintenance mode"

    rm maintenance
fi