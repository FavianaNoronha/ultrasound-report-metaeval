#!/bin/bash
# Waits for the running Llama job to stop (its 9-hour cap), then resumes it until all 1,770 rows are done.
# Run from ~/medical-imaging-ai in a NEW Terminal tab:  bash usmeta/results/partA/step48_confirm/run_after_llama.sh
cd ~/medical-imaging-ai || exit 1
echo "$(date '+%H:%M') waiting for the current Llama run to stop..."
while pgrep -f "usmeta.step48 llama-setc" >/dev/null; do sleep 60; done
echo "$(date '+%H:%M') first run stopped; resuming"
for i in 1 2 3; do
  caffeinate -i env PYTHONPATH=usmeta .venv/bin/python -m usmeta.step48 llama-setc --max-hours 8 && break
  echo "$(date '+%H:%M') run exited with an error; retry $i in 2 minutes"; sleep 120
done
echo "$(date '+%H:%M') LLAMA SET C DONE"
