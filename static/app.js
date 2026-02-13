document.addEventListener("DOMContentLoaded", () => {
    // State
    let queue = [];
    let currentIndex = 0;
    let isPlaying = false;
    let isShuffling = false;
    let isRepeating = false;
    let scanInterval = null;

    // DOM Elements
    const audioPlayer = document.getElementById("audio-player");
    const playPauseBtn = document.getElementById("play-pause-btn");
    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");
    const shuffleBtn = document.getElementById("shuffle-btn");
    const repeatBtn = document.getElementById("repeat-btn");
    const progressBar = document.getElementById("progress-bar");
    const currentTimeEl = document.getElementById("current-time");
    const durationEl = document.getElementById("duration");
    const volumeSlider = document.getElementById("volume-slider");
    
    const npTitle = document.getElementById("np-title");
    const npArtist = document.getElementById("np-artist");

    const promptInput = document.getElementById("prompt-input");
    const generateBtn = document.getElementById("generate-btn");
    const songListEl = document.getElementById("song-list");

    const scanBtn = document.getElementById("scan-btn");
    const scanModal = document.getElementById("scan-modal");
    const scanPathInput = document.getElementById("scan-path-input");
    const confirmScanBtn = document.getElementById("confirm-scan-btn");
    const cancelScanBtn = document.getElementById("cancel-scan-btn");
    const scanStatusEl = document.getElementById("scan-status");

    // --- Audio Player Logic ---

    function loadSong(index) {
        if (index < 0 || index >= queue.length) return;
        
        currentIndex = index;
        const song = queue[currentIndex];
        
        // Update Audio Source
        audioPlayer.src = `/audio/${song.id}`;
        audioPlayer.load();

        // Update UI
        npTitle.innerText = song.title;
        npArtist.innerText = song.artist;
        
        // Update Active Class in List
        document.querySelectorAll(".song-item").forEach((el, i) => {
            el.classList.toggle("active", i === currentIndex);
        });

        // Play
        playSong();
    }

    function playSong() {
        audioPlayer.play().then(() => {
            isPlaying = true;
            playPauseBtn.innerText = "⏸"; // Pause icon
        }).catch(err => console.error("Play error:", err));
    }

    function pauseSong() {
        audioPlayer.pause();
        isPlaying = false;
        playPauseBtn.innerText = "▶"; // Play icon
    }

    function togglePlay() {
        if (isPlaying) pauseSong();
        else playSong();
    }

    function nextSong() {
        if (queue.length === 0) return;
        let nextIndex = currentIndex + 1;
        if (nextIndex >= queue.length) {
            nextIndex = 0; // Loop back to start
        }
        loadSong(nextIndex);
    }

    function prevSong() {
        if (queue.length === 0) return;
        let prevIndex = currentIndex - 1;
        if (prevIndex < 0) {
            prevIndex = queue.length - 1; // Loop to end
        }
        loadSong(prevIndex);
    }

    // --- Event Listeners: Audio ---

    audioPlayer.addEventListener("timeupdate", () => {
        const { currentTime, duration } = audioPlayer;
        if (isNaN(duration)) return;
        
        const progress = (currentTime / duration) * 100;
        progressBar.value = progress;
        
        // Update Time Display
        currentTimeEl.innerText = formatTime(currentTime);
        durationEl.innerText = formatTime(duration);
    });

    audioPlayer.addEventListener("ended", () => {
        if (isRepeating) {
            playSong();
        } else {
            nextSong();
        }
    });

    // Seek
    progressBar.addEventListener("input", (e) => {
        const seekTime = (audioPlayer.duration / 100) * e.target.value;
        audioPlayer.currentTime = seekTime;
    });

    // Volume
    volumeSlider.addEventListener("input", (e) => {
        audioPlayer.volume = e.target.value;
    });

    // Controls
    playPauseBtn.addEventListener("click", togglePlay);
    nextBtn.addEventListener("click", nextSong);
    prevBtn.addEventListener("click", prevSong);
    
    shuffleBtn.addEventListener("click", () => {
        isShuffling = !isShuffling;
        shuffleBtn.classList.toggle("active", isShuffling);
        if (isShuffling) {
            // Fisher-Yates Shuffle
            for (let i = queue.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [queue[i], queue[j]] = [queue[j], queue[i]];
            }
            renderSongList();
            currentIndex = 0; // Reset index to top of shuffled list
            loadSong(0);
        }
    });

    repeatBtn.addEventListener("click", () => {
        isRepeating = !isRepeating;
        repeatBtn.innerText = isRepeating ? "🔂" : "🔁";
        repeatBtn.classList.toggle("active", isRepeating);
    });

    // --- Playlist Generation ---

    generateBtn.addEventListener("click", async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        generateBtn.disabled = true;
        generateBtn.innerText = "Generating...";
        songListEl.innerHTML = '<div style="text-align:center; padding: 2rem;">Searching specifically for "' + prompt + '"...</div>';

        try {
            const res = await fetch("/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: prompt, limit: 20 })
            });
            
            if (!res.ok) throw new Error("Generation failed");
            
            const songs = await res.json();
            queue = songs; // Replace queue with new results
            currentIndex = 0;
            renderSongList();
            
            if (queue.length > 0) {
                // Don't auto-play, just load first song
                loadSong(0);
                pauseSong(); 
            } else {
                songListEl.innerHTML = '<div style="text-align:center; padding: 2rem;">No songs found matching that mood.</div>';
            }

        } catch (err) {
            console.error(err);
            songListEl.innerHTML = `<div style="text-align:center; padding: 2rem; color:red;">Error: ${err.message}</div>`;
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerText = "Generate Playlist";
        }
    });

    function renderSongList() {
        songListEl.innerHTML = "";
        queue.forEach((song, index) => {
            const div = document.createElement("div");
            div.className = `song-item ${index === currentIndex ? 'active' : ''}`;
            div.innerHTML = `
                <span class="index">${index + 1}</span>
                <span class="title" title="${song.title}">${song.title}</span>
                <span class="artist" title="${song.artist}">${song.artist}</span>
                <span class="bpm">${song.bpm ? song.bpm.toFixed(0) : '-'}</span>
                <span class="score">${(song.score * 100).toFixed(0)}%</span>
                <span class="duration">Play</span> 
            `;
            div.addEventListener("click", () => loadSong(index));
            songListEl.appendChild(div);
        });
    }

    // --- Scanning Logic ---

    scanBtn.addEventListener("click", () => {
        scanModal.classList.remove("hidden");
        // Poll status immediately to see if one is running
        checkScanStatus();
    });

    cancelScanBtn.addEventListener("click", () => {
        scanModal.classList.add("hidden");
        if (scanInterval) clearInterval(scanInterval);
    });

    confirmScanBtn.addEventListener("click", async () => {
        const path = scanPathInput.value.trim();
        if (!path) return;

        confirmScanBtn.disabled = true;
        scanStatusEl.innerText = "Starting scan...";

        try {
            const res = await fetch("/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    path: path, 
                    enable_audio: true, 
                    enable_lyrics: true 
                })
            });
            
            if (res.ok) {
                startPollingScan();
            } else {
                const err = await res.json();
                scanStatusEl.innerText = "Error: " + err.detail;
                confirmScanBtn.disabled = false;
            }
        } catch (err) {
            scanStatusEl.innerText = "Network Error";
            confirmScanBtn.disabled = false;
        }
    });

    function startPollingScan() {
        if (scanInterval) clearInterval(scanInterval);
        scanInterval = setInterval(checkScanStatus, 2000);
    }

    async function checkScanStatus() {
        try {
            const res = await fetch("/scan/status");
            const status = await res.json();
            
            if (status.is_scanning) {
                scanStatusEl.innerText = `Scanning... Indexed: ${status.indexed_songs} songs.`;
                confirmScanBtn.disabled = true;
            } else {
                if (scanInterval) {
                    clearInterval(scanInterval);
                    scanInterval = null;
                }
                scanStatusEl.innerText = `Scan Complete! Total songs: ${status.indexed_songs}`;
                confirmScanBtn.disabled = false;
            }
        } catch (err) {
            console.error("Poll error", err);
        }
    }

    // --- Helpers ---

    function formatTime(seconds) {
        const min = Math.floor(seconds / 60);
        const sec = Math.floor(seconds % 60);
        return `${min}:${sec < 10 ? '0' : ''}${sec}`;
    }
});
