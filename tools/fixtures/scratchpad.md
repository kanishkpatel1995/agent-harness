# Externalize memory: the scratchpad pattern

The single highest-leverage move for a long-running agent is to stop using the
context window as storage. Give the agent a place to write things down, and keep
only what it needs for the next step in the window itself.

## The pattern

1. The agent reads a source, runs a query, or reaches a conclusion.
2. It immediately writes the durable part to an external store — a `notes.md`
   file, a database row, a vector index entry.
3. The window keeps a short pointer ("saved finding #4") rather than the full
   text.
4. When the agent needs detail later, it reads the store back on demand.

The window now holds a working set, not an archive. You can run for hundreds of
steps without the context growing, because the growth happens on disk.

## Why this beats bigger windows and better summarization

- **It's lossless.** Summarization throws away detail; the scratchpad keeps it.
- **It's inspectable.** You can open the file mid-run and see exactly what the
  agent "knows." This is gold for debugging and for demos.
- **It survives compaction.** When you drop old turns, nothing important
  vanished — it was written down. Compaction becomes a safe, routine operation.
- **It composes with retrieval.** A flat file works for small runs; swap in a
  vector store when you need semantic recall over thousands of notes.

## Making the agent actually use it

Agents won't take notes unless the harness nudges them:

- Put a rule in the system prompt: "After anything useful, save_note it. Do not
  rely on remembering raw text; the conversation will be compacted."
- Make note-taking a first-class tool, not a side effect.
- Have a `read_notes` tool and instruct the agent to call it before producing a
  final answer, so the report is built from the full record rather than whatever
  happened to survive in the window.

## Failure modes

- **Vague notes.** "Found some useful stuff" is worthless. Prompt for concrete
  claims, numbers, and source URLs.
- **Write-only memory.** If the agent never reads notes back, they don't help.
  The `read_notes`-before-finish step fixes this.
- **No structure at scale.** A single flat file is fine for a 30-step run; for
  long-lived agents, tag or index notes so retrieval stays precise.
