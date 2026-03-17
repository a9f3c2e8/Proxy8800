"""Обработчик команды /start"""
import logging
import os
import random
import hashlib
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import main_menu_keyboard
from core.config import MENU_IMAGES, CHANNEL_ID, PROXY_DOMAIN, PROXY_PORT, ADMIN_ID, VLESS_SUB_URL
from core.database import db
from utils import emoji

logger = logging.getLogger(__name__)


async def check_subscription(bot, user_id: int) -> bool:
    """Проверить подписку на канал"""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ('member', 'administrator', 'creator')
    except Exception:
        return False


def generate_trial_proxy(user_id: int, service_type: str, index: int) -> dict:
    """Генерировать пробный прокси"""
    data = f"{user_id}:trial:{service_type}:{index}"
    proxy_id = hashlib.md5(data.encode()).hexdigest()[:8]

    if service_type == 'proxy':
        secret = os.getenv('MTPROTO_SECRET', 'ee665192ec740b9064430789980cd72dbe7777772e676f6f676c652e636f6d')
        username = secret
        password = ''
    else:
        username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        password = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))

    return {
        'id': proxy_id,
        'ip': PROXY_DOMAIN,
        'port': PROXY_PORT,
        'username': username,
        'password': password,
        'country': 'nl',
        'period': '4',
        'service_type': service_type
    }


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")

    # Создаём пользователя если новый
    db.create_user(user.id, user.username, user.first_name)

    # Проверяем получал ли уже пробную подписку
    got_trial = db.get_user_data(user.id, 'got_trial', False)

    if not got_trial and update.message:
        # Новый пользователь — предлагаем подписаться на канал
        channel_name = CHANNEL_ID.replace('@', '')
        text = (
            f"👋 <b>Привет!</b>\n\n"
            f"Подпишись на канал и получи бесплатно на 4 дня:\n\n"
            f"📱 Прокси для Telegram\n"
            f"🌐 VPN для всех приложений\n\n"
            f"<b>Это бесплатно</b> — просто подпишись и нажми кнопку 👇"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{channel_name}")],
            [InlineKeyboardButton("🎁 Получить бесплатно", callback_data='check_sub')],
        ])
        msg = await update.message.reply_photo(
            photo=MENU_IMAGES['main'],
            caption=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        if 'main_photo_file_id' not in context.bot_data:
            context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id
        return

    # Обычный старт (уже получал триал или callback main_menu)
    welcome_text = (
        f"{emoji.star()} <b>Добро пожаловать в 8800 Proxy!</b>\n\n"
        f"<i>Ваш надежный партнер в мире прокси-серверов</i>\n\n"
        f"<blockquote>\"Качество и надежность - наш приоритет\"</blockquote>"
    )

    if update.message:
        if 'main_photo_file_id' in context.bot_data:
            await update.message.reply_photo(
                photo=context.bot_data['main_photo_file_id'],
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            msg = await update.message.reply_photo(
                photo=MENU_IMAGES['main'],
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
            context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id
    elif update.callback_query:
        try:
            photo_id = context.bot_data.get('main_photo_file_id', MENU_IMAGES['main'])
            media = InputMediaPhoto(media=photo_id, caption=welcome_text, parse_mode='HTML')
            msg = await update.callback_query.message.edit_media(
                media=media, reply_markup=main_menu_keyboard()
            )
            if 'main_photo_file_id' not in context.bot_data:
                context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id
        except Exception:
            await update.callback_query.message.delete()
            msg = await update.callback_query.message.reply_photo(
                photo=context.bot_data.get('main_photo_file_id', MENU_IMAGES['main']),
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
            if 'main_photo_file_id' not in context.bot_data:
                context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id


async def check_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка подписки и выдача пробной подписки"""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    # Уже получал триал
    got_trial = db.get_user_data(user_id, 'got_trial', False)
    if got_trial:
        await start_handler(update, context)
        return

    # Проверяем подписку
    subscribed = await check_subscription(context.bot, user_id)
    if not subscribed:
        await query.answer("❌ Вы не подписаны на канал!", show_alert=True)
        return

    # Выдаём пробные подписки
    # 1. Прокси для Telegram
    proxy_data = generate_trial_proxy(user_id, 'proxy', 0)
    db.assign_proxy(user_id, proxy_data['id'], proxy_data)

    # 2. VPN
    vpn_data = generate_trial_proxy(user_id, 'vpn', 1)
    db.assign_proxy(user_id, vpn_data['id'], vpn_data)

    # Отмечаем что триал получен
    db.set_user_data(user_id, 'got_trial', True)

    # MTProto ссылка
    secret = os.getenv('MTPROTO_SECRET', 'ee665192ec740b9064430789980cd72dbe7777772e676f6f676c652e636f6d')
    tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={PROXY_PORT}&secret={secret}"

    # VLESS подписка
    vless_link = VLESS_SUB_URL

    text = (
        "🎁 <b>Пробная подписка на 4 дня активирована!</b>\n\n"
        f"📱 <b>Прокси для Telegram</b>\n"
        f"Нажми кнопку — подключится автоматически\n\n"
        f"🌐 <b>VPN для всех приложений</b>\n"
        f"Нажми кнопку — добавь подписку в V2Box / Streisand\n\n"
        "<blockquote><i>Приятного использования! После окончания пробного периода — продлите в меню</i></blockquote>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Подключить прокси", url=tg_link)],
        [InlineKeyboardButton("🌐 Подключить VPN", callback_data='show_vpn_sub')],
        [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
    ])

    try:
        media = InputMediaPhoto(
            media=context.bot_data.get('main_photo_file_id', MENU_IMAGES['main']),
            caption=text, parse_mode='HTML'
        )
        await query.message.edit_media(media=media, reply_markup=keyboard)
    except Exception:
        await query.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode='HTML')

    logger.info(f"Пользователь {user_id} получил пробную подписку")


async def show_vpn_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать ссылку подписки VPN для копирования"""
    query = update.callback_query
    await query.answer()

    text = (
        "🌐 <b>VPN — подключение</b>\n\n"
        "1. Установи <b>V2Box</b> или <b>Streisand</b>\n"
        "2. Скопируй ссылку ниже\n"
        "3. Добавь подписку в приложении\n\n"
        f"<code>{VLESS_SUB_URL}</code>\n\n"
        "<blockquote><i>Нажми на ссылку чтобы скопировать</i></blockquote>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
    ])

    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode='HTML')
    except Exception:
        await query.message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML')
