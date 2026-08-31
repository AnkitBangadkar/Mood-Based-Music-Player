from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from soulseek.domain import CatalogProviderFactory, TextEncoder
from soulseek.storage import Store

ProgressCallback = Callable[[str, float, str], None]
logger = logging.getLogger(__name__)


class ScanService:
    def __init__(
        self,
        store: Store,
        provider_factory: CatalogProviderFactory,
        encoder: TextEncoder,
        batch_size: int = 16,
    ):
        self.store = store
        self.provider_factory = provider_factory
        self.encoder = encoder
        self.batch_size = batch_size

    def scan(self, root: Path, progress: ProgressCallback) -> dict:
        resolved = root.expanduser().resolve()
        provider = self.provider_factory.create(resolved)
        root_id = self.store.ensure_root(resolved)
        progress("discovering", 0.01, f"Discovering audio files in {resolved}")
        paths = provider.discover(resolved)
        seen_paths = {str(path.resolve()) for path in paths}
        counters = {"discovered": len(paths), "added": 0, "updated": 0, "unchanged": 0, "errors": 0}
        changed: list[tuple[str, str]] = []
        error_samples: list[dict[str, str]] = []

        for index, path in enumerate(paths, 1):
            try:
                metadata = provider.read(path)
                track_id, action = self.store.upsert_track(root_id, metadata)
                counters[action] += 1
                if action != "unchanged":
                    changed.append((track_id, metadata.searchable_text))
            except Exception as error:  # one corrupt file must not abort a library scan
                counters["errors"] += 1
                if len(error_samples) < 20:
                    error_samples.append({"path": str(path), "message": str(error)})
            fraction = 0.05 + 0.55 * index / max(1, len(paths))
            progress("metadata", fraction, f"Reading metadata {index}/{len(paths)}")

        changed_by_id = dict(changed)
        for track_id, text in self.store.tracks_missing_embeddings(
            root_id, self.encoder.encoder_id
        ):
            changed_by_id.setdefault(track_id, text)
        changed = list(changed_by_id.items())
        counters["embedded"] = len(changed)

        for start in range(0, len(changed), self.batch_size):
            batch = changed[start : start + self.batch_size]
            progress(
                "embedding",
                0.60 + 0.38 * start / max(1, len(changed)),
                f"Loading encoder and embedding tracks {start}/{len(changed)}",
            )
            vectors = self.encoder.encode_documents([text for _, text in batch])
            self.store.upsert_embeddings(
                self.encoder.encoder_id,
                [(track_id, vector) for (track_id, _), vector in zip(batch, vectors, strict=True)],
            )
            done = min(start + len(batch), len(changed))
            fraction = 0.60 + 0.38 * done / max(1, len(changed))
            progress("embedding", fraction, f"Embedding changed tracks {done}/{len(changed)}")

        missing = self.store.finish_root_scan(root_id, seen_paths)
        counters["missing"] = missing
        counters["error_samples"] = error_samples
        progress("complete", 1.0, "Scan complete")
        return counters


class JobManager:
    def __init__(self, store: Store, scan_service: ScanService):
        self.store = store
        self.scan_service = scan_service
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="soulseek-jobs")

    def submit_scan(self, root: Path) -> str:
        job_id = self.store.create_job("library_scan")
        self.executor.submit(self._run_scan, job_id, root)
        return job_id

    def _run_scan(self, job_id: str, root: Path) -> None:
        self.store.update_job(
            job_id, status="running", phase="starting", progress=0, message="Starting scan"
        )

        def progress(phase: str, value: float, message: str) -> None:
            self.store.update_job(job_id, phase=phase, progress=value, message=message)

        try:
            result = self.scan_service.scan(root, progress)
            self.store.update_job(
                job_id,
                status="succeeded",
                phase="complete",
                progress=1,
                message="Scan complete",
                result=result,
            )
        except Exception as error:
            logger.exception("Library scan job %s failed", job_id)
            self.store.update_job(
                job_id,
                status="failed",
                phase="failed",
                message=str(error),
                error={
                    "code": "scan_failed",
                    "message": str(error),
                },
            )

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
