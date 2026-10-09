"""Presentation-only state. Session owns every scheduling decision and effect."""
from dataclasses import dataclass
from html import escape
import os
from threading import Lock

from .diagnostics import Diagnostics
from .domain import View
from .openai_adapter import OpenAIInterpreter
from .scheduling_api import SchedulingAPI
from .session import Session

@dataclass(frozen=True)
class UISnapshot:
    view: View
    transcript: tuple[tuple[str,str],...]

class UIBridge:
    def __init__(self, session):
        self.session=session
        self._snapshot=UISnapshot(session.current_view,(('Assistant',session.current_view.text),))
        self._seen=set()
        self._lock=Lock()

    @property
    def snapshot(self): return self._snapshot

    @property
    def pending(self): return self._lock.locked()

    def submit(self, text, event_id, expected_revision=None):
        if not self._lock.acquire(blocking=False):
            return UISnapshot(View(('Processing the current turn. Please wait.',),'processing',revision=self._snapshot.view.revision),self._snapshot.transcript)
        try:
            # IDs retain no raw transcript; a stale old duplicate cannot restore
            # pre-reset private display history or replay a consequential action.
            if event_id in self._seen: return self._snapshot
            view=self.session.submit(text,event_id,expected_revision=expected_revision)
            if view.state=='stale': return UISnapshot(view,self._snapshot.transcript)
            self._seen.add(event_id)
            transcript=(('Assistant',view.text),) if text.strip().lower()=='reset' else self._snapshot.transcript+(('You',text),('Assistant',view.text))
            self._snapshot=UISnapshot(view,transcript)
            return self._snapshot
        finally:
            self._lock.release()

    def render_html(self):
        entries=''.join('<article class="turn"><strong>'+escape(role)+'</strong><pre>'+escape(text)+'</pre></article>' for role,text in self._snapshot.transcript)
        return '<section role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions text">'+entries+'</section>'

def configured_bridge():
    """No call occurs during setup; credentials stay in the HTTPS adapter only."""
    model=os.environ.get('SCHEDULING_MODEL')
    if not model or not os.environ.get('OPENAI_API_KEY'):
        raise ValueError('Set SCHEDULING_MODEL and OPENAI_API_KEY in the launch environment.')
    interpreter=OpenAIInterpreter(model=model)
    gateway=SchedulingAPI(base_url=os.environ.get('SCHEDULING_API_URL','http://127.0.0.1:4010'))
    return UIBridge(Session(gateway,interpreter,diagnostics=Diagnostics()))
