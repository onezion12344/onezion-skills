---
name: onezion-mimo
description: 通过小米 MiMo API 进行视频、音频、图片多模态处理及 V2.5 高级 TTS 语音合成。支持视频理解（URL/Base64）、音频理解与转录（WAV/MP3/FLAC/OGG）、图片理解（URL/Base64）、文本对话。TTS 支持预置音色、音色设计、音色克隆、情绪风格、方言、唱歌、导演模式、音频标签控制。兼容 OpenAI SDK。
agent_created: true
triggers:
  - "小米MiMo"
  - "MiMo"
  - "mimo"
  - "视频理解"
  - "音频理解"
  - "audio understanding"
  - "video understanding"
  - "mimo-v2"
  - "小米模型"
  - "mimo-omni"
  - "TTS"
  - "文本转语音"
  - "语音合成"
  - "声音克隆"
  - "音色设计"
  - "voice clone"
  - "voice design"
---

# onezion-mimo — 小米 MiMo 多模态 API 技能

通过小米 MiMo API 实现视频、音频、图片的全模态理解与处理。

## 前置条件

使用前需要配置 API Key。前往 [小米MiMo开放平台](https://platform.xiaomimimo.com/) 获取 token-plan 类型的 API Key。

```python
import os
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")  # 设置环境变量 MIMO_API_KEY
MIMO_BASE_URL = "https://token-plan-sgp.xiaomimimo.com/v1"
```

## API 基础信息

| 项目 | 值 |
|------|-----|
| **Base URL** | `https://token-plan-sgp.xiaomimimo.com/v1` |
| **Chat Completions Endpoint** | `POST /v1/chat/completions` |
| **认证方式** | `Authorization: Bearer $MIMO_API_KEY` |
| **兼容性** | 完全兼容 OpenAI Python SDK |

## 可用模型

| 模型 ID | 定位 |
|---------|------|
| `mimo-v2-omni` | **全模态旗舰**（视频+音频+图片+文本），默认开启推理 |
| `mimo-v2-pro` | 旗舰推理模型 |
| `mimo-v2.5` | 新一代全模态 Agent 模型 |
| `mimo-v2.5-pro` | 新一代旗舰推理模型 |
| `mimo-v2-tts` | 文本转语音 |
| `mimo-v2.5-tts` | 新一代文本转语音 |
| `mimo-v2.5-tts-voiceclone` | 语音克隆 |
| `mimo-v2.5-tts-voicedesign` | 语音设计 |

**多模态处理（视频/音频/图片）使用 `mimo-v2-omni` 或 `mimo-v2.5`。**
**注意：`mimo-v2-omni` 默认开启推理模式，需设置足够的 `max_tokens`（建议 ≥ 500），否则可能返回空内容。**

## 核心功能

### 1. 视频理解（⚠️ 高 token 消耗，务必选择策略）

视频是最费 token 的输入类型。根据任务需求选择合适的策略：

| 任务需求 | 推荐策略 | 10 秒视频估算 token |
|---------|---------|-------------------|
| 只要"说了什么" | 用 ffmpeg 抽帧 + 音频转录，喂文本/图片给 LLM | ~5,000-20,000 |
| 要"怎么表现的" | 多抽帧（每秒 1 帧）+ 音频转录 | ~20,000-50,000 |
| 要"完整视觉理解" | 直接发原始视频给 MiMo API | ~200,000-500,000 |
| 分析游戏/特效/运动 | 直接发原始视频（视觉信息不可压缩） | ~200,000-500,000 |

**⚡ 省 token 方式：抽帧 + 音频转录（推荐大多数场景）**

```bash
# 1. 抽关键帧（根据视频类型调整密度）
# 讲话/播客类：只需 1-2 帧封面
ffmpeg -y -i "video.mp4" -vf "select='eq(n,0)'" -frames:v 1 -vf "scale=640:-1" frame_%d.png

# 教程/演示类：每 5 秒 1 帧
ffmpeg -y -i "video.mp4" -vf "fps=1/5,scale=640:-1" frame_%d.png

# Vlog/生活类：每 2 秒 1 帧
ffmpeg -y -i "video.mp4" -vf "fps=1/2,scale=640:-1" frame_%d.png

# 2. 提取音频并转录
ffmpeg -y -i "video.mp4" -vn -acodec libmp3lame -q:a 2 audio.mp3
# 然后用 Whisper 或 MiMo 音频 API 转录

# 3. 将抽帧图片 + 转录文本发给 LLM 总结
```

**🎬 完整视频方式（需要视觉理解时使用）：**

视频 URL 方式：

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MIMO_API_KEY", ""),
    base_url="https://token-plan-sgp.xiaomimimo.com/v1"
)

completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这个视频里发生了什么？"},
            {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}}
        ]
    }]
)
print(completion.choices[0].message.content)
```

Base64 视频方式：

```python
import base64

with open("video.mp4", "rb") as f:
    video_data = base64.b64encode(f.read()).decode()

completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这个视频中发生了什么"},
            {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_data}"}}
        ]
    }]
)
```

> **⚠️ Token 消耗警告**：视频是最费 token 的输入类型。10 秒视频可能消耗 20-50 万 token（¥0.56-1.40）。务必根据任务需求选择合适的处理方式（见下方策略）。

### 2. 音频理解

支持 WAV、MP3、FLAC、OGG 格式，通过 Base64 编码传入。用于语音转录、音频内容分析、问答。

```python
import base64

with open("audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode()

completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这段音频说了什么？"},
            {"type": "input_audio", "input_audio": {"data": audio_data, "format": "wav"}}
        ]
    }]
)
```

音频格式与 format 参数对照：

| 格式 | format 值 |
|------|-----------|
| WAV | `wav` |
| MP3 | `mp3` |
| FLAC | `flac` |
| OGG | `ogg` |

### 3. 图片理解

支持 URL 和 Base64 两种方式。支持 JPEG、PNG、GIF、WebP。

**图片 URL 方式：**

```python
completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这张图片里有什么？"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
    }]
)
```

**Base64 图片方式：**

```python
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
    }]
)
```

### 4. 文本对话

使用 `mimo-v2-pro` 进行纯文本对话：

```python
completion = client.chat.completions.create(
    model="mimo-v2-pro",
    messages=[{"role": "user", "content": "你好，介绍一下小米MiMo"}],
    max_tokens=1024,
    temperature=0.7
)
```

> 注意：`mimo-v2-omni` 也可用于文本对话，但会消耗推理 token，需设置 `max_tokens ≥ 500`。

### 5. 文本转语音 (TTS) — V2.5 高级版

V2.5 TTS 系列提供三种模型，脚本目录：`$SKILLS_PATH/scripts/`

| 模型 ID | 脚本 | 用途 | 音色来源 |
|---------|------|------|---------|
| `mimo-v2.5-tts` | `mimo_tts.py` | 预置音色语音合成 | 内置精品音色，支持唱歌 |
| `mimo-v2.5-tts-voicedesign` | `mimo_tts_voicedesign.py` | 文本描述定制音色 | 文本描述生成 |
| `mimo-v2.5-tts-voiceclone` | `mimo_tts_voiceclone.py` | 音频样本复刻音色 | 音频样本 |

#### 预置音色

使用 `mimo-v2.5-tts` 时必须指定音色：

| 音色名 | Voice ID | 语言 | 性别 | 风格 |
|--------|----------|------|------|------|
| 冰糖 | `冰糖` | 中文 | 女性 | 活泼少女 |
| 茉莉 | `茉莉` | 中文 | 女性 | 知性女声 |
| 苏打 | `苏打` | 中文 | 男性 | 阳光少年 |
| 白桦 | `白桦` | 中文 | 男性 | 成熟男声 |
| Mia | `Mia` | English | Female | Lively girl |
| Chloe | `Chloe` | English | Female | Sweet Dreamy |
| Milo | `Milo` | English | Male | Sunny boy |
| Dean | `Dean` | English | Male | Steady Gentle |

#### 脚本用法

**预置音色合成：**
```bash
python3 $SKILLS_PATH/scripts/mimo_tts.py \
  --text "你好，今天天气真不错。" \
  --voice "冰糖"
```

**预置音色 + 自然语言风格控制：**
```bash
python3 $SKILLS_PATH/scripts/mimo_tts.py \
  --context "用温柔的语气，语速稍慢" \
  --text "没关系，慢慢来，我等你。" \
  --voice "冰糖" \
  --output tmp/mimo-v2.5-tts/comfort.wav
```

**预置音色 + 音频标签控制：**
```bash
python3 $SKILLS_PATH/scripts/mimo_tts.py \
  --text "（紧张，深呼吸）呼……冷静，冷静。不就是一个面试吗……（小声）哎呀，领带歪没歪？" \
  --voice "冰糖" \
  --output tmp/mimo-v2.5-tts/interview.wav
```

**音色设计：**
```bash
python3 $SKILLS_PATH/scripts/mimo_tts_voicedesign.py \
  --context "中年男性，节奏极快，情绪高亢，拍卖师风格。吐字连珠，带抑扬顿挫与紧迫感。" \
  --text "三百八十万！还有没有人加价？" \
  --output tmp/mimo-v2.5-tts/voicedesign.wav
```

**音色克隆：**
```bash
python3 $SKILLS_PATH/scripts/mimo_tts_voiceclone.py \
  --voice-file voice.mp3 \
  --text "你好，这是克隆后的声音。" \
  --output tmp/mimo-v2.5-tts/voiceclone.wav
```

**唱歌：**
```bash
python3 $SKILLS_PATH/scripts/mimo_tts.py \
  --text "(唱歌)原谅我这一生不羁放纵爱自由，也会怕有一天会跌倒" \
  --voice "冰糖" \
  --output tmp/mimo-v2.5-tts/singing.wav
```

#### 自然语言控制（所有模型均支持）

通过 `--context` 传入自然语言指令控制语气、情绪、风格：
- **多风格切换**：同一段语音内完成播报 → 低语 → 嘶吼的风格转场
- **多情绪混合**：支持"压抑的愤怒"、"带着哽咽的笑意"等复合情绪
- **多粒度控制**：段落级 → 句子级 → 词级 → 字粒度

#### 导演模式（高级）

从角色、场景、指导三个维度全方位刻画人物与声线：
- **【角色】** 人物身份、性格底色、外形气质与说话习惯
- **【场景】** 此刻发生了什么、和谁说话、情绪位置
- **【指导】** 语速、气息、停顿、重音、共鸣位置、音色质感、情绪起伏

#### 音频标签控制

`mimo-v2.5-tts` 和 `mimo-v2.5-tts-voiceclone` 支持在文本任意位置用括号描述语气、情绪或动作：

```
（紧张，深呼吸）呼……冷静，冷静。（语速加快）自我介绍已经背了五十遍了。（小声）哎呀，领带歪没歪？
```

**整体风格标签**在文本开头添加：`(唱歌)歌词`、`(东北话)哎呀妈呀`、`(粤语)呢个真係好正啊`、`(慵懒)再让我睡五分钟...`

#### 音色描述编写规则（voicedesign 用）

音色描述是嗓子的身份卡，只描写声音本身：
1. **必写：** 年龄段+性别、声音质感、语速节奏、情绪底色
2. **推荐加：** 风格/身份标签、辨识度小癖好
3. **硬约束：** 一到两句话白描式，不写场景/动作，不用真实演员名

#### 长文本处理

建议一次性生成，仅超过 **2500 字**时才需分段后 ffmpeg 拼接。

#### 依赖

```bash
pip install openai
# ffmpeg（仅长文本拼接时需要）
```

### 6. 深度思考模式

`mimo-v2-omni` 默认已开启推理，无需额外配置。如需控制推理强度，通过 `extra_body` 参数：

```python
completion = client.chat.completions.create(
    model="mimo-v2-omni",
    messages=[{"role": "user", "content": "天空为什么是蓝色的？"}],
    max_tokens=1000,
    extra_body={"thinking": {"type": "enabled"}}
)
```

## 工作流程

### 用户请求视频分析时

**第一步：判断任务需求，选择策略**

```
任务只要"说了什么/讲了什么"？
  → YES → 抽帧 + 音频转录 → 喂文本/图片给 LLM（省 95% token）
  → NO → 继续判断

任务需要视觉细节（表情、动作、画面变化）？
  → YES + 短视频（< 30秒）→ 直接发原始视频给 MiMo API
  → YES + 长视频（> 30秒）→ 高密度抽帧（每秒 1 帧）+ 音频转录
```

**第二步：执行分析**

- 省 token 路径：ffmpeg 抽帧 → 提取音频 → Whisper/ASR 转录 → 图片+文本发给 LLM
- 完整视频路径：确认视频文件路径或 URL 有效 → 使用 `mimo-v2-omni` → Base64/URL 传入 → 调用 API

### 用户请求音频分析时

1. 确认 API Key 和音频文件有效
2. 根据文件扩展名确定 `format` 参数（wav/mp3/flac/ogg）
3. Base64 编码音频文件
4. 使用 `{"type": "input_audio", "input_audio": {"data": ..., "format": "..."}}` 格式传入
5. 调用 API 并返回转录/分析结果

### 用户请求图片分析时

1. 确认 API Key 和图片有效
2. URL 或 Base64 方式传入
3. 使用 `{"type": "image_url", "image_url": {"url": "..."}}` 格式
4. 调用 API 并返回分析结果

## 依赖

```bash
pip install openai
```

## Token 消耗策略

**⚠️ 核心原则：根据任务需求选择最省 token 的方式。不要无脑发原始视频。**

### 视频（最贵！）

| 分析方式 | 10 秒视频 token | 10 秒视频费用（V2.5） | 适用场景 |
|---------|----------------|---------------------|---------|
| ❌ 直接发原始视频 | 20-50 万 | ¥0.56-1.40 | 仅在需要完整视觉理解时 |
| ✅ 抽帧 + 音频转录 | 0.5-2 万 | ¥0.01-0.06 | **推荐：大多数场景** |
| ✅ 纯音频转录 | 0.3-0.5 万 | ¥0.01 | 纯讲话/播客类 |

| 视频类型 | 推荐策略 | 抽帧密度 |
|---------|---------|---------|
| 🎤 讲话/播客/访谈 | 音频转录为主，1-2 帧封面 | 最省 |
| 📊 教程/演示/录屏 | 音频转录 + 每 5-10 秒 1 帧 | 适中 |
| 🎬 Vlog/生活记录 | 音频转录 + 每 2-3 秒 1 帧 | 较多 |
| 🎮 游戏/动作/特效 | 直接发原始视频（视觉不可压缩） | 最贵 |
| 📰 新闻/资讯 | 音频转录为主 + 关键画面帧 | 适中 |

### 音频

| 模态 | 策略 |
|------|------|
| 音频（< 5 分钟） | 直接编码发送（MiMo ASR） |
| 音频（> 5 分钟） | 先用 Whisper 本地转录，再喂文本给 LLM |

### 图片

| 模态 | 策略 |
|------|------|
| 图片 | 直接编码发送（token 消耗低，~200-1500/张） |
| 多张图片 | 优先 scale 到 640 宽度，减少 token |

### 省钱提示

以抽帧方式分析视频，同等 credits 可以分析几千个视频；直接发视频只能分析几十个。**务必优先使用省 token 的方式。**

## 注意事项

- 多模态处理使用 `mimo-v2-omni` 或 `mimo-v2.5`
- **关键：`mimo-v2-omni` 默认推理模式，`max_tokens` 必须 ≥ 500**，否则大量 token 被推理消耗导致输出为空
- **⚠️ 视频是最费 token 的输入。** 优先使用"抽帧+音频转录"方式，只在必须时才发原始视频
- 视频和音频文件需要通过 Base64 编码后传入（本地文件场景）
- API 完全兼容 OpenAI SDK，只需替换 `base_url` 和 `api_key`
- 本技能使用 token-plan SGP 节点（`token-plan-sgp.xiaomimimo.com`），Key 前缀为 `tp-`
- MiMo V2.5 知识截止日期未公开，推测约 2026 年 3-4 月。支持联网搜索弥补知识时效性
