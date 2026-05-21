# Box IM Python SDK

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

完整规范的Box IM即时通讯Python SDK，支持用户登录、消息收发、群组管理、文件上传、WebRTC音视频通话等功能。

## 功能特性

- ✅ **用户认证** - 支持账号密码登录、注册、Token刷新、密码修改
- ✅ **消息管理** - 发送/接收私聊、群聊消息，支持多种消息类型
- ✅ **离线消息** - 支持拉取离线消息
- ✅ **消息撤回** - 支持私聊和群聊消息撤回
- ✅ **群组管理** - 创建、修改、解散群组，管理成员
- ✅ **好友管理** - 添加、删除好友，查看好友列表和在线状态
- ✅ **文件上传** - 支持图片和文件上传
- ✅ **WebSocket** - 实时消息推送
- ✅ **WebRTC** - 音视频通话支持（呼叫、接听、拒绝、挂断）

## 安装

```bash
pip install aiohttp websockets
```

## 快速开始

```python
import asyncio
from box_im_bot_sdk import BoxIMBotSDK, BotConfig, MessageType

async def main():
    # 配置SDK
    config = BotConfig(
        api_base_url='https://www.boxim.online',
        ws_url='wss://www.boxim.online'
    )
    
    # 创建SDK实例
    sdk = BoxIMBotSDK(config)
    
    # 用户账号密码登录
    login_result = await sdk.start_with_password('username', 'password')
    print(f"登录成功: {login_result.user.nickname}")
    
    # 发送私聊消息
    message = await sdk.send_message('target_user_id', 'Hello World!')
    print(f"消息发送成功: {message.id}")
    
    # 发送群聊消息
    group_message = await sdk.send_group_message('group_id', '大家好!')
    print(f"群消息发送成功: {group_message.id}")

if __name__ == '__main__':
    asyncio.run(main())
```

## API 接口验证

已完成所有API接口与后端的一致性验证，共**52个接口**全部实现：

### ✅ 登录认证 (4个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| POST | /api/login | 用户登录 |
| POST | /register | 用户注册 |
| PUT | /refreshToken | 刷新Token |
| PUT | /modifyPwd | 修改密码 |

### ✅ 用户管理 (5个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| GET | /user/self | 获取当前用户信息 |
| GET | /user/find/{id} | 根据ID查找用户 |
| PUT | /user/update | 修改用户信息 |
| GET | /user/findByName | 根据用户名查找用户 |
| GET | /user/terminal/online | 判断用户终端在线 |

### ✅ 私聊消息 (8个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| POST | /message/private/send | 发送私聊消息 |
| DELETE | /message/private/recall/{id} | 撤回私聊消息 |
| GET | /message/private/loadOfflineMessage | 拉取离线消息 |
| PUT | /message/private/readed | 消息已读 |
| GET | /message/private/maxReadedId | 获取最大已读消息ID |
| DELETE | /message/private/deleteMessage | 删除消息 |
| DELETE | /message/private/deleteChat | 删除会话 |
| POST | /message/private/history | 查询历史消息 |

### ✅ 群聊消息 (8个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| POST | /message/group/send | 发送群聊消息 |
| DELETE | /message/group/recall/{id} | 撤回群聊消息 |
| GET | /message/group/loadOfflineMessage | 拉取离线消息 |
| PUT | /message/group/readed | 消息已读 |
| GET | /message/group/findReadedUsers | 获取已读用户ID |
| DELETE | /message/group/deleteMessage | 删除消息 |
| DELETE | /message/group/deleteChat | 删除会话 |
| POST | /message/group/history | 查询历史消息 |

### ✅ 群组管理 (11个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| POST | /group/create | 创建群聊 |
| PUT | /group/modify | 修改群聊信息 |
| DELETE | /group/delete/{groupId} | 解散群聊 |
| GET | /group/find/{groupId} | 查询单个群聊 |
| GET | /group/list | 查询群聊列表 |
| POST | /group/invite | 邀请进群 |
| GET | /group/members/{groupId} | 查询群聊成员 |
| GET | /group/members/online/{groupId} | 查询在线成员 |
| DELETE | /group/members/remove | 移除成员 |
| DELETE | /group/quit/{groupId} | 退出群聊 |
| PUT | /group/dnd | 免打扰设置 |

### ✅ 好友管理 (6个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| GET | /friend/list | 好友列表 |
| GET | /friend/online | 好友在线情况 |
| POST | /friend/add | 添加好友 |
| GET | /friend/find/{friendId} | 查找好友信息 |
| DELETE | /friend/delete/{friendId} | 删除好友 |
| PUT | /friend/dnd | 免打扰设置 |

### ✅ 文件上传 (2个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| POST | /image/upload | 上传图片 |
| POST | /file/upload | 上传文件 |

### ✅ WebRTC通话 (8个)

| HTTP方法 | 路径 | 说明 |
|---------|------|------|
| POST | /webrtc/private/call | 呼叫视频通话 |
| POST | /webrtc/private/accept | 接受视频通话 |
| POST | /webrtc/private/reject | 拒绝视频通话 |
| POST | /webrtc/private/cancel | 取消呼叫 |
| POST | /webrtc/private/failed | 呼叫失败 |
| POST | /webrtc/private/handup | 挂断 |
| POST | /webrtc/private/candidate | 同步candidate |
| POST | /webrtc/private/heartbeat | 心跳 |

### ⚠️ 注意事项

**机器人登录接口不存在**

后端系统中 `/auth/bot/login` 接口目前不存在，请使用用户账号密码登录方式：

```python
# 正确方式
login_result = await sdk.start_with_password('username', 'password')

# 不可用（机器人登录接口不存在）
# await sdk.start()
```

## 核心类说明

### BotConfig

SDK配置类

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| api_base_url | str | 是 | API基础URL |
| ws_url | str | 是 | WebSocket URL |
| bot_id | str | 否 | 机器人ID（暂不支持） |
| bot_secret | str | 否 | 机器人密钥（暂不支持） |
| request_timeout | int | 否 | 请求超时时间（默认30秒） |
| auto_reconnect | bool | 否 | 是否自动重连（默认True） |
| reconnect_interval | int | 否 | 重连间隔（默认5秒） |
| max_reconnect_attempts | int | 否 | 最大重连次数（默认5次） |
| heartbeat_interval | int | 否 | 心跳间隔（默认30秒） |
| enable_logging | bool | 否 | 是否启用日志（默认True） |
| log_level | LogLevel | 否 | 日志级别（默认INFO） |

### BoxIMBotSDK

主SDK类

**方法**

| 方法名 | 说明 |
|--------|------|
| `start_with_password(username, password)` | 用户账号密码登录 |
| `stop()` | 登出并断开连接 |
| `send_message(to_id, content, content_type)` | 发送私聊消息 |
| `send_group_message(group_id, content, content_type)` | 发送群聊消息 |
| `get_version()` | 获取SDK版本号 |
| `get_info()` | 获取SDK信息 |

**属性**

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `client` | BotClient | 获取底层客户端实例 |
| `message_manager` | MessageManager | 消息管理器 |
| `group_manager` | GroupManager | 群组管理器 |
| `user_manager` | UserManager | 用户管理器 |
| `file_manager` | FileManager | 文件管理器 |
| `webrtc_manager` | WebRTCManager | WebRTC管理器 |

### MessageType

消息类型枚举

| 值 | 名称 | 说明 |
|----|------|------|
| 1 | TEXT | 文本消息 |
| 2 | IMAGE | 图片消息 |
| 3 | VOICE | 语音消息 |
| 4 | VIDEO | 视频消息 |
| 5 | FILE | 文件消息 |
| 6 | CARD | 卡片消息 |
| 7 | NOTICE | 通知消息 |
| 8 | RECALL | 撤回消息 |
| 9 | TIMELINE | 时间线消息 |
| 100 | CUSTOM | 自定义消息 |

## 使用示例

### 发送不同类型消息

```python
# 发送文本消息
await sdk.send_message('user_id', 'Hello', MessageType.TEXT)

# 发送图片消息
await sdk.send_message('user_id', {'url': 'https://example.com/image.jpg'}, MessageType.IMAGE)

# 发送自定义消息
await sdk.send_message('user_id', {'type': 'custom', 'data': {}}, MessageType.CUSTOM)
```

### 用户注册和登录

```python
# 用户注册
register_result = await sdk.client.register(
    username='new_user',
    password='password123',
    nickname='新用户',
    email='user@example.com'
)

# 用户登录
login_result = await sdk.start_with_password('username', 'password')

# 刷新Token
new_token = await sdk.client.refresh_token('refresh_token')

# 修改密码
await sdk.client.modify_password('old_password', 'new_password')
```

### 消息管理

```python
# 拉取离线消息
offline_messages = await sdk.client.message_manager.load_offline_messages()

# 获取历史消息
history = await sdk.client.message_manager.get_private_history('friend_id')

# 撤回消息
await sdk.client.message_manager.recall_private_message('message_id')

# 删除消息
await sdk.client.message_manager.delete_private_message('message_id')

# 删除会话
await sdk.client.message_manager.delete_private_chat('friend_id')
```

### 群组管理

```python
# 创建群组
group = await sdk.client.group_manager.create_group('我的群组', '群组描述')

# 邀请成员
await sdk.client.group_manager.invite_members('group_id', ['user1', 'user2'])

# 获取群成员
members = await sdk.client.group_manager.get_members('group_id')

# 退出群组
await sdk.client.group_manager.quit_group('group_id')
```

### 文件上传

```python
# 上传图片
image_url = await sdk.client.file_manager.upload_image('/path/to/image.jpg')

# 上传文件
file_url = await sdk.client.file_manager.upload_file('/path/to/file.pdf')
```

### WebRTC通话

```python
# 发起视频通话
call_result = await sdk.client.webrtc_manager.call('target_id', 'video')

# 接受通话
await sdk.client.webrtc_manager.accept('call_id')

# 拒绝通话
await sdk.client.webrtc_manager.reject('call_id')

# 挂断通话
await sdk.client.webrtc_manager.hangup('call_id')
```

### 监听消息事件

```python
def on_message_received(message):
    print(f"收到消息: {message.content}")

sdk.on('message', on_message_received)
```

### 获取版本信息

```python
# 获取版本号
print(f"SDK版本: {BoxIMBotSDK.get_version()}")

# 获取完整信息
info = BoxIMBotSDK.get_info()
print(f"作者: {info['author']}")
print(f"许可证: {info['license']}")
```

## 许可证

MIT License

Copyright (c) 2026 归鸿

## 版本历史

### v1.0.0 (2026-05-21)
- 初始版本发布
- 实现全部52个API接口
- 支持用户账号密码登录、注册、Token刷新
- 支持私聊和群聊消息收发、撤回、历史查询
- 支持群组创建、管理、成员操作
- 支持好友添加、删除、在线状态查询
- 支持文件和图片上传
- 支持WebRTC音视频通话

## 联系方式

作者: 归鸿  
邮箱: xingk2026@126.com

---

> ⚠️ 注意：机器人登录接口目前不存在，请使用用户账号密码登录方式。