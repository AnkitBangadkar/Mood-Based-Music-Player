import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_prompt(prompt):
    print(f"\n>>> TESTING PROMPT: '{prompt}'")
    print("-" * 120)
    print(f"{ 'Score':<6} | { 'BPM':<6} | { 'Energy':<8} | { 'Title':<40} | Analysis")
    print("-" * 120)
    
    response = requests.post(f"{BASE_URL}/generate", json={"prompt": prompt, "limit": 5})
    if response.status_code == 200:
        songs = response.json()
        for s in songs:
            bpm = f"{s.get('bpm', 0):.1f}"
            energy = f"{s.get('energy', 0):.3f}"
            title = s['title'][:38]
            # Fetch full metadata from DB to see the rich description for judging
            # We don't have an endpoint for that, but we can infer from the result.
            print(f"{s['score']:.2f}   | {bpm:<6} | {energy:<8} | {title:<40} | BPM matches mood?")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    prompts = [
        "Intense adrenaline high speed chase",
        "Cozy rainy day study vibes with acoustic instruments",
        "Depressing heartbreak and deep loneliness"
    ]
    for p in prompts:
        test_prompt(p)
