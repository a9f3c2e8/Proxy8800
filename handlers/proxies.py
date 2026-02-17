"""Обработчик для просмотра прокси"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from core.database import db
from keyboards import back_to_main_keyboard
from core.config import COUNTRIES, PERIODS, MENU_IMAGES, PROXY_DOMAIN, PROXY_PORT

logger = logging.getLogger(__name__)


async def my_proxies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список активных прокси пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Быстрый ответ
    await query.answer()
    
    # Получаем прокси пользователя из базы
    proxies = db.get_user_proxies(user_id)
    
    if len(proxies) == 0:
        text = (
            "📋 <b>Ваши прокси</b>\n\n"
            "У вас пока нет активных прокси.\n\n"
            "<blockquote><i>Нажмите 'Купить прокси' чтобы приобрести</i></blockquote>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 Купить прокси", callback_data='buy_proxy')],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
        
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
    else:
        # Показываем прокси по одному с кнопкой подключения
        for idx, proxy in enumerate(proxies, 1):
            proxy_id = proxy.get('id', 'N/A')
            ip = proxy.get('ip', 'N/A')
            port = proxy.get('port', 'N/A')
            username = proxy.get('username', 'N/A')
            password = proxy.get('password', 'N/A')
            country_code = proxy.get('country', 'N/A').lower()
            country_name = COUNTRIES.get(country_code, country_code.upper())
            period = proxy.get('period', 'N/A')
            service_type = proxy.get('service_type', 'proxy')
            
            # Создаем ссылку для подключения к Telegram (MTProto)
            # MTProto ссылка (dd + 32 hex = 34 символа)
            secret = os.getenv('MTPROTO_SECRET', 'dd2ae5891b2b9b9b811b212050843193aa')
            tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={PROXY_PORT}&secret={secret}"
            
            text = (
                f"📱 <b>Прокси для Telegram</b>\n\n"
                f"IP: <code>{ip}</code>\n"
                f"Порт: <code>{port}</code>\n"
                f"Логин: <code>{username}</code>\n"
                f"Пароль: <code>{password}</code>\n"
                f"Период: {PERIODS.get(period, period)}\n\n"
                f"<code>{tg_link}</code>"
            )
            
            # Создаем кнопки
            keyboard = [
                [InlineKeyboardButton("📱 Подключить к Telegram", url=tg_link)],
                [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
            ]
            
            if idx == 1:
                # Первое сообщение - редактируем
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
            else:
                # Остальные - отправляем новыми сообщениями
                await query.message.reply_photo(
                    photo=MENU_IMAGES['profile'],
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
    
    logger.info(f"Пользователь {user_id} просмотрел список прокси")


async def view_proxy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать только прокси для Telegram"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Быстрый ответ
    await query.answer()
    
    # Получаем только прокси (не VPN)
    all_proxies = db.get_user_proxies(user_id)
    proxies = [p for p in all_proxies if p.get('service_type', 'proxy') == 'proxy']
    
    if len(proxies) == 0:
        text = (
            "📱 <b>Прокси для Telegram</b>\n\n"
            "У вас пока нет активных прокси.\n\n"
            "<blockquote><i>Приобретите прокси для доступа к Telegram</i></blockquote>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 Приобрести", callback_data='buy_proxy')],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
        
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
    else:
        # Показываем первый прокси
        proxy = proxies[0]
        proxy_id = proxy.get('id', 'N/A')
        ip = proxy.get('ip', 'N/A')
        port = proxy.get('port', 'N/A')
        username = proxy.get('username', 'N/A')
        password = proxy.get('password', 'N/A')
        service_type = proxy.get('service_type', 'proxy')
        period = proxy.get('period', 'N/A')
        
        # MTProto ссылка (dd + 32 hex = 34 символа)
        secret = os.getenv('MTPROTO_SECRET', 'dd2ae5891b2b9b9b811b212050843193aa')
        tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={PROXY_PORT}&secret={secret}"
        
        text = (
            f"📱 <b>Прокси для Telegram</b>\n\n"
            f"IP: <code>{ip}</code>\n"
            f"Порт: <code>{port}</code>\n"
            f"Логин: <code>{username}</code>\n"
            f"Пароль: <code>{password}</code>\n"
            f"Период: {PERIODS.get(period, period)}\n\n"
            f"<code>{tg_link}</code>"
        )
        
        keyboard = [
            [InlineKeyboardButton("📱 Подключить к Telegram", url=tg_link)],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
        
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


async def view_vpn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать только VPN"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Быстрый ответ
    await query.answer()
    
    # Получаем только VPN
    all_proxies = db.get_user_proxies(user_id)
    vpns = [p for p in all_proxies if p.get('service_type', 'proxy') == 'vpn']
    
    if len(vpns) == 0:
        text = (
            "🌐 <b>VPN для всех сервисов</b>\n\n"
            "У вас пока нет активного VPN.\n\n"
            "<blockquote><i>Приобретите VPN для YouTube и других сервисов</i></blockquote>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 Приобрести", callback_data='buy_proxy')],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
        
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
    else:
        # Показываем первый VPN
        vpn = vpns[0]
        ip = vpn.get('ip', 'N/A')
        port = vpn.get('port', 'N/A')
        username = vpn.get('username', 'N/A')
        password = vpn.get('password', 'N/A')
        period = vpn.get('period', 'N/A')
        
        happ_link = f"https://happ.page.link/?link=https://happ.page.link/proxy?server={ip}:{port}&login={username}&password={password}"
        
        text = (
            f"🌐 <b>VPN для всех сервисов</b>\n\n"
            f"IP: <code>{ip}</code>\n"
            f"Порт: <code>{port}</code>\n"
            f"Логин: <code>{username}</code>\n"
            f"Пароль: <code>{password}</code>\n"
            f"Период: {PERIODS.get(period, period)}\n\n"
            f"<code>{happ_link}</code>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🌐 Подключить к Happ", url=happ_link)],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
        
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

