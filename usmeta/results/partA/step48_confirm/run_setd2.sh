#!/bin/bash
# Set D2 (DEVIATIONS.md 2): Llama-3.1-8B writer. Waits for the Phi Set D Gemma job, commits the deviation,
# runs a 60-report pilot, then the full rewrite, filter, extraction and the Gemma judge. Re-run safely after a stop.
# Run:  bash ~/medical-imaging-ai/usmeta/results/partA/step48_confirm/run_setd2.sh
cd ~/medical-imaging-ai || exit 1
PY="caffeinate -i env STEP48_WRITER=llama PYTHONPATH=usmeta .venv/bin/python -m"
echo "$(date '+%a %H:%M') waiting for the Phi Set D Gemma job to finish..."
while pgrep -f "which setd --judge" >/dev/null; do sleep 60; done
set -e
git add usmeta/usmeta/step48.py usmeta/usmeta/step48_setd.py usmeta/results/partA/step48_confirm/DEVIATIONS.md usmeta/results/partA/step48_confirm/run_setd2.sh
git commit -m "Step 48: deviations 1-2 (Phi writer run-on fix; Phi Set D not eligible at filter stage, rewrite as Set D2 with Llama-3.1-8B writer) before any Set D score" || true
git push origin main || echo "PUSH FAILED - tell Claude (generation continues)"
echo "$(date '+%a %H:%M') 1/7 plan"
$PY usmeta.step48_setd plan
echo "$(date '+%a %H:%M') 2/7 pilot (about 6 minutes)"
$PY usmeta.step48_setd generate --max-hours 0.1
$PY usmeta.step48_setd pilot
RATE=$($PY usmeta.step48_setd pilot | sed -n 's/.*rate \([0-9.]*\).*/\1/p')
if python3 -c "import sys; sys.exit(0 if float('${RATE:-0}') >= 0.40 else 1)"; then echo "pilot ok ($RATE)"; else echo "PILOT KEEP RATE TOO LOW ($RATE) - STOPPED, tell Claude"; exit 1; fi
echo "$(date '+%a %H:%M') 3/7 writing reports"
$PY usmeta.step48_setd generate --max-hours 12
echo "$(date '+%a %H:%M') 4/7 gold filter"
$PY usmeta.step48_setd gold
echo "$(date '+%a %H:%M') 5/7 limit-of-detection reports"
$PY usmeta.step48_setd generate --only lod --max-hours 4
$PY usmeta.step48_setd gold
echo "$(date '+%a %H:%M') 6/7 extracting facts"
$PY usmeta.step48_setd extract
echo "$(date '+%a %H:%M') SET D2 READY FOR HAND CHECK (tell Claude)"
echo "$(date '+%a %H:%M') 7/7 Gemma judge on Set D2"
for i in 1 2 3; do $PY usmeta.step48 calls --which setd2 --judge gemma --max-hours 30 && break; sleep 120; done
echo "$(date '+%a %H:%M') SET D2 GEMMA DONE"
