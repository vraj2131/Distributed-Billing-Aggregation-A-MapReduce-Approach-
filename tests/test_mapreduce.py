# tests/test_mapreduce.py
import pytest
import logging
from mapreduce_billing.map_reduce import map_records, reduce_records
import os

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FakeRDD to simulate minimal RDD behavior for map and reduceByKey
class FakeRDD:
    def __init__(self, data):
        self.data = data

    def map(self, fn):
        mapped = [fn(x) for x in self.data]
        logger.info("map_records output: %s", mapped)
        print("map_records output:", mapped)
        return FakeRDD(mapped)

    def reduceByKey(self, fn):
        result = {}
        for key, value in self.data:
            if key in result:
                result[key] = fn(result[key], value)
            else:
                result[key] = value
        reduced = list(result.items())
        logger.info("reduce_records output: %s", reduced)
        print("reduce_records output:", reduced)
        return FakeRDD(reduced)

    def collect(self):
        return self.data


def test_map_records_single_entry(monkeypatch):
    # Set rate for 'login'
    monkeypatch.setenv("RATE_login", "0.005")
    lines = ["2025-05-02T00:00:00Z user1 login 200 100ms"]
    fake_rdd = FakeRDD(lines)

    mapped = map_records(fake_rdd).collect()
    assert len(mapped) == 1
    user, (duration, cost) = mapped[0]
    assert user == "user1"
    assert duration == 100
    assert cost == pytest.approx(100 * 0.005)


def test_reduce_records():
    a = (100, 0.5)
    b = (200, 2.0)
    result = reduce_records(a, b)
    logger.info("reduce_records single combine result: %s", result)
    print("reduce_records single combine result:", result)
    assert result == (300, pytest.approx(2.5))


def test_map_reduce_multiple_entries(monkeypatch):
    # Set rates for tasks
    monkeypatch.setenv("RATE_login", "0.005")
    monkeypatch.setenv("RATE_createOrder", "0.010")

    lines = [
        "2025-05-02T00:00:00Z user1 login 200 100ms",
        "2025-05-02T00:01:00Z user1 createOrder 201 200ms",
        "2025-05-02T00:02:00Z user2 login 200 50ms"
    ]
    fake_rdd = FakeRDD(lines)

    mapped_rdd = map_records(fake_rdd)
    reduced_rdd = mapped_rdd.reduceByKey(reduce_records)
    aggregated = reduced_rdd.collect()

    # Log and print final aggregated results
    logger.info("final aggregated results: %s", aggregated)
    print("final aggregated results:", aggregated)

    result_dict = {user: metrics for user, metrics in aggregated}

    # user1: duration 300ms, cost = 100*0.005 + 200*0.010
    duration1, cost1 = result_dict["user1"]
    assert duration1 == 300
    assert cost1 == pytest.approx(100 * 0.005 + 200 * 0.010)

    # user2: duration 50ms, cost = 50*0.005
    duration2, cost2 = result_dict["user2"]
    assert duration2 == 50
    assert cost2 == pytest.approx(50 * 0.005)
