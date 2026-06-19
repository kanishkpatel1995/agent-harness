"""Applied compaction bake-off (EXP-003): a real research agent answers FRAMES
multi-hop questions under different context-compaction policies, scored by
end-task accuracy per token.

Design note: we use ORACLE retrieval (fetch the question's gold Wikipedia
articles) to isolate the compaction policy from web-search quality. The articles
overflow the window, so compaction must fire; the metric is whether the agent
answers correctly, by policy.

Run:  python -m experiments.applied -v
"""
