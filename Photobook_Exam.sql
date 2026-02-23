-- 1. База співробітників магазину фотокниг
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR NOT NULL CONSTRAINT check_name_empty CHECK (full_name <> ''),
    position VARCHAR NOT NULL 
        DEFAULT 'Продавець' -- за замовчуванням для швидкості в базі буде продавець
        CONSTRAINT check_position_empty CHECK (position <> ''), 
    phone VARCHAR(20),
    email VARCHAR(100) NOT NULL UNIQUE CONSTRAINT check_email_empty CHECK (email <> ''),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- 2. База фотокниг
CREATE TABLE IF NOT EXISTS books (
    isbn VARCHAR(20) PRIMARY KEY,
    title VARCHAR(255) NOT NULL CONSTRAINT check_title_empty CHECK (title <> ''),
    year_pub INTEGER NOT NULL CONSTRAINT check_year CHECK (year_pub > 1800),
    author VARCHAR(255) NOT NULL CONSTRAINT check_author_empty CHECK (author <> ''),
    genre VARCHAR(100) NOT NULL CONSTRAINT check_genre_empty CHECK (genre <> ''),
    cost_price DECIMAL(10, 2) NOT NULL CONSTRAINT check_cost_positive CHECK (cost_price > 0),
    retail_price DECIMAL(10, 2) NOT NULL CONSTRAINT check_retail_positive CHECK (retail_price > 0),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- 3. База продажів
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    book_isbn VARCHAR(20) NOT NULL,
    sale_date DATE NOT NULL DEFAULT CURRENT_DATE, -- за замовчуванням ставимо сьогоднішню дату
    actual_price DECIMAL(10, 2) NOT NULL 
        CONSTRAINT check_actual_price_positive CHECK (actual_price > 0),
		
    -- Обмеження створення продажу, якщо співробітника не існує (вимога іспиту п.2 функціональність)
    CONSTRAINT fk_sales_employee 
        FOREIGN KEY (employee_id) 
        REFERENCES employees(id) 
        ON DELETE CASCADE,
        
    -- Обмеження створення продажу, якщо книги з таким ISBN не існує (вимога іспиту п.2 функціональність)
    CONSTRAINT fk_sales_book 
        FOREIGN KEY (book_isbn) 
        REFERENCES books(isbn) 
        ON DELETE CASCADE
);

INSERT INTO books (isbn, title, year_pub, author, genre, cost_price, retail_price) VALUES
-- Історія та Теорія
('978-0500544419', 'Magnum Contact Sheets', 2014, 'Kristen Lubben', 'History', 1800.00, 3600.00),
('978-0500410607', 'The Photobook: A History Vol. 1', 2004, 'Martin Parr', 'History', 1450.00, 2900.00),
('978-0810937160', 'The History of Photography', 1982, 'Beaumont Newhall', 'History', 800.00, 1650.00),
('978-0374522933', 'On Photography', 1977, 'Susan Sontag', 'Theory', 350.00, 720.00),
('978-0374532338', 'Camera Lucida', 1980, 'Roland Barthes', 'Theory', 320.00, 680.00),

-- Монографії та Арт-буки
('978-0500286424', 'The Decisive Moment', 2014, 'Henri Cartier-Bresson', 'Monograph', 2200.00, 4800.00),
('978-1597115117', 'The Americans', 1958, 'Robert Frank', 'Art', 1000.00, 2200.00),
('978-3836521111', 'Helmut Newton. Sumo', 2009, 'Helmut Newton', 'Fashion', 3000.00, 6500.00),
('978-0893817441', 'The Ballad of Sexual Dependency', 1986, 'Nan Goldin', 'Documentary', 1200.00, 2600.00),
('978-3869305318', 'I have a dream', 2012, 'Sebastiao Salgado', 'Documentary', 2000.00, 4100.00),
('978-1597112093', 'The Places We Live', 2008, 'Jonas Bendiksen', 'Documentary', 900.00, 1950.00),
('978-1597112529', 'Exiles', 2014, 'Josef Koudelka', 'Art', 1100.00, 2450.00),
('978-0500543336', 'In Flagrante Two', 2016, 'Chris Killip', 'Social', 1300.00, 2800.00),
('978-1597114790', 'Uncommon Places', 2015, 'Stephen Shore', 'Art', 1100.00, 2300.00),
('978-1597111430', 'The Portfolios', 2010, 'Ansel Adams', 'Landscape', 1500.00, 3100.00),

-- Технічна література
('978-1597113397', 'On-Camera Flash Techniques', 2015, 'Neil van Niekerk', 'Educational', 550.00, 1150.00),
('978-4861009111', 'Minolta Autocord Guide', 2015, 'Japanese Photo Society', 'Technical', 450.00, 980.00),
('978-1681985169', 'The Soul of the Camera', 2017, 'David duChemin', 'Educational', 600.00, 1250.00),
('978-0321934949', 'The Visual Toolbox', 2014, 'David duChemin', 'Educational', 500.00, 1050.00),
('978-1681985725', 'The Film Photography Handbook', 2019, 'Chris Marquardt', 'Technical', 650.00, 1400.00),

-- Вулична фотографія (Street)
('978-0500411123', 'Street Photography Now', 2010, 'Sophie Howarth', 'Street', 900.00, 1900.00),
('978-0500544471', 'The World Atlas of Street Photography', 2014, 'Jackie Higgins', 'Street', 1000.00, 2100.00),
('978-0500543473', 'Street World', 2007, 'Roger Gastman', 'Street', 750.00, 1600.00),
('978-0500541333', 'Bystander: A History of Street Photography', 2001, 'Joel Meyerowitz', 'Street', 850.00, 1850.00),

-- Енциклопедії та Сучасне
('978-0241433333', 'The Photography Book', 2021, 'Phaidon Editors', 'Encyclopedia', 700.00, 1500.00),
('978-0500293539', 'Chronicle of a Method', 2017, 'Oscar Barnack', 'Technical', 1200.00, 2550.00),
('978-0500542331', 'Portrait of a City', 2010, 'Taschen', 'Art', 1800.00, 3800.00),
('978-0500292222', 'The Art of Photography', 2010, 'Bruce Barnbaum', 'Educational', 800.00, 1750.00),
('978-1597113113', 'Aperture Magazine Anthology', 2012, 'Aperture', 'History', 1100.00, 2300.00),
('978-0500541111', 'Contact Sheet 190', 2016, 'Light Work', 'Documentary', 550.00, 1200.00),

-- Японська фотографія
('978-1597110518', 'Provoke', 2016, 'Diane Dufour', 'Art', 1200.00, 2600.00),
('978-4861009444', 'Sentimental Journey', 1971, 'Nobuyoshi Araki', 'Monograph', 1500.00, 3100.00),
('978-0500544563', 'Japan: A Photo History', 2004, 'Anne Tucker', 'History', 1000.00, 2100.00),

-- Мода та Портрети
('978-0500544464', 'Vogue: The Covers', 2017, 'Dodie Kazanjian', 'Fashion', 750.00, 1600.00),
('978-0375505096', 'Avedon Advertising', 2019, 'Richard Avedon', 'Fashion', 1800.00, 3900.00),
('978-0810906631', 'Portraits', 1976, 'Richard Avedon', 'Art', 1600.00, 3500.00),
('978-3836544412', 'Leibovitz: Portraits', 2014, 'Annie Leibovitz', 'Art', 2100.00, 4500.00),

-- Архітектура
('978-3791381411', 'Constructing Worlds', 2014, 'Iwan Baan', 'Architecture', 1000.00, 2200.00),
('978-3775739812', 'Julius Shulman: Modernism', 2015, 'Pierluigi Serraino', 'Architecture', 1400.00, 3000.00),

-- Сучасна та Документальна
('978-1597113182', 'The Last Testament', 2017, 'Jonas Bendiksen', 'Documentary', 1000.00, 2100.00),
('978-3958293311', 'Imperial Courts', 2015, 'Dana Lixenberg', 'Documentary', 1200.00, 2600.00),
('978-1597114110', 'Sleeping by the Mississippi', 2017, 'Alec Soth', 'Art', 1100.00, 2400.00),
('978-1597114943', 'Songbook', 2015, 'Alec Soth', 'Art', 1050.00, 2250.00),

-- Техніка та Процес
('978-0817439392', 'Creative Eye', 2010, 'Bryan Peterson', 'Educational', 450.00, 950.00),
('978-1681981414', 'The Negative', 1981, 'Ansel Adams', 'Technical', 600.00, 1350.00),
('978-1681981445', 'The Print', 1983, 'Ansel Adams', 'Technical', 600.00, 1350.00),
('978-1681981476', 'The Camera', 1980, 'Ansel Adams', 'Technical', 600.00, 1350.00),

-- Змішані
('978-0500544518', 'Photographers Sketchbooks', 2014, 'Stephen McLaren', 'History', 900.00, 1950.00),
('978-0500292211', 'Color in Photography', 2017, 'Bryan Peterson', 'Educational', 500.00, 1100.00),
('978-1597112000', 'Aperture Conversations', 2018, 'Melissa Harris', 'Theory', 800.00, 1750.00);

INSERT INTO employees (full_name, position, phone, email) VALUES
('Олександр Коваль', 'Старший продавець', '+380501112233', 'koval@photo.ua'),
('Марія Ткаченко', 'Продавець-консультант', '+380634445566', 'mariatkach@photo.ua'),
('Дмитро Петренко', 'Менеджер магазину', '+380957778899', 'petrenko@photo.ua'),
('Анна Сидоренко', 'Продавець', '+380671112233', 'annasidor@photo.ua'),
('Ігор Клименко', 'Продавець', '+380503334455', 'igor@photo.ua'),
('Олена Бондар', 'Консультант', '+380635556677', 'olena@photo.ua'),
('Сергій Мороз', 'Продавець', '+380971110022', 'sergmoroz@photo.ua'),
('Юлія Кравченко', 'Продавець', '+380508889900', 'yuliakravch@photo.ua'),
('Андрій Швець', 'Молодший продавець', '+380631234567', 'shvets@photo.ua'),
('Наталія Орлова', 'Адміністратор', '+380950001122', 'nataliaorlova@photo.ua');

-- 3. Створюю базу продажів
INSERT INTO sales (employee_id, book_isbn, actual_price, sale_date)
SELECT 
    (ARRAY[1,2,4,5,7,9,10])[floor(random()*7)+1], 
    (ARRAY['978-1681985725', '978-0374522933', '978-1681981414', '978-1597113397', '978-0241433333'])[floor(random()*5)+1], 
    700.00 + (random()*600), 
    '2026-01-01'::date + (floor(random()*30) || ' days')::interval
FROM generate_series(1, 50);

INSERT INTO sales (employee_id, book_isbn, actual_price, sale_date)
SELECT 
    (ARRAY[1,2,4,8,8,8])[floor(random()*6)+1], 
    (ARRAY['978-3836521111', '978-3836544412', '978-0500286424', '978-0375505096', '978-0810906631'])[floor(random()*5)+1], 
    3800.00 + (random()*2800), 
    '2026-02-01'::date + (floor(random()*27) || ' days')::interval
FROM generate_series(1, 80);

INSERT INTO sales (employee_id, book_isbn, actual_price, sale_date)
SELECT 
    (ARRAY[1,2,4,5,7,8,9,10])[floor(random()*8)+1], 
    (ARRAY['978-1597115117', '978-1597115117', '978-0500411123', '978-0500544471', '978-1597114790'])[floor(random()*5)+1], 
    1900.00 + (random()*1200), 
    '2026-03-01'::date + (floor(random()*20) || ' days')::interval
FROM generate_series(1, 100);

SELECT count(*) FROM sales;

