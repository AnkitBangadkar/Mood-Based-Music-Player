from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from soulseek.config import Settings
from soulseek.evaluation import load_queries, run_benchmark
from soulseek.services import build_services


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the active SoulSeek recommender")
    parser.add_argument("corpus", type=Path, help="Corpus root containing data/manifest.json")
    parser.add_argument(
        "--queries", type=Path, default=Path("benchmarks/dev_queries.json")
    )
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--scan-first",
        action="store_true",
        help="Repair/reindex the corpus before benchmarking, reusing the loaded encoder",
    )
    args = parser.parse_args()

    settings = Settings()
    services = build_services(settings)
    services.store.initialize()
    try:
        if args.scan_first:
            def report(phase: str, progress: float, message: str) -> None:
                print(f"[{progress:6.1%}] {phase}: {message}", file=sys.stderr)

            scan_result = services.scan_service.scan(args.corpus, report)
            print(f"Scan result: {json.dumps(scan_result)}", file=sys.stderr)
        result = run_benchmark(
            services.recommender,
            services.store,
            args.corpus / "data" / "manifest.json",
            load_queries(args.queries),
            k=args.k,
            playlist_size=args.size,
        )
    finally:
        services.jobs.shutdown()

    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
