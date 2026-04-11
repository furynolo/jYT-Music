from utils.duration_utils import parse_duration_to_seconds, format_seconds_to_human

def test_parse_duration_to_seconds():
    # Simple MM:SS
    assert parse_duration_to_seconds("4:20") == 260
    # Long MM:SS
    assert parse_duration_to_seconds("15:00") == 900
    # H:MM:SS
    assert parse_duration_to_seconds("1:05:30") == 3930
    # Edge cases
    assert parse_duration_to_seconds("") == 0
    assert parse_duration_to_seconds(None) == 0
    assert parse_duration_to_seconds("abc") == 0
    assert parse_duration_to_seconds("10") == 0

def test_format_seconds_to_human():
    # Minutes only
    assert format_seconds_to_human(45 * 60) == "45 minutes"
    # Single minute
    assert format_seconds_to_human(60) == "1 minute"
    # Hours and minutes
    assert format_seconds_to_human(3600 + 600) == "1 hour 10 minutes"
    # Single hour
    assert format_seconds_to_human(3600) == "1 hour"
    # Multi hour
    assert format_seconds_to_human(7200 + 120) == "2 hours 2 minutes"
    # Seconds only (short)
    assert format_seconds_to_human(15) == "15 seconds"
    # Zero/Negative
    assert format_seconds_to_human(0) == ""
    assert format_seconds_to_human(-10) == ""
