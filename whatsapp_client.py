"""
Provider-agnostic WhatsApp sending/parsing layer.

No WhatsApp API has been chosen yet (candidates: Meta Cloud API, Twilio,
360dialog, etc.). Fill these two functions in once a provider is picked —
the webhook in app.py only depends on this interface, not on any provider
specifics.
"""


def extract_incoming_message(payload: dict) -> tuple[str, str]:
    """Given the raw webhook payload, return (sender_id, message_text)."""
    raise NotImplementedError('Pick a WhatsApp provider and parse its payload shape here.')


def send_message(to: str, text: str) -> None:
    """Send `text` to `to` via the chosen WhatsApp provider."""
    raise NotImplementedError('Pick a WhatsApp provider and implement sending here.')
