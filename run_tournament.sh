#!/bin/bash
BASE_PORT=$1
python3 ./scripts/dicewars-tournament.py -l "./logs/" --ai-under-test xsismi01 -g $2 -n 5000 --port $((BASE_PORT+$2)) -b 101 -s 1337 -r --save "tournament-g$2-n5000-$(date).pickle"