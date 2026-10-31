#!/bin/bash
# Bring the packages in ~/.venvs/playfield-tools up to date with requirements.txt.
# (Add a package by putting its name in requirements.txt, then run this.)
#   bash scripts/update.sh
set -e
cd "$(dirname "$0")"
"$HOME/.venvs/playfield-tools/bin/pip" install --upgrade -r requirements.txt
