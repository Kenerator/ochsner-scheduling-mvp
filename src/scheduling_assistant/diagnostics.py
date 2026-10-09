"""Bounded, process-local diagnostic snapshots with no arbitrary string values."""
from math import isfinite
from threading import RLock

_ALLOWED = {
    'state': {'start', 'stale', 'intent', 'identity', 'no_match', 'zip', 'specialty', 'providers',
              'slots', 'confirmation', 'completed', 'unknown', 'assistance', 'clarify', 'empty'},
    'intent': {'provider_lookup', 'book', 'appointment_lookup', 'human', 'medical_advice', 'unsupported', 'unclear'},
    'operation': {'interpret', 'providers', 'find_patients', 'availability', 'book', 'submit', 'reset'},
    'outcome': {'not_attempted', 'completed', 'known_rejected', 'unknown', 'success', 'failure'},
    'reason': {'configuration', 'transport', 'http', 'refusal', 'incomplete', 'invalid_response',
               'invalid_context', 'invalid_configuration', 'bad_request', 'unavailable', 'bad_response',
               'response_too_large', 'unexpected_status', 'transport_failure', 'conflict',
               'stale', 'unsupported', 'no_match', 'ambiguous', 'invalid_input'},
}


class Diagnostics:
    """Callable sink; unknown keys and non-enum values are discarded at entry."""
    def __init__(self, capacity=200):
        if type(capacity) is not int or not 1 <= capacity <= 10000:
            raise ValueError('Invalid diagnostic capacity')
        self.capacity = capacity
        self._events = []
        self._lock = RLock()

    def __call__(self, event=None, **values):
        supplied = dict(event) if isinstance(event, dict) else {}
        supplied.update(values)
        safe = {key: value for key, value in supplied.items()
                if key in _ALLOWED and isinstance(value, str) and value in _ALLOWED[key]}
        elapsed = supplied.get('elapsed_ms')
        if type(elapsed) in (int, float) and isfinite(elapsed) and 0 <= elapsed <= 86400000:
            safe['elapsed_ms'] = round(elapsed, 3)
        if safe:
            with self._lock:
                self._events.append(safe)
                del self._events[:-self.capacity]

    @property
    def events(self):
        with self._lock:
            return tuple(dict(event) for event in self._events)
