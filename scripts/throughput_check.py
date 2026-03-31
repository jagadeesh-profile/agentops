from __future__ import annotations

import argparse
import concurrent.futures
import json
import time
import urllib.request


def post_job(base_url: str, index: int) -> str:
    payload = json.dumps(
        {
            "session_id": f"bench-{index}",
            "topic": f"research topic {index}",
            "constraints": [],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/jobs",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["id"]


def wait_for_completion(base_url: str, job_id: str, timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with urllib.request.urlopen(f"{base_url}/jobs/{job_id}", timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        status = data.get("status")
        if status == "completed":
            return True
        if status == "failed":
            return False
        time.sleep(0.2)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Concurrent throughput check for orchestration API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--jobs", type=int, default=20)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--poll-timeout", type=int, default=30)
    args = parser.parse_args()

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        job_ids = list(ex.map(lambda i: post_job(args.base_url, i), range(args.jobs)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        completed = list(
            ex.map(
                lambda job_id: wait_for_completion(args.base_url, job_id, args.poll_timeout),
                job_ids,
            )
        )
    duration = time.time() - start

    ok = sum(1 for item in completed if item)
    result = {
        "total": args.jobs,
        "completed": ok,
        "success_rate_percent": round((ok / args.jobs) * 100, 2) if args.jobs else 0.0,
        "duration_sec": round(duration, 2),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
