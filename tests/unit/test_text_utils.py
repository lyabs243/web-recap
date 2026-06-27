from app.modules.recap.application.services.text_utils import language_name, normalize_text, trim_to_chars


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("One\n\n  two\t three") == "One two three"


def test_trim_to_chars_adds_ellipsis_when_needed() -> None:
    assert trim_to_chars("abcdef", 5) == "abcd…"


def test_language_name_maps_supported_codes() -> None:
    assert language_name("fr") == "French"
    assert language_name("en") == "English"