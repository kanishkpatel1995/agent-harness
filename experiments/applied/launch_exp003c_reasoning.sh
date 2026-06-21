#!/bin/sh
# EXP-003c reasoning tier on NIM (nemotron-3-nano-30b, a fast reasoning MoE), judge on
# NIM 70b for consistency with the 8b/70b tiers. Auto-restart with --resume so a crash,
# a hung endpoint, or the Mac sleeping loses at most the one in-flight cell (each finished
# cell is flushed to results.csv immediately). Loops until the sweep exits 0.
set -u
REPO="/Users/kanishk/Desktop/agent-harness/.claude/worktrees/sleepy-sinoussi-00c73b"
cd "$REPO"
MODEL="nvidia/nemotron-3-nano-30b-a3b"

attempt=0
while : ; do
  attempt=$((attempt + 1))
  if [ "$attempt" -eq 1 ]; then RESUME=""; else RESUME="--resume"; fi
  echo "=== EXP-003c reasoning tier (NIM $MODEL) attempt $attempt $RESUME ==="
  date -u +"start %Y-%m-%dT%H:%M:%SZ"
  python3 -m experiments.applied --preset EXP003C --model "$MODEL" --judge $RESUME -v
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "=== complete (rc=0) after $attempt attempt(s) ==="; break; fi
  echo "=== exited rc=$rc; re-resuming in 15s ==="
  sleep 15
done
