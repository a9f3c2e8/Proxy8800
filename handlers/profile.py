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
    user_id = update.effective_user.id
    
    # Быстрый ответ
    await query.answer()
    
    username = update.effective_user.username or "Не указан"
    
    # Всегда читаем свежий баланс из БД
    balance = db.get_balance(user_id)
    context.user_data['balance'] = balance
    
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
    
    # VPN: открыт для админа, закрыт для остальных
    from core.config import ADMIN_ID
    if user_id == ADMIN_ID:
        if vpn_list:
            row.append(InlineKeyboardButton("🌐 VPN", callback_data='view_vpn'))
        else:
            row.append(InlineKeyboardButton("🌐 VPN", callback_data='buy_proxy'))
    else:
        row.append(InlineKeyboardButton("🔴 VPN", callback_data='vpn_unavailable'))
    
    keyboard.append(row)
    
    # Остальные кнопки по одной
    keyboard.append([InlineKeyboardButton("💳 Пополнить баланс", callback_data='topup')])
    keyboard.append([InlineKeyboardButton("📋 Все подключения", callback_data='my_proxies')])
    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    
    logger.info(f"Пользователь {user_id} открыл профиль")
    
    try:
        # Используем кэшированный file_id
        photo_id = context.bot_data.get('profile_photo_file_id', MENU_IMAGES['profile'])
        media = InputMediaPhoto(
            media=photo_id,
            caption=text,
            parse_mode='HTML'
        )
        msg = await query.message.edit_media(
            media=media,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # Сохраняем file_id если это первый раз
        if 'profile_photo_file_id' not in context.bot_data:
            context.bot_data['profile_photo_file_id'] = msg.photo[-1].file_id
    except Exception:
        await query.message.delete()
        msg = await query.message.reply_photo(
            photo=context.bot_data.get('profile_photo_file_id', MENU_IMAGES['profile']),
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        if 'profile_photo_file_id' not in context.bot_data:
            context.bot_data['profile_photo_file_id'] = msg.photo[-1].file_id
