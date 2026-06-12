# 每日读书推送 (daily_book_push)

GitHub Actions 定时推送书籍片段到飞书/企业微信，并用 Gemini 生成每日摘要与精华总结。

## 功能

- 书籍以 txt 存放在 `books/` 目录
- 在 `config/books.yaml` 配置推哪些书、每日字数
- 多本书按 **round-robin 轮播**，每天只推 1 本
- 阅读进度保存在 `state/progress.json`，Actions 自动 commit 回仓库
- AI 摘要失败时仍推送正文

## 快速开始（GitHub Actions）

### 1. 创建仓库并推送代码

将本项目推送到 GitHub（建议私有仓库，书籍可能有版权）。

### 2. 配置 Secrets

`Settings` → `Secrets and variables` → `Actions`

| Secret | 说明 | 必填 |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key | AI 开启时必填 |
| `FEISHU_WEBHOOK_URL` | 飞书群机器人 Webhook | 至少配一个通知渠道 |
| `WECHAT_WEBHOOK_URL` | 企业微信群机器人 Webhook | 至少配一个通知渠道 |

可选 Secrets / Variables：

| 名称 | 说明 |
|---|---|
| `GEMINI_MODEL` | 默认 `gemini/gemini-2.5-flash` |
| `GEMINI_MODEL_FALLBACK` | 备用模型 |
| `FEISHU_WEBHOOK_SECRET` | 飞书签名校验 |
| `FEISHU_WEBHOOK_KEYWORD` | 飞书关键词 |
| `WECHAT_MSG_TYPE` | `markdown` 或 `text` |

### 3. 添加书籍

1. 将 txt 放入 `books/`
2. 编辑 `config/books.yaml` 增加条目并设置 `enabled: true`

### 4. 手动测试

Actions → **每日读书推送** → **Run workflow**

可选参数：

- `dry_run=true`：只预览，不推送、不写进度
- `book_id=sample`：强制指定书籍

默认定时：每天 UTC 0:00（北京时间 08:00）。

## 本地调试

```bash
cd daily_book_push
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 GEMINI_API_KEY 和 Webhook

python main.py --dry-run
python main.py --dry-run --book sample
python main.py --notify-test
python main.py --reset sample
```

## CLI

```bash
python main.py                 # 正常运行
python main.py --dry-run       # 预览
python main.py --book ID       # 指定书籍
python main.py --reset ID      # 重置进度
python main.py --skip-ai       # 跳过 AI
python main.py --notify-test   # 测试通知
```

## 目录结构

```
books/              # txt 书籍
config/books.yaml   # 书籍与 AI 配置
state/progress.json # 阅读进度（自动更新）
src/                # 核心逻辑
main.py             # 入口
```

## 测试

```bash
pip install pytest
pytest tests/ -q
```

## 注意事项

- 书籍 txt 建议使用 UTF-8 编码
- Webhook 消息过长会自动分批发送
- Actions cron 可能延迟数分钟
- 建议使用私有仓库存放书籍内容

## 参考

实现思路借鉴 [daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 的 GitHub Actions、LiteLLM 与飞书/企微推送模式。
