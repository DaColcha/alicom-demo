# Alicon Demo — WhatsApp Accounting Assistant

A WhatsApp chatbot that answers accounting questions (e.g. RUC registration, filing deadlines) in Spanish, backed by an AWS Bedrock knowledge base. 

## Flow

```
WhatsApp user
     │  sends a message
     ▼
WhatsApp provider (TBD)
     │  POSTs the incoming message to your webhook
     ▼
POST /webhook/whatsapp          (app.py)
     │
     ├─ whatsapp_client.extract_incoming_message(payload)   → (sender_id, message_text)
     │
     ├─ bedrock_client.ask_accountant_bot(message_text)
     │       └─ Bedrock Agent Runtime: RetrieveAndGenerate
     │             ├─ retrieves relevant chunks from the Knowledge Base
     │             └─ generates an answer with Amazon Nova 2 Lite,
     │                constrained by a custom prompt template
     │
     └─ whatsapp_client.send_message(sender_id, answer)      → reply sent back to the user
```

`GET /webhook/whatsapp` is a separate, one-time handshake some providers (Meta Cloud API) call when you first register the webhook URL — it echoes back `hub.challenge` if `hub.verify_token` matches `WHATSAPP_VERIFY_TOKEN`.

## Files

| File | Responsibility |
|---|---|
| `app.py` | FastAPI app. Owns the two HTTP routes and wires `whatsapp_client` ↔ `bedrock_client` together. Provider-agnostic. |
| `bedrock_client.py` | `ask_accountant_bot(question) -> str`. Calls Bedrock's `retrieve_and_generate` against the knowledge base, with a prompt template that forces Spanish, an accountant tone, and answers grounded only in retrieved search results. |
| `whatsapp_client.py` | `extract_incoming_message(payload)` and `send_message(to, text)` — both currently `raise NotImplementedError`. This is the *only* file that should change when a WhatsApp provider is picked. |
| `requirements.txt` | `boto3`, `fastapi`, `uvicorn`. |

## Why it's structured this way

- **`whatsapp_client.py` is isolated from `app.py` and `bedrock_client.py`** so that choosing a provider later (Meta Cloud API vs. Twilio vs. 360dialog) only means implementing two functions with a fixed signature — the webhook routing and the Bedrock call don't need to know or care which provider is behind them.
- **`ask_accountant_bot` is a plain function, not a script**, so it can be called once per incoming HTTP request instead of running once at import time.
- **The prompt template is data, not model behavior** — Bedrock's `generationConfiguration.promptTemplate` lets us pin down language (Spanish) and persona (accountant) without fine-tuning or post-processing, using Bedrock's own `$search_results$` / `$output_format_instructions$` placeholders so retrieval grounding still works.
- **Amazon Nova 2 Lite is invoked via an inference profile ARN**, not the plain foundation-model ARN — Bedrock rejects on-demand invocation of this model without one.

## Running locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

export WHATSAPP_VERIFY_TOKEN=some-secret-you-pick
.venv/bin/uvicorn app:app --reload
```

Requires AWS credentials configured (`aws configure`) with Bedrock access in `us-east-1`.

## Running with Docker

The `Dockerfile` intentionally never bakes AWS credentials into the image — long-lived keys inside an image layer are a leak waiting to happen and can't be rotated without rebuilding. Instead, boto3's default credential chain resolves credentials at container *runtime*:

```bash
docker build -t alicon-demo .

docker run -d --name alicon-demo -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=<your_access_key_id> \
  -e AWS_SECRET_ACCESS_KEY=<your_secret_access_key> \
  -e WHATSAPP_VERIFY_TOKEN=devtoken \
  alicon-demo
```

Values come from `~/.aws/credentials` (the file `aws configure` wrote earlier).

Alternative if you'd rather not pass keys on the command line (they'd land in shell history): mount your AWS config read-only instead —

```bash
docker run -d --name alicon-demo -p 8000:8000 \
  -v ~/.aws:/root/.aws:ro \
  -e WHATSAPP_VERIFY_TOKEN=devtoken \
  alicon-demo
```

Test with the requests in `requests.http`, e.g. `curl "http://127.0.0.1:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=devtoken&hub.challenge=12345"` should echo back `12345`. Clean up with `docker stop alicon-demo && docker rm alicon-demo`.

**In an actual deployment, skip access keys entirely** and attach an IAM role instead — an ECS/Fargate task role, an EC2 instance profile, or IRSA on EKS. boto3 picks it up automatically with zero container config, and there's no long-lived credential to leak or rotate. One gotcha on bare EC2: IMDSv2's default hop limit of 1 blocks the metadata service from inside a container; raise it with `aws ec2 modify-instance-metadata-options --http-put-response-hop-limit 2`.

## What's left

- Pick a WhatsApp provider and implement `extract_incoming_message` / `send_message` in `whatsapp_client.py` accordingly.
- If the chosen provider doesn't use Meta's `hub.challenge` verification scheme, adjust or remove `GET /webhook/whatsapp` in `app.py`.
