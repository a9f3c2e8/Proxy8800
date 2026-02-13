#!/usr/bin/env python3
"""Скрипт запуска SOCKS5 прокси-сервера"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from proxy_server import main
import asyncio

if __name__ == '__main__':
    print("Запуск SOCKS5 прокси-сервера 8800.life...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
