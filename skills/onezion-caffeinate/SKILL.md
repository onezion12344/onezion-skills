---
name: onezion-caffeinate
description: "一键控制 Mac 睡眠行为。防止合盖睡眠、保持屏幕常亮、阻止系统空闲。触发词：caffeinate、防睡眠、合盖不睡、保持唤醒、屏幕常亮、prevent sleep、keep awake、clamshell、合盖".
allowed-tools: Bash, AskUserQuestion
agent_created: true
---

# onezion-caffeinate — Mac 睡眠控制

macOS 原生 `caffeinate` 命令的易用封装。无需安装任何东西。

## 常见场景速查

| 场景 | 命令 |
|------|------|
| 阻止系统睡眠（下载/渲染中） | `caffeinate -i` |
| 阻止屏幕熄灭 | `caffeinate -d` |
| 合盖不睡眠（需外接电源） | `caffeinate -s` |
| 完全不睡（屏幕+系统） | `caffeinate -dims` |
| 限制时间（如 2 小时） | `caffeinate -dims -t 7200` |
| 后台长期运行 | `caffeinate -dims &` |
| 停止 | `kill %1` 或 `killall caffeinate` |

## caffeinate 参数说明

| Flag | 作用 |
|------|------|
| `-d` | 防止 display sleep（屏幕常亮） |
| `-i` | 防止 system idle sleep（系统空闲不睡） |
| `-m` | 防止 disk sleep（磁盘不停转） |
| `-s` | 阻止系统休眠（包括合盖） |
| `-t N` | 超时秒数，N 秒后自动恢复 |
| `&` | 后台运行 |

## 使用流程

### 1. 判断用户需求

根据用户描述，选择合适的组合：

- "下载文件怕合盖中断" → `caffeinate -dims`
- "合盖后继续跑任务" → `caffeinate -s` 或 `caffeinate -dims`
- "屏幕一直亮着" → `caffeinate -d`
- "跑个长任务别睡" → `caffeinate -i`
- "跑 30 分钟别睡" → `caffeinate -dims -t 1800`

### ⚠️ 强制规则：必须设置时限

**每次调用 caffeinate 必须加上 `-t` 时间限制。** 不允许无期限运行。

如果用户没有指定时长，**必须使用 AskUserQuestion 询问**：

```json
{
  "questions": [{
    "question": "防睡眠要持续多久？",
    "header": "时长",
    "options": [
      {"label": "15 分钟", "description": "适合快速下载/渲染"},
      {"label": "30 分钟", "description": "适合中等任务"},
      {"label": "1 小时", "description": "适合较长的任务"},
      {"label": "2 小时", "description": "适合长任务"}
    ],
    "multiSelect": false
  }]
}
```

**时间选择规则：**
- 用户说具体时间 → 直接使用（如 "一个小时" → `-t 3600`）
- 用户说模糊时间 → 问清楚（如 "一会儿" → 让用户选具体时长）
- 用户说"一直" → 告知重启后自动恢复，但仍建议设置时限
- 所有 `-t` 参数单位为秒

**安全说明（告知用户）：**
- `caffeinate -t N`：N 秒后自动恢复睡眠，**重启后也会自动恢复**（因为 caffeinate 本身不持久化）
- 无需用户手动取消，到期自动失效
- 如果系统重启， caffeinate 自然消失，恢复默认睡眠行为

### 2. 执行

```bash
# 标准用法（带时限）
caffeinate -dims -t <秒数>

# 前台运行（用户能看到进度，Ctrl+C 可提前停止）
caffeinate -dims -t <秒数>

# 后台运行（静默，到期自动停止）
caffeinate -dims -t <秒数> &
```

### 3. 停止 caffeinate

```bash
# 前台：Ctrl+C 提前终止
# 后台：killall caffeinate
# 最自然的方式：等 -t 到期自动停止
```

## 安全提示

- `caffeinate -s`（合盖不睡）**只在接电源时有效**，电池模式下 macOS 会强制睡眠
- 合盖运行注意散热，尤其放包里
- 任务完成后记得停止 caffeinate，否则一直不睡
- 建议配合 `-t` 设置超时，避免忘记

## 进阶：pmset 设置

### 电池模式合盖不睡

`caffeinate` 在电池模式下无法阻止合盖睡眠（macOS 硬限制）。如果需要**电池模式也合盖不睡**，必须用 `pmset`：

```bash
# 禁用睡眠（电池+电源都生效）— 通过 GUI 弹窗获取权限
osascript -e 'do shell script "pmset -a disablesleep 1" with administrator privileges'

# 恢复默认
osascript -e 'do shell script "pmset -a disablesleep 0" with administrator privileges'

# 查看当前电源设置
pmset -g
```

**⚠️ 固定用 `osascript` GUI 弹窗获取管理员权限，不要直接用 `sudo`（命令行需要终端交互）。** 除非用户明确要求，否则优先用临时的 `caffeinate`。

### 定时恢复（推荐 ⭐）—— 两步法

用户最常担心的：改了设置忘记改回来。

**⚠️ 关键：必须拆成两步，不能合在一条 osascript 里。**
`osascript do shell script` 会等待内部所有子进程结束才返回，即使加了 `&` 也不行。把 `sleep 1800` 放在 osascript 里面 = 卡死 30 分钟。

#### 正确做法：分两步执行

**第一步：立刻禁用睡眠（需要密码）**
```bash
osascript -e 'do shell script "pmset -a disablesleep 1" with administrator privileges'
```
→ 弹窗填密码后立刻返回，不阻塞。

**第二步：后台倒计时自动恢复（run_in_background）**
```bash
(sleep <秒数> && osascript -e 'do shell script "pmset -a disablesleep 0" with administrator privileges') &
```
→ sleep 在 osascript **外面**，普通 bash 后台进程，不锁任何东西。到期后弹窗要求密码恢复。

#### 具体示例

| 时长 | 第一步（立即执行） | 第二步（后台） |
|------|-------------------|---------------|
| 30 分钟 | `osascript -e 'do shell script "pmset -a disablesleep 1" with administrator privileges'` | `(sleep 1800 && osascript -e 'do shell script "pmset -a disablesleep 0" with administrator privileges') &` |
| 1 小时 | 同上 | `(sleep 3600 && osascript -e 'do shell script "pmset -a disablesleep 0" with administrator privileges') &` |
| 2 小时 | 同上 | `(sleep 7200 && osascript -e 'do shell script "pmset -a disablesleep 0" with administrator privileges') &` |

**第二步必须用 `run_in_background: true`**，否则 WorkBuddy 会等 sleep 结束。

**工作原理：**
1. Step 1: `pmset -a disablesleep 1` → 立刻禁用睡眠，弹窗后秒返
2. Step 2: bash 后台进程 `sleep N` → N 秒后触发 osascript 弹窗 → 填密码恢复
3. Step 2 是独立 bash 进程，不依附于 osascript，即使 WorkBuddy 会话结束也会跑完

**⚠️ 注意事项：**
- 第一步弹窗填密码（系统级安全弹窗，密码不经过 WorkBuddy）
- 第二步到期后会再弹一次窗要求密码恢复——这是有意设计：作为提醒，不想恢复就点取消
- 电池模式合盖跑注意散热
- 如果系统重启，pmset 设置会保留，需手动恢复：`osascript -e 'do shell script "pmset -a disablesleep 0" with administrator privileges'`

**触发条件：** 用户说"电池模式合盖不睡"、"插不插电都要合盖不睡"、"设了怕忘记改回来"、"自动恢复"时使用此方案。

## 常见问题

**Q: 合盖后蓝牙鼠标/键盘断连？**
A: M 系列芯片常见问题。用有线键鼠，或者在合盖前先把蓝牙设备连上再合盖。

**Q: caffeinate -s 不起作用？**
A: 检查是否接了电源。电池模式下 macOS 不允许合盖不睡。

**Q: 怎么知道 caffeinate 在跑？**
A: `ps aux | grep caffeinate` 查看。
