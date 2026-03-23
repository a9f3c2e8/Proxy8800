"""Обработчик /start и подписки"""
import logging
import os
import hashlib
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import main_menu_keyboard
from core.config import MENU_IMAGES, CHANNEL_ID, PROXY_DOMAIN, PROXY_PORT, ADMIN_ID
from core.database import db
from utils import emoji

logger = logging.getLogger(__name__)


async def _check_sub(bot, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(CHANNEL_ID, user_id)
        return m.status in ('member', 'administrator', 'creator')
    except Exception:
        return False


def _trial_proxy(user_id, stype, idx):
    data = f"{user_id}:trial:{stype}:{idx}"
    pid = hashlib.md5(data.encode()).hexdigest()[:8]
    if stype == 'proxy':
        secret = os.getenv('MTPROTO_SECRET', '')
        return {'id': pid, 'ip': PROXY_DOMAIN, 'port': PROXY_PORT,
                'username': secret, 'password': '', 'country': 'nl',
                'period': '4', 'service_type': 'proxy'}
    else:
        import uuid as uuid_mod
        vuuid = str(uuid_mod.uuid4())
        token = hashlib.md5(f"{user_id}:trial:{vuuid}".encode()).hexdigest()[:16]
        db.create_vpn_key(user_id, vuuid, token)
        return {'id': pid, 'ip': PROXY_DOMAIN, 'port': PROXY_PORT,
                'username': vuuid, 'password': token, 'country': 'nl',
                'period': '4', 'service_type': 'vpn'}


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) /start")
    db.create_user(user.id, user.username, user.first_name)

    got_trial = db.get_user_data(user.id, 'got_trial', False)

    if not got_trial and update.message:
        ch = CHANNEL_ID.replace('@', '')
        text = ("👋 <b>Привет!</b>\n\n"
                "Подпишись на канал и получи бесплатно на 4 дня:\n\n"
                "📱 Прокси для Telegram\n🌐 VPN для всех приложений\n\n"
                "<b>Это бесплатно</b> — просто подпишись 👇")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{ch}")],
            [InlineKeyboardButton("🎁 Получить бесплатно", callback_data='check_sub')]])
        msg = await update.message.reply_photo(photo=MENU_IMAGES['main'], caption=text,
                                                reply_markup=kb, parse_mode='HTML')
        if 'main_photo_id' not in context.bot_data:
            context.bot_data['main_photo_id'] = msg.photo[-1].file_id
        return

    # Главное меню
    text = (f"{emoji.star()} <b>Добро пожаловать в 8800!</b>\n\n"
            f"<i>Ваш надёжный партнёр</i>\n\n"
            f"<blockquote>\"Качество и надёжность\"</blockquote>")

    photo = context.bot_data.get('main_photo_id', MENU_IMAGES['main'])
    if update.message:
        msg = await update.message.reply_photo(photo=photo, caption=text,
                                                reply_markup=main_menu_keyboard(), parse_mode='HTML')
        if 'main_photo_id' not in context.bot_data:
            context.bot_data['main_photo_id'] = msg.photo[-1].file_id
    elif update.callback_query:
        try:
            media = InputMediaPhoto(media=photo, caption=text, parse_mode='HTML')
            await update.callback_query.message.edit_media(media=media, reply_markup=main_menu_keyboard())
        except Exception:
            await update.callback_query.message.delete()
            await context.bot.send_photo(chat_id=update.effective_user.id, photo=photo,
                                          caption=text, reply_markup=main_menu_keyboard(), parse_mode='HTML')


async def check_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    uid = update.effective_user.id
    await q.answer()

    if db.get_user_data(uid, 'got_trial', False):
        await start_handler(update, context)
        return

    if not await _check_sub(context.bot, uid):
        await q.answer("❌ Вы не подписаны на канал!", show_alert=True)
        return

    # Выдаём триал
    px = _trial_proxy(uid, 'proxy', 0)
    db.assign_proxy(uid, px['id'], px)
    vpn = _trial_proxy(uid, 'vpn', 1)
    db.assign_proxy(uid, vpn['id'], vpn)
    db.set_user_data(uid, 'got_trial', True)

    secret = os.getenv('MTPROTO_SECRET', '')
    tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={PROXY_PORT}&secret={secret}"
    vpn_token = vpn['password']

    text = ("🎁 <b>Пробная подписка на 4 дня!</b>\n\n"
            "📱 <b>Прокси для Telegram</b>\nНажми кнопку — подключится автоматически\n\n"
            "🌐 <b>VPN для всех приложений</b>\nСкопируй ссылку в V2Box / Streisand")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Подключить прокси", url=tg_link)],
        [InlineKeyboardButton("🌐 Подключить VPN", callback_data=f'show_vpn_key_{vpn_token}')],
        [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]])

    try:
        photo = context.bot_data.get('main_photo_id', MENU_IMAGES['main'])
        media = InputMediaPhoto(media=photo, caption=text, parse_mode='HTML')
        await q.message.edit_media(media=media, reply_markup=kb)
    except Exception:
        await q.message.edit_caption(caption=text, reply_markup=kb, parse_mode='HTML')

    logger.info(f"User {uid} got trial")
    from handlers.followup import schedule_followups
    await schedule_followups(context.application, uid, "trial")


async def show_vpn_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    uid = update.effective_user.id
    await q.answer()
    keys = db.get_user_vpn_keys(uid)
    if not keys:
        text = "🌐 <b>VPN</b>\n\nНет активных ключей.\n\n<blockquote><i>Купите в меню «Приобрести»</i></blockquote>"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Приобрести", callback_data='buy_proxy')],
                                    [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]])
    else:
        k = keys[0]
        sub_url = k.get('sub_url') or f"http://8800.life:8080/sub/{k['token']}"
        text = ("🌐 <b>VPN — подключение</b>\n\n"
                "1. Установи <b>V2Box</b> или <b>Streisand</b>\n"
                "2. Скопируй ссылку ниже\n"
                f"3. Добавь подписку\n\n<code>{sub_url}</code>")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]])
    try:
        await q.message.edit_caption(caption=text, reply_markup=kb, parse_mode='HTML')
    except Exception:
        await q.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')


async def show_vpn_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    token = q.data.replace('show_vpn_key_', '')
    key = db.get_vpn_key_by_token(token)
    sub_url = (key.get('sub_url') if key else None) or f"http://8800.life:8080/sub/{token}"
    text = ("🌐 <b>VPN — подключение</b>\n\n"
            "1. Установи <b>V2Box</b> или <b>Streisand</b>\n"
            "2. Скопируй ссылку ниже\n"
            f"3. Добавь подписку\n\n<code>{sub_url}</code>")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]])
    try:
        await q.message.edit_caption(caption=text, reply_markup=kb, parse_mode='HTML')
    except Exception:
        await q.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')
