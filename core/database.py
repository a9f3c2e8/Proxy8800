"""База данных на SQLite"""
import sqlite3
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str = 'data/bot.db'):
        self.db_path = db_path
        # Создаем папку data если не существует
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _get_connection(self):
        """Получить подключение к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Инициализация базы данных"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица прокси
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                ip TEXT,
                port INTEGER,
                username TEXT,
                password TEXT,
                country TEXT,
                period TEXT,
                service_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица временных данных пользователя
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER,
                key TEXT,
                value TEXT,
                PRIMARY KEY (user_id, key),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("База данных SQLite инициализирована")
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None):
        """Создать пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, balance)
                VALUES (?, ?, ?, 100.0)
            ''', (user_id, username, first_name))
            conn.commit()
            logger.info(f"Создан пользователь {user_id}")
        except sqlite3.IntegrityError:
            pass  # Пользователь уже существует
        finally:
            conn.close()
    
    def get_balance(self, user_id: int) -> float:
        """Получить баланс пользователя"""
        user = self.get_user(user_id)
        if not user:
            self.create_user(user_id)
            return 100.0
        return user['balance']
    
    def add_balance(self, user_id: int, amount: float) -> bool:
        """Пополнить баланс"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET balance = balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        
        # Записываем транзакцию
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, 'deposit', 'Пополнение баланса'))
        
        conn.commit()
        conn.close()
        return True
    
    def subtract_balance(self, user_id: int, amount: float) -> bool:
        """Списать с баланса"""
        balance = self.get_balance(user_id)
        if balance < amount:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET balance = balance - ? WHERE user_id = ?
        ''', (amount, user_id))
        
        # Записываем транзакцию
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, -amount, 'purchase', 'Покупка прокси'))
        
        conn.commit()
        conn.close()
        return True
    
    def assign_proxy(self, user_id: int, proxy_id: str, proxy_data: Dict):
        """Выдать прокси пользователю"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO proxies (id, user_id, ip, port, username, password, country, period, service_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            proxy_id,
            user_id,
            proxy_data['ip'],
            proxy_data['port'],
            proxy_data['username'],
            proxy_data['password'],
            proxy_data['country'],
            proxy_data['period'],
            proxy_data.get('service_type', 'proxy')
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Прокси {proxy_id} выдан пользователю {user_id}")
    
    def get_user_proxies(self, user_id: int) -> List[Dict]:
        """Получить все прокси пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM proxies WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_proxy_count(self, user_id: int) -> int:
        """Получить количество прокси пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM proxies WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    
    def set_user_data(self, user_id: int, key: str, value):
        """Сохранить временные данные пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Создаем пользователя если не существует
        self.create_user(user_id)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_data (user_id, key, value)
            VALUES (?, ?, ?)
        ''', (user_id, key, json.dumps(value)))
        
        conn.commit()
        conn.close()
    
    def get_user_data(self, user_id: int, key: str, default=None):
        """Получить временные данные пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT value FROM user_data WHERE user_id = ? AND key = ?
        ''', (user_id, key))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['value'])
        return default


# Глобальный экземпляр базы данных
db = Database()
