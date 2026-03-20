"""Сервер подписок VPN — отдаёт персональные VLESS ключи + синхронизация с Amsterdam XRay"""
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

# Amsterdam sync URL (через SSH туннель, Amsterdam дёргает localhost:9888)
AMS_SYNC_URL = "http://8800.life:8080/api/trigger-sync"
AMS_API_SECRET = "8800life-sync-key"


def build_vless_uri(uuid: str, name: str = "%F0%9F%87%B3%F0%9F%87%B1%20NL%20%7C%20TCP") -> str:
    return f"vless://{uuid}@{VLESS_SERVER}:{VLESS_PORT}?{VLESS_PARAMS}#{name}"


async def push_vpn_token(token: str, uuid: str):
    """Уведомить Amsterdam о новом токене — триггерим sync"""
    logger.info(f"New VPN key: token={token[:8]}... uuid={uuid[:8]}...")
    # Синхронизация произойдёт через periodic_sync или по запросу /api/uuids


async def handle_sub(request: web.Request) -> web.Response:
    """Отдать подписку по токену"""
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
    """Отдать все UUID для XRay конфига"""
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
