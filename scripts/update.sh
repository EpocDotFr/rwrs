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

status=$(curl --basic --user "${ALWAYSDATA_API_TOKEN} account=${ALWAYSDATA_ACCOUNT_NAME}:" --data '' --request POST --silent --output /dev/null --write-out '%{http_code}' "https://api.alwaysdata.com/v1/site/${ALWAYSDATA_SITE_ID}/restart/")

if [ "$status" = 204 ];
then
    echo "Success"

    if [ "$MAINTENANCE_ALREADY_ENABLED" = false ]; then
        echo "Disabling maintenance mode"

        rm maintenance
    fi
else
    echo "Error occured while restarting site"
fi