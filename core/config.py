"""Конфигурация бота"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin
ADMIN_ID = 1649567897

# Remnawave Panel
REMNAWAVE_BASE_URL = os.getenv("REMNAWAVE_BASE_URL", "")
REMNAWAVE_TOKEN = os.getenv("REMNAWAVE_TOKEN", "")

# MTProxy
PROXY_DOMAIN = os.getenv("PROXY_DOMAIN", "8800.life")
PROXY_PORT = int(os.getenv("PROXY_PORT", "443"))
MTPROTO_SECRET = os.getenv("MTPROTO_SECRET", "")

# Channel
CHANNEL_ID = os.getenv("CHANNEL_ID", "@connections8800")

# Platega.io Payment
PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID", "")
PLATEGA_API_KEY = os.getenv("PLATEGA_API_KEY", "")

# Периоды
PERIODS = {
    '30': '1 месяц', '60': '2 месяца', '90': '3 месяца',
    '120': '4 месяца', '150': '5 месяцев', '180': '6 месяцев'
}

# Картинки для меню
MENU_IMAGES = {
    'main': 'https://i.postimg.cc/X7dYb2hv/Frame-1948756164.png',
    'channel': 'https://i.postimg.cc/Fs3H4Pqs/Frame-1948756165.png',
    'profile': 'https://i.postimg.cc/YqYCHXVp/Frame-1948756166.png',
    'support': 'https://i.postimg.cc/tCW4jrf4/Frame-1948756167.png',
    'locations': 'https://i.postimg.cc/65npXHS3/Frame-1948756168.png',
}
