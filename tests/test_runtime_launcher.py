"""Consumer launch qualification; fake model transport, never a vault/live call."""
import contextlib
import hashlib
import importlib
import io
import os
import socket
import subprocess
import sys
import tempfile
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scheduling_assistant import __main__ as cli
from scheduling_assistant.openai_adapter import OpenAIInterpreter
from scheduling_assistant.ui_bridge import configured_bridge
from tests.test_scheduling_ai import Response, Transport, envelope

ROOT = Path(__file__).resolve().parents[1]
CANARY = "synthetic-launch-canary"
PARENT_CANARY = "synthetic-parent-canary"


class ExistingModelConstructionTests(unittest.TestCase):
    """Catch routing to a scripted interpreter or loss of the configured model."""

    def test_cli_constructs_real_adapter_and_honors_explicit_model_override(self):
        transport = Transport(Response(envelope()))
        sessions = []
        def construct(config):
            session = cli._session(config)
            sessions.append(session)
            return session
        output, errors = io.StringIO(), io.StringIO()
        with patch("scheduling_assistant.openai_adapter.build_opener") as opener:
            opener.return_value.open = transport
            code = cli.main(["--model", "cli-override"], stdin=io.StringIO("quit\n"),
                            stdout=output, stderr=errors,
                            environ={"SCHEDULING_MODEL": "environment-model",
                                     "OPENAI_API_KEY": CANARY}, session_factory=construct)
        self.assertEqual(code, 0)
        self.assertEqual(transport.calls, [])  # Construction performs no paid request.
        self.assertIsInstance(sessions[0].interpreter, OpenAIInterpreter)
        sessions[0].interpreter.interpret("providers", {})
        request = transport.calls[0][0]
        self.assertEqual(json.loads(request.data)["model"], "cli-override")
        self.assertNotIn(CANARY, output.getvalue() + errors.getvalue())

    def test_cli_retains_environment_model_when_override_omitted(self):
        seen = []
        def construct(config):
            seen.append(config)
            return cli._session(config)
        with patch("scheduling_assistant.openai_adapter.build_opener"):
            code = cli.main([], stdin=io.StringIO("quit\n"), stdout=io.StringIO(),
                            stderr=io.StringIO(), session_factory=construct,
                            environ={"SCHEDULING_MODEL": "retained-model",
                                     "OPENAI_API_KEY": CANARY})
        self.assertEqual(code, 0)
        self.assertEqual(seen[0].model, "retained-model")

    def test_browser_constructs_real_adapter_without_startup_model_request(self):
        transport = Transport(Response(envelope()))
        with patch.dict("os.environ", {"SCHEDULING_MODEL": "browser-model",
                                       "OPENAI_API_KEY": CANARY}, clear=True), \
             patch("scheduling_assistant.openai_adapter.build_opener") as opener:
            opener.return_value.open = transport
            bridge = configured_bridge()
        self.assertIsInstance(bridge.session.interpreter, OpenAIInterpreter)
        self.assertEqual(transport.calls, [])
        bridge.session.interpreter.interpret("providers", {})
        self.assertEqual(json.loads(transport.calls[0][0].data)["model"], "browser-model")
        self.assertNotIn(CANARY, bridge.render_html())

    def test_missing_model_cannot_silently_construct_a_session(self):
        with patch("scheduling_assistant.__main__._session") as construct:
            code = cli.main([], environ={"OPENAI_API_KEY": CANARY},
                            stdout=io.StringIO(), stderr=io.StringIO())
        self.assertEqual(code, 2)
        construct.assert_not_called()


@contextlib.contextmanager
def installed_runtime():
    directory = ROOT / "tools/poc-runtime"
    if not (directory / "export-manifest.json").is_file():
        raise AssertionError("Await SM-reviewed runtime manifest; installation is pending.")
    names = ("launch", "credentials", "adapters", "processes")
    saved = {name: sys.modules.pop(name, None) for name in names}
    sys.path.insert(0, str(directory))
    try:
        yield tuple(importlib.import_module(name) for name in names)
    finally:
        sys.path.remove(str(directory))
        for name in names:
            sys.modules.pop(name, None)
            if saved[name] is not None:
                sys.modules[name] = saved[name]


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


class InstalledRuntimeContractTests(unittest.TestCase):
    def setUp(self):
        self.runtime = installed_runtime()
        self.launch, self.credentials, self.adapters, self.processes = self.runtime.__enter__()
        self.addCleanup(self.runtime.__exit__, None, None, None)
        self.config = self.launch.load_config(ROOT / "poc-launch.json")

    def test_manifest_binds_exact_reviewed_runtime_bytes(self):
        manifest = json.loads((ROOT / "tools/poc-runtime/export-manifest.json").read_text())
        self.assertEqual(manifest["source_revision"], "b7875452e3a999ca69ce170822c66e7f679b4442")
        self.assertEqual(manifest["source_worktree_state"], "clean")
        self.assertEqual(set(manifest["files"]), {
            "tools/poc-runtime/adapters.py", "tools/poc-runtime/credentials.py",
            "tools/poc-runtime/launch.py", "tools/poc-runtime/processes.py"})
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_consumer_manifest_binds_project_config_and_shared_manifest(self):
        binding = json.loads((ROOT / "poc-launch.manifest.json").read_text())
        self.assertEqual(binding["runtime_delivery_revision"], "6e89464582dd62a977aaec778c8d6f8a0adf25c7")
        self.assertEqual(set(binding["files"]), {"poc-launch.json", "tools/poc-runtime/export-manifest.json"})
        for name, digest in binding["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_default_main_selects_real_model_specs_without_inherited_key_fallback(self):
        captured = []
        def run(specs):
            captured.extend(specs)
            return 0
        with patch.dict(os.environ, {"SCHEDULING_MODEL": "configured-model", "OPENAI_API_KEY": PARENT_CANARY}), \
             patch.object(self.credentials, "resolve_key", return_value=CANARY), \
             patch.object(self.processes, "run_owned", side_effect=run):
            result = self.launch.main(["--config", str(ROOT / "poc-launch.json"),
                                       "--api-port", str(free_port())])
        self.assertEqual(result, 0)
        self.assertEqual([spec.role for spec in captured], ["mock", "model"])
        self.assertEqual(captured[1].environment["OPENAI_API_KEY"], CANARY)
        self.assertEqual(captured[1].environment["SCHEDULING_MODEL"], "configured-model")
        self.assertNotIn("OPENAI_API_KEY", captured[0].environment)

    def test_missing_model_and_interactive_offline_fail_without_fallback(self):
        for argv, env in [([], {}), (["--offline"], {}),
                          (["--model", " "], {}), ([], {"SCHEDULING_MODEL": "two names"})]:
            with self.subTest(argv=argv), self.assertRaises(self.credentials.LaunchError):
                self.launch.resolve_request(self.config, argv, env)

    def test_explicit_override_and_environment_model_are_preserved(self):
        for argv, env, expected in [([], {"SCHEDULING_MODEL": "env-model"}, "env-model"),
                                   (["--model", "override"], {"SCHEDULING_MODEL": "env-model"}, "override")]:
            request = self.launch.resolve_request(self.config, argv, env)
            self.assertEqual((request.mode, request.interface, request.model), ("model", "cli", expected))

    def specs(self, interface="cli"):
        argv = ["--model", "consumer-model", "--api-port", str(free_port())]
        if interface == "browser":
            argv += ["--interface", "browser", "--ui-port", str(free_port())]
        request = self.launch.resolve_request(self.config, argv, {})
        with patch.dict(os.environ, {"OPENAI_API_KEY": PARENT_CANARY, "BW_SESSION": "stale-session",
                                     "GITHUB_TOKEN": "stale-token"}):
            return self.adapters.process_specs(ROOT, self.config, request, key=CANARY)

    def test_cli_specs_reach_real_model_adapter_with_fake_transport(self):
        mock, model = self.specs()
        self.assertEqual(mock.role, "mock")
        self.assertEqual(model.argv[1:3], ("-m", "scheduling_assistant"))
        transport = Transport(Response(envelope()))
        output, errors = io.StringIO(), io.StringIO()
        with patch("scheduling_assistant.openai_adapter.build_opener") as opener:
            opener.return_value.open = transport
            code = cli.main(list(model.argv[3:]), environ=model.environment,
                            stdin=io.StringIO("providers\nquit\n"), stdout=output, stderr=errors)
        self.assertEqual(code, 0)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(json.loads(transport.calls[0][0].data)["model"], "consumer-model")
        self.assertNotIn(CANARY, output.getvalue() + errors.getvalue())

    def test_browser_specs_reach_real_server_side_model_adapter(self):
        mock, model = self.specs("browser")
        self.assertEqual(model.argv[1:4], ("-m", "marimo", "run"))
        self.assertIn(str(ROOT / "apps/scheduling_app.py"), model.argv)
        self.assertEqual(model.environment["SCHEDULING_API_URL"],
                         "http://127.0.0.1:" + mock.argv[-1])
        transport = Transport(Response(envelope()))
        with patch.dict(os.environ, model.environment, clear=True), \
             patch("scheduling_assistant.openai_adapter.build_opener") as opener:
            opener.return_value.open = transport
            bridge = configured_bridge()
        self.assertEqual(transport.calls, [])
        bridge.session.interpreter.interpret("providers", {})
        self.assertEqual(json.loads(transport.calls[0][0].data)["model"], "consumer-model")
        self.assertNotIn(CANARY, bridge.render_html())

    def test_only_model_child_receives_key_and_no_parent_vault_tokens_survive(self):
        for interface in ("cli", "browser"):
            specs = self.specs(interface)
            for spec in specs:
                self.assertNotIn("BW_SESSION", spec.environment)
                self.assertNotIn("GITHUB_TOKEN", spec.environment)
                self.assertNotIn(CANARY, repr(spec))
                self.assertNotIn(CANARY, " ".join(spec.argv))
                self.assertEqual("OPENAI_API_KEY" in spec.environment, spec.role == "model")
            self.assertEqual(specs[1].environment["OPENAI_API_KEY"], CANARY)

    def test_exact_notes_item_replaces_stale_inherited_key(self):
        with tempfile.TemporaryDirectory() as temp:
            helper = Path(temp) / "fake-helper"
            helper.write_text("#!/bin/sh\nexit 99\n")
            helper.chmod(0o700)
            calls = []
            def fake_run(argv, **kwargs):
                calls.append((argv, kwargs["env"]))
                return subprocess.CompletedProcess(argv, 0, CANARY, "")
            with patch.dict(os.environ, {"POC_SECRET_HELPER": str(helper), "OPENAI_API_KEY": PARENT_CANARY}):
                key = self.credentials.resolve_key(self.config["credential"], run=fake_run)
            self.assertEqual(key, CANARY)
            self.assertEqual(calls[0][0][1:], ["[Env] (Ochsner PoC) OPENAI_API_KEY", "notes"])
            self.assertNotIn("OPENAI_API_KEY", calls[0][1])
            self.assertEqual(len(calls), 1)

    def test_help_and_doctor_do_not_resolve_credentials_or_start_services(self):
        with tempfile.TemporaryDirectory() as temp:
            helper = Path(temp) / "must-not-run"
            helper.write_text("#!/bin/sh\nexit 99\n")
            helper.chmod(0o700)
            with patch.dict(os.environ, {"POC_SECRET_HELPER": str(helper)}), \
                 patch.object(self.credentials, "resolve_key", side_effect=AssertionError("vault called")), \
                 patch.object(self.processes, "run_owned", side_effect=AssertionError("service started")), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.launch.main(["--help"]), 0)
                self.assertEqual(self.launch.main(["--config", str(ROOT / "poc-launch.json"),
                    "--doctor", "--model", "doctor-model", "--api-port", str(free_port())]), 0)

    def test_occupied_port_fails_before_credentials_and_preserves_foreign_listener(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0)); listener.listen()
            port = listener.getsockname()[1]
            with patch.object(self.credentials, "resolve_key", side_effect=AssertionError("vault called")), \
                 contextlib.redirect_stderr(io.StringIO()):
                status = self.launch.main(["--config", str(ROOT / "poc-launch.json"),
                    "--model", "test-model", "--api-port", str(port)])
            self.assertEqual(status, 2)
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass

    def test_actual_owned_vendor_and_cli_start_and_exit_without_model_call(self):
        specs = self.specs()
        children = []
        def spawn(argv, **kwargs):
            # EOF exits the real CLI before any user/model request.
            if "scheduling_assistant" in argv:
                kwargs["stdin"] = subprocess.DEVNULL
                kwargs["stdout"] = subprocess.DEVNULL
                kwargs["stderr"] = subprocess.DEVNULL
            child = subprocess.Popen(argv, **kwargs)
            children.append(child)
            return child
        self.assertEqual(self.processes.run_owned(specs, popen=spawn), 0)
        self.assertEqual(len(children), 2)
        self.assertTrue(all(child.poll() is not None for child in children))

    def test_cancellation_after_mock_readiness_reaps_only_owned_mock(self):
        children = []
        def spawn(argv, **kwargs):
            if "scheduling_assistant" in argv:
                raise KeyboardInterrupt()
            child = subprocess.Popen(argv, **kwargs)
            children.append(child)
            return child
        with self.assertRaises(KeyboardInterrupt):
            self.processes.run_owned(self.specs(), popen=spawn)
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())


if __name__ == "__main__":
    unittest.main()
