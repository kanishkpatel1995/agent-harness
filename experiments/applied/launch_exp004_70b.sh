#!/bin/sh
# EXP-004 LoCoMo, 70b tier: the conversational-memory bake-off on the large instruct model
# (judge held at 70b, consistent with the 8b tier). Auto-restart with --resume so a crash,
# a hung endpoint, or the Mac sleeping loses at most the one in-flight cell. Loops until rc=0.
set -u
REPO="/Users/kanishk/Desktop/agent-harness/.claude/worktrees/sleepy-sinoussi-00c73b"
cd "$REPO"
MODEL="meta/llama-3.3-70b-instruct"

attempt=0
while : ; do
  attempt=$((attempt + 1))
  # Always --resume after the first attempt; the new 70b run dir is the newest EXP-004 dir.
  if [ "$attempt" -eq 1 ]; then RESUME=""; else RESUME="--resume"; fi
  echo "=== EXP-004 LoCoMo (70b, judged) attempt $attempt $RESUME ==="
  date -u +"start %Y-%m-%dT%H:%M:%SZ"
  python3 -m experiments.applied.locomo_runner --model "$MODEL" --n-conv 10 --q-per-conv 10 \
          --judge $RESUME -v
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "=== complete (rc=0) after $attempt attempt(s) ==="; break; fi
  echo "=== exited rc=$rc; resuming in 15s ==="
  sleep 15
done
