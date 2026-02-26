from sqlalchemy import select, insert, update, delete, func, cast, Date
from db import engine
from models import books, employees, sales
from datetime import datetime

def get_data(stmt):
    with engine.connect() as conn:
        return conn.execute(stmt).mappings().all()

def db_get_book_by_isbn(isbn):
    stmt = select(books).where(books.c.isbn == isbn)
    result = get_data(stmt)
    return result[0] if result else None

def execute_change(stmt):
    with engine.begin() as conn:
        conn.execute(stmt)

# Видалення Soft delete
def db_soft_delete(table, column, value):
    stmt = update(table).where(column == value).values(is_deleted=True)
    execute_change(stmt)

# CRUD ПРОДАЖІ

# CRUD продажі- меню №1 (історія продажів), Звіт 3
def db_get_all_sales_history():
    stmt = select(
        sales.c.id, sales.c.sale_date, books.c.title,
        sales.c.actual_price, books.c.cost_price, employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).order_by(sales.c.sale_date.desc())
    return get_data(stmt)

# CRUD продажі (зміна ціни) - меню №2
def db_get_sale_by_id(sale_id):
    stmt = (
        select(
            sales.c.id,
            sales.c.isbn,
            sales.c.actual_price,
            sales.c.sale_date,
            books.c.title.label('book_title'),
            employees.c.full_name.label('employee_name')
        )
        .select_from(
            sales
            .join(books, sales.c.isbn == books.c.isbn)
            .join(employees, sales.c.employee_id == employees.c.id)
        )
        .where(sales.c.id == sale_id)
    )
    result = get_data(stmt)
    return result[0] if result else None

def db_update_sale_price(sale_id, new_price):
    execute_change(update(sales).where(sales.c.id == sale_id).values(actual_price=new_price))

# CRUD продажі (повне видалення продажу) -  меню №3
def db_delete_sale(sale_id):
    execute_change(delete(sales).where(sales.c.id == sale_id))

# CRUD продажі (реєстрація продажу)
def db_add_sale(isbn, employee_id, price, quantity):
    sale_entries = [
        {
            "isbn": isbn,
            "employee_id": employee_id,
            "sale_date": datetime.now().date(),
            "actual_price": price
        }
        for _ in range(quantity)
    ]

    stmt = insert(sales).values(sale_entries)
    execute_change(stmt)

# CRUD КНИГИ

# Додавання книги
def db_add_book(data):
    stmt = insert(books).values(
        isbn=data['isbn'],
        title=data['title'],
        author=data['author'],
        genre=data['genre'],
        year_pub=data['year_pub'],
        cost_price=data['cost_price'],
        retail_price=data['retail_price']
    )
    execute_change(stmt)

# Каталог книг Звіт №2
def db_get_books():
    return get_data(select(books).where(books.c.is_deleted == False))

# Редагувати дані книги
def db_update_book(isbn, updated_data):
    stmt = update(books).where(books.c.isbn == isbn).values(
        title=updated_data['title'],
        author=updated_data['author'],
        genre=updated_data['genre'],
        year_pub=updated_data['year_pub'],
        cost_price=updated_data['cost_price'],
        retail_price=updated_data['retail_price']
    )
    execute_change(stmt)


# CRUD СПІВРОБІТНИКИ

# Додавання співробітника
def db_add_employee(data):
    stmt = insert(employees).values(
        full_name=data['full_name'],
        position=data['position'],
        phone=data['phone'],
        email=data['email'],
        is_deleted=False
    )
    execute_change(stmt)

# Редагування даних співробітника
# + Звіт №6
def db_get_employee_by_id(emp_id):
    with engine.connect() as conn:
        stmt = select(employees).where(
            (employees.c.id == emp_id) & (employees.c.is_deleted == False)
        )
        return conn.execute(stmt).mappings().first()

def db_update_employee(emp_id, data):
    stmt = update(employees).where(employees.c.id == emp_id).values(
        full_name=data['full_name'],
        position=data['position'],
        phone=data['phone'],
        email=data['email']
    )
    execute_change(stmt)


# БЛОК ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ
# 1. Оформити НОВИЙ ПРОДАЖ" - описано в CRUD Продажі
# 2. Керування історією продажів:
# Історія продажів - описано в CRUD Продажі
# Коригування ціни - описано в CRUD Продажі
# Видалення запису про продаж (повне) - описано в CRUD Продажі
# 3. Переглянути каталог книг (Звіт 1) описано в CRUD Книги

# БЛОК АНАЛІТИКА ТА ЗВІТНІСТЬ
# 1. Штат співробітників (Звіт 1)
def db_get_all_employees():
    return get_data(select(employees).where(employees.c.is_deleted == False))

# 2. Каталог книг (Звіт 2) - описано в CRUD Книги

# 3. Історія продажів (Звіт 3) - описано в CRUD Продажі

# 4. Продажі за дату (Звіт 4)
def db_get_sales_by_date(target_date):
    stmt = select(
        sales.c.id,
        sales.c.sale_date,
        books.c.title,
        sales.c.actual_price,
        employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(cast(sales.c.sale_date, Date) == cast(target_date, Date))
    return get_data(stmt)

# 5. Продажі за період (Звіт 5)
def db_get_sales_by_period(start_date, end_date):
    stmt = select(
        sales.c.id,
        sales.c.sale_date,
        books.c.title,
        employees.c.full_name,
        sales.c.actual_price
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(
        cast(sales.c.sale_date, Date).between(cast(start_date, Date), cast(end_date, Date))
    ).order_by(sales.c.sale_date)
    return get_data(stmt)

# 6. Звіт по співробітнику (Звіт №6)
def db_get_sales_by_employee(emp_id):
    stmt = select(
        sales.c.id,
        sales.c.sale_date,
        books.c.title,
        sales.c.actual_price,
        books.c.cost_price,
        employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(employees.c.id == emp_id).order_by(sales.c.sale_date.desc())
    return get_data(stmt)

# Топ книга періоду (Звіт №7)
def db_get_most_sold_book(start_date, end_date):
    stmt = select(
        books.c.title,
        func.count(sales.c.id).label('sales_count'),
        func.sum(sales.c.actual_price).label('total_revenue')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        cast(sales.c.sale_date, Date).between(cast(start_date, Date), cast(end_date, Date))
    ).group_by(books.c.title) \
        .order_by(func.count(sales.c.id).desc()) \
        .limit(1)
    return get_data(stmt)

# Найкращий продавець (Звіт №8)
def db_get_best_seller_employee(start_date, end_date):
    stmt = select(
        employees.c.full_name,
        func.count(sales.c.id).label('sales_count'),
        func.sum(sales.c.actual_price).label('total_revenue')
    ).select_from(
        sales.join(employees, sales.c.employee_id == employees.c.id)
    ).where(
        sales.c.sale_date.between(
            cast(start_date, Date),
            cast(end_date, Date)
        )
    ).group_by(employees.c.full_name) \
        .order_by(func.count(sales.c.id).desc()) \
        .limit(1)
    return get_data(stmt)

# Прибуток за період (Звіт №9)
def db_get_profit_report(start_date, end_date):
    stmt = select(
        func.coalesce(func.sum(sales.c.actual_price), 0).label('total_revenue'),
        func.coalesce(func.sum(books.c.cost_price), 0).label('total_cost'),
        func.coalesce(func.sum(sales.c.actual_price - books.c.cost_price), 0).label('net_profit')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        cast(sales.c.sale_date, Date).between(cast(start_date, Date), cast(end_date, Date))
    )
    return get_data(stmt)

# Топ автор (Звіт №10)
def db_get_most_sold_author(start_date, end_date):
    stmt = select(
        books.c.author,
        func.count(sales.c.id).label('total_sold')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        cast(sales.c.sale_date, Date).between(cast(start_date, Date), cast(end_date, Date))
    ).group_by(books.c.author) \
        .order_by(func.count(sales.c.id).desc()) \
        .limit(1)
    return get_data(stmt)

# Топ жанр (Звіт №11)
def db_get_most_sold_genre(start_date, end_date):
    stmt = select(
        books.c.genre,
        func.count(sales.c.id).label('total_sold')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        cast(sales.c.sale_date, Date).between(cast(start_date, Date), cast(end_date, Date))
    ).group_by(books.c.genre) \
        .order_by(func.count(sales.c.id).desc()) \
        .limit(1)
    return get_data(stmt)

