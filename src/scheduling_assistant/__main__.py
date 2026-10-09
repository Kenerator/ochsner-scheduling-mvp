"""Thin terminal adapter; Session owns every scheduling decision and effect."""
import argparse
from dataclasses import dataclass, field
import os
import sys
from time import monotonic
from uuid import uuid4


@dataclass(frozen=True)
class Configuration:
    model: str
    api_base_url: str
    scenario: str | None
    api_key: str = field(repr=False)


class ConfigurationError(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse otherwise echoes arbitrary input, which may be sensitive.
        raise ConfigurationError('Invalid arguments. Use --help for supported options.')


def _session(config):
    from .diagnostics import Diagnostics
    from .openai_adapter import OpenAIInterpreter
    from .scheduling_api import SchedulingAPI
    from .session import Session
    return Session(SchedulingAPI(config.api_base_url, scenario=config.scenario),
                   OpenAIInterpreter(config.model, api_key=config.api_key), diagnostics=Diagnostics())


def main(argv=None, *, stdin=None, stdout=None, stderr=None, environ=None,
         session_factory=None, clock=monotonic):
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    environ = os.environ if environ is None else environ
    parser = _Parser(description='AI scheduling assistant — synthetic local demonstration.', add_help=False)
    parser.add_argument('--help', '-h', action='store_true', help='Show help without connecting.')
    parser.add_argument('--model', help='Explicit Responses model; or set SCHEDULING_MODEL.')
    parser.add_argument('--api-base-url', '--api-url', default='http://127.0.0.1:4010', help='Loopback supplied scheduling API.')
    parser.add_argument('--scenario', choices=['api_failure'], help='Explicit synthetic failure scenario.')
    try:
        args = parser.parse_args(argv)
        if args.help:
            parser.print_help(file=stdout)
            return 0
        model = args.model if args.model is not None else environ.get('SCHEDULING_MODEL')
        if not isinstance(model, str) or not model.strip():
            raise ConfigurationError('Set --model or SCHEDULING_MODEL explicitly.')
        key = environ.get('OPENAI_API_KEY')
        if not isinstance(key, str) or not key.strip() or '\n' in key or '\r' in key:
            raise ConfigurationError('Set OPENAI_API_KEY in the process environment.')
        config = Configuration(model.strip(), args.api_base_url, args.scenario, key)
        session = (session_factory or _session)(config)
    except ConfigurationError as error:
        print(str(error), file=stderr)
        return 2
    except Exception:
        print('The assistant could not start. Check model and local API configuration.', file=stderr)
        return 2
    print(session.current_view.text, file=stdout, flush=True)
    print('Enter a scheduling request. Commands: reset, quit. Synthetic data only.', file=stdout, flush=True)
    if args.scenario:
        print('Synthetic service scenario: api_failure.', file=stdout, flush=True)
    try:
        while True:
            print('You> ', end='', file=stdout, flush=True)
            line = stdin.readline()
            if not line:
                break
            utterance = line.strip()
            if utterance.lower() in ('quit', 'exit'):
                break
            if not utterance:
                continue
            print('Processing…', file=stdout, flush=True)
            started = clock()
            view = session.submit(utterance, uuid4().hex, expected_revision=session.revision)
            print(view.text, file=stdout, flush=True)
            print(f'Elapsed: {max(0, clock() - started) * 1000:.0f} ms.', file=stdout, flush=True)
    except KeyboardInterrupt:
        print('\nInterrupted. A dispatched booking outcome may be unknown. Do not retry; ask clinic scheduling staff to verify.', file=stderr)
        return 130
    except Exception:
        print('The session stopped safely. If a booking was dispatched, its outcome may be unknown. Do not retry; ask clinic scheduling staff to verify.', file=stderr)
        return 1
    print('Session ended. Exiting does not resolve an unknown booking outcome.', file=stdout, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
