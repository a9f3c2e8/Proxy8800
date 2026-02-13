"""SOCKS5 прокси-сервер на Python"""
import asyncio
import struct
import socket
import logging
import os
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки API для проверки учетных данных
API_URL = os.getenv('API_URL', 'http://bot-server:5000/verify')
API_TOKEN = os.getenv('API_TOKEN', 'your_secret_token_here_change_me')
USE_API_VALIDATION = os.getenv('USE_API_VALIDATION', 'false').lower() == 'true'


class ProxyAuth:
    """Простая система аутентификации"""
    
    def __init__(self):
        self.credentials_store = {}
    
    def parse_domain(self, domain: str) -> Optional[Tuple[str, str]]:
        """Извлечение учетных данных из домена"""
        try:
            domain = domain.replace('.8800.life', '').split(':')[0]
            if len(domain) == 8 and domain.isalnum():
                return self.credentials_store.get(domain)
        except:
            pass
        return None


proxy_auth = ProxyAuth()


class SOCKS5Server:
    """SOCKS5 прокси-сервер с аутентификацией через домен"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 1080):
        self.host = host
        self.port = port
        self.active_connections = 0
    
    def verify_credentials_api(self, proxy_id: str, username: str, password: str) -> bool:
        """Проверка учетных данных через API"""
        if not USE_API_VALIDATION:
            return False
        
        try:
            import requests
            response = requests.post(
                API_URL,
                json={
                    'proxy_id': proxy_id,
                    'username': username,
                    'password': password
                },
                headers={'Authorization': f'Bearer {API_TOKEN}'},
                timeout=2
            )
            if response.status_code == 200:
                return response.json().get('valid', False)
            return False
        except Exception as e:
            logger.error(f"Ошибка API проверки: {e}")
            return False
    
    def verify_credentials(self, username: str, password: str, client_domain: str = None) -> bool:
        """Проверка учетных данных"""
        # Если включена API валидация
        if USE_API_VALIDATION and client_domain:
            proxy_id = client_domain.replace('.8800.life', '').split(':')[0]
            if len(proxy_id) == 8 and proxy_id.isalnum():
                return self.verify_credentials_api(proxy_id, username, password)
        
        # Локальная проверка (для тестирования)
        if client_domain:
            credentials = proxy_auth.parse_domain(client_domain)
            if credentials:
                expected_user, expected_pass = credentials
                if username == expected_user and password == expected_pass:
                    return True
        
        # Проверяем что логин и пароль не пустые и имеют правильную длину
        if len(username) == 8 and len(password) == 8:
            return True
        return False
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обработка клиента"""
        try:
            addr = writer.get_extra_info('peername')
            self.active_connections += 1
            logger.info(f"[{self.active_connections}] Новое подключение от {addr}")
            
            # 1. Приветствие и выбор метода аутентификации
            data = await reader.read(2)
            if len(data) < 2:
                return
            
            version, nmethods = struct.unpack('!BB', data)
            if version != 5:
                logger.warning(f"Неподдерживаемая версия SOCKS: {version}")
                return
            
            methods = await reader.read(nmethods)
            
            # Требуем аутентификацию (метод 2)
            if 2 in methods:
                writer.write(struct.pack('!BB', 5, 2))
                await writer.drain()
                
                # 2. Аутентификация
                auth_data = await reader.read(2)
                if len(auth_data) < 2:
                    return
                
                auth_version, ulen = struct.unpack('!BB', auth_data)
                if auth_version != 1:
                    return
                
                username = (await reader.read(ulen)).decode('utf-8')
                plen = struct.unpack('!B', await reader.read(1))[0]
                password = (await reader.read(plen)).decode('utf-8')
                
                # Проверяем учетные данные
                if self.verify_credentials(username, password):
                    writer.write(struct.pack('!BB', 1, 0))
                    await writer.drain()
                    logger.info(f"✓ Аутентификация успешна: {username}")
                else:
                    writer.write(struct.pack('!BB', 1, 1))
                    await writer.drain()
                    logger.warning(f"✗ Неудачная аутентификация: {username}")
                    return
            else:
                writer.write(struct.pack('!BB', 5, 255))
                await writer.drain()
                return
            
            # 3. Запрос подключения
            request = await reader.read(4)
            if len(request) < 4:
                return
            
            version, cmd, _, atyp = struct.unpack('!BBBB', request)
            
            if cmd != 1:
                writer.write(struct.pack('!BBBBIH', 5, 7, 0, 1, 0, 0))
                await writer.drain()
                return
            
            # Читаем адрес назначения
            if atyp == 1:
                addr_data = await reader.read(4)
                dst_addr = socket.inet_ntoa(addr_data)
            elif atyp == 3:
                addr_len = struct.unpack('!B', await reader.read(1))[0]
                dst_addr = (await reader.read(addr_len)).decode('utf-8')
            elif atyp == 4:
                addr_data = await reader.read(16)
                dst_addr = socket.inet_ntop(socket.AF_INET6, addr_data)
            else:
                writer.write(struct.pack('!BBBBIH', 5, 8, 0, 1, 0, 0))
                await writer.drain()
                return
            
            dst_port = struct.unpack('!H', await reader.read(2))[0]
            
            logger.info(f"→ Подключение к {dst_addr}:{dst_port}")
            
            # 4. Подключаемся к целевому серверу
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
                
                logger.info(f"✓ Успешное подключение к {dst_addr}:{dst_port}")
                
                # 5. Проксируем данные
                await asyncio.gather(
                    self.pipe(reader, remote_writer, f"client→{dst_addr}"),
                    self.pipe(remote_reader, writer, f"{dst_addr}→client"),
                    return_exceptions=True
                )
                
            except asyncio.TimeoutError:
                logger.error(f"✗ Таймаут подключения к {dst_addr}:{dst_port}")
                writer.write(struct.pack('!BBBBIH', 5, 4, 0, 1, 0, 0))
                await writer.drain()
            except Exception as e:
                logger.error(f"✗ Ошибка подключения к {dst_addr}:{dst_port}: {e}")
                writer.write(struct.pack('!BBBBIH', 5, 5, 0, 1, 0, 0))
                await writer.drain()
        
        except Exception as e:
            logger.error(f"✗ Ошибка обработки клиента: {e}")
        finally:
            self.active_connections -= 1
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            logger.info(f"[{self.active_connections}] Соединение закрыто")
    
    async def pipe(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, direction: str):
        """Проксирование данных"""
        total_bytes = 0
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
                total_bytes += len(data)
        except:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            if total_bytes > 0:
                logger.debug(f"{direction}: {total_bytes} байт")
    
    async def start(self):
        """Запуск сервера"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"  SOCKS5 Прокси-сервер 8800.life")
        logger.info(f"  Адрес: {addr[0]}:{addr[1]}")
        logger.info(f"  Аутентификация: Обязательна")
        logger.info(f"  API валидация: {'Включена' if USE_API_VALIDATION else 'Выключена'}")
        logger.info(f"{'='*60}")
        logger.info(f"")
        
        async with server:
            await server.serve_forever()


async def main():
    """Главная функция"""
    server = SOCKS5Server(host='0.0.0.0', port=1080)
    await server.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nСервер остановлен")
