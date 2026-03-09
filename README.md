# Mabdel backend AI

Production-oriented FastAPI backend for Mabdel AI mobile app modules:
- Home dashboard widgets
- Unified Inbox (conversations/messages)
- Calls
- Voice command flow + command history
- Group placeholder
- Documents (invoices + pdf export + docusign stub)
- Integrations catalog/connect/disconnect
- Settings + automation rules
- AI Agent endpoints (summary/draft/decision/smartflow)
- Webhooks ingestion + queue worker + websocket events

## Tech stack
- Python 3.11+
- FastAPI (async)
- MongoDB + Motor
- Pydantic v2 + pydantic-settings
- JWT (access + refresh), bcrypt hashing
- Redis + arq workers
- WebSockets
- Docker + docker-compose

## Run locally
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Worker:
```bash
arq app.infrastructure.queue.worker.WorkerSettings
```

## LLM provider switch
The agent layer defaults to a local `stub` provider. You can switch it to Hugging Face Inference Providers without changing the API surface:

```bash
LLM_PROVIDER=huggingface
LLM_API_KEY=hf_xxxxxxxxx
LLM_MODEL=openai/gpt-oss-20b
LLM_API_BASE=https://router.huggingface.co/v1
```

Notes:
- `stub` remains the default for local development and tests.
- The Hugging Face client calls the OpenAI-compatible `/chat/completions` route and falls back to the local stub if the remote response is invalid.
- Free-tier models are suitable for development and prototyping, but expect tighter rate limits and less reliable structured output than paid models.

## Run with Docker
```bash
docker compose up --build
```

## Key API examples

### Auth flow
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup/send-code -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\"}"
curl -X POST http://localhost:8000/api/v1/auth/signup/verify-code -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\",\"code\":\"1234\"}"
curl -X POST http://localhost:8000/api/v1/auth/signup -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\",\"name\":\"User\",\"password\":\"StrongPass123!\",\"language\":\"en\",\"timezone\":\"UTC\",\"signup_validation_token\":\"TOKEN\"}"
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\",\"password\":\"StrongPass123!\"}"
```

### Integrations
```bash
curl -H "Authorization: Bearer ACCESS" http://localhost:8000/api/v1/integrations/catalog
curl -X POST -H "Authorization: Bearer ACCESS" http://localhost:8000/api/v1/integrations/whatsapp/connect
```

### Webhooks
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/whatsapp -H "Content-Type: application/json" -d "{\"user_id\":\"USER_ID\",\"messages\":[{\"account_id\":\"acc1\",\"thread_id\":\"th1\",\"from_id\":\"ct1\",\"from_name\":\"Client\",\"text\":\"hi\",\"message_id\":\"m1\"}]}"
```

### Conversations
```bash
curl -H "Authorization: Bearer ACCESS" "http://localhost:8000/api/v1/conversations?filter=all"
curl -X POST -H "Authorization: Bearer ACCESS" -H "Content-Type: application/json" http://localhost:8000/api/v1/conversations/CONV_ID/messages -d "{\"text\":\"Hello from Mabdel\"}"
```

### Commands
```bash
curl -X POST -H "Authorization: Bearer ACCESS" -H "Content-Type: application/json" http://localhost:8000/api/v1/commands/interpret -d "{\"text\":\"Cancel Invoice\",\"context\":{\"document_id\":\"DOC_ID\"}}"
curl -X POST -H "Authorization: Bearer ACCESS" -H "Content-Type: application/json" http://localhost:8000/api/v1/commands/execute -d "{\"execute_token\":\"TOKEN\"}"
```

## Worker jobs
- `process_inbound`: raw event -> adapter parse -> contact/conversation/message upserts -> activity -> websocket
- `send_message`: outbound queued message -> adapter send -> status/activity/audit -> websocket
- `agent_decide`: inbound message -> guarded auto-reply decision

## Notes
- External platform APIs are adapter stubs but contracts are production-ready.
- OAuth tokens are encrypted at rest with Fernet key from env.
- Multi-tenancy enforced by `user_id` filters in service layer.
