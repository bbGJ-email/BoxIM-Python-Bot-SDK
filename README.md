# Box IM Python SDK

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

完整规范的Box IM即时通讯Python SDK，支持用户登录、消息收发、群组管理等功能。

## 功能特性

- ✅ **用户认证** - 支持账号密码登录、Token刷新
- ✅ **消息管理** - 发送/接收私聊、群聊消息，支持多种消息类型
- ✅ **群组管理** - 创建、修改、解散群组，管理成员
- ✅ **好友管理** - 添加、删除好友，查看好友列表
- ✅ **文件上传** - 支持图片和文件上传
- ✅ **WebSocket** - 实时消息推送
- ✅ **WebRTC** - 音视频通话支持

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

已完成所有API接口与后端的一致性验证：

### ✅ 已验证可用接口

**登录认证**
- `POST /api/login` - 用户登录
- `PUT /refreshToken` - 刷新Token
- `POST /register` - 用户注册
- `PUT /modifyPwd` - 修改密码

**用户管理**
- `GET /user/self` - 获取当前用户信息
- `GET /user/find/{id}` - 根据ID查找用户
- `PUT /user/update` - 修改用户信息

**消息管理**
- `POST /message/private/send` - 发送私聊消息
- `POST /message/group/send` - 发送群聊消息
- `DELETE /message/private/recall/{id}` - 撤回私聊消息
- `POST /message/private/history` - 查询历史消息

**群组管理**
- `POST /group/create` - 创建群组
- `PUT /group/modify` - 修改群组信息
- `POST /group/invite` - 邀请成员
- `DELETE /group/members/remove` - 移除成员

**好友管理**
- `GET /friend/list` - 好友列表
- `POST /friend/add` - 添加好友
- `DELETE /friend/delete/{friendId}` - 删除好友

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

### BoxIMBotSDK

主SDK类

**方法**

| 方法名 | 说明 |
|--------|------|
| `start_with_password(username, password)` | 用户账号密码登录 |
| `send_message(to_id, content, content_type)` | 发送私聊消息 |
| `send_group_message(group_id, content, content_type)` | 发送群聊消息 |
| `stop()` | 登出并断开连接 |
| `get_version()` | 获取SDK版本号 |
| `get_info()` | 获取SDK信息 |

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
- 支持用户账号密码登录
- 支持私聊和群聊消息
- 支持群组和好友管理
- 添加完整的API接口验证

## 联系方式

作者: 归鸿  
邮箱: xingk2026@126.com

---

> ⚠️ 注意：机器人登录接口目前不存在，请使用用户账号密码登录方式。