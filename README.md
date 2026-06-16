# daily_book_push

GitHub Actions 每日定时推送：**Gemini AI 荐书 + 精华总结** 到飞书 / 企业微信。无需本地存储书籍。

## 两种模式（可兼容）

| 模式 | 说明 | 命令 / 配置 |
|---|---|---|
| **recommend** | 纯 AI 每日荐书 + 精华金句 | `mode: recommend` |
| **read** | 本地 txt 分段阅读 + AI 摘要 | `mode: read` |
| **both** | 同一天推两条：先读书、后荐书 | `mode: both` |
| **alternate** | 按日轮换：一天读书、一天荐书 | `mode: alternate` |

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
```

## 荐书模式详情

每天由 Gemini 根据偏好与历史记录推荐一本书，推送内容包含：

- 为什么今天推荐
- 一句话概括
- 精华观点（3-5 条）
- 金句摘录
- 适合谁读 / 阅读建议

配置见 [`config/recommend.yaml`](config/recommend.yaml)：

- `categories`：感兴趣的领域
- `rotate_categories`：每天轮换一个侧重类别
- `use_google_search`：是否启用 Gemini 联网（需支持的模型）
- `avoid_repeat`：避免与近 90 天推荐重复

历史记录保存在 `state/recommend_history.json`。

## 快速开始（GitHub Actions）

### Secrets

| Secret | 说明 | 必填 |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key | 是 |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 | 至少一个 |
| `WECHAT_WEBHOOK_URL` | 企业微信机器人 | 至少一个 |

可选：`GEMINI_MODEL`、`GEMINI_USE_SEARCH`、`FEISHU_WEBHOOK_SECRET`

### 手动测试

Actions → **每日荐书推送** → Run workflow

- `mode=recommend`（默认）
- `dry_run=true` 可仅预览

默认定时：每天 UTC 0:00（北京时间 08:00）。

## 本地调试

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 GEMINI_API_KEY 和 Webhook

python main.py --dry-run              # 预览今日荐书
python main.py                        # 正式推送
python main.py --notify-test          # 测试通知
python main.py --mode read --dry-run  # 旧模式：本地 txt
```

## 目录结构

```
config/recommend.yaml      # 荐书偏好
config/books.yaml          # [read 模式] 本地书籍
state/recommend_history.json
state/progress.json        # [read 模式] 阅读进度
src/recommender.py         # AI 荐书逻辑
main.py
```

## 测试

```bash
pip install pytest
pytest tests/ -q
```

## 说明

- 荐书内容依赖 AI，请自行判断准确性；金句可能为概括或意译
- 联网搜索需 Gemini 支持 `googleSearch` 工具；失败时会自动降级为模型自身知识
- 建议私有仓库；`read` 模式书籍文件需自行管理版权
