import psycopg2
from config import host, user, password, db_name
import time

# Функция для получения соединения с базой данных
def get_connection():
    retries = 5
    delay = 5  # Задержка в секундах
    for i in range(retries):
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            return connection
        except Exception as ex:
            print(f"[INFO] Попытка {i + 1} из {retries}: Ошибка подключения к базе данных: {ex}")
            time.sleep(delay)
    return None

# Функция для создания таблицы (если она не существует)
def create_table():
    connection = get_connection()
    if connection:
        with connection.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS flats(
                id SERIAL PRIMARY KEY,
                city VARCHAR(50),
                address VARCHAR(50),
                description VARCHAR(200),
                photo VARCHAR(200),
                contacts VARCHAR(200),
                price INTEGER
                )"""
            )
            connection.commit()
        connection.close()

# Функция для добавления квартиры
def insert_flat(city, address, description, photo, contacts, price):
    connection = get_connection()
    if connection:
        with connection.cursor() as cur:
            cur.execute(
                """INSERT INTO flats (city, address, description, photo, contacts, price) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (city, address, description, photo, contacts, price)
            )
            connection.commit()
        connection.close()

# Функция для поиска квартир с ценой больше указанной
def check_by_cost_more(cost):
    connection = get_connection()
    if connection:
        with connection.cursor() as cur:
            cur.execute(
                """SELECT city, address, description, photo, contacts, price 
                FROM flats WHERE price > %s""",
                (cost,)
            )
            flats = cur.fetchall()
        if flats:
            connection.close()
            return flats
        else:
            connection.close()
            return 0

# Функция для поиска квартир с ценой меньше указанной
def check_by_cost_less(cost):
    connection = get_connection()
    if connection:
        with connection.cursor() as cur:
            cur.execute(
                """SELECT city, address, description, photo, contacts, price 
                FROM flats WHERE price < %s""",
                (cost,)
            )
            flats = cur.fetchall()
        if flats:
            connection.close()
            return flats
        else:
            connection.close()
            return 0

def check_by_city(city):
    connection = get_connection()
    create_table()
    if connection:
        with connection.cursor() as cur:
            cur.execute(
                """SELECT city, address, description, photo, contacts, price 
                FROM flats WHERE city = %s""",
                (city.lower(),)
            )
            flats = cur.fetchall()
            if flats:
                connection.close()
                return flats
            else:
                connection.close()
                return 0


