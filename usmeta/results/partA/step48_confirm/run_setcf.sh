#!/bin/bash
# Waits for the Llama Set C job (run_after_llama.sh), then builds and judges Set C-F (off-schema development errors).
# Run from a Terminal tab:  bash ~/medical-imaging-ai/usmeta/results/partA/step48_confirm/run_setcf.sh
cd ~/medical-imaging-ai || exit 1
PY="caffeinate -i env PYTHONPATH=usmeta .venv/bin/python -m"
echo "$(date '+%H:%M') waiting for any running Llama Set C job..."
while pgrep -f "usmeta.step48 llama-setc" >/dev/null; do sleep 60; done
for i in 1 2 3; do $PY usmeta.step48 llama-setc --max-hours 8 && break; sleep 120; done
echo "$(date '+%H:%M') LLAMA SET C DONE"
set -e
$PY usmeta.step48_devfab plan
$PY usmeta.step48_devfab generate --max-hours 4
$PY usmeta.step48_devfab gold
$PY usmeta.step48_devfab extract
$PY usmeta.step48 calls --which setcf --judge gemma --max-hours 6
$PY usmeta.step48 calls --which setcf --judge llama --max-hours 6
echo "$(date '+%H:%M') SET C-F DONE - READY FOR STAGE 1"
