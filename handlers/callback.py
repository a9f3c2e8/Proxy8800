"""Обработчик callback запросов — покупка прокси/VPN"""
import logging
import os
import time
import random
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import db
from keyboards import periods_keyboard, back_to_main_keyboard
from core.config import PERIODS, PROXY_DOMAIN, PROXY_PORT

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Роутер callback запросов"""
    query = update.callback_query
    data = query.data

    # Антиспам
    last = context.user_data.get('last_cb', 0)
    now = time.time()
    if now - last < 0.5:
        await query.answer("⏳", show_alert=False)
        return
    context.user_data['last_cb'] = now
    await query.answer()

    if data == 'server_unavailable':
        await query.answer("🔒 Сервер временно недоступен", show_alert=True)
    elif data == 'buy_service_proxy':
        await _service_proxy(update, context)
    elif data == 'buy_service_vpn':
        await _service_vpn(update, context)
    elif data == 'vpn_unavailable':
        await query.answer("🔴 VPN временно недоступен", show_alert=True)
    elif data.startswith('buy_period_'):
        await _period_selected(update, context, data)
    elif data == 'buy_confirm':
        await _order_confirm(update, context)


async def _service_proxy(update, context):
    q = update.callback_query
    uid = update.effective_user.id
    d = {'service_type': 'proxy', 'buy_country': 'nl'}
    context.user_data.update(d)
    db.set_user_data_batch(uid, d)
    await q.message.edit_caption(
        caption="📱 <b>Прокси для Telegram</b>\n\n🇳🇱 Сервер: Нидерланды\n\n<blockquote><i>Выберите период</i></blockquote>",
        reply_markup=periods_keyboard(), parse_mode='HTML')


async def _service_vpn(update, context):
    q = update.callback_query
    uid = update.effective_user.id
    d = {'service_type': 'vpn', 'buy_country': 'nl'}
    context.user_data.update(d)
    db.set_user_data_batch(uid, d)
    from keyboards import vpn_periods_keyboard
    await q.message.edit_caption(
        caption="🌐 <b>VPN для всех сервисов</b>\n\n<blockquote><i>Выберите период</i></blockquote>",
        reply_markup=vpn_periods_keyboard(), parse_mode='HTML')


async def _period_selected(update, context, data):
    q = update.callback_query
    uid = update.effective_user.id
    period = data.split('_')[2]
    stype = context.user_data.get('service_type') or db.get_user_data(uid, 'service_type', 'proxy')
    context.user_data.update({'buy_period': period, 'buy_quantity': 1, 'service_type': stype})
    db.set_user_data(uid, 'buy_period', period)
    db.set_user_data(uid, 'buy_quantity', 1)

    days = int(period)
    ppd = (99.0 if stype == 'vpn' else 50.0) / 30
    amount = ppd * days
    context.user_data['buy_amount'] = amount
    db.set_user_data(uid, 'buy_amount', amount)

    balance = db.get_balance(uid)
    label = "🌐 VPN" if stype == 'vpn' else "📱 Прокси"

    if balance >= amount:
        text = (f"💳 <b>Подтверждение оплаты</b>\n\nСервис: {label}\n"
                f"Период: {PERIODS.get(period)}\n\n"
                f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n💳 Баланс: <b>{balance:.2f} ₽</b>")
        kb = [[InlineKeyboardButton("✅ Оплатить", callback_data='buy_confirm')],
              [InlineKeyboardButton("❌ Отменить", callback_data='main_menu')]]
    else:
        text = (f"❌ <b>Недостаточно средств</b>\n\nСервис: {label}\n"
                f"Период: {PERIODS.get(period)}\n\n"
                f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n💳 Баланс: <b>{balance:.2f} ₽</b>")
        kb = [[InlineKeyboardButton("💳 Пополнить", callback_data='balance')],
              [InlineKeyboardButton("◀️ Меню", callback_data='main_menu')]]

    await q.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')


async def _order_confirm(update, context):
    q = update.callback_query
    uid = update.effective_user.id
    try:
        stype = context.user_data.get('service_type') or db.get_user_data(uid, 'service_type', 'proxy')
        period = context.user_data.get('buy_period') or db.get_user_data(uid, 'buy_period', '30')
        amount = float(context.user_data.get('buy_amount') or db.get_user_data(uid, 'buy_amount', 0))

        if not db.subtract_balance(uid, amount):
            bal = db.get_balance(uid)
            await q.message.edit_caption(
                caption=f"❌ <b>Недостаточно средств</b>\n\nНужно: {amount:.2f} ₽\nБаланс: {bal:.2f} ₽",
                reply_markup=back_to_main_keyboard(), parse_mode='HTML')
            return

        pid = hashlib.md5(f"{uid}:{random.randint(1000,9999)}".encode()).hexdigest()[:8]

        if stype == 'proxy':
            secret = os.getenv('MTPROTO_SECRET', '')
            proxy_data = {'id': pid, 'ip': PROXY_DOMAIN, 'port': PROXY_PORT,
                          'username': secret, 'password': '', 'country': 'nl',
                          'period': period, 'service_type': 'proxy'}
            db.assign_proxy(uid, pid, proxy_data)
            tg_link = f"https://t.me/proxy?server={PROXY_DOMAIN}&port={PROXY_PORT}&secret={secret}"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Подключить к Telegram", url=tg_link)],
                [InlineKeyboardButton("◀️ Меню", callback_data='main_menu')]])
        else:
            import uuid as uuid_mod
            vless_uuid = str(uuid_mod.uuid4())
            vpn_token = hashlib.md5(f"{uid}:{vless_uuid}:{random.randint(1000,9999)}".encode()).hexdigest()[:16]
            db.create_vpn_key(uid, vless_uuid, vpn_token)
            proxy_data = {'id': pid, 'ip': PROXY_DOMAIN, 'port': PROXY_PORT,
                          'username': vless_uuid, 'password': vpn_token, 'country': 'nl',
                          'period': period, 'service_type': 'vpn'}
            db.assign_proxy(uid, pid, proxy_data)
            logger.info(f"VPN key: token={vpn_token} uuid={vless_uuid[:8]}")
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Подключить VPN", callback_data=f'show_vpn_key_{vpn_token}')],
                [InlineKeyboardButton("◀️ Меню", callback_data='main_menu')]])

        bal = db.get_balance(uid)
        logger.info(f"User {uid} bought {stype} for {amount:.2f}")
        await q.message.edit_caption(
            caption=f"✅ <b>Заказ создан!</b>\n\nСписано: {amount:.2f} ₽\nБаланс: {bal:.2f} ₽",
            reply_markup=kb, parse_mode='HTML')

        # Добивы
        from handlers.followup import schedule_followups
        await schedule_followups(context.application, uid, "purchase")

    except Exception as e:
        logger.error(f"Order error {uid}: {e}", exc_info=True)
        try:
            await q.message.edit_caption(
                caption=f"❌ <b>Ошибка</b>\n\n<code>{e}</code>",
                reply_markup=back_to_main_keyboard(), parse_mode='HTML')
        except Exception:
            pass
