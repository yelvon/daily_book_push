from src.splitter import split_text


def test_split_at_paragraph_boundary():
    text = "第一段内容。" * 50 + "\n\n" + "第二段开始。" * 50
    result = split_text(text, offset=0, daily_chars=100)
    assert result.segment
    assert result.new_offset > 0
    assert result.new_offset <= len(text)
    assert not result.is_finished or result.new_offset == len(text)


def test_split_finished():
    text = "很短的内容。"
    result = split_text(text, offset=0, daily_chars=2000)
    assert result.is_finished
    assert result.new_offset == len(text)
    assert result.progress_pct == 100.0


def test_split_resume_offset():
    text = "abc" * 100
    first = split_text(text, offset=0, daily_chars=50)
    second = split_text(text, offset=first.new_offset, daily_chars=50)
    assert second.new_offset > first.new_offset


def test_split_empty_at_end():
    text = "完结"
    result = split_text(text, offset=len(text), daily_chars=100)
    assert result.is_finished
    assert result.segment == ""
