from app.config import settings


def test_cors_origin_list_parses_comma_separated_values():
    assert settings.cors_origin_list == ["http://localhost:5173"]


def test_data_cache_path_resolves_relative_to_backend_root(tmp_path):
    expected = settings.__class__.model_config["env_file"].parent / "app" / "data"
    assert settings.data_cache_path == expected


def test_data_cache_path_preserves_absolute_path(tmp_path):

    old = settings.data_cache_dir
    try:
        object.__setattr__(settings, "data_cache_dir", str(tmp_path / "cache"))
        assert settings.data_cache_path == tmp_path / "cache"
    finally:
        object.__setattr__(settings, "data_cache_dir", old)
