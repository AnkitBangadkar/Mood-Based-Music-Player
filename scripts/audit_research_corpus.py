from __future__ import annotations

import argparse
import json
from pathlib import Path

from soulseek.research import audit_research_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a SoulSeek research corpus")
    parser.add_argument("root", type=Path, help="Corpus root containing audio/ and data/")
    parser.add_argument(
        "--hashes", action="store_true", help="Hash every audio file to find exact duplicates"
    )
    args = parser.parse_args()
    print(json.dumps(audit_research_corpus(args.root, hashes=args.hashes), indent=2))


if __name__ == "__main__":
    main()
