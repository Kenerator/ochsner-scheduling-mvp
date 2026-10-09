"""Immutable service facts and process-local effect certainty; no transport here."""
from dataclasses import dataclass, field
from datetime import date, datetime
from threading import RLock
from uuid import uuid4

SPECIALTIES = ('primary_care', 'dermatology')
LOCATIONS = ('downtown', 'uptown', 'lakeside')

class DomainError(ValueError):
    """Invalid input/facts. Exception text contains no supplied values."""

def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise DomainError('Invalid text field')
    return value

def iso_date(value):
    text(value)
    try:
        if date.fromisoformat(value).isoformat() != value: raise ValueError()
    except ValueError: raise DomainError('Use an unambiguous date in YYYY-MM-DD format') from None
    return value

def timestamp(value):
    text(value)
    try:
        parsed=datetime.fromisoformat(value)
        if parsed.utcoffset() is None: raise ValueError()
    except ValueError: raise DomainError('Invalid service timestamp') from None
    return value

@dataclass(frozen=True)
class Preferences:
    specialty: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    appointment_type: str | None = None
    def __post_init__(self):
        if self.specialty is not None and self.specialty not in SPECIALTIES: raise DomainError('Unsupported specialty')
        if self.location is not None and self.location not in LOCATIONS: raise DomainError('Unsupported location')
        if self.appointment_type is not None: raise DomainError('Appointment type filtering is unsupported')
        for value in (self.start_date,self.end_date):
            if value is not None: iso_date(value)
        if self.start_date and self.end_date and self.start_date>self.end_date: raise DomainError('Start date must precede end date')

@dataclass(frozen=True)
class Patient:
    patient_id: str
    phone: str
    dob: str
    zip_code: str
    def __post_init__(self):
        for value in (self.patient_id,self.phone,self.zip_code): text(value)
        iso_date(self.dob)

@dataclass(frozen=True)
class Provider:
    provider_id: str
    name: str
    specialty: str
    locations: tuple[str,...]
    modalities: tuple[str,...]
    def __post_init__(self):
        text(self.provider_id);text(self.name)
        if self.specialty not in SPECIALTIES: raise DomainError('Invalid provider specialty')
        if not isinstance(self.locations,tuple) or not self.locations or any(x not in LOCATIONS for x in self.locations): raise DomainError('Invalid provider locations')
        if not isinstance(self.modalities,tuple) or not self.modalities: raise DomainError('Invalid provider modalities')
        for value in self.modalities: text(value)

@dataclass(frozen=True)
class Slot:
    slot_id: str
    provider_id: str
    specialty: str
    location: str
    start_time: str
    available: bool = True
    def __post_init__(self):
        text(self.slot_id);text(self.provider_id);timestamp(self.start_time)
        if self.specialty not in SPECIALTIES or self.location not in LOCATIONS or self.available is not True: raise DomainError('Invalid available slot')

@dataclass(frozen=True)
class Appointment:
    appointment_id: str
    patient_id: str
    provider_id: str
    specialty: str
    location: str
    start_time: str
    status: str
    def __post_init__(self):
        text(self.appointment_id);text(self.patient_id)
        Slot('validation',self.provider_id,self.specialty,self.location,self.start_time)
        if self.status!='scheduled': raise DomainError('Invalid appointment status')

@dataclass(frozen=True)
class Proposal:
    patient: Patient
    slot: Slot
    revision: int
    displayed_turn: int
    proposal_id: str = field(default_factory=lambda:uuid4().hex)

@dataclass(frozen=True)
class View:
    messages: tuple[str,...]
    state: str
    providers: tuple[Provider,...] = ()
    slots: tuple[Slot,...] = ()
    proposal: Proposal | None = None
    appointment: Appointment | None = None
    outcome: str = 'not_attempted'
    revision: int = 0
    @property
    def text(self): return '\n'.join(self.messages)

class ActionLedger:
    """Volatile conservative process guard. Reset never resolves an unknown write."""
    def __init__(self):
        self._lock=RLock();self._records={};self.unknown=False
    def claim(self, proposal_id):
        with self._lock:
            if self.unknown or proposal_id in self._records or 'in_flight' in self._records.values(): return False
            self._records[proposal_id]='in_flight'
            return True
    def resolve(self, proposal_id, outcome):
        with self._lock:
            if outcome not in ('completed','known_rejected','unknown'): raise DomainError('Invalid action outcome')
            self._records[proposal_id]=outcome
            if outcome=='unknown': self.unknown=True

PROCESS_ACTIONS=ActionLedger()
