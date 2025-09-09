from sqlmodel import SQLModel, create_engine, Session
import pathlib

DB_PATH = "./data/meeting_helper.db"
pathlib.Path("./data").mkdir(exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
