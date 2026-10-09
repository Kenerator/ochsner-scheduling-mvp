"""Serialized conversation owner. Only current, separately confirmed facts may book."""
from dataclasses import replace
from threading import RLock
from time import monotonic
from .domain import (Preferences, Proposal, View, DomainError, PROCESS_ACTIONS,
                     iso_date, text as valid_text)
from .core import affirmative, choose_slot, matching_appointment, slot_description
from .scheduling_api import APIError

DISCLOSURE = 'AI scheduling assistant — synthetic demonstration. Identity matching is not authentication.'
ASSISTANCE = 'Please contact clinic scheduling staff for assistance. No handoff has been queued.'
UNKNOWN = 'Booking outcome is unknown. Do not retry; ask clinic scheduling staff to verify whether an appointment was created. Reset does not resolve this uncertainty.'

class Session:
    def __init__(self, gateway, interpreter, ledger=None, diagnostics=None):
        self.gateway=gateway; self.interpreter=interpreter
        self.ledger=ledger if ledger is not None else PROCESS_ACTIONS
        self.diagnostics=diagnostics; self._lock=RLock(); self._events={}
        self._revision=0; self._turn=0
        self._clear()
        self._view=View((DISCLOSURE,'How can I help with provider lookup or booking?'), 'start')

    def _clear(self):
        self.preferences=Preferences(); self.phone=None; self.dob=None; self.zip=None
        self.patient=None; self.candidates=(); self.slots=(); self.proposal=None
        self.appointment=None; self.intent='unclear'; self._searched=False
        self._no_matches=0; self._zip_attempts=0; self._excluded=set()

    @property
    def revision(self):
        with self._lock: return self._revision

    @property
    def current_view(self):
        with self._lock: return self._view

    def _show(self, message, state, reason=None, **kwargs):
        if reason is not None: self._reason=reason
        self._view=View((message,),state,revision=self._revision,**kwargs)
        return self._view

    def _emit(self, operation, start, outcome='success', reason=None):
        if self.diagnostics is not None:
            try:
                self.diagnostics(operation=operation,state=self._view.state,intent=self.intent,
                                 outcome=outcome,reason=reason,elapsed_ms=(monotonic()-start)*1000)
            except Exception:
                pass  # Observability must never alter or retry a scheduling effect.

    def _call(self, operation, function, *args):
        start=monotonic()
        try:
            result=function(*args)
        except BaseException as error:
            self._emit(operation,start,'unknown' if getattr(error,'unknown',False) else 'failure',getattr(error,'reason',None))
            raise
        self._emit(operation,start)
        return result

    def _context(self):
        return {key:value for key,value in {
            'state':self._view.state, 'intent':self.intent,
            'specialty':self.preferences.specialty,'location':self.preferences.location,
            'start_date':self.preferences.start_date,'end_date':self.preferences.end_date,
            'required_answer':self._view.state,'slot_count':len(self.slots)
        }.items() if value is not None}

    def submit(self, text, event_id, expected_revision=None):
        with self._lock:
            if event_id in self._events: return self._events[event_id]
            if expected_revision is not None and expected_revision!=self._revision:
                return View(('This control is stale. Use the current conversation controls.',),'stale',revision=self._revision)
            start=monotonic(); self._reason=None
            self._revision+=1; self._turn+=1
            if isinstance(text,str) and text.strip().lower()=='reset':
                self._clear()
                result=self._show(DISCLOSURE+'\n'+(UNKNOWN if self.ledger.unknown else 'Conversation reset. How can I help?'),'unknown' if self.ledger.unknown else 'start')
            else:
                try:
                    valid_text(text)
                    interpretation=self._call('interpret',self.interpreter.interpret,text,self._context())
                    result=self._advance(text,interpretation)
                except APIError as error:
                    self._reason=error.reason
                    self.proposal=None; self.slots=()
                    result=self._show('The scheduling service could not complete this request. '+ASSISTANCE,'assistance')
                except Exception as error:
                    self._reason=getattr(error,'reason','invalid_input')
                    # Fail closed without exposing model, transport or private values.
                    self.proposal=None
                    result=self._show('I could not safely understand or validate that request. Please try a clear answer, or contact clinic scheduling staff. No booking was attempted.','clarify')
            self._emit('reset' if isinstance(text,str) and text.strip().lower()=='reset' else 'submit',start,result.outcome,self._reason)
            self._events[event_id]=result
            return result

    def _advance(self, utterance, item):
        if item.intent in ('human','medical_advice','unsupported','appointment_lookup'):
            self.proposal=None; self.slots=(); self.intent=item.intent
            lead={'human':'Human assistance is available through the clinic.',
                  'medical_advice':'I cannot provide medical advice or triage.',
                  'unsupported':'That request is outside this demonstration.',
                  'appointment_lookup':'Existing appointment lookup is not supported in this demonstration.'}[item.intent]
            return self._show(lead+' '+ASSISTANCE,'assistance',reason='unsupported')
        old_preferences=self.preferences
        updates={key:getattr(item,key) for key in ('specialty','location','start_date','end_date','appointment_type') if getattr(item,key) is not None}
        self.preferences=replace(self.preferences,**updates)
        changed=self.preferences!=old_preferences
        identity_changed=False
        for key in ('phone','dob','zip'):
            value=getattr(item,key)
            if value is not None:
                valid_text(value)
                if key=='dob': iso_date(value)
                if value!=getattr(self,key):
                    setattr(self,key,value); identity_changed=True
                    self.patient=None
                    if key in ('phone','dob'):
                        self.patient=None; self.candidates=(); self._searched=False
                        self.zip=None
        if identity_changed or changed:
            self.proposal=None; self.slots=(); self.appointment=None
        if item.intent!='unclear': self.intent=item.intent
        if self.intent=='provider_lookup':
            self.proposal=None
            rows=self._call('providers',self.gateway.providers,self.preferences)
            message='\n'.join(f'{p.name}: {p.specialty}; locations {", ".join(p.locations)}; modalities {", ".join(p.modalities)}' for p in rows)
            return self._show(message or 'No providers matched those filters. Try another supported location or specialty. '+ASSISTANCE,'providers',providers=rows)
        if self.intent!='book':
            return self._show('Would you like to find providers or book an appointment?','intent')
        if self.ledger.unknown: return self._show(UNKNOWN,'unknown',outcome='unknown')
        if self.appointment is not None and not changed and not identity_changed:
            return self._show('Already booked: '+self.appointment.appointment_id+'. No additional booking was attempted.','completed',appointment=self.appointment,outcome='completed')
        if not self.phone or not self.dob:
            return self._show('To match your synthetic patient record, provide your phone number and date of birth (YYYY-MM-DD).','identity')
        if self.patient is None:
            if not self._searched:
                self.candidates=self._call('find_patients',self.gateway.find_patients,self.phone,self.dob); self._searched=True
                if not self.candidates:
                    self._no_matches+=1
                    return self._show(('No matching patient record. You may correct the phone number or date of birth once.' if self._no_matches==1 else 'The record could not be matched. '+ASSISTANCE),'no_match' if self._no_matches==1 else 'assistance',reason='no_match')
            if len(self.candidates)==1:
                self.patient=self.candidates[0]
            elif len(self.candidates)>1:
                if self.zip is None:
                    return self._show('An additional private matching detail is needed. What is your ZIP code?','zip')
                self._zip_attempts+=1
                matches=tuple(p for p in self.candidates if p.zip_code==self.zip)
                if len(matches)!=1:
                    self.candidates=(); self._searched=True
                    return self._show('The record could not be uniquely matched. '+ASSISTANCE,'assistance',reason='ambiguous')
                self.patient=matches[0]
            else:
                return self._show('The record could not be matched. '+ASSISTANCE,'assistance',reason='no_match')
        if not self.preferences.specialty:
            return self._show('Which specialty: primary care or dermatology?','specialty')
        if self.proposal is not None:
            if item.slot_choice is not None:
                return self._select(item.slot_choice)
            if affirmative(utterance) and not changed and not identity_changed and self.proposal.displayed_turn<self._turn:
                return self._book()
            if utterance.strip().lower() in ('no','cancel','do not book'):
                self.proposal=None
                return self._show('Booking declined. No appointment was created. Choose another displayed slot or contact clinic scheduling staff.','slots',slots=self.slots)
            return self._show('No booking attempted. Confirm the displayed proposal in a separate message with yes, or decline with no.','confirmation',proposal=self.proposal)
        if not self.slots:
            self.slots=tuple(s for s in self._call('availability',self.gateway.availability,self.patient.patient_id,self.preferences) if s.slot_id not in self._excluded)
            if not self.slots:
                return self._show('No available slots matched. Try another location/date range or '+ASSISTANCE,'empty')
            # A choice in the same turn that first obtains slots is not a choice
            # among previously displayed facts.
            return self._show(self._slot_list(),'slots',slots=self.slots)
        if item.slot_choice is not None: return self._select(item.slot_choice)
        return self._show('Choose a currently displayed slot by number.\n'+self._slot_list(),'slots',slots=self.slots)

    def _slot_list(self):
        return '\n'.join(f'{n}. {slot_description(slot)}' for n,slot in enumerate(self.slots,1))

    def _select(self, choice):
        try: slot=choose_slot(choice,self.slots)
        except DomainError:
            self.proposal=None
            return self._show('Choose a currently displayed slot by number.\n'+self._slot_list(),'slots',slots=self.slots)
        self.proposal=Proposal(self.patient,slot,self._revision,self._turn)
        return self._show('Proposed appointment for your matched synthetic record: '+slot_description(slot)+'. Reply yes in a separate message to book this exact appointment, or no to decline.','confirmation',proposal=self.proposal,slots=self.slots)

    def _book(self):
        proposal=self.proposal
        if not self.ledger.claim(proposal.proposal_id):
            return self._show(UNKNOWN if self.ledger.unknown else 'This booking action has already been handled.','unknown' if self.ledger.unknown else 'assistance',outcome='unknown' if self.ledger.unknown else 'not_attempted')
        try:
            appointment=self._call('book',self.gateway.book,proposal.patient.patient_id,proposal.slot)
            if not matching_appointment(appointment,proposal): raise APIError('bad_response',201,unknown=True)
        except BaseException as error:
            unknown=not isinstance(error,APIError) or error.unknown
            self.ledger.resolve(proposal.proposal_id,'unknown' if unknown else 'known_rejected')
            self.proposal=None
            if not isinstance(error,Exception): raise
            if unknown: return self._show(UNKNOWN,'unknown',outcome='unknown')
            if error.reason=='conflict':
                self._excluded.add(proposal.slot.slot_id)
                self.slots=tuple(s for s in self._call('availability',self.gateway.availability,self.patient.patient_id,self.preferences) if s.slot_id not in self._excluded)
                return self._show('That slot was taken. No appointment was created. Choose a fresh option and confirm again.\n'+(self._slot_list() if self.slots else 'No alternative slots remain. '+ASSISTANCE),'slots' if self.slots else 'empty',slots=self.slots,outcome='known_rejected')
            return self._show('The service rejected this booking; no appointment was created. '+ASSISTANCE,'assistance',outcome='known_rejected')
        self.ledger.resolve(proposal.proposal_id,'completed')
        self.appointment=appointment; self.proposal=None; self.slots=()
        return self._show('Booked appointment '+appointment.appointment_id+': '+slot_description(proposal.slot)+'.','completed',appointment=appointment,outcome='completed')
