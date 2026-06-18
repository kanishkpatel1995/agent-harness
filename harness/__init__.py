"""agent-harness: a minimal, readable agent harness built to teach context engineering.

Public surface:
    from harness import build_agent, FakeLLM, LLMClient
"""

from .agent import build_agent
from .budget import Budget, BudgetExceeded
from .context import ContextManager
from .fake_llm import FakeLLM
from .llm import LLMClient
from .loop import run_agent, run_agent_safe
from .memory import Scratchpad
from .tools import ToolRegistry
from .trace import Trace

__all__ = [
    "build_agent",
    "FakeLLM",
    "LLMClient",
    "ContextManager",
    "Budget",
    "BudgetExceeded",
    "Scratchpad",
    "ToolRegistry",
    "Trace",
    "run_agent",
    "run_agent_safe",
]
