"""Compaction bake-off bench: a config-driven, logged, scalable experiment for
comparing context-compaction policies under varying token budgets, with a
no-compaction baseline and a model-max-window failure mode.

Entry point:  python -m experiments.bench -vv        (dev sweep, full logs)
              python -m experiments.bench --full      (70b sweep)
"""
