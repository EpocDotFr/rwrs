#!/usr/bin/env sh
#
# RWRS databases backup script
#
# This script backups all the RWRS SQLite databases, compress them all in one tar.gz file and send it to Dropbox.
# The following environment variables are required:
#  - DROPBOX_ACCESS_TOKEN

set -e # Makes any subsequent failing commands to exit the script immediately

DATA_DIR="storage/data"
declare -a DATABASES=("$DATA_DIR/"*".sqlite")
NOW=$(date +"%Y-%m-%d_%H-%M")
BACKUP_FILE="$DATA_DIR/backup_$NOW.tar.gz"
DATABASES_STRING=""
DROPBOX_FILEPATH="/rwrs/backups/${BACKUP_FILE##*/}"
DROPBOX_ACCESS_TOKEN=$(printenv DROPBOX_ACCESS_TOKEN)

echo "## Backing up databases"

for database in "${DATABASES[@]}"
do
    echo "  $database"
    sqlite3 "$database" ".backup '$database.bak'"
    DATABASES_STRING="$DATABASES_STRING${database##*/}.bak "
done

echo "## Compressing backup files"

tar -C $DATA_DIR -czf $BACKUP_FILE $DATABASES_STRING

echo "## Sending compressed backup"

curl -X POST https://content.dropboxapi.com/2/files/upload \
    --header "Authorization: Bearer $DROPBOX_ACCESS_TOKEN" \
    --header "Dropbox-API-Arg: {\"path\": \"$DROPBOX_FILEPATH\"}" \
    --header "Content-Type: application/octet-stream" \
    --data-binary @$BACKUP_FILE \
    --output /dev/null

echo "## Cleaning files"

rm -f "$DATA_DIR/"*".sqlite.bak"
rm -f $BACKUP_FILE