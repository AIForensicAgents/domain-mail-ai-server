from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
from .database import get_db
from .models import User
from .schemas import UserCreate, Token, UserOut
from .token_utils import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        validate_email(str(user.email))
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing = db.query(User).filter(User.email == str(user.email).lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user.password)
    u = User(email=str(user.email).lower(), hashed_password=hashed)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.post("/token", response_model=Token)
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(email).lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
