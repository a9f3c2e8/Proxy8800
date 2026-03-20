"""Главный обработчик callback запросов"""
import logging
import secrets
import os
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
    
    # Защита от спама - проверяем последнее нажатие
    last_callback = context.user_data.get('last_callback', 0)
    import time
    current_time = time.time()
    
    if current_time - last_callback < 0.5:  # 500ms между нажатиями
        await query.answer("⏳ Подождите немного", show_alert=False)
        return
    
    context.user_data['last_callback'] = current_time
    
    # Быстрый ответ на callback
    await query.answer()
    
    # Обработка неактивных серверов
    if data == 'server_unavailable':
        await query.answer("🔒 Этот сервер временно недоступен", show_alert=True)
        return
    
    # Обработка выбора типа сервиса
    if data == 'buy_service_proxy':
        await handle_service_proxy(update, context)
        return
    elif data == 'buy_service_vpn':
        await handle_service_vpn(update, context)
        return
    elif data == 'vpn_unavailable':
        await query.answer("🔴 VPN временно недоступен. Ведутся работы.", show_alert=True)
        return
    
    # Роутинг по типу callback
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
    
    # Кэшируем данные в context вместо множественных запросов к БД
    data = {
        'service_type': 'proxy',
        'buy_ip_version': '4',
        'buy_type': 'dedicated',
        'buy_country': 'nl'
    }
    context.user_data.update(data)
    
    # Сохраняем в БД одним запросом
    db.set_user_data_batch(user_id, data)
    
    text = (
        f"📱 <b>Прокси для Telegram</b>\n\n"
        f"🇳🇱 Сервер: Нидерланды\n\n"
        f"<blockquote><i>Выберите период</i></blockquote>"
    )
    
    await query.message.edit_caption(
        caption=text,
        reply_markup=periods_keyboard(),
        parse_mode='HTML'
    )


async def handle_service_vpn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора VPN для всех сервисов"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Кэшируем данные в context
    data = {
        'service_type': 'vpn',
        'buy_ip_version': '4',
        'buy_type': 'dedicated',
        'buy_country': 'nl'
    }
    context.user_data.update(data)
    
    # Сохраняем в БД одним запросом
    db.set_user_data_batch(user_id, data)
    
    text = (
        f"🌐 <b>VPN для всех сервисов</b>\n\n"
        f"<blockquote><i>Выберите период</i></blockquote>"
    )
    
    # Создаем клавиатуру с ценами для VPN
    from keyboards import vpn_periods_keyboard
    
    await query.message.edit_caption(
        caption=text,
        reply_markup=vpn_periods_keyboard(),
        parse_mode='HTML'
    )


async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Обработка выбора страны"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    country = data.split('_')[2]
    context.user_data['buy_country'] = country
    db.set_user_data(user_id, 'buy_country', country)
    
    logger.info(f"Пользователь {user_id} выбрал страну: {country}")
    
    # Используем edit_caption вместо edit_text, так как сообщение с фото
    await query.message.edit_caption(
        caption="⏱ <b>Выберите период</b>",
        reply_markup=periods_keyboard(),
        parse_mode='HTML'
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
    
    # Используем кэш вместо БД
    service_type = context.user_data.get('service_type') or db.get_user_data(user_id, 'service_type', 'proxy')
    context.user_data['service_type'] = service_type
    
    if service_type == 'vpn':
        # Для VPN: сразу показываем подтверждение оплаты (количество = 1)
        context.user_data['buy_quantity'] = 1
        db.set_user_data(user_id, 'buy_quantity', 1)
        
        # Рассчитываем стоимость
        period_days = int(period)
        price_per_month = 99.0  # VPN: 99₽ за месяц
        price_per_day = price_per_month / 30
        amount = price_per_day * period_days
        context.user_data['buy_amount'] = amount
        db.set_user_data(user_id, 'buy_amount', amount)
        
        # Кэшируем баланс
        if 'balance' not in context.user_data:
            context.user_data['balance'] = db.get_balance(user_id)
        balance = context.user_data['balance']
        
        from core.config import ADMIN_ID
        if user_id == ADMIN_ID or balance >= amount:
            # Достаточно средств - показываем кнопку "Оплатить"
            text = (
                f"💳 <b>Подтверждение оплаты</b>\n\n"
                f"Сервис: 🌐 VPN\n"
                f"Период: {PERIODS.get(period)}\n\n"
                f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n"
                f"💳 Ваш баланс: <b>{balance:.2f} ₽</b>"
            )
            keyboard = [
                [InlineKeyboardButton("✅ Оплатить", callback_data='buy_confirm')],
                [InlineKeyboardButton("❌ Отменить", callback_data='main_menu')]
            ]
        else:
            # Недостаточно средств - показываем кнопку "Пополнить"
            text = (
                f"❌ <b>Недостаточно средств</b>\n\n"
                f"Сервис: 🌐 VPN\n"
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
    else:
        # Для Прокси: сразу количество = 1, показываем оплату
        context.user_data['buy_quantity'] = 1
        db.set_user_data(user_id, 'buy_quantity', 1)
        
        period_days = int(period)
        price_per_month = 50.0
        price_per_day = price_per_month / 30
        amount = price_per_day * period_days
        context.user_data['buy_amount'] = amount
        db.set_user_data(user_id, 'buy_amount', amount)
        
        if 'balance' not in context.user_data:
            context.user_data['balance'] = db.get_balance(user_id)
        balance = context.user_data['balance']
        
        # Админ или достаточно средств
        from core.config import ADMIN_ID
        if user_id == ADMIN_ID or balance >= amount:
            text = (
                f"💳 <b>Подтверждение оплаты</b>\n\n"
                f"Сервис: 📱 Прокси для Telegram\n"
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
                f"Сервис: 📱 Прокси для Telegram\n"
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
        # Используем кэш вместо БД
        order_data = {
            'country': context.user_data.get('buy_country') or db.get_user_data(user_id, 'buy_country'),
            'quantity': context.user_data.get('buy_quantity') or db.get_user_data(user_id, 'buy_quantity'),
            'period': context.user_data.get('buy_period') or db.get_user_data(user_id, 'buy_period')
        }
        
        # Получаем стоимость из кэша
        amount = context.user_data.get('buy_amount') or db.get_user_data(user_id, 'buy_amount', 0)
        
        # Проверяем баланс и списываем
        if not db.subtract_balance(user_id, amount):
            from core.config import ADMIN_ID
            if user_id == ADMIN_ID:
                pass
            else:
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
        
        import random
        import hashlib
        from core.config import PROXY_DOMAIN, PROXY_PORT
        
        quantity = order_data['quantity']
        country_code = order_data['country']
        service_type = context.user_data.get('service_type') or db.get_user_data(user_id, 'service_type', 'proxy')
        
        first_proxy_data = None
        
        for i in range(quantity):
            data = f"{user_id}:{i}:{random.randint(1000, 9999)}"
            proxy_id = hashlib.md5(data.encode()).hexdigest()[:8]
            
            if service_type == 'proxy':
                import os
                secret = os.getenv('MTPROTO_SECRET', 'ee665192ec740b9064430789980cd72dbe63646e2e636c6f7564666c6172652e636f6d')
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
                # Сохраняем VPN ключ в БД
                db.create_vpn_key(user_id, vless_uuid, vpn_token)
                logger.info(f"VPN key created: token={vpn_token} uuid={vless_uuid[:8]}")
            
            proxy_data = {
                'id': proxy_id,
                'ip': PROXY_DOMAIN,
                'port': unique_port,
                'username': username,
                'password': password,
                'country': country_code,
                'period': order_data['period'],
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
            caption=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Order confirmation error for user {user_id}: {e}", exc_info=True)
