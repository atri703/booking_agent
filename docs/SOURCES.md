# Sources and dependency compatibility

Official documentation/source checked during implementation on 2026-11-18. Exact installed package APIs were inspected and exercised where tutorial examples differed.

| Component | Pinned version | Source |
|---|---|---|
| Google ADK | 2.14.1 | https://adk.dev/ and https://github.com/google/adk-python |
| A2A Python SDK | 1.3.1 | https://github.com/a2aproject/a2a-python |
| ADK A2A adapter | Included in ADK | https://adk.dev/a2a/quickstart-exposing/ |
| ADK Python OpenAI integration | LiteLLM 1.109.1 | https://adk.dev/agents/models/openai/ |
| OpenAI model | gpt-5.2 | https://developers.openai.com/api/docs/models/gpt-5.2 |
| ADK Eval | ADK eval extra | https://adk.dev/evaluate/ and https://adk.dev/evaluate/criteria/ |
| Google Agents CLI | 1.15.0 | https://google.github.io/agents-cli/guide/evaluation/ |
| Synthetic generation | Same CLI | https://github.com/google/agents-cli/blob/main/skills/google-agents-cli-eval/references/user-simulation.md |
| Dataset format | Google SDK schema | https://github.com/google/agents-cli/blob/main/skills/google-agents-cli-eval/references/dataset_schema.md |
| Spec Kit | specify-cli 1.4.2 | https://github.com/github/spec-kit and https://github.github.io/spec-kit/installation.html |
| FastAPI | 0.164.0 | https://fastapi.tiangolo.com/tutorial/testing/ |
| SQLite adapter | Python standard library | https://docs.python.org/3/library/sqlite3.html |
| uv CI | uv 0.13.9 | https://docs.astral.sh/uv/guides/integration/github/ |

Full transitive versions/hashes are in uv.lock. Re-evaluate model/provider/CLI behavior before upgrading; do not assume changing one package preserves generated schemas.

Spec Kit's installed `.specify`, `.agents/skills` and `.claude/skills` assets originate from GitHub Spec Kit, licensed MIT. Preserve their notices and upstream attribution. The repository's original MIT LICENSE is retained.
