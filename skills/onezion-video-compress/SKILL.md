---
name: onezion-video-compress
description: >
  自动视频压缩工具。输入视频路径+目标大小，自动计算最优参数（码率、preset、缩放），
  支持 2-pass 和 CRF 两种模式，输出到指定路径。
  触发词：压缩视频、video compress、视频转码、压到XX GB/MB、compress video、reduce video size、
  视频太大了、video too big、帮我压缩这个视频。
agent_created: true
---

# onezion-video-compress

自动视频压缩 skill，封装 ffmpeg 参数决策，让用户只需指定目标大小。

## 依赖

- `ffmpeg`（必须，用于编码）
- `ffprobe`（必须，用于分析视频信息）
- Python 3.8+

检查依赖：
```bash
ffmpeg -version && ffprobe -version && python3 --version
```

## 使用方式

### 基本用法（指定目标大小）

```bash
python3 ~/.workbuddy/skills/onezion-video-compress/scripts/compress.py \
  "/path/to/video.mov" \
  -t 900MB \
  -o "/path/to/output.mp4"
```

### 常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `input` | 输入视频路径（必须） | |
| `-t, --target` | 目标大小 | `900MB`, `1GB`, `500MB` |
| `-o, --output` | 输出路径 | `/path/to/out.mp4` |
| `-m, --mode` | 压缩模式 | `2pass`(默认) 或 `crf` |
| `--crf` | CRF 质量值 | `28`(默认)，越小质量越好 |
| `-p, --preset` | ffmpeg preset | `fast`/`medium`/`slow` 等 |
| `-s, --scale` | 缩放到指定高度 | `720`, `1080` |
| `-r, --fps` | 输出帧率 | `24`, `30` |
| `--audio-bitrate` | 音频码率 | `128k`(默认) |

### 模式说明

- **2pass 模式**（默认）：先分析再编码，文件大小控制最精确，适合有明确大小限制的场景
- **CRF 模式**：按质量常数编码，速度更快，文件大小不精确控制

### 自动决策逻辑

脚本内自动：
1. 用 `ffprobe` 获取时长、分辨率、帧率、是否有音轨
2. 计算目标视频码率 = (目标大小×8 - 音频大小) / 时长
3. 根据时长和分辨率自动选 preset（`fast`/`medium`/`slow`）
4. 根据目标码率自动判断是否缩放（码率<1500k 时缩到720p）
5. 码率上下限保护（300k~max）

## 与用户交互

当用户说"帮我压缩这个视频到 X GB"：
1. 确认视频路径（如果用户只给了一个大概位置，用 `ls` 找）
2. 确认目标大小
3. 询问是否有特殊要求（保持分辨率？快速模式？）
4. 运行脚本
5. 验证输出文件大小，报告结果

## 示例对话

**用户**: "把这个 recording.mov 压到 1GB 以下"
**执行**:
```bash
python3 ~/.workbuddy/skills/onezion-video-compress/scripts/compress.py \
  "recording.mov" -t 900MB -o "recording_compressed.mp4"
```

**用户**: "快速压缩，不在乎文件大小"
**执行**: 用 CRF 模式 + fast preset
```bash
python3 ~/.workbuddy/skills/onezion-video-compress/scripts/compress.py \
  "input.mov" -m crf --crf 26 -p fast
```

## 注意事项

- 2-pass 模式耗时是单 pass 的 ~2 倍，长视频（>1h）建议用 CRF 模式加速
- 屏幕录制类视频（低动态）用 CRF 28 + medium preset 效果很好
- 输出格式固定为 mp4（H.264 + AAC），兼容性最好
- 脚本会自动在输出文件加上 `-movflags +faststart`，适合网络播放
