import sqlite3
from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
import random

# Функция для подключения к локальному SQL Server
def connect_to_sql_server():
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=MSI-H620-PRO\\MSSQLSERVER01;"  # Указываем имя твоего сервера
            "DATABASE=CinemaDB;"  # Название твоей базы данных
            "Trusted_Connection=yes;"  # Использует Windows-аутентификацию
        )
        return conn
    except Exception as e:
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к SQL Server: {e}")
        return None

# Функция для создание базы данных если нет подключения к SSQL
def connect_to_sqlite():
    try:
        conn = sqlite3.connect('cinema_tickets.db')
        return conn
    except Exception as e:
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к SQLite: {e}")
        return None

# Создание таблиц (если они не существуют)
def create_tables():
    conn = connect_to_sqlite()
    if conn:
        cursor = conn.cursor()
        # Таблица фильмов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                duration TEXT NOT NULL,
                genre TEXT NOT NULL
            )
        ''')
        # Таблица сеансов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id INTEGER NOT NULL,
                show_time TEXT NOT NULL,
                FOREIGN KEY (movie_id) REFERENCES movies(id)
            )
        ''')
        # Таблица билетов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                seat_number TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                order_number TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        conn.commit()
        conn.close()

# Добавление тестовых данных
def add_sample_data():
    conn = connect_to_sqlite()
    if conn:
        cursor = conn.cursor()
        # Проверяем, есть ли уже данные в таблице movies
        cursor.execute("SELECT COUNT(*) FROM movies")
        if cursor.fetchone()[0] == 0:
            # Добавляем фильмы
            movies = [
                ("Криминальное чтиво", "2h 34m", "Криминал"),
                ("Крестный отец", "2h 55m", "Драма"),
                ("Бойцовский клуб", "2h 19m", "Триллер"),
                ("Интерстеллар", "2h 49m", "Фантастика"),
                ("Матрица", "2h 16m", "Фантастика")
            ]
            cursor.executemany("INSERT INTO movies (title, duration, genre) VALUES (?, ?, ?)", movies)
            # Добавляем сеансы
            cursor.execute("SELECT id FROM movies WHERE title='Криминальное чтиво'")
            movie_id = cursor.fetchone()[0]
            sessions = [
                (movie_id, "2025-04-25 18:00"),
                (movie_id, "2025-04-25 21:00")
            ]
            cursor.executemany("INSERT INTO sessions (movie_id, show_time) VALUES (?, ?)", sessions)
            # Добавляем сеансы для других фильмов
            cursor.execute("SELECT id FROM movies WHERE title='Крестный отец'")
            movie_id = cursor.fetchone()[0]
            sessions = [
                (movie_id, "2025-04-26 19:00"),
                (movie_id, "2025-04-26 22:00")
            ]
            cursor.executemany("INSERT INTO sessions (movie_id, show_time) VALUES (?, ?)", sessions)
            cursor.execute("SELECT id FROM movies WHERE title='Бойцовский клуб'")
            movie_id = cursor.fetchone()[0]
            sessions = [
                (movie_id, "2025-04-27 20:00"),
                (movie_id, "2025-04-27 23:00")
            ]
            cursor.executemany("INSERT INTO sessions (movie_id, show_time) VALUES (?, ?)", sessions)
            conn.commit()
        conn.close()

# Загрузка фильмов и сеансов
def load_movies_and_sessions():
    conn = connect_to_sqlite()
    if conn:
        cursor = conn.cursor()
        # Загрузка фильмов
        cursor.execute("SELECT * FROM movies")
        movies = cursor.fetchall()
        # Загрузка сеансов
        cursor.execute("SELECT s.id, m.title, s.show_time FROM sessions s JOIN movies m ON s.movie_id = m.id")
        sessions = cursor.fetchall()
        conn.close()
        return movies, sessions
    return [], []

# Просмотр списка фильмов
def view_movies():
    movies, _ = load_movies_and_sessions()
    for row in tree_movies.get_children():
        tree_movies.delete(row)
    for movie in movies:
        tree_movies.insert("", END, values=movie)

# Просмотр расписания сеансов
def view_sessions():
    _, sessions = load_movies_and_sessions()
    for row in tree_sessions.get_children():
        tree_sessions.delete(row)
    for session in sessions:
        tree_sessions.insert("", END, values=session)

# Бронирование билета
def book_ticket():
    session_id = entry_session_id.get()
    seat_number = entry_seat.get()
    customer_name = entry_customer.get()

    if session_id and seat_number and customer_name:
        order_number = f"ORDER-{random.randint(1000, 9999)}"  # Генерация номера заказа
        conn = connect_to_sqlite()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tickets (session_id, seat_number, customer_name, order_number) VALUES (?, ?, ?, ?)",
                          (session_id, seat_number, customer_name, order_number))
            conn.commit()
            conn.close()
            messagebox.showinfo("Успех", f"Билет успешно забронирован! Номер заказа: {order_number}")
            clear_entries()
            view_tickets()
    else:
        messagebox.showwarning("Ошибка", "Все поля должны быть заполнены!")

# Отмена бронирования
def cancel_booking():
    selected_item = tree_tickets.selection()
    if selected_item:
        ticket_id = tree_tickets.item(selected_item)['values'][0]
        conn = connect_to_sqlite()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tickets SET status='cancelled' WHERE id=?", (ticket_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Успех", "Бронирование успешно отменено!")
            view_tickets()
    else:
        messagebox.showwarning("Ошибка", "Выберите билет для отмены!")

# Просмотр истории бронирований
def view_tickets():
    for row in tree_tickets.get_children():
        tree_tickets.delete(row)
    conn = connect_to_sqlite()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, m.title, s.show_time, t.seat_number, t.customer_name, t.order_number, t.status
            FROM tickets t
            JOIN sessions s ON t.session_id = s.id
            JOIN movies m ON s.movie_id = m.id
            WHERE t.status = 'active'
        """)
        rows = cursor.fetchall()
        for row in rows:
            tree_tickets.insert("", END, values=row)
        conn.close()

# Очистка полей ввода
def clear_entries():
    entry_session_id.delete(0, END)
    entry_seat.delete(0, END)
    entry_customer.delete(0, END)

# Окно авторизации
def login():
    username = entry_username.get()
    password = entry_password.get()

    if username == "admin" and password == "admin":
        login_window.destroy()  # Закрываем окно авторизации
        main_window.deiconify()  # Открываем основное окно
    else:
        messagebox.showerror("Ошибка", "Неверный логин или пароль!")

# Основное окно программы
main_window = Tk()
main_window.title("Система автоматизации обработки билетов онлайн-кинотеатра")
main_window.geometry("1200x800")
main_window.configure(bg="#E1F5FE")  # Светло-синий фон
main_window.withdraw()  # Скрываем основное окно до авторизации

# Вкладки для фильмов, сеансов и билетов
notebook = ttk.Notebook(main_window)
notebook.pack(fill=BOTH, expand=True)

# Вкладка "Фильмы"
frame_movies = Frame(notebook, bg="#E1F5FE")
notebook.add(frame_movies, text="Фильмы")

tree_movies = ttk.Treeview(frame_movies, columns=("id", "title", "duration", "genre"), show="headings")
tree_movies.heading("id", text="ID")
tree_movies.heading("title", text="Название фильма")
tree_movies.heading("duration", text="Длительность")
tree_movies.heading("genre", text="Жанр")
tree_movies.pack(fill=BOTH, expand=True, padx=10, pady=10)

Button(frame_movies, text="Обновить список фильмов", command=view_movies, bg="#005BB5", fg="white", font=("Arial", 12)).pack(pady=10)

# Вкладка "Сеансы"
frame_sessions = Frame(notebook, bg="#E1F5FE")
notebook.add(frame_sessions, text="Сеансы")

tree_sessions = ttk.Treeview(frame_sessions, columns=("id", "title", "show_time"), show="headings")
tree_sessions.heading("id", text="ID")
tree_sessions.heading("title", text="Название фильма")
tree_sessions.heading("show_time", text="Время показа")
tree_sessions.pack(fill=BOTH, expand=True, padx=10, pady=10)

Button(frame_sessions, text="Обновить расписание", command=view_sessions, bg="#005BB5", fg="white", font=("Arial", 12)).pack(pady=10)

# Вкладка "Бронирование"
frame_booking = Frame(notebook, bg="#E1F5FE")
notebook.add(frame_booking, text="Бронирование")

Label(frame_booking, text="ID сеанса:", bg="#E1F5FE", fg="#005BB5", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
entry_session_id = Entry(frame_booking, font=("Arial", 12))
entry_session_id.grid(row=0, column=1, padx=10, pady=10)

Label(frame_booking, text="Номер места:", bg="#E1F5FE", fg="#005BB5", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10)
entry_seat = Entry(frame_booking, font=("Arial", 12))
entry_seat.grid(row=1, column=1, padx=10, pady=10)

Label(frame_booking, text="Имя клиента:", bg="#E1F5FE", fg="#005BB5", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=10)
entry_customer = Entry(frame_booking, font=("Arial", 12))
entry_customer.grid(row=2, column=1, padx=10, pady=10)

Button(frame_booking, text="Забронировать билет", command=book_ticket, bg="#005BB5", fg="white", font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=10)
Button(frame_booking, text="Отменить бронирование", command=cancel_booking, bg="#005BB5", fg="white", font=("Arial", 12)).grid(row=3, column=1, padx=10, pady=10)

# Вкладка "История бронирований"
frame_history = Frame(notebook, bg="#E1F5FE")
notebook.add(frame_history, text="История бронирований")

tree_tickets = ttk.Treeview(frame_history, columns=("id", "title", "show_time", "seat_number", "customer_name", "order_number", "status"), show="headings")
tree_tickets.heading("id", text="ID")
tree_tickets.heading("title", text="Название фильма")
tree_tickets.heading("show_time", text="Время показа")
tree_tickets.heading("seat_number", text="Номер места")
tree_tickets.heading("customer_name", text="Имя клиента")
tree_tickets.heading("order_number", text="Номер заказа")
tree_tickets.heading("status", text="Статус")
tree_tickets.pack(fill=BOTH, expand=True, padx=10, pady=10)

Button(frame_history, text="Обновить историю", command=view_tickets, bg="#005BB5", fg="white", font=("Arial", 12)).pack(pady=10)

# Инициализация базы данных и загрузка данных
create_tables()
add_sample_data()  # Добавляем тестовые данные
view_movies()
view_sessions()
view_tickets()

# Окно авторизации
login_window = Tk()
login_window.title("Авторизация")
login_window.geometry("500x300")
login_window.configure(bg="#0078D7")  # Синий фон

Label(login_window, text="Логин:", bg="#0078D7", fg="white", font=("Arial", 12)).pack(pady=10)
entry_username = Entry(login_window, font=("Arial", 12))
entry_username.pack(pady=5)

Label(login_window, text="Пароль:", bg="#0078D7", fg="white", font=("Arial", 12)).pack(pady=10)
entry_password = Entry(login_window, show="*", font=("Arial", 12))
entry_password.pack(pady=5)

Button(login_window, text="Войти", command=login, bg="#005BB5", fg="white", font=("Arial", 12)).pack(pady=20)

# Запуск основного цикла
login_window.mainloop()
