from __future__ import annotations

from dataclasses import dataclass

from soulseek.catalog import CatalogProviderRouter
from soulseek.config import Settings
from soulseek.domain import TextEncoder
from soulseek.encoders import HashingTextEncoder, SentenceTransformerEncoder
from soulseek.recommender import RecommendationService
from soulseek.scanning import JobManager, ScanService
from soulseek.storage import Store


@dataclass(slots=True)
class Services:
    settings: Settings
    store: Store
    encoder: TextEncoder
    recommender: RecommendationService
    scan_service: ScanService
    jobs: JobManager


def build_services(settings: Settings, encoder: TextEncoder | None = None) -> Services:
    store = Store(settings.db_path)
    if encoder is None:
        if settings.encoder_backend == "hashing":
            encoder = HashingTextEncoder(settings.encoder_dimensions)
        elif settings.encoder_backend == "sentence-transformers":
            encoder = SentenceTransformerEncoder(
                settings.encoder_model,
                settings.encoder_dimensions,
                settings.encoder_batch_size,
            )
        else:
            raise ValueError(f"Unsupported encoder backend: {settings.encoder_backend}")
    recommender = RecommendationService(
        store,
        encoder,
        retrieval_candidates=settings.retrieval_candidates,
        max_tracks_per_artist=settings.max_tracks_per_artist,
    )
    scan_service = ScanService(
        store,
        CatalogProviderRouter(),
        encoder,
        batch_size=settings.encoder_batch_size,
    )
    return Services(
        settings=settings,
        store=store,
        encoder=encoder,
        recommender=recommender,
        scan_service=scan_service,
        jobs=JobManager(store, scan_service),
    )
