#!/usr/bin/env python3
"""Synthetic HTTP integration demo; scripted interpretation is not live AI evidence."""
import argparse
import importlib.util
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit
from scheduling_assistant.domain import ActionLedger
from scheduling_assistant.interpretation import Interpretation
from scheduling_assistant.scheduling_api import SchedulingAPI
from scheduling_assistant.session import Session

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class SuppliedServer:
    """Fresh independent reference service; never binds shared demo ports."""
    def __enter__(self):
        source = ROOT / 'vendor/scheduling-reference/mock-api/server.py'
        spec = importlib.util.spec_from_file_location('demo_reference', source)
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        self.events = []
        events = self.events
        class Handler(reference.Handler):
            store = reference.Store()
            def respond(self, status, payload):
                events.append((self.command, urlsplit(self.path).path, status))
                super().respond(status, payload)
            def audit(self, *args):
                pass
        self.server = reference.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = Thread(target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()
        self.base_url = 'http://127.0.0.1:' + str(self.server.server_port)
        return self
    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        require(not self.thread.is_alive(), 'Owned reference service did not stop')


class ScriptedInterpreter:
    """Explicit test double: no model calls or natural-language interpretation claim."""
    def __init__(self):
        self.answers = []
    def interpret(self, text, context):
        return self.answers.pop(0)


def run(scenario):
    print('SIMULATED INTERPRETER + ACTUAL SUPPLIED HTTP scheduling integration demo')
    print('Synthetic fixtures only. Not live AI qualification; no real appointment.')
    with SuppliedServer() as service:
        interpreter = ScriptedInterpreter()
        session = Session(SchedulingAPI(service.base_url), interpreter, ledger=ActionLedger())
        turn = 0
        def send(label, utterance, intent='unclear', **fields):
            nonlocal turn
            turn += 1
            interpreter.answers.append(Interpretation(intent, **fields))
            view = session.submit(utterance, 'demo-turn-' + str(turn))
            # Summary only: do not record identity input or a raw conversation.
            print(f'Turn {turn}: {label} -> state={view.state}; outcome={view.outcome}')
            return view
        def posts():
            return [event for event in service.events if event[0] == 'POST']
        providers = send('provider lookup without identity',
                         'Which primary care providers are downtown?', 'provider_lookup',
                         specialty='primary_care', location='downtown')
        require(bool(providers.providers), 'No returned providers')
        require(service.events == [('GET', '/providers', 200)], 'Provider lookup requested identity')
        print('Returned providers:', len(providers.providers))
        if scenario == 'success':
            slots = send('unique synthetic identity and returned availability',
                         'Book primary care downtown for the supplied synthetic patient.', 'book',
                         specialty='primary_care', location='downtown',
                         phone='555-0101', dob='1985-04-12')
            require(bool(slots.slots), 'No returned slots')
            selected = slots.slots[0]
            proposal = send('choose displayed option', 'Choose option 1.', slot_choice='1')
            require(proposal.proposal is not None and proposal.proposal.slot == selected,
                    'Proposal mismatch')
            require(not posts(), 'Booked before confirmation')
            send('decline proposal', 'no')
            require(not posts(), 'Booked after decline')
            proposal = send('select again after declining', 'Choose option 1.', slot_choice='1')
            require(proposal.proposal is not None and not posts(), 'Selection unexpectedly booked')
            booked = send('separate explicit current confirmation', 'yes')
            require(booked.outcome == 'completed' and booked.appointment is not None,
                    'No validated booking')
            actual = booked.appointment
            require((actual.provider_id, actual.specialty, actual.location, actual.start_time) ==
                    (selected.provider_id, selected.specialty, selected.location, selected.start_time),
                    'Booking result mismatch')
            send('repeated confirmation does not replay', 'yes')
            require(posts() == [('POST', '/appointments', 201)], 'Expected exactly one booking HTTP201')
            print('Validated appointment matches selected returned provider, specialty, location and startTime.')
        else:
            no_match = send('no-match synthetic identity', 'Book for a synthetic patient.', 'book',
                            specialty='primary_care', phone='555-9999', dob='1990-01-01')
            require(no_match.state == 'no_match', 'Expected no-match correction opportunity')
            stopped = send('unresolved identity stops patient actions', 'I cannot correct those details.')
            require(stopped.state == 'assistance', 'Expected truthful human-assistance guidance')
            require(not posts(), 'No-match workflow booked')
            require([event[1] for event in service.events] == ['/providers', '/patients/search'],
                    'No-match workflow fetched patient-specific availability')
            print('Next step: contact clinic scheduling staff. No handoff has been queued.')
        for method, path, status in service.events:
            print(f'HTTP {method} {path} {status}')
        print('POST count:', len(posts()))
    print('PASS:', scenario, 'integration checks; fresh owned service cleaned up.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=('success', 'failure'), required=True)
    args = parser.parse_args()
    try:
        run(args.scenario)
    except Exception:
        parser.exit(1, 'FAIL: scheduling integration demo did not meet its checks.\n')


if __name__ == '__main__':
    main()
