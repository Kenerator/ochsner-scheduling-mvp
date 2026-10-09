"""Actual supplied HTTP service + deterministic interpreter; never live AI proof."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit
import unittest

from scheduling_assistant.domain import ActionLedger
from scheduling_assistant.interpretation import Interpretation
from scheduling_assistant.scheduling_api import SchedulingAPI
from scheduling_assistant.session import Session

ROOT = Path(__file__).resolve().parents[1]


class ScriptedInterpreter:
    def __init__(self):
        self.answers = []
    def interpret(self, text, context):
        return self.answers.pop(0)


class SuppliedHTTP:
    def __enter__(self):
        source = ROOT / 'vendor/scheduling-reference/mock-api/server.py'
        spec = importlib.util.spec_from_file_location('integration_reference', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.events = []
        events = self.events
        class Handler(module.Handler):
            store = module.Store()
            def respond(self, status, payload):
                events.append((self.command, urlsplit(self.path).path, status))
                super().respond(status, payload)
            def audit(self, *args):
                pass
        self.server = module.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = Thread(target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()
        self.base_url = 'http://127.0.0.1:' + str(self.server.server_port)
        return self
    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise RuntimeError('Owned reference server did not stop')


class SchedulingHTTPIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.service = SuppliedHTTP().__enter__()
        self.addCleanup(self.service.__exit__)
        self.interpreter = ScriptedInterpreter()
        self.api = SchedulingAPI(self.service.base_url)
        self.session = Session(self.api, self.interpreter, ledger=ActionLedger())
        self.event = 0

    def send(self, text, intent='unclear', **fields):
        self.interpreter.answers.append(Interpretation(intent, **fields))
        self.event += 1
        return self.session.submit(text, 'turn-' + str(self.event))

    def slots(self):
        return self.send('Book primary care downtown for my synthetic record.', 'book',
                         specialty='primary_care', location='downtown',
                         phone='555-0101', dob='1985-04-12')

    def posts(self):
        return [event for event in self.service.events if event[0] == 'POST']

    def test_provider_then_booking_requires_separate_confirmation_and_cannot_replay(self):
        providers = self.send('Which primary care providers are downtown?', 'provider_lookup',
                              specialty='primary_care', location='downtown')
        self.assertTrue(providers.providers)
        self.assertEqual(self.service.events, [('GET', '/providers', 200)])
        slots = self.slots()
        self.assertEqual(slots.state, 'slots')
        chosen = slots.slots[0]
        proposal = self.send('Choose option one.', slot_choice='1')
        self.assertEqual(proposal.proposal.slot, chosen)
        self.assertEqual(self.posts(), [])
        result = self.send('yes')
        self.assertEqual(result.outcome, 'completed')
        self.assertEqual(result.appointment.start_time, chosen.start_time)
        self.assertEqual(result.appointment.provider_id, chosen.provider_id)
        self.assertEqual(self.posts(), [('POST', '/appointments', 201)])
        self.send('yes')
        self.session.submit('yes', 'turn-' + str(self.event))
        self.assertEqual(len(self.posts()), 1)

    def test_no_match_truthful_guidance_and_no_patient_specific_effect(self):
        first = self.send('Book a synthetic patient.', 'book', specialty='primary_care',
                          phone='555-9999', dob='1990-01-01')
        self.assertEqual(first.state, 'no_match')
        final = self.send('I cannot correct those details.')
        self.assertEqual(final.state, 'assistance')
        self.assertIn('clinic scheduling staff', final.text)
        self.assertIsNone(final.appointment)
        self.assertEqual(self.service.events, [('GET', '/patients/search', 200)])
        for value in ('555-9999', '1990-01-01', 'pat_1001', 'Maya', 'Chen'):
            self.assertNotIn(value, first.text + final.text)

    def test_duplicate_patient_zip_is_private_local_and_unique(self):
        first = self.send('Book primary care.', 'book', specialty='primary_care',
                          phone='555-0130', dob='1978-09-22')
        self.assertEqual(first.state, 'zip')
        for value in ('Avery', 'Patel', 'pat_1003', 'pat_1004', '70115', '70005'):
            self.assertNotIn(value, first.text)
        matched = self.send('My ZIP is supplied privately.', zip='70005')
        self.assertEqual(matched.state, 'slots')
        self.assertEqual(self.session.patient.patient_id, 'pat_1004')
        self.assertEqual([event[1] for event in self.service.events], ['/patients/search', '/availability'])
        self.assertEqual(self.posts(), [])

    def test_conflict_refresh_excludes_rejected_slot_and_requires_fresh_consent(self):
        slots = self.slots()
        index = next(index for index, item in enumerate(slots.slots, 1)
                     if item.slot_id == 'slot_conflict_001')
        self.send('Select the returned conflict test option.', slot_choice=str(index))
        rejected = self.send('yes')
        self.assertEqual(rejected.outcome, 'known_rejected')
        self.assertIsNone(rejected.proposal)
        self.assertTrue(rejected.slots)
        self.assertNotIn('slot_conflict_001', [item.slot_id for item in rejected.slots])
        self.send('yes')
        self.assertEqual(self.posts(), [('POST', '/appointments', 409)])
        self.send('Select the refreshed first option.', slot_choice='1')
        self.assertEqual(len(self.posts()), 1)
        booked = self.send('yes')
        self.assertEqual(booked.outcome, 'completed')
        self.assertEqual([event[2] for event in self.posts()], [409, 201])

    def test_empty_availability_and_outage_are_truthful(self):
        empty = self.send('Book dermatology lakeside.', 'book', specialty='dermatology',
                          location='lakeside', phone='555-0101', dob='1985-04-12')
        self.assertEqual(empty.state, 'empty')
        self.assertEqual(self.posts(), [])
        self.session = Session(SchedulingAPI(self.service.base_url, scenario='api_failure'),
                               self.interpreter, ledger=ActionLedger())
        outage = self.send('Find providers.', 'provider_lookup')
        self.assertEqual(outage.state, 'assistance')
        self.assertIn('No handoff has been queued', outage.text)
        self.assertEqual(self.service.events[-1], ('GET', '/providers', 503))

    def test_stale_display_and_medical_request_cannot_book(self):
        self.slots()
        proposal = self.send('Select one.', slot_choice='1')
        self.send('Change to uptown.', location='uptown')
        stale = self.session.submit('yes', 'old-display', expected_revision=proposal.revision)
        self.assertEqual(stale.state, 'stale')
        final = self.send('Should I wait with chest pain?', 'medical_advice')
        self.assertEqual(final.state, 'assistance')
        self.assertIn('cannot provide medical advice or triage', final.text)
        self.assertEqual(self.posts(), [])

    def test_actual_committed_booking_with_lost_response_stays_unknown_across_reset(self):
        transport_api = SchedulingAPI(self.service.base_url)
        def lose_write_response(request, *, timeout):
            response = transport_api._opener.open(request, timeout=timeout)
            if request.get_method() == 'POST':
                try:
                    response.read()
                finally:
                    response.close()
                raise TimeoutError('PRIVATE_SENTINEL')
            return response
        self.session = Session(SchedulingAPI(self.service.base_url, transport=lose_write_response),
                               self.interpreter, ledger=ActionLedger())
        self.slots()
        self.send('Select one.', slot_choice='1')
        unknown = self.send('yes')
        self.assertEqual(unknown.outcome, 'unknown')
        self.assertNotIn('PRIVATE_SENTINEL', unknown.text)
        self.assertEqual(self.posts(), [('POST', '/appointments', 201)])
        self.session.submit('reset', 'reset')
        blocked = self.slots()
        self.assertEqual(blocked.outcome, 'unknown')
        self.assertEqual(len(self.posts()), 1)


class SchedulingDemoTests(unittest.TestCase):
    def test_both_scripted_demos_use_real_http_and_label_simulated_interpretation(self):
        for scenario in ('success', 'failure'):
            with self.subTest(scenario=scenario):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/demo_scheduling.py'),
                                         '--scenario', scenario], cwd=ROOT,
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('SIMULATED INTERPRETER', result.stdout)
                self.assertIn('ACTUAL SUPPLIED HTTP', result.stdout)
                self.assertIn('Not live AI qualification', result.stdout)
                self.assertIn('PASS', result.stdout)
                self.assertNotIn('555-', result.stdout)
                self.assertNotIn('1985-04-12', result.stdout)
                self.assertNotIn('1990-01-01', result.stdout)
                if scenario == 'success':
                    self.assertIn('POST /appointments 201', result.stdout)
                else:
                    self.assertIn('POST count: 0', result.stdout)


if __name__ == '__main__':
    unittest.main()
