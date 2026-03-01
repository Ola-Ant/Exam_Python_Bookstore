from validators import validate_year, validate_email, validate_date, validate_date_range, validate_positive_number, validate_text
from services import export_to_csv
import repositories as repo
from models import books as books_table
from models import employees as emp_table

# Soft delete
def delete_item_soft(table, label):
    while True:
        val = input(f"Введіть {label} для видалення (або 0 для виходу): ").strip()
        if val == "0":
            print("\nДію скасовано")
            return
        if not val:
            print(f"{label} не може бути порожнім")
            continue
        if label == "ID" and not val.isdigit():
            print("ID має бути числом.")
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
        print(f"\n{label} '{val}' не знайдено в базі даних")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    confirm = input(f"\nВи впевнені, що хочете видалити {display_name}? (y/n): ").strip().lower()

    if confirm == 'y':
        col = table.c.isbn if label == "ISBN" else table.c.id
        repo.db_soft_delete(table, col, val)
        print(f"\n{label} успішно видалено (позначено як видалений)")
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
        print("Книгу з таким ISBN не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    if book.get('is_deleted'):
        print(f"\nКнигу «{book['title']}» архівовано. Продаж неможливий")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"Вибрано: «{book['title']}» (Ціна в довіднику: {book['retail_price']} грн)")

    while True:
        emp_id_in = input("ID продавця (співробітника): ").strip()
        if not emp_id_in:
            print("ID не може бути порожнім")
            continue
        if not emp_id_in.isdigit():
            print("ID має бути числом")
            continue

        emp_id = int(emp_id_in)
        emp = repo.db_get_employee_by_id(emp_id)
        if not emp:
            print(f"Співробітника з ID {emp_id} не знайдено.")
            continue

        if emp.get('is_deleted'):
            print(f"Співробітник {emp['full_name']} звільнений! Оберіть активного продавця")
            continue

        print(f"Продавець: {emp['full_name']}")
        break

    while True:
        qty_in = input("Кількість [1]: ").strip() or "1"
        ok_qty, msg_qty = validate_positive_number(qty_in, "Кількість")
        if not ok_qty:
            print(f"{msg_qty}")
            continue
        qty = int(float(qty_in))
        break

    while True:
        default_price = str(book['retail_price'])
        price_in = input(f"Ціна [{default_price} грн]: ").strip() or default_price
        ok_p, msg_p = validate_positive_number(price_in, "Ціна")
        if not ok_p:
            print(f"{msg_p}")
            continue
        price = float(price_in)
        break
    try:
        total = price * qty
        repo.db_add_sale(isbn, emp_id, price, qty)
        print(f"\n{'—' * 45}")
        print(f"\nОформлено продаж {qty} шт. на суму {total:.2f} грн")
        print(f"{'—' * 45}")
    except Exception as e:
        print(f"\n {e}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Історія продажів (Звіт 3)
def show_full_sales_history_report():
    data = repo.db_get_all_sales_history()
    if not data:
        print("Історія продажів порожня")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"\n{'ПОВНИЙ СПИСОК ПРОДАЖІВ':^65}")
    print(f"{'ID':<5} | {'Дата':<10} | {'Книга':<30} | {'Ціна':<8}")
    print("-" * 65)

    for r in data:
        d = str(r['sale_date'])[:10]
        t = r['title'][:30]
        print(f"{r['id']:<5} | {d:<10} | {t:<30} | {r['actual_price']:>8.2f}")

    total_revenue = sum(r['actual_price'] for r in data)
    print("-" * 65)
    print(f"{'ЗАГАЛЬНА ВИРУЧКА:':<48} | {total_revenue:>8.2f} грн")

    confirm = input("\nЗберегти дані у CSV-файл? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        filename = f"sales_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        export_to_csv(data, filename)

    input("\nНатисніть Enter, щоб повернутися до меню")

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
                print(f"Запису з ID {sid} не знайдено")
                continue

            print(f"Поточна ціна продажу №{sid}: {sale['actual_price']} грн")

            new_p_in = input("Введіть нову ціну: ").strip()

            is_ok, msg = validate_positive_number(new_p_in, "Ціна")
            if not is_ok:
                print(f"{msg}")
                continue

            new_p = float(new_p_in)

            repo.db_update_sale_price(sid, new_p)
            print(f"Ціну для продажу №{sid} успішно змінено на {new_p} грн")

            input("\nНатисніть Enter, щоб повернутися до меню")
            break

        except ValueError:
            print("ID має бути числом")

# Детальна інформація про продаж
def show_sale_details():
    print(f"\n{'=' * 45}\nДЕТАЛЬНА ІНФОРМАЦІЯ ПРО ПРОДАЖ\n{'=' * 45}")
    sale_id = input("Введіть ID продажу: ").strip()

    if not sale_id.isdigit():
        print("ID має бути числом")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    sale = repo.db_get_sale_details(int(sale_id))

    if not sale:
        print(f"Продаж з ID {sale_id} не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"\nЗапис №{sale['id']}")
    print(f"Дата: {sale['sale_date']}")
    print(f"Книга: {sale['book_title']}")
    print(f"Продавець: {sale['employee_name']}")
    print(f"Ціна продажу: {sale['actual_price']:.2f} грн")
    print(f"Собівартість: {sale['cost_price']:.2f} грн")
    print(f"Прибуток: {sale['profit']:.2f} грн")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Видалення продажу (повне)
def delete_sale_ui():
    print(f"\n{'=' * 10} ВИДАЛЕННЯ ПРОДАЖУ {'=' * 10}")
    while True:
        sid_in = input("ID запису для ПОВНОГО видалення (0 - повернутись в меню): ").strip()

        if sid_in == "0":
            return

        try:
            sid = int(sid_in)
            sale = repo.db_get_sale_by_id(sid)

            if not sale:
                print(f"Продаж №{sid} не знайдено")
                continue

            print(f"\n{'-' * 40}")
            print(f"ЗНАЙДЕНО ПРОДАЖ №{sid}")
            print(f"Книга: {sale['book_title']}")
            print(f"Продавець: {sale['employee_name']}")
            print(f"Сума: {sale['actual_price']} грн.")
            print(f"Дата: {sale['sale_date']}")
            print(f"{'-' * 40}")

            confirm = input(f"Ви впевнені, що хочете видалити його НАЗАВЖДИ? (y/n): ").strip().lower()

            if confirm == 'y':
                repo.db_delete_sale(sid)
                print(f"Запис №{sid} остаточно видалено з бази.")
                break
            else:
                print("Скасовано (запис залишається в базі)")
                break

        except ValueError:
            print("ID має бути цілим числом")

    input("\nНатисніть Enter, щоб повернутися до меню")

# КНИГИ

# Каталог книг (Звіт 2)
def show_all_books_report():
    print(f"\n{'=' * 65}\nКАТАЛОГ КНИГ\n{'=' * 65}")
    rows = repo.db_get_books()

    if not rows:
        print("Каталог порожній")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"{'ISBN':<13} | {'Назва книги':<30} | {'Ціна':<8}")
    print("-" * 65)
    for r in rows:
        print(f"{r['isbn']:<13} | {r['title'][:30]:<30} | {r['retail_price']:>8.2f} грн")
    print(f"\n{'-' * 65}")

    confirm = input("Зберегти дані у CSV-файл? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"books_catalog_{timestamp}.csv"
        export_to_csv(rows, filename)

    input("\nНатисніть Enter, щоб повернутися до меню")

# Додати нову книгу
def add_book_cli():
    print(f"\n{'=' * 45}\nРЕЄСТРАЦІЯ КНИГИ\n{'=' * 45}")

    while True:
        isbn = input("ISBN (або 0 для виходу): ").strip()
        if isbn == "0":
            print("\nРеєстрацію книги скасовано")
            return

        if not isbn:
            print("ISBN не може бути порожнім")
            continue

        existing_book = repo.db_get_book_details(isbn)

        if existing_book:
            if existing_book.get('is_deleted'):
                print(f"\nКнига «{existing_book['title']}» знаходиться в архіві.")
                confirm = input("Бажаєте відновити її в каталозі? (y/n): ").strip().lower()

                if confirm == 'y':
                    if repo.db_restore_entity(books_table, books_table.c.isbn, isbn):
                        print(f"Книгу «{existing_book['title']}» успішно відновлено")
                        input("\nНатисніть Enter, щоб повернутися до меню")
                        return
                    else:
                        return
                else:
                    print("Операцію скасовано. Введіть інший ISBN.")
                    continue
            else:
                print(f"Книга з ISBN {isbn} ВЖЕ Є в активному каталозі! Введіть інший")
                continue

        break

    while True:
        title = input("Назва: ").strip()
        author = input("Автор: ").strip()
        genre = input("Жанр: ").strip()
        if title and author and genre:
            break
        print("Усі текстові поля (Назва, Автор, Жанр) мають бути заповнені")

    while True:
        yr = input("Рік видання: ")
        ok, msg = validate_year(yr)
        if ok:
            year = int(yr)
            break
        print(f"{msg}")

    while True:
        cost_in = input("Собівартість (Cost): ").strip()
        ok_c, msg_c = validate_positive_number(cost_in, "Собівартість")
        if ok_c:
            cost = float(cost_in)
            break
        print(f"{msg_c}")

    while True:
        retail_in = input("Рекомендована ціна (Retail): ").strip()
        ok_r, msg_r = validate_positive_number(retail_in, "Ціна продажу")

        if ok_r:
            retail = float(retail_in)

            if retail <= cost:
                print(f"Рекомендована ціна ({retail}) має бути вищою за собівартість ({cost})")
                print("Будь ласка, введіть коректну ціну для каталогу")
                continue
            break
        else:
            print(f"{msg_r}")

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
        print("\nКнигу успішно збережено в базі")
    except Exception as e:
        print(f"\n{e}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Редагувати дані книги
def edit_book_cli():
    print(f"\n{'=' * 45}\nРЕДАГУВАННЯ ДАНИХ КНИГИ\n{'=' * 45}")
    isbn_to_find = input("Введіть ISBN книги для зміни: ").strip()

    book = repo.db_get_book_by_isbn(isbn_to_find)
    if not book:
        print("Книгу з таким ISBN не знайдено")
        return

    print(f"\nЗнайдено: «{book['title']}»")
    print("Введіть нові дані (або натисність Enter, щоб залишити без змін):")

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
        raw_cost = input(f"Нова собівартість [{book['cost_price']}]: ").strip()
        if not raw_cost:
            new_cost = book['cost_price']
            break

        ok, msg = validate_positive_number(raw_cost, "Собівартість")
        if ok:
            new_cost = float(raw_cost)
            break
        print(f"{msg}")

    while True:
        raw_retail = input(f"Нова ціна продажу [{book['retail_price']}]: ").strip()
        if not raw_retail:
            new_retail = book['retail_price']
        else:
            ok, msg = validate_positive_number(raw_retail, "Ціна продажу")
            if not ok:
                print(f"{msg}")
                continue
            new_retail = float(raw_retail)

        if new_retail < new_cost:
            print(f"Ціна ({new_retail}) не може бути нижчою за собівартість ({new_cost})!")
            continue
        break

    updated_info = {
        'title': new_title,
        'author': new_author,
        'genre': new_genre,
        'year_pub': new_year,
        'cost_price': new_cost,
        'retail_price': new_retail
    }

    try:
        repo.db_update_book(isbn_to_find, updated_info)
        print(f"\nДані успішно оновлено!")

    except Exception as e:
        print(f"\nНе вдалося оновити дані: {e}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Детальна інформація про книгу
def show_book_details():
    print(f"\n{'=' * 45}\nДЕТАЛЬНА ІНФОРМАЦІЯ ПРО КНИГУ\n{'=' * 45}")
    isbn = input("Введіть ISBN книги: ").strip()
    book = repo.db_get_book_details(isbn)

    if not book:
        print(f"Книгу з ISBN '{isbn}' не знайдено.")
    else:
        margin = book['retail_price'] - book['cost_price']

        print(f"\nНазва: {book['title']}")
        print(f"Автор: {book['author']}")
        print(f"Жанр: {book['genre']}")
        print(f"Рік: {book['year_pub']}")
        print(f"{'-' * 20}")
        print(f"Собівартість: {book['cost_price']} грн")
        print(f"Ціна за прайсом: {book['retail_price']} грн")
        print(f"Очікуваний прибуток: {margin} грн")
        print(f"{'-' * 20}")

        if book.get('is_deleted'):
            print("Книга в архіві (продаж неможливий)")
        else:
            print("Книга доступна для продажу")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Видалення книги (soft delete)
def delete_book_ui():
    print(f"\n{'=' * 45}\nВИДАЛЕННЯ КНИГИ (архівування)\n{'=' * 45}")

    all_books = repo.db_get_books()
    active_books = [b for b in all_books if not b.get('is_deleted')]

    if not active_books:
        print("\nВ базі немає книг для видалення")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"\n{'ISBN':<15} | {'Назва':<30}")
    print("-" * 45)
    for b in active_books:
        print(f"{b['isbn']:<15} | {b['title']:<30}")
    print("-" * 45)

    print("\nВиберіть ISBN книги зі списку вище, щоб перенести її в архів")
    delete_item_soft(books_table, "ISBN")

# СПІВРОБІТНИКИ

# Штат співробітників (Звіт 1)
def show_employees_report():
    print(f"\n{'=' * 105}\nСПИСОК СПІВРОБІТНИКІВ (ШТАТ)\n{'=' * 105}")
    active_employees = repo.db_get_active_employees()

    if not active_employees:
        print("Активних співробітників не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    header = f"{'ID':<4} | {'ПІБ':<25} | {'Посада':<25} | {'Телефон':<13} | {'Email':<25}"
    print(header)
    print("-" * 105)

    for e in active_employees:
        name = e['full_name']
        pos = e['position']
        tel = e['phone'] if e['phone'] else "-"
        mail = e['email'] if e['email'] else "-"
        print(f"{e['id']:<4} | {name:<25} | {pos:<25} | {tel:<13} | {mail:<25}")

    print(f"\n{'-' * 105}")
    print(f"Всього активних співробітників: {len(active_employees)}")

    confirm = input("Зберегти список співробітників у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"active_employees_{timestamp}.csv"
        export_to_csv(active_employees, filename)

    input("\nНатисніть Enter, щоб повернутися до меню")

# Додати співробітника
def add_employee_cli():
    print(f"\n{'=' * 45}\nНОВИЙ СПІВРОБІТНИК\n{'=' * 45}")

    while True:
        name = input("ПІБ (або 0 для виходу): ").strip()
        if name == "0": return
        is_valid, error = validate_text(name, "ПІБ")
        if not is_valid:
            print(error)
            continue

        pos = input("Посада: ").strip()
        is_valid, error = validate_text(pos, "Посада")
        if not is_valid:
            print(error)
            continue
        break

    ph = input("Введіть телефон (натисніть Enter, щоб пропустити): ").strip()
    if not ph:
        ph = None

    while True:
        em = input("Введіть Email (обов'язково): ").strip()
        if not em:
            print("Email є обов'язковим полем")
            continue

        is_ok, msg = validate_email(em)
        if not is_ok:
            print(f"{msg}")
            continue

        existing_emp = repo.db_get_employee_by_email(em)

        if existing_emp:
            if existing_emp.get('is_deleted'):
                print(f"\nСпівробітник із Email {em} ({existing_emp['full_name']}) є в архіві")
                confirm = input("Поновити його в штаті? (y/n): ").strip().lower()

                if confirm == 'y':
                    if repo.db_restore_entity(emp_table, emp_table.c.email, em):
                        print(f"Співробітника {existing_emp['full_name']} успішно поновлено")
                        input("\nНатисніть Enter, щоб повернутися до меню")
                        return
                    else:
                        return
                else:
                    print("Операцію скасовано. Введіть інший Email")
                    continue
            else:
                print(f"Співробітник з Email {em} вже в штаті")
                continue
        break

    emp_data = {
        'full_name': name,
        'position': pos,
        'phone': ph,
        'email': em
    }
    try:
        repo.db_add_employee(emp_data)
        print(f"\nСпівробітника {name} успішно зареєстровано в системі")
    except Exception as e:
        print(f"\n{e}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Редагувати дані співробітника
def edit_employee_cli():
    print(f"\n{'=' * 45}\nРЕДАГУВАННЯ ДАНИХ СПІВРОБІТНИКА\n{'=' * 45}")
    employees = repo.db_get_all_employees()
    if not employees:
        print("В базі немає зареєстрованих співробітників")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"{'ID':<5} | {'ПІБ':<25} | {'Посада'}")
    print("-" * 45)
    for e in employees:
        print(f"{e['id']:<5} | {e['full_name']:<25} | {e['position']}")
    print("-" * 45)

    emp_id_str = input("\nВведіть ID співробітника для зміни: ").strip()

    if not emp_id_str.isdigit():
        print("ID має бути числом")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    emp_id = int(emp_id_str)
    employee = repo.db_get_employee_by_id(emp_id)

    if not employee:
        print(f"Співробітника з ID {emp_id} не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"\nЗнайдено: {employee['full_name']}")
    print("Введіть нові дані (Enter, щоб залишити без змін):")

    while True:
        raw_name = input(f"ПІБ [{employee['full_name']}]: ").strip()
        if not raw_name:
            new_name = employee['full_name']
            break
        is_ok, msg = validate_text(raw_name, "ПІБ")
        if is_ok:
            new_name = raw_name
            break
        print(msg)

    while True:
        raw_pos = input(f"Посада [{employee['position']}]: ").strip()
        if not raw_pos:
            new_position = employee['position']
            break

        is_ok, msg = validate_text(raw_pos, "Посада")
        if is_ok:
            new_position = raw_pos
            break
        print(msg)

    current_phone = employee['phone'] if employee['phone'] else "—"
    phone_input = input(f"Телефон [{current_phone}] (введіть '0' для видалення): ").strip()

    if phone_input == '0':
        new_phone = None
    elif not phone_input:
        new_phone = employee['phone']
    else:
        new_phone = phone_input

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
    try:
        repo.db_update_employee(emp_id, updated_info)
        print(f"\nДані співробітника {new_name} успішно оновлено")
    except Exception as e:
        print(f"\n{e}")

    input("\nНатисніть Enter для повернення в меню")


def show_employee_details():
    print(f"\n{'=' * 45}\nКАРТКА СПІВРОБІТНИКА\n{'=' * 45}")
    emp_id = input("Введіть ID співробітника: ").strip()

    if not emp_id.isdigit():
        print("ID має бути числом")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    emp = repo.db_get_employee_details(int(emp_id))

    if not emp:
        print(f"Співробітника з ID {emp_id} не знайдено")
    else:
        status = "Звільнений / Архів" if emp.get('is_deleted') else "Активний"
        print(f"\nСтатус:  {status}")
        print(f"\nПІБ: {emp['full_name']}")
        print(f"Посада: {emp['position']}")
        print(f"Телефон: {emp['phone'] if emp['phone'] else '—'}")
        print(f"Email: {emp['email']}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Видалення співробітника (soft delete)
def delete_employee_ui():
    print(f"\n{'=' * 45}\nВИДАЛЕННЯ СПІВРОБІТНИКА (звільнення)\n{'=' * 45}")
    active_employees = repo.db_get_active_employees()
    if not active_employees:
        print("\nВ базі немає активних співробітників для видалення")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"\n{'ID':<5} | {'ПІБ':<25} | {'Посада'}")
    print("-" * 45)
    for e in active_employees:
        if not e.get('is_deleted', False):
            print(f"{e['id']:<5} | {e['full_name']:<25} | {e['position']}")
    print("-" * 45)

    print("\nВиберіть ID співробітника зі списку вище, щоб перенести його в архів (звільнити)")
    delete_item_soft(emp_table, "ID")

# ЗВІТИ

# Продажі на дату (Звіт №4)
def show_sales_by_date_report():
    print(f"\n{'=' * 65}\nПРОДАЖІ ЗА ОБРАНУ ДАТУ\n{'=' * 65}")

    target_date = input("Введіть дату (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date(target_date)
    if not is_valid:
        print(f"{msg}")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    data = repo.db_get_sales_by_date(target_date)

    if not data:
        print(f"За дату {target_date} продажів не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print(f"\n{'ID':<5} | {'Співробітник':<20} | {'Книга':<20} | {'Ціна':<8}")
    print("-" * 65)

    for r in data:
        price = float(r['actual_price'])
        print(f"{r['id']:<5} | {r['full_name'][:20]:<20} | {r['title'][:20]:<20} | {price:>8.2f}")

    total_day = sum(float(r['actual_price']) for r in data)
    print("-" * 65)
    print(f"{'РАЗОМ ЗА ДЕНЬ:':<48} | {total_day:>8.2f} грн")

    confirm = input("\nЗберегти звіт у CSV? (y/n): ").strip().lower()
    if confirm == 'y':
        filename = f"sales_day_{target_date.replace('-', '')}.csv"
        export_to_csv(data, filename)

    input("\nНатисніть Enter, щоб повернутися до меню")

# Продажі за період (Звіт №5)
def show_sales_by_period_report():
    print(f"\n{'=' * 75}\nЗВІТ: ПРОДАЖІ ЗА ПЕРІОД\n{'=' * 75}")

    start = input("Дата початку (РРРР-ММ-ДД): ").strip()
    end = input("Дата кінця (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"{msg}")
        input("\nНатисніть Enter для повернення до меню")
        return

    data = repo.db_get_sales_by_period(start, end)

    if not data:
        print(f"За період з {start} по {end} продажів не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
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

    input("\nНатисніть Enter, щоб повернутися до меню")

# Звіт по співробітнику (Звіт №6)
def show_sales_by_employee_report():
    print(f"\n{'=' * 75}\nЗВІТ: ПРОДАЖІ ПО СПІВРОБІТНИКУ\n{'=' * 75}")

    staff = repo.db_get_all_employees()
    if not staff:
        print("Штат порожній")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    print("Доступні співробітники:")
    print(f"{'ID':<4} | {'ПІБ':<30} | {'Посада':<20}")
    print("-" * 60)
    for s in staff:
        status = "Архів (не в штаті)" if s.get('is_deleted') else "Активний"
        print(f"{s['id']:<4} | {s['full_name']:<30} | {status:<12}")

    emp_id_in = input("\nВведіть ID співробітника для звіту (0 - повернення в меню): ").strip()
    if emp_id_in == "0": return
    if not emp_id_in.isdigit():
        print("ID має бути числом")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return
    emp_id = int(emp_id_in)

    target_emp = repo.db_get_employee_by_id(emp_id)
    if not target_emp:
        print(f"Співробітника з ID {emp_id} не зареєстровано в системі")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    data = repo.db_get_sales_by_employee(emp_id)
    if not data:
        print(f"У співробітника {target_emp['full_name']} ще немає зареєстрованих продажів")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    emp_name = target_emp['full_name']

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

    input("\nНатисніть Enter, щоб повернутися до меню")

# Топ книга періоду (Звіт №7)
def show_most_sold_book_report():
    print(f"\n{'=' * 60}\nНАЙБІЛЬШ ПРОДАВАНА КНИГА\n{'=' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\n{msg}")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    data = repo.db_get_most_sold_book(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не було")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    top_book = data[0]
    revenue = float(top_book['total_revenue'])

    print(f"\nБЕСТСЕЛЕР ПЕРІОДУ:")
    print(f"Назва: {top_book['title']}")
    print(f"Кількість продажів: {top_book['sales_count']} прим.")
    print(f"Загальна виручка: {revenue:,.2f} грн")
    print(f"=" * 60)

    input("\nНатисніть Enter, щоб повернутися до меню")

# Найкращий продавець (Звіт №8)
def show_best_employee_report():
    print(f"\n{'=' * 60}\nАНАЛІЗ: НАЙКРАЩИЙ ПРОДАВЕЦЬ ПЕРІОДУ\n{'=' * 60}")
    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\n{msg}")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    data = repo.db_get_best_seller_employee(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не знайдено.")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    winner = data[0]
    revenue = float(winner['total_revenue'] or 0)

    print(f"\nКРАЩИЙ ПРОДАВЕЦЬ:")
    print(f"Співробітник: {winner['full_name']}")
    print(f"Кількість продажів: {winner['sales_count']}")
    print(f"Загальна сума продажів: {revenue:.2f} грн")
    print(f"=" * 60)

    input("\nНатисніть Enter, щоб повернутися до меню")

# Прибуток за період (Звіт №9)
def show_profit_report():
    print(f"\n{'=' * 60}\nПРИБУТОК ЗА ПЕРІОД\n{'=' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\n{msg}")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    data = repo.db_get_profit_report(start, end)

    report = data[0]
    rev = float(report.get('total_revenue') or 0)
    cost = float(report.get('total_cost') or 0)
    profit = float(report.get('net_profit') or 0)

    if rev == 0:
        print(f"\nЗа період з {start} по {end} продажів не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

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

    input("\nНатисніть Enter, щоб повернутися до меню")

# Топ автор (Звіт №10)
def show_most_sold_author_bonus_report():
    print(f"\n{'=' * 60}")
    print("НАЙПОПУЛЯРНІШИЙ АВТОР")
    print(f"{'=' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\n{msg}")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    data = repo.db_get_most_sold_author(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не знайдено")
        input("\nНатисніть Enter, щоб повернутися до меню")
        return

    winner = data[0]
    author_name = winner['author'] if winner['author'] else "Невідомий автор"

    print(f"\nТОП АВТОР ПЕРІОДУ:")
    print(f"Автор: {author_name}")
    print(f"Кількість проданих примірників: {winner['total_sold']} шт.")
    print(f"{'=' * 60}")

    input("\nНатисніть Enter, щоб повернутися до меню")

# Топ жанр (Звіт №11)
def show_most_sold_genre_report():
    print(f"\n{'=' * 60}\nНАЙПОПУЛЯРНІШИЙ ЖАНР\n{'=' * 60}")

    start = input("Початок періоду (РРРР-ММ-ДД): ").strip()
    end = input("Кінець періоду (РРРР-ММ-ДД): ").strip()

    is_valid, msg = validate_date_range(start, end)
    if not is_valid:
        print(f"\n{msg}")
        return

    data = repo.db_get_most_sold_genre(start, end)
    if not data:
        print(f"За період з {start} по {end} продажів не знайдено")
        return

    winner = data[0]
    genre_name = winner['genre'] if winner['genre'] else "Жанр не вказаний"

    print(f"\nТОП ЖАНР ПЕРІОДУ:")
    print(f"Жанр: {genre_name}")
    print(f"Продано примірників: {winner['total_sold']} шт.")
    print(f"{'=' * 60}")

    input("\nНатисніть Enter, щоб повернутися до меню")


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
        print("3. Переглянути деталі про книгу")
        print("4. Видалити книгу з каталогу")
        print("5. Додати співробітника")
        print("6. Редагувати дані співробітника")
        print("7. Детальна інформація про співробітника (Картка співробітника)")
        print("8. Видалити співробітника (звільнення)")
        print("0. Головне меню")

        choice = input("\nОберіть дію: ").strip()

        if choice == "1": add_book_cli()
        elif choice == "2": edit_book_cli()
        elif choice == "3": show_book_details()
        elif choice == "4": delete_book_ui()
        elif choice == "5": add_employee_cli()
        elif choice == "6": edit_employee_cli()
        elif choice == "7": show_employee_details()
        elif choice == "8": delete_employee_ui()
        elif choice == "0": break
        else:
            print("Невірний вибір. Будь ласка, введіть цифру від 0 до 8.")
            input("Натисніть Enter, щоб зробити вибір")


# МЕНЮ 2 рівень ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ

def sales_operations_menu():
    while True:
        print(f"\n{'-' * 45}")
        print("ОПЕРАЦІЙНА ДІЯЛЬНІСТЬ")
        print(f"{'-' * 45}")
        print("1. Оформити НОВИЙ ПРОДАЖ")
        print("2. Переглянути деталі продажу")
        print("3. Керування історією продажів (Редагування/Видалення)")
        print("4. Переглянути каталог книг")
        print("0. Головне меню")
        choice = input("\nОберіть дію: ").strip()
        if choice == "1": register_sale()
        elif choice == "2": show_sale_details()
        elif choice == "3": manage_sales_crud()
        elif choice == "4": show_all_books_report()
        elif choice == "0": break
        else:
            print("Невірний вибір. Будь ласка, введіть цифру від 0 до 4.")
            input("Натисніть Enter, щоб зробити вибір")

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
        else:
            print("\nНевірний вибір. Будь ласка, введіть цифру від 0 до 3.")
            input("Натисніть Enter, щоб зробити вибір")

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



