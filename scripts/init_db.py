from app.database import Base, engine, SessionLocal
from app.models import *  # noqa

def init():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


if __name__ == "__main__":
    init()
