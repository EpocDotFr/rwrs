#!/usr/bin/env sh
#
# RWRS Updater
#
# Well, this script updates everything in RWRS, i.e source code, database schema, dependencies, etc.

set -e # Makes any subsequent failing commands to exit the script immediately

DOMAIN=${1:-rwrstats.com}

echo "## Initializing"

. venv/bin/activate
export FLASK_APP=rwrs.py

echo "## Enabling maintenance mode"

touch maintenance

echo "## Updating dependencies"

pip install --upgrade --no-cache -r requirements.txt
pip install --upgrade --no-cache uwsgi

echo "## Pulling latest code version"

git pull

echo "## Migrating DB"

venv/bin/flask db upgrade

echo "## Restarting services"

chown -R www-data:www-data ./

supervisorctl restart $DOMAIN discordbot.$DOMAIN

echo "## Disabling maintenance mode"

rm maintenance