from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from soulseek.domain import FloatVector, TrackMetadata

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 15000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            current = connection.execute("PRAGMA user_version").fetchone()[0]
            if current > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema {current} is newer than supported schema {SCHEMA_VERSION}"
                )
            if current == 0:
                self._migrate_v1(connection)
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @staticmethod
    def _migrate_v1(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE scan_roots (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                last_scanned_at TEXT
            );

            CREATE TABLE tracks (
                id TEXT PRIMARY KEY,
                root_id TEXT NOT NULL REFERENCES scan_roots(id) ON DELETE CASCADE,
                path TEXT NOT NULL UNIQUE,
                modified_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT NOT NULL DEFAULT '',
                genre TEXT NOT NULL DEFAULT '',
                year INTEGER,
                duration_seconds REAL,
                track_number INTEGER,
                disc_number INTEGER,
                searchable_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'missing')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX ix_tracks_artist ON tracks(artist);
            CREATE INDEX ix_tracks_root_status ON tracks(root_id, status);

            CREATE VIRTUAL TABLE tracks_fts USING fts5(
                track_id UNINDEXED,
                searchable_text,
                tokenize = 'unicode61 remove_diacritics 2'
            );

            CREATE TABLE track_embeddings (
                track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                encoder_id TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                vector BLOB NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(track_id, encoder_id)
            );
            CREATE INDEX ix_embeddings_encoder ON track_embeddings(encoder_id);

            CREATE TABLE jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('queued', 'running', 'succeeded', 'failed')),
                phase TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0,
                message TEXT NOT NULL DEFAULT '',
                result_json TEXT,
                error_json TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT
            );
            CREATE INDEX ix_jobs_status ON jobs(status);
            CREATE UNIQUE INDEX ux_jobs_active_kind ON jobs(kind)
              WHERE status IN ('queued', 'running');

            CREATE TABLE playlist_runs (
                id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                intent_json TEXT NOT NULL,
                encoder_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE playlist_items (
                run_id TEXT NOT NULL REFERENCES playlist_runs(id) ON DELETE CASCADE,
                track_id TEXT NOT NULL REFERENCES tracks(id),
                position INTEGER NOT NULL,
                score REAL NOT NULL,
                reasons_json TEXT NOT NULL,
                PRIMARY KEY(run_id, position),
                UNIQUE(run_id, track_id)
            );

            CREATE TABLE feedback (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES playlist_runs(id) ON DELETE CASCADE,
                track_id TEXT REFERENCES tracks(id),
                value TEXT NOT NULL CHECK(value IN ('like', 'dislike', 'skip')),
                created_at TEXT NOT NULL
            );
            """
        )

    def health(self) -> bool:
        with self.connect() as connection:
            return connection.execute("SELECT 1").fetchone()[0] == 1

    def library_stats(self) -> dict[str, int]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE status = 'active') AS track_count,
                  COUNT(*) FILTER (WHERE status = 'missing') AS missing_count,
                  COUNT(DISTINCT root_id) AS root_count
                FROM tracks
                """
            ).fetchone()
            return dict(row)

    def ensure_root(self, root: Path) -> str:
        normalized = str(root.resolve())
        root_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"soulseek-root:{normalized}"))
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO scan_roots(id, path, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(path) DO NOTHING
                """,
                (root_id, normalized, utc_now()),
            )
            row = connection.execute(
                "SELECT id FROM scan_roots WHERE path = ?", (normalized,)
            ).fetchone()
            return row["id"]

    def finish_root_scan(self, root_id: str, seen_paths: set[str]) -> int:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT path FROM tracks WHERE root_id = ? AND status = 'active'", (root_id,)
            ).fetchall()
            missing = [row["path"] for row in rows if row["path"] not in seen_paths]
            if missing:
                connection.executemany(
                    "UPDATE tracks SET status = 'missing', updated_at = ? WHERE path = ?",
                    [(utc_now(), path) for path in missing],
                )
            connection.execute(
                "UPDATE scan_roots SET last_scanned_at = ? WHERE id = ?", (utc_now(), root_id)
            )
            return len(missing)

    def upsert_track(self, root_id: str, metadata: TrackMetadata) -> tuple[str, str]:
        path = str(metadata.path.resolve())
        track_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"soulseek-track:{path}"))
        now = utc_now()
        values = (
            root_id,
            path,
            metadata.modified_ns,
            metadata.size_bytes,
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.genre,
            metadata.year,
            metadata.duration_seconds,
            metadata.track_number,
            metadata.disc_number,
            metadata.searchable_text,
            now,
        )
        with self.connect() as connection:
            existing = connection.execute(
                """
                SELECT id, modified_ns, size_bytes, searchable_text, status
                FROM tracks WHERE path = ?
                """,
                (path,),
            ).fetchone()
            if (
                existing
                and existing["modified_ns"] == metadata.modified_ns
                and existing["size_bytes"] == metadata.size_bytes
                and existing["searchable_text"] == metadata.searchable_text
                and existing["status"] == "active"
            ):
                return existing["id"], "unchanged"

            if existing:
                track_id = existing["id"]
                connection.execute(
                    """
                    UPDATE tracks SET root_id=?, modified_ns=?, size_bytes=?, title=?, artist=?,
                      album=?, genre=?, year=?, duration_seconds=?, track_number=?, disc_number=?,
                      searchable_text=?, status='active', updated_at=?
                    WHERE id=?
                    """,
                    (*values[:1], *values[2:], track_id),
                )
                action = "updated"
            else:
                connection.execute(
                    """
                    INSERT INTO tracks(
                      id, root_id, path, modified_ns, size_bytes, title, artist, album, genre,
                      year, duration_seconds, track_number, disc_number, searchable_text,
                      created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (track_id, *values[:-1], now, now),
                )
                action = "added"

            connection.execute("DELETE FROM tracks_fts WHERE track_id = ?", (track_id,))
            connection.execute(
                "INSERT INTO tracks_fts(track_id, searchable_text) VALUES (?, ?)",
                (track_id, metadata.searchable_text),
            )
            return track_id, action

    def upsert_embeddings(
        self,
        encoder_id: str,
        rows: Sequence[tuple[str, FloatVector]],
    ) -> None:
        now = utc_now()
        values = [
            (
                track_id,
                encoder_id,
                int(vector.shape[0]),
                np.asarray(vector, dtype=np.float32).tobytes(),
                now,
            )
            for track_id, vector in rows
        ]
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO track_embeddings(track_id, encoder_id, dimensions, vector, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(track_id, encoder_id) DO UPDATE SET
                  dimensions=excluded.dimensions,
                  vector=excluded.vector,
                  updated_at=excluded.updated_at
                """,
                values,
            )

    def retrieval_rows(self, encoder_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT t.id, t.title, t.artist, t.album, t.genre, t.year, t.duration_seconds,
                       t.searchable_text, e.dimensions, e.vector
                FROM tracks t
                JOIN track_embeddings e ON e.track_id = t.id
                WHERE t.status = 'active' AND e.encoder_id = ?
                """,
                (encoder_id,),
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["embedding"] = np.frombuffer(item.pop("vector"), dtype=np.float32).copy()
                result.append(item)
            return result

    def tracks_missing_embeddings(self, root_id: str, encoder_id: str) -> list[tuple[str, str]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT t.id, t.searchable_text
                FROM tracks t
                WHERE t.root_id = ? AND t.status = 'active'
                  AND NOT EXISTS (
                    SELECT 1 FROM track_embeddings e
                    WHERE e.track_id = t.id AND e.encoder_id = ?
                  )
                """,
                (root_id, encoder_id),
            ).fetchall()
            return [(row["id"], row["searchable_text"]) for row in rows]

    def get_track(self, track_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, artist, album, genre, year, duration_seconds, path
                FROM tracks WHERE id = ? AND status = 'active'
                """,
                (track_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_tracks(self, page: int, page_size: int, search: str | None) -> tuple[list[dict], int]:
        offset = (page - 1) * page_size
        where = "status = 'active'"
        params: list[Any] = []
        if search:
            where += (
                " AND (title LIKE ? ESCAPE '\\' OR artist LIKE ? ESCAPE '\\' "
                "OR album LIKE ? ESCAPE '\\')"
            )
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            needle = f"%{escaped}%"
            params.extend([needle, needle, needle])
        with self.connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) FROM tracks WHERE {where}", params
            ).fetchone()[0]
            rows = connection.execute(
                f"""
                SELECT id, title, artist, album, genre, year, duration_seconds
                FROM tracks WHERE {where}
                ORDER BY artist COLLATE NOCASE, album COLLATE NOCASE,
                         disc_number, track_number, title COLLATE NOCASE
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()
            return [dict(row) for row in rows], total

    def create_job(self, kind: str) -> str:
        job_id = str(uuid.uuid4())
        with self.connect() as connection:
            active = connection.execute(
                "SELECT id FROM jobs WHERE kind = ? AND status IN ('queued', 'running')", (kind,)
            ).fetchone()
            if active:
                raise ActiveJobError(active["id"])
            try:
                connection.execute(
                    """
                    INSERT INTO jobs(id, kind, status, phase, created_at)
                    VALUES (?, ?, 'queued', 'queued', ?)
                    """,
                    (job_id, kind, utc_now()),
                )
            except sqlite3.IntegrityError as error:
                active = connection.execute(
                    "SELECT id FROM jobs WHERE kind = ? AND status IN ('queued', 'running')",
                    (kind,),
                ).fetchone()
                if active:
                    raise ActiveJobError(active["id"]) from error
                raise
        return job_id

    def update_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        phase: str | None = None,
        progress: float | None = None,
        message: str | None = None,
        result: dict | None = None,
        error: dict | None = None,
    ) -> None:
        assignments: list[str] = []
        values: list[Any] = []
        for column, value in (
            ("status", status),
            ("phase", phase),
            ("progress", progress),
            ("message", message),
        ):
            if value is not None:
                assignments.append(f"{column} = ?")
                values.append(value)
        if result is not None:
            assignments.append("result_json = ?")
            values.append(json.dumps(result))
        if error is not None:
            assignments.append("error_json = ?")
            values.append(json.dumps(error))
        if status == "running":
            assignments.append("started_at = COALESCE(started_at, ?)")
            values.append(utc_now())
        if status in {"succeeded", "failed"}:
            assignments.append("finished_at = ?")
            values.append(utc_now())
        if not assignments:
            return
        values.append(job_id)
        with self.connect() as connection:
            connection.execute(f"UPDATE jobs SET {', '.join(assignments)} WHERE id = ?", values)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            result_json = item.pop("result_json")
            error_json = item.pop("error_json")
            item["result"] = json.loads(result_json) if result_json else None
            item["error"] = json.loads(error_json) if error_json else None
            return item

    def fail_interrupted_jobs(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE jobs SET status='failed', phase='interrupted', finished_at=?,
                  error_json=? WHERE status IN ('queued', 'running')
                """,
                (
                    utc_now(),
                    json.dumps({"code": "process_restarted", "message": "Backend restarted"}),
                ),
            )

    def save_playlist(
        self,
        prompt: str,
        intent: dict[str, Any],
        encoder_id: str,
        items: Sequence[dict[str, Any]],
    ) -> str:
        run_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO playlist_runs(id, prompt, intent_json, encoder_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, prompt, json.dumps(intent), encoder_id, utc_now()),
            )
            connection.executemany(
                """
                INSERT INTO playlist_items(run_id, track_id, position, score, reasons_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        item["track_id"],
                        item["position"],
                        item["score"],
                        json.dumps(item["reasons"]),
                    )
                    for item in items
                ],
            )
        return run_id

    def add_feedback(self, run_id: str, track_id: str | None, value: str) -> str:
        feedback_id = str(uuid.uuid4())
        with self.connect() as connection:
            run = connection.execute(
                "SELECT 1 FROM playlist_runs WHERE id = ?", (run_id,)
            ).fetchone()
            if not run:
                raise KeyError(run_id)
            if track_id:
                item = connection.execute(
                    "SELECT 1 FROM playlist_items WHERE run_id = ? AND track_id = ?",
                    (run_id, track_id),
                ).fetchone()
                if not item:
                    raise ValueError("track_id is not part of this playlist run")
            connection.execute(
                """
                INSERT INTO feedback(id, run_id, track_id, value, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (feedback_id, run_id, track_id, value, utc_now()),
            )
        return feedback_id


class ActiveJobError(RuntimeError):
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"A job is already active: {job_id}")
