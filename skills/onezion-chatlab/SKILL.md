---
name: onezion-chatlab
description: "ChatLab 本地聊天记录查询工具。通过 ChatLab REST API 查询、搜索、统计导入的聊天记录（WhatsApp、微信等）。支持关键词搜索、SQL 聚合查询、会话管理、数据导入导出。触发词：ChatLab、聊天记录、chat history、search chat、聊天搜索、查询消息、聊天统计"
agent_created: true
triggers:
  - "ChatLab"
  - "chatlab"
  - "聊天记录"
  - "chat history"
  - "search chat"
  - "聊天搜索"
  - "查询消息"
  - "聊天统计"
  - "聊天导出"
---

# onezion-chatlab — ChatLab 本地聊天记录查询

通过 ChatLab REST API 查询、搜索和分析导入的本地聊天记录。

## 前置条件

ChatLab API 已启用（Settings → ChatLab API → Enable Service）。Token 已配置，无需用户额外操作。

## API 配置

| 项目 | 值 |
|------|-----|
| **Base URL** | `http://127.0.0.1:5200` |
| **API Prefix** | `/api/v1` |
| **认证** | `Authorization: Bearer clb_7724398278d03a8fd3f3753430625ee99e4b1e093d0aa6c23fb46e8be62ed1c3` |
| **数据格式** | JSON |

Token 前缀为 `clb_`。如过期，引导用户到 ChatLab Settings → ChatLab API 重新生成。

## 常用 curl 命令模板

所有请求都必须带上认证 header：

```bash
TOKEN="clb_7724398278d03a8fd3f3753430625ee99e4b1e093d0aa6c23fb46e8be62ed1c3"
AUTH="-H 'Authorization: Bearer $TOKEN'"
```

### 服务状态

```bash
curl -s http://127.0.0.1:5200/api/v1/status \
  -H "Authorization: Bearer $TOKEN"
```

### 列出所有会话

```bash
curl -s http://127.0.0.1:5200/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN"
```

### 获取单个会话详情

```bash
curl -s http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID> \
  -H "Authorization: Bearer $TOKEN"
```

### 查询消息（带过滤）

```bash
# 关键词搜索
curl -s "http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/messages?keyword=<KEYWORD>&page=1&limit=50" \
  -H "Authorization: Bearer $TOKEN"

# 时间范围过滤（Unix 时间戳）
curl -s "http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/messages?startTime=1700000000&endTime=1710000000" \
  -H "Authorization: Bearer $TOKEN"

# 按发送者过滤
curl -s "http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/messages?senderId=<SENDER_ID>" \
  -H "Authorization: Bearer $TOKEN"

# 组合过滤
curl -s "http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/messages?keyword=<KEYWORD>&startTime=<TS>&endTime=<TS>&senderId=<ID>&page=1&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

消息查询支持参数：`page`, `limit`（最大1000）, `startTime`, `endTime`（Unix时间戳）, `keyword`, `senderId`, `type`

### 获取成员列表

```bash
curl -s http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/members \
  -H "Authorization: Bearer $TOKEN"
```

### 获取会话统计概览

```bash
curl -s http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/stats/overview \
  -H "Authorization: Bearer $TOKEN"
```

### 执行 SQL 查询（只读）

```bash
curl -s -X POST http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/sql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT sender, COUNT(*) as count FROM messages GROUP BY sender ORDER BY count DESC LIMIT 10"}'
```

**注意：仅允许 SELECT 查询。** 常用 SQL 示例：

```sql
-- 消息数量按发送者统计
SELECT sender, COUNT(*) as count FROM messages GROUP BY sender ORDER BY count DESC;

-- 按日期统计消息量
SELECT date(timestamp, 'unixepoch') as day, COUNT(*) as count FROM messages GROUP BY day ORDER BY day;

-- 关键词搜索（SQL 方式）
SELECT * FROM messages WHERE content LIKE '%关键词%' ORDER BY timestamp DESC LIMIT 20;

-- 最活跃时段
SELECT strftime('%H', timestamp, 'unixepoch') as hour, COUNT(*) as count FROM messages GROUP BY hour ORDER BY count DESC;
```

### 导出会话

```bash
curl -s "http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/export" \
  -H "Authorization: Bearer $TOKEN"
```

导出限制：最多 100,000 条消息。

### 导入聊天记录

```bash
# JSON 格式（50MB 限制）
curl -s -X POST http://127.0.0.1:5200/api/v1/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @chatlab-format.json

# 增量导入到现有会话
curl -s -X POST http://127.0.0.1:5200/api/v1/sessions/<SESSION_ID>/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @new-messages.json
```

## 工作流程

### 查询聊天记录时

1. 先用 `GET /sessions` 获取会话列表，确认目标会话 ID
2. 用 `GET /sessions/:id/members` 获取成员列表（了解发送者）
3. 根据需求选择：
   - 简单搜索 → `GET /sessions/:id/messages?keyword=xxx`
   - 统计分析 → `POST /sessions/:id/sql` 执行聚合查询
   - 内容导出 → `GET /sessions/:id/export`

### 分析聊天内容时

1. 先用 `GET /sessions/:id/stats/overview` 了解整体概况
2. 用 SQL 查询进行维度分析（按人、按时间、按类型）
3. 用关键词搜索定位具体消息
4. 结果过多时分页获取（`page` 参数）

### 导入新聊天记录时

1. 确认 ChatLab Format JSON 格式正确
2. 用 `POST /import` 创建新会话
3. 后续增量数据用 `POST /sessions/:id/import` 导入
4. 去重规则：`timestamp + senderPlatformId + contentLength`

## 注意事项

- ChatLab 服务仅绑定 `127.0.0.1`，仅本地可访问
- SQL 查询只允许 `SELECT`，不支持写操作
- 消息分页最大每页 1000 条
- 导出最多 100,000 条消息
- JSON 导入 body 限制 50MB，JSONL 流式导入无限制
- 同一时间只能执行一个导入任务
