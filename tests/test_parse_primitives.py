from backend.app import _parse_primitives

FULL = '{"name": "saucer", "reynoldsNumber": 150, "primitives": [{"kind": "cylinder", "x": 0.0, "y": 0.0, "w": 0.4, "h": 0.4, "d": 0.1, "color": "#5c89a6"}, {"kind": "cone", "x": -0.1, "y": 0.1, "w": 0.2, "h": 0.2, "d": 0.2, "color": "#ede6dd"}]}'


def test_complete_json_gives_all_parts_name_and_re():
    parts, name, re_val = _parse_primitives(FULL)
    assert [p["kind"] for p in parts] == ["cylinder", "cone"]
    assert name == "saucer" and re_val == 150


def test_markdown_fences_are_ignored():
    parts, _, _ = _parse_primitives("```json\n" + FULL + "\n```")
    assert len(parts) == 2


def test_reply_cut_off_at_token_limit_keeps_complete_parts():
    # The real failure: the model hit max_new_tokens mid-object, so json.loads on the whole reply failed.
    cut = FULL[: FULL.rindex('{"kind": "cone"') + 30]
    parts, name, re_val = _parse_primitives(cut)
    assert [p["kind"] for p in parts] == ["cylinder"]
    assert name == "saucer" and re_val == 150


def test_garbage_gives_no_parts():
    assert _parse_primitives("sorry, I cannot do that")[0] == []


def test_out_of_range_values_are_clamped():
    parts, _, _ = _parse_primitives('{"kind": "box", "x": 9, "y": -9, "w": 5, "h": 0, "d": 1}')
    p = parts[0]
    assert -0.55 <= p["x"] <= 0.45 and -0.5 <= p["y"] <= 0.5 and p["w"] <= 0.65 and p["h"] >= 0.08
