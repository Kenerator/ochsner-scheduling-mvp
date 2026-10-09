"""Bounded loopback HTTP adapter; only validated service facts cross this boundary."""
import ipaddress
import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .domain import (Appointment, DomainError, Patient, Preferences, Provider,
                     Slot, iso_date, text)

MAX_RESPONSE_BYTES = 1024 * 1024


class APIError(Exception):
    """Safe classification only: never retain upstream payloads or exception text."""
    def __init__(self, reason, status=None, unknown=False):
        self.reason = reason
        self.status = status
        self.unknown = unknown
        super().__init__(reason)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Redirects could replay a write or escape the checked loopback endpoint.
        raise HTTPError(req.full_url, code, 'redirect_rejected', headers, fp)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('invalid_json_constant')


class SchedulingAPI:
    def __init__(self, base_url='http://127.0.0.1:4010', scenario=None,
                 timeout=5, transport=None):
        try:
            if not isinstance(base_url, str):
                raise ValueError()
            parsed = urlsplit(base_url)
            host = parsed.hostname
            if host != 'localhost' and not ipaddress.ip_address(host).is_loopback:
                raise ValueError()
            if (parsed.scheme not in ('http', 'https') or parsed.username is not None
                    or parsed.password is not None or parsed.path not in ('', '/')
                    or parsed.query or parsed.fragment):
                raise ValueError()
            parsed.port  # Validate malformed and out-of-range ports.
            if (type(timeout) not in (int, float) or not math.isfinite(timeout)
                    or timeout <= 0 or scenario not in (None, 'api_failure')):
                raise ValueError()
            if transport is not None and not callable(transport):
                raise ValueError()
        except (ValueError, TypeError):
            raise APIError('invalid_configuration') from None
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.scenario = scenario
        # Local scheduling must not inherit a potentially external HTTP proxy.
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())
        self._transport = transport or self._opener.open

    def _request(self, method, path, params=None, body=None, expected=200):
        """One dispatch, zero retries. Dispatched write ambiguity stays unknown."""
        writing = method == 'POST'
        query = urlencode(params or {})
        url = self.base_url + path + ('?' + query if query else '')
        headers = {'Accept': 'application/json'}
        if self.scenario:
            headers['X-Mock-Scenario'] = self.scenario
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        request = Request(url, data=data, headers=headers, method=method)
        response = None
        status = None
        try:
            try:
                response = self._transport(request, timeout=self.timeout)
            except HTTPError as error:
                response = error
            status = getattr(response, 'status', None)
            if type(status) is not int:
                raise APIError('bad_response', unknown=writing)
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type != 'application/json':
                raise APIError('bad_response', status, writing)
            declared_length = response.headers.get('Content-Length')
            if declared_length is not None:
                try:
                    declared_length = int(declared_length)
                    if declared_length < 0:
                        raise ValueError()
                except (ValueError, TypeError):
                    raise APIError('bad_response', status, writing) from None
                if declared_length > MAX_RESPONSE_BYTES:
                    raise APIError('response_too_large', status, writing)
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if not isinstance(raw, bytes):
                raise APIError('bad_response', status, writing)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise APIError('response_too_large', status, writing)
            if declared_length is not None and len(raw) != declared_length:
                raise APIError('bad_response', status, writing)
            try:
                payload = json.loads(raw.decode('utf-8'), object_pairs_hook=_object,
                                     parse_constant=_invalid_constant)
                if not isinstance(payload, dict):
                    raise ValueError()
            except (ValueError, UnicodeError, RecursionError):
                raise APIError('bad_response', status, writing) from None
            if status != expected:
                code = payload.get('code')
                valid_error = isinstance(code, str) and isinstance(payload.get('message'), str)
                if valid_error and status == 400 and code in (
                        'missing_parameter', 'invalid_parameter', 'invalid_json',
                        'unknown_patient', 'unknown_slot', 'confirmation_required'):
                    raise APIError('bad_request', status)
                if valid_error and status == 409 and code == 'slot_taken':
                    raise APIError('conflict', status)
                if valid_error and status == 503 and code == 'downstream_unavailable':
                    raise APIError('unavailable', status)
                raise APIError('unexpected_status', status, writing)
            return payload
        except APIError:
            raise
        except Exception as error:
            # Only an explicit urllib connection refusal establishes that no
            # request reached the service. Timeouts/disconnects remain uncertain.
            refused = (response is None and isinstance(error, URLError)
                       and isinstance(error.reason, ConnectionRefusedError))
            raise APIError('transport_failure', status, writing and not refused) from None
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

    def providers(self, preferences: Preferences) -> tuple[Provider, ...]:
        if not isinstance(preferences, Preferences):
            raise APIError('bad_request')
        params = {key: value for key, value in (
            ('specialty', preferences.specialty), ('location', preferences.location))
                  if value is not None}
        payload = self._request('GET', '/providers', params)
        try:
            rows = payload['providers']
            if not isinstance(rows, list):
                raise ValueError()
            result = []
            identifiers = set()
            for row in rows:
                if (not isinstance(row, dict) or not isinstance(row.get('locations'), list)
                        or not isinstance(row.get('modalities'), list)):
                    raise ValueError()
                item = Provider(row['providerId'], row['name'], row['specialty'],
                                tuple(row['locations']), tuple(row['modalities']))
                if (item.provider_id in identifiers
                        or preferences.specialty is not None and item.specialty != preferences.specialty
                        or preferences.location is not None and preferences.location not in item.locations):
                    raise ValueError()
                identifiers.add(item.provider_id)
                result.append(item)
            return tuple(result)
        except (KeyError, TypeError, ValueError, DomainError):
            raise APIError('bad_response', 200) from None

    def find_patients(self, phone: str, dob: str) -> tuple[Patient, ...]:
        try:
            text(phone)
            iso_date(dob)
        except DomainError:
            raise APIError('bad_request') from None
        payload = self._request('GET', '/patients/search', {'phone': phone, 'dob': dob})
        try:
            rows = payload['matches']
            if not isinstance(rows, list):
                raise ValueError()
            result = []
            identifiers = set()
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError()
                item = Patient(row['patientId'], row['phone'], row['dateOfBirth'], row['zipCode'])
                if item.patient_id in identifiers or item.phone != phone or item.dob != dob:
                    raise ValueError()
                identifiers.add(item.patient_id)
                result.append(item)
            # Multiple valid candidates stay private; the core resolves ZIP locally.
            return tuple(result)
        except (KeyError, TypeError, ValueError):
            raise APIError('bad_response', 200) from None

    def availability(self, patient_id: str, preferences: Preferences) -> tuple[Slot, ...]:
        try:
            text(patient_id)
            if not isinstance(preferences, Preferences) or preferences.specialty is None:
                raise DomainError('Missing specialty')
        except DomainError:
            raise APIError('bad_request') from None
        params = {key: value for key, value in (
            ('patientId', patient_id), ('specialty', preferences.specialty),
            ('location', preferences.location), ('startDate', preferences.start_date),
            ('endDate', preferences.end_date)) if value is not None}
        payload = self._request('GET', '/availability', params)
        try:
            rows = payload['slots']
            if not isinstance(rows, list):
                raise ValueError()
            result = []
            identifiers = set()
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError()
                item = Slot(row['slotId'], row['providerId'], row['specialty'],
                            row['location'], row['startTime'], row['available'])
                day = item.start_time[:10]
                if (item.slot_id in identifiers or item.specialty != preferences.specialty
                        or preferences.location is not None and item.location != preferences.location
                        or preferences.start_date is not None and day < preferences.start_date
                        or preferences.end_date is not None and day > preferences.end_date):
                    raise ValueError()
                identifiers.add(item.slot_id)
                result.append(item)
            return tuple(result)
        except (KeyError, TypeError, ValueError):
            raise APIError('bad_response', 200) from None

    def book(self, patient_id: str, slot: Slot) -> Appointment:
        """Core owns current consent; this adapter validates the resulting evidence."""
        try:
            text(patient_id)
            if not isinstance(slot, Slot):
                raise DomainError('Invalid slot')
        except DomainError:
            raise APIError('bad_request') from None
        payload = self._request('POST', '/appointments', body={
            'patientId': patient_id, 'slotId': slot.slot_id, 'confirmed': True}, expected=201)
        try:
            row = payload['appointment']
            if not isinstance(row, dict):
                raise ValueError()
            item = Appointment(row['appointmentId'], row['patientId'], row['providerId'],
                               row['specialty'], row['location'], row['startTime'], row['status'])
            actual = (item.patient_id, item.provider_id, item.specialty, item.location, item.start_time)
            expected = (patient_id, slot.provider_id, slot.specialty, slot.location, slot.start_time)
            if actual != expected:
                raise ValueError()
            return item
        except (KeyError, TypeError, ValueError):
            # A write may have committed before an unusable reply reached us.
            raise APIError('bad_response', 201, unknown=True) from None
