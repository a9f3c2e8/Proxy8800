"""MTProto прокси-сервер для Telegram"""
import asyncio
import socket
import logging
import os
import secrets
import hashlib
import struct
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MTProtoProxy:
    """MTProto прокси для Telegram"""
    
    # Telegram DC адреса
    TELEGRAM_SERVERS = {
        1: ('149.154.175.50', 443),
        2: ('149.154.167.51', 443),
        3: ('149.154.175.100', 443),
        4: ('149.154.167.91', 443),
        5: ('149.154.171.5', 443),
    }
    
    def __init__(self, host='0.0.0.0', port=8800, secret=None, domain='8800.life'):
        self.host = host
        self.port = port
        self.domain = domain
        
        # Если секрет не указан, генерируем с dd префиксом
        if secret:
            self.secret = secret
        else:
            self.secret = 'dd' + secrets.token_hex(16)
        
        # Парсим секрет
        self.secret_bytes = bytes.fromhex(self.secret[2:] if self.secret.startswith('dd') else self.secret)
        
        self.active_connections = 0
        self.stats = {
            'total_connections': 0,
            'bytes_sent': 0,
            'bytes_received': 0
        }
    
    def get_proxy_link(self):
        """Получить ссылку для подключения"""
        return f"https://t.me/proxy?server={self.domain}&port={self.port}&secret={self.secret}"
    
    def get_tg_link(self):
        """Получить tg:// ссылку"""
        return f"tg://proxy?server={self.domain}&port={self.port}&secret={self.secret}"
    
    def xor_bytes(self, data, key):
        """XOR шифрование"""
        return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))
    
    async def handle_client(self, client_reader, client_writer):
        """Обработка клиента MTProto"""
        client_addr = client_writer.get_extra_info('peername')
        self.active_connections += 1
        self.stats['total_connections'] += 1
        
        logger.info(f"[{self.active_connections}] MTProto подключение от {client_addr}")
        
        telegram_reader = None
        telegram_writer = None
        
        try:
            # Читаем первые 64 байта (handshake)
            handshake = await asyncio.wait_for(client_reader.readexactly(64), timeout=10)
            
            # Проверяем протокол
            # Первые 56 байт - nonce, следующие 8 - protocol tag
            nonce = handshake[:56]
            protocol_tag = handshake[56:64]
            
            # Создаем ключи шифрования из nonce и секрета
            init_key = hashlib.sha256(nonce + self.secret_bytes).digest()
            
            # Расшифровываем protocol tag
            decrypted_tag = self.xor_bytes(protocol_tag, init_key[:8])
            
            # Определяем DC из тега (обычно DC2)
            dc_id = 2
            telegram_host, telegram_port = self.TELEGRAM_SERVERS[dc_id]
            
            # Подключаемся к Telegram
            telegram_reader, telegram_writer = await asyncio.wait_for(
                asyncio.open_connection(telegram_host, telegram_port),
                timeout=10
            )
            
            logger.info(f"✓ Подключено к Telegram DC{dc_id} ({telegram_host})")
            
            # Создаем новый handshake для Telegram (без нашего секрета)
            # Telegram ожидает стандартный MTProto handshake
            telegram_handshake = nonce + decrypted_tag
            
            # Отправляем handshake в Telegram
            telegram_writer.write(telegram_handshake)
            await telegram_writer.drain()
            
            # Проксируем данные в обе стороны
            await asyncio.gather(
                self.pipe_data(client_reader, telegram_writer, init_key, "client->telegram"),
                self.pipe_data(telegram_reader, client_writer, init_key, "telegram->client"),
                return_exceptions=True
            )
            
        except asyncio.TimeoutError:
            logger.debug("Таймаут при подключении")
        except asyncio.IncompleteReadError:
            logger.debug("Клиент отключился во время handshake")
        except ConnectionRefusedError:
            logger.error("Не удалось подключиться к Telegram DC")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            self.active_connections -= 1
            
            # Закрываем соединения
            if telegram_writer:
                try:
                    telegram_writer.close()
                    await telegram_writer.wait_closed()
                except:
                    pass
            
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except:
                pass
            
            logger.info(f"[{self.active_connections}] Соединение закрыто")
    
    async def pipe_data(self, reader, writer, key, direction):
        """Проксирование данных с шифрованием"""
        try:
            offset = 0
            while True:
                data = await reader.read(16384)
                if not data:
                    break
                
                # Для MTProto данные могут быть зашифрованы
                # В простой реализации просто передаем как есть
                writer.write(data)
                await writer.drain()
                
                # Статистика
                if "client->telegram" in direction:
                    self.stats['bytes_sent'] += len(data)
                else:
                    self.stats['bytes_received'] += len(data)
                
                offset += len(data)
                    
        except asyncio.CancelledError:
            pass
        except ConnectionResetError:
            pass
        except Exception:
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
        
        logger.info("")
        logger.info("="*70)
        logger.info("  MTProto Proxy Server - 8800.life")
        logger.info(f"  Порт: {self.port}")
        logger.info(f"  Домен: {self.domain}")
        logger.info(f"  Secret: {self.secret}")
        logger.info("")
        logger.info("  📱 Ссылка для Telegram:")
        logger.info(f"  {self.get_proxy_link()}")
        logger.info("")
        logger.info("  🔗 Прямая ссылка:")
        logger.info(f"  {self.get_tg_link()}")
        logger.info("="*70)
        logger.info("")
        
        async with server:
            await server.serve_forever()


async def main():
    """Главная функция"""
    port = int(os.getenv('MTPROTO_PORT', '8800'))
    secret = os.getenv('MTPROTO_SECRET', None)
    domain = os.getenv('DOMAIN', '8800.life')
    
    proxy = MTProtoProxy(host='0.0.0.0', port=port, secret=secret, domain=domain)
    await proxy.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nСервер остановлен")
