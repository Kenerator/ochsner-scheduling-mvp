"""Synthetic interpretation boundary tests; no network or credentials."""
import unittest
from dataclasses import FrozenInstanceError
from scheduling_assistant.interpretation import Interpretation, ModelError

FIELDS = ('specialty','location','appointment_type','phone','dob','zip','start_date','end_date','slot_choice')
def extracted(**changes):
    value = dict.fromkeys(FIELDS)
    value['intent'] = 'provider_lookup'
    value.update(changes)
    return value

class InterpretationTests(unittest.TestCase):
    def test_nullable_answers_are_immutable_and_validated(self):
        value = Interpretation.from_dict(extracted(specialty='primary_care'))
        self.assertEqual(value.specialty, 'primary_care')
        self.assertIsNone(value.phone)
        with self.assertRaises(FrozenInstanceError): value.intent = 'book'
        with self.assertRaises(ValueError): Interpretation(intent='invented')
        with self.assertRaises(ValueError): Interpretation(intent='book', phone=123)
    def test_missing_extra_and_authority_fields_are_rejected(self):
        for field in ('patientId','confirmed','slots','appointmentId','answer'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                Interpretation.from_dict(extracted(**{field:'forbidden'}))
        value = extracted(); del value['phone']
        with self.assertRaises(ValueError): Interpretation.from_dict(value)
        with self.assertRaises(ValueError): Interpretation.from_dict(extracted(intent=None))

import contextlib
import io
import json
from unittest.mock import patch
from scheduling_assistant.openai_adapter import OpenAIInterpreter

def envelope(value=None):
    return {'status':'completed', 'output':[{'type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':json.dumps(extracted() if value is None else value),'annotations':[]}]}]}

class Response:
    def __init__(self, body, status=200):
        self.body = body if isinstance(body,bytes) else json.dumps(body).encode()
        self.status = status
        self.read_limits = []
    def read(self, size):
        self.read_limits.append(size)
        return self.body[:size]
    def __enter__(self): return self
    def __exit__(self, *args): pass

class Transport:
    def __init__(self, response=None, error=None):
        self.response = response or Response(envelope())
        self.error = error
        self.calls = []
    def __call__(self, request, *, timeout):
        self.calls.append((request,timeout))
        if self.error: raise self.error
        return self.response

class OpenAIInterpreterTests(unittest.TestCase):
    def adapter(self, transport):
        return OpenAIInterpreter(model='explicit-test-model',api_key='synthetic-secret',transport=transport)

    def test_request_constrains_fields_and_only_sends_current_safe_context(self):
        transport = Transport(Response(envelope(extracted(intent='book',slot_choice='2'))))
        result = self.adapter(transport).interpret('Choose second',{'state':'slots','slot_count':2})
        self.assertEqual(result.slot_choice,'2')
        self.assertEqual(len(transport.calls),1)
        request, timeout = transport.calls[0]
        self.assertEqual(timeout,30)
        self.assertEqual(request.full_url,'https://api.openai.com/v1/responses')
        self.assertEqual(request.get_method(),'POST')
        self.assertEqual(request.get_header('Authorization'),'Bearer synthetic-secret')
        payload = json.loads(request.data)
        self.assertEqual(payload['model'],'explicit-test-model')
        self.assertIs(payload['store'],False)
        self.assertNotIn('synthetic-secret',request.data.decode())
        self.assertNotIn('previous_response_id',payload)
        format_ = payload['text']['format']
        self.assertEqual(format_['type'],'json_schema')
        self.assertIs(format_['strict'],True)
        schema = format_['schema']
        self.assertIs(schema['additionalProperties'],False)
        self.assertEqual(set(schema['required']),{'intent',*FIELDS})
        self.assertEqual(schema['properties']['phone']['type'],['string','null'])
        self.assertEqual(set(schema['properties']['intent']['enum']),{'provider_lookup','book','appointment_lookup','human','medical_advice','unsupported','unclear'})
        self.assertEqual(json.loads(payload['input'][0]['content']),{'current_text':'Choose second','context':{'state':'slots','slot_count':2}})

    def test_configuration_requires_model_and_key_and_can_read_environment(self):
        transport = Transport()
        with patch.dict('os.environ',{'OPENAI_API_KEY':'synthetic-environment-key'},clear=True):
            OpenAIInterpreter(model='configured-model',transport=transport).interpret('providers',{})
            self.assertEqual(transport.calls[0][0].get_header('Authorization'),'Bearer synthetic-environment-key')
            for model in ('',None):
                with self.assertRaises(ModelError): OpenAIInterpreter(model=model,transport=transport)
        with patch.dict('os.environ',{},clear=True), self.assertRaises(ModelError):
            OpenAIInterpreter(model='configured-model',transport=transport)

    def test_private_and_untyped_context_is_rejected_before_transport(self):
        transport = Transport()
        for context in ({'patientId':'hidden'},{'history':['prior']},{'phone':'hidden'},{'slot_count':True},{'state':{'patient':'hidden'}},{'specialty':'hidden-identity'}):
            with self.subTest(context=context), self.assertRaises(ModelError):
                self.adapter(transport).interpret('providers',context)
        self.assertEqual(transport.calls,[])

    def test_refusal_incomplete_malformed_and_authority_output_are_rejected(self):
        refusal = envelope(); refusal['output'][0]['content'] = [{'type':'refusal','refusal':'private upstream prose'}]
        incomplete = envelope(); incomplete['status'] = 'incomplete'
        msg_incomplete = envelope(); msg_incomplete['output'][0]['status'] = 'incomplete'
        missing = envelope(); missing['output'] = []
        wrongtype = envelope(); wrongtype['output'][0]['content'][0]['text'] = 12
        for response in (refusal,incomplete,msg_incomplete,missing,wrongtype,envelope(extracted(confirmed=True)),b'not json',{'status':'failed','error':{'message':'private'}}):
            transport = Transport(Response(response))
            with self.subTest(response=response), self.assertRaises(ModelError) as error:
                self.adapter(transport).interpret('yes',{})
            self.assertNotIn('private',str(error.exception))
            self.assertEqual(len(transport.calls),1)

    def test_response_read_is_bounded_and_oversized_output_is_rejected(self):
        response = Response(b' '*(1024*1024+2)); transport = Transport(response)
        with self.assertRaises(ModelError): self.adapter(transport).interpret('providers',{})
        self.assertEqual(response.read_limits,[1024*1024+1])
        self.assertEqual(len(transport.calls),1)

    def test_error_paths_do_not_log_expose_raw_errors_or_retry(self):
        for transport in (Transport(error=TimeoutError('synthetic-secret private phone')),Transport(Response({'error':'private'},status=503))):
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output), self.assertRaises(ModelError) as error:
                self.adapter(transport).interpret('synthetic current turn',{})
            self.assertEqual(output.getvalue(),'')
            self.assertNotIn('synthetic-secret',str(error.exception))
            self.assertNotIn('private',str(error.exception))
            self.assertIsNone(error.exception.__cause__)
            self.assertEqual(len(transport.calls),1)

class OutputBoundaryTests(unittest.TestCase):
    def test_duplicate_output_keys_and_unbounded_field_text_are_rejected(self):
        duplicate = envelope()
        original = duplicate['output'][0]['content'][0]['text']
        duplicate['output'][0]['content'][0]['text'] = original[:-1] + ',"intent":"book"}'
        for body in (duplicate,envelope(extracted(phone='x'*501))):
            with self.subTest(body=body), self.assertRaises(ModelError):
                OpenAIInterpreter(model='test-model',api_key='synthetic',transport=Transport(Response(body))).interpret('providers',{})

    def test_non_message_actions_and_top_level_text_never_become_extraction(self):
        for body in ({'status':'completed','output_text':json.dumps(extracted()),'output':[]},
                     {'status':'completed','output':[{'type':'function_call','arguments':json.dumps(extracted())}]}):
            with self.subTest(body=body), self.assertRaises(ModelError):
                OpenAIInterpreter(model='test-model',api_key='synthetic',transport=Transport(Response(body))).interpret('providers',{})

    def test_completed_reasoning_item_can_precede_completed_structured_message(self):
        body = envelope(extracted(intent='medical_advice'))
        body['output'].insert(0,{'type':'reasoning','summary':[]})
        value = OpenAIInterpreter(model='test-model',api_key='synthetic',transport=Transport(Response(body))).interpret('Advice?',{})
        self.assertEqual(value.intent,'medical_advice')
