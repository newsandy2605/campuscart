"""Small reproducible API latency benchmark for the deployed local/dev API."""
from __future__ import annotations

import argparse
import statistics
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8100/health")
    parser.add_argument("--requests", type=int, default=50)
    args = parser.parse_args()

    samples = []
    failures = 0
    for _ in range(max(1, args.requests)):
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(args.url, timeout=5) as response:
                response.read()
                if response.status != 200:
                    failures += 1
        except Exception:
            failures += 1
        samples.append((time.perf_counter() - started) * 1000)

    ordered = sorted(samples)
    p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
    print({
        "url": args.url,
        "requests": len(samples),
        "failures": failures,
        "mean_ms": round(statistics.mean(samples), 2),
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(p95, 2),
        "max_ms": round(max(samples), 2),
    })


if __name__ == "__main__":
    main()
