# Local setup

Updated 2026-10-09. Run commands from the repository root. Verify **Python 3.11+** before creating the environment; substitute an explicit compatible executable if `python3` selects an older version. Development has used CPython 3.12.12 on macOS ARM. Fresh authenticated GitHub clones on macOS ARM and Minty Linux passed installation,114 tests and both demos at e0996c1. Genuine CLI qualification is recorded at2efd0f6; final-source UI requalification passed on both hosts. See [verification](../internal/scheduling-verification.md) for the completed post-checkpoint liveCLI coverage.

```sh
git clone https://github.com/Kenerator/ochsner-scheduling-mvp.git
cd ochsner-scheduling-mvp
# Authenticate with an account granted access to this private repository.
# Standard SSH alternative: git@github.com:Kenerator/ochsner-scheduling-mvp.git
python3.12 --version
python3.12 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m scheduling_assistant --help
```

The installation declares Marimo 0.25.0. The supplied scheduling service uses the Python standard library. Original intake documents, the bootstrap tool environment and Bitwarden are not runtime prerequisites.

## Check local ports

Before starting either service, check that API port **4010** and UI port **28180** are free:

```sh
.venv/bin/python - <<'PY'
import socket
for port in (4010, 28180):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', port))
        print(f'127.0.0.1:{port} is available')
PY
```

An address-in-use error means inspect the listener and coordinate ownership. Never kill an unrelated process. This check releases both ports; a later bind can still fail if another process starts meanwhile.

Start the reference API in its own terminal:

```sh
.venv/bin/python vendor/scheduling-reference/mock-api/server.py --port 4010
```

It binds `127.0.0.1` and holds synthetic appointments in memory. Keep this process visible so its ownership is clear.

## Configure live AI

Set `OPENAI_API_KEY` in the launch process using your normal local secret handling. Do not put the value in source, shell command arguments, URLs, screenshots or committed files. The application reads this environment variable directly and has no credential-store dependency. Then select the model explicitly:

```sh
export SCHEDULING_MODEL=gpt-5.4-mini
export SCHEDULING_API_URL=http://127.0.0.1:4010
```

The named model is the qualification target, not an automatic fallback. Account/model access and network connectivity are required for live conversation. Missing configuration fails safely; `--help` makes no model call.

CLI, in the configured environment:

```sh
.venv/bin/python -m scheduling_assistant --model gpt-5.4-mini \
  --api-base-url http://127.0.0.1:4010
```

`--api-url` is an alias. CLI also accepts `SCHEDULING_MODEL` when `--model` is omitted. For a clearly labeled outage exercise, add `--scenario api_failure`.

UI, in a separate terminal with the same environment:

```sh
.venv/bin/marimo run apps/scheduling_app.py --headless \
  --host 127.0.0.1 --port 28180
```

Open the URL printed by Marimo in the controlled Codex in-app browser for qualification. `--headless` prevents automatic browser launch. The UI reads `SCHEDULING_API_URL`; the CLI URL is set by its argument. Provider, booking with decline/separate consent/repeat guard, and no-match were exercised in controlled IAB on macOS ARM. Both fresh-clone hosts passed final-source UI rehearsal; exact revisions and the completed post-checkpoint CLI coverage are in [verification](../internal/scheduling-verification.md).

## Verification and reset

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario success
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario failure
```

Demos use isolated owned reference services and scripted interpretation, with no API key. Live AI/browser checks are separate. See [usage](usage.md) for synthetic inputs and safety behavior.

`reset` clears conversation/identity/consent, not an unresolved booking effect. Restart only your owned API process to restore its synthetic fixtures. Restarting the assistant loses process-local protection and does not establish whether a previously dispatched booking succeeded. Ask clinic scheduling staff to verify an unknown outcome before retrying.
