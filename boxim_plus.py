"""
BoxIM SDK - 完整的即时通讯SDK实现
Copyright (c) 2026 归鸿. All rights reserved.
基于MIT协议开源
"""

import asyncio
import aiohttp
import websockets
import json
import time
import random
import re
import uuid
import os
import ssl
import logging
import signal
import mimetypes
import tempfile
from typing import Optional, Dict, List, Callable, Any, Union, Tuple
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from datetime import datetime
import base64
import hashlib
from collections import defaultdict
from functools import wraps
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BoxIM')

class MessageType(IntEnum):
    TEXT = 0
    IMAGE = 1
    FILE = 2
    VOICE = 3
    VIDEO = 4
    USER_CARD = 5
    GROUP_CARD = 6
    LOCATION = 7
    QUOTE = 8
    SYSTEM = 21
    RECALL = 22
    NOTICE = 23
    ONLINE_STATUS = 82
    MUTED = 96

class Gender(IntEnum):
    MALE = 0
    FEMALE = 1
    UNKNOWN = 2

class Terminal(IntEnum):
    PC = 0
    MOBILE = 1
    WEB = 2

class WSCommand(IntEnum):
    AUTH = 0
    HEARTBEAT = 1
    FORCE_OFFLINE = 2
    PRIVATE_MESSAGE = 3
    GROUP_MESSAGE = 4
    SYSTEM_MESSAGE = 5

class Config:
    BASE_URL = "https://www.boxim.online"
    WS_URL = "wss://www.boxim.online/im"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    RECONNECT_DELAY = 1
    MAX_RECONNECT_DELAY = 300
    HEARTBEAT_INTERVAL = 20
    TOKEN_REFRESH_THRESHOLD = 300
    REQUEST_TIMEOUT = 30
    UPLOAD_CHUNK_SIZE = 1024 * 1024

@dataclass
class UserInfo:
    id: int
    userName: str
    nickName: str
    sex: int
    signature: str = ""
    headImage: str = ""
    headImageThumb: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    type: int = 1
    isBanned: bool = False
    reason: str = ""
    isManualApprove: bool = False
    isInBlacklist: Optional[bool] = None
    isAudioTip: bool = False
    status: int = 0
    online: Optional[bool] = None
    companyName: Optional[str] = None
    unbanTime: Optional[str] = None
    authStatus: Optional[int] = None

@dataclass
class GroupInfo:
    id: int
    name: str
    ownerId: int
    headImage: str = ""
    headImageThumb: str = ""
    notice: str = ""
    remarkNickName: str = ""
    showNickName: str = ""
    showGroupName: str = ""
    remarkGroupName: str = ""
    isAllMuted: bool = False
    isAllowInvite: bool = True
    isAllowShareCard: bool = True
    dissolve: bool = False
    quit: bool = False
    isMuted: bool = False
    isBanned: bool = False
    reason: str = ""
    isDnd: Optional[bool] = None
    isTop: bool = False
    topMessage: Optional[str] = None
    memberCount: int = 0
    rtcInfo: Optional[Any] = None
    unbanTime: Optional[str] = None

@dataclass
class FriendInfo:
    id: int
    nickName: str
    showNickName: str
    remarkNickName: str = ""
    headImage: str = ""
    isDnd: Optional[bool] = None
    isTop: bool = False
    deleted: bool = False
    online: bool = False
    onlineWeb: bool = False
    onlineApp: bool = False
    companyName: Optional[str] = None

@dataclass
class GroupMember:
    userId: int
    showNickName: str
    remarkNickName: str = ""
    headImage: str = ""
    isManager: bool = False
    isMuted: bool = False
    quit: bool = False
    online: bool = False
    showGroupName: str = ""
    remarkGroupName: str = ""
    companyName: Optional[str] = None
    version: Optional[int] = None

class Message:
    def __init__(self, data: Dict, is_group: bool = False):
        self.raw_data = data
        self.is_group = is_group
        self.id = data.get('id')
        self.type = data.get('type', 0)
        self.content = data.get('content', '')
        self.send_time = data.get('sendTime')
        self.send_id = data.get('sendId')
        self.send_nickname = data.get('sendNickName', '')
        self.status = data.get('status', 0)

        if is_group:
            self.group_id = data.get('groupId')
            self.at_user_ids = data.get('atUserIds', [])
            self.readed_count = data.get('readedCount', 0)
            self.receipt = data.get('receipt', False)
            self.receipt_ok = data.get('receiptOk')
        else:
            self.recv_id = data.get('recvId')

        self.quote_message = data.get('quoteMessage')
        self.parsed_content = self._parse_content()

    def _parse_content(self) -> Dict:
        if self.type == MessageType.TEXT:
            return {"text": self.content}
        elif self.type in [MessageType.IMAGE, MessageType.FILE, MessageType.VOICE,
                          MessageType.VIDEO, MessageType.USER_CARD, MessageType.GROUP_CARD,
                          MessageType.ONLINE_STATUS]:
            try:
                return json.loads(self.content)
            except Exception:
                return {"raw": self.content}
        return {"raw": self.content}

    @property
    def chat_id(self) -> int:
        return self.group_id if self.is_group else self.recv_id

    @property
    def is_at_me(self) -> bool:
        if not self.is_group:
            return False
        return False

    def __repr__(self) -> str:
        type_name = MessageType(self.type).name if self.type in MessageType._value2member_map_ else f"UNKNOWN({self.type})"
        return f"Message(id={self.id}, type={type_name}, sender={self.send_id}, chat_id={self.chat_id}, content={self.parsed_content})"

class BoxIMException(Exception):
    pass

class AuthException(BoxIMException):
    pass

class NetworkException(BoxIMException):
    pass

class UploadException(BoxIMException):
    pass

class RateLimiter:
    def __init__(self, calls: int = 10, period: int = 1):
        self.calls = calls
        self.period = period
        self.timestamps = []

    async def acquire(self):
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < self.period]

        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                await self.acquire()
        else:
            self.timestamps.append(now)

class FileUploader:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.rate_limiter = RateLimiter(calls=5, period=1)

    async def upload_file(self, file_path: str) -> Optional[str]:
        await self.rate_limiter.acquire()
        url = f"{Config.BASE_URL}/api/file/upload"
        return await self._upload(file_path, url, "file")

    async def upload_image(self, file_path: str, is_permanent: bool = True, thumb_size: int = 50) -> Optional[Dict]:
        await self.rate_limiter.acquire()
        url = f"{Config.BASE_URL}/api/image/upload?isPermanent={str(is_permanent).lower()}&thumbSize={thumb_size}"
        return await self._upload(file_path, url, "file")

    async def upload_audio(self, file_path: str) -> Optional[str]:
        await self.rate_limiter.acquire()
        url = f"{Config.BASE_URL}/api/file/upload"
        return await self._upload(file_path, url, "file")

    async def _upload(self, file_path: str, url: str, field_name: str) -> Optional[Any]:
        if not self.boxim.is_logged_in:
            raise AuthException("未登录")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:
            raise UploadException("文件大小超过限制(100MB)")

        try:
            filename = os.path.basename(file_path)
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'

            headers = self.boxim._get_headers()
            if 'Content-Type' in headers:
                del headers['Content-Type']

            timeout = aiohttp.ClientTimeout(total=max(60, file_size / (1024 * 1024) * 10))

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=timeout
            ) as session:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field(field_name, f, filename=filename, content_type=content_type)

                    async with session.post(url, headers=headers, data=data) as resp:
                        result = await resp.json()
                        if result.get("code") == 200:
                            return result.get("data")
                        else:
                            raise UploadException(f"上传失败: {result.get('message')}")
        except Exception as e:
            if isinstance(e, (UploadException, AuthException)):
                raise
            raise NetworkException(f"上传时发生错误: {e}")

class APIClient:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def request(self, method: str, path: str, params: Dict = None, json: Any = None, body: Any = None, **kwargs) -> Dict:
        if not self.session:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
            ) as session:
                return await self._do_request(session, method, path, params, json, body, **kwargs)
        else:
            return await self._do_request(self.session, method, path, params, json, body, **kwargs)

    async def _do_request(self, session: aiohttp.ClientSession,
                       method: str, path: str, params: Dict = None,
                       json_data: Any = None, body: Any = None, **kwargs) -> Dict:
        url = f"{Config.BASE_URL}{path}"

        if 'headers' not in kwargs:
            kwargs['headers'] = self.boxim._get_headers()

        try:
            if json_data is not None:
                async with session.request(method, url, params=params, json=json_data, **kwargs) as resp:
                    result = await resp.json()
                    if result.get("code") != 200:
                        raise BoxIMException(f"API错误: {result.get('message')}")
                    return result
            elif body is not None:
                async with session.request(method, url, params=params, data=body, **kwargs) as resp:
                    result = await resp.json()
                    if result.get("code") != 200:
                        raise BoxIMException(f"API错误: {result.get('message')}")
                    return result
            else:
                async with session.request(method, url, params=params, json=json_data, **kwargs) as resp:
                    result = await resp.json()
                    if result.get("code") != 200:
                        raise BoxIMException(f"API错误: {result.get('message')}")
                    return result
        except aiohttp.ClientError as e:
            raise NetworkException(f"网络请求失败: {e}")

class AuthModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)

    async def register(self, username: str, password: str, nickName: str = None) -> bool:
        try:
            payload = {
                "userName": username,
                "password": password,
                "nickName": nickName or username
            }
            result = await self.api.request('POST', '/api/register', json=payload)
            return result.get("code") == 200
        except Exception as e:
            logger.error(f"注册失败: {e}")
            return False

    async def login(self, username: str, password: str, terminal: Terminal = Terminal.PC) -> bool:
        self.boxim.terminal = terminal
        try:
            result = await self.api.request('POST', '/api/login', json={
                "terminal": terminal.value,
                "userName": username,
                "password": password
            })

            data = result['data']
            self.boxim.access_token = data['accessToken']
            self.boxim.refresh_token = data['refreshToken']
            self.boxim.access_token_expires = time.time() + data['accessTokenExpiresIn']
            self.boxim.refresh_token_expires = time.time() + data['refreshTokenExpiresIn']

            import jwt
            payload = jwt.decode(self.boxim.access_token, options={"verify_signature": False})
            info = json.loads(payload.get("info", "{}"))
            self.boxim.user_id = info.get("userId")

            logger.info(f"登录成功: 用户ID={self.boxim.user_id}")

            if self.boxim.auto_refresh_token:
                self.boxim._start_token_refresh_task()

            return True

        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False

    async def refresh_token(self) -> bool:
        if not self.boxim.refresh_token or time.time() > self.boxim.refresh_token_expires:
            logger.error("无法刷新token: refresh_token无效或已过期")
            return False

        headers = self.boxim._get_headers()
        headers['refreshToken'] = self.boxim.refresh_token

        try:
            result = await self.api.request('PUT', '/api/refreshToken', headers=headers, json={})

            data = result['data']
            self.boxim.access_token = data['accessToken']
            self.boxim.refresh_token = data['refreshToken']
            self.boxim.access_token_expires = time.time() + data['accessTokenExpiresIn']
            self.boxim.refresh_token_expires = time.time() + data['refreshTokenExpiresIn']

            logger.info("Token刷新成功")
            return True

        except Exception as e:
            logger.error(f"Token刷新失败: {e}")
            return False

    async def modify_password(self, old_password: str, new_password: str) -> bool:
        try:
            payload = {
                "oldPassword": old_password,
                "newPassword": new_password
            }
            await self.api.request('PUT', '/api/modifyPwd', json=payload)
            return True
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return False

class UserModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)

    async def get_self_info(self) -> Optional[UserInfo]:
        try:
            result = await self.api.request('GET', '/api/user/self')
            return UserInfo(**result['data'])
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        try:
            result = await self.api.request('GET', f'/api/user/find/{user_id}')
            return UserInfo(**result['data'])
        except Exception as e:
            logger.error(f"获取用户{user_id}信息失败: {e}")
            return None

    async def find_user_by_name(self, name: str) -> Optional[List[UserInfo]]:
        try:
            result = await self.api.request('GET', '/api/user/findByName', params={"name": name})
            data = result['data']
            if isinstance(data, list):
                return [UserInfo(**u) for u in data]
            elif isinstance(data, dict):
                return [UserInfo(**data)]
            return []
        except Exception as e:
            logger.error(f"查找用户失败: {e}")
            return None

    async def update_profile(self, **kwargs) -> bool:
        allowed_fields = ['nickName', 'sex', 'signature', 'headImage', 'headImageThumb']
        payload = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if 'headImage' in payload and os.path.exists(payload['headImage']):
            uploader = FileUploader(self.boxim)
            result = await uploader.upload_image(payload['headImage'], is_permanent=True)
            if result:
                payload['headImage'] = result.get('originUrl')
                payload['headImageThumb'] = result.get('thumbUrl')

        payload['id'] = self.boxim.user_id

        try:
            await self.api.request('PUT', '/api/user/update', json=payload)
            return True
        except Exception as e:
            logger.error(f"更新个人资料失败: {e}")
            return False

    async def search_user(self, keyword: str) -> Optional[List[UserInfo]]:
        try:
            result = await self.api.request('GET', '/api/user/findByName', params={"name": keyword})
            data = result['data']
            if isinstance(data, list):
                return [UserInfo(**user) for user in data]
            elif isinstance(data, dict):
                return [UserInfo(**data)]
            return []
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            return None

    async def get_online_terminals(self, user_ids: List[int]) -> Optional[List[Dict]]:
        try:
            user_ids_str = ','.join(map(str, user_ids))
            result = await self.api.request('GET', '/api/user/terminal/online', params={"userIds": user_ids_str})
            return result['data']
        except Exception as e:
            logger.error(f"获取在线终端失败: {e}")
            return None

class FriendModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)
        self._friend_cache = {}
        self._cache_time = 0

    async def get_friend_list(self, force_refresh: bool = False, version: int = 0) -> Optional[List[FriendInfo]]:
        if not force_refresh and time.time() - self._cache_time < 60:
            return list(self._friend_cache.values())

        try:
            result = await self.api.request('GET', '/api/friend/list', params={"version": version})
            friends = [FriendInfo(**friend) for friend in result['data']]
            self._friend_cache = {f.id: f for f in friends}
            self._cache_time = time.time()
            return friends
        except Exception as e:
            logger.error(f"获取好友列表失败: {e}")
            return None

    async def get_friend_online_status(self) -> Optional[Dict]:
        try:
            result = await self.api.request('GET', '/api/friend/online')
            return result['data']
        except Exception as e:
            logger.error(f"获取好友在线状态失败: {e}")
            return None

    async def get_friend_info(self, friend_id: int) -> Optional[FriendInfo]:
        try:
            result = await self.api.request('GET', f'/api/friend/find/{friend_id}')
            return FriendInfo(**result['data'])
        except Exception as e:
            logger.error(f"获取好友信息失败: {e}")
            return None

    async def add_friend(self, friend_id: int) -> bool:
        try:
            await self.api.request('POST', '/api/friend/add', params={"friendId": friend_id})
            return True
        except Exception as e:
            logger.error(f"添加好友失败: {e}")
            return False

    async def delete_friend(self, friend_id: int) -> bool:
        try:
            await self.api.request('DELETE', f'/api/friend/delete/{friend_id}')
            if friend_id in self._friend_cache:
                del self._friend_cache[friend_id]
            return True
        except Exception as e:
            logger.error(f"删除好友失败: {e}")
            return False

    async def set_dnd(self, friend_id: int, isDnd: bool = True) -> bool:
        try:
            await self.api.request('PUT', '/api/friend/dnd', json={"friendId": friend_id, "isDnd": isDnd})
            return True
        except Exception as e:
            logger.error(f"设置好友免打扰失败: {e}")
            return False

class GroupModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)
        self._group_cache = {}
        self._members_cache = {}

    async def get_group_list(self, version: int = 0) -> Optional[List[GroupInfo]]:
        try:
            result = await self.api.request('GET', '/api/group/list', params={"version": version})
            groups = [GroupInfo(**g) for g in result['data']]
            self._group_cache = {g.id: g for g in groups}
            return groups
        except Exception as e:
            logger.error(f"获取群组列表失败: {e}")
            return None

    async def get_group_info(self, group_id: int) -> Optional[GroupInfo]:
        if group_id in self._group_cache:
            return self._group_cache[group_id]

        try:
            result = await self.api.request('GET', f'/api/group/find/{group_id}')
            group = GroupInfo(**result['data'])
            self._group_cache[group_id] = group
            return group
        except Exception as e:
            logger.error(f"获取群组信息失败: {e}")
            return None

    async def create_group(self, name: str, member_ids: List[int]) -> Optional[int]:
        try:
            result = await self.api.request('POST', '/api/group/create', json={"name": name, "memberIds": member_ids})
            return result['data'].get('id')
        except Exception as e:
            logger.error(f"创建群组失败: {e}")
            return None

    async def modify_group(self, group_id: int, name: str = None, notice: str = None, headImage: str = None, isAllMuted: bool = None) -> bool:
        try:
            payload = {"groupId": group_id}
            if name is not None:
                payload["name"] = name
            if notice is not None:
                payload["notice"] = notice
            if headImage is not None:
                payload["headImage"] = headImage
            if isAllMuted is not None:
                payload["isAllMuted"] = isAllMuted

            await self.api.request('PUT', '/api/group/modify', json=payload)
            return True
        except Exception as e:
            logger.error(f"修改群组信息失败: {e}")
            return False

    async def dissolve_group(self, group_id: int) -> bool:
        try:
            await self.api.request('DELETE', f'/api/group/delete/{group_id}')
            if group_id in self._group_cache:
                del self._group_cache[group_id]
            return True
        except Exception as e:
            logger.error(f"解散群组失败: {e}")
            return False

    async def get_group_members(self, group_id: int, version: int = 0) -> Optional[List[GroupMember]]:
        try:
            result = await self.api.request('GET', f'/api/group/members/{group_id}', params={"version": version})
            members = [GroupMember(**m) for m in result['data']]
            self._members_cache[group_id] = members
            return members
        except Exception as e:
            logger.error(f"获取群成员失败: {e}")
            return None

    async def get_online_members(self, group_id: int) -> Optional[List[int]]:
        try:
            result = await self.api.request('GET', f'/api/group/members/online/{group_id}')
            return result['data']
        except Exception as e:
            logger.error(f"获取在线成员失败: {e}")
            return None

    async def invite_members(self, group_id: int, friend_ids: List[int]) -> bool:
        try:
            await self.api.request('POST', '/api/group/invite', json={"groupId": group_id, "friendIds": friend_ids})
            return True
        except Exception as e:
            logger.error(f"邀请成员失败: {e}")
            return False

    async def remove_members(self, group_id: int, user_ids: List[int]) -> bool:
        try:
            await self.api.request('DELETE', '/api/group/members/remove', json={"groupId": group_id, "userIds": user_ids})
            return True
        except Exception as e:
            logger.error(f"移除成员失败: {e}")
            return False

    async def quit_group(self, group_id: int) -> bool:
        try:
            await self.api.request('DELETE', f'/api/group/quit/{group_id}')
            if group_id in self._group_cache:
                del self._group_cache[group_id]
            return True
        except Exception as e:
            logger.error(f"退出群组失败: {e}")
            return False

    async def set_dnd(self, group_id: int, isDnd: bool = True) -> bool:
        try:
            await self.api.request('PUT', '/api/group/dnd', json={"groupId": group_id, "isDnd": isDnd})
            return True
        except Exception as e:
            logger.error(f"设置群组免打扰失败: {e}")
            return False

class PrivateMessageModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)
        self.uploader = FileUploader(boxim_instance)

    async def send_message(self, user_id: int, content: str, msg_type: MessageType = MessageType.TEXT) -> Optional[int]:
        local_id = str(uuid.uuid4().int)[:16]
        payload = {
            "localId": local_id,
            "content": content,
            "type": msg_type.value,
            "recvId": user_id
        }

        try:
            result = await self.api.request('POST', '/api/message/private/send', json=payload)
            return result['data'].get('id')
        except Exception as e:
            logger.error(f"发送私聊消息失败: {e}")
            return None

    async def recall_message(self, message_id: int) -> bool:
        try:
            await self.api.request('DELETE', f'/api/message/private/recall/{message_id}')
            return True
        except Exception as e:
            logger.error(f"撤回消息失败: {e}")
            return False

    async def load_offline_messages(self, min_id: int) -> Optional[List[Message]]:
        try:
            result = await self.api.request('GET', '/api/message/private/loadOfflineMessage', params={"minId": min_id})
            return [Message(msg, is_group=False) for msg in result['data']]
        except Exception as e:
            logger.error(f"拉取离线消息失败: {e}")
            return None

    async def mark_read(self, friend_id: int, message_id: Optional[int] = None) -> bool:
        try:
            params = {"friendId": friend_id}
            if message_id is not None:
                params["messageId"] = message_id
            await self.api.request('PUT', '/api/message/private/readed', params=params)
            return True
        except Exception as e:
            logger.error(f"标记已读失败: {e}")
            return False

    async def get_max_readed_id(self, friend_id: int) -> Optional[int]:
        try:
            result = await self.api.request('GET', '/api/message/private/maxReadedId', params={"friendId": friend_id})
            return result['data']
        except Exception as e:
            logger.error(f"获取最大已读消息ID失败: {e}")
            return None

    async def delete_message(self, chat_id: int, message_ids: List[int]) -> bool:
        try:
            await self.api.request('DELETE', '/api/message/private/deleteMessage', json={"chatId": chat_id, "messageIds": message_ids})
            return True
        except Exception as e:
            logger.error(f"删除消息失败: {e}")
            return False

    async def delete_chat(self, chat_id: int) -> bool:
        try:
            await self.api.request('DELETE', '/api/message/private/deleteChat', json={"chatId": chat_id})
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    async def get_history(self, friend_id: int, min_seq_no: Optional[int] = None, max_seq_no: Optional[int] = None) -> Optional[List[Message]]:
        params = {"friendId": friend_id}
        if min_seq_no:
            params["minSeqNo"] = min_seq_no
        if max_seq_no:
            params["maxSeqNo"] = max_seq_no

        try:
            result = await self.api.request('POST', '/api/message/private/history', json=params)
            return [Message(msg, is_group=False) for msg in result['data']]
        except Exception as e:
            logger.error(f"获取历史消息失败: {e}")
            return None

class GroupMessageModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)
        self.uploader = FileUploader(boxim_instance)

    async def send_message(self, group_id: int, content: str, msg_type: MessageType = MessageType.TEXT, at_user_ids: List[int] = None) -> Optional[int]:
        local_id = str(uuid.uuid4().int)[:16]
        payload = {
            "localId": local_id,
            "content": content,
            "type": msg_type.value,
            "groupId": group_id,
            "atUserIds": at_user_ids or [],
            "receipt": False
        }

        try:
            result = await self.api.request('POST', '/api/message/group/send', json=payload)
            return result['data'].get('id')
        except Exception as e:
            logger.error(f"发送群聊消息失败: {e}")
            return None

    async def recall_message(self, message_id: int) -> bool:
        try:
            await self.api.request('DELETE', f'/api/message/group/recall/{message_id}')
            return True
        except Exception as e:
            logger.error(f"撤回消息失败: {e}")
            return False

    async def load_offline_messages(self, min_id: int) -> Optional[List[Message]]:
        try:
            result = await self.api.request('GET', '/api/message/group/loadOfflineMessage', params={"minId": min_id})
            return [Message(msg, is_group=True) for msg in result['data']]
        except Exception as e:
            logger.error(f"拉取离线消息失败: {e}")
            return None

    async def mark_read(self, group_id: int, message_id: Optional[int] = None) -> bool:
        try:
            params = {"groupId": group_id}
            if message_id is not None:
                params["messageId"] = message_id
            await self.api.request('PUT', '/api/message/group/readed', params=params)
            return True
        except Exception as e:
            logger.error(f"标记已读失败: {e}")
            return False

    async def get_readed_users(self, group_id: int, message_id: int) -> Optional[List[int]]:
        try:
            result = await self.api.request('GET', '/api/message/group/findReadedUsers', params={"groupId": group_id, "messageId": message_id})
            return result['data']
        except Exception as e:
            logger.error(f"获取已读用户失败: {e}")
            return None

    async def delete_message(self, chat_id: int, message_ids: List[int]) -> bool:
        try:
            await self.api.request('DELETE', '/api/message/group/deleteMessage', json={"chatId": chat_id, "messageIds": message_ids})
            return True
        except Exception as e:
            logger.error(f"删除消息失败: {e}")
            return False

    async def delete_chat(self, chat_id: int) -> bool:
        try:
            await self.api.request('DELETE', '/api/message/group/deleteChat', json={"chatId": chat_id})
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    async def get_history(self, group_id: int, min_seq_no: Optional[int] = None, max_seq_no: Optional[int] = None) -> Optional[List[Message]]:
        params = {"groupId": group_id}
        if min_seq_no:
            params["minSeqNo"] = min_seq_no
        if max_seq_no:
            params["maxSeqNo"] = max_seq_no

        try:
            result = await self.api.request('POST', '/api/message/group/history', json=params)
            return [Message(msg, is_group=True) for msg in result['data']]
        except Exception as e:
            logger.error(f"获取历史消息失败: {e}")
            return None

class WebRTCModule:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.api = APIClient(boxim_instance)

    async def call(self, uid: int, mode: str = "video", offer: str = "") -> bool:
        try:
            params = {"uid": uid, "mode": mode}
            await self.api.request('POST', '/api/webrtc/private/call', params=params, body=offer)
            return True
        except Exception as e:
            logger.error(f"发起通话失败: {e}")
            return False

    async def accept(self, uid: int, answer: str = "") -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/accept', params={"uid": uid}, body=answer)
            return True
        except Exception as e:
            logger.error(f"接受通话失败: {e}")
            return False

    async def reject(self, uid: int) -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/reject', params={"uid": uid})
            return True
        except Exception as e:
            logger.error(f"拒绝通话失败: {e}")
            return False

    async def cancel(self, uid: int) -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/cancel', params={"uid": uid})
            return True
        except Exception as e:
            logger.error(f"取消呼叫失败: {e}")
            return False

    async def failed(self, uid: int, reason: str = "") -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/failed', params={"uid": uid, "reason": reason})
            return True
        except Exception as e:
            logger.error(f"通话失败上报失败: {e}")
            return False

    async def hangup(self, uid: int) -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/handup', params={"uid": uid})
            return True
        except Exception as e:
            logger.error(f"挂断通话失败: {e}")
            return False

    async def send_candidate(self, uid: int, candidate: str) -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/candidate', params={"uid": uid}, body=candidate)
            return True
        except Exception as e:
            logger.error(f"发送候选失败: {e}")
            return False

    async def send_heartbeat(self, uid: int) -> bool:
        try:
            await self.api.request('POST', '/api/webrtc/private/heartbeat', params={"uid": uid})
            return True
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")
            return False

class ChatHelper:
    def __init__(self, boxim_instance):
        self.boxim = boxim_instance
        self.private = PrivateMessageModule(boxim_instance)
        self.group = GroupMessageModule(boxim_instance)
        self.uploader = FileUploader(boxim_instance)

    def _split_image_tags(self, text: str) -> list:
        parts = []
        pattern = r"<send_image>(https?://[^\s<]+)</send_image>"
        last_end = 0
        for match in re.finditer(pattern, text):
            if match.start() > last_end:
                parts.append(text[last_end:match.start()])
            parts.append({"type": "image", "url": match.group(1)})
            last_end = match.end()
        if last_end < len(text):
            parts.append(text[last_end:])
        return parts

    async def _download_image_to_temp(self, url: str) -> Optional[str]:
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=timeout
            ) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"图片下载失败 {url}: HTTP {resp.status}")
                        return None
                    data = await resp.read()

                    content_type = resp.headers.get('Content-Type', '')
                    ext = None
                    if content_type:
                        try:
                            ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
                        except Exception:
                            ext = None
                    if not ext:
                        ext = '.jpg'

                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(data)
                        return tmp.name
        except Exception as e:
            logger.error(f"图片下载失败 {url}: {e}")
            return None

    async def send_private_text(self, user_id: int, text: str) -> Optional[int]:
        segments = self._split_image_tags(text)

        msg_id = None
        for i, seg in enumerate(segments):
            if isinstance(seg, str):
                if seg.strip():
                    msg_id = await self.private.send_message(user_id, seg, MessageType.TEXT)
            elif isinstance(seg, dict) and seg.get("type") == "image":
                image_url = seg["url"]
                temp_path = await self._download_image_to_temp(image_url)
                if not temp_path:
                    continue
                try:
                    result = await self.uploader.upload_image(temp_path)
                    if not result:
                        continue
                    content = json.dumps({
                        "originUrl": result.get("originUrl"),
                        "thumbUrl": result.get("thumbUrl"),
                        "width": result.get("width"),
                        "height": result.get("height")
                    })
                    msg_id = await self.private.send_message(user_id, content, MessageType.IMAGE)
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
        return msg_id

    async def send_private_image(self, user_id: int, image_path: str) -> Optional[int]:
        result = await self.uploader.upload_image(image_path)
        if not result:
            return None

        content = json.dumps({
            "originUrl": result.get("originUrl"),
            "thumbUrl": result.get("thumbUrl"),
            "width": result.get("width"),
            "height": result.get("height")
        })

        return await self.private.send_message(user_id, content, MessageType.IMAGE)

    async def send_private_file(self, user_id: int, file_path: str) -> Optional[int]:
        url = await self.uploader.upload_file(file_path)
        if not url:
            return None

        content = json.dumps({
            "name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "url": url
        })

        return await self.private.send_message(user_id, content, MessageType.FILE)

    async def send_private_voice(self, user_id: int, voice_path: str, duration: int = 0) -> Optional[int]:
        url = await self.uploader.upload_audio(voice_path)
        if not url:
            return None

        content = json.dumps({
            "duration": duration,
            "url": url
        })

        return await self.private.send_message(user_id, content, MessageType.VOICE)

    async def send_group_text(self, group_id: int, text: str, at_user_ids: List[int] = None) -> Optional[int]:
        segments = self._split_image_tags(text)

        msg_id = None
        for i, seg in enumerate(segments):
            if isinstance(seg, str):
                if seg.strip():
                    msg_id = await self.group.send_message(
                        group_id, seg, MessageType.TEXT,
                        at_user_ids=at_user_ids if i == 0 else None
                    )
            elif isinstance(seg, dict) and seg.get("type") == "image":
                image_url = seg["url"]
                temp_path = await self._download_image_to_temp(image_url)
                if not temp_path:
                    continue
                try:
                    result = await self.uploader.upload_image(temp_path)
                    if not result:
                        continue
                    content = json.dumps({
                        "originUrl": result.get("originUrl"),
                        "thumbUrl": result.get("thumbUrl"),
                        "width": result.get("width"),
                        "height": result.get("height")
                    })
                    msg_id = await self.group.send_message(
                        group_id, content, MessageType.IMAGE,
                        at_user_ids=at_user_ids if i == 0 else None
                    )
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
        return msg_id

    async def send_group_image(self, group_id: int, image_path: str, at_user_ids: List[int] = None) -> Optional[int]:
        result = await self.uploader.upload_image(image_path)
        if not result:
            return None

        content = json.dumps({
            "originUrl": result.get("originUrl"),
            "thumbUrl": result.get("thumbUrl"),
            "width": result.get("width"),
            "height": result.get("height")
        })

        return await self.group.send_message(group_id, content, MessageType.IMAGE, at_user_ids)

    async def send_group_file(self, group_id: int, file_path: str, at_user_ids: List[int] = None) -> Optional[int]:
        url = await self.uploader.upload_file(file_path)
        if not url:
            return None

        content = json.dumps({
            "name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "url": url
        })

        return await self.group.send_message(group_id, content, MessageType.FILE, at_user_ids)

    async def send_group_voice(self, group_id: int, voice_path: str, duration: int = 0, at_user_ids: List[int] = None) -> Optional[int]:
        url = await self.uploader.upload_audio(voice_path)
        if not url:
            return None

        content = json.dumps({
            "duration": duration,
            "url": url
        })

        return await self.group.send_message(group_id, content, MessageType.VOICE, at_user_ids)

class BoxIM:
    def __init__(self, auto_refresh_token: bool = True, auto_reconnect: bool = True, log_level: int = logging.INFO):
        self.auto_refresh_token = auto_refresh_token
        self.auto_reconnect = auto_reconnect
        logger.setLevel(log_level)

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.access_token_expires: float = 0
        self.refresh_token_expires: float = 0
        self.user_id: Optional[int] = None
        self.terminal: Terminal = Terminal.PC

        self.ws_connection: Optional[websockets.WebSocketClientProtocol] = None
        self.ws_task: Optional[asyncio.Task] = None
        self.ws_reconnect_count: int = 0
        self.ws_running: bool = False
        self._shutdown_event: Optional[asyncio.Event] = None

        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.command_handlers: Dict[str, Callable] = {}
        self.middleware_handlers: List[Callable] = []

        self.auth = AuthModule(self)
        self.user = UserModule(self)
        self.friend = FriendModule(self)
        self.group = GroupModule(self)
        self.private_message = PrivateMessageModule(self)
        self.group_message = GroupMessageModule(self)
        self.webrtc = WebRTCModule(self)
        self.chat = ChatHelper(self)
        self.uploader = FileUploader(self)

        self._tasks: List[asyncio.Task] = []

    @property
    def is_logged_in(self) -> bool:
        return self.access_token is not None and time.time() < self.access_token_expires

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "www.boxim.online",
            "Origin": Config.BASE_URL,
            "Referer": f"{Config.BASE_URL}/",
            "User-Agent": Config.USER_AGENT,
            "accessToken": self.access_token or "",
        }

    async def login(self, username: str, password: str, terminal: Terminal = Terminal.PC) -> bool:
        return await self.auth.login(username, password, terminal)

    async def register(self, username: str, password: str, nickName: str = None) -> bool:
        return await self.auth.register(username, password, nickName)

    async def refresh_access_token(self) -> bool:
        return await self.auth.refresh_token()

    async def modify_password(self, old_password: str, new_password: str) -> bool:
        return await self.auth.modify_password(old_password, new_password)

    def _start_token_refresh_task(self):
        async def refresh_task():
            while self.is_logged_in:
                try:
                    wait_time = max(0, self.access_token_expires - time.time() - Config.TOKEN_REFRESH_THRESHOLD)
                    await asyncio.sleep(wait_time)

                    if self.is_logged_in:
                        await self.refresh_access_token()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Token刷新任务异常: {e}")
                    await asyncio.sleep(60)

        task = asyncio.create_task(refresh_task())
        self._tasks.append(task)

    async def connect(self) -> bool:
        if not self.is_logged_in:
            logger.error("未登录，无法连接WebSocket")
            return False

        if self.ws_running:
            logger.warning("WebSocket已在运行")
            return True

        if self._shutdown_event is None:
            self._shutdown_event = asyncio.Event()

        self.ws_running = True
        self.ws_task = asyncio.create_task(self._ws_loop())
        self._tasks.append(self.ws_task)

        for _ in range(10):
            if self.ws_connection and not getattr(self.ws_connection, 'closed', False):
                return True
            await asyncio.sleep(0.5)

        return False

    async def disconnect(self):
        self.ws_running = False

        if self._shutdown_event:
            self._shutdown_event.set()

        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None

        if self.ws_task:
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                pass

    async def _ws_loop(self):
        while self.ws_running:
            try:
                await self._ws_connect()
            except Exception as e:
                logger.error(f"WebSocket异常: {e}")

            if self.ws_running and self.auto_reconnect:
                self.ws_reconnect_count += 1
                delay = min(Config.RECONNECT_DELAY * (2 ** self.ws_reconnect_count), Config.MAX_RECONNECT_DELAY)
                logger.info(f"将在{delay}秒后重连...")

                try:
                    if self._shutdown_event is None:
                        await asyncio.sleep(delay)
                    else:
                        try:
                            await asyncio.wait_for(self._shutdown_event.wait(), timeout=delay)
                            if self._shutdown_event.is_set():
                                break
                        except asyncio.TimeoutError:
                            pass
                except asyncio.CancelledError:
                    break
                except RuntimeError:
                    break
            else:
                break

    async def _ws_connect(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(f"正在连接WebSocket... (第{self.ws_reconnect_count + 1}次)")

        async with websockets.connect(Config.WS_URL, ssl=ssl_context) as websocket:
            self.ws_connection = websocket
            self.ws_reconnect_count = 0

            await self._ws_auth()

            heartbeat_task = asyncio.create_task(self._ws_heartbeat())

            try:
                await self._ws_receive()
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    async def _ws_auth(self):
        auth_msg = json.dumps({
            "cmd": WSCommand.AUTH.value,
            "data": {"accessToken": self.access_token}
        })
        await self.ws_connection.send(auth_msg)
        logger.info("WebSocket认证已发送")

    async def _ws_heartbeat(self):
        while True:
            try:
                heartbeat_msg = json.dumps({
                    "cmd": WSCommand.HEARTBEAT.value,
                    "data": {}
                })
                await self.ws_connection.send(heartbeat_msg)
                await asyncio.sleep(Config.HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                break

    async def _ws_receive(self):
        async for message in self.ws_connection:
            try:
                data = json.loads(message)
                await self._handle_ws_message(data)
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")

    async def _handle_ws_message(self, data: Dict):
        cmd = data.get('cmd')
        msg_data = data.get('data', {})

        if cmd == WSCommand.PRIVATE_MESSAGE:
            msg = Message(msg_data, is_group=False)
            await self._dispatch_message(msg, 'private')

        elif cmd == WSCommand.GROUP_MESSAGE:
            msg = Message(msg_data, is_group=True)
            await self._dispatch_message(msg, 'group')

        elif cmd == WSCommand.SYSTEM_MESSAGE:
            await self._dispatch_message(msg_data, 'system')

        elif cmd == WSCommand.FORCE_OFFLINE:
            logger.warning("收到强制下线通知")
            await self._dispatch_message(msg_data, 'offline')
            self.ws_running = False

    async def _dispatch_message(self, message: Union[Message, Dict], msg_type: str):
        if isinstance(message, Message):
            try:
                if message.type == MessageType.TEXT:
                    text = message.parsed_content.get('text', '')
                    if not str(text).strip():
                        logger.debug(f"过滤空文本消息: {message}")
                        return
                else:
                    parsed = message.parsed_content
                    if isinstance(parsed, dict) and parsed.get('raw', '') == '':
                        logger.debug(f"过滤内容为空的消息: {message}")
                        return
            except Exception:
                pass

        for handler in self.middleware_handlers:
            try:
                result = await handler(message, msg_type)
                if result is False:
                    return
            except Exception as e:
                logger.error(f"中间件处理异常: {e}")

        if isinstance(message, Message) and message.type == MessageType.TEXT:
            text = message.parsed_content.get('text', '')
            if text.startswith('/'):
                parts = text.split(maxsplit=1)
                cmd = parts[0][1:].lower()
                args = parts[1] if len(parts) > 1 else ''

                if cmd in self.command_handlers:
                    try:
                        await self.command_handlers[cmd](message, args)
                        return
                    except Exception as e:
                        logger.error(f"命令处理异常: {e}")

        for handler in self.message_handlers.get(msg_type, []):
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"消息处理异常: {e}")

    def on_private_message(self, func: Callable = None):
        def decorator(f):
            self.message_handlers['private'].append(f)
            return f
        return decorator(func) if func else decorator

    def on_group_message(self, func: Callable = None):
        def decorator(f):
            self.message_handlers['group'].append(f)
            return f
        return decorator(func) if func else decorator

    def on_system_message(self, func: Callable = None):
        def decorator(f):
            self.message_handlers['system'].append(f)
            return f
        return decorator(func) if func else decorator

    def command(self, *commands: str):
        def decorator(func):
            for cmd in commands:
                self.command_handlers[cmd.lower()] = func
            return func
        return decorator

    def middleware(self, func: Callable = None):
        def decorator(f):
            self.middleware_handlers.append(f)
            return f
        return decorator(func) if func else decorator

    def on_message(self, message_types: List[MessageType] = None, chat_types: List[str] = None):
        def decorator(func):
            async def wrapper(message):
                if message_types and message.type not in [t.value for t in message_types]:
                    return
                await func(message)

            for chat_type in (chat_types or ['private', 'group']):
                self.message_handlers[chat_type].append(wrapper)

            return func
        return decorator

    async def run(self):
        if not self.is_logged_in:
            raise AuthException("请先登录")

        await self.connect()

        try:
            await asyncio.gather(*self._tasks)
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.stop()

    async def start(self):
        if not self.is_logged_in:
            raise AuthException("请先登录")

        await self.connect()

    async def stop(self):
        logger.info("正在停止BoxIM...")

        try:
            await self.disconnect()
        except Exception as e:
            logger.error(f"断开WebSocket时出错: {e}")

        for task in list(self._tasks):
            if not task.done():
                try:
                    task.cancel()
                except Exception:
                    pass

        if self._tasks:
            try:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"等待任务结束时出错: {e}")

        self._tasks.clear()
        logger.info("BoxIM已停止")

    def __repr__(self) -> str:
        status = "已登录" if self.is_logged_in else "未登录"
        ws_status = "已连接" if self.ws_connection and not self.ws_connection.closed else "未连接"
        return f"BoxIM(status={status}, ws={ws_status}, user_id={self.user_id})"

async def example():
    bot = BoxIM(auto_refresh_token=True, auto_reconnect=True)

    if not await bot.login("用户名", "密码"):
        print("登录失败")
        return

    @bot.on_private_message
    async def handle_private(message: Message):
        print(f"收到私聊: {message}")
        await bot.chat.send_private_text(message.send_id, f"收到: {message.content}")

    @bot.on_group_message
    async def handle_group(message: Message):
        print(f"收到群聊: {message}")
        if bot.user_id in message.at_user_ids:
            await bot.chat.send_group_text(
                message.group_id,
                "收到@",
                at_user_ids=[message.send_id]
            )

    await bot.run()

if __name__ == "__main__":
    asyncio.run(example())
