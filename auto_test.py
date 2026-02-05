import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"
TEST_PATH = os.path.abspath("songs_testing")

def run_test():
    # 1. Trigger Scan
    print(f"--- 1. Starting Scan for {TEST_PATH} ---")
    try:
        requests.post(f"{BASE_URL}/scan", json={
            "path": TEST_PATH, 
            "enable_audio": True, 
            "enable_lyrics": True, 
            "enable_online_lyrics": True
        })
    except Exception as e:
        print(f"Failed to trigger scan: {e}")
        return

    # 2. Wait for completion
    print("--- 2. Waiting for Scan... ---")
    prev_count = -1
    for _ in range(60): # Wait up to 60 seconds (scan takes ~30s)
        try:
            time.sleep(2)
            res = requests.get(f"{BASE_URL}/songs")
            if res.status_code == 200:
                songs = res.json()
                count = len(songs)
                print(f"Indexed songs: {count}/30")
                if count >= 30:
                    print("Scan complete!")
                    break
                if count == prev_count and count > 0:
                    # If count stuck for 10s, maybe it's done? No, server is async.
                    pass
                prev_count = count
        except:
            pass
            
    # 3. Generate Playlist
    print("\n--- 3. Generating Playlist: 'Happy upbeat and joyful' ---")
    try:
        response = requests.post(f"{BASE_URL}/generate", json={"prompt": "Happy upbeat and joyful", "limit": 10})
        if response.status_code == 200:
            songs = response.json()
            print("-" * 110)
            print(f"{'#':<3} | {'Score':<5} | {'BPM':<5} | {'Lyr?':<4} | {'Title':<30} | {'Artist'}")
            print("-" * 110)
            for i, song in enumerate(songs, 1):
                score = song['score']
                title = (song['title'][:28] + '..') if len(song['title']) > 28 else song['title']
                artist = (song['artist'][:25] + '..') if len(song['artist']) > 25 else song['artist']
                bpm = f"{song.get('bpm', 0):.1f}"
                has_lyrics = "Yes" if song.get('has_lyrics') else "No"
                print(f"{i:<3} | {score:.2f} | {bpm:<5} | {has_lyrics:<4} | {title:<30} | {artist}")
            print("-" * 110)
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    # Wait for server startup
    time.sleep(5) 
    run_test()
