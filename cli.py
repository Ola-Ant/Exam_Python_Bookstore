from validators import validate_year, validate_email, validate_date, validate_date_range
from services import export_to_csv
import repositories as repo

# Soft delete
def delete_item_soft(table, label):
    while True:
        val = input(f"Введіть {label} для видалення (або 0 для виходу): ").strip()
        if val == "0":
            print("\nДію скасовано. Повернення в меню...")
            return
        if not val:
            print(f"Помилка: {label} не може бути порожнім.")
            continue
        if label == "ID" and not val.isdigit():
            print("Помилка: ID має бути числом.")
            continue
        break
    display_name = ""
    if label == "ISBN":
        item = repo.db_get_book_by_isbn(val)
        if item:
            display_name = f"Книгу «{item['title']}»"
    else:
        item = repo.db_get_employee_by_id(int(val))
        if item:
            display_name = f"Співробітника ({item['full_name']})"

    if not display_name:
        print(f"\nПомилка. {label} '{val}' не знайдено в базі даних.")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    confirm = input(f"\nВи впевнені, що хочете видалити {display_name}? (y/n): ").strip().lower()

    if confirm == 'y':
        col = table.c.isbn if label == "ISBN" else table.c.id
        repo.db_soft_delete(table, col, val)
        print(f"\n{label} успішно видалено (позначено як видалений).")
    else:
        print("\nДію скасовано")

    input("\nНатисніть Enter, щоб повернутися до меню")

# ПРОДАЖІ

# Реєстрація нового продажу
def register_sale():
    print(f"\n{'=' * 45}\nНОВИЙ ПРОДАЖ\n{'=' * 45}")

    isbn = input("ISBN книги: ").strip()
    book = repo.db_get_book_by_isbn(isbn)

    if not book:
        print("Помилка: Книгу не знайдено")
        return

    print(f"Вибрано: «{book['title']}»")

    while True:
        emp_id_in = input("ID продавця: ").strip()
        try:
            emp_id = int(emp_id_in)
            if repo.db_get_employee_by_id(emp_id):
                break
            print("Помилка: Співробітника з таким ID не існує")
        except ValueError:
            print("Помилка: ID має бути числом")

    while True:
        try:
            qty_in = input("Кількість [1]: ").strip()
            qty = int(qty_in) if qty_in else 1

            if qty <= 0:
                print("Помилка: Кількість має бути більше 0")
                continue

            price_in = input(f"Ціна [{book['retail_price']} грн]: ").strip()
            price = float(price_in) if price_in else book['retail_price']

            if price < 0:
                print("Помилка: Ціна не може бути від'ємною")
                continue
            break
        except ValueError:
            print("Помилка: Вводьте числа для ціни та кількості")

    repo.db_add_sale(isbn, emp_id, price, qty)
    print(f"\nУспішно! Оформлено продаж {qty} шт. на суму {price * qty:.2f} грн.")
    input("\nНатисніть Enter, щоб повернутися до меню")

# Історія продажів (Звіт 3)
def show_full_sales_history_report():
    data = repo.db_get_all_sales_history()
    if not data:
        print("Історія продажів порожня")
        return
    print(f"\n{'ПОВНИЙ СПИСОК ПРОДАЖІВ':^65}")
    print(f"{'ID':<5} | {'Дата':<10} | {'Книга':<30} | {'Ціна':<8}")
    print("-" * 65)

    for r in data:
        d = str(r['sale_date'])[:10]
        t = r['title'][:30]
        print(f"{r['id']:<5} | {d:<10} | {t:<30} | {r['actual_price']:>8.2f}")

    confirm = input("\nЗберегти дані у CSV-файл? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        filename = f"sales_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        export_to_csv(data, filename)

# Коригування ціни
def edit_sale_price_ui():
    print(f"\n{'-' * 20} КОРИГУВАННЯ ЦІНИ {'-' * 20}")
    while True:
        sid_in = input("ID запису для редагування (0 - повернутись в меню): ").strip()
        if sid_in == "0":
            break

        try:
            sid = int(sid_in)
            sale = repo.db_get_sale_by_id(sid)

            if not sale:
                print(f"Помилка: Запису з ID {sid} не знайдено")
                continue
            print(f"Поточна ціна чека №{sid}: {sale['actual_price']} грн")

            new_p_in = input("Введіть нову ціну: ").strip()

            if not new_p_in:
                print("Ціна не може бути порожньою")
                continue

            new_p = float(new_p_in)
            if new_p < 0:
                print("Ціни мають бути додатними")
                continue

            repo.db_update_sale_price(sid, new_p)
            print(f"Ціну для продажу №{sid} успішно змінено на {new_p} грн")
            break

        except ValueError:
            print("Помилка: Вводьте лише числа для ID та ціни")

# Видалення продажу (повне)
def delete_sale_ui():
    print(f"\n{'=' * 10} ВИДАЛЕННЯ ПРОДАЖУ {'=' * 10}")
    while True:
        sid_in = input("ID запису для ПОВНОГО видалення (0 - повернутись в меню): ").strip()
        if sid_in == "0":
            break
        try:
            sid = int(sid_in)
            sale = repo.db_get_sale_by_id(sid)
            if not sale:
                print(f"Помилка: Продаж №{sid} не знайдено.")
                continue

            print(f"\n{'-' * 40}")
            print(f"ЗНАЙДЕНО ПРОДАЖ №{sid}")
            print(f"Книга: {sale.get('book_title', 'Не вказано')}")
            print(f"Продавець: {sale.get('employee_name', 'Не вказано')}")
            print(f"Сума: {sale['actual_price']} грн.")
            print(f"Дата: {sale.get('sale_date', '---')}")
            print(f"{'-' * 40}")

            confirm = input(f"Ви впевнені, що хочете видалити його НАЗАВЖДИ? (y/n): ").strip().lower()

            if confirm == 'y':
                repo.db_delete_sale(sid)
                print(f"Запис №{sid} остаточно видалено з бази.")
                break
            else:
                print("Скасовано. Запис залишається в базі.")
                break

        except ValueError:
            print("Помилка: ID має бути цілим числом.")

    input("\nНатисніть Enter, щоб повернутися до меню")

# КНИГИ

# Каталог книг (Звіт 2)
def show_all_books_report():
    print(f"\n{'=' * 55}\nКАТАЛОГ КНИГ\n{'=' * 55}")
    rows = repo.db_get_books()
    if not rows: print("Каталог порожній."); return
    print(f"{'ISBN':<13} | {'Назва книги':<30} | {'Ціна':<8}")
    print("-" * 55)
    for r in rows:
        print(f"{r['isbn']:<13} | {r['title'][:30]:<30} | {r['retail_price']:>8.2f} грн")
    print(f"\n{'-' * 55}")

    confirm = input("Зберегти дані у CSV-файл? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"books_catalog_{timestamp}.csv"
        export_to_csv(rows, filename)

# Додати нову книгу
def add_book_cli():
    print(f"\n{'=' * 45}\nРЕЄСТРАЦІЯ КНИГИ\n{'=' * 45}")

    while True:
        isbn = input("ISBN: ").strip()
        title = input("Назва: ").strip()
        author = input("Автор: ").strip()
        genre = input("Жанр: ").strip()

        if isbn and title and author and genre:
            break
        print("Помилка: Усі текстові поля (ISBN, Назва, Автор, Жанр) мають бути заповнені")

    while True:
        yr = input("Рік видання: ")
        ok, msg = validate_year(yr)
        if ok:
            year = int(yr)
            break
        print(f" {msg}")

    while True:
        try:
            cost = float(input("Собівартість: "))
            retail = float(input("Ціна продажу: "))

            if cost < 0 or retail < 0:
                print("Помилка: Ціни мають бути додатними")
                continue
            break
        except ValueError:
            print("Помилка: Ціни мають бути числами (наприклад: 250.50)")

    book_info = {
        'isbn': isbn,
        'title': title,
        'author': author,
        'genre': genre,
        'year_pub': year,
        'cost_price': cost,
        'retail_price': retail
    }
    try:
        repo.db_add_book(book_info)
        print("\n[Успіх]: Книгу успішно збережено в базі!")
    except Exception as e:
        if "unique" in str(e).lower():
            print(f"\nКнига з ISBN '{isbn}' вже існує в системі")
            print("Ви не можете додати дублікат")
        else:
            print(f"\n[Помилка бази даних]: {e}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Редагувати дані книги
def edit_book_cli():
    print(f"\n{'=' * 45}\nРЕДАГУВАННЯ ДАНИХ КНИГИ\n{'=' * 45}")
    isbn_to_find = input("Введіть ISBN книги для зміни: ").strip()

    book = repo.db_get_book_by_isbn(isbn_to_find)
    if not book:
        print("Книгу з таким ISBN не знайдено.")
        return

    print(f"\nЗнайдено: «{book['title']}»")
    print("Введіть нові дані (або залишити старе - Enter):")

    new_title = input(f"Нова назва [{book['title']}]: ").strip() or book['title']
    new_author = input(f"Новий автор [{book['author']}]: ").strip() or book['author']
    new_genre = input(f"Новий жанр [{book['genre']}]: ").strip() or book['genre']

    while True:
        raw_year = input(f"Новий рік видання [{book['year_pub']}]: ").strip()
        if not raw_year:
            new_year = book['year_pub']
            break

        ok, msg = validate_year(raw_year)
        if ok:
            new_year = int(raw_year)
            break
        print(f"{msg}")

    while True:
        try:
            raw_cost = input(f"Нова собівартість [{book['cost_price']}]: ").strip()
            new_cost = float(raw_cost) if raw_cost else book['cost_price']

            raw_retail = input(f"Нова ціна продажу [{book['retail_price']}]: ").strip()
            new_retail = float(raw_retail) if raw_retail else book['retail_price']

            if new_cost <= 0 or new_retail <= 0:
                print("Помилка: Ціни мають бути додатними")
                continue
            break
        except ValueError:
            print("Помилка: Вводьте числа для цін")

    updated_info = {
        'title': new_title, 'author': new_author, 'genre': new_genre,
        'year_pub': new_year, 'cost_price': new_cost, 'retail_price': new_retail
    }

    repo.db_update_book(isbn_to_find, updated_info)
    print(f"\nДані успішно оновлено!")
    input("\nНатисніть Enter, щоб повернутися до меню")

# Видалення книги (soft delete)
def delete_book_ui():
    print(f"\n{'=' * 45}\nВИДАЛЕННЯ КНИГИ (архівування)\n{'=' * 45}")

    books = repo.db_get_books()

    if not books:
        print("\nВ базі немає книг для видалення.")
        input("\nНатисніть Enter, щоб повернутися в меню")
        return

    print(f"\n{'ISBN':<15} | {'Назва':<30}")
    print("-" * 45)
    for b in books:
        if not b.get('is_deleted', False):
            print(f"{b['isbn']:<15} | {b['title']:<30}")
    print("-" * 45)

    from models import books as books_table
    delete_item_soft(books_table, "ISBN")

# СПІВРОБІТНИКИ

# Штат співробітників (Звіт 1)
def show_employees_report():
    print(f"\n{'=' * 85}\nСПИСОК СПІВРОБІТНИКІВ (ШТАТ)\n{'=' * 85}")
    data = repo.db_get_all_employees()

    if not data:
        print("У штаті поки немає жодного співробітника.")
        return
    header = f"{'ID':<4} | {'ПІБ':<20} | {'Посада':<15} | {'Телефон':<13} | {'Email':<20}"
    print(header)
    print("-" * 85)

    for e in data:
        name = e['full_name'][:20]
        pos = e['position'][:15]
        tel = e['phone'] if e['phone'] else "-"
        mail = e['email'] if e['email'] else "-"
        print(f"{e['id']:<4} | {name:<20} | {pos:<15} | {tel:<13} | {mail:<20}")

    print(f"\n{'-' * 45}")

    confirm = input("Зберегти дані у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"employees_contacts_{timestamp}.csv"
        export_to_csv(data, filename)

# Додати співробітника
def add_employee_cli():
    print(f"\n{'=' * 45}\nНОВИЙ СПІВРОБІТНИК\n{'=' * 45}")

    while True:
        name = input("ПІБ: ").strip()
        pos = input("Посада: ").strip()
        if name and pos:
            break
        print("Помилка: ПІБ та Посада обов'язкові!")

    ph = input("Телефон: ").strip()

    while True:
        em = input("Email: ").strip()
        is_ok, msg = validate_email(em)
        if is_ok:
            break
        print(f"{msg}")

    emp_data = {
        'full_name': name,
        'position': pos,
        'phone': ph,
        'email': em
    }
    repo.db_add_employee(emp_data)
    print(f"Співробітника {name} успішно зареєстровано")
    input("\nНатисніть Enter, щоб повернутися до меню")

# Редагувати дані співробітника
def edit_employee_cli():
    print(f"\n{'=' * 45}\nРЕДАГУВАННЯ ДАНИХ СПІВРОБІТНИКА\n{'=' * 45}")
    employees = repo.db_get_all_employees()
    if not employees:
        print("В базі немає зареєстрованих співробітників.")
        input("\nНатисніть Enter")
        return

    print(f"{'ID':<5} | {'ПІБ':<25} | {'Посада'}")
    print("-" * 45)
    for e in employees:
        print(f"{e['id']:<5} | {e['full_name']:<25} | {e['position']}")
    print("-" * 45)

    emp_id_str = input("\nВведіть ID співробітника для зміни: ").strip()

    try:
        emp_id = int(emp_id_str)
    except ValueError:
        print("Помилка: ID має бути числом")
        input("\nНатисніть Enter")
        return

    employee = repo.db_get_employee_by_id(emp_id)
    if not employee:
        print(f"Співробітника з ID {emp_id} не знайдено.")
        input("\nНатисніть Enter")
        return

    print(f"\nЗнайдено: {employee['full_name']}")
    print("Введіть нові дані (Enter, щоб залишити без змін):")

    new_name = input(f"ПІБ [{employee['full_name']}]: ").strip() or employee['full_name']
    new_position = input(f"Посада [{employee['position']}]: ").strip() or employee['position']
    new_phone = input(f"Телефон [{employee['phone']}]: ").strip() or employee['phone']

    while True:
        new_email_input = input(f"Email [{employee['email']}]: ").strip()

        if not new_email_input:
            new_email = employee['email']
            break

        is_ok, msg = validate_email(new_email_input)
        if is_ok:
            new_email = new_email_input
            break
        print(f"{msg}")

    updated_info = {
        'full_name': new_name,
        'position': new_position,
        'phone': new_phone,
        'email': new_email
    }
    repo.db_update_employee(emp_id, updated_info)

    print(f"\nДані співробітника {new_name} успішно оновлено!")
    input("\nНатисніть Enter, щоб повернутися до меню")

# Видалення співробітника (soft delete)
def delete_employee_ui():
    print(f"\n{'=' * 45}\nВИДАЛЕННЯ СПІВРОБІТНИКА (звільнення)\n{'=' * 45}")
    employees = repo.db_get_all_employees()
    if not employees:
        print("\n[Увага]: В базі немає активних співробітників для видалення.")
        input("\nНатисніть Enter, щоб повернутися в меню")
        return

    print(f"\n{'ID':<5} | {'ПІБ':<25} | {'Посада'}")
    print("-" * 45)
    for e in employees:
        if not e.get('is_deleted', False):
            print(f"{e['id']:<5} | {e['full_name']:<25} | {e['position']}")
    print("-" * 45)

    from models import employees as emp_table
    delete_item_soft(emp_table, "ID")

# ЗВІТИ

# Продажі на дату (Звіт №4)
def show_sales_by_date_report():
    print(f"\n{'=' * 65}\nПРОДАЖІ ЗА ОБРАНУ ДАТУ\n{'=' * 65}")

    target_date = input("Введіть дату (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date(target_date)
    if not is_valid:
        print(f"Помилка: {msg}")
        return

    data = repo.db_get_sales_by_date(target_date)

    if not data:
        print(f"За дату {target_date} продажів не знайдено.")
        return

    print(f"\n{'ID':<5} | {'Співробітник':<20} | {'Книга':<20} | {'Ціна':<8}")
    print("-" * 65)

    for r in data:
        price = float(r['actual_price'])
        print(f"{r['id']:<5} | {r['full_name'][:20]:<20} | {r['title'][:20]:<20} | {price:>8.2f}")

    confirm = input("\nЗберегти звіт у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        filename = f"sales_day_{target_date.replace('-', '')}.csv"
        export_to_csv(data, filename)

# Продажі за період (Звіт №5)
def show_sales_by_period_report():
    print(f"\n{'=' * 75}\nЗВІТ: ПРОДАЖІ ЗА ПЕРІОД\n{'=' * 75}")

    start = input("Дата початку (РРРР-ММ-ДД): ").strip()
    end = input("Дата кінця (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"Помилка: {msg}")
        return

    data = repo.db_get_sales_by_period(start, end)

    if not data:
        print(f"За період з {start} по {end} продажів не знайдено.")
        return

    print(f"{'ID':<5} | {'Дата':<10} | {'Книга':<25} | {'Ціна':>8}")
    print("-" * 75)

    total_revenue = 0
    for r in data:
        d = str(r['sale_date'])[:10]
        print(f"{r['id']:<5} | {d:<10} | {r['title'][:25]:<25} | {r['actual_price']:>8.2f}")
        total_revenue += r['actual_price']

    print("-" * 75)
    print(f"{'РАЗОМ ЗА ПЕРІОД:':>46} | {total_revenue:>8.2f} грн")

    confirm = input("\nЗберегти звіт у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        filename = f"sales_period_{start}_to_{end}.csv"
        export_to_csv(data, filename)

# Звіт по співробітнику (Звіт №6)
def show_sales_by_employee_report():
    print(f"\n{'=' * 75}\nЗВІТ: ПРОДАЖІ ПО СПІВРОБІТНИКУ\n{'=' * 75}")

    staff = repo.db_get_all_employees()
    if not staff:
        print("Помилка: штат порожній.")
        return

    print("Доступні співробітники:")
    print(f"{'ID':<4} | {'ПІБ':<30} | {'Посада':<20}")
    print("-" * 60)
    for s in staff:
        print(f"{s['id']:<4} | {s['full_name']:<30} | {s['position']:<20}")

    emp_id_in = input("\nВведіть ID співробітника для звіту (0 - повернення в меню): ").strip()
    if emp_id_in == "0": return
    if not emp_id_in.isdigit():
        print("Помилка: ID має бути числом.")
        return
    emp_id = int(emp_id_in)

    data = repo.db_get_sales_by_employee(emp_id)
    if not data:
        print(f"Записів про продажі для ID {emp_id} не знайдено.")
        return

    emp_name = data[0]['full_name']

    print(f"\nІсторія продажів для: {emp_name}")
    print(f"{'ID':<5} | {'Дата':<10} | {'Книга':<30} | {'Ціна':>8}")
    print("-" * 65)

    total_revenue = 0
    for r in data:
        date_str = str(r['sale_date'])[:10]
        print(f"{r['id']:<5} | {date_str:<10} | {r['title'][:30]:<30} | {r['actual_price']:>8.2f}")
        total_revenue += r['actual_price']

    print("-" * 65)
    print(f"{'ЗАГАЛЬНА СУМА:':>48} | {total_revenue:>8.2f} грн")

    confirm = input("\nЗберегти дані по співробітнику у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        filename = f"sales_emp_{emp_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        export_to_csv(data, filename)

# Топ книга періоду (Звіт №7)
def show_most_sold_book_report():
    print(f"\n{'=' * 60}\nНАЙБІЛЬШ ПРОДАВАНА КНИГА\n{'*' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\nПомилка: {msg}")
        return
    data = repo.db_get_most_sold_book(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не було.")
        return
    top_book = data[0]
    revenue = float(top_book['total_revenue'])

    print(f"\nБЕСТСЕЛЕР ПЕРІОДУ:")
    print(f"Назва: {top_book['title']}")
    print(f"Кількість продажів: {top_book['sales_count']} прим.")
    print(f"Загальна виручка: {revenue:,.2f} грн")
    print(f"*" * 60)

# Найкращий продавець (Звіт №8)
def show_best_employee_report():
    print(f"\n{'=' * 60}\nАНАЛІЗ: НАЙКРАЩИЙ ПРОДАВЕЦЬ ПЕРІОДУ\n{'*' * 60}")
    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\nПомилка: {msg}")
        return

    data = repo.db_get_best_seller_employee(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не знайдено.")
        return

    winner = data[0]
    revenue = float(winner['total_revenue'] or 0)

    print(f"\nКРАЩИЙ ПРОДАВЕЦЬ:")
    print(f"Співробітник: {winner['full_name']}")
    print(f"Кількість продажів: {winner['sales_count']}")
    print(f"Загальна сума продажів: {revenue:.2f} грн")
    print(f"=" * 60)

# Прибуток за період (Звіт №9)
def show_profit_report():
    print(f"\n{'=' * 60}\nПРИБУТОК ЗА ПЕРІОД\n{'=' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\nПомилка: {msg}")
        return

    data = repo.db_get_profit_report(start, end)

    if not data or data[0].get('total_revenue') is None:
        print(f"\nЗа період з {start} по {end} продажів не знайдено.")
        return

    report = data[0]

    rev = float(report.get('total_revenue') or 0)
    cost = float(report.get('total_cost') or 0)
    profit = float(report.get('net_profit') or 0)

    print(f"\nРезультати за період {start} — {end}:")
    print(f"{'-' * 45}")
    print(f"Загальна виручка:    {rev:>15.2f} грн")
    print(f"Собівартість книг:   {cost:>15.2f} грн")
    print(f"{'-' * 45}")
    print(f"ЧИСТИЙ ПРИБУТОК:     {profit:>15.2f} грн")
    print(f"{'=' * 60}")

    confirm = input("\nЗберегти звіт у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        filename = f"profit_report_{start}_{end}.csv"
        export_to_csv(data, filename)

# Топ автор (Звіт №10)
def show_most_sold_author_bonus_report():
    print(f"\n{'=' * 20}")
    print("НАЙПОПУЛЯРНІШИЙ АВТОР")
    print(f"{'=' * 20}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\nПомилка: {msg}")
        return

    data = repo.db_get_most_sold_author(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не знайдено.")
        return

    winner = data[0]
    author_name = winner['author'] if winner['author'] else "Невідомий автор"

    print(f"\nТОП АВТОР ПЕРІОДУ:")
    print(f"Автор: {author_name}")
    print(f"Кількість проданих примірників: {winner['total_sold']} шт.")
    print(f"{'=' * 45}")

# Топ жанр (Звіт №11)
def show_most_sold_genre_report():
    print(f"\n{'=' * 60}\nНАЙПОПУЛЯРНІШИЙ ЖАНР\n{'#' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\nПомилка: {msg}")
        return

    data = repo.db_get_most_sold_genre(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не знайдено.")
        return

    winner = data[0]
    genre_name = winner['genre'] if winner['genre'] else "Жанр не вказаний"

    print(f"\nТОП ЖАНР ПЕРІОДУ:")
    print(f"Жанр: {genre_name}")
    print(f"Продано примірників: {winner['total_sold']} шт.")
    print(f"{'=' * 60}")


# ГОЛОВНЕ МЕНЮ

def main_menu():
    while True:
        print(f"\n{'=' * 55}")
        print(f"{'СИСТЕМА УПРАВЛІННЯ КНИЖКОВИМ МАГАЗИНОМ':^55}")
        print(f"{'=' * 55}")
        print("\n1. АДМІНІСТРУВАННЯ")
        print("2. ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ")
        print("3. АНАЛІТИКА ТА ЗВІТНІСТЬ")
        print("\n0. ВИХІД")

        choice = input("\nОберіть розділ: ").strip()
        if choice == "1":
            data_management_menu()
        elif choice == "2":
            sales_operations_menu()
        elif choice == "3":
            analytics_reports_menu()
        elif choice == "0":
            break
        else:
            print("Невірний вибір. Будь ласка, введіть цифру від 0 до 3.")


# МЕНЮ 2 рівень АДМІНІСТРУВАННЯ

def data_management_menu():
    while True:
        print(f"\n{'-' * 45}")
        print("АДМІНІСТРАТОР")
        print(f"{'-' * 45}")
        print("1. Додати нову книгу")
        print("2. Редагувати дані книги")
        print("3. Видалити книгу з каталогу")
        print("4. Додати співробітника")
        print("5. Редагувати дані співробітника")
        print("6. Видалити співробітника (звільнення)")
        print("0. Головне меню")

        choice = input("\nОберіть дію: ").strip()

        if choice == "1": add_book_cli()
        elif choice == "2": edit_book_cli()
        elif choice == "3": delete_book_ui()
        elif choice == "4": add_employee_cli()
        elif choice == "5": edit_employee_cli()
        elif choice == "6": delete_employee_ui()
        elif choice == "0": break
        else:
            print("Невірний вибір. Будь ласка, введіть цифру від 0 до 6.")


# МЕНЮ 2 рівень ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ

def sales_operations_menu():
    while True:
        print(f"\n{'-' * 45}")
        print("ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ")
        print(f"{'-' * 45}")
        print("1. Оформити НОВИЙ ПРОДАЖ")
        print("2. Керування історією продажів (Редагування/Видалення)")
        print("3. Переглянути каталог книг")
        print("0. Головне меню")
        choice = input("\nОберіть дію: ").strip()
        if choice == "1": register_sale()
        elif choice == "2": manage_sales_crud()
        elif choice == "3": show_all_books_report()
        elif choice == "0": break

# Підменю №2 Керування історією продажів

def manage_sales_crud():
    while True:
        print(f"\n{'-' * 45}")
        print("КЕРУВАННЯ ІСТОРІЄЮ ПРОДАЖІВ")
        print(f"{'-' * 45}")
        print("1. Історія продажів")
        print("2. Коригування ціни")
        print("3. Видалення запису про продаж (повне)")
        print("0. Головне меню")

        choice = input("\nОберіть дію: ").strip()

        if choice == "1":
            show_full_sales_history_report()

        elif choice == "2":
            edit_sale_price_ui()

        elif choice == "3":
            delete_sale_ui()

        elif choice == "0":
            break

# # МЕНЮ 2 рівень  АНАЛІТИКА ТА ЗВІТНІСТЬ

def analytics_reports_menu():
    while True:
        print(f"\n{'-' * 45}")
        print("АНАЛІТИКА ТА ЗВІТНІСТЬ")
        print(f"{'-' * 45}")
        print(f"{'1. Штат співробітників':<30} {'7. Топ книга періоду':<30}")
        print(f"{'2. Каталог книг':<30} {'8. Найкращий продавець':<30}")
        print(f"{'3. Історія продажів':<30} {'9. Прибуток за період':<30}")
        print(f"{'4. Продажі за дату':<30} {'10. Топ автор':<30}")
        print(f"{'5. Продажі за період':<30} {'11. Топ жанр':<30}")
        print(f"{'6. Продажі по співробітнику':<30} {'0. Головне меню':<30}")

        choice = input("\nОберіть номер звіту або натисніть 0 для повернення в меню: ").strip()
        if choice == "0":
            break
        if choice not in [str(i) for i in range(1, 12)]:
            print("Невірний вибір. Будь ласка, введіть цифру від 0 до 11.")
            continue

        handle_report(choice)

        print("\n" + "-" * 45)
        input("Натисніть Enter, щоб повернутися до вибору звітів")

def handle_report(choice):
    if choice == "1":
        show_employees_report()

    elif choice == "2":
        show_all_books_report()

    elif choice == "3":
        show_full_sales_history_report()

    elif choice == "4":
        show_sales_by_date_report()

    elif choice == "5":
        show_sales_by_period_report()

    elif choice == "6":
        show_sales_by_employee_report()

    elif choice == "7":
        show_most_sold_book_report()

    elif choice == "8":
        show_best_employee_report()

    elif choice == "9":
        show_profit_report()

    elif choice == "10":
        show_most_sold_author_bonus_report()

    elif choice == "11":
        show_most_sold_genre_report()

    else:
        print("Невірний вибір. Будь ласка, введіть цифру від 0 до 11.")



