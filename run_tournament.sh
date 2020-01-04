#!/bin/bash
BASE_PORT=30000
python3 ./scripts/dicewars-tournament.py -l . --ai-under-test xsismi01 -g $1 -n 5000 --port $((BASE_PORT+$1)) -b 101 -s 1337 -r --save "tournament-g$1-n5000-$(date).pickle"