import sqlite3
import asyncio
from config.config import DATABASE_NAME
import logging

logger = logging.getLogger(__name__)

async def get_db_connection():
    """Создает новое соединение с базой данных."""
    def sync_connect():
        return sqlite3.connect(DATABASE_NAME)
    return await asyncio.to_thread(sync_connect)

async def init_db():
    """Инициализирует базу данных, включая таблицы для обучений и бизнесов с корректными названиями."""
    def sync_init():
        conn = sqlite3.connect(DATABASE_NAME)
        try:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    username TEXT,
                    referral_code TEXT UNIQUE,
                    referrer_id INTEGER,
                    bonus INTEGER DEFAULT 0,
                    rank INTEGER DEFAULT 1,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    balance INTEGER DEFAULT 0,
                    solix INTEGER DEFAULT 0,
                    aurix INTEGER DEFAULT 0,
                    valorium INTEGER DEFAULT 0,
                    registration_date TEXT,
                    last_daily DATE,
                    daily_streak INTEGER DEFAULT 0,
                    banned INTEGER DEFAULT 0
                )
            ''')

            # Таблица обучений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS education (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cost INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    required_level INTEGER NOT NULL
                )
            ''')

            # Пройденные обучения у пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_educations (
                    user_id INTEGER,
                    education_id INTEGER,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(education_id) REFERENCES education(id) ON DELETE CASCADE
                )
            ''')

            # Таблица бизнесов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    base_cost INTEGER NOT NULL,
                    base_income INTEGER NOT NULL,
                    max_level INTEGER NOT NULL,
                    income_multiplier REAL NOT NULL,
                    upgrade_cost_multiplier REAL NOT NULL,
                    required_level INTEGER NOT NULL,
                    required_education_id INTEGER,
                    FOREIGN KEY(required_education_id) REFERENCES education(id) ON DELETE SET NULL
                )
            ''')

            # Владение бизнесами пользователями
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_businesses (
                    user_id INTEGER,
                    business_id INTEGER,
                    level INTEGER DEFAULT 1,
                    last_collected_income DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(business_id) REFERENCES businesses(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(sync_init)
