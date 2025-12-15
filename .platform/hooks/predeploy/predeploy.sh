#!/bin/bash
set -e

source $PYTHONPATH/activate

rm -rf static/webpack_bundles/ || echo "no webpack bundles to remove"
rm -rf staticfiles/ || echo "no staticfiles to remove"
NODE_OPTIONS=--max_old_space_size=400 npm install --omit:dev
NODE_OPTIONS=--openssl-legacy-provider npm run build

python manage.py compilescss

python manage.py collectstatic --noinput --ignore *.scss
