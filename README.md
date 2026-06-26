# daily_book_push

GitHub Actions 每日定时推送：**AI 荐书 / 本地读书 / 市场事件雷达 / 每日经济学 / 每日法学 / 每日商业案例** 到飞书 / 企业微信。各学习频道支持独立群机器人，避免消息堆叠。

## 推送模式（可兼容）

| 模式 | 说明 | 命令 / 配置 |
|---|---|---|
| **recommend** | 纯 AI 每日荐书 + 精华金句 | `mode: recommend` |
| **read** | 本地 txt 分段阅读 + AI 摘要 | `mode: read` |
| **both** | 同一天推两条：先读书、后荐书 | `mode: both` |
| **alternate** | 按日轮换：一天读书、一天荐书 | `mode: alternate` |
| **economics** | 每日经济学学习：平日概念、周末案例/复盘 | `mode: economics` |
| **law** | 每日法学（创业法律）：平日概念、周末案例/复盘 | `mode: law` |
| **business** | 每日商业案例：创业者可迁移的商业判断 | `mode: business` |
| **market** | 每日市场事件雷达：未来 90 天重要市场事件 | `mode: market` |

默认模式由 [`config/recommend.yaml`](config/recommend.yaml) 的 `mode` 决定，也可用 CLI `--mode` 或 Actions 手动选择覆盖。

### 模式组合示例

```yaml
# 只要 AI 荐书
mode: recommend

# 只要读本地书（如国富论）
mode: read

# 两条都要：早上读书 + 晚上荐书（会收到 2 条消息）
mode: both

# 轮换：偶数日读书、奇数日荐书（可在 schedule_strategy 调整）
mode: alternate
schedule_strategy:
  alternate_even_day: read
```

```bash
python main.py --mode read --dry-run
python main.py --mode recommend --dry-run
python main.py --mode both --dry-run
python main.py --mode alternate --dry-run
python main.py --mode economics --dry-run
python main.py --mode law --dry-run
python main.py --mode business --dry-run
python main.py --mode market --dry-run
```

## 荐书模式详情

每天由 AI 根据偏好与历史记录推荐一本书，推送内容包含：

- 为什么今天推荐
- 一句话概括
- 精华观点（3-5 条）
- 金句摘录
- 适合谁读 / 阅读建议

配置见 [`config/recommend.yaml`](config/recommend.yaml)：

- `categories`：感兴趣的领域
- `rotate_categories`：每天轮换一个侧重类别
- `use_google_search`：是否启用 Gemini 联网（仅 Gemini 后端生效）
- `avoid_repeat`：避免与近 90 天推荐重复

历史记录保存在 `state/recommend_history.json`。

## 每日经济学频道

`economics` 是独立学习频道，配置见 [`config/economics.yaml`](config/economics.yaml)。默认节奏：

- 平日：一个经济学概念，包含一句话理解、生活例子、深入解释、今日思考、延伸阅读
- 周末：一个案例或本周复盘，把概念放到真实生活/商业现象里理解
- 难度：从 `基础概念` 开始，逐步进入消费者选择、供需、市场、企业、宏观、金融等模块

进度保存在 `state/economics_progress.json`，不会和荐书历史混用。

### 独立群配置

书籍 / 荐书频道使用：

- `FEISHU_WEBHOOK_URL`
- `WECHAT_WEBHOOK_URL`

经济学频道使用：

- `ECONOMICS_FEISHU_WEBHOOK_URL`
- `ECONOMICS_WECHAT_WEBHOOK_URL`

运行 `--mode economics` 时只会使用经济学专用 webhook；如果没配置，不会回退到书籍群。

## 每日法学频道

`law` 是独立学习频道，配置见 [`config/law.yaml`](config/law.yaml)。默认节奏：

- 平日：一个创业法律概念，包含一句话理解、创业场景、深入解释、今日思考、延伸阅读
- 周末：一个创业纠纷/合规案例或本周复盘
- 法域：以中国法为主，可偶尔补充国际/对比视角
- 每条推送包含免责声明：**本内容仅供学习参考，不构成法律意见**

进度保存在 `state/law_progress.json`。

法学频道使用：

- `LAW_FEISHU_WEBHOOK_URL`
- `LAW_WECHAT_WEBHOOK_URL`

运行 `--mode law` 时只会使用法学专用 webhook；如果没配置，不会回退到书籍群。

## 每日商业案例频道

`business` 是独立创业案例频道，配置见 [`config/business.yaml`](config/business.yaml)。默认节奏：

- 平日：拆一个真实公司、产品、商业模式或关键决策
- 周末：复盘本周案例背后的共同规律
- 重点：不是新闻摘要，而是提炼商业机制、创业者启发和适用边界

进度保存在 `state/business_progress.json`。

商业案例频道使用：

- `BUSINESS_FEISHU_WEBHOOK_URL`
- `BUSINESS_WECHAT_WEBHOOK_URL`

运行 `--mode business` 时只会使用商业案例专用 webhook；如果没配置，不会回退到书籍群。

## 每日市场事件雷达

`market` 是独立市场事件频道，配置见 [`config/market.yaml`](config/market.yaml)。默认节奏：

- 每天北京时间 09:00 推送未来 90 天重要市场事件
- 重点覆盖中国、美国和全球宏观数据、央行会议、政策窗口、期货期权交割、指数调仓、财报季和地缘政治
- 所有重点事件要求标注 `confirmed` / `scheduled` / `watchlist`
- 仅做事件观察，不构成投资建议

状态保存在 `state/market_events.json`。

市场事件频道使用：

- `MARKET_FEISHU_WEBHOOK_URL`
- `MARKET_WECHAT_WEBHOOK_URL`

运行 `--mode market` 时只会使用市场事件专用 webhook；如果没配置，不会回退到书籍群。

## 快速开始（GitHub Actions）

### Secrets

| Secret | 说明 | 必填 |
|---|---|---|
| `CURSOR_API_KEY` | Cursor API Key（[Integrations](https://cursor.com/dashboard/integrations)） | 二选一 |
| `GEMINI_API_KEY` | Google Gemini API Key | 二选一 |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 | 至少一个 |
| `WECHAT_WEBHOOK_URL` | 企业微信机器人 | 至少一个 |
| `ECONOMICS_FEISHU_WEBHOOK_URL` | 经济学频道飞书机器人 | economics 模式至少一个 |
| `ECONOMICS_WECHAT_WEBHOOK_URL` | 经济学频道企业微信机器人 | economics 模式至少一个 |
| `LAW_FEISHU_WEBHOOK_URL` | 法学频道飞书机器人 | law 模式至少一个 |
| `LAW_WECHAT_WEBHOOK_URL` | 法学频道企业微信机器人 | law 模式至少一个 |
| `BUSINESS_FEISHU_WEBHOOK_URL` | 商业案例频道飞书机器人 | business 模式至少一个 |
| `BUSINESS_WECHAT_WEBHOOK_URL` | 商业案例频道企业微信机器人 | business 模式至少一个 |
| `MARKET_FEISHU_WEBHOOK_URL` | 市场事件频道飞书机器人 | market 模式至少一个 |
| `MARKET_WECHAT_WEBHOOK_URL` | 市场事件频道企业微信机器人 | market 模式至少一个 |

> **LLM 选择**：`CURSOR_API_KEY` 与 `GEMINI_API_KEY` 至少配置一个；两者都配时 **Cursor 优先**，Cursor 失败会自动回退 Gemini。

可选：`CURSOR_MODEL`、`GEMINI_MODEL`、`GEMINI_USE_SEARCH`、`FEISHU_WEBHOOK_SECRET`

### 定时推送

五个 workflow 独立运行，互不干扰：

| Workflow | 内容 | 北京时间 | cron (UTC) |
|---|---|---|---|
| **每日荐书推送** | 荐书 / 读书（由 `config/recommend.yaml` 的 `mode` 决定） | 08:00 | `0 0 * * *` |
| **每日市场事件雷达** | 未来 90 天市场事件 | 09:00 | `0 1 * * *` |
| **每日法学推送** | 创业法律学习 | 12:30 | `30 4 * * *` |
| **每日商业案例推送** | 商业案例学习 | 18:00 | `0 10 * * *` |
| **每日经济学推送** | 经济学学习 | 20:00 | `0 12 * * *` |

修改时间：编辑对应 workflow 文件里的 `cron` 表达式（GitHub Actions 使用 UTC）。

### 手动测试

- Actions → **每日荐书推送**：可选 `recommend` / `read` / `both` / `alternate`
- Actions → **每日市场事件雷达**：固定 `market` 模式
- Actions → **每日法学推送**：固定 `law` 模式
- Actions → **每日商业案例推送**：固定 `business` 模式
- Actions → **每日经济学推送**：固定 `economics` 模式
- 五个 workflow 都支持 `dry_run=true` 仅预览

## 本地调试

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 CURSOR_API_KEY 或 GEMINI_API_KEY，以及 Webhook

python main.py --dry-run              # 预览今日荐书
python main.py                        # 正式推送
python main.py --notify-test          # 测试通知
python main.py --mode read --dry-run  # 旧模式：本地 txt
python main.py --mode economics --dry-run
python main.py --mode law --dry-run
python main.py --mode business --dry-run
python main.py --mode market --dry-run
```

## 目录结构

```
.github/workflows/
  daily-push.yml           # 荐书/读书，北京时间 08:00
  daily-market-push.yml    # 市场事件雷达，北京时间 09:00
  daily-law-push.yml       # 法学，北京时间 12:30
  daily-business-push.yml  # 商业案例，北京时间 18:00
  daily-economics-push.yml # 经济学，北京时间 20:00
config/recommend.yaml      # 荐书偏好
config/economics.yaml      # [economics 模式] 经济学学习路径
config/law.yaml            # [law 模式] 创业法律学习路径
config/business.yaml       # [business 模式] 商业案例学习路径
config/market.yaml         # [market 模式] 市场事件雷达配置
config/books.yaml          # [read 模式] 本地书籍
state/recommend_history.json
state/economics_progress.json
state/law_progress.json
state/business_progress.json
state/market_events.json
state/progress.json        # [read 模式] 阅读进度
src/llm_client.py         # LLM 调用（Cursor 优先，Gemini 备用）
src/recommender.py         # AI 荐书逻辑
src/economics.py           # 每日经济学逻辑
src/law.py                 # 每日法学逻辑
src/business.py            # 每日商业案例逻辑
src/market.py              # 每日市场事件雷达逻辑
main.py
```

## 测试

```bash
pip install pytest
pytest tests/ -q
```

## 说明

- 荐书、经济学、法学、商业案例、市场事件内容均依赖 AI，请自行判断准确性
- 市场事件雷达仅供事件观察，不构成投资建议
- 法学内容不构成法律意见，重要决策请咨询执业律师
- Gemini 联网搜索需模型支持 `googleSearch` 工具；Cursor 后端无联网，失败时会自动降级为模型自身知识或回退 Gemini
- 建议私有仓库；`read` 模式书籍文件需自行管理版权
