# 🎵 Mood-Based Playlist Generator

A local-first, AI-powered music player that generates playlists based on your mood.

![Screenshot](https://via.placeholder.com/800x450?text=Mood+Playlist+Generator+UI)

## ✨ Features

- **Mood-Based Generation**: Describe your mood (e.g., "Sad songs for a rainy day", "High energy workout music") and get a perfect playlist.
- **Smart Analysis**: Analyzes your local music library for:
  - BPM (Tempo)
  - Energy & Danceability
  - Musical Key & Mode (Major/Minor)
  - Emotional Valence (Happy/Sad)
- **Lyrics Integration**: Fetches lyrics automatically and uses them for semantic search.
- **Privacy Focused**: Runs entirely locally. Your music data stays on your machine.
- **Modern Web Interface**: Clean, dark-themed UI with a built-in audio player.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- A folder with your music files (.mp3, .flac, .wav, .m4a)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AnkitBangadkar/Mood-Based-Music-Player.git
   cd Mood-Based-Music-Player
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This will install PyTorch and other ML libraries, which may take a few minutes.*

### Usage

1. **Start the server**
   ```bash
   python main.py
   ```

2. **Open the Web App**
   Open your browser and go to: `http://localhost:8000`

3. **Scan Your Library**
   - Click the **"Scan Library"** button in the top right.
   - Enter the **absolute path** to your music folder (e.g., `C:\Users\Name\Music` or `/home/user/Music`).
   - Click **"Start Scan"**. The first scan will take some time as it analyzes audio features and downloads lyrics.

4. **Generate Playlists**
   - Type a mood description in the search bar (e.g., "Calm instrumental for studying").
   - Click **"Generate Playlist"**.
   - Click any song to play it!

## 🛠️ Technology Stack

- **Backend**: FastAPI, Uvicorn, SQLite
- **AI/ML**: Sentence-Transformers (`all-mpnet-base-v2`), Librosa
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Audio Processing**: Mutagen, Librosa

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
