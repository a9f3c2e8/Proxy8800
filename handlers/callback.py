"""Главный обработчик callback запросов"""
import logging
import os
import time
import random
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import db
from keyboards import (
    countries_keyboard,
    periods_keyboard,
    confirm_order_keyboard,
    back_to_main_keyboard
)
from core.config import COUNTRIES, PERIODS

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный роутер для callback запросов"""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    last_callback = context.user_data.get('last_callback', 0)
    current_time = time.time()
    if current_time - last_callback < 0.5:
        await query.answer("⏳ Подождите немного", show_alert=False)
        return
    context.user_data['last_callback'] = current_time
    await query.answer()

    if data == 'server_unavailable':
        await query.answer("🔒 Этот сервер временно недоступен", show_alert=True)
        return
    if data == 'buy_service_proxy':
        await handle_service_proxy(update, context)
        return
    elif data == 'buy_service_vpn':
        await handle_service_vpn(update, context)
        return
    elif data == 'vpn_unavailable':
        await query.answer("🔴 VPN временно недоступен. Ведутся работы.", show_alert=True)
        return

    if data.startswith('buy_country_'):
        await handle_country_selection(update, context, data)
    elif data.startswith('buy_period_'):
        await handle_period_selection(update, context, data)
    elif data.startswith('countries_page_'):
        await handle_countries_pagination(update, context, data)
    elif data == 'buy_confirm':
        await handle_order_confirmation(update, context)


async def handle_service_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора Прокси для Telegram"""
    query = update.callback_query
    user_id = update.effective_user.id
    data = {
        'service_type': 'proxy',
        'buy_ip_version': '4',
        'buy_type': 'dedicated',
        'buy_country': 'nl'
    }
    context.user_data.update(data)
    db.set_user_data_batch(user_id, data)
    text = (
        f"📱 <b>Прокси для Telegram</b>\n\n"
        f"🇳🇱 Сервер: Нидерланды\n\n"
        f"<blockquote><i>Выберите период</i></blockquote>"
    )
    await query.message.edit_caption(
        caption=text, reply_markup=periods_keyboard(), parse_mode='HTML'
    )


async def handle_service_vpn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора VPN для всех сервисов"""
    query = update.callback_query
    user_id = update.effective_user.id
    data = {
        'service_type': 'vpn',
        'buy_ip_version': '4',
        'buy_type': 'dedicated',
        'buy_country': 'nl'
    }
    context.user_data.update(data)
    db.set_user_data_batch(user_id, data)
    text = (
        f"🌐 <b>VPN для всех сервисов</b>\n\n"
        f"<blockquote><i>Выберите период</i></blockquote>"
    )
    from keyboards import vpn_periods_keyboard
    await query.message.edit_caption(
        caption=text, reply_markup=vpn_periods_keyboard(), parse_mode='HTML'
    )


async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Обработка выбора страны"""
    query = update.callback_query
    user_id = update.effective_user.id
    country = data.split('_')[2]
    context.user_data['buy_country'] = country
    db.set_user_data(user_id, 'buy_country', country)
    logger.info(f"Пользователь {user_id} выбрал страну: {country}")
    await query.message.edit_caption(
        caption="⏱ <b>Выберите период</b>",
        reply_markup=periods_keyboard(), parse_mode='HTML'
    )


async def handle_countries_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Обработка пагинации стран"""
    query = update.callback_query
    page = int(data.split('_')[-1])
    await query.message.edit_reply_markup(reply_markup=countries_keyboard(page=page))


async def handle_period_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Обработка выбора периода"""
    query = update.callback_query
    user_id = update.effective_user.id

    period = data.split('_')[2]
    context.user_data['buy_period'] = period
    db.set_user_data(user_id, 'buy_period', period)
    logger.info(f"Пользователь {user_id} выбрал период: {period} дней")

    service_type = context.user_data.get('service_type') or db.get_user_data(user_id, 'service_type', 'proxy')
    context.user_data['service_type'] = service_type

    context.user_data['buy_quantity'] = 1
    db.set_user_data(user_id, 'buy_quantity', 1)

    period_days = int(period)
    if service_type == 'vpn':
        price_per_day = 99.0 / 30
        service_label = "🌐 VPN"
    else:
        price_per_day = 50.0 / 30
        service_label = "📱 Прокси для Telegram"

    amount = price_per_day * period_days
    context.user_data['buy_amount'] = amount
    db.set_user_data(user_id, 'buy_amount', amount)

    # Всегда свежий баланс из БД
    balance = db.get_balance(user_id)
    context.user_data['balance'] = balance

    if balance >= amount:
        text = (
            f"💳 <b>Подтверждение оплаты</b>\n\n"
            f"Сервис: {service_label}\n"
            f"Период: {PERIODS.get(period)}\n\n"
            f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n"
            f"💳 Ваш баланс: <b>{balance:.2f} ₽</b>"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Оплатить", callback_data='buy_confirm')],
            [InlineKeyboardButton("❌ Отменить", callback_data='main_menu')]
        ]
    else:
        text = (
            f"❌ <b>Недостаточно средств</b>\n\n"
            f"Сервис: {service_label}\n"
            f"Период: {PERIODS.get(period)}\n\n"
            f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n"
            f"💳 Ваш баланс: <b>{balance:.2f} ₽</b>\n\n"
            f"<blockquote><i>Пополните баланс для продолжения</i></blockquote>"
        )
        keyboard = [
            [InlineKeyboardButton("💳 Пополнить баланс", callback_data='balance')],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]

    await query.message.edit_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_order_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Подтверждение и создание заказа"""
    query = update.callback_query
    user_id = update.effective_user.id

    try:
        country = context.user_data.get('buy_country') or db.get_user_data(user_id, 'buy_country') or 'nl'
        quantity = context.user_data.get('buy_quantity') or db.get_user_data(user_id, 'buy_quantity') or 1
        period = context.user_data.get('buy_period') or db.get_user_data(user_id, 'buy_period') or '30'
        amount = context.user_data.get('buy_amount') or db.get_user_data(user_id, 'buy_amount', 0)
        service_type = context.user_data.get('service_type') or db.get_user_data(user_id, 'service_type', 'proxy')

        quantity = int(quantity) if quantity else 1
        amount = float(amount) if amount else 0

        logger.info(f"Order confirm: user={user_id} type={service_type} qty={quantity} amount={amount}")

        # Списываем баланс
        if not db.subtract_balance(user_id, amount):
            balance = db.get_balance(user_id)
            context.user_data['balance'] = balance
            await query.message.edit_caption(
                caption=(
                    "❌ <b>Недостаточно средств!</b>\n\n"
                    f"Стоимость заказа: {amount:.2f} ₽\n"
                    f"Ваш баланс: {balance:.2f} ₽\n\n"
                    "Пополните баланс и попробуйте снова."
                ),
                reply_markup=back_to_main_keyboard(),
                parse_mode='HTML'
            )
            return

        context.user_data['balance'] = db.get_balance(user_id)

        from core.config import PROXY_DOMAIN, PROXY_PORT

        first_proxy_data = None

        for i in range(quantity):
            data = f"{user_id}:{i}:{random.randint(1000, 9999)}"
            proxy_id = hashlib.md5(data.encode()).hexdigest()[:8]

            if service_type == 'proxy':
                secret = os.getenv('MTPROTO_SECRET', 'ee665192ec740b9064430789980cd72dbe7777772e676f6f676c652e636f6d')
                username = secret
                password = ''
                unique_port = PROXY_PORT
            else:
                import uuid as uuid_mod
                vless_uuid = str(uuid_mod.uuid4())
                vpn_token = hashlib.md5(f"{user_id}:{vless_uuid}:{random.randint(1000,9999)}".encode()).hexdigest()[:16]
                username = vless_uuid
                password = vpn_token
                unique_port = PROXY_PORT
                db.create_vpn_key(user_id, vless_uuid, vpn_token)
                logger.info(f"VPN key created: token={vpn_token} uuid={vless_uuid[:8]}")

            proxy_data = {
                'id': proxy_id,
                'ip': PROXY_DOMAIN,
                'port': unique_port,
                'username': username,
                'password': password,
                'country': country,
                'period': period,
                'service_type': service_type
            }
            db.assign_proxy(user_id, proxy_id, proxy_data)

            if i == 0:
                first_proxy_data = proxy_data

        logger.info(f"Пользователь {user_id} купил {quantity} {service_type} за {amount:.2f} ₽")

        text = (
            "✅ <b>Заказ успешно создан!</b>\n\n"
            f"Выдано: {quantity} шт.\n"
            f"Списано: {amount:.2f} ₽\n"
            f"Остаток баланса: {db.get_balance(user_id):.2f} ₽"
        )

        if first_proxy_data:
            if service_type == 'vpn':
                vpn_token = first_proxy_data['password']
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 Подключить VPN", callback_data=f'show_vpn_key_{vpn_token}')],
                    [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
                ])
            else:
                secret = os.getenv('MTPROTO_SECRET', 'ee665192ec740b9064430789980cd72dbe7777772e676f6f676c652e636f6d')
                tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={first_proxy_data['port']}&secret={secret}"
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📱 Подключить к Telegram", url=tg_link)],
                    [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
                ])
        else:
            keyboard = back_to_main_keyboard()

        await query.message.edit_caption(
            caption=text, reply_markup=keyboard, parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Order confirmation error for user {user_id}: {e}", exc_info=True)
        try:
            await query.message.edit_caption(
                caption=f"❌ <b>Ошибка при создании заказа</b>\n\n<code>{e}</code>",
                reply_markup=back_to_main_keyboard(),
                parse_mode='HTML'
            )
        except Exception:
            pass
