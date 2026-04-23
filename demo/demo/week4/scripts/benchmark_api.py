from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import re
import statistics
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


PATH_PATTERN = re.compile(r"^  (/[^:]+):\s*$")
METHOD_PATTERN = re.compile(r"^    (get|post|put|patch|delete|options|head):\s*$")
PATH_PARAM_PATTERN = re.compile(r"\{[^}]+\}")


@dataclass
class RequestResult:
    endpoint: str
    latency_ms: float
    ok: bool
    status_code: int | None
    error: str | None


def parse_get_endpoints(openapi_path: Path) -> List[str]:
    content = openapi_path.read_text(encoding="utf-8").splitlines()
    current_path: str | None = None
    path_has_get: Dict[str, bool] = {}

    for line in content:
        path_match = PATH_PATTERN.match(line)
        if path_match:
            current_path = path_match.group(1)
            path_has_get[current_path] = False
            continue

        method_match = METHOD_PATTERN.match(line)
        if method_match and current_path:
            if method_match.group(1) == "get":
                path_has_get[current_path] = True

        if line and not line.startswith(" "):
            current_path = None

    endpoints = [path for path, has_get in path_has_get.items() if has_get]
    return sorted(endpoints)


def normalize_endpoint(endpoint: str) -> str:
    return PATH_PARAM_PATTERN.sub("1", endpoint)


def send_request(base_url: str, endpoint: str, timeout: float, bearer_token: str | None) -> RequestResult:
    url = f"{base_url.rstrip('/')}{endpoint}"
    request = urllib.request.Request(url, method="GET")
    if bearer_token:
        request.add_header("Authorization", f"Bearer {bearer_token}")

    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            latency_ms = (time.perf_counter() - started) * 1000
            status_code = getattr(response, "status", None)
            ok = 200 <= (status_code or 0) < 400
            return RequestResult(endpoint, latency_ms, ok, status_code, None)
    except urllib.error.HTTPError as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        return RequestResult(endpoint, latency_ms, False, exc.code, str(exc))
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.perf_counter() - started) * 1000
        return RequestResult(endpoint, latency_ms, False, None, str(exc))


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * p
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return values[low]
    weight = rank - low
    return values[low] * (1 - weight) + values[high] * weight


def summarize_results(results: List[RequestResult]) -> Dict[str, Dict[str, float | int]]:
    grouped: Dict[str, List[RequestResult]] = defaultdict(list)
    for item in results:
        grouped[item.endpoint].append(item)

    summary: Dict[str, Dict[str, float | int]] = {}
    for endpoint, items in grouped.items():
        latencies = sorted(i.latency_ms for i in items)
        total = len(items)
        errors = sum(1 for i in items if not i.ok)
        summary[endpoint] = {
            "total_requests": total,
            "successful_requests": total - errors,
            "error_requests": errors,
            "error_rate_pct": round((errors / total) * 100, 2) if total else 0.0,
            "avg_response_time_ms": round(statistics.fmean(latencies), 2) if latencies else 0.0,
            "p50_response_time_ms": round(percentile(latencies, 0.50), 2) if latencies else 0.0,
            "p95_response_time_ms": round(percentile(latencies, 0.95), 2) if latencies else 0.0,
            "min_response_time_ms": round(latencies[0], 2) if latencies else 0.0,
            "max_response_time_ms": round(latencies[-1], 2) if latencies else 0.0,
        }
    return summary


def run_benchmark(
    base_url: str,
    endpoints: List[str],
    total_requests: int,
    concurrency: int,
    timeout: float,
    bearer_token: str | None,
) -> Tuple[List[RequestResult], float]:
    scheduled_endpoints: List[str] = []
    for i in range(total_requests):
        scheduled_endpoints.append(normalize_endpoint(endpoints[i % len(endpoints)]))

    started = time.perf_counter()
    results: List[RequestResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(send_request, base_url, endpoint, timeout, bearer_token)
            for endpoint in scheduled_endpoints
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    elapsed_sec = time.perf_counter() - started
    return results, elapsed_sec


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark API response time and error rate from OpenAPI GET endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL of API server")
    parser.add_argument("--openapi", default="openapi.yaml", help="Path to OpenAPI spec file")
    parser.add_argument("--requests", type=int, default=200, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout per request in seconds")
    parser.add_argument("--bearer-token", default=None, help="Optional Bearer token value")
    parser.add_argument("--output", default=None, help="Optional JSON output file path")
    args = parser.parse_args()

    openapi_path = Path(args.openapi).resolve()
    if not openapi_path.exists():
        raise FileNotFoundError(f"OpenAPI file not found: {openapi_path}")
    if args.requests <= 0:
        raise ValueError("--requests must be > 0")
    if args.concurrency <= 0:
        raise ValueError("--concurrency must be > 0")

    endpoints = parse_get_endpoints(openapi_path)
    if not endpoints:
        raise RuntimeError("No GET endpoints found in OpenAPI file.")

    results, elapsed_sec = run_benchmark(
        base_url=args.base_url,
        endpoints=endpoints,
        total_requests=args.requests,
        concurrency=args.concurrency,
        timeout=args.timeout,
        bearer_token=args.bearer_token,
    )
    summary = summarize_results(results)
    total_errors = sum(1 for r in results if not r.ok)

    report = {
        "base_url": args.base_url,
        "openapi": str(openapi_path),
        "total_requests": len(results),
        "concurrency": args.concurrency,
        "elapsed_seconds": round(elapsed_sec, 3),
        "throughput_rps": round(len(results) / elapsed_sec, 2) if elapsed_sec else 0.0,
        "overall_error_rate_pct": round((total_errors / len(results)) * 100, 2) if results else 0.0,
        "endpoints": summary,
    }

    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.write_text(output, encoding="utf-8")
        print(f"\nSaved benchmark report to: {out_path}")


if __name__ == "__main__":
    main()
