#!/usr/bin/env bash
#
# RWRS API documentation generator
#
# Generates the RWRS API documentation. aglio must be installed. Input API Blueprint files are located in docs/api,
# output file is saved in static/api_doc.html.
# Refs:
# - https://github.com/danielgtaylor/aglio

set -e # Makes any subsequent failing commands to exit the script immediately

aglio \
    -i docs/api/index.apib \
    -o static/api_doc.html \
    --theme-variables flatly \
    --theme-full-width