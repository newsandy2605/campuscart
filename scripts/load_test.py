"""Concurrent HTTP smoke/load test. Example: python scripts/load_test.py --url http://localhost:8100/health --requests 200 --concurrency 20"""
from __future__ import annotations
import argparse, asyncio, statistics, time
import httpx

async def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--url', default='http://localhost:8100/health'); p.add_argument('--requests', type=int, default=100); p.add_argument('--concurrency', type=int, default=10); p.add_argument('--timeout', type=float, default=10); args=p.parse_args()
    sem=asyncio.Semaphore(max(1,args.concurrency)); samples=[]; failures=0
    async with httpx.AsyncClient(timeout=args.timeout) as client:
      async def one():
        nonlocal failures
        async with sem:
          t=time.perf_counter()
          try:
            r=await client.get(args.url); r.raise_for_status()
          except Exception:
            failures += 1
          finally:
            samples.append((time.perf_counter()-t)*1000)
      await asyncio.gather(*(one() for _ in range(max(1,args.requests))))
    ordered=sorted(samples); p95=ordered[max(0,int(len(ordered)*0.95)-1)]
    print({'url':args.url,'requests':len(samples),'failures':failures,'mean_ms':round(statistics.mean(samples),2),'p50_ms':round(statistics.median(samples),2),'p95_ms':round(p95,2),'max_ms':round(max(samples),2)})

if __name__=='__main__': asyncio.run(main())
