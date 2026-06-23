"""Adapters that wrap real open-source memory systems behind the Policy interface.

Each adapter implements the same `compact(old, llm, store)` (or backs the `store`)
so a famous memory system becomes just another bench arm — measured head-to-head
against the hand-rolled policies. All imports are guarded: an adapter only loads
if its library is installed, so the core package stays dependency-free.

    langchain_summary  — LangChain ConversationSummaryBufferMemory  (compact)
    mem0_store         — Mem0 extract->update memory                (externalize)
    letta_store        — Letta / MemGPT archival memory             (externalize / isolate)
    chroma_store       — Chroma + sentence-transformers store        (the externalize backend)
"""
