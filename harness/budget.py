"""Budget: the answer to 'when does the agent stop?'

An unguarded agent has three ways to run away from you: too many steps (loops),
too many tokens (cost + latency), and too many dollars. This tracks all three
and raises BudgetExceeded the moment any cap is crossed. The loop catches it.

Costs are approximate. litellm can give exact per-model costs; we keep a tiny
price table as a fallback so the demo works fully offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# USD per 1K tokens (input, output). Rough, for offline estimation only.
_PRICES = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-5-haiku": (0.0008, 0.004),
    "fake": (0.0, 0.0),
}


class BudgetExceeded(Exception):
    pass


@dataclass
class Budget:
    max_steps: int = 40
    max_tokens: int = 200_000
    max_usd: float = 1.00

    steps: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    usd: float = 0.0
    _history: list = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def check_step(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise BudgetExceeded(f"max_steps={self.max_steps} reached")

    def record_usage(self, usage: dict, model: str):
        pin = usage.get("prompt_tokens", 0) or 0
        pout = usage.get("completion_tokens", 0) or 0
        self.prompt_tokens += pin
        self.completion_tokens += pout
        self.usd += self._cost(model, pin, pout)
        self._history.append({"step": self.steps, "in": pin, "out": pout, "usd": round(self.usd, 4)})

        if self.total_tokens > self.max_tokens:
            raise BudgetExceeded(f"token cap {self.max_tokens} exceeded ({self.total_tokens})")
        if self.usd > self.max_usd:
            raise BudgetExceeded(f"cost cap ${self.max_usd:.2f} exceeded (${self.usd:.4f})")

    def _cost(self, model: str, pin: int, pout: int) -> float:
        key = next((k for k in _PRICES if k in (model or "")), "fake")
        cin, cout = _PRICES[key]
        return (pin / 1000) * cin + (pout / 1000) * cout

    def summary(self) -> str:
        return (
            f"steps={self.steps}/{self.max_steps}  "
            f"tokens={self.total_tokens:,}  "
            f"est_cost=${self.usd:.4f}/${self.max_usd:.2f}"
        )
