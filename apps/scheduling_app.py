"""Local submitted-turn Marimo interface; rendering never performs scheduling."""
import marimo

__generated_with = '0.25.0'
app = marimo.App(width='medium', app_title='Ochsner Scheduling Assistant')

@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    import sys
    from uuid import uuid4
    root = Path(__file__).resolve().parents[1]
    if str(root / 'src') not in sys.path:
        sys.path.insert(0, str(root / 'src'))
    from scheduling_assistant.ui_bridge import configured_bridge
    return configured_bridge, mo, root, uuid4

@app.cell
def _(configured_bridge):
    try:
        bridge = configured_bridge()
        configuration_error = None
    except Exception:
        bridge = None
        configuration_error = 'Configure SCHEDULING_MODEL and OPENAI_API_KEY before launch, with a valid loopback SCHEDULING_API_URL (default http://127.0.0.1:4010). Restart this app after changing the environment. Credential values are never shown.'
    return bridge, configuration_error

@app.cell
def _(bridge, mo):
    # Submitted callbacks update state from this same controls cell. Rebuild
    # its form/buttons after the spinner clears, without replaying a callback.
    get_snapshot, set_snapshot = mo.state(bridge.snapshot if bridge is not None else None, allow_self_loops=True)
    return get_snapshot, set_snapshot

@app.cell
def _(mo, root):
    _theme = (root / 'assets/ui/themes/ochsner.css').read_text()
    _style = '''
    .scheduling-header {border-top:6px solid var(--brand-primary);padding:1.25rem 0;}
    .scheduling-header h1 {color:var(--brand-primary);font-size:1.7rem;}
    .turn {border-left:3px solid var(--brand-primary);padding:.6rem 1rem;margin:.8rem 0;background:var(--surface);color:var(--text);}
    .turn pre {font-family:var(--font-ui);white-space:pre-wrap;overflow-wrap:anywhere;margin:.4rem 0;}
    button:focus-visible, textarea:focus-visible, input:focus-visible {outline:3px solid var(--brand-primary);outline-offset:3px;}
    '''
    mo.vstack([
        mo.Html('<style>' + _theme + _style + '</style>'),
        mo.image(str(root / 'assets/ui/branding/ochsner-health.svg'), alt='Ochsner Health', width=222),
        mo.Html('<header class="scheduling-header"><h1>Scheduling assistant</h1><p>AI-assisted scheduling · Internal synthetic demonstration</p><p>Use synthetic patient information only. Your current message is sent to the model for interpretation. Identity matching here is not authentication. Conversation state is temporary; reset clears the displayed conversation.</p></header>'),
    ])
    return

@app.cell
def _(bridge, configuration_error, get_snapshot, mo, set_snapshot, uuid4):
    mo.stop(bridge is None, mo.callout(configuration_error or 'Configuration unavailable.', kind='warn'))
    _snapshot = get_snapshot()
    _revision = _snapshot.view.revision
    _event = uuid4().hex
    _reset_event = uuid4().hex
    _confirm_event = uuid4().hex

    def _dispatch(text, event):
        if not isinstance(text, str) or not text.strip():
            return
        with mo.status.spinner(title='Processing your turn…', subtitle='Please wait before submitting again.'):
            set_snapshot(bridge.submit(text, event, expected_revision=_revision))

    # Callbacks alone consume submitted values. Reading/rendering form.value
    # would make reruns into effects, so no downstream cell reads it.
    message_form = mo.ui.text_area(
        label='Your message', placeholder='Ask for providers, request booking, or answer the last question.',
        max_length=500, rows=3, full_width=True, disabled=bridge.pending,
    ).form(
        submit_button_label='Send message', clear_on_submit=True,
        submit_button_disabled=bridge.pending, loading=bridge.pending,
        validate=lambda value: None if isinstance(value, str) and value.strip() else 'Enter a message.',
        on_change=lambda value: _dispatch(value, _event),
    )
    reset_button = mo.ui.button(
        value=0, on_click=lambda count: count + 1,
        on_change=lambda _: _dispatch('reset', _reset_event),
        label='Reset conversation', disabled=bridge.pending,
        tooltip='Clear conversation. An unknown booking outcome remains unresolved.',
    )
    confirm_button = mo.ui.button(
        value=0, on_click=lambda count: count + 1,
        on_change=lambda _: _dispatch('yes', _confirm_event),
        label='Confirm displayed appointment', kind='success',
        disabled=bridge.pending or bridge.snapshot.view.proposal is None,
        tooltip='Book only the exact proposal displayed in this conversation.',
    )
    mo.vstack([
        message_form,
        mo.hstack([confirm_button, reset_button], justify='start'),
        mo.md('Send one turn at a time. Review the exact proposal before confirming. You can also type **no** to decline or **reset** to clear the conversation.'),
    ])
    return

@app.cell
def _(bridge, get_snapshot, mo):
    mo.stop(bridge is None)
    _snapshot = get_snapshot()
    mo.vstack([
        mo.Html('<p role="status" aria-live="polite">' + ('Processing…' if bridge.pending else 'Ready for your next turn.') + '</p>'),
        mo.callout('This control is stale. Use the current conversation controls.', kind='warn') if _snapshot.view.state == 'stale' else mo.Html(''),
        mo.Html(bridge.render_html()),
    ])
    return

if __name__ == '__main__':
    app.run()
