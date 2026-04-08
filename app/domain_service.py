from sqlalchemy.orm import Session
from .models import Domain, User
from fastapi import HTTPException


def register_domain(db: Session, owner: User, name: str) -> Domain:
    name = name.strip().lower()
    if db.query(Domain).filter(Domain.name == name).first():
        raise HTTPException(status_code=400, detail="Domain already registered")
    d = Domain(name=name, owner_id=owner.id)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def list_domains(db: Session, owner: User) -> list[Domain]:
    return db.query(Domain).filter(Domain.owner_id == owner.id).order_by(Domain.created_at.desc()).all()


def get_domain_by_name(db: Session, name: str) -> Domain | None:
    return db.query(Domain).filter(Domain.name == name.strip().lower()).first()
