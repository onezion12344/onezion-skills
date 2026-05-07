---
name: onezion-video-summarize
description: 智能视频分析工具，支持在线视频（YouTube、Bilibili 等 1000+ 站点）和本地视频（.mov、.mp4、.mkv）的内容总结、转录、提取。触发词：视频总结、视频转录、video summarize、summarize video、视频摘要、帮我总结这个视频.
allowed-tools: Bash, Read, Write, WebFetch, AskUserQuestion
agent_created: true
---

# 视频内容总结 (Video Summarizer)

智能视频分析工具，根据视频类型自动选择最优分析策略，**在保证质量的前提下最大限度节省 token 消耗**。

支持两种输入：
- **在线视频**：YouTube、Bilibili、Twitter/X、抖音、小红书等 1000+ 站点
- **本地视频**：.mov、.mp4、.mkv 等本地文件

## When to Use

- 用户发送任何视频链接并要求总结/摘要/提取内容
- 用户发送本地视频文件路径要求分析
- 关键词：总结视频、视频摘要、这个视频讲了什么、帮我看看这个视频、转录、视频内容分析

## Token 消耗参考（MiMo-V2.5）

> ⚠️ 视频是最费 token 的输入类型。以下是估算值：

| 分析方式 | 10秒视频估算 token | 10秒视频估算费用（V2.5） | 适用场景 |
|---------|-------------------|------------------------|---------|
| **直接发送视频给模型** | 20-50 万 token | ¥0.56-1.40 | ❌ 不推荐，极度浪费 |
| **抽取关键帧 + 音频转录** | 0.5-2 万 token | ¥0.01-0.06 | ✅ **推荐：性价比最高** |
| **纯音频转录（无画面）** | 0.3-0.5 万 token | ¥0.01 | ✅ 适合纯讲话/播客类 |

> 💡 **核心原则**：永远不要直接把原始视频发给模型。先用 ffmpeg 抽帧 + MiMo 音频转录，再用文本/图片喂给 LLM，可节省 **95%+** 的 token。

## 视频类型判断与分析策略

### 分析前：判断视频类型

在开始分析前，先快速判断视频属于哪种类型，选择对应策略：

| 视频类型 | 特征 | 分析策略 | 抽帧数 |
|---------|------|---------|--------|
| 🎤 **讲话/播客/访谈** | 一个人或多个人说话，画面变化少 | 以**音频转录**为主，抽 1-2 帧封面即可 | 1-2 帧 |
| 📊 **教程/演示/录屏** | 屏幕操作、PPT、代码演示 | 音频转录 + 每 5-10 秒抽 1 帧 | 3-5 帧/分钟 |
| 🎬 **Vlog/生活记录** | 画面频繁变化，有字幕和BGM | 音频转录 + 每 2-3 秒抽 1 帧 | 10-15 帧/分钟 |
| 🎮 **游戏/动作/特效** | 画面变化剧烈，视觉信息为主 | 多抽帧（每秒 1 帧），音频为辅 | 15-30 帧/分钟 |
| 📰 **新闻/资讯** | 主播+画面切换 | 音频转录为主 + 关键画面帧 | 3-5 帧/分钟 |

### 决策流程

```
1. 获取视频元数据（时长、分辨率、帧率）
2. 判断视频类型（看前 3 秒 + 时长）
3. 选择分析策略：
   - 短视频（< 30秒）→ 抽 3-5 帧 + 全部音频
   - 中等（30秒-5分钟）→ 按类型抽帧 + 音频转录
   - 长视频（> 5分钟）→ 按类型抽帧 + 音频转录（MiMo mimo-v2-omni）
4. 将关键帧图片 + 转录文本发给 LLM 生成总结
```

## Prerequisites

- `yt-dlp`（已预装）
- FFmpeg（yt-dlp 依赖）
- `MIMO_API_KEY` 环境变量（或 mimo-mcp 已配置，用于音频转录和文本总结）
- MiMo API Base URL: `https://token-plan-sgp.xiaomimimo.com/v1`（Token Plan SGP 节点）
- Python 3 + `openai` 库（`pip install openai`）
- Safari 浏览器（部分站点如 B 站需要 Cookie）

## Workflow

### Step 0: 判断视频类型 & 选择策略

```bash
# 获取视频基本信息（在线或本地）
# 在线视频
yt-dlp --print title --print duration_string --print description "VIDEO_URL"
# 本地视频
ffprobe -v quiet -print_format json -show_format -show_streams "VIDEO_PATH"
```

根据输出判断视频类型，确定抽帧策略（见上方表格）。

### Step 1: 获取视频信息 & 下载

**在线视频：**
```bash
# 获取信息
yt-dlp --print title --print duration_string --print description "VIDEO_URL"

# B 站等需要 Cookie 的站点
yt-dlp --cookies-from-browser safari --print title --print duration_string --print description "VIDEO_URL"
```

**本地视频：**
```bash
# 直接用 ffprobe 获取信息
ffprobe -v quiet -print_format json -show_format -show_streams "VIDEO_PATH"
```

### Step 2: 智能抽帧（节省 token 的关键！）

```bash
# 根据视频类型选择抽帧密度
# 讲话/播客类：只需封面帧
ffmpeg -y -i "VIDEO" -vf "select='eq(n,0)'" -frames:v 1 -vf "scale=640:-1" output_dir/frame_%d.png

# 教程/演示类：每 5 秒抽 1 帧
ffmpeg -y -i "VIDEO" -vf "fps=1/5,scale=640:-1" output_dir/frame_%d.png

# Vlog/生活类：每 2 秒抽 1 帧
ffmpeg -y -i "VIDEO" -vf "fps=1/2,scale=640:-1" output_dir/frame_%d.png

# 游戏/动作类：每秒 1 帧
ffmpeg -y -i "VIDEO" -vf "fps=1,scale=640:-1" output_dir/frame_%d.png

# ⚠️ 始终 scale 到 640 宽度，避免高分辨率图片浪费 token
# ⚠️ 控制总帧数在 10-20 帧以内，超过就降低频率
```

### Step 3: 下载/提取音频

**在线视频：**
```bash
mkdir -p output_dir
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "output_dir/video.%(ext)s" "VIDEO_URL"

# 同时尝试下载字幕（如有）
yt-dlp --list-subs "VIDEO_URL"
yt-dlp --write-sub --skip-download -o "output_dir/video" "VIDEO_URL"
```

**本地视频：**
```bash
# 用 ffmpeg 提取音频
ffmpeg -y -i "VIDEO_PATH" -vn -acodec libmp3lame -q:a 2 output_dir/audio.mp3
```

> ⚠️ **Cookie 策略：**
> - YouTube / Twitter 等大多数站点：不需要 Cookie，直接下载
> - B 站：必须 `--cookies-from-browser safari`（返回 HTTP 412）
> - Chrome/Firefox Cookie 在 macOS ARM 上可能因加密失败，Safari 最可靠

### Step 4: MiMo 音频转录

使用 MiMo `mimo-v2-omni` 模型进行音频转录（支持 WAV/MP3/FLAC/OGG，比本地 Whisper 更快更准）：

```python
python3 << 'EOF'
import os
import base64
from openai import OpenAI

AUDIO_FILE = "output_dir/video.mp3"
OUTPUT_FILE = "output_dir/transcript.txt"

# 从环境变量读取（或 mimo-mcp .env 已配置）
MIMO_API_KEY = os.environ.get("MIMO_API_KEY")
MIMO_BASE_URL = os.environ.get("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")

if not MIMO_API_KEY:
    print("❌ MIMO_API_KEY 未设置！", flush=True)
    exit(1)

client = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)

# 根据文件扩展名确定 format
ext = os.path.splitext(AUDIO_FILE)[1].lower()
format_map = {".wav": "wav", ".mp3": "mp3", ".flac": "flac", ".ogg": "ogg"}
audio_format = format_map.get(ext, "mp3")

# Base64 编码音频
with open(AUDIO_FILE, "rb") as f:
    audio_data = base64.b64encode(f.read()).decode()

print("正在使用 MiMo mimo-v2-omni 转录音频...")
completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "请逐字转录这段音频的全部内容。只输出转录文本，不要添加任何解释、总结或格式化。如果有多个说话人，请用不同行区分。"},
            {"type": "input_audio", "input_audio": {"data": audio_data, "format": audio_format}}
        ]
    }],
    max_tokens=8192
)

transcript = completion.choices[0].message.content
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(transcript)

print(f"✅ 转录完成！共 {len(transcript)} 字")
print(f"已保存到: {OUTPUT_FILE}")
print("\n--- 转录预览 ---")
print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
EOF
```

> 💡 **MiMo 转录优势：**
> - 无需本地安装 Whisper（省 3GB+ 磁盘空间）
> - 转录质量接近 large 模型，速度更快
> - 原生支持中英日韩等多语言自动识别
> - Token Plan 用户 TTS/ASR 限时免费，音频转录消耗少量 credit
>
> ⚠️ **音频文件过大时**（>25MB）：先用 ffmpeg 分段，再逐段转录后拼接。
> ```bash
> # 分段（每段 10 分钟）
> ffmpeg -y -i audio.mp3 -f segment -segment_time 600 -c copy output_dir/part_%03d.mp3
> ```

### Step 5: 生成总结报告

**关键：转录文本已包含视频全部语音信息。直接由当前 Agent（你）基于转录文本生成总结，无需调用第三方 LLM。**

读取转录文本文件后，以当前 Agent 的身份直接生成结构化总结报告，保存为 Markdown 文件。

#### 总结报告模板

```markdown
# {视频标题}

> **时长**: {时长} | **上传**: {日期} | **播放**: {播放量}

---

## 1. 视频概述

（2-3句话概括视频核心主题和目的）

## 2. 核心内容要点

（分条列出主要观点/信息，每条1-2句话，可加子标题）

## 3. 关键数据/文件引用

（视频中提到的具体数字、文件名、法律条文等硬信息）

## 4. 整体评价

（视频风格、来源可信度判断、适合人群、注意事项）
```

#### 总结由当前 Agent 直接完成

**无需调用外部 LLM。** 当前 Agent（你）就是 LLM——读取转录文本后直接生成总结即可。不需要再调 MiMo/DeepSeek/OpenRouter 做总结，那是多余的一步。

## Platform-Specific Notes

| 平台 | Cookie 需求 | 字幕 | 注意事项 |
|------|:----------:|:----:|---------|
| **YouTube** | 不需要 | ✅ CC字幕 | 最稳定，首选方案 |
| **Bilibili** | ✅ 需要 Safari | 弹幕(danmaku) | HTTP 412 反爬 |
| **Twitter/X** | 可能需要 | ❌ 通常无 | 短视频为主 |
| **抖音** | 可能需要 | ❌ | 需要分享链接 |
| **OneDrive/SharePoint** | ✅ 需要认证 | ❌ | 公开链接返回 403，需下载后处理 |
| **其他** | 视情况 | 视情况 | yt-dlp 支持的都能用 |

## Known Issues & Solutions

| 问题 | 解决方案 |
|------|---------|
| OneDrive 403/500 | 文件需要登录访问，改为下载本地文件后处理 |
| HTTP 412 (B站) | `--cookies-from-browser safari` |
| Cookie 解密失败 (Chrome) | 改用 Safari |
| 文件名含特殊字符导致路径失败 | `cp` 重命名为英文名后操作 |
| MiMo 转录返回空内容 | 检查 `MIMO_API_KEY` 是否正确、`MIMO_BASE_URL` 是否指向正确节点 |
| MiMo 音频文件过大（>25MB） | 先用 ffmpeg 分段（每段 10 分钟），逐段转录后拼接 |
| MiMo mimo-v2-omni 输出为空 | `max_tokens` 需 ≥ 500，该模型默认开启推理会消耗 token |

## Output

- 音频文件：`output_dir/video.mp3`
- 字幕/弹幕：`output_dir/video.*.xml` 或 `.srt`（如有）
- 转录文本：`output_dir/transcript.txt`
- 总结报告：`output_dir/视频总结报告.md`

## MiMo 用于转录

本 skill 使用小米 MiMo API 完成音频转录。文本总结由当前 Agent（调用 skill 的 LLM）直接完成，无需额外调用外部模型。

### 可用模型

| 模型 | 用途 | 说明 |
|------|------|------|
| `mimo-v2-omni` | 音频转录（ASR） | 全模态模型，原生支持音频理解，多语言自动识别 |

### Token Plan 费用

| 模型 | 费用说明 |
|------|---------|
| 音频转录（mimo-v2-omni） | 1 token = 1 credit（很便宜） |
| TTS（mimo-v2.5-tts） | **限时免费** |

> 以 10 分钟视频为例：抽帧 + 音频转录 ≈ ¥0.01-0.06，总结由 Agent 免费完成。

## 成本对比：直接发视频 vs 抽帧+转录

以 MiMo-V2.5 为例（1M token = ¥2.80）：

| 方案 | 10 秒视频 | 1 分钟视频 | 10 分钟视频 |
|------|----------|-----------|------------|
| ❌ 直接发原始视频 | ¥0.56-1.40 | ¥3.36-8.40 | ¥33-84 |
| ✅ 抽帧(5帧) + 音频转录 | ¥0.01-0.03 | ¥0.05-0.15 | ¥0.3-1.0 |
| ✅ 纯音频转录（讲话类） | ¥0.01 | ¥0.03-0.08 | ¥0.2-0.5 |
| **节省比例** | **~97%** | **~98%** | **~99%** |

> 💡 用抽帧方式分析视频，同等 credits 可以分析 **几千个视频**，而直接发视频可能只能分析几十个。务必优先使用省 token 的方式。
