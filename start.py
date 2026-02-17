#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("🚀 Запуск 8800.life Proxy Bot\n")
    
    try:
        # Останавливаем старые контейнеры
        print("🛑 Останавливаем старые контейнеры...")
        subprocess.run("docker compose down", shell=True, check=False)
        
        # Запускаем
        print("▶️  Запускаем сервисы...")
        result = subprocess.run("docker compose up -d --build", shell=True, check=True)
        
        print("\n✅ Запущено!")
        print("\n📊 Статус:")
        subprocess.run("docker compose ps", shell=True)
        
        print("\n📱 Ссылка для Telegram:")
        print("https://t.me/proxy?server=8800.life&port=8800&secret=dd7f8a9b2c3d4e5f6789abcdef012345")
        
        print("\n📋 Команды:")
        print("  Логи бота:   docker compose logs -f bot")
        print("  Логи прокси: docker compose logs -f mtproxy")
        print("  Остановить:  docker compose down")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
