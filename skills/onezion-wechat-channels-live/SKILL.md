---
name: onezion-wechat-channels-live
description: >
  多平台直播录制 + 视频号专属下载 + 智能总结一体化工具。
  整合 StreamCap/streamget（50+ 平台直播录制）与 wechatVideoDownload（视频号视频/直播下载），
  录制完成后可自动调用 onezion-video-summarize 进行转录与总结。
  触发词：直播录制、视频号直播、live stream recording、看直播、总结直播、
  录制直播间、直播回放、download live、record live、wechat channels live。
agent_created: true
---

# onezion-wechat-channels-live

多平台直播录制 + 视频号专属下载 + 智能总结一体化 skill。

## 架构

```
┌─────────────────────────────────────────────────┐
│              onezion-wechat-channels-live        │
├────────────────────┬────────────────────────────┤
│   streamget        │   wechatVideoDownload      │
│   (50+ 平台)       │   (视频号专属)             │
│   Python CLI       │   Windows GUI              │
│   解析流URL+录制   │   自动监听 + 一键下载      │
├────────────────────┴────────────────────────────┤
│              FFmpeg 录制引擎                      │
├─────────────────────────────────────────────────┤
│   onezion-video-summarize (转录 + 总结)          │
└─────────────────────────────────────────────────┘
```

## 工具选择指南

| 场景 | 工具 | 说明 |
|------|------|------|
| B站/抖音/快手/Twitch/YouTube 等 50+ 平台 | **streamget + FFmpeg** | Agent 可直接调用，全自动 |
| StreamCap GUI 批量监控 | **StreamCap 桌面/Web** | 纯 GUI，适合长期监控多个主播 |
| 微信视频号（Windows） | **wechatVideoDownload** | 仅 Windows，需微信 PC 运行 |
| 微信视频号（macOS） | **抓包 + FFmpeg** 或 **屏幕录制** | 需手动获取流 URL |

**重要**：StreamCap 是纯 GUI 应用（Flet 框架），**没有 REST API**，无法被 Agent 直接调用。
Agent 自动化录制使用底层 `streamget` 库 + FFmpeg，无需启动 StreamCap GUI。

## 依赖

- **Python 3.10+**
- **FFmpeg**（录制 + 转码核心）
- **streamget**（pip 包，StreamCap 底层流获取库）

检查依赖：
```bash
python3 --version && ffmpeg -version && pip3 show streamget
```

## 快速安装

```bash
bash ~/.workbuddy/skills/onezion-wechat-channels-live/scripts/setup.sh
```

安装内容：
1. 通过 pip 安装 `streamget`
2. 克隆 StreamCap 仓库到 `~/Tools/StreamCap/`（可选，用于 GUI 模式）
3. 检查 FFmpeg 是否已安装

---

## 使用方式

### 一、Agent 自动录制（streamget + FFmpeg）

这是 Agent 可直接调用的自动化路径，适用于 50+ 平台。

#### 基本用法

```bash
# 一键录制（自动解析流 URL + FFmpeg 录制）
python3 ~/.workbuddy/skills/onezion-wechat-channels-live/scripts/record_and_summarize.py \
  --url "https://live.bilibili.com/xxxxx" \
  --duration 3600 \
  --output ~/records/stream.flv

# 录制完成后自动调用总结
python3 ~/.workbuddy/skills/onezion-wechat-channels-live/scripts/record_and_summarize.py \
  --url "https://live.bilibili.com/xxxxx" \
  --duration 3600 \
  --summarize

# 直接用流 URL 录制（适用于视频号等 streamget 不支持的平台）
python3 ~/.workbuddy/skills/onezion-wechat-channels-live/scripts/record_and_summarize.py \
  --stream-url "https://pull-flv-xxx.flv" \
  --output ~/records/wechat_live.flv
```

#### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--url` | 直播间 URL（自动解析流地址） | `https://live.bilibili.com/12345` |
| `--stream-url` | 直接提供流 URL（跳过解析） | `https://pull-flv-xxx.flv` |
| `--duration` | 录制时长（秒），不指定则持续录制 | `3600`（1小时） |
| `--output` | 输出文件路径 | `~/records/stream.flv` |
| `--summarize` | 录制完成后自动总结 | |
| `--check` | 仅检查依赖 | |

#### 支持的平台（streamget 50+）

**国内（30+）**：抖音、快手、虎牙、斗鱼、B站、小红书、YY、映客、AcFun、京东、淘宝等

**海外（10+）**：TikTok、Twitch、PandTV、Soop、Twitcasting、CHZZK、Shopee、YouTube、LiveMe、Flextv、Popkontv、Bigo 等

#### 注意事项

- YouTube、淘宝等平台需要 cookies
- 小红书、花椒等使用一次性 URL，不支持循环监控
- 抖音短链接需要 Node.js 环境

---

### 二、StreamCap GUI（批量监控，可选）

StreamCap 是基于 Flet 的桌面/Web GUI，适合长期监控多个主播。

**注意：StreamCap 没有 REST API，无法被 Agent 直接调用。仅作为人工操作的 GUI 工具。**

#### 启动

```bash
# 桌面模式
cd ~/Tools/StreamCap && python3 main.py

# Web 模式（浏览器访问）
cd ~/Tools/StreamCap && python3 main.py --web
# 访问 http://127.0.0.1:6006
```

#### 功能

| 功能 | 说明 |
|------|------|
| 循环监控 | 实时监控，开播自动录制 |
| 定时任务 | 在设定时间段内检查并录制 |
| 批量录制 | 同时监控多个直播间 |
| 分段录制 | 按时长切分文件（默认30分钟/段） |
| 自动转码 | 录制完成后自动转为 MP4 |
| 消息推送 | 开播状态通知 |

#### 配置

通过 `.env` 文件配置环境变量：
```bash
nano ~/Tools/StreamCap/.env
```

录制任务通过 GUI 界面添加（点击 "+" 按钮），配置直播间 URL、录制格式、质量等。

#### DMG 安装（macOS）

也可直接下载预编译包：
- 下载：https://github.com/ihmily/StreamCap/releases/latest
- 双击 `.dmg` 安装
- 如提示"应用已损坏"：`sudo xattr -rd com.apple.quarantine /Applications/StreamCap.app`

---

### 三、wechatVideoDownload — 视频号专属

#### 功能

- 视频号视频下载（含加密视频自动解密）
- 视频号直播录制（实时）
- 视频号直播回放下载
- 视频号图片下载
- 自动监听微信客户端流量

#### 平台限制

- **仅支持 Windows**
- 需要微信 PC 客户端运行
- 最新版本：v2.6（2025-01-03）

#### Windows 上安装使用

1. 下载：https://pan.quark.cn/s/02054d6f9664 （v2.6）
2. 解压后运行 exe
3. 点击"开始监听"
4. 在微信中打开视频号，软件自动捕获
5. 选择下载或复制链接

#### macOS 替代方案

**方案 A：抓取直播流 URL + FFmpeg**

1. 在微信中打开视频号直播间
2. 使用 Charles/Proxyman 等抓包工具捕获直播流
3. 找到 `https://pull-m*.wxlivecdn.com/*.flv` 格式的流地址
4. 使用 FFmpeg 录制：
   ```bash
   ffmpeg -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 \
     -i "直播流URL" -c copy output.flv
   ```

**方案 B：屏幕录制（onezion-screenpipe）**

使用 `onezion-screenpipe` 进行持续屏幕+音频录制，适合无法获取流 URL 的场景。

**方案 C：虚拟机**

在 Parallels/VMware 中运行 Windows + wechatVideoDownload。

---

### 四、录制 + 总结一体化

录制完成后自动调用 `onezion-video-summarize`：

```bash
# 录制 + 自动总结
python3 ~/.workbuddy/skills/onezion-wechat-channels-live/scripts/record_and_summarize.py \
  --url "https://live.bilibili.com/xxxxx" \
  --duration 3600 \
  --summarize
```

总结流程：
1. 录制完成 → 生成 `.flv/.mp4` 文件
2. 调用 `onezion-video-summarize` → 云端转录 API（优先）+ 摘要生成
3. 输出结构化总结文档

---

## Agent 交互流程

当用户说"帮我录制/总结某个直播"时：

1. **确认平台**：视频号？还是其他平台？
2. **确认目标**：直播间 URL
3. **确认需求**：只录制 / 录制+总结 / 直接总结已有录像
4. **执行**：
   - streamget 支持的平台 → `record_and_summarize.py --url`
   - 视频号 → 抓包获取流 URL → `record_and_summarize.py --stream-url`
   - 已有录像 → 直接调用 `onezion-video-summarize`
5. **输出**：录制文件 + 总结文档

## 常见问题

**Q: StreamCap 支持视频号吗？**
A: 不支持。streamget/StreamCap 平台列表中没有微信视频号（GitHub 上有 3 个 open issue 请求此功能，暂无实现计划）。

**Q: wechatVideoDownload 能在 Mac 上用吗？**
A: 不能，Windows 专用。Mac 上用抓包+FFmpeg 或屏幕录制替代。

**Q: 录制的视频太大怎么办？**
A: 用 `onezion-video-compress` 压缩后再总结。

**Q: 部分平台需要 cookies？**
A: YouTube、淘宝等需要。StreamCap GUI 模式下可在界面中配置；CLI 模式需自行处理 cookies。

**Q: 循环监控某主播开播？**
A: 使用 StreamCap GUI 的"循环监控"功能，Agent 无法直接操作此功能（无 API）。
