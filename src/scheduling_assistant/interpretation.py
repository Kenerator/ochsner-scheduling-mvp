"""Advisory current-turn extraction; deliberately has no effect/consent fields."""
from dataclasses import dataclass, fields
from typing import Mapping, Protocol

INTENTS = ('provider_lookup','book','appointment_lookup','human','medical_advice','unsupported','unclear')

class ModelError(ValueError):
    """Safe fixed reason only; never wrap raw provider text in user diagnostics."""
    def __init__(self, reason='invalid_response'):
        allowed = ('configuration','transport','http','refusal','incomplete','invalid_response','invalid_context')
        self.reason = reason if reason in allowed else 'invalid_response'
        super().__init__(self.reason)

@dataclass(frozen=True)
class Interpretation:
    intent: str
    specialty: str | None = None
    location: str | None = None
    appointment_type: str | None = None
    phone: str | None = None
    dob: str | None = None
    zip: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    slot_choice: str | None = None

    def __post_init__(self):
        if self.intent not in INTENTS: raise ModelError()
        for item in fields(self):
            value = getattr(self, item.name)
            if value is not None and (not isinstance(value, str) or len(value) > 500):
                raise ModelError()

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) != {item.name for item in fields(cls)}:
            raise ModelError()
        return cls(**value)

class Interpreter(Protocol):
    def interpret(self, current_text: str, safe_context: Mapping[str, object]) -> Interpretation: ...
