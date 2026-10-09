import json
import unittest
from scheduling_assistant.diagnostics import Diagnostics


class DiagnosticTests(unittest.TestCase):
    def test_allowlisted_events_keep_timing_and_exclude_private_fields(self):
        sink = Diagnostics()
        sink(state='identity', intent='book', operation='find_patients', outcome='not_attempted', elapsed_ms=12.5,
             phone='private-phone', patient_id='private-id', text='private-prompt', api_key='private-key')
        self.assertEqual(sink.events, ({'state': 'identity', 'intent': 'book', 'operation': 'find_patients',
                                       'outcome': 'not_attempted', 'elapsed_ms': 12.5},))
        self.assertNotIn('private', json.dumps(sink.events))

    def test_arbitrary_values_cannot_hide_inside_allowed_fields(self):
        sink = Diagnostics()
        sink({'state': 'private-state', 'intent': 'private-intent', 'operation': '/patients?phone=private',
              'outcome': 'private-outcome', 'reason': 'private-error', 'elapsed_ms': float('nan')})
        self.assertEqual(sink.events, ())
        for elapsed in (-1, float('inf'), True, 'private-timing'):
            sink(elapsed_ms=elapsed)
        self.assertEqual(sink.events, ())

    def test_snapshots_are_detached_and_capacity_is_bounded(self):
        sink = Diagnostics(capacity=2)
        sink(state='identity'); sink(state='slots'); sink(state='confirmation')
        snapshot = sink.events
        snapshot[0]['state'] = 'private-mutation'
        self.assertEqual(sink.events, ({'state': 'slots'}, {'state': 'confirmation'}))

    def test_safe_error_reasons_do_not_include_raw_exceptions(self):
        sink = Diagnostics()
        sink(operation='book', outcome='unknown', reason='transport_failure', elapsed_ms=3000)
        self.assertEqual(sink.events[0]['reason'], 'transport_failure')
