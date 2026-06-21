#!/bin/sh
# EXP-003c reasoning tier, run LOCALLY via LM Studio (qwen3.5-9b) with bulletproof
# checkpointing. Before every attempt it re-ensures the LM Studio server is up and the
# model is loaded with our FIXED context length, then runs the sweep with --resume.
# Because each finished cell is flushed to results.csv immediately, a crash, an LM Studio
# unload, or the Mac sleeping loses at most the one in-flight cell, never the whole run.
# Loops until the sweep exits 0 (all cells done). The judge stays on NIM (70b) so the
# metric is held constant across the 8b/70b/reasoning tiers.
set -u
REPO="/Users/kanishk/Desktop/agent-harness/.claude/worktrees/sleepy-sinoussi-00c73b"
LMS="$HOME/.lmstudio/bin/lms"
MODEL_KEY="qwen/qwen3.5-9b"     # what lms loads from disk
MODEL_ID="qwen3.5-9b"          # stable API identifier we always reuse
CTX=16384                      # fixed context length, set on every (re)load
API_BASE="http://localhost:1234/v1"
cd "$REPO"

attempt=0
while : ; do
  attempt=$((attempt + 1))
  echo "=== attempt $attempt: ensure LM Studio server + model @ ctx $CTX ==="
  "$LMS" server start >/dev/null 2>&1
  if ! "$LMS" ps 2>/dev/null | grep -q "$MODEL_ID"; then
    echo "model not loaded; loading $MODEL_KEY (id=$MODEL_ID) @ ctx $CTX"
    "$LMS" load "$MODEL_KEY" --context-length "$CTX" --gpu max -y --identifier "$MODEL_ID" >/dev/null 2>&1
  fi

  # First attempt starts a fresh run dir; later attempts resume it (it is the newest
  # EXP-003c dir, so --resume targets it). This avoids resuming into a stale dir.
  if [ "$attempt" -eq 1 ]; then RESUME=""; else RESUME="--resume"; fi

  echo "=== attempt $attempt: run sweep (local agent + NIM judge) $RESUME ==="
  python3 -m experiments.applied --preset EXP003C --model "$MODEL_ID" \
          --api-base "$API_BASE" --judge $RESUME -v
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "=== sweep complete (rc=0) after $attempt attempt(s) ==="
    break
  fi
  echo "=== sweep exited rc=$rc; re-ensuring server/model and resuming in 20s ==="
  sleep 20
done
