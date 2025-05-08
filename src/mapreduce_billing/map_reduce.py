"""
Core MapReduce functions for Spark billing aggregation:
- map_records: convert each log line into (user, (duration_ms, cost))
- reduce_records: sum durations and costs across records for a given user
"""

from .naive_aggregation import load_rates, parse_line

def map_records(lines_rdd):
    """
    Transform an RDD of log lines into an RDD of (user, (duration_ms, cost)).

    Args:
        lines_rdd (pyspark.RDD[str]): RDD where each element is a log line string.

    Returns:
        pyspark.RDD[(str, (int, float))]: RDD of user to (duration, cost) tuples.
    """
    rates = load_rates()

    def to_pair(line):
        user, task, duration = parse_line(line)
        rate = rates.get(task, 0.0)
        cost = duration * rate
        return user, (duration, cost)

    return lines_rdd.map(to_pair)

def reduce_records(a, b):
    """
    Combine two (duration, cost) tuples by summing their components.

    Args:
        a (tuple[int, float]): (duration_ms, cost)
        b (tuple[int, float]): (duration_ms, cost)

    Returns:
        tuple[int, float]: summed (duration_ms, cost)
    """
    return a[0] + b[0], a[1] + b[1]
