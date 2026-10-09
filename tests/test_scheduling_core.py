import unittest
from dataclasses import FrozenInstanceError
from scheduling_assistant.domain import (Preferences, Patient, Provider, Slot, Appointment, Proposal, View, ActionLedger, DomainError)


class DomainTests(unittest.TestCase):
    def test_invalid_preferences_and_dates_cannot_become_state(self):
        for values in ({'specialty': 'cardiology'}, {'location': 'elsewhere'}, {'start_date': '2026-02-30'}, {'start_date':'2026-10-10','end_date':'2026-10-09'}, {'appointment_type':'surgery'}):
            with self.subTest(fields=tuple(values)):
                with self.assertRaises(DomainError): Preferences(**values)
        self.assertEqual(Preferences(specialty='primary_care',location='downtown').specialty,'primary_care')

    def test_returned_types_reject_missing_or_unusable_facts(self):
        with self.assertRaises(DomainError): Patient('', '555-0101', '1985-04-12', '70115')
        with self.assertRaises(DomainError): Patient('p', '555-0101', '1985-02-30', '70115')
        with self.assertRaises(DomainError): Slot('s','pr','primary_care','downtown','2026-10-10T09:00:00',True)
        with self.assertRaises(DomainError): Slot('s','pr','primary_care','downtown','2026-10-10T09:00:00-05:00','true')
        with self.assertRaises(DomainError): Provider('p','Name','primary_care',('nowhere',),('in_person',))
        with self.assertRaises(DomainError): Appointment('a','p','pr','primary_care','downtown','2026-10-10T09:00:00-05:00','pending')

    def test_proposal_and_views_are_immutable_snapshots(self):
        patient=Patient('p','555-0101','1985-04-12','00123')
        slot=Slot('s','pr','primary_care','downtown','2026-10-10T09:00:00-05:00',True)
        proposal=Proposal(patient,slot,2,3)
        view=View(('Confirm?',),'confirmation',proposal=proposal,revision=2)
        with self.assertRaises(FrozenInstanceError): slot.location='uptown'
        with self.assertRaises(FrozenInstanceError): view.state='booked'
        self.assertEqual(proposal.patient.zip_code,'00123')
        self.assertEqual(view.text,'Confirm?')

    def test_unknown_action_guard_cannot_be_cleared_by_new_session(self):
        ledger=ActionLedger()
        self.assertTrue(ledger.claim('one'))
        self.assertFalse(ledger.claim('one'))
        self.assertFalse(ledger.claim('two'))
        ledger.resolve('one','unknown')
        self.assertTrue(ledger.unknown)
        self.assertFalse(ledger.claim('two'))

    def test_completed_action_cannot_be_reclaimed(self):
        ledger=ActionLedger()
        self.assertTrue(ledger.claim('one'))
        ledger.resolve('one','completed')
        self.assertFalse(ledger.claim('one'))
        self.assertTrue(ledger.claim('two'))

class SafetyTests(unittest.TestCase):
    def test_confirmation_requires_a_standalone_affirmative(self):
        from scheduling_assistant.core import affirmative
        for value in ('yes', ' YES! ', 'confirm.', 'yes, book it'):
            self.assertTrue(affirmative(value))
        for value in ('yes but uptown','sure maybe','book the first one and yes','no','yes if morning'):
            self.assertFalse(affirmative(value))

    def test_choice_must_be_a_current_displayed_slot(self):
        from scheduling_assistant.core import choose_slot
        slot=Slot('returned','pr','primary_care','downtown','2026-10-10T09:00:00-05:00')
        self.assertEqual(choose_slot('1',(slot,)),slot)
        self.assertEqual(choose_slot('returned',(slot,)),slot)
        for value in ('2','invented','0','-1'):
            with self.assertRaises(DomainError): choose_slot(value,(slot,))

    def test_appointment_must_match_every_proposed_fact(self):
        from scheduling_assistant.core import matching_appointment
        patient=Patient('p','555-0101','1985-04-12','70115')
        slot=Slot('s','pr','primary_care','downtown','2026-10-10T09:00:00-05:00')
        proposal=Proposal(patient,slot,1,1)
        good=Appointment('a','p','pr','primary_care','downtown',slot.start_time,'scheduled')
        bad=Appointment('a','other','pr','primary_care','downtown',slot.start_time,'scheduled')
        self.assertTrue(matching_appointment(good,proposal))
        self.assertFalse(matching_appointment(bad,proposal))
