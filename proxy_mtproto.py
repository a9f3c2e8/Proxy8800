"""MTProto прокси-сервер для Telegram"""
import asyncio
import logging
import os
import secrets
import hashlib
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

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
        if self.secret.startswith('dd'):
            self.secret_bytes = bytes.fromhex(self.secret[2:])
            self.random_padding = True
        else:
            self.secret_bytes = bytes.fromhex(self.secret)
            self.random_padding = False
        
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
    
    def create_aes_ctr(self, key, iv):
        """Создать AES-CTR шифр"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        return cipher
    
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
            
            # Извлекаем nonce (первые 56 байт) и зашифрованный тег (последние 8 байт)
            nonce = handshake[:56]
            encrypted_tag = handshake[56:64]
            
            # Создаем ключи для расшифровки по протоколу MTProto
            key_material = hashlib.sha256(nonce + self.secret_bytes).digest()
            
            decrypt_key = key_material[:16]
            decrypt_iv = key_material[16:32]
            
            # Расшифровываем тег
            cipher = self.create_aes_ctr(decrypt_key, decrypt_iv)
            decryptor = cipher.decryptor()
            decrypted_tag = decryptor.update(encrypted_tag)
            
            # Определяем DC (обычно DC2)
            dc_id = 2
            telegram_host, telegram_port = self.TELEGRAM_SERVERS[dc_id]
            
            # Подключаемся к Telegram
            telegram_reader, telegram_writer = await asyncio.wait_for(
                asyncio.open_connection(telegram_host, telegram_port),
                timeout=10
            )
            
            logger.info(f"✓ Подключено к Telegram DC{dc_id}")
            
            # Создаем handshake для Telegram
            telegram_handshake = nonce + decrypted_tag
            telegram_writer.write(telegram_handshake)
            await telegram_writer.drain()
            
            # Создаем ключи для шифрования в обратную сторону
            encrypt_key_material = hashlib.sha256(self.secret_bytes + nonce).digest()
            encrypt_key = encrypt_key_material[:16]
            encrypt_iv = encrypt_key_material[16:32]
            
            # Создаем шифры для обеих сторон
            client_decrypt_cipher = self.create_aes_ctr(decrypt_key, decrypt_iv)
            client_decryptor = client_decrypt_cipher.decryptor()
            
            client_encrypt_cipher = self.create_aes_ctr(encrypt_key, encrypt_iv)
            client_encryptor = client_encrypt_cipher.encryptor()
            
            # Проксируем данные в обе стороны
            await asyncio.gather(
                self.pipe_data(client_reader, telegram_writer, client_decryptor, "client->telegram"),
                self.pipe_data(telegram_reader, client_writer, client_encryptor, "telegram->client"),
                return_exceptions=True
            )
            
        except asyncio.TimeoutError:
            logger.debug("Таймаут при подключении")
        except asyncio.IncompleteReadError:
            logger.debug("Клиент отключился во время handshake")
        except ConnectionRefusedError:
            logger.error("Не удалось подключиться к Telegram DC")
        except OSError as e:
            logger.error(f"Ошибка сети: {e}")
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
        finally:
            self.active_connections -= 1
            
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
    
    async def pipe_data(self, reader, writer, crypto, direction):
        """Проксирование данных с шифрованием/дешифрованием"""
        try:
            while True:
                data = await reader.read(16384)
                if not data:
                    break
                
                if crypto:
                    data = crypto.update(data)
                
                writer.write(data)
                await writer.drain()
                
                if "client->telegram" in direction:
                    self.stats['bytes_sent'] += len(data)
                else:
                    self.stats['bytes_received'] += len(data)
                    
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
    port = int(os.getenv('PROXY_PORT', '8800'))
    secret = os.getenv('MTPROTO_SECRET', None)
    domain = os.getenv('PROXY_DOMAIN', '8800.life')
    
    proxy = MTProtoProxy(host='0.0.0.0', port=port, secret=secret, domain=domain)
    await proxy.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nСервер остановлен")
