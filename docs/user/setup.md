# Local setup

Updated 2026-10-12. Run commands from the repository root. Verify **Python 3.11+** before creating the environment; substitute an explicit compatible executable if `python3` selects an older version. Development has used CPython 3.12.12 on macOS ARM. Fresh authenticated GitHub clones on macOS ARM and Minty Linux passed installation,114 tests and both demos at e0996c1. Genuine CLI qualification is recorded at2efd0f6; final-source UI requalification passed on both hosts. See [verification](../internal/scheduling-verification.md) for the completed post-checkpoint liveCLI coverage.

```sh
git clone https://github.com/Kenerator/ochsner-scheduling-mvp.git
cd ochsner-scheduling-mvp
# The repository is public; authentication is needed only for authorized writes.
# Standard SSH alternative: git@github.com:Kenerator/ochsner-scheduling-mvp.git
python3.12 --version
python3.12 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m scheduling_assistant --help
```

The installation declares Marimo 0.25.0. The supplied scheduling service uses the Python standard library. Original intake documents and the bootstrap tool environment are not runtime prerequisites. The normal Ochsner launcher uses the trusted Bitwarden helper; the direct application entrypoints below remain environment-only alternatives.

## Normal Ochsner launch (model-first)

Run from this repository root with the project Python. Configure the **path**, not the secret value, to your already-installed trusted `bw-get-secret` helper. It must be a regular executable; do not supply a shell command. The launcher reads only **`[Env] (Ochsner PoC) OPENAI_API_KEY`**, field **`notes`**. It never substitutes an inherited `OPENAI_API_KEY` or the generic vault item.

```sh
export POC_SECRET_HELPER=/absolute/path/to/trusted/bw-get-secret.sh
export SCHEDULING_MODEL=gpt-5.4-mini
.venv/bin/python tools/poc-runtime/launch.py --help
.venv/bin/python tools/poc-runtime/launch.py --doctor
.venv/bin/python tools/poc-runtime/launch.py
```

The model name is an explicit choice, not an automatic default or availability guarantee. `--model MODEL` overrides `SCHEDULING_MODEL`; missing/invalid model configuration fails before credential lookup. CLI is the default. For Marimo:

```sh
.venv/bin/python tools/poc-runtime/launch.py --interface browser --ui-port 28180
```

The shared wrapper's browser default is **28456** if `--ui-port` is omitted. API default is **4010**; `--api-port PORT` selects a different free loopback port for its owned mock. Do not start a second API manually when using this wrapper. Occupied/duplicate ports fail safely; no foreign listener is stopped. Open the printed loopback URL yourself; the launcher does not open a browser or dashboard.

`--help` and `--doctor` retrieve no credential, start no service and make no model request. Doctor checks configuration/dependencies/helper executable/ports, not vault availability or model access. Normal startup privately resolves the scalar key, starts the unchanged synthetic API and real CLI/Marimo model host, and makes no startup model request. Only the model host receives the key; the mock receives no model/vault credentials and its raw request audit is suppressed. Ctrl-C cleans up only this launch's owned children. Cleanup failures report uncertainty; never kill another session to free a port.

There is **no interactive MVP offline mode**: `--offline` fails explicitly. Use the scripted demos below for a no-call rehearsal. Missing/locked/ambiguous credentials fail with safe guidance; they never select rehearsal or another model. Keys remain in process memory; Python cannot promise zeroization of immutable strings. Do not capture secret-bearing environments or helper output.

The [shared manifest](../../tools/poc-runtime/export-manifest.json) pins runtime1.0.0/source `b7875452`; [consumer binding](../../poc-launch.manifest.json) binds this config to the reviewed delivery `6e894645`. Consumer qualification is currently macOS ARM/Python3.12.12 with `lsof` on PATH. Linux/Windows launcher lifecycle and fresh live model/browser flows have not been qualified by this follow-on; historical application evidence retains its original date/source in [verification](../internal/scheduling-verification.md).

## Direct application entrypoints

These explicit reviewer alternatives retain the original environment-only credential contract and have no Bitwarden dependency. They do not use the managed wrapper or its owned cleanup. Start and stop your own reference service, then choose the CLI or UI below.

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
