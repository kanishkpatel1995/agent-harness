# EXP-004 — locomo-transfer

**Hypothesis:** The FRAMES compaction ranking transfers to conversational memory: under high compaction pressure, structure and retrieval preserving policies (importance, semantic, reversible-hybrid, externalize) preserve more LoCoMo QA accuracy than truncation, because conversational questions hinge on specific facts scattered across early sessions that blind truncation drops.

**Assumptions:**
- The agent reads all sessions of a conversation (oracle), so there is no retrieval-quality confound.
- Each conversation's sessions (tens of thousands of chars) overflow the 1500-token budget and force many compactions.
- The conversation is compacted once per policy; the same window answers every sampled question (amortized compaction).
- The 70b LLM judge credits paraphrase and date-format differences in short conversational answers.
- 8b is a dev model; the solid run repeats on the 70b.

Run `20260622-0233` · git `68256be` · model `meta/llama-3.3-70b-instruct`

## Results

_Fill in after analysis: did the hypothesis hold? strongest threat?_
