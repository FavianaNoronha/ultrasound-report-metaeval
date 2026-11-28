#!/bin/bash
# Waits for Gemma on Set D2, then: Llama judge (300 subset), VERT (Set C calibration + Set D2), GREEN, CRIMSON.
# Each comparator is independent: a failure is reported and the script moves on. Safe to re-run (resumes).
# Run:  bash ~/medical-imaging-ai/usmeta/results/partA/step48_confirm/run_comparators.sh
cd ~/medical-imaging-ai || exit 1
PY="caffeinate -i env STEP48_WRITER=llama PYTHONPATH=usmeta .venv/bin/python -m"
git add usmeta/usmeta/step48_comparators.py usmeta/usmeta/third_party usmeta/usmeta/step48.py usmeta/results/partA/step48_confirm/DEVIATIONS.md usmeta/results/partA/step48_confirm/run_comparators.sh usmeta/results/partA/step48_confirm/handcheck_setD2.json usmeta/results/partA/step48_confirm/handcheck_setD2_result.md
git commit -m "Step 48: comparator code (GREEN, CRIMSON, VERT via MLX), deviation 3, Set D2 hand check 133/133, before any Set D2 score" || true
git push origin main || echo "PUSH FAILED - tell Claude"
echo "$(date '+%a %H:%M') waiting for Gemma on Set D2..."
while pgrep -f "which setd2 --judge gemma" >/dev/null; do sleep 60; done
step() { echo "$(date '+%a %H:%M') >>> $*"; $PY "$@" || echo "$(date '+%a %H:%M') FAILED: $* (tell Claude)"; }
step usmeta.step48 calls --which setd2 --judge llama --max-hours 6
step usmeta.step48_comparators run --model vert --which setc --max-hours 4
step usmeta.step48_comparators run --model vert --which setd2 --max-hours 4
step usmeta.step48_comparators convert --model green
step usmeta.step48_comparators run --model green --which setd2 --max-hours 6
step usmeta.step48_comparators convert --model crimson
step usmeta.step48_comparators run --model crimson --which setd2 --max-hours 8
echo "$(date '+%a %H:%M') COMPARATORS DONE (tell Claude)"
