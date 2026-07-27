# Technical Documentation

> For a plain-language overview of what this project is, see [README.md](README.md).

This document covers architecture, setup, and deployment for the WhatsApp accounting assistant.

## Flow

```
WhatsApp user
     │  sends a message
     ▼
WhatsApp Business API (Meta Cloud API / WABA)
     │  POSTs the incoming message to your webhook
     ▼
POST /webhook/whatsapp          (app.py)
     │
     ├─ whatsapp_client.extract_incoming_message(payload)   → (sender_id, message_text)
     │
     ├─ bedrock_client.ask_accountant_bot(message_text)
     │       └─ Bedrock Agent Runtime: RetrieveAndGenerate
     └─ whatsapp_client.send_message(sender_id, answer)      → reply sent back to the user
```

`GET /webhook/whatsapp` is a separate, one-time handshake some providers (Meta Cloud API) call when you first register the webhook URL — it echoes back `hub.challenge` if `hub.verify_token` matches `WHATSAPP_VERIFY_TOKEN`.

## Files

| File | Responsibility |
|---|---|
| `app.py` | FastAPI app. Owns the two HTTP routes and wires `whatsapp_client` ↔ `bedrock_client` together. Provider-agnostic. |
| `bedrock_client.py` | `ask_accountant_bot(question) -> str`. Calls Bedrock's `retrieve_and_generate` against the knowledge base, with a prompt template that forces Spanish, an accountant tone, and answers grounded only in retrieved search results. |
| `whatsapp_client.py` | `extract_incoming_message(payload)` and `send_message(to, text)`, implemented against Meta's WhatsApp Business API (Cloud API / WABA). This is the *only* file that talks to the Graph API directly. |
| `requirements.txt` | `boto3`, `fastapi`, `requests`, `uvicorn`. |


## Running locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

export WHATSAPP_VERIFY_TOKEN=some-secret-you-pick
export WHATSAPP_ACCESS_TOKEN=<your-cloud-api-access-token>
export WHATSAPP_PHONE_NUMBER_ID=<your-phone-number-id>
.venv/bin/uvicorn app:app --reload
```

Requires AWS credentials configured (`aws configure`) with Bedrock access in `us-east-1`.

`WHATSAPP_ACCESS_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` come from the Meta App Dashboard for the WhatsApp Business app (System User token + the phone number's ID under WhatsApp > API Setup). `WHATSAPP_API_VERSION` defaults to `v25.0` and can be overridden if Meta deprecates it.

## Running with Docker

The `Dockerfile` intentionally never bakes AWS credentials into the image — long-lived keys inside an image layer are a leak waiting to happen and can't be rotated without rebuilding. Instead, boto3's default credential chain resolves credentials at container *runtime*:

```bash
docker build -t alicon-demo .

docker run -d --name alicon-demo -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=<your_access_key_id> \
  -e AWS_SECRET_ACCESS_KEY=<your_secret_access_key> \
  -e WHATSAPP_VERIFY_TOKEN=devtoken \
  -e WHATSAPP_ACCESS_TOKEN=<your_cloud_api_access_token> \
  -e WHATSAPP_PHONE_NUMBER_ID=<your_phone_number_id> \
  alicon-demo
```

Test with the requests in `requests.http`, e.g. `curl "http://127.0.0.1:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=devtoken&hub.challenge=12345"` should echo back `12345`. Clean up with `docker stop alicon-demo && docker rm alicon-demo`.
