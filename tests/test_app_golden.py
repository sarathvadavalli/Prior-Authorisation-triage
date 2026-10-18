"""Fixed synthetic UI interactions compared with authored golden expectations."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests" / "golden" / "ui.json").read_text(encoding="utf-8"))


def snapshot(app):
    """Inspect both returned data and the actual result panel visible to users."""
    panel = app.container(key="result_panel")
    return {
        "result": app.session_state["last_result"],
        "success": [element.value for element in panel.success],
        "warning": [element.value for element in panel.warning],
        "info": [element.value for element in panel.info],
        "text": [element.value for element in panel.text],
        "markdown": [element.value for element in panel.markdown],
        "captions": [element.value for element in panel.caption],
        "visible_controls": sorted(
            element.key
            for kind in ("selectbox", "segmented_control", "text_input", "checkbox", "button")
            for element in getattr(app, kind)
        ),
    }


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_ui_golden(case):
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    assert not app.exception
    for step in case["steps"]:
        for kind in ("selectbox", "segmented_control", "text_input", "checkbox"):
            for key, value in step.get(kind, {}).items():
                getattr(app, kind)(key=key).set_value(value)
        if "button" in step:
            app.button(key=step["button"]).click()
        app.run()
        assert not app.exception
        if "expected" in step:
            assert snapshot(app) == step["expected"]
