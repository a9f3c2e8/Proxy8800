"""Сервер подписок VPN — отдаёт персональные VLESS ключи + пуш на Amsterdam"""
import asyncio
import base64
import logging
import aiohttp
from aiohttp import web
from core.database import db

logger = logging.getLogger(__name__)

# VLESS параметры
VLESS_SERVER = "8800.life"
VLESS_PORT = 2053
VLESS_PARAMS = (
    "encryption=none"
    "&flow=xtls-rprx-vision"
    "&security=reality"
    "&sni=www.google.com"
    "&fp=safari"
    "&pbk=1_D1eK_sMIOFkKmnYp55ucN7gZsrVuNgVuM9bnBES2c"
    "&sid=abcd1234"
    "&type=tcp"
)

# Amsterdam sub-server (через nginx на 8080)
AMS_SUB_URL = "http://8800.life:8080"
AMS_API_SECRET = "8800life-sync-key"


def build_vless_uri(uuid: str, name: str = "%F0%9F%87%B3%F0%9F%87%B1%20NL%20%7C%20TCP") -> str:
    return f"vless://{uuid}@{VLESS_SERVER}:{VLESS_PORT}?{VLESS_PARAMS}#{name}"


async def push_vpn_token(token: str, uuid: str):
    """Отправить token+uuid на амстердамский sub-server"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{AMS_SUB_URL}/api/push-token",
                json={"token": token, "uuid": uuid},
                headers={"Authorization": f"Bearer {AMS_API_SECRET}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                result = await resp.text()
                logger.info(f"Push token to AMS: {resp.status} {result}")
    except Exception as e:
        logger.error(f"Failed to push token to AMS: {e}")


async def push_all_tokens():
    """Отправить все токены на амстердамский sub-server"""
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT token, uuid FROM vpn_keys")
        rows = cursor.fetchall()
        conn.close()
        tokens = {row["token"]: row["uuid"] for row in rows}
        if not tokens:
            return
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{AMS_SUB_URL}/api/push-all",
                json={"tokens": tokens},
                headers={"Authorization": f"Bearer {AMS_API_SECRET}"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                result = await resp.text()
                logger.info(f"Sync tokens to AMS: {resp.status} {result}")
    except Exception as e:
        logger.error(f"Failed to sync tokens to AMS: {e}")


async def periodic_sync():
    """Фоновая задача — синхронизация токенов каждые 60 сек"""
    while True:
        await asyncio.sleep(60)
        await push_all_tokens()


async def handle_sub(request: web.Request) -> web.Response:
    token = request.match_info.get("token", "")
    if not token:
        return web.Response(status=404, text="not found")
    vpn_key = db.get_vpn_key_by_token(token)
    if not vpn_key:
        return web.Response(status=404, text="not found")
    uri = build_vless_uri(vpn_key["uuid"])
    b64 = base64.b64encode(uri.encode()).decode()
    return web.Response(
        text=b64,
        content_type="text/plain",
        headers={
            "Profile-Title": "8800 connection's",
            "Profile-Update-Interval": "1",
            "Subscription-Userinfo": "upload=0; download=0; total=0; expire=0",
            "Support-Url": "https://t.me/connections8800",
            "Profile-Web-Page-Url": "https://t.me/connections8800",
            "Cache-Control": "no-cache",
        },
    )


async def handle_uuids(request: web.Request) -> web.Response:
    uuids = db.get_all_vpn_uuids()
    import json
    return web.Response(
        text=json.dumps({"clients": [{"id": u, "flow": "xtls-rprx-vision"} for u in uuids]}),
        content_type="application/json",
    )


def create_sub_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/sub/{token}", handle_sub)
    app.router.add_get("/api/uuids", handle_uuids)
    return app


async def start_sub_server(port: int = 8888):
    app = create_sub_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Subscription server started on port {port}")
    return runner
