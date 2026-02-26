import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData

load_dotenv()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

DB_URI = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"

engine = create_engine(DB_URI, echo=False)
metadata = MetaData()