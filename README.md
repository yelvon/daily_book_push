# daily_book_push

GitHub Actions 每日定时推送：**AI 荐书 / 本地读书 / 每日经济学 / 每日法学** 到飞书 / 企业微信。各学习频道支持独立群机器人，避免消息堆叠。

## 推送模式（可兼容）

| 模式 | 说明 | 命令 / 配置 |
|---|---|---|
| **recommend** | 纯 AI 每日荐书 + 精华金句 | `mode: recommend` |
| **read** | 本地 txt 分段阅读 + AI 摘要 | `mode: read` |
| **both** | 同一天推两条：先读书、后荐书 | `mode: both` |
| **alternate** | 按日轮换：一天读书、一天荐书 | `mode: alternate` |
| **economics** | 每日经济学学习：平日概念、周末案例/复盘 | `mode: economics` |
| **law** | 每日法学（创业法律）：平日概念、周末案例/复盘 | `mode: law` |

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

> **LLM 选择**：`CURSOR_API_KEY` 与 `GEMINI_API_KEY` 至少配置一个；两者都配时 **Cursor 优先**，Cursor 失败会自动回退 Gemini。

可选：`CURSOR_MODEL`、`GEMINI_MODEL`、`GEMINI_USE_SEARCH`、`FEISHU_WEBHOOK_SECRET`

### 定时推送

三个 workflow 独立运行，互不干扰：

| Workflow | 内容 | 北京时间 | cron (UTC) |
|---|---|---|---|
| **每日荐书推送** | 荐书 / 读书（由 `config/recommend.yaml` 的 `mode` 决定） | 08:00 | `0 0 * * *` |
| **每日法学推送** | 创业法律学习 | 12:30 | `30 4 * * *` |
| **每日经济学推送** | 经济学学习 | 20:00 | `0 12 * * *` |

修改时间：编辑对应 workflow 文件里的 `cron` 表达式（GitHub Actions 使用 UTC）。

### 手动测试

- Actions → **每日荐书推送**：可选 `recommend` / `read` / `both` / `alternate`
- Actions → **每日法学推送**：固定 `law` 模式
- Actions → **每日经济学推送**：固定 `economics` 模式
- 三个 workflow 都支持 `dry_run=true` 仅预览

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
```

## 目录结构

```
.github/workflows/
  daily-push.yml           # 荐书/读书，北京时间 08:00
  daily-law-push.yml       # 法学，北京时间 12:30
  daily-economics-push.yml # 经济学，北京时间 20:00
config/recommend.yaml      # 荐书偏好
config/economics.yaml      # [economics 模式] 经济学学习路径
config/law.yaml            # [law 模式] 创业法律学习路径
config/books.yaml          # [read 模式] 本地书籍
state/recommend_history.json
state/economics_progress.json
state/law_progress.json
state/progress.json        # [read 模式] 阅读进度
src/llm_client.py         # LLM 调用（Cursor 优先，Gemini 备用）
src/recommender.py         # AI 荐书逻辑
src/economics.py           # 每日经济学逻辑
src/law.py                 # 每日法学逻辑
main.py
```

## 测试

```bash
pip install pytest
pytest tests/ -q
```

## 说明

- 荐书、经济学、法学内容均依赖 AI，请自行判断准确性
- 法学内容不构成法律意见，重要决策请咨询执业律师
- Gemini 联网搜索需模型支持 `googleSearch` 工具；Cursor 后端无联网，失败时会自动降级为模型自身知识或回退 Gemini
- 建议私有仓库；`read` 模式书籍文件需自行管理版权
