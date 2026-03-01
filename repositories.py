from sqlalchemy import select, insert, update, delete, func, cast, Date
from sqlalchemy.exc import IntegrityError
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

def db_check_isbn_exists(isbn):
    stmt = select(books.c.isbn).where(books.c.isbn == isbn)
    result = get_data(stmt)
    return len(result) > 0

def execute_change(stmt):
    try:
        with engine.begin() as conn:
            conn.execute(stmt)
    except IntegrityError as e:
        error_text = str(e).lower()

        if "unique" in error_text:
            if "email" in error_text:
                raise Exception("Цей Email вже закріплений за іншим співробітником")
            if "isbn" in error_text:
                raise Exception("Книга з таким ISBN вже є у вашому каталозі")
            return

        if "foreign key" in error_text:
            raise Exception("Не вдалося виконати дію: цей запис пов'язаний з іншими даними в системі")
        if "check" in error_text:
            raise Exception("Дані не пройшли перевірку: переконайтеся, що ціни та кількість є додатними")
        raise Exception(f"Не вдалося зберегти зміни. Будь ласка, перевірте правильність введених даних")

    except Exception:
        raise Exception("Тимчасовий збій у роботі бази даних. Спробуйте ще раз за хвилину")

# Видалення Soft delete
def db_soft_delete(table, column, value):
    stmt = update(table).where(column == value).values(is_deleted=True)
    execute_change(stmt)

# Відновлення співробітника/книги з архіву
# (повернення в штат/відновлення книги в разі помилкового видалення або появі в продажу)
def db_restore_entity(table, column, value):
    try:
        stmt = update(table).where(column == value).values(is_deleted=False)
        execute_change(stmt)
        return True
    except Exception as e:
        print(f"Виникла технічна помилка при спробі відновити запис у базі даних")
        print("Спробуйте ще раз або зверніться до адміністратора")
        return False

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
    try:
        sale_entries = [
            {
                "isbn": isbn,
                "employee_id": employee_id,
                "sale_date": datetime.now().date(),
                "actual_price": price
            }
            for _ in range(quantity)
        ]

        with engine.begin() as conn:
            conn.execute(sales.insert().values(sale_entries))


    except Exception as e:
        err = str(e).lower()
        if "foreign key" in err:
            raise Exception("Не вдалося оформити продаж: обрана книга або співробітник не існують в базі")
        elif "check" in err:
            raise Exception("Ціна продажу має бути більшою за 0")
        else:
            raise Exception(f"Не вдалося зареєструвати продаж через технічну помилку")

# Детальна інформація про продаж
def db_get_sale_details(sale_id):
    stmt = (
        select(
            sales.c.id,
            sales.c.sale_date,
            sales.c.actual_price,
            books.c.title.label('book_title'),
            books.c.cost_price,
            employees.c.full_name.label('employee_name')
        )
        .select_from(
            sales
            .join(books, sales.c.isbn == books.c.isbn)
            .join(employees, sales.c.employee_id == employees.c.id)
        )
        .where(sales.c.id == sale_id)
    )

    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()
        if result:
            data = dict(result)
            data['profit'] = data['actual_price'] - data['cost_price']
            return data
        return None

# CRUD КНИГИ

def db_add_book(book_info):
    try:
        with engine.begin() as conn:
            conn.execute(books.insert().values(book_info))
    except Exception as e:
        err = str(e).lower()
        if "unique" in err:
            raise Exception(f"ISBN {book_info['isbn']} вже існує")
        elif "check" in err:
            raise Exception("Перевірте дані: ціна, рік та кількість мають бути більше 0")
        else:
            raise Exception(f"Сталася технічна помилка при додаванні книги до бази")

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

# Детальна інформація про книгу
def db_get_book_details(isbn):
    with engine.connect() as conn:
        res = conn.execute(books.select().where(books.c.isbn == isbn)).mappings().first()
        return dict(res) if res else None

# CRUD СПІВРОБІТНИКИ

# Додавання співробітника
def db_add_employee(data):
    try:
        stmt = insert(employees).values(
            full_name=data['full_name'],
            position=data['position'],
            phone=data['phone'],
            email=data['email'],
            is_deleted=False
        )
        execute_change(stmt)

    except Exception as e:
        err = str(e).lower()

        if "unique" in err:
            raise Exception(f"Співробітник з email '{data['email']}' вже зареєстрований")
        else:
            raise Exception(f"Сталася технічна помилка при збереженні в базу даних")

# Редагування даних співробітника
# + Звіт №6
def db_get_employee_by_id(emp_id):
    with engine.connect() as conn:
        stmt = select(employees).where(employees.c.id == emp_id)
        res = conn.execute(stmt).mappings().first()
        return dict(res) if res else None

def db_get_employee_by_email(email):
    with engine.connect() as conn:
        stmt = select(employees).where(employees.c.email == email)
        res = conn.execute(stmt).mappings().first()
        return dict(res) if res else None

def db_update_employee(emp_id, data):
    try:
        stmt = update(employees).where(employees.c.id == emp_id).values(
            full_name=data['full_name'],
            position=data['position'],
            phone=data['phone'],
            email=data['email']
        )
        execute_change(stmt)
    except Exception as e:
        err = str(e).lower()
        if "unique" in err:
            raise Exception(f"Email '{data['email']}' вже використовується іншим співробітником")
        else:
            raise Exception(f"Не вдалося оновити дані. Сталася технічна помилка")

# Детальна інформація про співробітника
def db_get_employee_details(emp_id):
    with engine.connect() as conn:
        stmt = employees.select().where(employees.c.id == emp_id)
        res = conn.execute(stmt).mappings().first()
        return dict(res) if res else None

# БЛОК ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ
# 1. Оформити НОВИЙ ПРОДАЖ" - описано в CRUD Продажі
# 2. Керування історією продажів:
# Історія продажів - описано в CRUD Продажі
# Коригування ціни - описано в CRUD Продажі
# Видалення запису про продаж (повне) - описано в CRUD Продажі
# 3. Переглянути каталог книг (Звіт 1) описано в CRUD Книги

# БЛОК АНАЛІТИКА ТА ЗВІТНІСТЬ
# 1. Штат співробітників (Звіт 1)
# всі співробітники (звільнені та активні)
def db_get_all_employees():
    return get_data(select(employees))

def db_get_active_employees():
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

