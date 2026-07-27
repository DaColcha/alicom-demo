import os
from typing import Any, Optional

import requests

WHATSAPP_API_VERSION = os.environ.get('WHATSAPP_API_VERSION', 'v21.0')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')

GRAPH_API_URL = f'https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages'


def extract_incoming_message(payload: dict) -> Optional[tuple[Any, Any]]:
    print('Checking incoming message' , payload)
    value = payload['entry'][0]['changes'][0]['value']
    message = value['messages'][0]

    if message.get('type') != 'text':
        return None

    return message['from'], message['text']['body']


def send_message(to: str, text: str) -> None:
    print('Sending response to ' , to)
    response = requests.post(
        GRAPH_API_URL,
        headers={'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}'},
        json={
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'body': text},
        },
        timeout=10,
    )
    response.raise_for_status()
