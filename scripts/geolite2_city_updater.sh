#!/usr/bin/env sh
#
# RWRS GeoLite2 City database updater
#
# This script updates the MaxMind GeoLite2 City database used by the geoip2 Python package, itself used by RWRS to
# determine the physical location of the RWR servers. The said database is stored in storage/data/GeoLite2-City.mmdb
# Refs:
# - https://dev.maxmind.com/geoip/geoip2/geolite2/
# - https://geoip2.readthedocs.io/en/latest/

set -e # Makes any subsequent failing commands to exit the script immediately

DATA_DIR="storage/data"
REMOTE_DB_FILE="http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz"
OUTPUT_FILE="$DATA_DIR/GeoLite2-City.tar.gz"

echo "## Downloading and decompressing archive"

curl -o $OUTPUT_FILE -sS $REMOTE_DB_FILE
tar -xzf $OUTPUT_FILE -C $DATA_DIR
rm $OUTPUT_FILE

echo "## Removing old version"

rm -f "$DATA_DIR/"*".mmdb"

echo "## Applying new version"

mv "$DATA_DIR/GeoLite2-City_"*"/GeoLite2-City.mmdb" $DATA_DIR

echo "## Cleaning temporary directories"

rm -r "$DATA_DIR/GeoLite2-City_"*
chown www-data:www-data "$DATA_DIR/"*".mmdb"