#!/bin/bash
# Step 47: run every remaining machine step automatically, resuming where it left off.
# Start once with:  bash usmeta/results/partA/step47_audit_route/run_all.sh
# It stops before scoring, because the 50-report hand check must be filled first.
cd ~/medical-imaging-ai || exit 1
export PYTHONPATH=usmeta
PY=.venv/bin/python
D=usmeta/results/partA/step47_audit_route
LOG=$D/run_all.log
say() { echo "[$(date '+%d %b %H:%M')] $*" | tee -a "$LOG"; }

run_until() {  # run_until <success-text> <tries> <command...>
  local want="$1" tries="$2"; shift 2
  for i in $(seq 1 "$tries"); do
    say "RUN ($i/$tries): $*"
    "$@" 2>&1 | tee -a "$LOG" | grep -q "$want" && { say "OK: $*"; return 0; }
  done
  say "STOPPED: '$*' did not finish after $tries tries. Send the log to Claude."; exit 1
}

retry_ok() {  # retry_ok <tries> <command...>  (success = exit code 0)
  local tries="$1"; shift
  for i in $(seq 1 "$tries"); do
    say "RUN ($i/$tries): $*"
    "$@" >>"$LOG" 2>&1 && { say "OK: $*"; return 0; }
  done
  say "STOPPED: '$*' failed $tries times. Send the log to Claude."; exit 1
}

say "=== Step 47 run_all started ==="
[ -f $D/set_C/plan.json ] || retry_ok 1 $PY -m usmeta.step47_freetext plan

# core generation: repeat until gold accepts it
for i in 1 2 3 4; do
  $PY -m usmeta.step47_freetext gold >>"$LOG" 2>&1 && { say "OK: core generation complete"; break; }
  [ $i = 4 ] && { say "STOPPED: core generation incomplete after 3 runs"; exit 1; }
  retry_ok 1 $PY -m usmeta.step47_freetext generate --max-hours 12
done
# limit-of-detection reports, then rebuild and extract
retry_ok 3 $PY -m usmeta.step47_freetext generate --only lod --max-hours 4
retry_ok 1 $PY -m usmeta.step47_freetext gold
retry_ok 3 $PY -m usmeta.step47_freetext extract

[ -f $D/handcheck_setC.csv ] || retry_ok 1 $PY -m usmeta.step47_audit_route export-handcheck
say ">>> HAND CHECK READY: open $D/handcheck_setC.csv (you or Harshal). The judge runs continue meanwhile."

run_until "calls complete" 4 $PY -m usmeta.step47_audit_route calls --set test --max-hours 8
run_until "calls complete" 3 $PY -m usmeta.step47_audit_route calls --set test --judge llama --max-hours 6
[ -f $D/extraction_v5_setr.json ] || retry_ok 1 $PY -m usmeta.step47_audit_route extract-setr
run_until "calls complete" 2 $PY -m usmeta.step47_audit_route calls --set setr --max-hours 2

say "=== ALL MACHINE STEPS DONE. Fill the hand check, then tell Claude to run score-test. ==="
