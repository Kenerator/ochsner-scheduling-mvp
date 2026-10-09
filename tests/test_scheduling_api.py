"""Scheduling wire boundaries: finite local transport and returned provider facts."""
import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
import unittest

from scheduling_assistant.domain import Preferences
from scheduling_assistant.scheduling_api import APIError, SchedulingAPI


class Response(io.BytesIO):
    def __init__(self, body, status=200, content_type='application/json', headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        super().__init__(body)
        self.status = status
        self.headers = {'Content-Type': content_type, **(headers or {})}


class Transport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, request, *, timeout):
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        return self.response


def provider(**changes):
    return dict(providerId='provider_a', name='Synthetic Provider',
                specialty='primary_care', locations=['downtown'],
                modalities=['in_person'], **changes) if not changes else {
                    **provider(), **changes}


class SchedulingTransportTests(unittest.TestCase):
    def test_loopback_only_configuration(self):
        for url in ('http://example.com:4010', 'http://127.0.0.1.evil.test',
                    'http://user:password@localhost:4010', 'file:///tmp/api',
                    'http://127.0.0.1:4010/path', 'http://localhost:4010?key=x',
                    'http://localhost:4010#fragment', 'http://localhost:99999'):
            with self.subTest(url=url), self.assertRaises(APIError):
                SchedulingAPI(url)
        for url in ('http://127.0.0.1:4010', 'http://localhost:4010',
                    'http://[::1]:4010'):
            SchedulingAPI(url)

    def test_timeout_and_scenario_configuration(self):
        for timeout in (None, True, 0, -1, float('inf'), float('nan'), '5'):
            with self.subTest(timeout=timeout), self.assertRaises(APIError):
                SchedulingAPI(timeout=timeout)
        with self.assertRaises(APIError):
            SchedulingAPI(scenario='invented')
        transport = Transport(Response({'providers': []}))
        api = SchedulingAPI(scenario='api_failure', transport=transport)
        api.providers(Preferences())
        request, timeout = transport.calls[0]
        self.assertEqual(timeout, 5)
        self.assertEqual(request.get_header('X-mock-scenario'), 'api_failure')

    def test_url_encoding_and_no_retry(self):
        transport = Transport(error=URLError('SENSITIVE_SENTINEL'))
        api = SchedulingAPI(transport=transport)
        with self.assertRaises(APIError) as caught:
            api._request('GET', '/patients/search', {'phone': '555 + & 0101', 'dob': '1985-04-12'})
        query = parse_qs(urlparse(transport.calls[0][0].full_url).query)
        self.assertEqual(query, {'phone': ['555 + & 0101'], 'dob': ['1985-04-12']})
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(caught.exception.reason, 'transport_failure')
        self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))
        self.assertFalse(caught.exception.unknown)

    def test_oversize_header_and_body_fail_closed(self):
        bodies = [(b'{}', {'Content-Length': str(1024 * 1024 + 1)}),
                  (b' ' * (1024 * 1024 + 1), {}),
                  (b'{}', {'Content-Length': 'invalid'})]
        for body, headers in bodies:
            transport = Transport(Response(body, headers=headers))
            with self.subTest(headers=headers), self.assertRaises(APIError):
                SchedulingAPI(transport=transport).providers(Preferences())
            self.assertTrue(transport.response.closed)

    def test_strict_json_and_content_type(self):
        for raw in (b'{bad', b'[]', b'null', b'{"providers":NaN}',
                    b'{"providers":[],"providers":[]}', b'\xff'):
            with self.subTest(raw=raw), self.assertRaises(APIError):
                SchedulingAPI(transport=Transport(Response(raw))).providers(Preferences())
        with self.assertRaises(APIError):
            SchedulingAPI(transport=Transport(Response(b'{}', content_type='text/html'))).providers(Preferences())

    def test_safe_status_errors(self):
        for status, code, reason in ((400, 'invalid_parameter', 'bad_request'),
                                     (503, 'downstream_unavailable', 'unavailable'),
                                     (500, 'private_error', 'unexpected_status'),
                                     (302, 'redirect', 'unexpected_status')):
            response = Response({'code': code, 'message': 'SENSITIVE_SENTINEL'}, status=status)
            transport = Transport(response)
            with self.subTest(status=status), self.assertRaises(APIError) as caught:
                SchedulingAPI(transport=transport).providers(Preferences())
            self.assertEqual((caught.exception.status, caught.exception.reason), (status, reason))
            self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))
            self.assertEqual(len(transport.calls), 1)

    def test_post_redirect_is_not_followed(self):
        api = SchedulingAPI()
        request = __import__('urllib.request', fromlist=['Request']).Request(
            'http://127.0.0.1:4010/appointments', data=b'{}', method='POST')
        handlers = [handler for handler in api._opener.handlers
                    if hasattr(handler, 'redirect_request')]
        self.assertTrue(handlers)
        with self.assertRaises(HTTPError):
            handlers[0].redirect_request(request, None, 307, 'redirect', {},
                                         'http://127.0.0.1:4011/appointments')


class ProviderContractTests(unittest.TestCase):
    def call(self, payload, preferences=None):
        transport = Transport(Response(payload))
        return SchedulingAPI(transport=transport).providers(preferences or Preferences()), transport

    def test_optional_filters_and_immutable_typed_facts(self):
        result, transport = self.call({'providers': [provider()]}, Preferences('primary_care', 'downtown'))
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0].provider_id, 'provider_a')
        self.assertEqual(result[0].locations, ('downtown',))
        request = transport.calls[0][0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(urlparse(request.full_url).path, '/providers')
        self.assertEqual(parse_qs(urlparse(request.full_url).query),
                         {'specialty': ['primary_care'], 'location': ['downtown']})
        self.assertIsNone(request.data)
        _, unfiltered = self.call({'providers': []})
        self.assertEqual(urlparse(unfiltered.calls[0][0].full_url).query, '')

    def test_valid_empty_results(self):
        self.assertEqual(self.call({'providers': []})[0], ())

    def test_malformed_and_duplicate_results_fail_closed(self):
        malformed = ({}, {'providers': None}, {'providers': {}}, {'providers': [None]},
                     {'providers': [provider(), provider()]},
                     {'providers': [provider(providerId='')]},
                     {'providers': [provider(name=3)]},
                     {'providers': [provider(specialty='invented')]},
                     {'providers': [provider(locations='downtown')]},
                     {'providers': [provider(locations=[])]},
                     {'providers': [provider(modalities='in_person')]},
                     {'providers': [provider(modalities=[3])]},
                     {'providers': [{key: value for key, value in provider().items() if key != 'name'}]})
        for payload in malformed:
            with self.subTest(payload=payload), self.assertRaises(APIError):
                self.call(payload)

    def test_returned_facts_must_match_requested_filters(self):
        for changes in ({'specialty': 'dermatology'}, {'locations': ['uptown']}):
            with self.subTest(changes=changes), self.assertRaises(APIError):
                self.call({'providers': [provider(**changes)]}, Preferences('primary_care', 'downtown'))


def patient(**changes):
    return {**dict(patientId='patient_a', phone='555 + & 0101',
                   dateOfBirth='1985-04-12', zipCode='00123'), **changes}


def slot(**changes):
    return {**dict(slotId='slot_a', providerId='provider_a', specialty='primary_care',
                   location='downtown', startTime='2026-10-15T09:00:00-05:00',
                   available=True), **changes}


def appointment(**changes):
    return {**dict(appointmentId='appointment_a', patientId='patient_a',
                   providerId='provider_a', specialty='primary_care',
                   location='downtown', startTime='2026-10-15T09:00:00-05:00',
                   status='scheduled'), **changes}


class PatientAndAvailabilityTests(unittest.TestCase):
    def test_patient_search_encodes_exact_query_and_preserves_zip(self):
        transport = Transport(Response({'matches': [patient()]}))
        result = SchedulingAPI(transport=transport).find_patients('555 + & 0101', '1985-04-12')
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0].zip_code, '00123')
        request = transport.calls[0][0]
        self.assertEqual(urlparse(request.full_url).path, '/patients/search')
        self.assertEqual(parse_qs(urlparse(request.full_url).query),
                         {'phone': ['555 + & 0101'], 'dob': ['1985-04-12']})
        self.assertNotIn('zip', request.full_url)

    def test_patient_empty_and_private_duplicate_matches_are_valid(self):
        for matches in ([], [patient(), patient(patientId='patient_b', zipCode='00456')]):
            api = SchedulingAPI(transport=Transport(Response({'matches': matches})))
            self.assertEqual(len(api.find_patients('555 + & 0101', '1985-04-12')), len(matches))

    def test_patient_malformed_mismatched_and_duplicate_ids_rejected(self):
        bad = ({}, {'matches': None}, {'matches': [None]},
               {'matches': [patient(), patient()]},
               {'matches': [patient(phone='wrong')]},
               {'matches': [patient(dateOfBirth='1985-04-13')]},
               {'matches': [patient(zipCode=123)]},
               {'matches': [patient(patientId='')]})
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(APIError):
                SchedulingAPI(transport=Transport(Response(payload))).find_patients('555 + & 0101', '1985-04-12')

    def test_bad_local_inputs_dispatch_nothing(self):
        from scheduling_assistant.domain import Slot
        transport = Transport()
        api = SchedulingAPI(transport=transport)
        actions = [lambda: api.find_patients('', '1985-04-12'),
                   lambda: api.find_patients('555', '1985-02-30'),
                   lambda: api.availability('', Preferences('primary_care')),
                   lambda: api.availability('patient_a', Preferences()),
                   lambda: api.book('', Slot('s', 'p', 'primary_care', 'downtown', '2026-10-15T09:00:00-05:00')),
                   lambda: api.book('patient_a', {'slotId': 's'})]
        for action in actions:
            with self.assertRaises(APIError) as caught:
                action()
            self.assertFalse(caught.exception.unknown)
        self.assertEqual(transport.calls, [])

    def test_availability_validates_filters_and_offset_without_reinterpretation(self):
        preferences = Preferences('primary_care', 'downtown', '2026-10-15', '2026-10-15')
        transport = Transport(Response({'slots': [slot()]}))
        result = SchedulingAPI(transport=transport).availability('patient_a', preferences)
        self.assertEqual(result[0].start_time, '2026-10-15T09:00:00-05:00')
        query = parse_qs(urlparse(transport.calls[0][0].full_url).query)
        self.assertEqual(query, {'patientId': ['patient_a'], 'specialty': ['primary_care'],
                                'location': ['downtown'], 'startDate': ['2026-10-15'], 'endDate': ['2026-10-15']})
        api = SchedulingAPI(transport=Transport(Response({'slots': []})))
        self.assertEqual(api.availability('patient_a', preferences), ())

    def test_availability_malformed_unavailable_filter_and_duplicate_rejected(self):
        changes = ({'available': False}, {'available': 'true'}, {'available': 1},
                   {'specialty': 'dermatology'}, {'location': 'uptown'},
                   {'startTime': '2026-10-14T09:00:00-05:00'},
                   {'startTime': '2026-10-16T09:00:00-05:00'},
                   {'startTime': '2026-10-15T09:00:00'}, {'slotId': ''})
        payloads = [{'slots': [slot(**change)]} for change in changes]
        payloads += [{}, {'slots': None}, {'slots': [None]}, {'slots': [slot(), slot()]},
                     {'slots': [{key: value for key, value in slot().items() if key != 'available'}]}]
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(APIError):
                SchedulingAPI(transport=Transport(Response(payload))).availability(
                    'patient_a', Preferences('primary_care', 'downtown', '2026-10-15', '2026-10-15'))


class BookingContractTests(unittest.TestCase):
    def stored_slot(self):
        from scheduling_assistant.domain import Slot
        row = slot()
        return Slot(row['slotId'], row['providerId'], row['specialty'],
                    row['location'], row['startTime'])

    def test_booking_exact_payload_and_validated_201(self):
        transport = Transport(Response({'appointment': appointment()}, status=201))
        result = SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
        self.assertEqual(result.appointment_id, 'appointment_a')
        request, timeout = transport.calls[0]
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(urlparse(request.full_url).path, '/appointments')
        self.assertEqual(json.loads(request.data),
                         {'patientId': 'patient_a', 'slotId': 'slot_a', 'confirmed': True})
        self.assertEqual(timeout, 5)
        self.assertEqual(len(transport.calls), 1)

    def test_malformed_mismatched_and_non201_booking_are_unknown(self):
        payloads = [{}, {'appointment': None}, {'appointment': {}}]
        payloads += [{'appointment': appointment(**change)} for change in (
            {'appointmentId': ''}, {'patientId': 'another'}, {'providerId': 'another'},
            {'specialty': 'dermatology'}, {'location': 'uptown'},
            {'startTime': '2026-10-15T10:00:00-05:00'}, {'status': 'cancelled'})]
        cases = [(201, payload) for payload in payloads]
        cases += [(200, {'appointment': appointment()}), (204, b''), (201, b'{bad'),
                  (500, {'code': 'internal_error', 'message': 'PRIVATE_SENTINEL'}),
                  (409, {'code': 'invented', 'message': 'PRIVATE_SENTINEL'}),
                  (503, {'code': 'invented', 'message': 'PRIVATE_SENTINEL'}),
                  (400, {'code': 'unknown_slot'})]
        for status, payload in cases:
            transport = Transport(Response(payload, status=status))
            with self.subTest(status=status, payload=payload), self.assertRaises(APIError) as caught:
                SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
            self.assertTrue(caught.exception.unknown)
            self.assertEqual(caught.exception.status, status)
            self.assertNotIn('PRIVATE_SENTINEL', str(caught.exception))
            self.assertEqual(len(transport.calls), 1)

    def test_recognized_rejections_are_known(self):
        for status, code, reason in ((400, 'unknown_slot', 'bad_request'),
                                     (409, 'slot_taken', 'conflict'),
                                     (503, 'downstream_unavailable', 'unavailable')):
            transport = Transport(Response({'code': code, 'message': 'PRIVATE_SENTINEL'}, status=status))
            with self.subTest(status=status), self.assertRaises(APIError) as caught:
                SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
            self.assertFalse(caught.exception.unknown)
            self.assertEqual(caught.exception.reason, reason)
            self.assertEqual(len(transport.calls), 1)

    def test_dispatched_transport_failures_never_retry_or_claim_failure_certainty(self):
        for error in (TimeoutError('PRIVATE_SENTINEL'), ConnectionResetError('PRIVATE_SENTINEL'),
                      URLError('PRIVATE_SENTINEL')):
            transport = Transport(error=error)
            with self.subTest(error=type(error).__name__), self.assertRaises(APIError) as caught:
                SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
            self.assertTrue(caught.exception.unknown)
            self.assertEqual(len(transport.calls), 1)
            self.assertNotIn('PRIVATE_SENTINEL', str(caught.exception))

    def test_explicit_connection_refusal_before_dispatch_is_known(self):
        transport = Transport(error=URLError(ConnectionRefusedError('PRIVATE_SENTINEL')))
        with self.assertRaises(APIError) as caught:
            SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
        self.assertFalse(caught.exception.unknown)
        self.assertEqual(caught.exception.reason, 'transport_failure')
        self.assertEqual(len(transport.calls), 1)

    def test_timeout_after_effect_and_interrupted_dispatch_never_retry(self):
        effects = []
        def uncertain(request, *, timeout):
            effects.append(request.get_method())
            raise TimeoutError('PRIVATE_SENTINEL')
        with self.assertRaises(APIError) as caught:
            SchedulingAPI(transport=uncertain).book('patient_a', self.stored_slot())
        self.assertTrue(caught.exception.unknown)
        self.assertEqual(effects, ['POST'])
        transport = Transport(error=KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
        self.assertEqual(len(transport.calls), 1)

    def test_post_redirect_response_is_unknown_and_single_dispatch(self):
        transport = Transport(Response({'code': 'redirect', 'message': 'moved'}, status=307))
        with self.assertRaises(APIError) as caught:
            SchedulingAPI(transport=transport).book('patient_a', self.stored_slot())
        self.assertTrue(caught.exception.unknown)
        self.assertEqual(len(transport.calls), 1)


class ReferenceHTTPComponentTests(unittest.TestCase):
    def test_actual_reference_search_availability_booking_conflict_and_outage(self):
        import importlib.util
        from pathlib import Path
        from threading import Thread
        source = Path(__file__).resolve().parents[1] / 'vendor/scheduling-reference/mock-api/server.py'
        spec = importlib.util.spec_from_file_location('scheduling_reference_component', source)
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        events = []
        class Handler(reference.Handler):
            store = reference.Store()
            def audit(self, method, path, status, ms):
                events.append((method, path, status))
        server = reference.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        try:
            api = SchedulingAPI('http://127.0.0.1:' + str(server.server_port))
            self.assertTrue(api.providers(Preferences('primary_care', 'downtown')))
            self.assertEqual(api.find_patients('555-9999', '1990-01-01'), ())
            self.assertEqual(len(api.find_patients('555-0130', '1978-09-22')), 2)
            found = api.find_patients('555-0101', '1985-04-12')
            self.assertEqual(len(found), 1)
            slots = api.availability(found[0].patient_id, Preferences('primary_care', 'downtown'))
            chosen = next(item for item in slots if item.slot_id == 'slot_4001')
            booked = api.book(found[0].patient_id, chosen)
            self.assertEqual(booked.start_time, chosen.start_time)
            self.assertEqual(booked.patient_id, found[0].patient_id)
            with self.assertRaises(APIError) as caught:
                api.book(found[0].patient_id, chosen)
            self.assertEqual((caught.exception.reason, caught.exception.unknown), ('conflict', False))
            outage = SchedulingAPI(api.base_url, scenario='api_failure')
            with self.assertRaises(APIError) as caught:
                outage.book(found[0].patient_id, chosen)
            self.assertEqual((caught.exception.reason, caught.exception.unknown), ('unavailable', False))
            self.assertEqual([event[2] for event in events if event[0] == 'POST'], [201, 409, 503])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()
