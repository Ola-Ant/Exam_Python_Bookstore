import re
from datetime import datetime

def validate_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Некоректний формат Email (коректний формат: name@gmail.com)."
    return True, ""

def validate_year(year_str):
    try:
        year = int(year_str)
        current_year = datetime.now().year
        if 1850 <= year <= current_year:
            return True, ""
        return False, f"Рік має бути в діапазоні від 1850 до {current_year}."
    except ValueError:
        return False, "Рік має бути цілим числом."

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, ""
    except ValueError:
        return False, "Неправильний формат дати. Використовуйте РРРР-ММ-ДД (наприклад: 2025-02-15)."


def validate_date_range(start_str, end_str):
    ok_start, msg_start = validate_date(start_str)
    ok_end, msg_end = validate_date(end_str)

    if not ok_start or not ok_end:
        return False, f"Некоректний формат дат. Початок: [{start_str}], Кінець: [{end_str}]. Використовуйте РРРР-ММ-ДД."

    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()

    if start > end:
        return False, f"Дата початку ({start_str}) не може бути пізніше за дату кінця ({end_str})."

    if end > datetime.now().date():
        return False, f"Дата кінця ({end_str}) не може бути в майбутньому."

    return True, ""