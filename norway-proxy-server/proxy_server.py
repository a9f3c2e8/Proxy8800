"""SOCKS5 прокси-сервер на Python"""
import asyncio
import struct
import socket
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SOCKS5Server:
    """SOCKS5 прокси-сервер"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8800):
        self.host = host
        self.port = port
        self.active_connections = 0
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Проверка учетных данных (все 8-символьные пары принимаются)"""
        if len(username) == 8 and len(password) == 8:
            return True
        return False
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обработка клиента"""
        try:
            addr = writer.get_extra_info('peername')
            self.active_connections += 1
            logger.info(f"[{self.active_connections}] Новое подключение от {addr}")
            
            # 1. Приветствие
            data = await reader.read(2)
            if len(data) < 2:
                return
            
            version, nmethods = struct.unpack('!BB', data)
            if version != 5:
                return
            
            methods = await reader.read(nmethods)
            
            # Требуем аутентификацию
            if 2 in methods:
                writer.write(struct.pack('!BB', 5, 2))
                await writer.drain()
                
                # 2. Аутентификация
                auth_data = await reader.read(2)
                if len(auth_data) < 2:
                    return
                
                auth_version, ulen = struct.unpack('!BB', auth_data)
                username = (await reader.read(ulen)).decode('utf-8')
                plen = struct.unpack('!B', await reader.read(1))[0]
                password = (await reader.read(plen)).decode('utf-8')
                
                if self.verify_credentials(username, password):
                    writer.write(struct.pack('!BB', 1, 0))
                    await writer.drain()
                    logger.info(f"✓ Аутентификация: {username}")
                else:
                    writer.write(struct.pack('!BB', 1, 1))
                    await writer.drain()
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
            
            # Читаем адрес
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
            
            logger.info(f"→ {dst_addr}:{dst_port}")
            
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
                
                logger.info(f"✓ Подключено к {dst_addr}:{dst_port}")
                
                # 5. Проксируем данные
                await asyncio.gather(
                    self.pipe(reader, remote_writer),
                    self.pipe(remote_reader, writer),
                    return_exceptions=True
                )
                
            except:
                writer.write(struct.pack('!BBBBIH', 5, 5, 0, 1, 0, 0))
                await writer.drain()
        
        except:
            pass
        finally:
            self.active_connections -= 1
            try:
                writer.close()
                await writer.wait_closed()
            except:
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
        except:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def start(self):
        """Запуск сервера"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"  SOCKS5 Прокси-сервер 8800.life")
        logger.info(f"  Адрес: {self.host}:{self.port}")
        logger.info(f"  Аутентификация: Обязательна")
        logger.info(f"{'='*60}")
        logger.info(f"")
        
        async with server:
            await server.serve_forever()


async def main():
    """Главная функция"""
    server = SOCKS5Server(host='0.0.0.0', port=8800)
    await server.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nСервер остановлен")
