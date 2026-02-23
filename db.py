from sqlalchemy import create_engine, MetaData
DB_URI = "postgresql+psycopg://postgres:Hardy220223@localhost:5432/photobook_store"
engine = create_engine(DB_URI, echo=False)

metadata = MetaData()
