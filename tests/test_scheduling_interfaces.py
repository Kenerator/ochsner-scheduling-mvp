import io
import unittest
from scheduling_assistant.__main__ import main
from scheduling_assistant.domain import View


class FakeSession:
    revision = 0
    current_view = View(('AI scheduling assistant — synthetic demonstration.',), 'start')
    def __init__(self): self.turns = []
    def submit(self, text, event_id, expected_revision=None):
        self.turns.append((text, event_id, expected_revision))
        self.revision += 1
        return View(('Returned safe facts: ' + ('reset' if text == 'reset' else 'provider'),), 'providers', revision=self.revision)


class InterfaceTests(unittest.TestCase):
    def invoke(self, args, text='', env=None, factory=None):
        out, err = io.StringIO(), io.StringIO()
        result = main(args, stdin=io.StringIO(text), stdout=out, stderr=err,
                      environ={} if env is None else env, session_factory=factory)
        return result, out.getvalue(), err.getvalue()

    def test_help_and_missing_configuration_never_build_session(self):
        def forbidden(*args): self.fail('No runtime session should be built')
        code, out, err = self.invoke(['--help'], factory=forbidden)
        self.assertEqual(code, 0); self.assertIn('--model', out); self.assertEqual(err, '')
        code, out, err = self.invoke([], factory=forbidden)
        self.assertEqual(code, 2); self.assertIn('SCHEDULING_MODEL', err)
        code, out, err = self.invoke(['--model', 'chosen-model'], factory=forbidden)
        self.assertEqual(code, 2); self.assertIn('OPENAI_API_KEY', err)

    def test_thin_cli_sends_each_turn_once_and_renders_shared_view(self):
        session = FakeSession(); configs = []
        def factory(config): configs.append(config); return session
        code, out, err = self.invoke(['--api-base-url', 'http://127.0.0.1:4010', '--scenario', 'api_failure'],
                                    'find providers\nreset\nquit\nignored\n',
                                    {'SCHEDULING_MODEL': 'chosen-model', 'OPENAI_API_KEY': 'private-key'}, factory)
        self.assertEqual(code, 0); self.assertEqual(err, '')
        self.assertEqual([turn[0] for turn in session.turns], ['find providers', 'reset'])
        self.assertEqual(len(set(turn[1] for turn in session.turns)), 2)
        self.assertEqual([turn[2] for turn in session.turns], [0, 1])
        self.assertIn('AI scheduling assistant', out); self.assertIn('Processing', out)
        self.assertIn('Elapsed:', out); self.assertIn('Returned safe facts: provider', out)
        self.assertEqual(configs[0].model, 'chosen-model'); self.assertEqual(configs[0].scenario, 'api_failure')
        self.assertNotIn('private-key', out + err)

    def test_model_argument_overrides_environment_and_bad_arguments_are_safe(self):
        session = FakeSession(); configs = []
        self.invoke(['--model', 'explicit'], env={'SCHEDULING_MODEL': 'environment', 'OPENAI_API_KEY': 'key'},
                    factory=lambda config: configs.append(config) or session)
        self.assertEqual(configs[0].model, 'explicit')
        code, out, err = self.invoke(['--scenario', 'secret-input'], factory=lambda config: self.fail())
        self.assertEqual(code, 2); self.assertNotIn('secret-input', out + err)

    def test_unexpected_startup_failure_never_exposes_raw_exception(self):
        def broken(config): raise RuntimeError('private-provider-error')
        code, out, err = self.invoke(['--model', 'model'], env={'OPENAI_API_KEY': 'private-key'}, factory=broken)
        self.assertEqual(code, 2); self.assertNotIn('private', out + err)
        self.assertIn('configuration', err.lower())

    def test_interruption_warns_about_unknown_effect_without_retry(self):
        class Interrupted(FakeSession):
            def submit(self, *args, **kwargs): raise KeyboardInterrupt('private')
        code, out, err = self.invoke(['--model', 'model'], 'yes\n', {'OPENAI_API_KEY': 'key'}, lambda config: Interrupted())
        self.assertEqual(code, 130); self.assertIn('unknown', out + err); self.assertIn('Do not retry', out + err)
        self.assertNotIn('private', out + err)

    def test_cli_preserves_real_controller_separate_consent_and_single_booking(self):
        from scheduling_assistant.session import Session
        from scheduling_assistant.domain import ActionLedger, Patient, Slot, Appointment
        from scheduling_assistant.interpretation import Interpretation
        from collections import deque
        patient = Patient('synthetic-patient', '555-0100', '1980-01-01', '00123')
        slot = Slot('returned-slot', 'returned-provider', 'primary_care', 'downtown', '2026-10-20T10:00:00-05:00')
        class Gateway:
            def __init__(self): self.bookings = []
            def find_patients(self, phone, dob): return (patient,)
            def availability(self, patient_id, preferences): return (slot,)
            def book(self, patient_id, selected):
                self.bookings.append((patient_id, selected))
                return Appointment('returned-appointment', patient_id, selected.provider_id, selected.specialty,
                                   selected.location, selected.start_time, 'scheduled')
        class Interpreter:
            def __init__(self):
                self.items = deque((Interpretation('book', specialty='primary_care', phone=patient.phone, dob=patient.dob),
                                    Interpretation('unclear', slot_choice='1'), Interpretation('unclear'), Interpretation('unclear')))
            def interpret(self, text, context): return self.items.popleft()
        gateway = Gateway()
        session = Session(gateway, Interpreter(), ledger=ActionLedger())
        code, out, err = self.invoke(['--model', 'model'], 'book\nfirst\nyes\nyes\nquit\n',
                                    {'OPENAI_API_KEY': 'key'}, lambda config: session)
        self.assertEqual(code, 0); self.assertEqual(err, '')
        self.assertEqual(gateway.bookings, [(patient.patient_id, slot)])
        self.assertLess(out.index('Proposed appointment'), out.index('Booked appointment'))
        self.assertIn('Reply yes in a separate message', out)
        self.assertNotIn(patient.phone, out); self.assertNotIn(patient.dob, out)
