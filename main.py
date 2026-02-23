import csv
import os
import re
from sqlalchemy import select, insert, update, func
from datetime import datetime
from db import engine
from models import books, employees, sales


# ЕКСПОРТ

def export_to_csv(data, filename):
    filepath = os.path.join('export', filename)

    if not data:
        print("Відсутні дані для експорту!")
        return

    fieldnames = data[0].keys()

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"\nЗвіт збережено у файл: {filepath}")


# ЗВІТИ ТА АНАЛІТИКА (11 звітів)

"""Звіт №1 Повна інформація про співробітників"""
def show_all_employees():
    print(f"\n{'=' * 45}\nСПИСОК СПІВРОБІТНИКІВ МАГАЗИНУ\n{'=' * 45}")
    print(f"\n{'ID':<5} | {'ПІБ':<30} | {'ПОСАДА':<25} | {'ТЕЛЕФОН':<15} | {'EMAIL':<25}")
    print("-" * 110)
    stmt = select(employees).where(employees.c.is_deleted == False)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        if not rows:
            print("Співробітників не знайдено.")
        else:
            for row in rows:
                print(f"{row['id']:<5} | "
                      f"{row['full_name'][:30]:<30} | "
                      f"{row['position'][:25]:<25} | "
                      f"{row['phone']:<15} | "
                      f"{row['email']:<25}")
            print("-" * 110)
            save_choice = input("\nЗберегти список співробітників у файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                export_to_csv(rows, "employees_list.csv")

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №2 Повна інформація про книги"""
def show_all_books():
    print(f"\n{'=' * 45}\n КАТАЛОГ КНИГ\n{'=' * 45}")
    print(f"\n{'ISBN':<18} | {'НАЗВА':<30} | {'РІК':<6} | {'АВТОР':<20} | {'ЖАНР':<15} | {'СОБІВАРТ.':<10} | {'ЦІНА':<10}")
    print("-" * 125)
    stmt = select(books).where(books.c.is_deleted == False).order_by(books.c.title)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        if not rows:
            print("У базі даних немає доступних книг.")
        else:
            for row in rows:
                print(f"{str(row['isbn']):<18} | "
                      f"{row['title'][:30]:<30} | "
                      f"{row['year_pub']:<6} | "
                      f"{row['author'][:20]:<20} | "
                      f"{row['genre'][:15]:<15} | "
                      f"{float(row['cost_price']):>10.2f} | "
                      f"{float(row['retail_price']):>10.2f}")
            print("-" * 125)
            save_choice = input("\nЗберегти каталог книг у файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                export_to_csv(rows, "all_books_catalog.csv")

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №3 Повна інформація про продажі"""
def show_all_sales():
    print(f"\n{'=' * 45}\nІСТОРІЯ ПРОДАЖІВ\n{'=' * 45}")
    print(f"\n{'ДАТА':<12} | {'КНИГА':<30} | {'ЦІНА':<10} | {'ПРИБУТОК':<10} | {'ПРОДАВЕЦЬ':<25}")
    print("-" * 105)
    stmt = select(
        sales.c.sale_date,
        books.c.title,
        sales.c.actual_price,
        books.c.cost_price,
        employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).order_by(sales.c.sale_date.desc())

    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        if not rows:
            print("У базі даних немає зареєстрованих продажів")
        else:
            total_sum = 0
            total_profit = 0

            for row in rows:
                profit = float(row['actual_price']) - float(row['cost_price'])
                total_sum += float(row['actual_price'])
                total_profit += profit

                print(f"{str(row['sale_date']):<12} | "
                      f"{row['title'][:30]:<30} | "
                      f"{float(row['actual_price']):>10.2f} | "
                      f"{profit:>10.2f} | "
                      f"{row['full_name'][:25]:<25}")

            print("-" * 105)
            print(f"ЗАГАЛЬНИЙ ОБОРОТ: {total_sum:.2f} грн")
            print(f"ЗАГАЛЬНИЙ ПРИБУТОК: {total_profit:.2f} грн")

            save_choice = input("\nЗберегти історію продажів у файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                export_to_csv(rows, "sales_history_report.csv")

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №4 Продажі за дату"""
def show_sales_by_date():
    print(f"\nЗвіт про РЕЗУЛЬТАТИ ПРОДАЖІВ за дату")
    date_str = input("\nВведіть дату (YYYY-MM-DD): ").strip()

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print("Помилка: Неправильний формат дати. Спробуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    stmt = select(
        sales.c.sale_date,
        books.c.title,
        sales.c.actual_price,
        books.c.cost_price,
        employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(sales.c.sale_date == target_date)

    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        if not rows:
            print(f"За дату {date_str} продажів не знайдено.")
        else:
            print(f"\nРЕЗУЛЬТАТИ ПРОДАЖІВ за {date_str}:")
            print(f"\n{'ДАТА':<12} | {'КНИГА':<30} | {'ЦІНА':<10} | {'ПРИБУТОК':<10} | {'ПРОДАВЕЦЬ':<25}")
            print("-" * 105)

            total_day_profit = 0
            for row in rows:
                profit = float(row['actual_price']) - float(row['cost_price'])  #
                total_day_profit += profit

                print(f"{str(row['sale_date']):<12} | "
                      f"{row['title'][:30]:<30} | "
                      f"{float(row['actual_price']):>10.2f} | "
                      f"{profit:>10.2f} | "
                      f"{row['full_name'][:25]:<25}")

            print("-" * 105)
            print(f"ЗАГАЛЬНИЙ ПРИБУТОК ЗА ДЕНЬ: {total_day_profit:.2f} грн")

            save_choice = input(f"\nЗберегти звіт за {target_date} у файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                f_name = f"sales_{target_date}.csv"
                export_to_csv(rows, f_name)

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №5 Продажі за період"""
def show_sales_by_period():
    print(f"\nЗвіт про РЕЗУЛЬТАТИ ПРОДАЖІВ за період")
    start_str = input("\nВведіть дату початку (YYYY-MM-DD): ").strip()
    end_str = input("Введіть дату кінця (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("Помилка: Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    stmt = select(
        sales.c.sale_date,
        books.c.title,
        sales.c.actual_price,
        books.c.cost_price,
        employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)  #
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(
        sales.c.sale_date.between(start_date, end_date)
    ).order_by(sales.c.sale_date)

    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

        if not rows:
            print(f"За період з {start_date} по {end_date} продажів не знайдено.")
        else:
            print(f"\nПРОДАЖІ ЗА ПЕРІОД з {start_date} по {end_date}:")
            print(f"\n{'ДАТА':<12} | {'КНИГА':<30} | {'ЦІНА':<10} | {'ПРИБУТОК':<10} | {'ПРОДАВЕЦЬ':<25}")
            print("-" * 105)

            total_sum = 0
            total_profit = 0

            for row in rows:
                profit = float(row['actual_price']) - float(row['cost_price'])
                total_sum += float(row['actual_price'])
                total_profit += profit

                print(f"{str(row['sale_date']):<12} | "
                      f"{row['title'][:30]:<30} | "
                      f"{float(row['actual_price']):>10.2f} | "
                      f"{profit:>10.2f} | "
                      f"{row['full_name'][:25]:<25}")

            print("-" * 105)
            print(f"ЗАГАЛЬНА ВИРУЧКА: {total_sum:.2f} грн")
            print(f"ЗАГАЛЬНИЙ ПРИБУТОК: {total_profit:.2f} грн")

            save_choice = input(f"\nЗберегти звіт за період {start_date} — {end_date} у файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                f_name = f"sales_period_{start_date}_to_{end_date}.csv"
                export_to_csv(rows, f_name)

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №6 Продажі конкретного співробітника"""
def show_employee_sales():
    print(f"\nЗвіт про ПРОДАЖІ СПІВРОБІТНИКА")
    emp_id_str = input("Введіть ID співробітника: ").strip()

    try:
        emp_id = int(emp_id_str)
    except ValueError:
        print("\nПомилка: ID має бути числом!")
        input("Натисніть Enter, щоб спробувати знову")
        return

    stmt = select(
        sales.c.sale_date,
        books.c.title,
        sales.c.actual_price,
        books.c.cost_price,
        employees.c.full_name
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(employees.c.id == emp_id).order_by(sales.c.sale_date.desc())

    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

        if not rows:
            print(f"\nДля співробітника з ID {emp_id} продажів не знайдено.")
        else:
            emp_name = rows[0]['full_name']
            print(f"\n{'=' * 45}\nПРОДАЖІ ЗА СПІВРОБІТНИКОМ\n{'=' * 45}")
            print(f"\nСпівробітник: {emp_name}")
            print(f"{'ДАТА':<12} | {'КНИГА':<30} | {'ЦІНА':<10} | {'ПРИБУТОК':<10}")
            print("-" * 75)

            total_emp_sum = 0
            total_emp_profit = 0

            for row in rows:
                profit = float(row['actual_price']) - float(row['cost_price'])
                total_emp_sum += float(row['actual_price'])
                total_emp_profit += profit

                print(f"{str(row['sale_date']):<12} | "
                      f"{row['title'][:30]:<30} | "
                      f"{float(row['actual_price']):>10.2f} | "
                      f"{profit:>10.2f}")

            print("-" * 75)
            print(f"ЗАГАЛЬНА ВИРУЧКА СПІВРОБІТНИКА: {total_emp_sum:.2f} грн")
            print(f"ЗАГАЛЬНИЙ ПРИБУТОК: {total_emp_profit:.2f} грн")

            save_choice = input(f"\nЗберегти звіт для {emp_name} у файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                f_name = f"sales_{emp_name}.csv".replace(" ", "_")
                export_to_csv(rows, f_name)

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №7 Найбільш продавана книга за період"""
def show_top_book():
    print(f"\nНАЙПОПУЛЯРНІША КНИГА ПЕРІОДУ")
    start_str = input("\nВведіть дату початку періоду (YYYY-MM-DD): ").strip()
    end_str = input("Введіть дату кінця періоду (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("\nПомилка: Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    count_formula = func.count(sales.c.id)

    stmt = select(
        books.c.title,
        count_formula.label('total_count')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        sales.c.sale_date.between(start_date, end_date)
    ).group_by(
        books.c.title
    ).order_by(
        count_formula.desc()
    ).limit(1)

    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()

        if not row:
            print(f"\nЗа період з {start_date} по {end_date} продажів не знайдено.")
        else:
            print(f"\n{'=' * 45}\nНАЙПОПУЛЯРНІША КНИГА ПЕРІОДУ\n{'=' * 45}")
            print(f"\nПеріод аналізу: з {start_date} по {end_date}")
            print(f"НАЗВА КНИГИ: {row['title']}")
            print(f"КІЛЬКІСТЬ ПРОДАНИХ ПРИМІРНИКІВ: {row['total_count']} шт.")

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №8 Найуспішніший продавець за період"""
def show_top_seller():
    print(f"\nНАЙУСПІШНІШИЙ ПРОДАВЕЦЬ ПЕРІОДУ")
    start_str = input("\nВведіть дату початку періоду (YYYY-MM-DD): ").strip()
    end_str = input("Введіть дату кінця періоду (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("Помилка: Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    profit_formula = func.sum(sales.c.actual_price - books.c.cost_price)

    stmt = select(
        employees.c.full_name,
        profit_formula.label('total_profit')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
        .join(employees, sales.c.employee_id == employees.c.id)
    ).where(
        sales.c.sale_date.between(start_date, end_date)
    ).group_by(
        employees.c.full_name
    ).order_by(
        profit_formula.desc()
    ).limit(1)

    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()

        if not row:
            print(f"\nЗа період з {start_date} по {end_date} активності продавців не знайдено.")
        else:
            print(f"\n{'=' * 45}\nНАЙУСПІШНІШИЙ ПРОДАВЕЦЬ ПЕРІОДУ\n{'=' * 45}")
            print(f"\nПеріод аналізу: з {start_date} по {end_date}:")
            print(f"НАЙКРАЩИЙ РЕЗУЛЬТАТ у продавця: {row['full_name']}")
            print(f"ЗАГАЛЬНИЙ ПРИБУТОК: {float(row['total_profit']):.2f} грн.")

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №9 Сумарний прибуток за період"""
def show_total_profit():
    print(f"\nСУМАРНИЙ ПРИБУТОК ЗА ПЕРІОД")
    start_str = input("\nВведіть дату початку (YYYY-MM-DD): ").strip()
    end_str = input("Введіть дату кінця (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("\nПомилка: Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    revenue_formula = func.sum(sales.c.actual_price)
    profit_formula = func.sum(sales.c.actual_price - books.c.cost_price)

    stmt = select(
        revenue_formula.label('total_revenue'),
        profit_formula.label('total_net_profit')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        sales.c.sale_date.between(start_date, end_date)
    )

    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()

        if not row or row['total_revenue'] is None:
            print(f"\nЗа період з {start_date} по {end_date} продажів не зафіксовано.")
        else:
            print(f"\n{'=' * 45}\nЗАГАЛЬНИЙ ПРИБУТОК МАГАЗИНУ\n{'=' * 45}")
            print(f"\nРезультати за період з {start_date} по {end_date}:")
            print("-" * 45)
            print(f"ЗАГАЛЬНА ВИРУЧКА: {float(row['total_revenue']):>15.2f} грн.")
            print(f"ЧИСТИЙ ПРИБУТОК: {float(row['total_net_profit']):>15.2f} грн.")
            print("-" * 45)

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №10 Автор, який найбільше продається за період"""
def show_top_author():
    print(f"\nНАЙПОПУЛЯРНІШИЙ АВТОР ПЕРІОДУ")
    start_str = input("\nВведіть дату початку (YYYY-MM-DD): ").strip()
    end_str = input("Введіть дату кінця (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("\nПомилка: Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    sold_formula = func.count(sales.c.id)

    stmt = select(
        books.c.author,
        sold_formula.label('books_sold')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        sales.c.sale_date.between(start_date, end_date)
    ).group_by(
        books.c.author
    ).order_by(
        sold_formula.desc()
    ).limit(1)

    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()

        if not row:
            print(f"\nЗа період з {start_date} по {end_date} продажів не знайдено.")
        else:
            print(f"\n{'=' * 45}\nНАЙПОПУЛЯРНІШИЙ АВТОР ПЕРІОДУ\n{'=' * 45}")
            print(f"\nРезультати за період з {start_date} по {end_date}:")
            print(f"АВТОР-ЛІДЕР ПРОДАЖІВ: {row['author']}")
            print(f"КІЛЬКІСТЬ ПРОДАНИХ КНИГ: {row['books_sold']} шт.")

    input("\nНатисніть Enter для повернення до меню")

"""Звіт №11 Жанр, що найбільше продається за період"""
def show_top_genre():
    print(f"\nНАЙУСПІШНІШИЙ ЖАНР ПЕРІОДУ")
    start_str = input("\nВведіть дату початку (YYYY-MM-DD): ").strip()
    end_str = input("Введіть дату кінця (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("\nПомилка: Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        input("Натисніть Enter, щоб спробувати знову")
        return

    genre_sales_formula = func.count(sales.c.id)

    stmt = select(
        books.c.genre,
        genre_sales_formula.label('genre_sales')
    ).select_from(
        sales.join(books, sales.c.isbn == books.c.isbn)
    ).where(
        sales.c.sale_date.between(start_date, end_date)
    ).group_by(
        books.c.genre
    ).order_by(
        genre_sales_formula.desc()
    ).limit(1)

    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()

        if not row:
            print(f"\nЗа період з {start_date} по {end_date} продажів не зафіксовано.")
        else:
            print(f"\n{'=' * 45}\nНАЙПОПУЛЯРНІШИЙ ЖАНР ПЕРІОДУ\n{'=' * 45}")
            print(f"\nРезультати за період з {start_date} по {end_date}:")
            print(f"ЖАНР-БЕСТСЕЛЕР: {row['genre']}")
            print(f"КІЛЬКІСТЬ ПРОДАНИХ КНИГ : {row['genre_sales']} шт.")

    input("\nНатисніть Enter для повернення до меню")

# фУНКЦІЇ

"""Функція №1. Додавання нової книги"""
def add_book():
    print(f"\n{'='*45}\nДОДАВАННЯ НОВОЇ КНИГИ\n{'='*45}")
    isbn = input("ISBN (унікальний код): ").strip()
    title = input("Назва книги: ").strip()
    author = input("Автор: ").strip()
    genre = input("Жанр: ").strip()

    try:
        year = int(input("Рік публікації (YYYY): ").strip())
        cost = float(input("Собівартість (cost_price): ").strip())
        retail = float(input("Ціна продажу (retail_price): ").strip())

        if cost <= 0 or retail <= 0:
            print("Помилка: Ціни мають бути додатними!")
            input("\nНатисніть Enter для повернення")
            return
    except ValueError:
        print("Помилка: Рік та ціни мають бути тільки числовими!")
        input("\nНатисніть Enter для повернення")
        return
    stmt = insert(books).values(
        isbn=isbn,
        title=title,
        author=author,
        genre=genre,
        year_pub=year,
        cost_price=cost,
        retail_price=retail,
        is_deleted=False
    )

    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()
        print(f"Книга «{title}» успішно додана!")

    input("\nНатисніть Enter для повернення до меню")

"""Функція №2. Редагування інформації про книгу"""
def edit_book():
    print(f"\n{'=' * 45}\nРЕДАГУВАННЯ ДАНИХ КНИГИ\n{'=' * 45}")
    isbn_to_find = input("Введіть ISBN книги, яку треба змінити: ").strip()
    check_stmt = select(books).where(books.c.isbn == isbn_to_find)

    with engine.connect() as conn:
        book = conn.execute(check_stmt).mappings().first()

        if not book:
            print("Книгу з таким ISBN не знайдено.")
            input("\nНатисніть Enter для повернення")
            return

        print(f"\nЗнайдено книгу: «{book['title']}»")
        print("Введіть нові дані (натисніть Enter, щоб залишити без змін):")

        new_title = input(f"Нова назва [{book['title']}]: ").strip() or book['title']
        new_author = input(f"Новий автор [{book['author']}]: ").strip() or book['author']
        new_genre = input(f"Новий жанр [{book['genre']}]: ").strip() or book['genre']

        try:
            raw_year = input(f"Новий рік видання [{book['year_pub']}]: ").strip()
            new_year = int(raw_year) if raw_year else book['year_pub']

            raw_cost = input(f"Нова собівартість [{book['cost_price']}]: ").strip()
            new_cost = float(raw_cost) if raw_cost else book['cost_price']

            raw_retail = input(f"Нова ціна продажу [{book['retail_price']}]: ").strip()
            new_retail = float(raw_retail) if raw_retail else book['retail_price']

            if new_cost <= 0 or new_retail <= 0:
                print("Помилка: Ціни мають бути додатними!")
                input("\nНатисніть Enter для повернення")
                return
        except ValueError:
            print("Помилка: Ціни мають бути числовими!")
            input("\nНатисніть Enter для повернення")
            return

        update_stmt = update(books).where(books.c.isbn == isbn_to_find).values(
            title=new_title,
            author=new_author,
            genre=new_genre,
            year_pub=new_year,
            cost_price=new_cost,
            retail_price=new_retail
        )

        conn.execute(update_stmt)
        conn.commit()
        print(f"\nІнформацію про книгу успішно оновлено!")

    input("\nНатисніть Enter для повернення до меню")

"""Функція №3. Видалення книги"""
def delete_book():
    print(f"\n{'=' * 45}\nВИДАЛЕННЯ КНИГИ З КАТАЛОГУ\n{'=' * 45}")
    isbn_to_del = input("Введіть ISBN книги для видалення: ").strip()
    check_stmt = select(books.c.title).where(books.c.isbn == isbn_to_del)

    with engine.connect() as conn:
        book = conn.execute(check_stmt).mappings().first()

        if not book:
            print("Книгу з таким ISBN не знайдено.")
        else:
            print(f"\nВи впевнені, що хочете видалити книгу: «{book['title']}»?")
            confirm = input("Введіть 'y' для підтвердження або будь-яку іншу клавішу для скасування: ").strip().lower()

            if confirm == 'y':
                stmt = update(books).where(books.c.isbn == isbn_to_del).values(is_deleted=True)
                conn.execute(stmt)
                conn.commit()
                print(f"\nКнигу «{book['title']}» успішно приховано з каталогу.")
            else:
                print("\nВидалення скасовано.")

    input("\nНатисніть Enter для повернення до меню")


"""Функція №4. Додавання нового співробітника"""
def add_employee():
    print(f"\n{'='*45}\nДОДАВАННЯ НОВОГО СПІВРОБІТНИКА\n{'='*45}")

    full_name = input("ПІБ співробітника: ").strip()
    position = input("Посада: ").strip()
    phone = input("Номер телефону: ").strip()
    while True:
        email = input("Email: ").strip()
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            break
        else:
            print("\nПомилка: Некоректний формат Email.")
            print("Підказка: Адреса має містити '@' та крапку (наприклад: name@gmail.com)")

            choice = input("\nБажаєте спробувати ще раз? (y - так, n - вийти в меню): ").strip().lower()
            if choice != 'y':
                print("Додавання співробітника скасовано")
                input("Натисніть Enter для повернення")
                return

    if not full_name or not position:
        print("Помилка: ПІБ та Посада є обов'язковими для заповнення!")
        input("\nНатисніть Enter для повернення")
        return

    stmt = insert(employees).values(
        full_name=full_name,
        position=position,
        phone=phone,
        email=email,
        is_deleted=False
    )

    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()
        print(f"\nСпівробітника {full_name} успішно додано!")

    input("\nНатисніть Enter для повернення до меню")


"""Функція №5. Редагування даних співробітника"""
def edit_employee():
    print(f"\n{'=' * 45}\nРЕДАГУВАННЯ ДАНИХ СПІВРОБІТНИКА\n{'=' * 45}")
    emp_id_str = input("Введіть ID співробітника для змін: ").strip()

    try:
        emp_id = int(emp_id_str)
    except ValueError:
        print("\nПомилка: ID має бути числом!")
        input("Натисніть Enter для повернення")
        return

    check_stmt = select(employees).where(employees.c.id == emp_id)

    with engine.connect() as conn:
        employee = conn.execute(check_stmt).mappings().first()

        if not employee:
            print(f"Співробітника з ID {emp_id} не знайдено.")
            input("\nНатисніть Enter для повернення")
            return

        print(f"\nЗнайдено: {employee['full_name']}")
        print("Введіть нові дані (натисніть Enter, щоб залишити без змін):")

        new_name = input(f"ПІБ [{employee['full_name']}]: ").strip() or employee['full_name']
        new_position = input(f"Посада [{employee['position']}]: ").strip() or employee['position']
        new_phone = input(f"Телефон [{employee['phone']}]: ").strip() or employee['phone']
        while True:
            new_email = input(f"Email [{employee['email']}]: ").strip() or employee['email']
            if re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                break
            else:
                print("Помилка: Некоректний формат Email (має бути name@gmail.com)")
                choice = input("Бажаєте спробувати ще раз? (y/n): ").strip().lower()
                if choice != 'y':
                    print("Редагування скасовано.")
                    input("Натисніть Enter для повернення в меню.")
                    return

        update_stmt = update(employees).where(employees.c.id == emp_id).values(
            full_name=new_name,
            position=new_position,
            phone=new_phone,
            email=new_email
        )

        conn.execute(update_stmt)
        conn.commit()
        print(f"\nДані співробітника {new_name} успішно оновлено!")

    input("\nНатисніть Enter для повернення до меню")

"""Функція №6. Видалення (звільнення) співробітника"""
def delete_employee():
    print(f"\n{'=' * 45}\n ЗВІЛЬНЕННЯ СПІВРОБІТНИКА\n{'=' * 45}")
    emp_id_str = input("Введіть ID співробітника для видалення: ").strip()

    try:
        emp_id = int(emp_id_str)
    except ValueError:
        print("\nПомилка: ID має бути числом!")
        input("Натисніть Enter для повернення")
        return

    check_stmt = select(employees.c.full_name).where(employees.c.id == emp_id)

    with engine.connect() as conn:
        employee = conn.execute(check_stmt).mappings().first()

        if not employee:
            print(f"Співробітника з ID {emp_id} не знайдено.")
        else:
            print(f"\nВи впевнені, що хочете позначити як звільненого: {employee['full_name']}?")
            confirm = input("Введіть 'y' для підтвердження: ").strip().lower()

            if confirm == 'y':
                stmt = update(employees).where(employees.c.id == emp_id).values(is_deleted=True)
                conn.execute(stmt)
                conn.commit()
                print(f"\nСпівробітник {employee['full_name']} переведений у статус звільнених.")
            else:
                print("\nДія скасована.")

    input("\nНатисніть Enter для повернення до меню")

"""Функція №7. Оформлення нового продажу"""
def register_sale():
    print(f"\n{'='*45}\nОФОРМЛЕННЯ НОВОГО ПРОДАЖУ\n{'='*45}")
    book_isbn = input("Введіть ISBN книги: ").strip()
    emp_id_str = input("Введіть ID співробітника: ").strip()

    try:
        emp_id = int(emp_id_str)
    except ValueError:
        print("\nПомилка: ID співробітника має бути числом!")
        input("Натисніть Enter для повернення")
        return

    current_date = datetime.now().date()

    with engine.connect() as conn:
        # Валідація наявності книги у каталозі
        book_stmt = select(books.c.title, books.c.author, books.c.retail_price).where(
            (books.c.isbn == book_isbn) & (books.c.is_deleted == False)
        )
        book_check = conn.execute(book_stmt).mappings().first()

        if not book_check:
            print("Помилка: Книгу не знайдено!")
            input("\nНатисніть Enter для повернення")
            return
        # Валідація наявності пацівника
        emp_stmt = select(employees.c.full_name).where(
            (employees.c.id == emp_id) & (employees.c.is_deleted == False)
        )
        emp_check = conn.execute(emp_stmt).mappings().first()

        if not emp_check:
            print("Помилка: Співробітника не знайдено!")
            input("\nНатисніть Enter для повернення")
            return
        # Реєстрація продажу (декілька примірників однієї книги)
        try:
            qty_input = input(f"Кількість примірників [1]: ").strip()
            qty = int(qty_input) if qty_input else 1

            price_input = input(f"Ціна за 1 шт [{book_check['retail_price']}]: ").strip()
            price = float(price_input) if price_input else book_check['retail_price']

            if qty <= 0 or price <= 0:
                print("Помилка: Значення мають бути додатними!")
                input("\nНатисніть Enter для повернення")
                return
        except ValueError:
            print("Помилка: Введіть числові значення!")
            input("\nНатисніть Enter для повернення")
            return

            # Враховуємо кількість примірників циклом окремими рядками
        for _ in range(qty):
            stmt = insert(sales).values(
                isbn=book_isbn,
                employee_id=emp_id,
                sale_date=current_date,
                actual_price=price
            )
            conn.execute(stmt)

        conn.commit()

        print(f"\nПродаж успішно оформлено!")
        print("-" * 40)
        print(f"Книга:      {book_check['title']}")
        print(f"Автор:      {book_check['author']}")
        print(f"Дата:       {current_date}")
        print(f"Кількість:  {qty} шт.")
        print(f"Ціна:       {price:.2f} грн")
        print(f"РАЗОМ:      {qty * price:.2f} грн")
        print(f"Продавець:  {emp_check['full_name']}")
        print("-" * 40)

    input("\nНатисніть Enter для повернення до меню")




#  ГОЛОВНЕ МЕНЮ

def main_menu():
    while True:
        print(f"\n{'=' * 50}")
        print(f"{'СИСТЕМА УПРАВЛІННЯ КНИЖКОВИМ МАГАЗИНОМ':^50}")
        print(f"{'=' * 50}")

        print("\n1. АДМІНІСТРАТОР")
        print("2. ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ (ПРОДАЖІ)")
        print("3. АНАЛІТИКА ТА ЗВІТНІСТЬ")

        print("\n0. ВИХІД З ПРОГРАМИ")
        print(f"{'=' * 50}")

        choice = input("\nОберіть розділ меню: ").strip()

        if choice == "1":
            data_management_menu()
        elif choice == "2":
            sales_operations_menu()
        elif choice == "3":
            analytics_reports_menu()
        elif choice == "0":
            print("\nДякуємо за роботу! Програма завершена.")
            break
        else:
            print("Невірний вибір! Введіть цифру від 0 до 3.")
            input("Натисніть Enter для повернення")

#  АДМІНІСТРАТОР

def data_management_menu():
    while True:
        print(f"\n{'-' * 45}")
        print(f"{'КЕРУВАННЯ КНИГАМИ ТА ПЕРСОНАЛОМ':^45}")
        print(f"{'-' * 45}")

        print("\n--- [ КНИГИ ] ---")
        print("1. Додати нову книгу")
        print("2. Редагувати інформацію про книгу")
        print("3. Видалити книгу з каталогу")

        print("\n--- [ ПЕРСОНАЛ ] ---")
        print("4. Додати нового співробітника")
        print("5. Редагувати дані співробітника")
        print("6. Видалити співробітника")

        print("\n0. Повернутися до Головного меню")
        print(f"{'-' * 45}")

        choice = input("\nОберіть дію: ").strip()

        if choice == "1":
            add_book() # Функція №1
        elif choice == "2":
            edit_book() # Функція №2
        elif choice == "3":
            delete_book() # Функція №3
        elif choice == "4":
            add_employee() # Функція №4
        elif choice == "5":
            edit_employee() # Функція №5
        elif choice == "6":
            delete_employee() # Функція №6
        elif choice == "0":
            break
        else:
            print("Невірний вибір! Введіть цифру від 0 до 6.")
            input("Натисніть Enter для повернення")

#  ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ (ПРОДАЖІ)

def sales_operations_menu():
    while True:
        print(f"\n{'-' * 45}")
        print(f"{'ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ (ПРОДАЖІ)':^45}")
        print(f"{'-' * 45}")

        print("1. Оформити НОВИЙ ПРОДАЖ")
        print("2. Переглянути повну історію продажів")
        print("-" * 25)
        print("3. Список усіх книг (каталог)")
        print("4. Список усіх співробітників")

        print("\n0. Повернутися до Головного меню")
        print(f"{'-' * 45}")

        choice = input("\nОберіть дію: ").strip()

        if choice == "1":
            register_sale() # Функція №7
        elif choice == "2":
            show_all_sales()  # Звіт №3
        elif choice == "3":
            show_all_books()  # Звіт №2
        elif choice == "4":
            show_all_employees()  # Звіт №1
        elif choice == "0":
            break
        else:
            print("Невірний вибір! Введіть цифру від 0 до 4.")
            input("Натисніть Enter для повернення")

#  АНАЛІТИКА ТА ЗВІТНІСТЬ

def analytics_reports_menu():
    while True:
        print(f"\n{'-' * 45}")
        print(f"{'АНАЛІТИЧНА ТА ЗВІТНІСТЬ':^45}")
        print(f"{'-' * 45}")

        print("1. Продажі за конкретну дату")
        print("2. Продажі за обраний період")
        print("3. Продажі конкретного співробітника")
        print("-" * 25)
        print("4. Найбільш продавана книга за період")
        print("5. НАЙУСПІШНІШИЙ ПРОДАВЕЦЬ визначеного періоду (за прибутком)")
        print("6. ЗАГАЛЬНИЙ ПРИБУТОК МАГАЗИНУ")
        print("7. Найпопулярніший АВТОР")
        print("8. Найпопулярніший ЖАНР")

        print("\n0. Повернутися до Головного меню")
        print(f"{'-' * 45}")

        choice = input("\nОберіть звіт: ").strip()

        if choice == "1":
            show_sales_by_date()  # Звіт №4
        elif choice == "2":
            show_sales_by_period()  # Звіт №5
        elif choice == "3":
            show_employee_sales()  # Звіт №6
        elif choice == "4":
            show_top_book()  # Звіт №7
        elif choice == "5":
            show_top_seller()  # Звіт №8
        elif choice == "6":
            show_total_profit()  # Звіт №9
        elif choice == "7":
            show_top_author()  # Звіт №10
        elif choice == "8":
            show_top_genre()  # Звіт №11
        elif choice == "0":
            break
        else:
            print("Невірний вибір! Введіть цифру від 0 до 8.")
            input("Натисніть Enter для повернення")



if __name__ == "__main__":
    main_menu()