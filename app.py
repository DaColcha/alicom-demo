import os

from fastapi import FastAPI, Request, Response

from bedrock_client import ask_accountant_bot
import whatsapp_client

app = FastAPI()

WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', '')

@app.get('/webhook/whatsapp')
def verify_webhook(request: Request):
    """Handshake endpoint Meta's Cloud API (WABA) calls once when
    the webhook URL is registered."""
    mode = request.query_params.get('hub.mode')
    token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')

    if mode == 'subscribe' and token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type='text/plain')
    return Response(status_code=403)


@app.post('/webhook/whatsapp')
async def receive_message(request: Request):
    payload = await request.json()
    incoming = whatsapp_client.extract_incoming_message(payload)
    if incoming is None:
        return {'status': 'ignored'}

    sender_id, message_text = incoming
    answer = ask_accountant_bot(message_text)
    whatsapp_client.send_message(sender_id, answer)
    return {'status': 'ok'}
