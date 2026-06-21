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
  # Always --resume: the EXP-003c reasoning run dir already exists (it is the newest
  # EXP-003c dir), so this continues it and skips the cells already done.
  echo "=== EXP-003c reasoning tier (NIM $MODEL) attempt $attempt ==="
  date -u +"start %Y-%m-%dT%H:%M:%SZ"
  # Compaction summaries run on a fast instruct model (llama-3.1-8b); the reasoning model
  # only produces the final answer (the capability under test). This keeps the summary arms
  # tractable -- the nano's verbose chain-of-thought made self-summarizing prohibitively slow
  # (single cells wedging past 200s). Agent watchdog 120s covers the nano's answer reasoning.
  python3 -m experiments.applied --preset EXP003C --model "$MODEL" --judge --resume \
          --summarizer meta/llama-3.1-8b-instruct --agent-timeout 120 -v
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "=== complete (rc=0) after $attempt attempt(s) ==="; break; fi
  echo "=== exited rc=$rc; re-resuming in 15s ==="
  sleep 15
done
