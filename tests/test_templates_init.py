from backend.templates_init import prepare_templates


def test_prepare_templates_creates_frames_and_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.templates_init._cache", None)
    monkeypatch.setattr("backend.config.TEMPLATE_FRAMES_DIR", tmp_path / "target")
    result = prepare_templates()
    assert result.frame_count > 0
    assert len(result.faces_per_frame) == result.frame_count
