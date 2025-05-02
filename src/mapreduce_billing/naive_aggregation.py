# src/mapreduce_billing/naive_aggregation.py
"""
Naive, single-process billing aggregation:
- Reads API log lines from a text file
- Parses each line for user, task, and duration
- Applies per-task rates (from environment variables RATE_<task>)
- Sums total duration and cost per user
- Writes results to an output file
"""
import os
import argparse
from dotenv import load_dotenv


def load_rates():
    """
    Load all environment variables starting with RATE_ into a dict:
      RATE_login=0.005  -> {'login': 0.005, ...}
    """
    load_dotenv()  # load from .env in working dir, if present
    rates = {}
    for name, val in os.environ.items():
        if name.startswith("RATE_"):
            task = name.split("_", 1)[1]
            try:
                rates[task] = float(val)
            except ValueError:
                raise ValueError(f"Invalid rate for {task}: {val}")
    return rates


def parse_line(line: str):
    """
    Parse a log line of the form:
      timestamp user task status duration_ms
    Returns (user, task, duration_ms)
    """
    parts = line.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid log line: '{line.strip()}'")
    _, user, task, _, duration = parts
    if not duration.endswith("ms"):
        raise ValueError(f"Invalid duration format: '{duration}'")
    try:
        duration_ms = int(duration[:-2])
    except ValueError:
        raise ValueError(f"Cannot parse duration: '{duration}'")
    return user, task, duration_ms


def aggregate_naive(input_path: str):
    """
    Perform naive aggregation on the log file:
      - Sum total duration per user
      - Sum total cost per user (duration * rate)
    Returns a dict: { user: {'total_duration_ms': int, 'total_cost': float} }
    """
    rates = load_rates()
    totals = {}
    with open(input_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            user, task, duration = parse_line(line)
            rate = rates.get(task, 0.0)
            cost = duration * rate
            if user not in totals:
                totals[user] = {'total_duration_ms': 0, 'total_cost': 0.0}
            totals[user]['total_duration_ms'] += duration
            totals[user]['total_cost'] += cost
    return totals


def main():
    """
    CLI entry point for naive aggregation.
    Writes output to a file, defaulting to './data/billing.txt'.
    """
    parser = argparse.ArgumentParser(
        description="Naive billing aggregation from API logs"
    )
    parser.add_argument(
        "--input-path", required=True,
        help="Path to the API logs text file"
    )
    parser.add_argument(
        "--output-path", default="./data/billing.txt",
        help="Path to write billing output file"
    )
    args = parser.parse_args()

    results = aggregate_naive(args.input_path)

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Write results
    with open(args.output_path, 'w') as out_f:
        for user, metrics in sorted(results.items()):
            duration = metrics['total_duration_ms']
            cost = metrics['total_cost']
            out_f.write(f"{user}: total_duration={duration}ms, total_cost={cost:.2f}\n")


if __name__ == "__main__":
    main()
