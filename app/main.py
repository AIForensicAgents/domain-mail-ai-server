from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.health import router as health_router
from .routes.auth import router as auth_router
from .routes.domains import router as domains_router
from .routes.inbound import router as inbound_router
from .routes.outbound import router as outbound_router
from .config import settings

# Create FastAPI app
app = FastAPI(
    title="MailGPT Server",
    description="Domain registration, inbound email processing with dynamic mailboxes, and AI-powered replies using OpenAI.",
    version="0.1.0",
)

# CORS (adjust as needed for your environment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*" if settings.APP_ENV != "production" else settings.APP_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, prefix="/health", tags=["health"])  # GET /health
app.include_router(auth_router, prefix="/auth", tags=["auth"])       # /auth/register, /auth/token
app.include_router(domains_router, prefix="/domains", tags=["domains"])  # /domains endpoints
app.include_router(inbound_router, prefix="/inbound", tags=["inbound"])  # /inbound/email
app.include_router(outbound_router, prefix="/outbound", tags=["outbound"])  # /outbound/send


@app.get("/")
def root():
    return {"name": "MailGPT Server", "status": "ok"}
