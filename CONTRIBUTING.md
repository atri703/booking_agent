# Contributing

Use Python 3.12 and `uv sync --locked --all-extras`. Follow AGENTS.md. Branch from the current default branch (`master`), make a focused change, update its specification and regression coverage, and open a pull request explaining the user-visible behavior and validation.

Do not include `.env`, runtime JSON, customer data or generated evaluation transcripts in commits. Maintain the JSON/SQLite adapter parity suite and regenerate Agent Card/eval exports when their source changes. Paid live evaluations are explicitly invoked and never required for an ordinary unauthenticated clone.

The project uses Ruff for lint/format, pytest for deterministic tests, ADK Eval for model/tool behavior, and Google Agents CLI for synthetic multi-turn conversations. See docs/EVALUATION.md for the distinction.
