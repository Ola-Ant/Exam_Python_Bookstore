from sqlalchemy import Table
from db import engine, metadata

books = Table("books", metadata, autoload_with=engine)
employees = Table("employees", metadata, autoload_with=engine)
sales = Table("sales", metadata, autoload_with=engine)