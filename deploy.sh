#!/usr/bin/env bash
set -e

python3 update_site.py

git add .
git commit -m "auto update site" || echo "No changes to commit."
git push
