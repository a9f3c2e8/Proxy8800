"""Обработчик для просмотра прокси"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from core.database import db
from keyboards import back_to_main_keyboard
from core.config import COUNTRIES, PERIODS, MENU_IMAGES, PROXY_DOMAIN, PROXY_PORT

logger = logging.getLogger(__name__)


def build_proxy_message(proxy, idx, total):
    """Собрать текст и кнопки для одного прокси"""
    service_type = proxy.get('service_type', 'proxy')
    period = proxy.get('period', 'N/A')

    if service_type == 'proxy':
        secret = os.getenv('MTPROTO_SECRET', 'ee665192ec740b9064430789980cd72dbe7777772e676f6f676c652e636f6d')
        tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={PROXY_PORT}&secret={secret}"
        text = (
            f"📱 <b>Прокси для Telegram</b> ({idx + 1}/{total})\n\n"
            f"Период: {PERIODS.get(period, period)}\n\n"
            f"<code>{tg_link}</code>"
        )
        buttons = [[InlineKeyboardButton("📱 Подключить к Telegram", url=tg_link)]]
    else:
        username = proxy.get('username', '')
        password = proxy.get('password', '')
        text = (
            f"🌐 <b>VPN</b> ({idx + 1}/{total})\n\n"
            f"Период: {PERIODS.get(period, period)}\n"
            f"Логин: <code>{username}</code>\n"
            f"Пароль: <code>{password}</code>"
        )
        buttons = []

    # Пагинация
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f'proxy_page_{idx - 1}'))
    if total > 1:
        nav.append(InlineKeyboardButton(f"{idx + 1}/{total}", callback_data='proxy_page_noop'))
    if idx < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f'proxy_page_{idx + 1}'))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    return text, InlineKeyboardMarkup(buttons)


async def show_proxy_page(message, proxies, idx, bot_data):
    """Показать страницу прокси через edit_media"""
    if not proxies:
        text = (
            "📋 <b>Ваши подключения</b>\n\n"
            "У вас пока нет активных подключений.\n\n"
            "<blockquote><i>Нажмите «Приобрести» чтобы купить</i></blockquote>"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Приобрести", callback_data='buy_proxy')],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ])
    else:
        idx = max(0, min(idx, len(proxies) - 1))
        text, keyboard = build_proxy_message(proxies[idx], idx, len(proxies))

    try:
        media = InputMediaPhoto(
            media=bot_data.get('main_photo_file_id', MENU_IMAGES['profile']),
            caption=text, parse_mode='HTML'
        )
        await message.edit_media(media=media, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка edit_media: {e}")
        try:
            await message.edit_caption(caption=text, reply_markup=keyboard, parse_mode='HTML')
        except Exception:
            pass


async def my_proxies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список активных прокси пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    proxies = db.get_user_proxies(user_id)
    context.user_data['cached_proxies'] = proxies
    await show_proxy_page(query.message, proxies, 0, context.bot_data)
    logger.info(f"Пользователь {user_id} просмотрел список прокси")


async def proxy_page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пагинация прокси"""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    data = query.data
    if data == 'proxy_page_noop':
        return

    page = int(data.split('_')[-1])
    proxies = context.user_data.get('cached_proxies') or db.get_user_proxies(user_id)
    context.user_data['cached_proxies'] = proxies
    await show_proxy_page(query.message, proxies, page, context.bot_data)


async def view_proxy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать только прокси для Telegram"""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    all_proxies = db.get_user_proxies(user_id)
    proxies = [p for p in all_proxies if p.get('service_type', 'proxy') == 'proxy']
    context.user_data['cached_proxies'] = proxies
    await show_proxy_page(query.message, proxies, 0, context.bot_data)


async def view_vpn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать только VPN"""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    all_proxies = db.get_user_proxies(user_id)
    vpns = [p for p in all_proxies if p.get('service_type', 'proxy') == 'vpn']
    context.user_data['cached_proxies'] = vpns
    await show_proxy_page(query.message, vpns, 0, context.bot_data)
