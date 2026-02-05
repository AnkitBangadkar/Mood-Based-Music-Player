# 🎵 Local Mood-Based Playlist Generator

## What is this?
This is a smart music system that lives entirely on your computer. Instead of clicking through genres or artists, you just tell it how you feel (e.g., *"I need high energy music for a boss fight"* or *"Sad vibes for a rainy day"*), and it builds a playlist for you instantly from your own local music library.

**Key Features:**
*   **100% Offline & Private:** No data leaves your PC.
*   **Fast:** Generates playlists in milliseconds.
*   **Smart:** It understands "moods", not just keywords, using Artificial Intelligence.

---

## 🚀 How It Works (The "Magic" Explained)

The system works in three simple steps:

### 1. The "Listen" Phase (Scanning)
When you point the system to your music folder, it doesn't just list the files. It reads the "DNA" of each song:
*   **Metadata:** Title, Artist, Album, Genre.
*   **AI Interpretation:** It converts this text into a mathematical fingerprint (called a **Vector Embedding**).
    *   *Think of it this way:* The system places every song on a giant 3D map. "Happy" songs cluster in one corner, "Sad" songs in another, "Heavy Metal" in a third.

### 2. The "Understanding" Phase (Prompting)
When you type *"High energy cyberpunk action"*, the system's brain (`all-MiniLM-L6-v2`) converts your sentence into coordinates on that same map.

### 3. The "Match" Phase (Generating)
It simply looks for the songs on the map that are closest to your prompt's coordinates.
*   If your prompt lands in the "Aggressive/Electronic" neighborhood, it grabs the nearest songs (like the *Cyberpunk 2077* soundtrack).

---

## 🧪 Live Test Results

We ran a test against your `songs_testing` folder (containing ~30 diverse tracks including Anime OSTs, Pop, and Rock). Here is what happened:

### Test 1: "High energy cyberpunk action combat"
> **Result:** It correctly identified the **Cyberpunk 2077** soundtrack.
1.  *Major Crimes* - Health
2.  *Delicate Weapon* - Grimes
3.  *Who's Ready for Tomorrow* - Rat Boy

### Test 2: "Very sad and emotional slow song"
> **Result:** It picked melancholic and slower tracks.
1.  *Little Dark Age* - MGMT (Known for its dark/gothic synth-pop vibe)
2.  *Clarity* - Zedd
3.  *Delicate Weapon* - Grimes

### Test 3: "Cute and happy upbeat pop"
> **Result:** It found City Pop and upbeat tracks.
1.  *Plastic Love* - Mariya Takeuchi
2.  *Clarity* - Zedd
3.  *Ponpon Shit* - Namakopuri (Very chaotic/cute pop)

---

## 🛠 Technical Under the Hood (For the Curious)

*   **Brain:** `Sentence-Transformers` (Python library). We use a "Mini" model that is super fast and lightweight, perfect for running on standard laptops without a dedicated graphics card.
*   **Engine:** `FastAPI` handles the requests, and `NumPy` does the math (Cosine Similarity) to find the matches.
*   **Database:** `SQLite` stores the song info so we don't have to re-scan every time.

## 🏁 How to Use It

1.  **Start the Server:**
    ```bash
    python main.py
    ```
3. **Using the API:**
   *   **Scan a Library:**
       (You only do this once or when you add new music)
       
       **PowerShell:**
       ```powershell
       Invoke-RestMethod -Uri "http://127.0.0.1:8000/scan" -Method Post -Body '{"path": "Z:/Code/pbl2/songs_testing"}' -ContentType "application/json"
       ```
       
       **CMD / Linux / Git Bash:**
       ```bash
       curl -X POST "http://127.0.0.1:8000/scan" -H "Content-Type: application/json" -d '{"path": "Z:/Code/pbl2/songs_testing"}'
       ```

   *   **Get a Playlist:**
       **PowerShell:**
       ```powershell
       Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" -Method Post -Body '{"prompt": "Epic orchestral music"}' -ContentType "application/json"
       ```
