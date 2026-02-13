"""Обработчик профиля"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from core.database import db
from keyboards import back_to_main_keyboard
from core.config import MENU_IMAGES
from utils import emoji

logger = logging.getLogger(__name__)


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать профиль пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username or "Не указан"
    balance = db.get_balance(user_id)
    proxy_count = db.get_proxy_count(user_id)
    
    text = (
        f"{emoji.settings()} <b>Ваш профиль</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Username: @{username}\n\n"
        f"💰 Баланс: <b>{balance:.2f} ₽</b>\n"
        f"📋 Активных прокси: <b>{proxy_count} шт.</b>\n\n"
        f"<blockquote><i>Выберите тип подключения</i></blockquote>"
    )
    
    # Получаем прокси пользователя
    proxies = db.get_user_proxies(user_id)
    
    # Разделяем прокси по типу сервиса
    proxy_list = []
    vpn_list = []
    
    for proxy in proxies:
        service_type = proxy.get('service_type', 'proxy')
        if service_type == 'vpn':
            vpn_list.append(proxy)
        else:
            proxy_list.append(proxy)
    
    keyboard = []
    
    # Кнопки для прокси и VPN - 2 в ряд
    row = []
    if proxy_list:
        row.append(InlineKeyboardButton("📱 Прокси", callback_data='view_proxy'))
    else:
        row.append(InlineKeyboardButton("📱 Прокси", callback_data='buy_proxy'))
    
    # VPN временно недоступен
    row.append(InlineKeyboardButton("🔴 VPN", callback_data='vpn_unavailable'))
    
    keyboard.append(row)
    
    # Остальные кнопки по одной
    keyboard.append([InlineKeyboardButton("📋 Все подключения", callback_data='my_proxies')])
    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    
    logger.info(f"Пользователь {user_id} открыл профиль")
    
    try:
        media = InputMediaPhoto(
            media=MENU_IMAGES['profile'],
            caption=text,
            parse_mode='HTML'
        )
        await query.message.edit_media(
            media=media,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования медиа: {e}")
        await query.message.delete()
        await query.message.reply_photo(
            photo=MENU_IMAGES['profile'],
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
