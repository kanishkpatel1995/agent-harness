"""The agent loop.

This is the whole loop. It is deliberately small: ~40 lines of real logic.

The talk's thesis lives here. The loop is trivial. Everything that makes a
long-running agent *not fall apart* lives in the things the loop calls into:
the ContextManager (what the model sees), the Budget (when to stop), the
Scratchpad (memory that lives outside the window), and the Trace (so you can
watch it happen). Read this file first, then read context.py.
"""

from __future__ import annotations

from .budget import Budget, BudgetExceeded
from .context import ContextManager
from .tools import ToolRegistry
from .trace import Trace


def run_agent(
    llm,
    context: ContextManager,
    tools: ToolRegistry,
    budget: Budget,
    trace: Trace,
    max_steps: int = 40,
) -> str:
    """Run the agent until it calls finish(), runs out of budget, or hits max_steps.

    Returns the final answer string.
    """
    for step in range(1, max_steps + 1):
        budget.check_step()
        trace.step_start(step, context, budget)

        # 1. Ask the model what to do next, given the CURRENT context window.
        response = llm.complete(context.messages(), tools=tools.schemas())
        budget.record_usage(response.usage, llm.model)

        # 2. No tool call => the model is talking, not acting. We're done.
        if not response.tool_calls:
            context.add_assistant(response.content or "")
            trace.final(response.content or "", budget)
            return response.content or ""

        # 3. Record the model's decision, then run each requested tool.
        context.add_assistant(response.content, tool_calls=response.tool_calls)
        for call in response.tool_calls:
            trace.tool_call(call)
            if call["name"] == "finish":
                answer = call["arguments"].get("report", "")
                context.add_tool_result(call["id"], "ok")
                trace.final(answer, budget)
                return answer
            result = tools.dispatch(call["name"], call["arguments"])
            context.add_tool_result(call["id"], result)
            trace.tool_result(call["name"], result)

        # 4. The one line that keeps a long run alive: prune/summarize the
        #    context window if it has grown past its budget.
        compacted = context.maybe_compact(llm)
        if compacted:
            trace.compaction(compacted, context)

    trace.note(f"Hit max_steps={max_steps} without finishing.")
    return context.last_assistant_text() or "(no answer: ran out of steps)"


def run_agent_safe(*args, **kwargs) -> str:
    """Same as run_agent but turns a blown budget into a graceful return.

    A real harness should never crash the process because the agent got
    expensive. It should stop, report what it has, and let the caller decide.
    """
    try:
        return run_agent(*args, **kwargs)
    except BudgetExceeded as exc:
        trace = kwargs.get("trace") or (args[4] if len(args) > 4 else None)
        if trace:
            trace.note(f"Budget exceeded: {exc}")
        context = kwargs.get("context") or args[1]
        return context.last_assistant_text() or f"(stopped early: {exc})"
