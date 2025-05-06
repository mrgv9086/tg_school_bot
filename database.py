import sqlite3
from datetime import datetime
import threading


class Database:
    CREATE_RECEIPT_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spoon_id INTEGER NOT NULL UNIQUE,
            image_url TEXT NOT NULL,
            title TEXT NOT NULL,
            ingridients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            nutritional TEXT NOT NULL,
            spoon_url TEXT NOT NULL
        )
    """

    CREATE_USER_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    """

    CREATE_HISTORY_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dish_name TEXT,
            recipe_title TEXT,
            timestamp TEXT
        )
    """

    CREATE_FAVOURITE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            receipt_id INTEGER NOT NULL,
            UNIQUE(user_id, receipt_id)
        )
    """

    def __init__(self, db_path="recipes_history.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.initialize_db()

    def get_connection(self):
        """Получаем соединение для текущего потока"""
        if not hasattr(self.local, "connection") or self.local.connection is None:
            self.local.connection = sqlite3.connect(self.db_path)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection

    def initialize_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(self.CREATE_RECEIPT_TABLE_SQL)
        cursor.execute(self.CREATE_USER_TABLE_SQL)
        cursor.execute(self.CREATE_HISTORY_TABLE_SQL)
        cursor.execute(self.CREATE_FAVOURITE_TABLE_SQL)

        conn.commit()

    def add_receipt(self, spoon_id, image_url, title, ingridients, instructions, nutritional, spoon_url):
        conn = self.get_connection()
        conn.execute("""
            INSERT OR IGNORE INTO receipts (spoon_id, image_url, title, ingridients, instructions, nutritional, spoon_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (spoon_id, image_url, title, ingridients, instructions, nutritional, spoon_url))
        conn.commit()

    def add_user(self, user_id, username):
        conn = self.get_connection()
        conn.execute("""
            INSERT OR IGNORE INTO users (id, username)
            VALUES (?, ?)
        """, (user_id, username))
        conn.commit()

    def add_history(self, user_id, dish_name, recipe_title):
        conn = self.get_connection()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('''
            INSERT INTO history (user_id, dish_name, recipe_title, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, dish_name, recipe_title, timestamp))
        conn.commit()

    def get_user_history(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dish_name, recipe_title, timestamp 
            FROM history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (user_id,))
        return cursor.fetchall()

    def get_favourite(self, user_id, receipt_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM favourites WHERE user_id=? AND receipt_id=?
        """, (user_id, receipt_id))
        return cursor.fetchone()

    def add_favourite(self, user_id, receipt_id):
        conn = self.get_connection()
        conn.execute('''
            INSERT OR IGNORE INTO favourites (user_id, receipt_id)
            VALUES (?, ?)
        ''', (user_id, receipt_id))
        conn.commit()

    def get_favourites_count(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM favourites WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]

    def get_favourites(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.spoon_id, r.title
            FROM favourites f
            JOIN receipts r ON f.receipt_id = r.spoon_id
            WHERE f.user_id = ?
        ''', (user_id,))
        return cursor.fetchall()

    def get_recipe(self, recipe_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT * FROM receipts r WHERE r.spoon_id = ?
            """
            , (recipe_id,))
        return cursor.fetchone()

    def close_connection(self):
        """Закрыть соединение для текущего потока"""
        if hasattr(self.local, "connection") and self.local.connection is not None:
            self.local.connection.close()
            self.local.connection = None
