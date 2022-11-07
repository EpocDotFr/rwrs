#!/usr/bin/env bash

set -e # Makes any subsequent failing commands to exit the script immediately

echo "Loading env variables from dotenv files"

if [ -f .env ]; then
    export $(cat .env | xargs)
fi

if [ -f .flaskenv ]; then
    export $(cat .flaskenv | xargs)
fi

# Activate Python env
. venv/bin/activate

# Determine if we should enable maintenance mode
if [ -f maintenance ]; then
    MAINTENANCE_ALREADY_ENABLED=true
else
    MAINTENANCE_ALREADY_ENABLED=false
fi

if [ "$MAINTENANCE_ALREADY_ENABLED" = false ]; then
    echo "Enabling maintenance mode"

    touch maintenance
fi

echo "Pulling latest code version"

git pull

echo "Restarting site"

chown -R www-data:www-data ./

supervisorctl restart rwrstats.com

if [ "$MAINTENANCE_ALREADY_ENABLED" = false ]; then
    echo "Disabling maintenance mode"

    rm maintenance
fi
