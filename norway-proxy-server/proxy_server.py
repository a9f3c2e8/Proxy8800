"""SOCKS5 прокси-сервер на Python"""
import asyncio
import struct
import socket
import logging
import os
import sqlite3
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SOCKS5Server:
    """SOCKS5 прокси-сервер"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8800, require_auth: bool = True, max_connections: int = 1000, db_path: str = '/data/proxy.db'):
        self.host = host
        self.port = port
        self.require_auth = require_auth
        self.active_connections = 0
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
        self.db_path = db_path
        self.active_sessions = {}
    
    def _get_db_connection(self):
        """Получить подключение к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def verify_credentials(self, username: str, password: str) -> dict:
        """Проверка учетных данных через базу данных"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM proxy_users 
                WHERE username = ? AND password = ?
            ''', (username, password))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logger.warning(f"Неверные учетные данные: {username}")
                return None
            
            user = dict(row)
            
            # Проверяем срок действия
            expires_at = datetime.fromisoformat(user['expires_at'])
            if datetime.now() > expires_at:
                logger.warning(f"Прокси для {username} истек (до {expires_at})")
                return None
            
            # Проверяем лимит трафика
            if user['traffic_limit'] > 0 and user['traffic_used'] >= user['traffic_limit']:
                logger.warning(f"Превышен лимит трафика для {username}")
                return None
            
            logger.info(f"✓ Аутентификация: {username} (TG: {user['telegram_user_id']})")
            return user
            
        except Exception as e:
            logger.error(f"Ошибка проверки учетных данных: {e}")
            return None
    
    def update_last_used(self, username: str):
        """Обновить время последнего использования"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE proxy_users SET last_used = CURRENT_TIMESTAMP
                WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
            logger.debug(f"Обновлено last_used для {username}")
        except Exception as e:
            logger.error(f"Ошибка обновления last_used: {e}")
    
    def log_connection(self, username: str, client_ip: str, destination: str):
        """Записать подключение"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO connection_stats (username, client_ip, destination)
                VALUES (?, ?, ?)
            ''', (username, client_ip, destination))
            
            conn.commit()
            conn.close()
            logger.debug(f"Логировано подключение {username} -> {destination}")
        except Exception as e:
            logger.error(f"Ошибка логирования подключения: {e}")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обработка клиента"""
        async with self.semaphore:
            username = None
            try:
                addr = writer.get_extra_info('peername')
                self.active_connections += 1
                logger.info(f"[{self.active_connections}] Новое подключение от {addr}")
                
                # 1. Приветствие
                data = await asyncio.wait_for(reader.read(2), timeout=5)
                if len(data) < 2:
                    logger.warning("Недостаточно данных для приветствия")
                    return
                
                version, nmethods = struct.unpack('!BB', data)
                if version != 5:
                    logger.warning(f"Неподдерживаемая версия SOCKS: {version}")
                    return
                
                methods = await asyncio.wait_for(reader.read(nmethods), timeout=5)
                
                # Выбираем метод аутентификации
                if self.require_auth and 2 in methods:
                    writer.write(struct.pack('!BB', 5, 2))
                    await writer.drain()
                    
                    # 2. Аутентификация
                    auth_data = await asyncio.wait_for(reader.read(2), timeout=5)
                    if len(auth_data) < 2:
                        logger.warning("Недостаточно данных для аутентификации")
                        return
                    
                    auth_version, ulen = struct.unpack('!BB', auth_data)
                    username = (await asyncio.wait_for(reader.read(ulen), timeout=5)).decode('utf-8')
                    plen = struct.unpack('!B', await asyncio.wait_for(reader.read(1), timeout=5))[0]
                    password = (await asyncio.wait_for(reader.read(plen), timeout=5)).decode('utf-8')
                    
                    user = self.verify_credentials(username, password)
                    if user:
                        writer.write(struct.pack('!BB', 1, 0))
                        await writer.drain()
                        self.update_last_used(username)
                        writer._username = username
                    else:
                        writer.write(struct.pack('!BB', 1, 1))
                        await writer.drain()
                        logger.warning(f"✗ Отклонено: {username}")
                        return
                elif not self.require_auth and 0 in methods:
                    writer.write(struct.pack('!BB', 5, 0))
                    await writer.drain()
                    logger.info("✓ Подключение без аутентификации")
                else:
                    writer.write(struct.pack('!BB', 5, 255))
                    await writer.drain()
                    logger.warning("Клиент не поддерживает требуемые методы аутентификации")
                    return
                
                # 3. Запрос подключения
                request = await asyncio.wait_for(reader.read(4), timeout=5)
                if len(request) < 4:
                    logger.warning("Недостаточно данных для запроса")
                    return
                
                version, cmd, _, atyp = struct.unpack('!BBBB', request)
                
                if cmd != 1:
                    writer.write(struct.pack('!BBBBIH', 5, 7, 0, 1, 0, 0))
                    await writer.drain()
                    logger.warning(f"Неподдерживаемая команда: {cmd}")
                    return
                
                # Читаем адрес
                if atyp == 1:
                    addr_data = await asyncio.wait_for(reader.read(4), timeout=5)
                    dst_addr = socket.inet_ntoa(addr_data)
                elif atyp == 3:
                    addr_len = struct.unpack('!B', await asyncio.wait_for(reader.read(1), timeout=5))[0]
                    dst_addr = (await asyncio.wait_for(reader.read(addr_len), timeout=5)).decode('utf-8')
                elif atyp == 4:
                    addr_data = await asyncio.wait_for(reader.read(16), timeout=5)
                    dst_addr = socket.inet_ntop(socket.AF_INET6, addr_data)
                else:
                    writer.write(struct.pack('!BBBBIH', 5, 8, 0, 1, 0, 0))
                    await writer.drain()
                    logger.warning(f"Неподдерживаемый тип адреса: {atyp}")
                    return
                
                dst_port = struct.unpack('!H', await asyncio.wait_for(reader.read(2), timeout=5))[0]
                
                destination = f"{dst_addr}:{dst_port}"
                logger.info(f"→ {destination}")
                
                # Логируем подключение если есть username
                if hasattr(writer, '_username'):
                    self.log_connection(writer._username, addr[0], destination)
                
                # 4. Подключаемся
                try:
                    remote_reader, remote_writer = await asyncio.wait_for(
                        asyncio.open_connection(dst_addr, dst_port),
                        timeout=10
                    )
                    
                    bind_addr = remote_writer.get_extra_info('sockname')
                    bind_ip = socket.inet_aton(bind_addr[0])
                    bind_port = bind_addr[1]
                    
                    writer.write(struct.pack('!BBBB', 5, 0, 0, 1) + bind_ip + struct.pack('!H', bind_port))
                    await writer.drain()
                    
                    logger.info(f"✓ Подключено к {destination}")
                    
                    # 5. Проксируем данные
                    await asyncio.gather(
                        self.pipe(reader, remote_writer),
                        self.pipe(remote_reader, writer),
                        return_exceptions=True
                    )
                    
                except asyncio.TimeoutError:
                    writer.write(struct.pack('!BBBBIH', 5, 4, 0, 1, 0, 0))
                    await writer.drain()
                    logger.error(f"✗ Таймаут подключения к {destination}")
                except Exception as e:
                    writer.write(struct.pack('!BBBBIH', 5, 5, 0, 1, 0, 0))
                    await writer.drain()
                    logger.error(f"✗ Ошибка подключения к {destination}: {e}")
            
            except asyncio.TimeoutError:
                logger.warning("Таймаут при обработке клиента")
            except Exception as e:
                logger.error(f"✗ Ошибка обработки клиента: {e}")
            finally:
                self.active_connections -= 1
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                logger.info(f"[{self.active_connections}] Соединение закрыто")
    
    async def pipe(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Проксирование данных"""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
    
    async def start(self):
        """Запуск сервера"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        auth_status = "Обязательна" if self.require_auth else "Опциональна"
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"  SOCKS5 Прокси-сервер 8800.life")
        logger.info(f"  Адрес: {self.host}:{self.port}")
        logger.info(f"  Аутентификация: {auth_status}")
        logger.info(f"  Макс. соединений: {self.max_connections}")
        logger.info(f"  База данных: {self.db_path}")
        logger.info(f"{'='*60}")
        logger.info(f"")
        
        async with server:
            await server.serve_forever()


async def main():
    """Главная функция"""
    require_auth = os.getenv('REQUIRE_AUTH', 'true').lower() == 'true'
    max_connections = int(os.getenv('MAX_CONNECTIONS', '1000'))
    db_path = os.getenv('DB_PATH', '/data/proxy.db')
    
    server = SOCKS5Server(
        host='0.0.0.0', 
        port=8800, 
        require_auth=require_auth, 
        max_connections=max_connections,
        db_path=db_path
    )
    await server.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nСервер остановлен")
