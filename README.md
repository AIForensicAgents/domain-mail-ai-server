<!-- Open Graph / Twitter Cards -->
<meta property="og:title" content="MailGPT Server" />
<meta property="og:description" content="Python FastAPI service for domain registration, inbound email processing with dynamic mailboxes, and AI-powered replies using OpenAI gpt-5.4." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://example.com/" />
<meta property="og:image" content="https://example.com/og.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="MailGPT Server" />
<meta name="twitter:description" content="Python FastAPI service for domain registration, inbound email processing with dynamic mailboxes, and AI-powered replies using OpenAI gpt-5.4." />
<meta name="twitter:image" content="https://example.com/og.png" />

# MailGPT Server

A production-style Python repository that provides:

- API to register domains
- Email server implementation surface for each registered domain (inbound webhook + outbound SMTP)
- Dynamic mailbox creation when the first incoming message arrives to a recipient
- AI-powered auto-replies to incoming messages using OpenAI gpt-5.4
- Email thread history passed as context clipped to the most recent 10k tokens
- Full Python stack with FastAPI, SQLAlchemy, and SQLite by default
- Inbound webhook/API processing design
- Outbound email sending flow
- Lightweight but realistic FastAPI implementation
- SQLAlchemy models and schemas
- Clean project structure
- Implement user auth
- No Docker required

## Features Overview

- Register and manage domains via authenticated endpoints
- Receive inbound email via a secure webhook and automatically create mailboxes for new recipients under a registered domain
- Persist domains, mailboxes, threads, and messages in SQLite by default
- Build AI replies with OpenAI gpt-5.4 using up to 10k tokens of recent thread context
- Send outbound emails via SMTP, with optional delegated operations

## Project Structure

- app/
  - main.py: FastAPI application startup and router registration
  - config.py: Centralized configuration and environment variable load
  - database.py: SQLAlchemy engine/session setup
  - models.py: SQLAlchemy ORM models
  - schemas.py: Pydantic models (request/response)
  - auth.py: Authentication routes and dependencies
  - token_utils.py: Password hashing and JWT utilities
  - domain_service.py: Domain CRUD operations
  - mail_service.py: Inbound processing, mailbox/thread/message handling, outbound SMTP
  - ai_service.py: OpenAI integration with context clipping
  - history_service.py: Thread history construction and token clipping helpers
  - routes/: Route modules (domains, inbound, outbound, health, auth)
- scripts/
  - init_db.py: Database initialization script

## Configuration

Set the following environment variables. See .env.example for a template.

Required for basic operation:
- APP_ENV: Environment name (e.g., development, production)
- SECRET_KEY: Secret key used for signing JWTs
- DATABASE_URL: SQLAlchemy URL (default: sqlite:///./data/app.db)
- OPENAI_API_KEY: API key for OpenAI
- OPENAI_MODEL: OpenAI model (default: gpt-5.4)
- INBOUND_API_TOKEN: Secret token to authenticate inbound webhook calls
- SMTP_HOST: SMTP server hostname
- SMTP_PORT: SMTP server port
- SMTP_USERNAME: SMTP username
- SMTP_PASSWORD: SMTP password

Optional and advanced:
- ORG_ID: OpenAI organization ID
- SYSTEM_PROMPT: System prompt text for the AI assistant
- MAX_TOKENS_WINDOW: Max tokens for context clipping (default: 10000)
- MAX_COMPLETION_TOKENS: Max tokens for the AI completion (default: 512)
- SMTP_USE_TLS: Use TLS (starttls) for SMTP (default: true)
- SMTP_USE_SSL: Use SSL for SMTP (default: false)
- FROM_FALLBACK_EMAIL: Fallback From email to use if needed
- APP_BASE_URL: Base URL for links in emails or callbacks
- ACCESS_TOKEN_EXPIRE_MINUTES: JWT access token validity window (default: 60)
- DELEGATED_EMAIL: Required for deployments that need delegated operations (e.g., when sending on behalf of a domain or shared mailbox). If provided, outbound messages will use this as the actual From, and the mailbox address will be set as Reply-To.

Note: Keep secrets safe and never commit your .env to version control.

## Setup Instructions

1) Prerequisites
- Python 3.10+
- An SMTP provider with credentials
- An OpenAI account and API key

2) Create and activate a virtual environment
- macOS/Linux:
  - python3 -m venv .venv
  - source .venv/bin/activate
- Windows (PowerShell):
  - python -m venv .venv
  - .venv\\Scripts\\Activate.ps1

3) Install dependencies
- pip install -r requirements.txt

4) Create and configure environment
- cp .env.example .env
- Edit .env with your values

5) Initialize the database
- python scripts/init_db.py

6) Run the server
- uvicorn app.main:app --reload

7) Test health check
- curl http://127.0.0.1:8000/health

## Inbound Email Webhook Design

Endpoint: POST /inbound/email

Authentication:
- Provide header X-Webhook-Token with value equal to INBOUND_API_TOKEN.

Payload (JSON example):
- {
  "domain": "example.com",
  "recipient": "support@example.com",
  "sender": "user@external.com",
  "subject": "Question about pricing",
  "text": "Hello...",
  "html": "<p>Hello...</p>",
  "message_id": "<abc@example.com>",
  "in_reply_to": "<prev@example.com>",
  "references": ["<prev@example.com>"]
}

Behavior:
- Validate domain is registered
- Dynamically provision recipient mailbox if missing
- Resolve or create a thread
- Persist inbound message
- Build thread history and call OpenAI gpt-5.4 for an auto-reply
- Send outbound reply using SMTP
- Persist outbound message

## Outbound Email Sending Flow

Endpoint: POST /outbound/send (authenticated)
- Allows sending a message from a specific mailbox to an external recipient
- Persists message and, if no existing thread, creates one
- If DELEGATED_EMAIL is set, uses that address as From and sets Reply-To to mailbox address

## API: Domain Registration

Endpoints (authenticated):
- POST /domains: Register a new domain
- GET /domains: List your domains

## Data Storage

- domains: Registered domains owned by users
- mailboxes: Recipient addresses under a domain, created on first inbound
- threads: Conversation containers for a mailbox and counterparties
- messages: Individual inbound/outbound messages with metadata

## Auth

- Implement user auth

## Notes

- This repo provides a realistic but compact reference implementation. You will still need a production-grade MTA/Mail Gateway (e.g., SES, Postmark, Mailgun, or your own SMTP relay) to call the inbound webhook, and valid SMTP credentials for outbound. Ensure INBOUND_API_TOKEN remains secret between your gateway and this service.

## Development Tips

- Logs are printed to stdout; integrate with your preferred logging stack in production.
- For SQLite, the default path is ./data/app.db. Ensure the data directory exists and is writable by the process.

## License

MIT
