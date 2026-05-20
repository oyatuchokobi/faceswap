from backend.templates_init import prepare_templates
from backend.config import TEMPLATE_FRAMES_DIR


def test_prepare_templates_creates_frames_and_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.templates_init._cache", None)
    monkeypatch.setattr("backend.config.TEMPLATE_FRAMES_DIR", tmp_path / "basketball")
    result = prepare_templates()
    assert result.frame_count == 121
    assert result.faces_per_frame
    assert len(result.faces_per_frame) == 121
