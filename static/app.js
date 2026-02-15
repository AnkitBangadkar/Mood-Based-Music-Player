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
    const scanProgressEl = document.getElementById("scan-progress");
    const scanProgressBar = document.getElementById("scan-progress-bar");
    const scanStageEl = document.getElementById("scan-stage");
    const scanPercentEl = document.getElementById("scan-percent");
    const scanCurrentFileEl = document.getElementById("scan-current-file");
    const scanCountEl = document.getElementById("scan-count");
    const scanSongsTotalEl = document.getElementById("scan-songs-total");
    const scanTimerEl = document.getElementById("scan-timer");
    const scanEtaEl = document.getElementById("scan-eta");

    // --- Audio Player Logic ---

    function loadSong(index, autoPlay = true) {
        if (index < 0 || index >= queue.length) return;
        
        currentIndex = index;
        const song = queue[currentIndex];
        
        // Update Audio Source
        audioPlayer.src = `/audio/${song.id}`;
        audioPlayer.load();

        // Update UI - now playing info
        npTitle.innerText = song.title;
        npArtist.innerText = song.artist + (song.album ? ` • ${song.album}` : '');
        
        // Update Active Class in List
        document.querySelectorAll("#song-list .song-item").forEach((el, i) => {
            el.classList.toggle("active", i === currentIndex);
            el.classList.remove("playing"); // Remove playing class initially
        });
        
        // Update playing state in list
        updateSongListPlayingState();

        // Scroll to active song
        const activeItem = document.querySelector("#song-list .song-item.active");
        if (activeItem) {
            activeItem.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        // Only play if autoPlay is true
        if (autoPlay) {
            playSong();
        } else {
            // Still update icons to show paused state
            updatePlayPauseIcon();
            updateSongListPlayingState();
        }
    }

    function updatePlayPauseIcon() {
        const icon = playPauseBtn.querySelector('i');
        if (icon) {
            icon.setAttribute('data-lucide', isPlaying ? 'pause' : 'play');
            lucide.createIcons();
        }
    }

    function updateSongListPlayingState() {
        // Update all song items to show/hide playing indicator
        document.querySelectorAll("#song-list .song-item").forEach((el, i) => {
            const indexSpan = el.querySelector('.index');
            if (i === currentIndex) {
                if (isPlaying) {
                    indexSpan.innerHTML = '<i data-lucide="volume-2" class="playing-indicator"></i>';
                } else {
                    indexSpan.innerHTML = `<span>${i + 1}</span><i data-lucide="pause"></i>`;
                }
            } else {
                indexSpan.innerHTML = `<span>${i + 1}</span><i data-lucide="play"></i>`;
            }
        });
        lucide.createIcons();
    }

    function playSong() {
        audioPlayer.play().then(() => {
            isPlaying = true;
            // Add playing class to active song
            document.querySelectorAll("#song-list .song-item").forEach((el, i) => {
                el.classList.toggle("playing", i === currentIndex);
            });
            updatePlayPauseIcon();
            updateSongListPlayingState();
        }).catch(err => console.error("Play error:", err));
    }

    function pauseSong() {
        audioPlayer.pause();
        isPlaying = false;
        // Remove playing class from active song
        document.querySelectorAll("#song-list .song-item").forEach((el, i) => {
            el.classList.remove("playing");
        });
        updatePlayPauseIcon();
        updateSongListPlayingState();
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
        repeatBtn.classList.toggle("active", isRepeating);
    });

    // --- Playlist Generation ---

    // Enter key to generate
    promptInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            generateBtn.click();
        }
    });

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        // Don't trigger if typing in input
        if (e.target.tagName === "INPUT") return;
        
        switch(e.code) {
            case "Space":
                e.preventDefault();
                togglePlay();
                break;
            case "ArrowRight":
                nextSong();
                break;
            case "ArrowLeft":
                prevSong();
                break;
            case "KeyM":
                // Mute/unmute
                if (audioPlayer.volume > 0) {
                    audioPlayer.dataset.prevVolume = audioPlayer.volume;
                    audioPlayer.volume = 0;
                    volumeSlider.value = 0;
                } else {
                    audioPlayer.volume = audioPlayer.dataset.prevVolume || 0.8;
                    volumeSlider.value = audioPlayer.volume;
                }
                break;
        }
    });

    generateBtn.addEventListener("click", async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i data-lucide="loader-2" class="loading"></i> Generating...';
        lucide.createIcons();
        songListEl.innerHTML = '<div class="empty-state"><i data-lucide="loader-2" class="loading"></i><p>Searching for "' + prompt + '"...</p></div>';
        lucide.createIcons();

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
            
            // Calculate total duration
            const totalDuration = songs.reduce((acc, s) => acc + (s.duration || 0), 0);
            const totalMins = Math.floor(totalDuration / 60);
            
            renderSongList();
            
            // Add playlist stats header
            if (queue.length > 0) {
                const statsDiv = document.createElement("div");
                statsDiv.className = "playlist-stats";
                statsDiv.innerHTML = `
                    <span><i data-lucide="music"></i> ${queue.length} songs</span>
                    <span><i data-lucide="clock"></i> ${totalMins} min total</span>
                `;
                songListEl.insertBefore(statsDiv, songListEl.firstChild);
                lucide.createIcons();
                
                // Don't auto-play, just load first song
                loadSong(0, false);
                pauseSong(); 
            } else {
                songListEl.innerHTML = '<div class="empty-state"><i data-lucide="search-x"></i><p>No songs found matching that mood.</p></div>';
                lucide.createIcons();
            }

        } catch (err) {
            console.error(err);
            songListEl.innerHTML = `<div class="empty-state"><i data-lucide="alert-circle"></i><p>Error: ${err.message}</p></div>`;
            lucide.createIcons();
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i data-lucide="wand-2"></i> Generate Playlist';
            lucide.createIcons();
        }
    });

    function renderSongList() {
        songListEl.innerHTML = "";
        queue.forEach((song, index) => {
            const div = document.createElement("div");
            div.className = `song-item ${index === currentIndex ? 'active' : ''}`;
            
            // Arousal: 0-100 (calm to excited)
            const arousal = song.arousal !== undefined && song.arousal !== null ? Math.round(song.arousal * 100) : null;
            // Valence: -100 to +100 (sad to happy), normalize to 0-100 for display
            const valence = song.valence !== undefined && song.valence !== null ? Math.round((song.valence + 1) * 50) : null;
            
            // Determine mood label based on valence/arousal (2D circumplex model)
            let moodLabel = '-';
            if (valence !== null && arousal !== null) {
                // High arousal = top, Low arousal = bottom
                // High valence = right, Low valence = left
                if (valence > 60 && arousal > 60) moodLabel = 'Excited';
                else if (valence > 60 && arousal < 40) moodLabel = 'Content';
                else if (valence < 40 && arousal > 60) moodLabel = 'Angry';
                else if (valence < 40 && arousal < 40) moodLabel = 'Sad';
                else if (arousal > 70) moodLabel = 'Energetic';
                else if (valence > 70) moodLabel = 'Happy';
                else if (valence < 30) moodLabel = 'Depressed';
                else if (arousal < 30) moodLabel = 'Calm';
                else moodLabel = 'Neutral';
            }
            
            div.innerHTML = `
                <span class="index">
                    ${index === currentIndex && isPlaying 
                        ? `<i data-lucide="volume-2" class="playing-indicator"></i>` 
                        : `<span>${index + 1}</span><i data-lucide="play"></i>`}
                </span>
                <div class="title-col">
                    <span class="title" title="${song.title}">${song.title}</span>
                    <span class="artist" title="${song.artist}">${song.artist}</span>
                </div>
                <span class="album" title="${song.album}">${song.album || '-'}</span>
                <div class="mood-badges">
                    ${arousal !== null ? `<span class="mood-badge energy" title="Arousal: ${arousal}% (Calm ↔ Excited)"><i data-lucide="zap"></i>${arousal}%</span>` : '-'}
                </div>
                <div class="mood-badges">
                    ${valence !== null ? `<span class="mood-badge valence" title="Valence: ${valence}% (Sad ↔ Happy) - ${moodLabel}"><i data-lucide="heart"></i>${valence}%</span>` : '-'}
                </div>
                <span class="score">${song.score ? song.score.toFixed(0) + '%' : '-'}</span>
                <span class="duration">${formatTime(song.duration)}</span>
            `;
            div.addEventListener("click", () => loadSong(index));
            songListEl.appendChild(div);
        });
        lucide.createIcons();
    }

    // --- Scanning Logic ---

    scanBtn.addEventListener("click", () => {
        scanModal.classList.remove("hidden");
        scanModal.classList.add("visible");
        scanProgressEl.classList.add("hidden");
        scanProgressBar.style.width = '0%';
        // Poll status immediately to see if one is running
        checkScanStatus();
    });

    cancelScanBtn.addEventListener("click", () => {
        scanModal.classList.add("hidden");
        scanModal.classList.remove("visible");
        scanProgressEl.classList.add("hidden");
        scanProgressBar.style.width = '0%';
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

    function formatTime(seconds) {
        if (!seconds) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    async function checkScanStatus() {
        try {
            const res = await fetch("/scan/status");
            const status = await res.json();
            
            // Show/hide progress section
            if (status.is_scanning || status.stage !== 'idle') {
                scanProgressEl.classList.remove("hidden");
            }
            
            // Update stage
            const stageNames = {
                'scanning': 'Scanning files...',
                'embedding': 'Building embeddings...',
                'clap': 'Computing CLAP embeddings...',
                'complete': 'Complete!',
                'idle': 'Ready'
            };
            scanStageEl.innerText = stageNames[status.stage] || status.stage;
            scanStageEl.className = 'stage-' + status.stage;
            
            // Update progress bar
            const percent = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;
            scanProgressBar.style.width = percent + '%';
            scanPercentEl.innerText = percent + '%';
            
            // Update current file
            scanCurrentFileEl.innerText = status.current_file || '';
            
            // Update counts - show "new" vs "existing"
            const newFiles = status.current;
            const totalFiles = status.total;
            const existing = status.existing_songs || 0;
            scanCountEl.innerText = `${newFiles} / ${totalFiles} new files`;
            scanSongsTotalEl.innerText = `Total indexed: ${status.indexed_songs} (${existing} existing + ${newFiles} new)`;
            
            // Update timer and ETA
            if (status.elapsed_seconds !== undefined && status.elapsed_seconds !== null) {
                scanTimerEl.innerText = `${formatTime(status.elapsed_seconds)} elapsed`;
            } else {
                scanTimerEl.innerText = '--:-- elapsed';
            }
            
            if (status.eta_seconds !== undefined && status.eta_seconds !== null && status.is_scanning) {
                scanEtaEl.innerText = `ETA: ${formatTime(status.eta_seconds)}`;
            } else if (!status.is_scanning && status.stage === 'complete') {
                scanEtaEl.innerText = `Total time: ${formatTime(status.elapsed_seconds)}`;
            } else if (status.is_scanning && newFiles > 0) {
                scanEtaEl.innerText = 'ETA: calculating...';
            } else {
                scanEtaEl.innerText = 'ETA: --:--';
            }
            
            // Show basic status for compatibility
            if (status.is_scanning) {
                scanStatusEl.innerText = `Processing: ${status.current_file}`;
                confirmScanBtn.disabled = true;
            } else {
                if (scanInterval) {
                    clearInterval(scanInterval);
                    scanInterval = null;
                }
                scanStatusEl.innerText = `Scan Complete! Total songs: ${status.indexed_songs}`;
                scanProgressBar.style.width = '100%';
                scanPercentEl.innerText = '100%';
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
