from fastapi import APIRouter
from ..auth import router as _router

router = APIRouter()

# Re-export routes from app.auth under /auth
router.include_router(_router)
