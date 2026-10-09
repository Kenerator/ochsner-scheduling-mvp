import unittest
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from scheduling_assistant.domain import ActionLedger, Provider
from scheduling_assistant.interpretation import Interpretation
from scheduling_assistant.session import Session

class Scripted:
    def __init__(self,*items): self.items=deque(items);self.calls=[]
    def interpret(self,text,context):
        self.calls.append(context)
        value=self.items.popleft()
        if isinstance(value,Exception): raise value
        return value

class Gateway:
    def __init__(self): self.calls=[]
    def providers(self,preferences):
        self.calls.append(('providers',preferences))
        return (Provider('pr','Dr Synthetic','primary_care',('downtown',),('in_person',)),)

class DiscoveryTests(unittest.TestCase):
    def make(self,*items):
        gateway=Gateway();interpreter=Scripted(*items)
        return Session(gateway,interpreter,ledger=ActionLedger()),gateway,interpreter
    def test_discovery_needs_no_identity_and_renders_only_returned_provider(self):
        session,gateway,interpreter=self.make(Interpretation(intent='provider_lookup',specialty='primary_care',location='downtown'))
        view=session.submit('Which primary care doctors are downtown?','one')
        self.assertIn('Dr Synthetic',view.text)
        self.assertNotIn('date of birth',view.text.lower())
        self.assertEqual([x[0] for x in gateway.calls],['providers'])
        self.assertNotIn('patient_id',interpreter.calls[0])
    def test_context_retains_preferences_across_followup(self):
        session,gateway,interpreter=self.make(Interpretation(intent='provider_lookup',specialty='primary_care'),Interpretation(intent='unclear',location='downtown'))
        session.submit('primary care providers','one');session.submit('downtown','two')
        self.assertEqual(gateway.calls[-1][1].specialty,'primary_care')
        self.assertEqual(gateway.calls[-1][1].location,'downtown')
    def test_duplicate_and_concurrent_event_has_one_interpretation_and_read(self):
        session,gateway,interpreter=self.make(Interpretation(intent='provider_lookup'))
        with ThreadPoolExecutor(max_workers=2) as pool:
            views=list(pool.map(lambda _:session.submit('providers','same'),range(2)))
        self.assertEqual(views[0],views[1]);self.assertEqual(len(interpreter.calls),1);self.assertEqual(len(gateway.calls),1)
    def test_stale_ui_event_cannot_answer_next_question(self):
        session,gateway,interpreter=self.make(Interpretation(intent='provider_lookup'))
        revision=session.revision
        session.submit('providers','one',expected_revision=revision)
        view=session.submit('yes','old',expected_revision=revision)
        self.assertIn('stale',view.text.lower());self.assertEqual(len(interpreter.calls),1)
    def test_model_failure_exposes_no_raw_error_and_no_effect(self):
        session,gateway,interpreter=self.make(ValueError('private-sentinel'))
        view=session.submit('providers','one')
        self.assertNotIn('private-sentinel',view.text);self.assertEqual(gateway.calls,[])
    def test_unsupported_advice_human_and_lookup_stop_calls(self):
        for intent in ('medical_advice','human','unsupported','appointment_lookup'):
            with self.subTest(intent=intent):
                session,gateway,interpreter=self.make(Interpretation(intent=intent))
                view=session.submit('request','one')
                self.assertIn('clinic',view.text.lower());self.assertEqual(gateway.calls,[])
    def test_reset_retains_unknown_guard_and_invalidates_old_controls(self):
        session,gateway,interpreter=self.make()
        session.ledger.unknown=True
        view=session.submit('reset','reset')
        self.assertIn('unknown',view.text.lower());self.assertTrue(session.ledger.unknown)

from scheduling_assistant.domain import Patient, Slot, Appointment
from scheduling_assistant.scheduling_api import APIError

P=Patient('private-patient','555-0100','1980-01-01','00123')
S=Slot('slot-a','provider-a','primary_care','downtown','2026-10-20T10:00:00-05:00')
S2=Slot('slot-b','provider-b','primary_care','downtown','2026-10-21T10:00:00-05:00')
class BookingGateway(Gateway):
    def __init__(self,patients=(P,),slots=(S,S2),error=None):
        super().__init__();self.patients=patients;self.slots=slots;self.error=error
    def find_patients(self,phone,dob):
        self.calls.append(('patients',phone,dob));return self.patients
    def availability(self,patient_id,preferences):
        self.calls.append(('availability',patient_id));return self.slots
    def book(self,patient_id,slot):
        self.calls.append(('book',patient_id,slot))
        if self.error: raise self.error
        return Appointment('appointment-a',patient_id,slot.provider_id,slot.specialty,slot.location,slot.start_time,'scheduled')

class BookingTests(unittest.TestCase):
    def make(self,*items,gateway=None):
        gateway=gateway or BookingGateway(); interpreter=Scripted(*items)
        return Session(gateway,interpreter,ledger=ActionLedger()),gateway,interpreter
    def start(self,*tail,gateway=None):
        session,gateway,interpreter=self.make(Interpretation('book',specialty='primary_care',location='downtown',phone=P.phone,dob=P.dob),*tail,gateway=gateway)
        view=session.submit('book primary care downtown phone 555-0100 DOB 1980-01-01','start')
        self.assertEqual(view.state,'slots');self.assertEqual(self.books(gateway),[])
        return session,gateway,interpreter
    def books(self,gateway): return [x for x in gateway.calls if x[0]=='book']
    def test_exact_separate_consent_and_repeat_and_duplicate_never_rebook(self):
        session,gateway,interpreter=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('unclear'))
        proposal=session.submit('first','choice');self.assertEqual(proposal.state,'confirmation')
        self.assertEqual(self.books(gateway),[])
        result=session.submit('yes','consent');self.assertEqual(result.outcome,'completed')
        self.assertEqual(session.submit('yes','consent'),result)
        self.assertEqual(session.submit('yes','repeat').outcome,'completed');self.assertEqual(len(self.books(gateway)),1)
    def test_same_turn_choice_yes_and_mixed_consent_never_book(self):
        session,gateway,interpreter=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear'))
        session.submit('first, yes book it','choice')
        view=session.submit('yes but change something','mixed')
        self.assertEqual(view.state,'confirmation');self.assertEqual(self.books(gateway),[])
    def test_decline_clears_proposal(self):
        session,gateway,_=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('unclear'))
        session.submit('first','choice');session.submit('no','decline');session.submit('yes','old')
        self.assertIsNone(session.proposal);self.assertEqual(self.books(gateway),[])
    def test_changed_location_invalidates_proposal_and_old_confirmation(self):
        gateway=BookingGateway(slots=(S,))
        session,gateway,_=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear',location='uptown'),Interpretation('unclear'),gateway=gateway)
        session.submit('first','choice');session.submit('uptown instead','change');session.submit('yes','old')
        self.assertEqual(self.books(gateway),[])
    def test_identity_required_before_availability(self):
        session,gateway,_=self.make(Interpretation('book',specialty='primary_care'),Interpretation('unclear',phone=P.phone),Interpretation('unclear',dob=P.dob))
        session.submit('book','one');session.submit('phone','two');self.assertEqual(gateway.calls,[])
        session.submit('dob','three');self.assertEqual([c[0] for c in gateway.calls],['patients','availability'])
    def test_duplicate_zip_resolves_privately_without_second_api_search(self):
        other=Patient('other-private',P.phone,P.dob,'99999')
        session,gateway,model=self.make(Interpretation('book',specialty='primary_care',phone=P.phone,dob=P.dob),Interpretation('unclear',zip='00123'),gateway=BookingGateway(patients=(P,other)))
        view=session.submit('book','one');self.assertEqual(view.state,'zip')
        for secret in ('private-patient','other-private','00123','99999'): self.assertNotIn(secret,view.text)
        view=session.submit('00123','two');self.assertEqual(view.state,'slots');self.assertEqual(session.patient,P)
        self.assertEqual([c[0] for c in gateway.calls],['patients','availability'])
        self.assertNotIn('00123',str(model.calls));self.assertNotIn('private-patient',str(model.calls))
    def test_no_match_one_correction_then_assistance_no_patient_details(self):
        session,gateway,_=self.make(Interpretation('book',specialty='primary_care',phone=P.phone,dob=P.dob),Interpretation('unclear',phone='555-9999'),gateway=BookingGateway(patients=()))
        first=session.submit('book','one');self.assertEqual(first.state,'no_match')
        second=session.submit('correct','two');self.assertEqual(second.state,'assistance')
        self.assertEqual([c[0] for c in gateway.calls],['patients','patients'])
        self.assertNotIn(P.phone,first.text+second.text)
    def test_conflict_excludes_trap_and_requires_fresh_choice_consent(self):
        gateway=BookingGateway(error=APIError('conflict',409))
        session,gateway,_=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('unclear'),Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),gateway=gateway)
        session.submit('first','choice');view=session.submit('yes','consent')
        self.assertEqual(view.outcome,'known_rejected');self.assertEqual(view.slots,(S2,))
        session.submit('yes','stale');self.assertEqual(len(self.books(gateway)),1)
        gateway.error=None;session.submit('first','fresh');result=session.submit('yes','fresh-consent')
        self.assertEqual(result.outcome,'completed');self.assertEqual(len(self.books(gateway)),2)
    def test_unknown_write_freezes_after_reset_without_raw_error(self):
        session,gateway,_=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),gateway=BookingGateway(error=TimeoutError('private-sentinel')))
        session.submit('first','choice');view=session.submit('yes','consent')
        self.assertEqual(view.outcome,'unknown');self.assertNotIn('private-sentinel',view.text)
        session.submit('reset','reset');view=session.submit('book again','again')
        self.assertEqual(view.outcome,'unknown');self.assertEqual(len(self.books(gateway)),1)
    def test_interrupted_write_sets_unknown_before_propagating(self):
        session,gateway,_=self.start(Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),gateway=BookingGateway(error=KeyboardInterrupt()))
        session.submit('first','choice')
        with self.assertRaises(KeyboardInterrupt):session.submit('yes','consent')
        self.assertTrue(session.ledger.unknown)
    def test_model_refusal_invalidates_pending_consent(self):
        session,gateway,_=self.start(Interpretation('unclear',slot_choice='1'),ValueError('private'),Interpretation('unclear'))
        session.submit('first','choice');session.submit('yes','refused');session.submit('yes','old')
        self.assertEqual(self.books(gateway),[])
    def test_changed_zip_clears_previously_resolved_patient(self):
        other=Patient('other-private',P.phone,P.dob,'99999')
        session,gateway,_=self.make(Interpretation('book',specialty='primary_care',phone=P.phone,dob=P.dob),Interpretation('unclear',zip='00123'),Interpretation('unclear',slot_choice='1'),Interpretation('unclear',zip='99999'),gateway=BookingGateway(patients=(P,other)))
        session.submit('book','one');session.submit('00123','two');session.submit('first','three');session.submit('99999 instead','four')
        self.assertEqual(session.patient,other);self.assertIsNone(session.proposal);self.assertEqual(self.books(gateway),[])

class SessionDiagnosticsTests(unittest.TestCase):
    def test_operation_diagnostics_are_present_timed_and_private(self):
        from scheduling_assistant.diagnostics import Diagnostics
        sink=Diagnostics();gateway=BookingGateway()
        session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),Interpretation('unclear',slot_choice='1'),Interpretation('unclear')),ledger=ActionLedger(),diagnostics=sink)
        for event,turn in enumerate(('book','first','yes')):session.submit(turn,str(event))
        operations={e.get('operation') for e in sink.events}
        self.assertTrue({'interpret','find_patients','availability','book','submit'}<=operations)
        self.assertTrue(all(e['elapsed_ms']>=0 for e in sink.events))
        for secret in (P.patient_id,P.phone,P.dob,P.zip_code,S.slot_id):self.assertNotIn(secret,str(sink.events))
    def test_diagnostic_failure_does_not_change_confirmed_action(self):
        def broken(**event):raise RuntimeError('private-sentinel')
        gateway=BookingGateway();session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),Interpretation('unclear',slot_choice='1'),Interpretation('unclear')),ledger=ActionLedger(),diagnostics=broken)
        for event,turn in enumerate(('book','first','yes')):view=session.submit(turn,str(event))
        self.assertEqual(view.outcome,'completed');self.assertEqual(len([x for x in gateway.calls if x[0]=='book']),1)

class IdentityMutationTests(unittest.TestCase):
    def test_phone_change_requires_fresh_zip_for_new_duplicate_candidates(self):
        other=Patient('other-private',P.phone,P.dob,'99999')
        new=Patient('new-private','555-0200',P.dob,P.zip_code)
        new_other=Patient('new-other','555-0200',P.dob,'99999')
        gateway=BookingGateway(patients=(P,other))
        session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),Interpretation('unclear',zip=P.zip_code),Interpretation('unclear',phone=new.phone)),ledger=ActionLedger())
        session.submit('book','one');session.submit('ZIP','two');gateway.patients=(new,new_other)
        view=session.submit('new phone','three')
        self.assertEqual(view.state,'zip');self.assertIsNone(session.patient)
        self.assertEqual(len([x for x in gateway.calls if x[0]=='availability']),1)
    def test_identity_change_after_success_does_not_claim_previous_booking_for_new_patient(self):
        gateway=BookingGateway()
        session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('book',phone='555-0200'),Interpretation('unclear',slot_choice='1')),ledger=ActionLedger())
        for n,turn in enumerate(('book','first','yes')):session.submit(turn,str(n))
        gateway.patients=(Patient('new-private','555-0200',P.dob,'99999'),)
        session.submit('book for another phone','new')
        view=session.submit('first','choice')
        self.assertEqual(view.state,'confirmation');self.assertEqual(view.proposal.patient.patient_id,'new-private')
        self.assertEqual(len([x for x in gateway.calls if x[0]=='book']),1)

class EscalationDiagnosticsTests(unittest.TestCase):
    def test_no_match_and_unsupported_have_safe_reason_codes(self):
        from scheduling_assistant.diagnostics import Diagnostics
        for interpretation,expected,gateway in ((Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),'no_match',BookingGateway(patients=())),(Interpretation('medical_advice'),'unsupported',BookingGateway())):
            sink=Diagnostics();session=Session(gateway,Scripted(interpretation),ledger=ActionLedger(),diagnostics=sink)
            session.submit('request','one')
            self.assertEqual(sink.events[-1]['reason'],expected)
    def test_ambiguous_zip_has_distinct_reason(self):
        from scheduling_assistant.diagnostics import Diagnostics
        sink=Diagnostics();gateway=BookingGateway(patients=(P,Patient('other',P.phone,P.dob,'99999')))
        session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),Interpretation('unclear',zip='00000')),ledger=ActionLedger(),diagnostics=sink)
        session.submit('book','one');session.submit('ZIP','two')
        self.assertEqual(sink.events[-1]['reason'],'ambiguous')

class BoundedFollowupTests(unittest.TestCase):
    def test_missing_identity_question_does_not_reask_supplied_phone(self):
        session=Session(BookingGateway(),Scripted(Interpretation('book',phone=P.phone)),ledger=ActionLedger())
        view=session.submit('book with phone','one')
        self.assertIn('date of birth',view.text);self.assertNotIn('phone number',view.text)
    def test_second_no_match_stops_further_search_until_reset(self):
        gateway=BookingGateway(patients=());session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob),Interpretation('unclear',phone='555-0200'),Interpretation('unclear',phone='555-0300')),ledger=ActionLedger())
        for n,turn in enumerate(('book','correct once','correct again')):view=session.submit(turn,str(n))
        self.assertEqual(view.state,'assistance');self.assertEqual(len(gateway.calls),2)
    def test_new_preferences_end_conflict_exclusion_cycle(self):
        gateway=BookingGateway(error=APIError('conflict',409));session=Session(gateway,Scripted(Interpretation('book',phone=P.phone,dob=P.dob,specialty='primary_care'),Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('unclear',location='downtown')),ledger=ActionLedger())
        for n,turn in enumerate(('book','first','yes')):session.submit(turn,str(n))
        view=session.submit('downtown please','new-search')
        self.assertIn(S,view.slots)

class UnsupportedScopeTests(unittest.TestCase):
    def test_explicit_unsupported_specialty_stops_with_reason_specific_assistance(self):
        gateway=BookingGateway();session=Session(gateway,Scripted(Interpretation('book',specialty='neurology')),ledger=ActionLedger())
        view=session.submit('book neurology','one')
        self.assertEqual(view.state,'assistance');self.assertIn('supported',view.text.lower());self.assertEqual(gateway.calls,[])

class PersonaBehaviorTests(unittest.TestCase):
    """Pinned Jules/Ellie-Rae/Morgan-Rae/Sam-Rae hypothesis checks."""
    def test_invalid_number_keeps_current_choices_and_invalidates_old_consent(self):
        gateway=BookingGateway()
        model=Scripted(Interpretation('book',specialty='primary_care',phone=P.phone,dob=P.dob),Interpretation('unclear',slot_choice='1'),Interpretation('unclear',slot_choice='99'),Interpretation('unclear'))
        session=Session(gateway,model,ActionLedger())
        session.submit('book','start');session.submit('1','select')
        view=session.submit('99','invalid')
        self.assertEqual(view.state,'slots');self.assertEqual(view.slots,(S,S2))
        self.assertIn('1.',view.text);self.assertIn('2.',view.text)
        self.assertIsNone(session.proposal)
        session.submit('yes','old-consent')
        self.assertFalse(any(c[0]=='book' for c in gateway.calls))
        self.assertEqual(sum(c[0]=='patients' for c in gateway.calls),1)

    def test_failed_interpretation_cannot_preserve_a_confirmable_proposal(self):
        gateway=BookingGateway()
        model=Scripted(Interpretation('book',specialty='primary_care',phone=P.phone,dob=P.dob),Interpretation('unclear',slot_choice='1'),ValueError('private-model-detail'),Interpretation('unclear'))
        session=Session(gateway,model,ActionLedger())
        session.submit('book','start');session.submit('1','select')
        failed=session.submit('change preference','failed')
        self.assertIsNone(session.proposal);self.assertIsNone(failed.proposal)
        self.assertNotIn('private-model-detail',failed.text)
        session.submit('yes','old-consent')
        self.assertFalse(any(c[0]=='book' for c in gateway.calls))

    def test_support_context_separates_known_missing_outcome_without_private_values(self):
        gateway=BookingGateway()
        model=Scripted(Interpretation('book',specialty='primary_care',location='downtown',phone=P.phone),Interpretation('human'))
        session=Session(gateway,model,ActionLedger())
        session.submit('book','start');view=session.submit('I need staff help','help')
        self.assertIn('Known:',view.text);self.assertIn('primary_care',view.text)
        self.assertIn('Missing:',view.text);self.assertIn('date of birth',view.text)
        self.assertIn('Booking outcome: not attempted',view.text)
        for private in (P.phone,P.dob,P.patient_id,P.zip_code):self.assertNotIn(private,view.text)
        self.assertIn('No handoff has been queued',view.text)
        self.assertEqual(gateway.calls,[])

    def test_support_context_retains_actual_booking_outcome(self):
        for error,outcome in ((None,'completed'),(APIError('unavailable',503),'known rejected'),(APIError('transport',unknown=True),'unknown')):
            with self.subTest(outcome=outcome):
                gateway=BookingGateway(error=error)
                model=Scripted(Interpretation('book',specialty='primary_care',phone=P.phone,dob=P.dob),Interpretation('unclear',slot_choice='1'),Interpretation('unclear'),Interpretation('human'))
                session=Session(gateway,model,ActionLedger())
                session.submit('book','start');session.submit('1','select');session.submit('yes','consent')
                calls=list(gateway.calls);view=session.submit('staff help','help')
                self.assertIn('Booking outcome: '+outcome,view.text)
                self.assertEqual(view.outcome,outcome.replace(' ','_'))
                self.assertEqual(gateway.calls,calls)
                self.assertIn('No handoff has been queued',view.text)
                if outcome=='unknown':self.assertIn('Do not retry',view.text)
