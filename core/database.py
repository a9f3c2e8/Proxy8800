"""База данных SQLite"""
import sqlite3
import json
import logging
import os
from typing import Dict, List, Optional
from core.config import ADMIN_ID

logger = logging.getLogger(__name__)

ADMIN_BALANCE = 99999999.0


class Database:
    def __init__(self, db_path: str = 'data/bot.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS proxies (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            ip TEXT, port INTEGER, username TEXT, password TEXT,
            country TEXT, period TEXT, service_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER, key TEXT, value TEXT,
            PRIMARY KEY (user_id, key)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, amount REAL, type TEXT, description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS vpn_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, uuid TEXT NOT NULL, token TEXT NOT NULL UNIQUE,
            rw_user_uuid TEXT,
            sub_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_proxies_uid ON proxies(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_vpn_uid ON vpn_keys(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_vpn_token ON vpn_keys(token)')
        conn.commit()
        conn.close()
        logger.info("БД инициализирована")

    # --- Users ---
    def create_user(self, user_id: int, username: str = None, first_name: str = None):
        bal = ADMIN_BALANCE if user_id == ADMIN_ID else 0.0
        conn = self._conn()
        try:
            conn.execute('INSERT INTO users (user_id,username,first_name,balance) VALUES (?,?,?,?)',
                         (user_id, username, first_name, bal))
            conn.commit()
        except sqlite3.IntegrityError:
            if user_id == ADMIN_ID:
                row = conn.execute('SELECT balance FROM users WHERE user_id=?', (user_id,)).fetchone()
                if row and row['balance'] < 1_000_000:
                    conn.execute('UPDATE users SET balance=? WHERE user_id=?', (ADMIN_BALANCE, user_id))
                    conn.commit()
        finally:
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_balance(self, user_id: int) -> float:
        u = self.get_user(user_id)
        if not u:
            self.create_user(user_id)
            return ADMIN_BALANCE if user_id == ADMIN_ID else 0.0
        return u['balance']

    def add_balance(self, user_id: int, amount: float):
        conn = self._conn()
        conn.execute('UPDATE users SET balance=balance+? WHERE user_id=?', (amount, user_id))
        conn.execute('INSERT INTO transactions (user_id,amount,type,description) VALUES (?,?,?,?)',
                     (user_id, amount, 'deposit', 'Пополнение'))
        conn.commit()
        conn.close()

    def subtract_balance(self, user_id: int, amount: float) -> bool:
        if self.get_balance(user_id) < amount:
            return False
        conn = self._conn()
        conn.execute('UPDATE users SET balance=balance-? WHERE user_id=?', (amount, user_id))
        conn.execute('INSERT INTO transactions (user_id,amount,type,description) VALUES (?,?,?,?)',
                     (user_id, -amount, 'purchase', 'Покупка'))
        conn.commit()
        conn.close()
        return True

    def set_balance(self, user_id: int, amount: float):
        conn = self._conn()
        conn.execute('UPDATE users SET balance=? WHERE user_id=?', (amount, user_id))
        conn.commit()
        conn.close()

    # --- Proxies ---
    def assign_proxy(self, user_id: int, proxy_id: str, data: Dict):
        conn = self._conn()
        conn.execute('''INSERT INTO proxies (id,user_id,ip,port,username,password,country,period,service_type)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                     (proxy_id, user_id, data['ip'], data['port'], data['username'],
                      data['password'], data['country'], data['period'], data.get('service_type', 'proxy')))
        conn.commit()
        conn.close()

    def get_user_proxies(self, user_id: int) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute('SELECT * FROM proxies WHERE user_id=? ORDER BY created_at DESC', (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_proxy_count(self, user_id: int) -> int:
        conn = self._conn()
        r = conn.execute('SELECT COUNT(*) as c FROM proxies WHERE user_id=?', (user_id,)).fetchone()
        conn.close()
        return r['c']

    # --- VPN Keys ---
    def create_vpn_key(self, user_id: int, vless_uuid: str, token: str,
                       rw_user_uuid: str = None, sub_url: str = None):
        conn = self._conn()
        conn.execute('INSERT INTO vpn_keys (user_id,uuid,token,rw_user_uuid,sub_url) VALUES (?,?,?,?,?)',
                     (user_id, vless_uuid, token, rw_user_uuid, sub_url))
        conn.commit()
        conn.close()

    def get_vpn_key_by_token(self, token: str) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute('SELECT * FROM vpn_keys WHERE token=?', (token,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_vpn_keys(self, user_id: int) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute('SELECT * FROM vpn_keys WHERE user_id=? ORDER BY created_at DESC', (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_vpn_uuids(self) -> List[str]:
        conn = self._conn()
        rows = conn.execute('SELECT DISTINCT uuid FROM vpn_keys').fetchall()
        conn.close()
        return [r['uuid'] for r in rows]

    # --- User Data (temp) ---
    def set_user_data(self, user_id: int, key: str, value):
        self.create_user(user_id)
        conn = self._conn()
        conn.execute('INSERT OR REPLACE INTO user_data (user_id,key,value) VALUES (?,?,?)',
                     (user_id, key, json.dumps(value)))
        conn.commit()
        conn.close()

    def set_user_data_batch(self, user_id: int, data: Dict):
        self.create_user(user_id)
        conn = self._conn()
        vals = [(user_id, k, json.dumps(v)) for k, v in data.items()]
        conn.executemany('INSERT OR REPLACE INTO user_data (user_id,key,value) VALUES (?,?,?)', vals)
        conn.commit()
        conn.close()

    def get_user_data(self, user_id: int, key: str, default=None):
        conn = self._conn()
        row = conn.execute('SELECT value FROM user_data WHERE user_id=? AND key=?', (user_id, key)).fetchone()
        conn.close()
        return json.loads(row['value']) if row else default

    # --- Admin ---
    def get_admin_stats(self) -> Dict:
        conn = self._conn()
        c = conn.cursor()
        total_users = c.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        total_proxies = c.execute('SELECT COUNT(*) as c FROM proxies').fetchone()['c']
        total_balance = c.execute('SELECT COALESCE(SUM(balance),0) as s FROM users').fetchone()['s']
        total_tx = c.execute('SELECT COUNT(*) as c FROM transactions').fetchone()['c']
        tx_sum = c.execute('SELECT COALESCE(SUM(amount),0) as s FROM transactions').fetchone()['s']
        proxy_cnt = c.execute("SELECT COUNT(*) as c FROM proxies WHERE service_type='proxy'").fetchone()['c']
        vpn_cnt = c.execute("SELECT COUNT(*) as c FROM proxies WHERE service_type='vpn'").fetchone()['c']
        conn.close()
        return {
            'total_users': total_users, 'total_proxies': total_proxies,
            'total_balance': total_balance, 'total_transactions': total_tx,
            'transactions_sum': tx_sum, 'proxy_count': proxy_cnt, 'vpn_count': vpn_cnt,
        }

    def get_all_users(self, page=0, per_page=10) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?',
                            (per_page, page * per_page)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_total_users(self) -> int:
        conn = self._conn()
        r = conn.execute('SELECT COUNT(*) as c FROM users').fetchone()
        conn.close()
        return r['c']

    def get_all_users_ids(self) -> List[int]:
        conn = self._conn()
        rows = conn.execute('SELECT user_id FROM users').fetchall()
        conn.close()
        return [r['user_id'] for r in rows]

    def get_all_proxies(self, page=0, per_page=10) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute('SELECT * FROM proxies ORDER BY created_at DESC LIMIT ? OFFSET ?',
                            (per_page, page * per_page)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_total_proxies(self) -> int:
        conn = self._conn()
        r = conn.execute('SELECT COUNT(*) as c FROM proxies').fetchone()
        conn.close()
        return r['c']

    def get_all_transactions(self, page=0, per_page=10) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute('SELECT * FROM transactions ORDER BY created_at DESC LIMIT ? OFFSET ?',
                            (per_page, page * per_page)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_total_transactions(self) -> int:
        conn = self._conn()
        r = conn.execute('SELECT COUNT(*) as c FROM transactions').fetchone()
        conn.close()
        return r['c']

    def cleanup_temp_data(self) -> int:
        conn = self._conn()
        conn.execute('DELETE FROM user_data')
        cnt = conn.total_changes
        conn.commit()
        conn.close()
        return cnt

    def cleanup_old_transactions(self, days=90) -> int:
        conn = self._conn()
        c = conn.execute("DELETE FROM transactions WHERE created_at < datetime('now','-'||?||' days')", (days,))
        cnt = c.rowcount
        conn.commit()
        conn.close()
        return cnt


db = Database()
