from src.notifier.wecom_format import adapt_markdown_for_wework, strip_markdown


def test_strip_markdown_removes_headers_and_bold():
    raw = "## 标题\n**作者**：张三\n---\n- 要点"
    plain = strip_markdown(raw)
    assert "##" not in plain
    assert "**" not in plain
    assert "标题" in plain
    assert "作者" in plain
    assert "要点" in plain


def test_adapt_markdown_converts_headers_to_bold():
    raw = "## 今日荐书\n### 精华观点\n---"
    adapted = adapt_markdown_for_wework(raw)
    assert "**今日荐书**" in adapted
    assert "**精华观点**" in adapted
    assert "---" not in adapted
