"""WebSocket чат поддержки"""
import json
import logging
import asyncio
import time
from typing import Dict, List, Optional
from aiohttp import web, WSMsgType
from core.config import ADMIN_ID

logger = logging.getLogger(__name__)


class ChatServer:
    """WebSocket сервер для чата поддержки в миниаппе"""

    def __init__(self, bot_app=None):
        self.bot_app = bot_app  # telegram Application для уведомлений админу
        # user_id -> websocket
        self.user_connections: Dict[int, web.WebSocketResponse] = {}
        # admin connections (admin can have multiple)
        self.admin_connections: List[web.WebSocketResponse] = []
        # chat history: user_id -> list of messages
        self.history: Dict[int, List[dict]] = {}
        self.MAX_HISTORY = 100

    def _add_to_history(self, user_id: int, text: str, from_user: bool, image: str = None):
        if user_id not in self.history:
            self.history[user_id] = []
        msg = {
            'text': text,
            'from_user': from_user,
            'time': time.strftime('%H:%M'),
            'ts': time.time(),
            'image': image
        }
        self.history[user_id].append(msg)
        if len(self.history[user_id]) > self.MAX_HISTORY:
            self.history[user_id] = self.history[user_id][-self.MAX_HISTORY:]
        return msg

    async def handle_user_ws(self, request: web.Request) -> web.WebSocketResponse:
        """WebSocket для пользователя миниаппа"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        user_id = int(request.query.get('user_id', 0))
        name = request.query.get('name', 'User')

        if not user_id:
            await ws.close(message=b'no user_id')
            return ws

        # Register
        old_ws = self.user_connections.get(user_id)
        if old_ws and not old_ws.closed:
            try:
                await old_ws.close()
            except Exception:
                pass
        self.user_connections[user_id] = ws
        logger.info(f"Chat: user {user_id} ({name}) connected")

        # Send history
        if user_id in self.history:
            await ws.send_json({
                'type': 'history',
                'messages': self.history[user_id][-50:]
            })

        # Notify admin
        await self._notify_admins({
            'type': 'user_online',
            'user_id': user_id,
            'name': name
        })

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get('type') == 'message':
                            text = data.get('text', '').strip()
                            image = data.get('image')  # base64 image
                            if not text and not image:
                                continue
                            m = self._add_to_history(user_id, text, from_user=True, image=image)
                            # Forward to admin
                            await self._notify_admins({
                                'type': 'user_message',
                                'user_id': user_id,
                                'name': name,
                                'text': text,
                                'time': m['time'],
                                'image': image
                            })
                            # Also notify admin via Telegram if no admin WS connected
                            if not self.admin_connections and self.bot_app:
                                try:
                                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                                    kb = InlineKeyboardMarkup([[
                                        InlineKeyboardButton("💬 Ответить", callback_data=f'admin_chat_reply_{user_id}')
                                    ]])
                                    msg_text = text or '📷 Фото'
                                    await self.bot_app.bot.send_message(
                                        ADMIN_ID,
                                        f"💬 <b>Чат поддержки</b>\n\n"
                                        f"От: {name} (ID: <code>{user_id}</code>)\n"
                                        f"Сообщение: {msg_text}",
                                        parse_mode='HTML',
                                        reply_markup=kb
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to notify admin via TG: {e}")
                    except json.JSONDecodeError:
                        pass
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        except Exception as e:
            logger.error(f"Chat WS error for {user_id}: {e}")
        finally:
            if self.user_connections.get(user_id) is ws:
                del self.user_connections[user_id]
            logger.info(f"Chat: user {user_id} disconnected")

        return ws

    async def handle_admin_ws(self, request: web.Request) -> web.WebSocketResponse:
        """WebSocket для админа — видит все чаты"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Simple auth via query param
        token = request.query.get('token', '')
        if token != 'admin8800secret':
            await ws.close(message=b'unauthorized')
            return ws

        self.admin_connections.append(ws)
        logger.info("Chat: admin connected")

        # Send all active chats summary
        chats = []
        for uid, msgs in self.history.items():
            if msgs:
                last = msgs[-1]
                chats.append({
                    'user_id': uid,
                    'last_message': last['text'][:50],
                    'last_time': last['time'],
                    'unread': sum(1 for m in msgs if m['from_user'])
                })
        await ws.send_json({'type': 'chats_list', 'chats': chats})

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get('type') == 'reply':
                            target_uid = int(data.get('user_id', 0))
                            text = data.get('text', '').strip()
                            image = data.get('image')
                            if not target_uid or (not text and not image):
                                continue
                            m = self._add_to_history(target_uid, text, from_user=False, image=image)
                            user_ws = self.user_connections.get(target_uid)
                            if user_ws and not user_ws.closed:
                                await user_ws.send_json({
                                    'type': 'message',
                                    'text': text,
                                    'time': m['time'],
                                    'image': image
                                })
                        elif data.get('type') == 'get_history':
                            target_uid = int(data.get('user_id', 0))
                            msgs = self.history.get(target_uid, [])
                            await ws.send_json({
                                'type': 'chat_history',
                                'user_id': target_uid,
                                'messages': msgs[-50:]
                            })
                    except (json.JSONDecodeError, ValueError):
                        pass
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        except Exception as e:
            logger.error(f"Admin WS error: {e}")
        finally:
            if ws in self.admin_connections:
                self.admin_connections.remove(ws)
            logger.info("Chat: admin disconnected")

        return ws

    async def _notify_admins(self, data: dict):
        """Send to all connected admin websockets"""
        dead = []
        for ws in self.admin_connections:
            if ws.closed:
                dead.append(ws)
                continue
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.admin_connections:
                self.admin_connections.remove(ws)

    async def admin_reply_from_bot(self, user_id: int, text: str):
        """Админ отвечает через Telegram бота (команда /reply)"""
        m = self._add_to_history(user_id, text, from_user=False)
        user_ws = self.user_connections.get(user_id)
        if user_ws and not user_ws.closed:
            await user_ws.send_json({
                'type': 'message',
                'text': text,
                'time': m['time']
            })
            return True
        return False


# Singleton
chat_server = ChatServer()


async def start_chat_server(port: int = 8888, bot_app=None):
    """Запуск WebSocket сервера для чата"""
    chat_server.bot_app = bot_app

    app = web.Application()
    app.router.add_get('/ws/chat', chat_server.handle_user_ws)
    app.router.add_get('/ws/admin', chat_server.handle_admin_ws)

    # Health check
    async def health(request):
        return web.Response(text='ok')
    app.router.add_get('/health', health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Chat WebSocket server started on port {port}")
    return runner
