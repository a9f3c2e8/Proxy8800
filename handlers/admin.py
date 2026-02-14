"""Админ-панель бота"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import db
from core.config import ADMIN_ID, COUNTRIES, PERIODS
from datetime import datetime

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == ADMIN_ID


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню админ-панели"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        # Просто игнорируем команду для не-админов
        return
    
    text = (
        "🔐 <b>Админ-панель</b>\n\n"
        "Управление ботом и пользователями"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("👥 Пользователи", callback_data='admin_users'),
            InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')
        ],
        [
            InlineKeyboardButton("💰 Управление балансами", callback_data='admin_balances')
        ],
        [
            InlineKeyboardButton("📋 Все прокси", callback_data='admin_proxies'),
            InlineKeyboardButton("💸 Транзакции", callback_data='admin_transactions')
        ],
        [
            InlineKeyboardButton("📢 Рассылка", callback_data='admin_broadcast'),
            InlineKeyboardButton("🗑 Очистка", callback_data='admin_cleanup')
        ],
        [InlineKeyboardButton("❌ Закрыть", callback_data='admin_close')]
    ]
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика бота"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    # Получаем статистику
    stats = db.get_admin_stats()
    
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"📋 Всего прокси выдано: <b>{stats['total_proxies']}</b>\n"
        f"💰 Общий баланс пользователей: <b>{stats['total_balance']:.2f} ₽</b>\n"
        f"💸 Всего транзакций: <b>{stats['total_transactions']}</b>\n"
        f"💵 Сумма транзакций: <b>{stats['transactions_sum']:.2f} ₽</b>\n\n"
        f"📱 Прокси (Telegram): <b>{stats['proxy_count']}</b>\n"
        f"🌐 VPN: <b>{stats['vpn_count']}</b>"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Список пользователей с пагинацией"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    page = context.user_data.get('admin_users_page', 0)
    per_page = 10
    
    users = db.get_all_users(page=page, per_page=per_page)
    total_users = db.get_total_users()
    total_pages = (total_users + per_page - 1) // per_page
    
    text = f"👥 <b>Пользователи</b> (стр. {page + 1}/{total_pages})\n\n"
    
    for user in users:
        user_id = user['user_id']
        username = user['username'] or 'Нет'
        balance = user['balance']
        proxy_count = db.get_proxy_count(user_id)
        
        text += (
            f"ID: <code>{user_id}</code>\n"
            f"@{username} | 💰 {balance:.2f}₽ | 📋 {proxy_count} шт.\n\n"
        )
    
    keyboard = []
    
    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data='admin_users_prev'))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data='admin_users_page'))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data='admin_users_next'))
    keyboard.append(nav_row)
    
    keyboard.append([
        InlineKeyboardButton("🔍 Найти пользователя", callback_data='admin_find_user'),
        InlineKeyboardButton("➕ Добавить баланс", callback_data='admin_add_balance')
    ])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')])
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_balances_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Управление балансами - выбор пользователя"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    page = context.user_data.get('admin_balance_users_page', 0)
    per_page = 8
    
    users = db.get_all_users(page=page, per_page=per_page)
    total_users = db.get_total_users()
    total_pages = (total_users + per_page - 1) // per_page
    
    text = (
        f"💰 <b>Управление балансами</b>\n"
        f"Стр. {page + 1}/{total_pages}\n\n"
        f"Выберите пользователя:"
    )
    
    keyboard = []
    
    # Кнопки пользователей - по 2 в ряд
    for i in range(0, len(users), 2):
        row = []
        for j in range(2):
            if i + j < len(users):
                user = users[i + j]
                user_id = user['user_id']
                username = user['username'] or f"ID{user_id}"
                balance = user['balance']
                
                # Короткое имя для кнопки
                btn_text = f"@{username[:12]}" if user['username'] else f"ID{user_id}"
                btn_text += f" ({balance:.0f}₽)"
                
                row.append(InlineKeyboardButton(
                    btn_text,
                    callback_data=f'admin_balance_select_{user_id}'
                ))
        keyboard.append(row)
    
    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data='admin_balance_users_prev'))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data='admin_balance_users_page'))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data='admin_balance_users_next'))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')])
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_proxies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Список всех прокси"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    page = context.user_data.get('admin_proxies_page', 0)
    per_page = 5
    
    proxies = db.get_all_proxies(page=page, per_page=per_page)
    total_proxies = db.get_total_proxies()
    total_pages = (total_proxies + per_page - 1) // per_page
    
    text = f"📋 <b>Все прокси</b> (стр. {page + 1}/{total_pages})\n\n"
    
    for proxy in proxies:
        user_id = proxy['user_id']
        ip = proxy['ip']
        port = proxy['port']
        service_type = "📱 Прокси" if proxy.get('service_type') == 'proxy' else "🌐 VPN"
        created = proxy['created_at'][:10]
        
        text += (
            f"{service_type} | User: <code>{user_id}</code>\n"
            f"<code>{ip}:{port}</code> | {created}\n\n"
        )
    
    keyboard = []
    
    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data='admin_proxies_prev'))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data='admin_proxies_page'))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data='admin_proxies_next'))
    keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')])
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_transactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """История транзакций"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    page = context.user_data.get('admin_transactions_page', 0)
    per_page = 10
    
    transactions = db.get_all_transactions(page=page, per_page=per_page)
    total_transactions = db.get_total_transactions()
    total_pages = (total_transactions + per_page - 1) // per_page
    
    text = f"💸 <b>Транзакции</b> (стр. {page + 1}/{total_pages})\n\n"
    
    for tx in transactions:
        user_id = tx['user_id']
        amount = tx['amount']
        tx_type = tx['type']
        desc = tx['description']
        created = tx['created_at'][:16]
        
        emoji = "➕" if amount > 0 else "➖"
        text += (
            f"{emoji} <code>{user_id}</code> | {amount:+.2f}₽\n"
            f"{desc} | {created}\n\n"
        )
    
    keyboard = []
    
    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data='admin_transactions_prev'))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data='admin_transactions_page'))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data='admin_transactions_next'))
    keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')])
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка сообщений"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    text = (
        "📢 <b>Рассылка</b>\n\n"
        "Отправьте сообщение для рассылки.\n\n"
        "✅ Поддерживается:\n"
        "• Премиум эмодзи 🌟\n"
        "• HTML форматирование\n"
        "• Markdown форматирование\n"
        "• Жирный, курсив, подчеркнутый текст\n"
        "• Ссылки и кнопки\n"
        "• Картинки, видео, файлы\n\n"
        "<i>Для отмены нажмите кнопку ниже</i>"
    )
    
    context.user_data['waiting_for'] = 'broadcast_message'
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='admin_menu')]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_cleanup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очистка данных"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    text = (
        "🗑 <b>Очистка данных</b>\n\n"
        "⚠️ Внимание! Эти действия необратимы!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗑 Очистить временные данные", callback_data='admin_cleanup_temp')],
        [InlineKeyboardButton("🗑 Удалить старые транзакции", callback_data='admin_cleanup_transactions')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')]
    ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для админ-панели"""
    query = update.callback_query
    data = query.data
    
    if not is_admin(update.effective_user.id):
        await query.answer("❌ Нет доступа", show_alert=True)
        return
    
    await query.answer()
    
    # Навигация
    if data == 'admin_menu':
        await admin_handler(update, context)
    elif data == 'admin_stats':
        await admin_stats_handler(update, context)
    elif data == 'admin_users':
        context.user_data['admin_users_page'] = 0
        await admin_users_handler(update, context)
    elif data == 'admin_users_prev':
        context.user_data['admin_users_page'] = max(0, context.user_data.get('admin_users_page', 0) - 1)
        await admin_users_handler(update, context)
    elif data == 'admin_users_next':
        context.user_data['admin_users_page'] = context.user_data.get('admin_users_page', 0) + 1
        await admin_users_handler(update, context)
    elif data == 'admin_balances':
        context.user_data['admin_balance_users_page'] = 0
        await admin_balances_handler(update, context)
    elif data == 'admin_balance_users_prev':
        context.user_data['admin_balance_users_page'] = max(0, context.user_data.get('admin_balance_users_page', 0) - 1)
        await admin_balances_handler(update, context)
    elif data == 'admin_balance_users_next':
        context.user_data['admin_balance_users_page'] = context.user_data.get('admin_balance_users_page', 0) + 1
        await admin_balances_handler(update, context)
    elif data.startswith('admin_balance_select_'):
        user_id = int(data.split('_')[-1])
        context.user_data['selected_user_id'] = user_id
        await admin_balance_action_handler(update, context, user_id)
    elif data.startswith('admin_balance_action_'):
        action = data.split('_')[-1]
        user_id = context.user_data.get('selected_user_id')
        if user_id:
            await admin_balance_input_handler(update, context, user_id, action)
    elif data == 'admin_proxies':
        context.user_data['admin_proxies_page'] = 0
        await admin_proxies_handler(update, context)
    elif data == 'admin_proxies_prev':
        context.user_data['admin_proxies_page'] = max(0, context.user_data.get('admin_proxies_page', 0) - 1)
        await admin_proxies_handler(update, context)
    elif data == 'admin_proxies_next':
        context.user_data['admin_proxies_page'] = context.user_data.get('admin_proxies_page', 0) + 1
        await admin_proxies_handler(update, context)
    elif data == 'admin_transactions':
        context.user_data['admin_transactions_page'] = 0
        await admin_transactions_handler(update, context)
    elif data == 'admin_transactions_prev':
        context.user_data['admin_transactions_page'] = max(0, context.user_data.get('admin_transactions_page', 0) - 1)
        await admin_transactions_handler(update, context)
    elif data == 'admin_transactions_next':
        context.user_data['admin_transactions_page'] = context.user_data.get('admin_transactions_page', 0) + 1
        await admin_transactions_handler(update, context)
    elif data == 'admin_broadcast':
        await admin_broadcast_handler(update, context)
    elif data == 'admin_cleanup':
        await admin_cleanup_handler(update, context)
    elif data == 'admin_cleanup_temp':
        count = db.cleanup_temp_data()
        await query.message.edit_text(
            f"✅ Очищено {count} записей временных данных",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')]]),
            parse_mode='HTML'
        )
    elif data == 'admin_cleanup_transactions':
        count = db.cleanup_old_transactions(days=90)
        await query.message.edit_text(
            f"✅ Удалено {count} старых транзакций",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='admin_menu')]]),
            parse_mode='HTML'
        )
    elif data == 'admin_close':
        await query.message.delete()


async def admin_balance_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Выбор действия с балансом пользователя"""
    query = update.callback_query
    
    user = db.get_user(user_id)
    if not user:
        await query.message.edit_text(
            "❌ Пользователь не найден",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='admin_balances')]]),
            parse_mode='HTML'
        )
        return
    
    username = user['username'] or f"ID{user_id}"
    balance = user['balance']
    
    text = (
        f"💰 <b>Управление балансом</b>\n\n"
        f"Пользователь: @{username}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Текущий баланс: <b>{balance:.2f} ₽</b>\n\n"
        f"Выберите действие:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить", callback_data='admin_balance_action_add'),
            InlineKeyboardButton("➖ Списать", callback_data='admin_balance_action_subtract')
        ],
        [InlineKeyboardButton("🔄 Установить", callback_data='admin_balance_action_set')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_balances')]
    ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_balance_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, action: str) -> None:
    """Запрос суммы для операции с балансом"""
    query = update.callback_query
    
    user = db.get_user(user_id)
    username = user['username'] or f"ID{user_id}"
    balance = user['balance']
    
    action_text = {
        'add': '➕ Добавить баланс',
        'subtract': '➖ Списать баланс',
        'set': '🔄 Установить баланс'
    }
    
    text = (
        f"{action_text.get(action, 'Операция')}\n\n"
        f"Пользователь: @{username}\n"
        f"Текущий баланс: <b>{balance:.2f} ₽</b>\n\n"
        f"Отправьте сумму числом:"
    )
    
    context.user_data['waiting_for'] = f'admin_balance_{action}'
    context.user_data['selected_user_id'] = user_id
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='admin_balances')]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений для админа"""
    if not is_admin(update.effective_user.id):
        return
    
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for == 'broadcast_message':
        # Рассылка с поддержкой всех форматов и премиум эмодзи
        users = db.get_all_users_ids()
        success = 0
        failed = 0
        
        status_msg = await update.message.reply_text(
            f"📢 Рассылка началась...\n\n"
            f"Всего пользователей: {len(users)}"
        )
        
        # Копируем сообщение со всеми форматами, эмодзи и entities
        for user_id in users:
            try:
                await update.message.copy(chat_id=user_id)
                success += 1
            except Exception:
                failed += 1
        
        context.user_data.pop('waiting_for', None)
        
        await status_msg.edit_text(
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"Успешно: {success}\n"
            f"Ошибок: {failed}",
            parse_mode='HTML'
        )
    
    elif waiting_for == 'admin_balance_add':
        try:
            amount = float(update.message.text)
            user_id = context.user_data.get('selected_user_id')
            
            db.add_balance(user_id, amount)
            context.user_data.pop('waiting_for', None)
            
            new_balance = db.get_balance(user_id)
            await update.message.reply_text(
                f"✅ Добавлено {amount:.2f}₽\n"
                f"Новый баланс: {new_balance:.2f}₽",
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    elif waiting_for == 'admin_balance_subtract':
        try:
            amount = float(update.message.text)
            user_id = context.user_data.get('selected_user_id')
            
            if db.subtract_balance(user_id, amount):
                context.user_data.pop('waiting_for', None)
                new_balance = db.get_balance(user_id)
                await update.message.reply_text(
                    f"✅ Списано {amount:.2f}₽\n"
                    f"Новый баланс: {new_balance:.2f}₽",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("❌ Недостаточно средств")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    elif waiting_for == 'admin_balance_set':
        try:
            amount = float(update.message.text)
            user_id = context.user_data.get('selected_user_id')
            
            db.set_balance(user_id, amount)
            context.user_data.pop('waiting_for', None)
            
            await update.message.reply_text(
                f"✅ Установлен баланс {amount:.2f}₽",
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
