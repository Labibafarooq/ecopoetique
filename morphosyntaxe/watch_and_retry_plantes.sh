#!/bin/bash
# Waits for the main Task1 plantes run to finish, then automatically retries
# all failed batches accumulated by that point (not just the count seen at
# launch time — whatever is in task1_plantes_failed_keys.tsv once the main
# run actually exits).
MAIN_PID=3534857
LOGDIR=/home/lfarooq/ecopoetique/resultats
WATCHER_LOG="$LOGDIR/task1_plantes_retry_watcher.log"

echo "$(date): watcher started, waiting on main run PID $MAIN_PID" >> "$WATCHER_LOG"

while kill -0 "$MAIN_PID" 2>/dev/null; do
    sleep 60
done

echo "$(date): main plantes run (PID $MAIN_PID) has exited, starting retry of failed batches" >> "$WATCHER_LOG"

cd /home/lfarooq/ecopoetique/morphosyntaxe || exit 1
python3 -u retry_plantes.py >> "$LOGDIR/task1_plantes_retry.log" 2>&1

echo "$(date): retry pass finished" >> "$WATCHER_LOG"
