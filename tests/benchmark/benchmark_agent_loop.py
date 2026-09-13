"""Headless benchmark of the MCP agent loop.
Requires: the job_db Postgres container running, and valid .key files under
career_matcher_agentic/{llm,embedder,mcp_servers/crawler}/.key.

trigger_crawler is benchmarked in dry-run mode by mock McpBridge.call_tool, since a
live run would scrape a real external site via paid Firecrawl and write to the shared DB.

Usage: 
    uv run python tests/benchmark/benchmark_agent_loop.py --cv-path "path/to/cv.pdf"
"""

import argparse
import statistics
import time
from unittest.mock import patch

from tqdm import tqdm  # Ensure you have 'tqdm' installed: uv pip install tqdm

from career_matcher_agentic.mcp_clients.mcp_bridge import McpBridge
from career_matcher_agentic.mcp_host.llm import run_turn

DRY_RUN_TOOLS = {"job_crawler__trigger_crawler"}


def _percentile(data: list[float], pct: float) -> float:
    """Linear-interpolation percentile (matches numpy's default 'linear' method)."""
    ordered = sorted(data)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100)
    lo, hi = int(rank), min(int(rank) + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] + frac * (ordered[hi] - ordered[lo])


def build_cases(cv_path: str | None) -> list[tuple[str, str | None]]:
    cases = [
        ("What job boards can you crawl job listings from?", "job_crawler__list_supported_sites"),
        ("List the job sites you support crawling.", "job_crawler__list_supported_sites"),
        ("I know Python, FastAPI, Docker, and PostgreSQL. Find me matching jobs, limit 3.", "career_matcher__match_jobs_from_prompt"),
        ("My skills are React, TypeScript, and Node.js. Any matches? limit 2", "career_matcher__match_jobs_from_prompt"),
        ("I'm searching for a job with Java, Spring Boot, and SQL skills, remote preferred.", "career_matcher__match_jobs_from_prompt"),
        ("What's the weather like today?", None),  # expect no tool call
        ("Crawl itviec.com for AI Engineer job postings.", "job_crawler__trigger_crawler"),  # dry-run only
    ]
    if cv_path:
        cases += [
            (f"Here's my CV at {cv_path}. Find jobs matching it using semantic/embedding search, limit 3.", "embedding_matcher__match_jobs_from_cv_embedding"),
            (f"Using the CV at {cv_path}, find matching jobs via literal keyword match only, don't use embeddings.", "career_matcher__match_jobs_from_cv"),
            (f"Given the CV at {cv_path}, semantically match me to jobs, limit to 3.", "embedding_matcher__match_jobs_from_cv_embedding"),
        ]
    return cases


def run_case(bridge: McpBridge, prompt: str, expected: str | None) -> dict:
    history: list = []
    start = time.perf_counter()

    if expected in DRY_RUN_TOOLS:
        with patch.object(
            McpBridge, "call_tool",
            return_value={"matches": [], "total_jobs_in_db": 0, "last_crawled_at": None, "note": "dry-run stub"},
        ):
            _, log = run_turn(history, prompt, bridge)
    else:
        _, log = run_turn(history, prompt, bridge)

    elapsed = time.perf_counter() - start
    called = [entry["tool"] for entry in log]
    first_call = called[0] if called else None
    correct = (first_call == expected) if expected else (first_call is None)

    return {
        "prompt": prompt[:60],
        "expected": expected,
        "called": called,
        "correct": correct,
        "rounds": len(log),
        "latency_s": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cv-path", default=None, help="Path to a real CV file, to also benchmark the CV-based matching tools.")
    args = parser.parse_args()

    if not args.cv_path:
        print("No --cv-path given: skipping match_jobs_from_cv / match_jobs_from_cv_embedding cases.\n")

    bridge = McpBridge()
    cases = build_cases(args.cv_path)
    results = []

    # Iterate with tqdm to show real-time progress
    with tqdm(total=len(cases), desc="Benchmarking", unit="case") as pbar:
        for prompt, expected in cases:
            # Update the progress bar text to show the current prompt being tested
            pbar.set_postfix_str(f"Running: {prompt[:30]}...")
            
            # Run the case
            result = run_case(bridge, prompt, expected)
            results.append(result)
            
            # Advance the progress bar by 1
            pbar.update(1)

    print("\n--- Individual Results ---")
    for r in results:
        print(f"[{r['latency_s']:6.2f}s] expected={r['expected']!r:45} called={r['called']!r:55} correct={r['correct']}")

    latencies = [r["latency_s"] for r in results]
    accuracy = sum(r["correct"] for r in results) / len(results)

    print("\n--- Summary ---")
    print(f"Cases: {len(results)}")
    print(f"Tool-selection accuracy: {accuracy:.1%}")
    print(f"Latency avg: {statistics.mean(latencies):.2f}s  median: {statistics.median(latencies):.2f}s  "
          f"p95: {_percentile(latencies, 95):.2f}s  min: {min(latencies):.2f}s  max: {max(latencies):.2f}s")
    print(f"Avg rounds per turn: {statistics.mean(r['rounds'] for r in results):.2f}")

    wrong = [r for r in results if not r["correct"]]
    if wrong:
        print("\nMisses:")
        for r in wrong:
            print(f"  - {r['prompt']!r} -> expected {r['expected']}, got {r['called']}")


if __name__ == "__main__":
    main()