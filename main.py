"""Главный файл запуска бота"""
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from core.config import BOT_TOKEN
from handlers import (
    start_handler,
    check_sub_handler,
    show_vpn_sub_handler,
    show_vpn_key_handler,
    balance_handler,
    my_proxies_handler,
    view_proxy_handler,
    view_vpn_handler,
    proxy_page_handler,
    buy_proxy_handler,
    help_handler,
    profile_handler,
    support_handler,
    callback_handler,
    message_handler,
    topup_handler,
    topup_amount_handler,
    topup_custom_handler,
    topup_method_handler,
    topup_check_handler,
)
from handlers.admin import (
    admin_handler,
    admin_callback_handler,
    admin_message_handler,
    is_admin
)
from services.subscription import start_sub_server

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Роутер для текстовых сообщений"""
    if is_admin(update.effective_user.id) and context.user_data.get('waiting_for', '').startswith('admin_'):
        await admin_message_handler(update, context)
    elif is_admin(update.effective_user.id) and context.user_data.get('waiting_for') == 'broadcast_message':
        await admin_message_handler(update, context)
    else:
        await message_handler(update, context)


async def post_init(application: Application) -> None:
    """Запуск subscription сервера после инициализации бота"""
    await start_sub_server(port=8888)


def setup_handlers(application: Application) -> None:
    """Регистрация всех обработчиков"""
    
    # Админ команды
    application.add_handler(CommandHandler("admin", admin_handler))
    
    # Команды
    application.add_handler(CommandHandler("start", start_handler))
    
    # Callback обработчики
    application.add_handler(CallbackQueryHandler(check_sub_handler, pattern='^check_sub$'))
    application.add_handler(CallbackQueryHandler(show_vpn_sub_handler, pattern='^show_vpn_sub$'))
    application.add_handler(CallbackQueryHandler(show_vpn_key_handler, pattern='^show_vpn_key_'))
    application.add_handler(CallbackQueryHandler(start_handler, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(balance_handler, pattern='^balance$'))
    application.add_handler(CallbackQueryHandler(my_proxies_handler, pattern='^my_proxies$'))
    application.add_handler(CallbackQueryHandler(proxy_page_handler, pattern='^proxy_page_'))
    application.add_handler(CallbackQueryHandler(view_proxy_handler, pattern='^view_proxy$'))
    application.add_handler(CallbackQueryHandler(view_vpn_handler, pattern='^view_vpn$'))
    application.add_handler(CallbackQueryHandler(buy_proxy_handler, pattern='^buy_proxy$'))
    application.add_handler(CallbackQueryHandler(help_handler, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(profile_handler, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(support_handler, pattern='^support$'))
    
    # Платежи (topup)
    application.add_handler(CallbackQueryHandler(topup_handler, pattern='^topup$'))
    application.add_handler(CallbackQueryHandler(topup_amount_handler, pattern='^topup_amt_'))
    application.add_handler(CallbackQueryHandler(topup_custom_handler, pattern='^topup_custom$'))
    application.add_handler(CallbackQueryHandler(topup_method_handler, pattern='^topup_pay_'))
    application.add_handler(CallbackQueryHandler(topup_check_handler, pattern='^topup_check$'))
    
    # Админ callback обработчики
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^admin_'))
    
    # Общий callback обработчик для процесса покупки
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))


async def run_bot() -> None:
    """Запуск бота с subscription сервером"""
    logger.info("Запуск бота 8800.life...")
    
    # Сначала запускаем subscription server
    sub_runner = await start_sub_server(port=8888)
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(60)
        .get_updates_connect_timeout(60)
        .get_updates_read_timeout(60)
        .get_updates_write_timeout(60)
        .get_updates_pool_timeout(60)
        .build()
    )
    
    setup_handlers(application)
    
    # Инициализируем с retry
    for attempt in range(10):
        try:
            await application.initialize()
            logger.info("Telegram API connected")
            break
        except Exception as e:
            logger.warning(f"Init attempt {attempt+1} failed: {e}")
            await asyncio.sleep(5)
    
    await application.start()
    
    logger.info("Бот успешно запущен!")
    
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    
    # Ждём бесконечно
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await sub_runner.cleanup()


def main() -> None:
    """Запуск бота"""
    asyncio.run(run_bot())


if __name__ == '__main__':
    main()
