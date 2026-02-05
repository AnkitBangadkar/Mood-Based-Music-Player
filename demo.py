import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_test(mood_prompt):
    print(f"\n--- Mood Prompt: '{mood_prompt}' ---")
    try:
        response = requests.post(f"{BASE_URL}/generate", json={"prompt": mood_prompt, "limit": 5})
        if response.status_code == 200:
            songs = response.json()
            for i, song in enumerate(songs, 1):
                # Simple confidence bar
                score = song['score']
                bar = "#" * int(score * 20)
                print(f"{i}. [{score:.2f}] {song['title']} by {song['artist']} ({song['album']})")
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    print("Running Live Mood Generation Tests...\n")
    
    prompts = [
        "High energy cyberpunk action combat",
        "Very sad and emotional slow song",
        "Cute and happy upbeat pop"
    ]
    
    for p in prompts:
        run_test(p)
