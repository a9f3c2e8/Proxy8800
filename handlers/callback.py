"""Главный обработчик callback запросов"""
import logging
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
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
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
    
    # Устанавливаем тип сервиса и фиксированную страну (Нидерланды)
    db.set_user_data(user_id, 'service_type', 'proxy')
    db.set_user_data(user_id, 'buy_ip_version', '4')
    db.set_user_data(user_id, 'buy_type', 'dedicated')
    db.set_user_data(user_id, 'buy_country', 'nl')  # Нидерланды
    
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
    
    # Устанавливаем тип сервиса и фиксированную страну
    db.set_user_data(user_id, 'service_type', 'vpn')
    db.set_user_data(user_id, 'buy_ip_version', '4')
    db.set_user_data(user_id, 'buy_type', 'dedicated')
    db.set_user_data(user_id, 'buy_country', 'nl')  # Нидерланды
    
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
    db.set_user_data(user_id, 'buy_period', period)
    
    logger.info(f"Пользователь {user_id} выбрал период: {period} дней")
    
    # Проверяем тип сервиса
    service_type = db.get_user_data(user_id, 'service_type', 'proxy')
    
    if service_type == 'vpn':
        # Для VPN: сразу показываем подтверждение оплаты (количество = 1)
        db.set_user_data(user_id, 'buy_quantity', 1)
        
        # Рассчитываем стоимость
        period_days = int(period)
        price_per_month = 99.0  # VPN: 99₽ за месяц
        price_per_day = price_per_month / 30
        amount = price_per_day * period_days
        db.set_user_data(user_id, 'buy_amount', amount)
        
        balance = db.get_balance(user_id)
        
        if balance >= amount:
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
        # Для Прокси: запрашиваем количество
        context.user_data['waiting_for'] = 'quantity'
        
        sent_message = await query.message.edit_caption(
            caption=(
                f"🔢 <b>Введите количество прокси</b>\n\n"
                f"Период: {PERIODS.get(period)}\n\n"
                f"<blockquote><i>Отправьте число от 1 до 100</i></blockquote>"
            ),
            parse_mode='HTML'
        )
        
        # Сохраняем ID сообщения для последующего редактирования
        context.user_data['quantity_message_id'] = sent_message.message_id


async def handle_order_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Подтверждение и создание заказа"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    order_data = {
        'country': db.get_user_data(user_id, 'buy_country'),
        'quantity': db.get_user_data(user_id, 'buy_quantity'),
        'period': db.get_user_data(user_id, 'buy_period')
    }
    
    # Получаем стоимость
    amount = db.get_user_data(user_id, 'buy_amount', 0)
    
    # Проверяем баланс и списываем
    if not db.subtract_balance(user_id, amount):
        await query.message.edit_text(
            "❌ <b>Недостаточно средств!</b>\n\n"
            f"Стоимость заказа: {amount:.2f} ₽\n"
            f"Ваш баланс: {db.get_balance(user_id):.2f} ₽\n\n"
            "Пополните баланс и попробуйте снова.",
            reply_markup=back_to_main_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Генерируем прокси данные
    import random
    import string
    import hashlib
    
    quantity = order_data['quantity']
    country_code = order_data['country']
    service_type = db.get_user_data(user_id, 'service_type', 'proxy')
    
    # IP прокси-сервера
    PROXY_SERVER_IP = "104.233.9.112"
    
    # Сохраняем данные первого прокси для кнопки
    first_proxy_data = None
    
    # Выдаем прокси пользователю
    for i in range(quantity):
        # Генерируем proxy_id (8 символов)
        data = f"{user_id}:{i}:{random.randint(1000, 9999)}"
        proxy_id = hashlib.md5(data.encode()).hexdigest()[:8]
        
        # Генерируем логин и пароль (8 символов)
        username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Порт всегда 8800
        unique_port = 8800
        
        proxy_data = {
            'id': proxy_id,
            'ip': PROXY_SERVER_IP,
            'port': unique_port,
            'username': username,
            'password': password,
            'country': country_code,
            'period': order_data['period'],
            'service_type': service_type
        }
        db.assign_proxy(user_id, proxy_id, proxy_data)
        
        # Сохраняем первый для кнопки
        if i == 0:
            first_proxy_data = proxy_data
    
    text = (
        "✅ <b>Заказ успешно создан!</b>\n\n"
        f"Выдано: {quantity} шт.\n"
        f"Списано: {amount:.2f} ₽\n"
        f"Остаток баланса: {db.get_balance(user_id):.2f} ₽"
    )
    logger.info(f"Пользователь {user_id} купил {quantity} за {amount:.2f} ₽")
    
    # Создаем кнопки с ссылкой на подключение
    if first_proxy_data:
        if service_type == 'vpn':
            # Для VPN показываем кнопку подключения к Happ
            happ_link = f"https://happ.page.link/?link=https://happ.page.link/proxy?server={first_proxy_data['ip']}:{first_proxy_data['port']}&login={first_proxy_data['username']}&password={first_proxy_data['password']}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Подключиться к Happ", url=happ_link)],
                [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
            ])
        else:
            # Для прокси показываем кнопку подключения к Telegram
            tg_link = f"https://t.me/socks?server={first_proxy_data['ip']}&port={first_proxy_data['port']}&user={first_proxy_data['username']}&pass={first_proxy_data['password']}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Подключиться к Telegram", url=tg_link)],
                [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
            ])
    else:
        keyboard = back_to_main_keyboard()
    
    # Используем edit_caption вместо edit_text, так как сообщение с фото
    await query.message.edit_caption(
        caption=text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
