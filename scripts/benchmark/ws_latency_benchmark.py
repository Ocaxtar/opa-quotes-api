"""Benchmark de latencia end-to-end para WebSocket quotes.

Escucha el stream WebSocket de opa-quotes-api y calcula percentiles de latencia
usando el timestamp embebido en cada mensaje.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
import websockets


@dataclass
class BenchmarkResult:
    samples: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    elapsed_s: float
    throughput_msg_s: float


def parse_timestamp(value: str) -> datetime:
    """Parsea timestamps ISO-8601 con soporte para sufijo 'Z'."""
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def percentile(sorted_values: list[float], pct: float) -> float:
    """Percentil simple para listas ordenadas."""
    if not sorted_values:
        return 0.0
    if pct <= 0:
        return sorted_values[0]
    if pct >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def format_result(result: BenchmarkResult) -> str:
    return (
        "\n".join(
            [
                "📊 Resultados benchmark WebSocket (opa-quotes-api)",
                f"Samples: {result.samples}",
                f"Elapsed: {result.elapsed_s:.2f}s",
                f"Throughput: {result.throughput_msg_s:.2f} msg/s",
                f"Latency p50: {result.p50_ms:.2f}ms",
                f"Latency p95: {result.p95_ms:.2f}ms",
                f"Latency p99: {result.p99_ms:.2f}ms",
                f"Latency avg: {result.avg_ms:.2f}ms",
                f"Latency min: {result.min_ms:.2f}ms",
                f"Latency max: {result.max_ms:.2f}ms",
            ]
        )
        + "\n"
    )


async def measure_latency(
    ws_url: str,
    duration_s: int,
    warmup_s: int,
    tickers: str | None,
) -> BenchmarkResult:
    latencies: list[float] = []
    start_time = time.time()
    warmup_deadline = start_time + warmup_s
    end_time = start_time + duration_s

    url = ws_url
    if tickers:
        url = f"{ws_url}?tickers={tickers}"

    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
        while time.time() < end_time:
            raw = await ws.recv()
            now = datetime.now(timezone.utc)
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue

            timestamp_raw = payload.get("timestamp")
            if not timestamp_raw:
                continue

            try:
                sent_time = parse_timestamp(timestamp_raw)
            except ValueError:
                continue

            latency_ms = (now - sent_time).total_seconds() * 1000
            if time.time() >= warmup_deadline:
                latencies.append(latency_ms)

    elapsed = max(time.time() - start_time, 0.001)
    sorted_lat = sorted(latencies)
    p50 = percentile(sorted_lat, 50)
    p95 = percentile(sorted_lat, 95)
    p99 = percentile(sorted_lat, 99)
    avg = statistics.fmean(sorted_lat) if sorted_lat else 0.0

    return BenchmarkResult(
        samples=len(sorted_lat),
        p50_ms=p50,
        p95_ms=p95,
        p99_ms=p99,
        min_ms=sorted_lat[0] if sorted_lat else 0.0,
        max_ms=sorted_lat[-1] if sorted_lat else 0.0,
        avg_ms=avg,
        elapsed_s=elapsed,
        throughput_msg_s=len(sorted_lat) / elapsed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark de latencia end-to-end para WebSocket quotes",
    )
    parser.add_argument(
        "--ws-url",
        default="ws://localhost:8000/v1/ws/quotes",
        help="URL base del WebSocket (sin query string)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Duración total de la captura en segundos (default 300)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Tiempo de warmup (segundos) a excluir de métricas (default 10)",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Lista de tickers separados por coma (opcional)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    result = asyncio.run(
        measure_latency(
            ws_url=args.ws_url,
            duration_s=args.duration,
            warmup_s=args.warmup,
            tickers=args.tickers,
        )
    )
    print(format_result(result))


if __name__ == "__main__":
    main()
