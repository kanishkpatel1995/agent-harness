"""LLM judge for FRAMES answers.

Given (question, model answer, gold answer), return 1 if the model answer is
correct (allowing paraphrase and formatting differences), else 0. We use a strong
model for the solid run. LLM judges carry position and verbosity biases (Zheng et
al., 2306.05685), so for the solid run we validate the judge against the gold
substring match on a sample and report agreement.
"""

from __future__ import annotations

from experiments.bench.logsetup import get

log = get("judge")

JUDGE_SYS = (
    "You grade a candidate answer against the gold answer for a research question. "
    "Reply with exactly one word: CORRECT if the candidate states the gold answer "
    "(allowing paraphrase, synonyms, and formatting differences), otherwise INCORRECT."
)


def judge(llm, question, answer, gold):
    r = llm.complete([
        {"role": "system", "content": JUDGE_SYS},
        {"role": "user", "content": f"Question: {question}\nGold answer: {gold}\n"
                                    f"Candidate answer: {answer}\nVerdict (CORRECT or INCORRECT):"},
    ], stage="judge")
    v = (r.content or "").strip().upper()
    correct = ("CORRECT" in v) and ("INCORRECT" not in v)
    return int(correct), r.usage
