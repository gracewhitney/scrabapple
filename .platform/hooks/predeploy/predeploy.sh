#!/bin/bash
set -e

source $PYTHONPATH/activate

NODE_OPTIONS=--max_old_space_size=400 npm install --omit:dev

rm -rf static/webpack_bundles/ || echo "no webpack bundles to remove"
rm -rf staticfiles/webpack_bundles/ || echo "no staticfiles webpack bundles to remove"
NODE_OPTIONS=--openssl-legacy-provider npm run build

python manage.py compilescss

python manage.py collectstatic --noinput --ignore *.scss
