"""
Box IM Python SDK
=================

完整规范的Box IM即时通讯Python SDK，支持用户登录、消息收发、群组管理等功能。

注意：此版本已根据后端真实API接口进行修正。

Copyright (c) 2026 归鸿

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "归鸿"
__copyright__ = "Copyright (c) 2026 归鸿"
__license__ = "MIT"
__description__ = "Box IM Python SDK - 即时通讯机器人开发工具包"

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, TypeVar

import aiohttp

# ============================================================================
# 类型定义和枚举
# ============================================================================

T = TypeVar('T')


class MessageType(IntEnum):
    TEXT = 1
    IMAGE = 2
    VOICE = 3
    VIDEO = 4
    FILE = 5
    CARD = 6
    NOTICE = 7
    RECALL = 8
    TIMELINE = 9
    CUSTOM = 100


class TerminalType(IntEnum):
    WEB = 0
    APP = 1
    PC = 2


class SessionType(IntEnum):
    PRIVATE = 0
    GROUP = 1
    SYSTEM = 2


class OnlineStatus(IntEnum):
    OFFLINE = 0
    ONLINE = 1


class ErrorCode(IntEnum):
    SUCCESS = 0
    PARAM_ERROR = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500


class CommandType(IntEnum):
    LOGIN = 1
    LOGOUT = 2
    HEARTBEAT = 3
    PRIVATE_MESSAGE = 4
    GROUP_MESSAGE = 5
    SYSTEM_MESSAGE = 6
    ACK = 7
    ERROR = 8
    USER_STATUS = 9


class GroupRole(IntEnum):
    MEMBER = 0
    ADMIN = 1
    OWNER = 2


class MessageStatus(IntEnum):
    SENDING = 0
    SENT = 1
    DELIVERED = 2
    READ = 3
    FAILED = 4


class ConnectionState(IntEnum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    RECONNECTING = 3


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class FriendRequestStatus(IntEnum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2


class NotificationType(IntEnum):
    FRIEND_REQUEST = 1
    GROUP_INVITE = 2
    SYSTEM = 3


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class User:
    user_id: str
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[OnlineStatus] = None
    terminal: Optional[TerminalType] = None
    last_login_time: Optional[int] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Group:
    group_id: str
    group_name: str
    avatar: Optional[str] = None
    owner_id: Optional[str] = None
    description: Optional[str] = None
    member_count: Optional[int] = None
    max_members: Optional[int] = None
    is_muted: Optional[bool] = None
    is_private: Optional[bool] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupMember:
    user_id: str
    username: str
    group_id: str
    role: GroupRole = GroupRole.MEMBER
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    join_time: Optional[int] = None
    is_muted: Optional[bool] = None


@dataclass
class Session:
    session_id: str
    type: SessionType
    target_id: str
    target_name: Optional[str] = None
    target_avatar: Optional[str] = None
    last_message: Optional[Any] = None
    last_message_time: Optional[int] = None
    unread_count: Optional[int] = None
    is_pinned: Optional[bool] = None
    is_muted: Optional[bool] = None
    is_encrypted: Optional[bool] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    message_id: str
    from_id: str
    to_id: str
    session_type: SessionType
    content_type: MessageType
    content: Any
    timestamp: int
    message_uid: Optional[str] = None
    from_name: Optional[str] = None
    from_avatar: Optional[str] = None
    to_name: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    status: Optional[MessageStatus] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None


@dataclass
class UserLoginResponse:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    user_info: User


@dataclass
class BotConfig:
    api_base_url: str
    ws_url: str
    bot_id: Optional[str] = None
    bot_secret: Optional[str] = None
    auto_reconnect: bool = True
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 10
    heartbeat_interval: float = 30.0
    request_timeout: float = 30.0
    enable_logging: bool = True
    log_level: LogLevel = LogLevel.INFO


@dataclass
class ApiResponse:
    code: int
    message: str
    data: Any
    timestamp: Optional[int] = None


@dataclass
class PaginatedResponse:
    list: List[Any]
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False


@dataclass
class WebSocketPacket:
    cmd: CommandType
    data: Any
    seq: Optional[str] = None
    timestamp: Optional[int] = None


@dataclass
class MessageAck:
    message_id: str
    success: bool
    error: Optional[str] = None


@dataclass
class TypingData:
    user_id: str
    is_typing: bool
    session_id: str


@dataclass
class QueryOptions:
    page: Optional[int] = None
    page_size: Optional[int] = None
    keyword: Optional[str] = None
    sort_by: Optional[str] = None
    order: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FriendRequest:
    request_id: str
    from_id: str
    from_name: Optional[str] = None
    from_avatar: Optional[str] = None
    to_id: Optional[str] = None
    to_name: Optional[str] = None
    to_avatar: Optional[str] = None
    status: FriendRequestStatus = FriendRequestStatus.PENDING
    message: Optional[str] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None


@dataclass
class Notification:
    notification_id: str
    type: NotificationType
    content: Any
    read: bool = False
    create_time: Optional[int] = None


@dataclass
class RetryOptions:
    max_attempts: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 30.0
    should_retry: Optional[Callable[[Exception], bool]] = None


@dataclass
class RateLimitConfig:
    requests_per_second: int = 10
    burst_size: int = 20


@dataclass
class CacheOptions:
    enable_cache: bool = True
    ttl_seconds: int = 300
    max_size: int = 1000


@dataclass
class SDKStats:
    messages_sent: int = 0
    messages_received: int = 0
    connections_established: int = 0
    reconnect_attempts: int = 0
    errors_encountered: int = 0


# ============================================================================
# 日志系统
# ============================================================================


class Logger:
    _instances: Dict[str, 'Logger'] = {}
    _root_logger: Optional[logging.Logger] = None
    
    def __init__(self, name: str):
        self.name = name
        self._logger = self._get_logger(name)
    
    @classmethod
    def _get_logger(cls, name: str) -> logging.Logger:
        if cls._root_logger is None:
            cls._setup_root_logger()
        return logging.getLogger(name)
    
    @classmethod
    def _setup_root_logger(cls):
        logger = logging.getLogger('box_im_sdk')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        cls._root_logger = logger
    
    @classmethod
    def get_instance(cls, name: str) -> 'Logger':
        if name not in cls._instances:
            cls._instances[name] = Logger(name)
        return cls._instances[name]
    
    def debug(self, msg: str, *args):
        self._logger.debug(msg, *args)
    
    def info(self, msg: str, *args):
        self._logger.info(msg, *args)
    
    def warning(self, msg: str, *args):
        self._logger.warning(msg, *args)
    
    def error(self, msg: str, *args, exc_info: Optional[Exception] = None):
        if exc_info:
            self._logger.error(msg, *args, exc_info=True)
        else:
            self._logger.error(msg, *args)


# ============================================================================
# 事件发射器
# ============================================================================


EventHandler = Callable[..., Any]


class BotEventEmitter:
    _instance: Optional['BotEventEmitter'] = None
    
    def __init__(self):
        self._listeners: Dict[str, List[EventHandler]] = {}
        self._once_listeners: Dict[str, List[EventHandler]] = {}
        self._logger = Logger.get_instance('EventEmitter')
    
    @classmethod
    def get_instance(cls) -> 'BotEventEmitter':
        if cls._instance is None:
            cls._instance = BotEventEmitter()
        return cls._instance
    
    def on(self, event: str, handler: EventHandler) -> 'BotEventEmitter':
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)
        return self
    
    def once(self, event: str, handler: EventHandler) -> 'BotEventEmitter':
        if event not in self._once_listeners:
            self._once_listeners[event] = []
        self._once_listeners[event].append(handler)
        return self
    
    def off(self, event: str, handler: Optional[EventHandler] = None) -> 'BotEventEmitter':
        if handler is None:
            self._listeners.pop(event, None)
            self._once_listeners.pop(event, None)
        else:
            if event in self._listeners:
                self._listeners[event] = [h for h in self._listeners[event] if h != handler]
        return self
    
    def emit(self, event: str, *args, **kwargs) -> bool:
        handled = False
        if event in self._listeners:
            for handler in self._listeners[event]:
                self._call_handler(handler, *args, **kwargs)
                handled = True
        if event in self._once_listeners:
            handlers = self._once_listeners.pop(event)
            for handler in handlers:
                self._call_handler(handler, *args, **kwargs)
                handled = True
        return handled
    
    def _call_handler(self, handler: EventHandler, *args, **kwargs):
        try:
            result = handler(*args, **kwargs)
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception as e:
            self._logger.error(f"Error in event handler", exc_info=e)


# ============================================================================
# HTTP客户端
# ============================================================================


class HttpClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = Logger.get_instance('HttpClient')
        self.access_token: Optional[str] = None
        self._default_headers: Dict[str, str] = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        self._session: Optional[aiohttp.ClientSession] = None
    
    def set_access_token(self, token: str) -> None:
        self.access_token = token
    
    def _build_url(self, url: str) -> str:
        if url.startswith(('http://', 'https://')):
            return url
        return self.base_url + '/' + url.lstrip('/')
    
    async def request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        start_time = time.time()
        request_headers = dict(self._default_headers)
        
        if self.access_token:
            request_headers['Authorization'] = f'Bearer {self.access_token}'
        
        full_url = self._build_url(url)
        self.logger.debug(f"HTTP {method} {full_url}")
        
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            
            async with self._session.request(
                method=method,
                url=full_url,
                json=data if method in ('POST', 'PUT', 'PATCH') else None,
                params=params if method in ('GET', 'DELETE') else None,
                headers=request_headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                elapsed = time.time() - start_time
                response_json = await response.json()
                
                if response_json.get('code') not in (0, 200, None):
                    error = Exception(f"{response_json.get('code')}: {response_json.get('message', 'Unknown error')}")
                    self.logger.error(f"Request failed", exc_info=error)
                    raise error
                
                return response_json.get('data') or response_json
            
        except Exception as e:
            self.logger.error(f"HTTP error", exc_info=e)
            raise
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request('GET', url, params=params)
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request('POST', url, data=data)
    
    async def put(self, url: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request('PUT', url, data=data)
    
    async def delete(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request('DELETE', url, params=params)
    
    async def destroy(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# ============================================================================
# WebSocket客户端
# ============================================================================


class WebSocketClient:
    def __init__(
        self,
        url: str,
        auto_reconnect: bool = True,
        reconnect_interval: float = 5.0,
        max_reconnect_attempts: int = 10,
        heartbeat_interval: float = 30.0,
    ):
        self.url = url
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.heartbeat_interval = heartbeat_interval
        
        self.logger = Logger.get_instance('WebSocket')
        self.event_emitter = BotEventEmitter.get_instance()
        
        self._ws = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._reconnect_attempts = 0
        self._access_token: Optional[str] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
    
    def set_access_token(self, token: str) -> None:
        self._access_token = token
    
    @property
    def connection_state(self) -> ConnectionState:
        return self._connection_state
    
    def _set_connection_state(self, state: ConnectionState):
        old_state = self._connection_state
        self._connection_state = state
        if old_state != state:
            self.event_emitter.emit('connection_state_change', old_state, state)
    
    async def connect(self) -> None:
        if self._connection_state == ConnectionState.CONNECTED:
            return
        
        self._set_connection_state(ConnectionState.CONNECTING)
        self.logger.info("Connecting to WebSocket...")
        
        try:
            import websockets
            ws_url = self.url
            if self._access_token:
                ws_url = f"{ws_url}?token={self._access_token}"
            
            self._ws = await websockets.connect(ws_url)
            self._set_connection_state(ConnectionState.CONNECTED)
            self._reconnect_attempts = 0
            
            self.logger.info("WebSocket connected")
            self.event_emitter.emit('connected')
            
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
        except Exception as e:
            self.logger.error("WebSocket connection failed", exc_info=e)
            self._set_connection_state(ConnectionState.DISCONNECTED)
            if self.auto_reconnect:
                self._schedule_reconnect()
            raise
    
    async def _receive_loop(self):
        try:
            while self._connection_state == ConnectionState.CONNECTED and self._ws:
                try:
                    message = await self._ws.recv()
                    data = json.loads(message)
                    self._handle_message(data)
                except websockets.exceptions.ConnectionClosed as e:
                    self.logger.warning("Connection closed", e.code, e.reason)
                    self._handle_disconnect(True)
                    break
                except json.JSONDecodeError as e:
                    self.logger.error("Failed to parse message", exc_info=e)
                except Exception as e:
                    self.logger.error("Error receiving message", exc_info=e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error("Receive loop error", exc_info=e)
            self._handle_disconnect(True)
    
    async def _heartbeat_loop(self):
        try:
            while self._connection_state == ConnectionState.CONNECTED:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeat()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error("Heartbeat loop error", exc_info=e)
    
    async def _send_heartbeat(self):
        if self._connection_state != ConnectionState.CONNECTED:
            return
        try:
            packet = WebSocketPacket(
                cmd=CommandType.HEARTBEAT,
                data={'timestamp': int(time.time() * 1000)},
                timestamp=int(time.time() * 1000)
            )
            await self._send_packet(packet)
        except Exception as e:
            self.logger.error("Failed to send heartbeat", exc_info=e)
    
    def _handle_message(self, data: Dict[str, Any]):
        try:
            cmd = CommandType(data.get('cmd', 0))
            packet_data = data.get('data')
            
            if cmd == CommandType.LOGIN:
                self.event_emitter.emit('login_success')
            elif cmd == CommandType.PRIVATE_MESSAGE:
                self.event_emitter.emit('private_message', packet_data)
                self.event_emitter.emit('message', packet_data)
            elif cmd == CommandType.GROUP_MESSAGE:
                self.event_emitter.emit('group_message', packet_data)
                self.event_emitter.emit('message', packet_data)
            elif cmd == CommandType.SYSTEM_MESSAGE:
                self.event_emitter.emit('system_message', packet_data)
                self.event_emitter.emit('message', packet_data)
            elif cmd == CommandType.USER_STATUS:
                if packet_data.get('status') == OnlineStatus.ONLINE:
                    self.event_emitter.emit('user_online', packet_data)
                else:
                    self.event_emitter.emit('user_offline', packet_data.get('userId'))
            elif cmd == CommandType.ACK:
                self.event_emitter.emit('message_ack', packet_data)
            elif cmd == CommandType.ERROR:
                self.logger.error("Server error", packet_data)
                self.event_emitter.emit('server_error', packet_data)
        except Exception as e:
            self.logger.error("Failed to handle message", exc_info=e)
    
    def _handle_disconnect(self, should_reconnect: bool):
        self._set_connection_state(ConnectionState.DISCONNECTED)
        self._stop_tasks()
        self.event_emitter.emit('disconnected')
        
        if self.auto_reconnect and should_reconnect:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        if self._connection_state == ConnectionState.RECONNECTING:
            return
        self._set_connection_state(ConnectionState.RECONNECTING)
        asyncio.create_task(self._reconnect())
    
    async def _reconnect(self):
        while self._reconnect_attempts < self.max_reconnect_attempts:
            try:
                self._reconnect_attempts += 1
                self.logger.info(f"Reconnecting... (attempt {self._reconnect_attempts})")
                
                delay = self.reconnect_interval * min(self._reconnect_attempts, 5)
                await asyncio.sleep(delay)
                await self.connect()
                return
            except Exception as e:
                self.logger.error("Reconnect failed", exc_info=e)
        
        self.logger.error("Max reconnect attempts reached")
        self._set_connection_state(ConnectionState.DISCONNECTED)
    
    def _stop_tasks(self):
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
    
    async def _send_packet(self, packet: WebSocketPacket) -> None:
        if self._ws and self._connection_state == ConnectionState.CONNECTED:
            try:
                await self._ws.send(json.dumps({
                    'cmd': packet.cmd,
                    'data': packet.data,
                    'seq': packet.seq,
                    'timestamp': packet.timestamp
                }))
            except Exception as e:
                self.logger.error("Failed to send packet", exc_info=e)
                raise
    
    async def send_packet(self, packet: WebSocketPacket) -> Any:
        if self._connection_state != ConnectionState.CONNECTED:
            raise Exception("WebSocket not connected")
        await self._send_packet(packet)
    
    async def close(self) -> None:
        self.auto_reconnect = False
        self._stop_tasks()
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._set_connection_state(ConnectionState.DISCONNECTED)
        self.logger.info("WebSocket closed")
    
    async def destroy(self) -> None:
        await self.close()


# ============================================================================
# 消息管理器
# ============================================================================


class MessageManager:
    def __init__(self, http_client: HttpClient, ws_client: WebSocketClient, user_id: str):
        self.http_client = http_client
        self.ws_client = ws_client
        self.user_id = user_id
        self.logger = Logger.get_instance('MessageManager')
        self.event_emitter = BotEventEmitter.get_instance()
        self._message_cache: Dict[str, Message] = {}
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        self.event_emitter.on('private_message', self._on_message_received)
        self.event_emitter.on('group_message', self._on_message_received)
        self.event_emitter.on('system_message', self._on_message_received)
    
    def _on_message_received(self, message_data: Dict[str, Any]):
        message = self._dict_to_message(message_data)
        self._cache_message(message)
        self.logger.debug("Message received", message.message_id)
    
    def _dict_to_message(self, data: Dict[str, Any]) -> Message:
        return Message(
            message_id=data.get('messageId', str(uuid.uuid4())),
            from_id=data.get('fromId', ''),
            to_id=data.get('toId', ''),
            session_type=SessionType(data.get('sessionType', SessionType.PRIVATE)),
            content_type=MessageType(data.get('contentType', MessageType.TEXT)),
            content=data.get('content'),
            timestamp=data.get('timestamp', int(time.time() * 1000)),
            message_uid=data.get('messageUid'),
            from_name=data.get('fromName'),
            from_avatar=data.get('fromAvatar'),
            to_name=data.get('toName'),
            extra=data.get('extra', {}),
            status=MessageStatus(data.get('status', MessageStatus.SENT)) if data.get('status') else None,
            create_time=data.get('createTime'),
            update_time=data.get('updateTime')
        )
    
    def _cache_message(self, message: Message):
        self._message_cache[message.message_id] = message
        if len(self._message_cache) > 1000:
            keys = list(self._message_cache.keys())
            for key in keys[:100]:
                self._message_cache.pop(key, None)
    
    async def send_private_message(
        self,
        to_id: str,
        content: Any,
        content_type: MessageType = MessageType.TEXT,
    ) -> Message:
        try:
            message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:9]}"
            
            result = await self.http_client.post('/message/private/send', {
                'toId': to_id,
                'content': content,
                'contentType': content_type
            })
            
            message = Message(
                message_id=result.get('messageId', message_id) if result else message_id,
                from_id=self.user_id,
                to_id=to_id,
                session_type=SessionType.PRIVATE,
                content_type=content_type,
                content=content,
                timestamp=int(time.time() * 1000)
            )
            
            self._cache_message(message)
            return message
            
        except Exception as e:
            self.logger.error("Failed to send private message", exc_info=e)
            raise
    
    async def send_group_message(
        self,
        group_id: str,
        content: Any,
        content_type: MessageType = MessageType.TEXT,
    ) -> Message:
        try:
            message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:9]}"
            
            result = await self.http_client.post('/message/group/send', {
                'groupId': group_id,
                'content': content,
                'contentType': content_type
            })
            
            message = Message(
                message_id=result.get('messageId', message_id) if result else message_id,
                from_id=self.user_id,
                to_id=group_id,
                session_type=SessionType.GROUP,
                content_type=content_type,
                content=content,
                timestamp=int(time.time() * 1000)
            )
            
            self._cache_message(message)
            return message
            
        except Exception as e:
            self.logger.error("Failed to send group message", exc_info=e)
            raise
    
    async def recall_private_message(self, message_id: str) -> None:
        try:
            await self.http_client.delete(f'/message/private/recall/{message_id}')
            self.logger.info("Private message recalled", message_id)
        except Exception as e:
            self.logger.error("Failed to recall private message", exc_info=e)
            raise
    
    async def recall_group_message(self, message_id: str) -> None:
        try:
            await self.http_client.delete(f'/message/group/recall/{message_id}')
            self.logger.info("Group message recalled", message_id)
        except Exception as e:
            self.logger.error("Failed to recall group message", exc_info=e)
            raise
    
    async def mark_private_readed(self, friend_id: str, message_id: Optional[str] = None) -> None:
        try:
            params = {'friendId': friend_id}
            if message_id:
                params['messageId'] = message_id
            await self.http_client.put('/message/private/readed', params)
        except Exception as e:
            self.logger.error("Failed to mark private message as read", exc_info=e)
    
    async def mark_group_readed(self, group_id: str, message_id: Optional[str] = None) -> None:
        try:
            params = {'groupId': group_id}
            if message_id:
                params['messageId'] = message_id
            await self.http_client.put('/message/group/readed', params)
        except Exception as e:
            self.logger.error("Failed to mark group message as read", exc_info=e)
    
    async def get_private_history(self, friend_id: str) -> List[Message]:
        try:
            result = await self.http_client.post('/message/private/history', {'friendId': friend_id})
            
            messages = []
            if result and isinstance(result, list):
                for item in result:
                    message = self._dict_to_message(item)
                    self._cache_message(message)
                    messages.append(message)
            
            return messages
        except Exception as e:
            self.logger.error("Failed to get private message history", exc_info=e)
            raise
    
    async def get_group_history(self, group_id: str) -> List[Message]:
        try:
            result = await self.http_client.post('/message/group/history', {'groupId': group_id})
            
            messages = []
            if result and isinstance(result, list):
                for item in result:
                    message = self._dict_to_message(item)
                    self._cache_message(message)
                    messages.append(message)
            
            return messages
        except Exception as e:
            self.logger.error("Failed to get group message history", exc_info=e)
            raise
    
    def on_message(self, handler: Callable[[Message], Any]) -> None:
        self.event_emitter.on('message', lambda data: handler(self._dict_to_message(data)))
    
    def on_private_message(self, handler: Callable[[Message], Any]) -> None:
        self.event_emitter.on('private_message', lambda data: handler(self._dict_to_message(data)))
    
    def on_group_message(self, handler: Callable[[Message], Any]) -> None:
        self.event_emitter.on('group_message', lambda data: handler(self._dict_to_message(data)))
    
    async def load_offline_messages(self) -> List[Message]:
        try:
            result = await self.http_client.get('/message/private/loadOfflineMessage')
            
            messages = []
            if result and isinstance(result, list):
                for item in result:
                    message = self._dict_to_message(item)
                    self._cache_message(message)
                    messages.append(message)
            
            return messages
        except Exception as e:
            self.logger.error("Failed to load offline messages", exc_info=e)
            raise
    
    async def get_private_max_readed_id(self, friend_id: str) -> int:
        try:
            result = await self.http_client.get('/message/private/maxReadedId', {'friendId': friend_id})
            return int(result.get('maxReadedId', 0)) if result else 0
        except Exception as e:
            self.logger.error("Failed to get max readed id", exc_info=e)
            raise
    
    async def delete_private_message(self, message_id: str) -> None:
        try:
            await self.http_client.delete('/message/private/deleteMessage', {'messageId': message_id})
            self._message_cache.pop(message_id, None)
            self.logger.info("Private message deleted", message_id)
        except Exception as e:
            self.logger.error("Failed to delete private message", exc_info=e)
            raise
    
    async def delete_private_chat(self, friend_id: str) -> None:
        try:
            await self.http_client.delete('/message/private/deleteChat', {'friendId': friend_id})
            self._message_cache = {k: v for k, v in self._message_cache.items() if v.to_id != friend_id}
            self.logger.info("Private chat deleted", friend_id)
        except Exception as e:
            self.logger.error("Failed to delete private chat", exc_info=e)
            raise
    
    async def load_group_offline_messages(self) -> List[Message]:
        try:
            result = await self.http_client.get('/message/group/loadOfflineMessage')
            
            messages = []
            if result and isinstance(result, list):
                for item in result:
                    message = self._dict_to_message(item)
                    self._cache_message(message)
                    messages.append(message)
            
            return messages
        except Exception as e:
            self.logger.error("Failed to load group offline messages", exc_info=e)
            raise
    
    async def get_group_readed_users(self, group_id: str, message_id: str) -> List[str]:
        try:
            result = await self.http_client.get('/message/group/findReadedUsers', {'groupId': group_id, 'messageId': message_id})
            return result.get('userIds', []) if result else []
        except Exception as e:
            self.logger.error("Failed to get group readed users", exc_info=e)
            raise
    
    async def delete_group_message(self, message_id: str) -> None:
        try:
            await self.http_client.delete('/message/group/deleteMessage', {'messageId': message_id})
            self._message_cache.pop(message_id, None)
            self.logger.info("Group message deleted", message_id)
        except Exception as e:
            self.logger.error("Failed to delete group message", exc_info=e)
            raise
    
    async def delete_group_chat(self, group_id: str) -> None:
        try:
            await self.http_client.delete('/message/group/deleteChat', {'groupId': group_id})
            self._message_cache = {k: v for k, v in self._message_cache.items() if v.group_id != group_id}
            self.logger.info("Group chat deleted", group_id)
        except Exception as e:
            self.logger.error("Failed to delete group chat", exc_info=e)
            raise
    
    def clear_cache(self) -> None:
        self._message_cache.clear()
    
    async def destroy(self) -> None:
        self.clear_cache()


# ============================================================================
# 群组管理器
# ============================================================================


class GroupManager:
    def __init__(self, http_client: HttpClient, user_id: str):
        self.http_client = http_client
        self.user_id = user_id
        self.logger = Logger.get_instance('GroupManager')
        self._group_cache: Dict[str, Group] = {}
    
    def _dict_to_group(self, data: Dict[str, Any]) -> Group:
        return Group(
            group_id=data.get('groupId', data.get('id', '')),
            group_name=data.get('groupName', data.get('name', '')),
            avatar=data.get('avatar'),
            owner_id=data.get('ownerId'),
            description=data.get('description'),
            member_count=data.get('memberCount'),
            max_members=data.get('maxMembers'),
            is_muted=data.get('isMuted'),
            is_private=data.get('isPrivate'),
            create_time=data.get('createTime'),
            update_time=data.get('updateTime'),
            extra=data.get('extra', {})
        )
    
    async def create_group(self, name: str, description: Optional[str] = None, member_ids: Optional[List[str]] = None) -> Group:
        try:
            data = {'groupName': name}
            if description:
                data['description'] = description
            if member_ids:
                data['memberIds'] = member_ids
            
            result = await self.http_client.post('/group/create', data)
            group = self._dict_to_group(result)
            self._group_cache[group.group_id] = group
            return group
        except Exception as e:
            self.logger.error("Failed to create group", exc_info=e)
            raise
    
    async def modify_group(self, group_id: str, group_name: Optional[str] = None, description: Optional[str] = None, avatar: Optional[str] = None) -> Group:
        try:
            data = {'groupId': group_id}
            if group_name:
                data['groupName'] = group_name
            if description:
                data['description'] = description
            if avatar:
                data['avatar'] = avatar
            
            result = await self.http_client.put('/group/modify', data)
            group = self._dict_to_group(result)
            self._group_cache[group_id] = group
            return group
        except Exception as e:
            self.logger.error("Failed to modify group", exc_info=e)
            raise
    
    async def delete_group(self, group_id: str) -> None:
        try:
            await self.http_client.delete(f'/group/delete/{group_id}')
            self._group_cache.pop(group_id, None)
        except Exception as e:
            self.logger.error("Failed to delete group", exc_info=e)
            raise
    
    async def get_group(self, group_id: str) -> Group:
        cached = self._group_cache.get(group_id)
        if cached:
            return cached
        
        try:
            data = await self.http_client.get(f'/group/find/{group_id}')
            group = self._dict_to_group(data)
            self._group_cache[group_id] = group
            return group
        except Exception as e:
            self.logger.error("Failed to get group", exc_info=e)
            raise
    
    async def get_group_list(self, version: Optional[int] = 0) -> List[Group]:
        try:
            params = {'version': version} if version else {}
            result = await self.http_client.get('/group/list', params)
            
            groups = []
            if result and isinstance(result, list):
                for item in result:
                    group = self._dict_to_group(item)
                    self._group_cache[group.group_id] = group
                    groups.append(group)
            
            return groups
        except Exception as e:
            self.logger.error("Failed to get group list", exc_info=e)
            raise
    
    async def invite_to_group(self, group_id: str, member_ids: List[str]) -> None:
        try:
            await self.http_client.post('/group/invite', {'groupId': group_id, 'memberIds': member_ids})
        except Exception as e:
            self.logger.error("Failed to invite members", exc_info=e)
            raise
    
    async def get_group_members(self, group_id: str, version: Optional[int] = 0) -> List[GroupMember]:
        try:
            params = {'version': version} if version else {}
            result = await self.http_client.get(f'/group/members/{group_id}', params)
            
            members = []
            if result and isinstance(result, list):
                for item in result:
                    member = GroupMember(
                        user_id=item.get('userId', ''),
                        username=item.get('username', ''),
                        group_id=group_id,
                        role=GroupRole(item.get('role', GroupRole.MEMBER)),
                        nickname=item.get('nickname'),
                        avatar=item.get('avatar'),
                        join_time=item.get('joinTime'),
                        is_muted=item.get('isMuted')
                    )
                    members.append(member)
            
            return members
        except Exception as e:
            self.logger.error("Failed to get group members", exc_info=e)
            raise
    
    async def get_online_member_ids(self, group_id: str) -> List[str]:
        try:
            result = await self.http_client.get(f'/group/members/online/{group_id}')
            if result and isinstance(result, list):
                return [str(user_id) for user_id in result]
            return []
        except Exception as e:
            self.logger.error("Failed to get online member ids", exc_info=e)
            raise
    
    async def remove_group_members(self, group_id: str, member_ids: List[str]) -> None:
        try:
            await self.http_client.delete('/group/members/remove', {'groupId': group_id, 'memberIds': member_ids})
        except Exception as e:
            self.logger.error("Failed to remove group members", exc_info=e)
            raise
    
    async def quit_group(self, group_id: str) -> None:
        try:
            await self.http_client.delete(f'/group/quit/{group_id}')
            self._group_cache.pop(group_id, None)
        except Exception as e:
            self.logger.error("Failed to quit group", exc_info=e)
            raise
    
    async def set_group_dnd(self, group_id: str, muted: bool) -> None:
        try:
            await self.http_client.put('/group/dnd', {'groupId': group_id, 'isMuted': muted})
            if group_id in self._group_cache:
                self._group_cache[group_id].is_muted = muted
        except Exception as e:
            self.logger.error("Failed to set group dnd", exc_info=e)
            raise
    
    def clear_cache(self) -> None:
        self._group_cache.clear()
    
    async def destroy(self) -> None:
        self.clear_cache()


# ============================================================================
# 文件管理器
# ============================================================================


class FileManager:
    def __init__(self, http_client: HttpClient):
        self.http_client = http_client
        self.logger = Logger.get_instance('FileManager')
    
    async def upload_image(self, file_path: str) -> str:
        try:
            self.logger.info(f"Uploading image: {file_path}")
            
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.split('/')[-1])
                result = await self.http_client.post('/image/upload', data)
            
            return result.get('url', '')
        
        except Exception as e:
            self.logger.error("Failed to upload image", exc_info=e)
            raise
    
    async def upload_file(self, file_path: str) -> str:
        try:
            self.logger.info(f"Uploading file: {file_path}")
            
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.split('/')[-1])
                result = await self.http_client.post('/file/upload', data)
            
            return result.get('url', '')
        
        except Exception as e:
            self.logger.error("Failed to upload file", exc_info=e)
            raise


# ============================================================================
# WebRTC管理器
# ============================================================================


class WebRTCManager:
    def __init__(self, http_client: HttpClient, user_id: str):
        self.http_client = http_client
        self.user_id = user_id
        self.logger = Logger.get_instance('WebRTCManager')
    
    async def call(self, target_id: str, call_type: str = 'video') -> Dict[str, Any]:
        try:
            self.logger.info(f"Calling {target_id}")
            
            result = await self.http_client.post('/webrtc/private/call', {
                'targetId': target_id,
                'callType': call_type
            })
            
            return result
        
        except Exception as e:
            self.logger.error("Failed to make call", exc_info=e)
            raise
    
    async def accept(self, call_id: str) -> Dict[str, Any]:
        try:
            self.logger.info(f"Accepting call: {call_id}")
            
            result = await self.http_client.post('/webrtc/private/accept', {'callId': call_id})
            
            return result
        
        except Exception as e:
            self.logger.error("Failed to accept call", exc_info=e)
            raise
    
    async def reject(self, call_id: str) -> None:
        try:
            self.logger.info(f"Rejecting call: {call_id}")
            
            await self.http_client.post('/webrtc/private/reject', {'callId': call_id})
            
        except Exception as e:
            self.logger.error("Failed to reject call", exc_info=e)
            raise
    
    async def cancel(self, call_id: str) -> None:
        try:
            self.logger.info(f"Canceling call: {call_id}")
            
            await self.http_client.post('/webrtc/private/cancel', {'callId': call_id})
            
        except Exception as e:
            self.logger.error("Failed to cancel call", exc_info=e)
            raise
    
    async def failed(self, call_id: str, reason: str) -> None:
        try:
            self.logger.info(f"Call failed: {call_id}, reason: {reason}")
            
            await self.http_client.post('/webrtc/private/failed', {
                'callId': call_id,
                'reason': reason
            })
            
        except Exception as e:
            self.logger.error("Failed to report call failure", exc_info=e)
            raise
    
    async def hangup(self, call_id: str) -> None:
        try:
            self.logger.info(f"Hanging up call: {call_id}")
            
            await self.http_client.post('/webrtc/private/handup', {'callId': call_id})
            
        except Exception as e:
            self.logger.error("Failed to hang up call", exc_info=e)
            raise
    
    async def send_candidate(self, call_id: str, candidate: Dict[str, Any]) -> None:
        try:
            self.logger.debug(f"Sending candidate for call: {call_id}")
            
            await self.http_client.post('/webrtc/private/candidate', {
                'callId': call_id,
                'candidate': candidate
            })
            
        except Exception as e:
            self.logger.error("Failed to send candidate", exc_info=e)
            raise
    
    async def send_heartbeat(self, call_id: str) -> None:
        try:
            await self.http_client.post('/webrtc/private/heartbeat', {'callId': call_id})
            
        except Exception as e:
            self.logger.error("Failed to send heartbeat", exc_info=e)
            raise


# ============================================================================
# 用户管理器
# ============================================================================


class UserManager:
    def __init__(self, http_client: HttpClient, user_id: str):
        self.http_client = http_client
        self.user_id = user_id
        self.logger = Logger.get_instance('UserManager')
        self._user_cache: Dict[str, User] = {}
        self._current_user_info: Optional[User] = None
    
    def _dict_to_user(self, data: Dict[str, Any]) -> User:
        return User(
            user_id=data.get('userId', data.get('id', '')),
            username=data.get('username', ''),
            nickname=data.get('nickname'),
            avatar=data.get('avatar'),
            email=data.get('email'),
            phone=data.get('phone'),
            status=OnlineStatus(data.get('status')) if data.get('status') is not None else None,
            terminal=TerminalType(data.get('terminal')) if data.get('terminal') is not None else None,
            last_login_time=data.get('lastLoginTime'),
            create_time=data.get('createTime'),
            update_time=data.get('updateTime'),
            extra=data.get('extra', {})
        )
    
    def set_current_user_info(self, user: User) -> None:
        self._current_user_info = user
        self._user_cache[user.user_id] = user
    
    def get_current_user_info(self) -> Optional[User]:
        return self._current_user_info
    
    async def get_self_info(self) -> User:
        try:
            data = await self.http_client.get('/user/self')
            user = self._dict_to_user(data)
            self._current_user_info = user
            self._user_cache[user.user_id] = user
            return user
        except Exception as e:
            self.logger.error("Failed to get self info", exc_info=e)
            raise
    
    async def get_user_info(self, user_id: str) -> User:
        cached = self._user_cache.get(user_id)
        if cached:
            return cached
        
        try:
            data = await self.http_client.get(f'/user/find/{user_id}')
            user = self._dict_to_user(data)
            self._user_cache[user_id] = user
            return user
        except Exception as e:
            self.logger.error("Failed to get user info", exc_info=e)
            raise
    
    async def find_user_by_name(self, name: str) -> List[User]:
        try:
            result = await self.http_client.get('/user/findByName', {'name': name})
            
            users = []
            if result and isinstance(result, list):
                for item in result:
                    user = self._dict_to_user(item)
                    self._user_cache[user.user_id] = user
                    users.append(user)
            
            return users
        except Exception as e:
            self.logger.error("Failed to find user by name", exc_info=e)
            raise
    
    async def update_user_info(self, nickname: Optional[str] = None, avatar: Optional[str] = None) -> User:
        try:
            data = {}
            if nickname:
                data['nickname'] = nickname
            if avatar:
                data['avatar'] = avatar
            
            result = await self.http_client.put('/user/update', data)
            user = self._dict_to_user(result)
            if user.user_id == self.user_id:
                self._current_user_info = user
            self._user_cache[user.user_id] = user
            return user
        except Exception as e:
            self.logger.error("Failed to update user info", exc_info=e)
            raise
    
    async def get_user_online_terminal(self, user_ids: List[str]) -> Dict[str, List[TerminalType]]:
        try:
            result = await self.http_client.get('/user/terminal/online', {'userIds': ','.join(map(str, user_ids))})
            
            terminal_map = {}
            if result and isinstance(result, dict):
                for user_id, terminals in result.items():
                    if isinstance(terminals, list):
                        terminal_map[str(user_id)] = [TerminalType(t) for t in terminals]
            
            return terminal_map
        except Exception as e:
            self.logger.error("Failed to get user online terminal", exc_info=e)
            raise
    
    async def get_friend_list(self, version: Optional[int] = 0) -> List[User]:
        try:
            params = {'version': version} if version else {}
            result = await self.http_client.get('/friend/list', params)
            
            friends = []
            if result and isinstance(result, list):
                for item in result:
                    user = self._dict_to_user(item)
                    self._user_cache[user.user_id] = user
                    friends.append(user)
            
            return friends
        except Exception as e:
            self.logger.error("Failed to get friend list", exc_info=e)
            raise
    
    async def get_online_friends(self) -> List[User]:
        try:
            result = await self.http_client.get('/friend/online')
            
            online_friends = []
            if result and isinstance(result, list):
                for item in result:
                    user = self._dict_to_user(item)
                    self._user_cache[user.user_id] = user
                    online_friends.append(user)
            
            return online_friends
        except Exception as e:
            self.logger.error("Failed to get online friends", exc_info=e)
            raise
    
    async def add_friend(self, friend_id: str) -> None:
        try:
            await self.http_client.post('/friend/add', {'friendId': friend_id})
        except Exception as e:
            self.logger.error("Failed to add friend", exc_info=e)
            raise
    
    async def get_friend_info(self, friend_id: str) -> User:
        try:
            data = await self.http_client.get(f'/friend/find/{friend_id}')
            user = self._dict_to_user(data)
            self._user_cache[friend_id] = user
            return user
        except Exception as e:
            self.logger.error("Failed to get friend info", exc_info=e)
            raise
    
    async def delete_friend(self, friend_id: str) -> None:
        try:
            await self.http_client.delete(f'/friend/delete/{friend_id}')
            self._user_cache.pop(friend_id, None)
        except Exception as e:
            self.logger.error("Failed to delete friend", exc_info=e)
            raise
    
    async def set_friend_dnd(self, friend_id: str, muted: bool) -> None:
        try:
            await self.http_client.put('/friend/dnd', {'friendId': friend_id, 'isMuted': muted})
        except Exception as e:
            self.logger.error("Failed to set friend dnd", exc_info=e)
            raise
    
    def clear_cache(self) -> None:
        self._user_cache.clear()
    
    async def destroy(self) -> None:
        self.clear_cache()


# ============================================================================
# 主客户端类
# ============================================================================


class BotClient:
    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = Logger.get_instance('BotClient')
        
        if config.enable_logging:
            Logger.set_level(config.log_level)
        
        self._http_client = HttpClient(config.api_base_url, config.request_timeout)
        self._ws_client = WebSocketClient(
            url=config.ws_url,
            auto_reconnect=config.auto_reconnect,
            reconnect_interval=config.reconnect_interval,
            max_reconnect_attempts=config.max_reconnect_attempts,
            heartbeat_interval=config.heartbeat_interval
        )
        
        self._message_manager: Optional[MessageManager] = None
        self._group_manager: Optional[GroupManager] = None
        self._user_manager: Optional[UserManager] = None
        self._file_manager: Optional[FileManager] = None
        self._webrtc_manager: Optional[WebRTCManager] = None
        
        self._user_id: Optional[str] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        if self._initialized:
            return
        self.logger.info("Initializing BotClient...")
        self._initialized = True
    
    async def login(self) -> None:
        raise NotImplementedError(
            "机器人登录接口不存在！请使用 login_with_password() 进行用户登录。"
        )
    
    async def register(
        self,
        username: str,
        password: str,
        nickname: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> UserLoginResponse:
        try:
            self.logger.info("Registering new user...")
            
            data = {
                'userName': username,
                'password': password
            }
            if nickname:
                data['nickname'] = nickname
            if email:
                data['email'] = email
            if phone:
                data['phone'] = phone
            
            result = await self._http_client.post('/register', data)
            
            access_token = result.get('accessToken', '')
            self._http_client.set_access_token(access_token)
            self._ws_client.set_access_token(access_token)
            
            user_info_data = result.get('userInfo', {})
            user_info = User(
                user_id=str(user_info_data.get('userId', '')),
                username=user_info_data.get('username', ''),
                nickname=user_info_data.get('nickname'),
                avatar=user_info_data.get('avatar'),
                email=user_info_data.get('email'),
                phone=user_info_data.get('phone'),
                extra=user_info_data.get('extra', {})
            )
            
            self._user_id = user_info.user_id
            self._message_manager = MessageManager(self._http_client, self._ws_client, self._user_id)
            self._group_manager = GroupManager(self._http_client, self._user_id)
            self._user_manager = UserManager(self._http_client, self._user_id)
            self._file_manager = FileManager(self._http_client)
            self._webrtc_manager = WebRTCManager(self._http_client, self._user_id)
            self._user_manager.set_current_user_info(user_info)
            
            await self._ws_client.connect()
            
            self.logger.info("Registration successful")
            
            return UserLoginResponse(
                access_token=access_token,
                refresh_token=result.get('refreshToken', ''),
                expires_in=result.get('expiresIn', 0),
                token_type=result.get('tokenType', 'Bearer'),
                user_info=user_info
            )
            
        except Exception as e:
            self.logger.error("Registration failed", exc_info=e)
            raise
    
    async def refresh_token(self, refresh_token: str) -> UserLoginResponse:
        try:
            self.logger.info("Refreshing token...")
            
            result = await self._http_client.put('/refreshToken', {'refreshToken': refresh_token})
            
            access_token = result.get('accessToken', '')
            self._http_client.set_access_token(access_token)
            self._ws_client.set_access_token(access_token)
            
            user_info_data = result.get('userInfo', {})
            user_info = User(
                user_id=str(user_info_data.get('userId', '')),
                username=user_info_data.get('username', ''),
                nickname=user_info_data.get('nickname'),
                avatar=user_info_data.get('avatar'),
                email=user_info_data.get('email'),
                phone=user_info_data.get('phone'),
                extra=user_info_data.get('extra', {})
            )
            
            self._user_id = user_info.user_id
            
            self.logger.info("Token refreshed successfully")
            
            return UserLoginResponse(
                access_token=access_token,
                refresh_token=result.get('refreshToken', ''),
                expires_in=result.get('expiresIn', 0),
                token_type=result.get('tokenType', 'Bearer'),
                user_info=user_info
            )
            
        except Exception as e:
            self.logger.error("Failed to refresh token", exc_info=e)
            raise
    
    async def modify_password(self, old_password: str, new_password: str) -> None:
        try:
            self.logger.info("Modifying password...")
            
            await self._http_client.put('/modifyPwd', {
                'oldPassword': old_password,
                'newPassword': new_password
            })
            
            self.logger.info("Password modified successfully")
            
        except Exception as e:
            self.logger.error("Failed to modify password", exc_info=e)
            raise
    
    async def login_with_password(
        self,
        username: str,
        password: str,
        terminal: Optional[TerminalType] = TerminalType.WEB
    ) -> UserLoginResponse:
        try:
            self.logger.info("Logging in with password...")
            
            result = await self._http_client.post('/api/login', {
                'userName': username,
                'password': password,
                'terminal': terminal
            })
            
            access_token = result.get('accessToken', '')
            self._http_client.set_access_token(access_token)
            self._ws_client.set_access_token(access_token)
            
            user_info_data = result.get('userInfo', {})
            user_info = User(
                user_id=str(user_info_data.get('userId', '')),
                username=user_info_data.get('username', ''),
                nickname=user_info_data.get('nickname'),
                avatar=user_info_data.get('avatar'),
                email=user_info_data.get('email'),
                phone=user_info_data.get('phone'),
                extra=user_info_data.get('extra', {})
            )
            
            self._user_id = user_info.user_id
            
            self._message_manager = MessageManager(self._http_client, self._ws_client, self._user_id)
            self._group_manager = GroupManager(self._http_client, self._user_id)
            self._user_manager = UserManager(self._http_client, self._user_id)
            self._file_manager = FileManager(self._http_client)
            self._webrtc_manager = WebRTCManager(self._http_client, self._user_id)
            self._user_manager.set_current_user_info(user_info)
            
            await self._ws_client.connect()
            
            self.logger.info("Login with password successful")
            
            return UserLoginResponse(
                access_token=access_token,
                refresh_token=result.get('refreshToken', ''),
                expires_in=result.get('expiresIn', 0),
                token_type=result.get('tokenType', 'Bearer'),
                user_info=user_info
            )
            
        except Exception as e:
            self.logger.error("Login with password failed", exc_info=e)
            raise
    
    async def logout(self) -> None:
        self.logger.info("Logging out...")
        
        if self._ws_client:
            await self._ws_client.close()
        
        if self._message_manager:
            await self._message_manager.destroy()
        if self._group_manager:
            await self._group_manager.destroy()
        if self._user_manager:
            await self._user_manager.destroy()
        
        if self._http_client:
            await self._http_client.destroy()
        
        self.logger.info("Logged out")
    
    def is_ready(self) -> bool:
        return (
            self._initialized and
            self._ws_client.connection_state == ConnectionState.CONNECTED and
            self._user_id is not None
        )
    
    @property
    def message_manager(self) -> MessageManager:
        if not self._message_manager:
            raise Exception("Client not logged in")
        return self._message_manager
    
    @property
    def file_manager(self) -> FileManager:
        if not self._file_manager:
            raise Exception("Client not logged in")
        return self._file_manager
    
    @property
    def webrtc_manager(self) -> WebRTCManager:
        if not self._webrtc_manager:
            raise Exception("Client not logged in")
        return self._webrtc_manager
    
    async def send_private_message(self, to_id: str, content: Any, content_type: MessageType = MessageType.TEXT) -> Message:
        return await self.message_manager.send_private_message(to_id, content, content_type)
    
    async def send_group_message(self, group_id: str, content: Any, content_type: MessageType = MessageType.TEXT) -> Message:
        return await self.message_manager.send_group_message(group_id, content, content_type)
    
    def on_message(self, handler: Callable[[Message], Any]) -> None:
        self.message_manager.on_message(handler)
    
    def on(self, event: str, handler: Callable) -> None:
        event_emitter = BotEventEmitter.get_instance()
        event_emitter.on(event, handler)
    
    def off(self, event: str, handler: Optional[Callable] = None) -> None:
        event_emitter = BotEventEmitter.get_instance()
        event_emitter.off(event, handler)


# ============================================================================
# 简化封装类
# ============================================================================


def create_bot_client(config: BotConfig) -> BotClient:
    return BotClient(config)


class BoxIMBotSDK:
    def __init__(self, config: BotConfig):
        self._bot_client = create_bot_client(config)
    
    @staticmethod
    def get_version() -> str:
        return __version__
    
    @staticmethod
    def get_info() -> Dict[str, str]:
        return {
            'version': __version__,
            'author': __author__,
            'copyright': __copyright__,
            'license': __license__,
            'description': __description__
        }
    
    async def start(self) -> None:
        await self._bot_client.initialize()
        await self._bot_client.login()
    
    async def start_with_password(
        self,
        username: str,
        password: str,
        terminal: Optional[TerminalType] = TerminalType.WEB
    ) -> UserLoginResponse:
        await self._bot_client.initialize()
        return await self._bot_client.login_with_password(username, password, terminal)
    
    async def stop(self) -> None:
        await self._bot_client.logout()
    
    @property
    def client(self) -> BotClient:
        return self._bot_client
    
    def is_ready(self) -> bool:
        return self._bot_client.is_ready()
    
    async def send_message(self, to_id: str, content: Any, content_type: MessageType = MessageType.TEXT) -> Message:
        return await self._bot_client.send_private_message(to_id, content, content_type)
    
    async def send_group_message(self, group_id: str, content: Any, content_type: MessageType = MessageType.TEXT) -> Message:
        return await self._bot_client.send_group_message(group_id, content, content_type)
    
    def on_message(self, handler: Callable[[Message], Any]) -> None:
        self._bot_client.on_message(handler)
    
    def on(self, event: str, handler: Callable) -> None:
        self._bot_client.on(event, handler)
    
    def off(self, event: str, handler: Optional[Callable] = None) -> None:
        self._bot_client.off(event, handler)


# ============================================================================
# 全局版本信息函数
# ============================================================================


def get_version() -> str:
    return __version__


def get_sdk_info() -> Dict[str, str]:
    return {
        'version': __version__,
        'author': __author__,
        'copyright': __copyright__,
        'license': __license__,
        'description': __description__
    }


def print_sdk_info() -> None:
    info = get_sdk_info()
    print("=" * 60)
    print("Box IM Python SDK")
    print("=" * 60)
    for key, value in info.items():
        print(f"{key.title():15}: {value}")
    print("=" * 60)


# ============================================================================
# 模块导出
# ============================================================================


__all__ = [
    'get_version', 'get_sdk_info', 'print_sdk_info',
    'MessageType', 'TerminalType', 'SessionType', 'OnlineStatus', 'ErrorCode',
    'CommandType', 'GroupRole', 'MessageStatus', 'ConnectionState', 'LogLevel',
    'FriendRequestStatus', 'NotificationType',
    'BotConfig', 'User', 'Group', 'GroupMember', 'Session', 'Message',
    'UserLoginResponse', 'ApiResponse', 'PaginatedResponse', 'WebSocketPacket',
    'MessageAck', 'TypingData', 'QueryOptions', 'FriendRequest', 'Notification',
    'RetryOptions', 'RateLimitConfig', 'CacheOptions', 'SDKStats',
    'Logger', 'BotEventEmitter', 'HttpClient', 'WebSocketClient',
    'MessageManager', 'GroupManager', 'UserManager', 'FileManager', 'WebRTCManager',
    'BotClient', 'BoxIMBotSDK', 'create_bot_client',
]
