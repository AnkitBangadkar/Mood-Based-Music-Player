import requests
import json
import sys
import os

BASE_URL = "http://127.0.0.1:8000"

def check_server():
    try:
        requests.get(BASE_URL)
        return True
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the backend server.")
        print("   Please make sure you are running 'python main.py' in another terminal window.")
        return False

def scan_library():
    print("\n--- 📂 Scan Music Library ---")
    path = input("Enter the full path to your music folder: ").strip()
    
    # Remove quotes if user copied path as "C:\Path"
    path = path.replace('"', '').replace("'", "")
    
    if not os.path.exists(path):
        print(f"❌ Error: Path does not exist: {path}")
        return

    enable_audio = input("Enable Deep Audio Analysis? (Better results, but slower) [Y/n]: ").strip().lower() != 'n'
    enable_lyrics = input("Enable Lyrics Extraction? (From tags/files) [Y/n]: ").strip().lower() != 'n'
    enable_online = False
    
    if enable_lyrics:
        enable_online = input("Enable Online Lyrics Fetching? (Scrapes Genius.com if missing) [y/N]: ").strip().lower() == 'y'

    payload = {
        "path": path,
        "enable_audio": enable_audio,
        "enable_lyrics": enable_lyrics,
        "enable_online_lyrics": enable_online
    }

    print(f"Sending scan request for: {path}...")
    try:
        response = requests.post(f"{BASE_URL}/scan", json=payload)
        if response.status_code == 200:
            print(f"✅ Scan started successfully! (Audio: {enable_audio}, Lyrics: {enable_lyrics}, Online: {enable_online})")
            print("Check server logs for progress.")
        else:
            print(f"❌ Server Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def generate_playlist():
    print("\n--- 🎵 Generate Playlist ---")
    prompt = input("How are you feeling? (e.g., 'fast paced action', 'sad piano'): ").strip()
    
    if not prompt:
        return

    try:
        print(f"Thinking...")
        response = requests.post(f"{BASE_URL}/generate", json={"prompt": prompt, "limit": 10})
        
        if response.status_code == 200:
            songs = response.json()
            if not songs:
                print("⚠️  No matching songs found.")
            else:
                print(f"\n✨ Playlist for: '{prompt}'")
                print("-" * 110)
                print(f"{'#':<3} | {'Score':<5} | {'BPM':<5} | {'Lyr?':<4} | {'Title':<30} | {'Artist'}")
                print("-" * 110)
                for i, song in enumerate(songs, 1):
                    score = song['score']
                    title = (song['title'][:28] + '..') if len(song['title']) > 28 else song['title']
                    artist = (song['artist'][:25] + '..') if len(song['artist']) > 25 else song['artist']
                    bpm = song.get('bpm', '--')
                    has_lyrics = "Yes" if song.get('has_lyrics') else "No"
                    
                    print(f"{i:<3} | {score:.2f} | {bpm:<5} | {has_lyrics:<4} | {title:<30} | {artist}")
                print("-" * 110)
        else:
            print(f"❌ Server Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    print("\n🎛️  Mood Playlist CLI Controller")
    print("================================")
    
    if not check_server():
        return

    while True:
        print("\nOptions:")
        print("1. 📂 Scan a new music folder")
        print("2. 🎵 Generate a playlist")
        print("3. ❌ Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == '1':
            scan_library()
        elif choice == '2':
            generate_playlist()
        elif choice == '3':
            print("Bye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()