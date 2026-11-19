# Run and test locally

This guide starts the booking agent from a fresh clone. Run every command from the repository root (the directory containing `pyproject.toml`). The application is a single-user local demo; keep it bound to `127.0.0.1` and use one server worker.

## 1. Install the prerequisites

Install Git and [`uv`](https://docs.astral.sh/uv/getting-started/installation/). This project supports Python 3.11, 3.12, or 3.13; install the recommended Python 3.12 through `uv`, then confirm everything is available:

```powershell
uv --version
git --version
uv python install 3.12
uv python list
```

Note - (if "uv python install 3.12" shows error try this instead "uv python install 3.12 --native-tls")

On Windows, the official standalone installer command is:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen the terminal after installing `uv` if it is not immediately found, then run `uv python install 3.12`. If a compatible Python is already installed, `uv` can detect and use it, but the explicit command makes a fresh-machine setup predictable.

## 2. Clone and install the project

```powershell
git clone https://github.com/atri703/booking_agent.git
cd booking_agent
uv sync --locked --all-extras
```

`uv sync` creates the local `.venv` and installs the exact locked dependencies. Use `uv run --no-sync ...` for the remaining commands so they run in that environment without changing the lock file.

## 3. Create the local `.env` file

Copy the tracked template to the ignored local file:

```powershell
Copy-Item .env.example .env
notepad .env
```

On macOS or Linux, use `cp .env.example .env` and open it in your editor. Put a real key only in `.env`—never in `.env.example`, documentation, a commit, terminal output, or a screenshot.

For **OpenRouter**, use this minimal configuration and replace only the placeholder value:

```dotenv
OPENAI_API_KEY=
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY_HERE
BOOKING_MODEL=openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
```

For the default **OpenAI GPT-5.2** path instead, use:

```dotenv
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
OPENROUTER_API_KEY=
BOOKING_MODEL=openai/gpt-5.2
```

Only the key for the selected provider is required. Saving `.env` is enough because the application loads it automatically; restart the server after changing it. Verify that Git ignores the file without displaying its contents:

```powershell
git check-ignore .env
```

The command should print `.env`. If it does not, stop and do not commit the key. Chat needs a provider key, but the browser CRUD workflow and all ordinary offline tests work without one.

## 4. Run a keyless smoke test

This exercises create, read, update, and delete against a temporary JSON file and never changes `runtime/`:

```powershell
uv run --no-sync python -m scripts.demo_crud
```

## 5. Start the local server

```powershell
uv run --no-sync uvicorn booking_agent.server:app --host 127.0.0.1 --port 8001
```

Leave this terminal running. Open these URLs:

- Application: <http://127.0.0.1:8001>
- Health check: <http://127.0.0.1:8001/health>
- REST API documentation: <http://127.0.0.1:8001/docs>

The health response should report `status: ok`, `storage: json`, and `mode: single-user-local-demo`. Stop the server with `Ctrl+C`.

## 6. Manual booking test without a model call

1. Open <http://127.0.0.1:8001>.
2. Under **Test without an API key**, enter a test name.
3. Select a future weekday within 90 days. Business hours are 09:00–17:00 in `Asia/Kolkata` by default.
4. Select 30 or 60 minutes and click **Find available slots**.
5. Choose a returned slot and click **Prepare booking**.
6. Check the exact details under **Review proposed change**. At this point no booking has been saved.
7. Click **Confirm this exact change**, then click **Refresh** under **Your bookings**.

The confirmed booking is stored in `runtime/bookings.json`. Conversation history from chat is stored separately in `runtime/sessions.json`. These runtime files are local and Git-ignored; do not commit them.

To test rescheduling, choose another available slot and click **Reschedule** beside the booking, review the new proposal, and confirm it. To test cancellation, click **Cancel**, review the proposal, and confirm it. Merely saying “yes” in chat never commits a change.

## 7. Manual chat test with OpenRouter or OpenAI

Start the server after saving `.env`, open the **Chat** section, and send a message like this after replacing the date:

```text
Find an available 30-minute consultation on YYYY-MM-DD and prepare a booking for Local Test User.
```

Use a future weekday within 90 days. A successful response should use the availability and proposal tools and show a pending proposal; inspect it and use the UI confirmation button to save it. Refresh **Your bookings** and inspect `runtime/bookings.json` to verify the result.

If chat returns `503`, confirm that `BOOKING_MODEL` and its matching key are both present in `.env`, then restart the server. OpenRouter models can also be temporarily unavailable or rate-limited even when the local setup is correct.

## 8. Run automated offline checks

These commands do not call OpenAI, OpenRouter, or Google services:

```powershell
uv run --no-sync ruff check booking_agent coordinator eval_agent scripts tests
uv run --no-sync ruff format --check booking_agent coordinator eval_agent scripts tests
uv run --no-sync python -m pytest -q
uv run --no-sync python -m scripts.demo_crud
uv run --no-sync python -m scripts.run_adk_eval --offline
uv run --no-sync python -m scripts.build_eval_sets
uv run --no-sync python -m scripts.export_agent_card
```

The offline ADK evaluation uses a scripted model. It checks framework/tool wiring but does not prove that a live provider model behaves correctly.

For a quicker focused check of provider selection and credential handling, run:

```powershell
uv run --no-sync python -m pytest -q tests/test_model_config.py
```

## 9. Run one live model evaluation intentionally

This command makes a real request to the provider selected in `.env`. It runs only the reviewed `create_30` case, uses isolated temporary JSON storage, and must leave bookings unchanged because evaluation never performs client confirmation:

```powershell
uv run --no-sync python -m scripts.run_adk_eval --case create_30
```

The result is written to `artifacts/adk-live.json`; a failure returns a nonzero exit code. Do not use `--judge` unless Google model credentials and billing are intentionally configured—the judge is separate from the OpenAI/OpenRouter model under test.

## 10. Common problems

- **No slots:** choose a future Monday–Friday within 90 days and ensure the appointment ends by 17:00.
- **Port 8001 already in use:** stop the older server process before starting another one.
- **Chat says a key is missing:** the selected `openrouter/...` model requires `OPENROUTER_API_KEY`; other configured models use `OPENAI_API_KEY`.
- **Booking is not in JSON:** preparing a proposal is not enough; confirm the exact proposal in the UI.
- **401 Unauthorized:** leave `BOOKING_API_TOKEN` empty for the basic local run, or enter the same configured token in the browser.
- **Corrupt JSON:** stop the server and restore a known backup. The application deliberately does not erase or silently reset corrupt data.
