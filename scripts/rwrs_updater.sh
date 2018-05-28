#!/usr/bin/env bash
#
# RWRS updater
#
# Well, this script updates everything in RWRS, i.e source code, database schema, dependencies, etc.

set -e # Makes any subsequent failing commands to exit the script immediately

TYPE=${1:-fast}
DOMAIN=${2:-rwrstats.com}

echo "## Initializing ($TYPE update)"

. venv/bin/activate
export FLASK_APP=rwrs.py

echo "## Enabling maintenance mode"

touch maintenance

echo "## Pulling latest code version"

git pull

if [ $TYPE = "full" ]; then
    echo "## Updating dependencies"

    pip install --upgrade --no-cache -r requirements.txt
    pip install --upgrade --no-cache uwsgi
fi

if [ $TYPE = "full" ]; then
    echo "## Migrating DB"

    venv/bin/flask db upgrade

    echo "## Clearing cache"

    venv/bin/flask cc
fi

echo "## Restarting services"

chown -R www-data:www-data ./

supervisorctl restart $DOMAIN discordbot.$DOMAIN

echo "## Disabling maintenance mode"

rm maintenance