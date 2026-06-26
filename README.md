# daily_book_push

<p align="center">
  <strong>一套运行在 GitHub Actions 上的每日 AI 推送系统</strong>
</p>

<p align="center">
  读书、市场事件、法学、商业案例、经济学，一天五次，把长期输入自动送到飞书或企业微信。
</p>

<p align="center">
  <a href="https://github.com/yelvon/daily_book_push/actions/workflows/daily-push.yml"><img alt="daily book" src="https://img.shields.io/github/actions/workflow/status/yelvon/daily_book_push/daily-push.yml?label=book&style=flat-square"></a>
  <a href="https://github.com/yelvon/daily_book_push/actions/workflows/daily-market-push.yml"><img alt="market radar" src="https://img.shields.io/github/actions/workflow/status/yelvon/daily_book_push/daily-market-push.yml?label=market&style=flat-square"></a>
  <a href="https://github.com/yelvon/daily_book_push/actions/workflows/daily-law-push.yml"><img alt="law" src="https://img.shields.io/github/actions/workflow/status/yelvon/daily_book_push/daily-law-push.yml?label=law&style=flat-square"></a>
  <a href="https://github.com/yelvon/daily_book_push/actions/workflows/daily-business-push.yml"><img alt="business" src="https://img.shields.io/github/actions/workflow/status/yelvon/daily_book_push/daily-business-push.yml?label=business&style=flat-square"></a>
  <a href="https://github.com/yelvon/daily_book_push/actions/workflows/daily-economics-push.yml"><img alt="economics" src="https://img.shields.io/github/actions/workflow/status/yelvon/daily_book_push/daily-economics-push.yml?label=economics&style=flat-square"></a>
</p>

## What It Does

`daily_book_push` 是一个面向个人成长和创业准备的自动化推送系统。它每天按固定时间运行 GitHub Actions，调用 Cursor / Gemini 生成内容，并推送到飞书或企业微信。

它的核心思路很简单：把值得长期积累的知识，拆成每天一小块，自动送到你会看的地方。

## Highlights

- **多频道独立运行**：荐书、市场事件、法学、商业案例、经济学互不干扰。
- **独立群机器人**：每个频道都可以推到不同飞书群或企业微信群，避免消息堆叠。
- **AI + 历史去重**：每个学习频道都有独立状态文件，尽量避免重复内容。
- **GitHub Actions 托管**：无需服务器，Fork 后配置 Secrets 即可定时运行。
- **本地可预览**：所有频道都支持 `--dry-run`，可以先看内容再正式推送。
- **Cursor 优先，Gemini 兜底**：同时配置时优先使用 Cursor，失败后自动回退 Gemini。

## Daily Schedule

| 时间（北京时间） | Workflow | 频道 | 目标 |
|---:|---|---|---|
| 08:00 | `daily-push.yml` | 荐书 / 本地读书 | 每天读一点，或发现一本值得读的书 |
| 09:00 | `daily-market-push.yml` | 市场事件雷达 | 提前看到未来 90 天重要市场事件 |
| 12:30 | `daily-law-push.yml` | 创业法律 | 建立创业相关法律常识和风险意识 |
| 18:00 | `daily-business-push.yml` | 商业案例 | 拆解公司、产品、商业模式和关键决策 |
| 20:00 | `daily-economics-push.yml` | 经济学 | 从浅到深学习经济学概念和案例 |

GitHub Actions 使用 UTC 时间，具体 cron 配置在 `.github/workflows/` 目录下。

## Channels

### Book

荐书 / 读书频道支持两种方式：

- `recommend`：AI 每天推荐一本书，附精华观点、金句和阅读建议。
- `read`：读取本地 `books/*.txt`，每天推送一段，并可用 AI 总结。

常用命令：

```bash
python main.py --mode recommend --dry-run
python main.py --mode read --dry-run
```

配置文件：

- `config/recommend.yaml`
- `config/books.yaml`

状态文件：

- `state/recommend_history.json`
- `state/progress.json`

### Market

市场事件雷达关注未来 90 天内可能影响金融市场的事件，尤其是中国和美国。

覆盖范围：

- 宏观数据：CPI、PPI、PCE、非农、PMI、GDP、社融、M2。
- 央行会议：FOMC、ECB、BOJ、BOE、LPR、MLF。
- 市场结构：三巫日、期权到期、期货交割、指数调仓。
- 其他事件：OPEC+、财报季、政策窗口、地缘政治。

它要求每个重点事件标注 `confirmed` / `scheduled` / `watchlist`，无法确认日期时必须写“待确认”。

```bash
python main.py --mode market --dry-run
```

配置文件：`config/market.yaml`  
状态文件：`state/market_events.json`

### Law

法学频道聚焦创业相关法律常识，以中国法为主，偶尔补充国际对比视角。

内容包括公司设立、股权结构、股东协议、劳动用工、合同管理、融资尽调、知识产权、数据合规和争议解决。

每条推送都会包含免责声明：本内容仅供学习参考，不构成法律意见。

```bash
python main.py --mode law --dry-run
```

配置文件：`config/law.yaml`  
状态文件：`state/law_progress.json`

### Business

商业案例频道不做新闻摘要，而是拆解真实公司、产品、商业模式或关键决策，提炼创业者可迁移的判断力。

内容结构：

- 现象
- 核心逻辑
- 创业者启发
- 风险提醒
- 延伸思考

```bash
python main.py --mode business --dry-run
```

配置文件：`config/business.yaml`  
状态文件：`state/business_progress.json`

### Economics

经济学频道从基础概念开始，逐步进入消费者选择、供需、市场、企业、宏观、货币、金融和全球化。

平日学概念，周末做案例或复盘。

```bash
python main.py --mode economics --dry-run
```

配置文件：`config/economics.yaml`  
状态文件：`state/economics_progress.json`

## Quick Start

### 1. Fork or Clone

```bash
git clone git@github.com:yelvon/daily_book_push.git
cd daily_book_push
```

### 2. Install Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Configure AI Provider

至少配置一个：

```bash
CURSOR_API_KEY=
GEMINI_API_KEY=
```

两者都配置时，系统会优先使用 Cursor；Cursor 失败时回退 Gemini。

### 4. Configure Webhooks

书籍 / 荐书频道：

```bash
FEISHU_WEBHOOK_URL=
WECHAT_WEBHOOK_URL=
```

独立频道：

```bash
MARKET_FEISHU_WEBHOOK_URL=
MARKET_WECHAT_WEBHOOK_URL=

LAW_FEISHU_WEBHOOK_URL=
LAW_WECHAT_WEBHOOK_URL=

BUSINESS_FEISHU_WEBHOOK_URL=
BUSINESS_WECHAT_WEBHOOK_URL=

ECONOMICS_FEISHU_WEBHOOK_URL=
ECONOMICS_WECHAT_WEBHOOK_URL=
```

每个频道只会使用自己的 webhook，不会回退到书籍群。

### 5. Preview

```bash
python main.py --mode recommend --dry-run
python main.py --mode market --dry-run
python main.py --mode law --dry-run
python main.py --mode business --dry-run
python main.py --mode economics --dry-run
```

## GitHub Actions Setup

在仓库的 `Settings -> Secrets and variables -> Actions` 中配置：

| Secret | 用途 |
|---|---|
| `CURSOR_API_KEY` | Cursor API Key，和 Gemini 二选一 |
| `GEMINI_API_KEY` | Gemini API Key，和 Cursor 二选一 |
| `FEISHU_WEBHOOK_URL` | 书籍 / 荐书频道飞书机器人 |
| `WECHAT_WEBHOOK_URL` | 书籍 / 荐书频道企业微信机器人 |
| `MARKET_FEISHU_WEBHOOK_URL` | 市场事件频道飞书机器人 |
| `MARKET_WECHAT_WEBHOOK_URL` | 市场事件频道企业微信机器人 |
| `LAW_FEISHU_WEBHOOK_URL` | 法学频道飞书机器人 |
| `LAW_WECHAT_WEBHOOK_URL` | 法学频道企业微信机器人 |
| `BUSINESS_FEISHU_WEBHOOK_URL` | 商业案例频道飞书机器人 |
| `BUSINESS_WECHAT_WEBHOOK_URL` | 商业案例频道企业微信机器人 |
| `ECONOMICS_FEISHU_WEBHOOK_URL` | 经济学频道飞书机器人 |
| `ECONOMICS_WECHAT_WEBHOOK_URL` | 经济学频道企业微信机器人 |

可选配置：

```bash
CURSOR_MODEL=composer-2.5
GEMINI_MODEL=gemini/gemini-2.5-flash
GEMINI_MODEL_FALLBACK=gemini/gemini-2.0-flash
GEMINI_USE_SEARCH=true
WECHAT_MSG_TYPE=text
WECHAT_PERSONAL_COMPAT=true
WEBHOOK_VERIFY_SSL=true
```

## Run Modes

| Mode | Description |
|---|---|
| `recommend` | AI 每日荐书 |
| `read` | 本地 txt 分段阅读 |
| `both` | 同一天执行 `read` + `recommend` |
| `alternate` | 读书和荐书按日轮换 |
| `market` | 每日市场事件雷达 |
| `law` | 每日法学 |
| `business` | 每日商业案例 |
| `economics` | 每日经济学 |

默认模式由 `config/recommend.yaml` 的 `mode` 决定；也可以通过 CLI 或 GitHub Actions 手动选择。

## Project Structure

```text
.github/workflows/
  daily-push.yml
  daily-market-push.yml
  daily-law-push.yml
  daily-business-push.yml
  daily-economics-push.yml

config/
  recommend.yaml
  books.yaml
  market.yaml
  law.yaml
  business.yaml
  economics.yaml

state/
  recommend_history.json
  progress.json
  market_events.json
  law_progress.json
  business_progress.json
  economics_progress.json

src/
  recommender.py
  market.py
  law.py
  business.py
  economics.py
  notifier/
```

## Testing

```bash
pytest tests/ -q
```

## Notes

- 市场事件雷达仅供事件观察，不构成投资建议。
- 法学内容仅供学习参考，不构成法律意见；重要决策请咨询执业律师。
- AI 生成内容可能有遗漏或错误，关键事实请自行核验。
- Gemini 联网搜索需要模型支持 `googleSearch` 工具。
- 建议使用私有仓库；`read` 模式的本地书籍文件需自行管理版权。
