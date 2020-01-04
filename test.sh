#!/bin/bash
tmux new-session -d -s "SUI" 'ls'
for i in {2..5}
do
    tmux neww -t "SUI:$i"
    tmux send-keys -t "SUI:$i" "cd $(pwd) && . path.sh && ./run_tournament.sh $1 $i" Enter
done