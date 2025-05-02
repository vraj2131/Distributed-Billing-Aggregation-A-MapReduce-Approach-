# tests/test_naive.py
import pytest
from pathlib import Path
from mapreduce_billing.naive_aggregation import aggregate_naive

def create_temp_log(tmp_path, lines):
     """
     Helper to write a temporary log file and return its path.
     """
     log_file = tmp_path / "api_logs.txt"
     log_file.write_text("\n".join(lines))
     return str(log_file)


def test_aggregate_naive_single_entry(monkeypatch, tmp_path):
    # Set rate for 'login' via environment
    monkeypatch.setenv("RATE_login", "0.005")

    # Single log entry: user1, 100ms login
    lines = [
        "2025-05-02T00:00:00Z user1 login 200 100ms"
    ]
    log_path = create_temp_log(tmp_path, lines)

    result = aggregate_naive(log_path)
    print("Single entry aggregation result:", result)
    expected = {
        "user1": {
            "total_duration_ms": 100,
            "total_cost": 100 * 0.005
        }
    }
    assert result == expected


def test_aggregate_naive_multiple_entries(monkeypatch, tmp_path):
    # Set rates for multiple tasks
    monkeypatch.setenv("RATE_login", "0.005")
    monkeypatch.setenv("RATE_createOrder", "0.010")

    # Three entries across two users and two tasks
    lines = [
        "2025-05-02T00:00:00Z user1 login 200 100ms",
        "2025-05-02T00:01:00Z user1 createOrder 201 200ms",
        "2025-05-02T00:02:00Z user2 login 200 50ms"
    ]
    log_path = create_temp_log(tmp_path, lines)

    result = aggregate_naive(log_path)
    print("Multiple entries aggregation result:", result)

    # user1: 100ms + 200ms = 300ms; cost = 100*0.005 + 200*0.010
    assert result["user1"]["total_duration_ms"] == 300
    assert pytest.approx(result["user1"]["total_cost"], rel=1e-6) == 100 * 0.005 + 200 * 0.010

    # user2: 50ms; cost = 50*0.005
    assert result["user2"]["total_duration_ms"] == 50
    assert pytest.approx(result["user2"]["total_cost"], rel=1e-6) == 50 * 0.005
