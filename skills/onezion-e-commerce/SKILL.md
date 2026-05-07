---
name: onezion-e-commerce
description: 全平台电商工具集。全网比价（price.py/main.py，覆盖淘宝/京东/拼多多/抖音/快手/1688/苏宁/唯品会）+ 返利宝（淘/京/拼返利链接）+ 唯品会深度购物（自动路由到唯品会技能集）。触发词：比价/找便宜/查价格/返利/省钱/唯品会购物/帮我找XX最低价。
---

# OneZion E-Commerce

全平台电商工具集，含全网比价 + 返利宝 + 唯品会深度购物支持。

| 模块 | 入口 | 平台覆盖 |
|------|------|---------|
| 全网比价 | `price.py` / `main.py` | 淘宝/京东/拼多多/抖音/快手/1688/苏宁/唯品会 |
| 返利宝 | `rebate/cli/rebate_assistant_router.js` | 淘宝/京东/拼多多 |
| 唯品会购物 | 唯品会技能集（`vipshop-*`） | 唯品会 |

---

## 一、全网比价

### 调用方式

```bash
# 入口 A：price.py（推荐，零依赖，Python 3 标准库）
python3 scripts/price-comparison/price.py search --keyword "关键字" --sourceType 0 --pages 1 --format csv
python3 scripts/price-comparison/price.py link --goodsId "商品ID" --sourceType 平台编码

# 入口 B：main.py（uv 版，需 aiohttp/PyYAML）
uv run scripts/price-comparison/main.py search --keyword "关键字" --source 0
uv run scripts/price-comparison/main.py detail --id "商品ID" --source 1
```

### 平台编码 (sourceType)

| 编码 | 平台 | 编码 | 平台 |
|:---:|------|:---:|------|
| 0 | 全部 | 5 | 唯品会 |
| 1 | 淘宝/天猫 | 7 | 抖音 |
| 2 | 京东 | 8 | 快手 |
| 3 | 拼多多 | 22 | 1688 |
| 4 | 苏宁 | | |

### 比价工作流

#### 第一步：构造关键字并检索

从用户输入提取核心关键字，调用 search 命令。

#### 第二步：过滤无关商品 + 输出推荐表格

从 CSV 结果逐条检查商品名称：
- **保留**：名称与搜索意图明确相关的条目
- **排除**：明显不相关、品类不符的条目

过滤后输出 Markdown 表格：

| ID | 名称 | 平台 | 商铺 | 价格 | 原价 | 优惠 | 月销 | 推荐度 | 推荐理由 |

**推荐度评估标准**（综合三项因素）：
1. **相关性**（权重最高）：商品名称与用户搜索意图的匹配程度
2. **价格**：在同类商品中的价格竞争力
3. **月销量**：反映市场认可度

按推荐度从高到低排列，推荐度相同时按价格升序。

> 必须记住每个商品的 goodsId 和 sourceType（内部映射），后续获取链接需要。

#### 第三步：输出检索说明 + 等待用户选品

表格后输出检索概况、推荐排序、注意事项、汇总结论，并在末尾提示：

> 请输入您关注的商品序号（可多选，用逗号或空格分隔），我将为您获取购买链接。

#### 第四步：根据用户选择的 ID 获取链接

逐个调用 link 命令，每次间隔 0.5 秒。

#### 第五步：汇总输出带链接的最终结果

| ID | 名称 | 平台 | 商铺 | 价格 | 链接 |

---

## 二、返利宝

通过 Node.js 脚本处理淘宝/京东/拼多多的返利链接生成，支持微信授权与提现。

### 统一入口

```bash
node scripts/rebate/cli/rebate_assistant_router.js --raw-message '<用户原始消息>' --format md
```

### 三条场景路由

| 场景 | 触发条件 | 处理脚本 |
|------|---------|---------|
| S01 授权与教程 | "返利"、"教程"、"提现"、"我已授权"、"账户余额" | `m01_operation_guide.js` |
| S02 链接返利 | 消息含 `http://` 或 `https://` 商品链接 | `m02_platform_link.js` |
| S03 商品搜索 | 无链接但表达购物需求 | `product_search.js` |

### 执行硬约束

1. 命中返利宝后，优先调用 `rebate_assistant_router.js`。
2. 脚本标准输出是什么，就向用户原样返回什么。
3. 返回方式必须是普通 assistant 对话消息，不能只显示在 tool output 面板中。
4. 返回消息必须使用 md 格式；调用脚本时优先使用 `--format md`。
5. 禁止在脚本输出前后追加解释、总结、润色、转述。
6. 禁止在接口失败时自行编造返利链接、口令或到账说明。

### S01 授权与教程

触发词：`返利`、`教程`、`详细教程`、`提现教程`、`提现10元`、`确认提现`、`我已授权`、`授权完成`、`账户余额`

可用 action：`start_auth`、`confirm_auth`、`detailed_tutorial`、`withdraw_tutorial`、`withdraw_prepare`、`withdraw_confirm`、`account_balance`

```bash
node scripts/rebate/cli/m01_operation_guide.js --action <action> --format md
node scripts/rebate/cli/m01_operation_guide.js --action withdraw_prepare --raw-message '提现10元' --format md
```

### S02 链接返利

```bash
node scripts/rebate/cli/m02_platform_link.js --raw-message '<用户链接>' --format md
```

### S03 商品搜索

```bash
node scripts/rebate/cli/product_search.js --raw-message '<用户消息>' --format md
```

---

## 三、优惠券知识库

### 拼多多优惠券类型

| 类型 | 子类 | 面额 |
|------|------|------|
| 店铺券 | 新人券 / 关注券 / 收藏券 / 分享券 | 3-20 元 |
| 平台券 | 满减券 / 品类券 / 品牌券 | 满100-10 至 满1000-100 |
| 隐藏券 | 内部券 / 大额券 / 神券 | 10-500 元 |

### 叠加规则

```
最优叠加 = 店铺券 + 平台券 + 百亿补贴 + 返利
```

### 热门品类参考

| 品类 | 平均优惠 | 推荐券 |
|------|---------|--------|
| 手机 | 5-10% | 百亿补贴 |
| 电脑 | 3-8% | 品牌券 |
| 家电 | 10-20% | 满减券 |
| 服装 | 20-40% | 店铺券 |
| 鞋子 | 15-30% | 品牌券 |
| 护肤 | 15-30% | 品牌券 |
| 零食 | 20-40% | 满减券 |

### 最佳下单时间

| 时间 | 优惠力度 |
|------|---------|
| 0 点 | 新品首发 |
| 10 点 | 限时秒杀 |
| 20 点 | 晚间促销 |
| 大促 | 618/双11 |

---

## 路由决策

当用户消息涉及电商购物时：

1. **唯品会购物**（登录/搜索/详情/促销/图片搜索） → 调用唯品会技能集（`vipshop-*`）
2. **返利请求**（教程/授权/提现/链接返利） → 返利宝（S01/S02/S03）
3. **纯比价/查价格/找便宜** → 全网比价（`price.py`，优先）
4. **拼多多优惠券查询** → 优惠券知识库

---

## 脚本说明

- `price.py`：Python 3 标准库，零依赖，后端 `maishou88.com`，优先使用
- `main.py`：需 `aiohttp` + `PyYAML`，通过 `uv run` 执行，同后端，备选
- 返利脚本：Node.js（已编译），无额外 npm 依赖，通过 `node` 直接执行
- 唯品会脚本：Python 3 标准库，零依赖，需通过 `vipshop-user-login` 先登录
- 所有脚本均为客户端请求第三方服务，不会读写本地文件
