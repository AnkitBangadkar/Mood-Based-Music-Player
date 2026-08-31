import time
from pathlib import Path

from conftest import make_wav
from fastapi.testclient import TestClient

from soulseek.api import create_app
from soulseek.encoders import HashingTextEncoder
from soulseek.services import build_services


def test_scan_generate_feedback_and_range_playback(settings, tmp_path: Path):
    music = tmp_path / "music"
    make_wav(music / "Rainy Evening Drive.wav")
    make_wav(music / "Quiet Night Road.wav")
    services = build_services(settings, HashingTextEncoder(settings.encoder_dimensions))
    app = create_app(settings, services)

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["encoder_id"].startswith("hashing-v1")
        assert health.headers["x-request-id"]

        accepted = client.post("/api/v1/library/scans", json={"root": str(music)})
        assert accepted.status_code == 202
        status_url = accepted.json()["status_url"]
        for _ in range(100):
            job = client.get(status_url).json()
            if job["status"] in {"succeeded", "failed"}:
                break
            time.sleep(0.01)
        assert job["status"] == "succeeded", job
        assert job["result"]["added"] == 2

        library = client.get("/api/v1/tracks").json()
        assert library["total"] == 2
        track_id = library["items"][0]["id"]
        assert "path" not in library["items"][0]

        playlist = client.post(
            "/api/v1/playlists", json={"prompt": "rainy evening drive", "size": 2}
        )
        assert playlist.status_code == 200
        body = playlist.json()
        assert len(body["tracks"]) == 2
        assert body["intent"]["desired_text"] == "rainy evening drive"

        feedback = client.post(
            "/api/v1/feedback",
            json={
                "playlist_id": body["playlist_id"],
                "track_id": body["tracks"][0]["id"],
                "value": "like",
            },
        )
        assert feedback.status_code == 202

        audio = client.get(f"/api/v1/tracks/{track_id}/audio", headers={"Range": "bytes=0-15"})
        assert audio.status_code == 206
        assert len(audio.content) == 16
        assert audio.headers["content-range"].startswith("bytes 0-15/")


def test_errors_have_stable_shape(settings):
    services = build_services(settings, HashingTextEncoder(settings.encoder_dimensions))
    with TestClient(create_app(settings, services)) as client:
        response = client.post("/api/v1/playlists", json={"prompt": "x", "size": 2})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
        assert response.json()["error"]["request_id"]
