#!/bin/sh
# EXP-003c launcher: the model axis. Runs the five separating arms from EXP-003b on a
# strong instruct model and a reasoning model, sequentially, under caffeinate so the
# Mac does not sleep mid-run. Each invocation creates its own EXP-003c run dir.
# Arm 1 (the safe, high-value 70b) runs first, so it completes even if the reasoning
# arm misbehaves. Idempotent-ish: re-running creates fresh run dirs.
set -e
REPO="/Users/kanishk/Desktop/agent-harness/.claude/worktrees/sleepy-sinoussi-00c73b"
cd "$REPO"

echo "=== EXP-003c arm 1/2: meta/llama-3.3-70b-instruct (strong instruct) ==="
date -u +"start %Y-%m-%dT%H:%M:%SZ"
python3 -m experiments.applied --preset EXP003C -v

echo "=== EXP-003c arm 2/2: nvidia/llama-3.3-nemotron-super-49b-v1.5 (reasoning) ==="
date -u +"start %Y-%m-%dT%H:%M:%SZ"
python3 -m experiments.applied --preset EXP003C --model nvidia/llama-3.3-nemotron-super-49b-v1.5 -v

echo "=== EXP-003c complete ==="
date -u +"done %Y-%m-%dT%H:%M:%SZ"
