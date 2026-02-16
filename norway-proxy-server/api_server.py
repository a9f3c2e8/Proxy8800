"""API сервер для управления прокси через 8800.life"""
import asyncio
import json
import logging
from aiohttp import web
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Только критичные ошибки
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyDatabase:
    """База данных для прокси-сервера"""
    
    def __init__(self, db_path: str = '/data/proxy.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблица активных пользователей прокси
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxy_users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                telegram_user_id INTEGER,
                expires_at TIMESTAMP NOT NULL,
                traffic_limit INTEGER DEFAULT 0,
                traffic_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        ''')
        
        # Таблица статистики подключений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connection_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                client_ip TEXT,
                destination TEXT,
                bytes_sent INTEGER DEFAULT 0,
                bytes_received INTEGER DEFAULT 0,
                connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                disconnected_at TIMESTAMP,
                FOREIGN KEY (username) REFERENCES proxy_users (username)
            )
        ''')
        
        # Индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_proxy_users_telegram ON proxy_users(telegram_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_proxy_users_expires ON proxy_users(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connection_stats_username ON connection_stats(username)')
        
        conn.commit()
        conn.close()
        print(f"Proxy DB initialized")
    
    def create_proxy_user(self, username: str, password: str, telegram_user_id: int, 
                         days: int = 30, traffic_limit: int = 0) -> bool:
        """Создать пользователя прокси"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(days=days)
        
        try:
            cursor.execute('''
                INSERT INTO proxy_users (username, password, telegram_user_id, expires_at, traffic_limit)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, telegram_user_id, expires_at, traffic_limit))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verify_credentials(self, username: str, password: str) -> Optional[Dict]:
        """Проверить учетные данные и вернуть информацию о пользователе"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM proxy_users 
            WHERE username = ? AND password = ?
        ''', (username, password))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        user = dict(row)
        
        # Проверяем срок действия
        expires_at = datetime.fromisoformat(user['expires_at'])
        if datetime.now() > expires_at:
            return None
        
        # Проверяем лимит трафика
        if user['traffic_limit'] > 0 and user['traffic_used'] >= user['traffic_limit']:
            return None
        
        return user
    
    def update_last_used(self, username: str):
        """Обновить время последнего использования"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE proxy_users SET last_used = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def log_connection(self, username: str, client_ip: str, destination: str):
        """Записать подключение"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO connection_stats (username, client_ip, destination)
            VALUES (?, ?, ?)
        ''', (username, client_ip, destination))
        
        conn.commit()
        conn.close()
    
    def update_traffic(self, username: str, bytes_sent: int, bytes_received: int):
        """Обновить статистику трафика"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE proxy_users 
            SET traffic_used = traffic_used + ?
            WHERE username = ?
        ''', (bytes_sent + bytes_received, username))
        
        conn.commit()
        conn.close()
    
    def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[Dict]:
        """Получить прокси-пользователя по Telegram ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM proxy_users 
            WHERE telegram_user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (telegram_user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_stats(self, username: str) -> Dict:
        """Получить статистику пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Информация о пользователе
        cursor.execute('SELECT * FROM proxy_users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {}
        
        user_dict = dict(user)
        
        # Статистика подключений
        cursor.execute('''
            SELECT COUNT(*) as total_connections,
                   SUM(bytes_sent) as total_sent,
                   SUM(bytes_received) as total_received
            FROM connection_stats
            WHERE username = ?
        ''', (username,))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'username': user_dict['username'],
            'telegram_user_id': user_dict['telegram_user_id'],
            'expires_at': user_dict['expires_at'],
            'traffic_limit': user_dict['traffic_limit'],
            'traffic_used': user_dict['traffic_used'],
            'created_at': user_dict['created_at'],
            'last_used': user_dict['last_used'],
            'total_connections': stats['total_connections'] or 0,
            'total_sent': stats['total_sent'] or 0,
            'total_received': stats['total_received'] or 0
        }
    
    def extend_subscription(self, username: str, days: int) -> bool:
        """Продлить подписку"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE proxy_users 
            SET expires_at = datetime(expires_at, '+' || ? || ' days')
            WHERE username = ?
        ''', (days, username))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM proxy_users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_user(self, username: str) -> bool:
        """Удалить пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM proxy_users WHERE username = ?', (username,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success


class ProxyAPIServer:
    """API сервер для управления прокси"""
    
    def __init__(self, db: ProxyDatabase, api_key: str, host: str = '0.0.0.0', port: int = 8801):
        self.db = db
        self.api_key = api_key
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        """Настроить маршруты API"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/api/health', self.health)
        self.app.router.add_post('/api/user/create', self.create_user)
        self.app.router.add_get('/api/user/{telegram_id}', self.get_user)
        self.app.router.add_get('/api/user/{telegram_id}/stats', self.get_user_stats)
        self.app.router.add_post('/api/user/{username}/extend', self.extend_user)
        self.app.router.add_delete('/api/user/{username}', self.delete_user)
        self.app.router.add_get('/api/users', self.list_users)
        self.app.router.add_post('/api/verify', self.verify_credentials)
    
    def _check_auth(self, request: web.Request) -> bool:
        """Проверить API ключ"""
        auth_header = request.headers.get('Authorization', '')
        return auth_header == f'Bearer {self.api_key}'
    
    async def index(self, request: web.Request):
        """Главная страница"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>8800.life Proxy Management</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                .info { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .endpoint { background: #fff; border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 3px; }
                .method { display: inline-block; padding: 3px 8px; border-radius: 3px; font-weight: bold; margin-right: 10px; }
                .get { background: #61affe; color: white; }
                .post { background: #49cc90; color: white; }
                .delete { background: #f93e3e; color: white; }
                code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🔒 8800.life Proxy Management API</h1>
            <div class="info">
                <p><strong>Статус:</strong> ✅ Работает</p>
                <p><strong>Версия:</strong> 1.0.0</p>
                <p>Все данные хранятся внутри системы. IP-адреса не раскрываются.</p>
            </div>
            
            <h2>API Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/health</code>
                <p>Проверка работоспособности API</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/user/create</code>
                <p>Создать нового пользователя прокси</p>
                <p>Body: <code>{"telegram_user_id": 123, "username": "user123", "password": "pass123", "days": 30}</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/user/{telegram_id}</code>
                <p>Получить информацию о пользователе по Telegram ID</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/user/{telegram_id}/stats</code>
                <p>Получить статистику пользователя</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/user/{username}/extend</code>
                <p>Продлить подписку</p>
                <p>Body: <code>{"days": 30}</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span>
                <code>/api/user/{username}</code>
                <p>Удалить пользователя</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/users</code>
                <p>Получить список всех пользователей</p>
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                <strong>Авторизация:</strong> Все запросы требуют заголовок <code>Authorization: Bearer YOUR_API_KEY</code>
            </p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def health(self, request: web.Request):
        """Проверка здоровья"""
        return web.json_response({
            'status': 'ok',
            'service': '8800.life Proxy API',
            'version': '1.0.0'
        })
    
    async def create_user(self, request: web.Request):
        """Создать пользователя"""
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            data = await request.json()
            telegram_user_id = data['telegram_user_id']
            username = data['username']
            password = data['password']
            days = data.get('days', 30)
            traffic_limit = data.get('traffic_limit', 0)
            
            success = self.db.create_proxy_user(username, password, telegram_user_id, days, traffic_limit)
            
            if success:
                return web.json_response({
                    'success': True,
                    'username': username,
                    'expires_in_days': days
                })
            else:
                return web.json_response({'error': 'User already exists'}, status=400)
        
        except Exception:
            return web.json_response({'error': 'Internal error'}, status=500)
    
    async def get_user(self, request: web.Request):
        """Получить пользователя"""
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = int(request.match_info['telegram_id'])
        user = self.db.get_user_by_telegram_id(telegram_id)
        
        if user:
            # Скрываем пароль
            user_safe = user.copy()
            user_safe['password'] = '***'
            return web.json_response(user_safe)
        else:
            return web.json_response({'error': 'User not found'}, status=404)
    
    async def get_user_stats(self, request: web.Request):
        """Получить статистику пользователя"""
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = int(request.match_info['telegram_id'])
        user = self.db.get_user_by_telegram_id(telegram_id)
        
        if not user:
            return web.json_response({'error': 'User not found'}, status=404)
        
        stats = self.db.get_user_stats(user['username'])
        return web.json_response(stats)
    
    async def extend_user(self, request: web.Request):
        """Продлить подписку"""
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            username = request.match_info['username']
            data = await request.json()
            days = data['days']
            
            success = self.db.extend_subscription(username, days)
            
            if success:
                return web.json_response({'success': True, 'extended_days': days})
            else:
                return web.json_response({'error': 'User not found'}, status=404)
        
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def delete_user(self, request: web.Request):
        """Удалить пользователя"""
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        username = request.match_info['username']
        success = self.db.delete_user(username)
        
        if success:
            return web.json_response({'success': True})
        else:
            return web.json_response({'error': 'User not found'}, status=404)
    
    async def list_users(self, request: web.Request):
        """Список пользователей"""
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        users = self.db.get_all_users()
        
        # Скрываем пароли
        users_safe = []
        for user in users:
            user_safe = user.copy()
            user_safe['password'] = '***'
            users_safe.append(user_safe)
        
        return web.json_response({'users': users_safe, 'total': len(users_safe)})
    
    async def verify_credentials(self, request: web.Request):
        """Проверить учетные данные (для внутреннего использования)"""
        try:
            data = await request.json()
            username = data['username']
            password = data['password']
            
            user = self.db.verify_credentials(username, password)
            
            if user:
                return web.json_response({'valid': True, 'telegram_user_id': user['telegram_user_id']})
            else:
                return web.json_response({'valid': False})
        
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def start(self):
        """Запустить сервер"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"")
        print(f"{'='*60}")
        print(f"  8800.life Proxy Management API")
        print(f"  Port: {self.port}")
        print(f"{'='*60}")
        print(f"")


async def main():
    """Главная функция"""
    api_key = os.getenv('API_KEY', 'change-me-in-production')
    
    db = ProxyDatabase()
    api_server = ProxyAPIServer(db, api_key, host='0.0.0.0', port=8801)
    
    await api_server.start()
    
    # Держим сервер запущенным
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAPI stopped")
