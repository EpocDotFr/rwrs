#!/usr/bin/env bash
#
# RWRS GeoLite2 City database updater
#
# This script updates the MaxMind GeoLite2 City database used by the geoip2 Python package, itself used by RWRS to
# determine the physical location of the RWR servers. The said database is stored in instance/GeoLite2-City.mmdb.
# Refs:
# - https://dev.maxmind.com/geoip/geoip2/geolite2/
# - https://geoip2.readthedocs.io/en/latest/

set -e # Makes any subsequent failing commands to exit the script immediately

echo "Loading env variables from dotenv files"

if [ -f .env ]; then
    export $(cat .env | xargs)
fi

if [ -f .flaskenv ]; then
    export $(cat .flaskenv | xargs)
fi

if [ "$GEOIP_LICENSE_KEY" = "" ]; then
    echo "Missing license key"
    exit
fi

OUTPUT_DIR="instance"
REMOTE_DB_FILE="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=$GEOIP_LICENSE_KEY&suffix=tar.gz"
OUTPUT_FILE="$OUTPUT_DIR/GeoLite2-City.tar.gz"

echo "Downloading and decompressing archive"

curl -o $OUTPUT_FILE -sS $REMOTE_DB_FILE
tar -xzf $OUTPUT_FILE -C $OUTPUT_DIR
rm $OUTPUT_FILE

echo "Removing old version"

rm -f "$OUTPUT_DIR/"*".mmdb"

echo "Applying new version"

mv "$OUTPUT_DIR/GeoLite2-City_"*"/GeoLite2-City.mmdb" $OUTPUT_DIR

echo "Cleaning temporary directories"

rm -r "$OUTPUT_DIR/GeoLite2-City_"*