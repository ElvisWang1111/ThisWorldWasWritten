from synthetic_world.site_builder import _markup_to_html
from synthetic_world.llm_client import extract_json, extract_json_list


def test_markup_links_and_cites():
    title_to_slug = {"velmora": "velmora"}
    ref_numbers = {"src_000001": 1}
    out = _markup_to_html(
        "Velmora is in [[Velmora]].{cite:src_000001}",
        title_to_slug, ref_numbers, rel="../",
    )
    assert '<a href="../wiki/velmora.html">Velmora</a>' in out
    assert 'href="#cite-src_000001">[1]</a>' in out
    assert out.startswith("<p>")


def test_markup_escapes_html():
    out = _markup_to_html("a < b & c", {}, {}, rel="")
    assert "&lt;" in out and "&amp;" in out


def test_markup_unknown_link_falls_back_to_text():
    out = _markup_to_html("See [[Nowhere]].", {}, {}, rel="")
    assert "Nowhere" in out
    assert "<a" not in out


def test_extract_json_handles_code_fence():
    text = "Here you go:\n```json\n{\"a\": 1}\n```\nThanks!"
    assert extract_json(text) == {"a": 1}


def test_extract_json_list_from_array():
    text = '[{"x": 1}, {"x": 2}]'
    assert extract_json_list(text) == [{"x": 1}, {"x": 2}]


def test_extract_json_list_from_jsonl():
    text = '{"x": 1}\n{"x": 2}\n'
    assert extract_json_list(text) == [{"x": 1}, {"x": 2}]


def test_extract_json_repairs_truncated_object():
    from synthetic_world.llm_client import extract_json
    # Object truncated mid-string inside a nested array (the real failure mode).
    text = (
        '{\n  "summary": "Added three countries.",\n'
        '  "new_entities": [\n'
        '    {"name": "Valdoria", "entity_type": "country"},\n'
        '    {"name": "Severia", "entity_type": "country", "description": "Mountain k'
    )
    out = extract_json(text)
    assert out["summary"] == "Added three countries."
    names = [e["name"] for e in out["new_entities"]]
    assert "Valdoria" in names  # the complete entity survives


def test_extract_json_list_salvages_truncated_array():
    # Simulates an LLM response cut off mid-object at max_tokens, inside an
    # unterminated ```json fence (no closing fence, no closing bracket).
    text = (
        '```json\n[\n'
        '  {"name": "Velmora", "entity_type": "city"},\n'
        '  {"name": "Loras", "entity_type": "city"},\n'
        '  {"name": "Sarnath C'
    )
    out = extract_json_list(text)
    assert [o["name"] for o in out] == ["Velmora", "Loras"]
