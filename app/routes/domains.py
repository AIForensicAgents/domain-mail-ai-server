from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import DomainCreate, DomainOut
from ..domain_service import register_domain, list_domains
from ..token_utils import get_current_user
from ..models import User

router = APIRouter()


@router.post("/", response_model=DomainOut)
def create_domain(payload: DomainCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = register_domain(db, current_user, payload.name)
    return d


@router.get("/", response_model=list[DomainOut])
def get_domains(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_domains(db, current_user)
