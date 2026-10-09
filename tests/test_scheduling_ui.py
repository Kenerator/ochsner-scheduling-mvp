"""UI bridge tests use the actual Session with synthetic collaborators."""
import importlib.util
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from scheduling_assistant.domain import ActionLedger, Provider
from scheduling_assistant.interpretation import Interpretation
from scheduling_assistant.session import Session
from scheduling_assistant.ui_bridge import UIBridge, configured_bridge

class Interpreter:
    def __init__(self): self.calls=[]
    def interpret(self,text,context):
        self.calls.append(text)
        return Interpretation(intent='provider_lookup',specialty='primary_care',location='downtown')
class Gateway:
    def __init__(self): self.calls=[]
    def providers(self,prefs):
        self.calls.append('providers')
        return (Provider('provider_synthetic','<script>alert("service")</script>','primary_care',('downtown',),('in_person',)),)

def bridge():
    gateway=Gateway(); interpreter=Interpreter()
    return UIBridge(Session(gateway,interpreter,ActionLedger())), gateway, interpreter

class UIBridgeTests(unittest.TestCase):
    def test_duplicate_submission_and_render_do_not_repeat_effects(self):
        ui,gateway,interpreter=bridge()
        old=ui.snapshot
        result=ui.submit('providers','event-1',expected_revision=0)
        self.assertEqual(result.view.state,'providers')
        self.assertEqual(ui.submit('providers','event-1',expected_revision=0),result)
        for _ in range(3): ui.render_html()
        self.assertEqual(gateway.calls,['providers'])
        self.assertEqual(interpreter.calls,['providers'])
        self.assertEqual(len(result.transcript),3)
        self.assertEqual(len(old.transcript),1)

    def test_stale_control_does_not_interpret_or_mutate_current_transcript(self):
        ui,gateway,interpreter=bridge()
        current=ui.submit('providers','first',expected_revision=0)
        stale=ui.submit('yes','stale-confirm',expected_revision=0)
        self.assertEqual(stale.view.state,'stale')
        self.assertEqual(ui.snapshot.transcript,current.transcript)
        self.assertEqual(gateway.calls,['providers'])
        self.assertEqual(interpreter.calls,['providers'])

    def test_transcript_is_escaped_and_instances_are_isolated(self):
        ui,_,_=bridge(); other,_,_=bridge()
        ui.submit('<img src=x onerror=alert(1)>','a',expected_revision=0)
        rendered=ui.render_html()
        self.assertNotIn('<script>',rendered)
        self.assertNotIn('<img src=x',rendered)
        self.assertIn('&lt;script&gt;',rendered)
        self.assertIn('&lt;img',rendered)
        self.assertEqual(other.snapshot.view.revision,0)
        self.assertEqual(len(other.snapshot.transcript),1)

    def test_reset_clears_transcript_but_preserves_unknown_warning(self):
        ui,_,_=bridge()
        ui.submit('providers','a',expected_revision=0)
        ui.session.ledger.unknown=True
        reset=ui.submit('reset','reset',expected_revision=1)
        self.assertEqual(len(reset.transcript),1)
        self.assertEqual(reset.view.state,'unknown')
        self.assertIn('unknown',reset.transcript[0][1])
        self.assertNotIn('onerror',ui.render_html())

    def test_overlapping_submission_is_rejected_while_processing(self):
        ui,gateway,interpreter=bridge()
        entered=threading.Event(); release=threading.Event()
        original=interpreter.interpret
        def blocked(text,context):
            entered.set(); release.wait(3)
            return original(text,context)
        interpreter.interpret=blocked
        worker=threading.Thread(target=lambda:ui.submit('providers','first',expected_revision=0))
        worker.start(); self.assertTrue(entered.wait(2))
        self.assertTrue(ui.pending)
        rejected=ui.submit('yes','overlap',expected_revision=0)
        self.assertEqual(rejected.view.state,'processing')
        self.assertTrue(worker.is_alive(), 'Pending response must not wait for the first turn')
        release.set(); worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertFalse(ui.pending)
        self.assertEqual(gateway.calls,['providers'])

    def test_missing_configuration_is_safe_and_calls_no_model(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaises(ValueError) as caught:
            configured_bridge()
        self.assertNotIn('key value',str(caught.exception))

    def test_configuration_wires_live_adapters_and_explicit_model(self):
        with patch.dict(os.environ,{'SCHEDULING_MODEL':'explicit-model','OPENAI_API_KEY':'synthetic-secret','SCHEDULING_API_URL':'http://127.0.0.1:4010'},clear=True):
            ui=configured_bridge()
        self.assertEqual(ui.session.interpreter.model,'explicit-model')
        self.assertEqual(type(ui.session.gateway).__name__,'SchedulingAPI')
        self.assertEqual(ui.snapshot.view.state,'start')

    def test_marimo_app_loads_without_configuration_or_side_effects(self):
        path=Path(__file__).resolve().parents[1]/'apps/scheduling_app.py'
        spec=importlib.util.spec_from_file_location('scheduling_ui_test',path)
        module=importlib.util.module_from_spec(spec)
        with patch.dict(os.environ,{},clear=True): spec.loader.exec_module(module)
        self.assertEqual(module.app.__class__.__name__,'App')

class UIBookingTests(unittest.TestCase):
    def test_stale_confirmation_and_double_click_cannot_repeat_booking(self):
        from scheduling_assistant.domain import Patient,Slot,Appointment
        patient=Patient('patient-test','555-0100','1980-01-01','00123')
        slot=Slot('slot-test','provider-test','primary_care','downtown','2026-10-20T10:00:00-05:00')
        class BookingGateway:
            def __init__(self): self.books=[]
            def find_patients(self,*args): return (patient,)
            def availability(self,*args): return (slot,)
            def book(self,patient_id,chosen):
                self.books.append((patient_id,chosen))
                return Appointment('appointment-test',patient_id,chosen.provider_id,chosen.specialty,chosen.location,chosen.start_time,'scheduled')
        class Turns:
            def __init__(self):
                self.turns=iter((Interpretation('book',specialty='primary_care',phone=patient.phone,dob=patient.dob),Interpretation('unclear',slot_choice='1'),Interpretation('unclear')))
            def interpret(self,*args): return next(self.turns)
        gateway=BookingGateway();ui=UIBridge(Session(gateway,Turns(),ActionLedger()))
        ui.submit('book','start',expected_revision=0)
        selected=ui.submit('first','choice',expected_revision=1)
        self.assertEqual(selected.view.state,'confirmation')
        self.assertEqual(gateway.books,[])
        stale=ui.submit('yes','old-confirm',expected_revision=1)
        self.assertEqual(stale.view.state,'stale')
        self.assertEqual(gateway.books,[])
        result=ui.submit('yes','confirm',expected_revision=2)
        self.assertEqual(result.view.outcome,'completed')
        self.assertEqual(ui.submit('yes','confirm',expected_revision=2),result)
        for _ in range(3): ui.render_html()
        self.assertEqual(len(gateway.books),1)

    def test_duplicate_before_reset_cannot_restore_private_transcript(self):
        ui,_,_=bridge()
        ui.submit('private synthetic turn','old',expected_revision=0)
        ui.submit('reset','reset',expected_revision=1)
        result=ui.submit('private synthetic turn','old',expected_revision=0)
        self.assertEqual(len(result.transcript),1)
        self.assertNotIn('private synthetic turn',ui.render_html())

class ConfiguredUIDiagnosticsTests(unittest.TestCase):
    def test_configured_session_retains_safe_events_for_an_actual_turn(self):
        with patch.dict(os.environ,{'SCHEDULING_MODEL':'explicit-model','OPENAI_API_KEY':'synthetic-secret'},clear=True):
            ui=configured_bridge()
        self.assertIsNotNone(ui.session.diagnostics)
        # Exercise the configured Session with local boundaries; no HTTPS request.
        ui.session.gateway=Gateway()
        ui.session.interpreter=Interpreter()
        ui.submit('synthetic-private-input','diagnostic-turn',expected_revision=0)
        events=ui.session.diagnostics.events
        self.assertEqual([event['operation'] for event in events],['interpret','providers','submit'])
        self.assertTrue(all('elapsed_ms' in event for event in events))
        self.assertTrue(all(set(event)<= {'operation','state','intent','outcome','reason','elapsed_ms'} for event in events))
        for forbidden in ('synthetic-private-input','synthetic-secret','provider_synthetic'):
            self.assertNotIn(forbidden,str(events))

class MarimoCallbackCycleTests(unittest.TestCase):
    def test_submitted_callback_reschedules_its_controls_after_state_change(self):
        # Use the pinned Marimo app, real form callback and its actual graph
        # scheduler: no UI substitute or mocked reactivity is involved.
        from marimo._runtime.runner.cell_runner import Runner
        from marimo._runtime.runner.hooks import NotebookCellHooks
        path=Path(__file__).resolve().parents[1]/'apps/scheduling_app.py'
        spec=importlib.util.spec_from_file_location('ui_callback_cycle',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        ui,gateway,_=bridge()
        _,definitions=module.app.run(defs={'bridge':ui,'configuration_error':None})
        form=definitions['message_form']
        controls_id=next(cid for cid,cell in module.app._graph.cells.items() if 'message_form' in cell.defs)
        form._on_change('providers')
        self.assertEqual(ui.snapshot.view.state,'providers')
        self.assertEqual(gateway.calls,['providers'])
        runner=Runner(set(),module.app._graph,dict(definitions),None,NotebookCellHooks())
        scheduled=runner.resolve_state_updates({definitions['get_snapshot']:controls_id})
        self.assertIn(controls_id,scheduled,'The submitted callback must rebuild its form and buttons')
        _,rerendered=module.app.run(defs={
            'bridge':ui,'configuration_error':None,
            'get_snapshot':definitions['get_snapshot'],'set_snapshot':definitions['set_snapshot'],
        })
        self.assertIsNot(rerendered['message_form'],form)
        rerendered['message_form']._on_change('providers again')
        self.assertEqual(gateway.calls,['providers','providers'])
