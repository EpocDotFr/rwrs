cd storage/data
rm -f *.mmdb
curl -O http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
tar -xzf GeoLite2-City.tar.gz