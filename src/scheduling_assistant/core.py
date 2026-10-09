"""Pure safety predicates. Models and presentation cannot supply effect authority."""
from .domain import DomainError

def affirmative(value):
    normalized=value.strip().lower().strip(' .!?')
    return normalized in ('yes','confirm','yes, book it')

def choose_slot(choice, slots):
    if not isinstance(choice,str): raise DomainError('Choose a displayed option')
    if choice.isdecimal():
        index=int(choice)-1
        if 0<=index<len(slots): return slots[index]
    for slot in slots:
        if choice==slot.slot_id: return slot
    raise DomainError('Choose a currently displayed option')

def matching_appointment(appointment, proposal):
    slot=proposal.slot
    return (appointment.patient_id==proposal.patient.patient_id and
            (appointment.provider_id,appointment.specialty,appointment.location,appointment.start_time,appointment.status)==
            (slot.provider_id,slot.specialty,slot.location,slot.start_time,'scheduled'))

def slot_description(slot):
    return f'{slot.specialty} at {slot.location}, {slot.start_time} (provider {slot.provider_id}; slot {slot.slot_id})'
