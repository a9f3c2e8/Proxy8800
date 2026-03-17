"""Клиент Platega.io для приёма платежей"""
import uuid
import aiohttp
import logging
from typing import Optional, Dict

from core.config import PLATEGA_MERCHANT_ID, PLATEGA_API_KEY

logger = logging.getLogger(__name__)

BASE_URL = "https://app.platega.io"


async def create_payment(amount: float, user_id: int, payment_method: int = 2) -> Optional[Dict]:
    """Создать платёж в Platega.io
    
    payment_method: 2=СБП/QR, 10=CardRu/МИР, 12=International
    """
    transaction_id = str(uuid.uuid4())
    
    headers = {
        "Content-Type": "application/json",
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_API_KEY,
    }
    
    body = {
        "paymentMethod": payment_method,
        "id": transaction_id,
        "paymentDetails": {
            "amount": int(amount),
            "currency": "RUB"
        },
        "description": f"8800.life пополнение #{user_id}",
        "payload": str(user_id),
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/transaction/process",
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("redirect"):
                    logger.info(f"Платёж создан: {transaction_id} на {amount}₽ для {user_id}")
                    return {
                        "transaction_id": data.get("transactionId", transaction_id),
                        "redirect": data["redirect"],
                        "status": data.get("status", "PENDING"),
                        "amount": amount,
                    }
                else:
                    logger.error(f"Platega error {resp.status}: {data}")
                    return None
    except Exception as e:
        logger.error(f"Platega request error: {e}")
        return None


async def check_payment(transaction_id: str) -> Optional[str]:
    """Проверить статус платежа. Возвращает статус: PENDING/CONFIRMED/EXPIRED/CANCELED/FAILED"""
    headers = {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_API_KEY,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/transaction/{transaction_id}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("status")
                else:
                    logger.error(f"Platega check error {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Platega check error: {e}")
        return None
