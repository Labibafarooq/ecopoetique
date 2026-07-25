#!/bin/bash
# Autonomous sequencing script (2026-07-08), requested by Labiba:
# 1. Wait for Task 2 gold validation (decision-tree) to finish
# 2. Wait for Task 4.5 gold validation (CMT chain) to finish
# 3. Run Task 0 v10b calibration (fresh 20-novel test)
# 4. Only THEN stop and restart Task 1 (never touch Task 1 before this point)

set -e

echo "[orchestrator] $(date) — waiting for Task 2 (decision-tree) to finish..."
until grep -q "^Final:" ~/ecopoetique/métaphore/task2_decisiontree_run.log 2>/dev/null; do
    sleep 30
done
echo "[orchestrator] $(date) — Task 2 done."

echo "[orchestrator] $(date) — waiting for Task 4.5 (CMT chain) to finish..."
until grep -q "^Final:" ~/ecopoetique/comparison/task45_cmt_run.log 2>/dev/null; do
    sleep 30
done
echo "[orchestrator] $(date) — Task 4.5 done."

echo "[orchestrator] $(date) — starting Task 0 v10b calibration (20 novels)..."
cd ~/ecopoetique/narratologie
python3 -u run_task0_v10_foc_reg_tem.py --test 20 > test_v10b_20.log 2>&1
echo "[orchestrator] $(date) — Task 0 v10b done."

echo "[orchestrator] $(date) — stopping Task 1..."
TASK1_PID=$(pgrep -f "run_task1_corpus.py --category plantes" | head -1)
if [ -n "$TASK1_PID" ]; then
    kill "$TASK1_PID"
    sleep 3
    echo "[orchestrator] Task 1 (PID $TASK1_PID) stopped."
else
    echo "[orchestrator] WARNING: Task 1 process not found — nothing to stop."
fi

echo "[orchestrator] $(date) — restarting Task 1..."
cd ~/ecopoetique/métaphore
nohup python3 -u run_task1_corpus.py --category plantes >> ../resultats/task1_plantes_run.log 2>&1 &
disown
echo "[orchestrator] $(date) — Task 1 restarted. Orchestration complete."
