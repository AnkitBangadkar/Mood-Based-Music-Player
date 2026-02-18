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
    
    // Main page scan progress panel elements
    const scanProgressPanel = document.getElementById("scan-progress-panel");
    const scanPanelTitle = document.getElementById("scan-panel-title");
    const scanPanelStage = document.getElementById("scan-panel-stage");
    const scanPanelElapsed = document.getElementById("scan-panel-elapsed");
    const scanPanelEta = document.getElementById("scan-panel-eta");
    const scanPanelProgressFill = document.getElementById("scan-panel-progress-fill");
    const scanPanelCurrent = document.getElementById("scan-panel-current");
    const scanPanelTotal = document.getElementById("scan-panel-total");
    const scanPanelPercent = document.getElementById("scan-panel-percent");
    const scanPanelFile = document.getElementById("scan-panel-file");
    const scanCloseBtn = document.getElementById("scan-close-btn");
    const scanCompleteActions = document.getElementById("scan-complete-actions");
    const dismissCompleteBtn = document.getElementById("dismiss-complete-btn");
    
    // Library menu elements
    const libraryBtn = document.getElementById("library-btn");
    const libraryBtnText = document.getElementById("library-btn-text");
    const libraryProgress = document.getElementById("library-progress");
    const libraryDropdown = document.getElementById("library-dropdown");
    const libraryStats = document.getElementById("library-stats");
    const libraryLastScan = document.getElementById("library-last-scan");
    const showProgressBtn = document.getElementById("show-progress-btn");
    const flushLibraryBtn = document.getElementById("flush-library-btn");
    
    // Flush modal elements
    const flushModal = document.getElementById("flush-modal");
    const cancelFlushBtn = document.getElementById("cancel-flush-btn");
    const confirmFlushBtn = document.getElementById("confirm-flush-btn");
    
    // State management
    let isScanMinimized = false;
    let lastScanStats = JSON.parse(localStorage.getItem('lastScanStats') || '{}');

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
                    indexSpan.innerHTML = '<i data-lucide="pause" class="paused-indicator"></i>';
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
            
            // Check if top match is low quality
            const topScore = songs.length > 0 ? songs[0].score : 0;
            const hasLowConfidence = topScore !== null && topScore < 35;
            
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
                
                // Add low confidence warning if needed
                if (hasLowConfidence) {
                    const warningDiv = document.createElement("div");
                    warningDiv.className = "low-confidence-warning";
                    warningDiv.innerHTML = `
                        <i data-lucide="alert-triangle"></i>
                        <div>
                            <strong>Low match confidence</strong>
                            <p>Your library may not have songs matching "${prompt}". The best match scored only ${topScore.toFixed(0)}%.</p>
                        </div>
                    `;
                    songListEl.insertBefore(warningDiv, songListEl.firstChild);
                }
                
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
                <span class="score ${song.match_quality || ''}" title="Semantic similarity: ${song.semantic_score ? song.semantic_score.toFixed(0) + '%' : 'N/A'}">${song.score ? song.score.toFixed(0) + '%' : '-'}</span>
                <span class="duration">${formatTime(song.duration)}</span>
            `;
            div.addEventListener("click", () => loadSong(index));
            songListEl.appendChild(div);
        });
        lucide.createIcons();
    }

    // --- Library Management ---

    function updateLibraryButton() {
        // Update library button text based on state
        const songCount = lastScanStats.songCount || 0;
        const elapsed = lastScanStats.elapsed;
        
        if (songCount > 0 && elapsed) {
            libraryBtnText.innerText = `${songCount} songs`;
        } else if (songCount > 0) {
            libraryBtnText.innerText = `${songCount} songs`;
        } else {
            libraryBtnText.innerText = 'Library';
        }
        
        // Update dropdown stats with elapsed time
        if (songCount > 0) {
            let statsText = `${songCount} songs indexed`;
            if (lastScanStats.elapsed) {
                statsText += ` • ${formatDuration(lastScanStats.elapsed)}`;
            }
            libraryStats.innerText = statsText;
        } else {
            libraryStats.innerText = 'No songs indexed';
        }
        
        // Update last scan time
        if (lastScanStats.timestamp) {
            const date = new Date(lastScanStats.timestamp);
            libraryLastScan.innerText = 'Last scan: ' + date.toLocaleString();
        } else {
            libraryLastScan.innerText = 'Last scan: Never';
        }
        
        lucide.createIcons();
    }

    function toggleLibraryDropdown() {
        libraryDropdown.classList.toggle("hidden");
        lucide.createIcons();
    }

    function hideLibraryDropdown() {
        libraryDropdown.classList.add("hidden");
    }

    libraryBtn.addEventListener("click", () => {
        if (isScanMinimized) {
            // Restore progress panel
            scanProgressPanel.classList.remove("hidden");
            isScanMinimized = false;
            libraryProgress.classList.add("hidden");
        } else {
            // Toggle dropdown
            toggleLibraryDropdown();
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
        if (!libraryBtn.contains(e.target) && !libraryDropdown.contains(e.target)) {
            hideLibraryDropdown();
        }
    });

    showProgressBtn.addEventListener("click", () => {
        hideLibraryDropdown();
        const savedStats = JSON.parse(localStorage.getItem('lastScanStats') || '{}');
        if (savedStats.elapsed && savedStats.songCount) {
            showCompletedScanPanel(savedStats);
        } else {
            scanProgressPanel.classList.remove("hidden");
            isScanMinimized = false;
            libraryProgress.classList.add("hidden");
        }
    });

    // Flush library handlers
    flushLibraryBtn.addEventListener("click", () => {
        hideLibraryDropdown();
        flushModal.classList.remove("hidden");
        flushModal.classList.add("visible");
        lucide.createIcons();
    });

    cancelFlushBtn.addEventListener("click", () => {
        flushModal.classList.add("hidden");
        flushModal.classList.remove("visible");
    });

    confirmFlushBtn.addEventListener("click", async () => {
        confirmFlushBtn.disabled = true;
        confirmFlushBtn.innerHTML = '<i data-lucide="loader-2" class="loading"></i> Flushing...';
        lucide.createIcons();

        try {
            const res = await fetch("/library/flush", { method: "POST" });
            if (res.ok) {
                // Clear local storage
                lastScanStats = {};
                localStorage.removeItem('lastScanStats');
                updateLibraryButton();
                
                // Clear song list
                queue = [];
                renderSongList();
                songListEl.innerHTML = '<div class="empty-state"><i data-lucide="music-2"></i><p>Library cleared. Scan to add songs.</p></div>';
                lucide.createIcons();
                
                confirmFlushBtn.innerHTML = '<i data-lucide="check"></i> Flushed!';
                lucide.createIcons();
                setTimeout(() => {
                    flushModal.classList.add("hidden");
                    flushModal.classList.remove("visible");
                    confirmFlushBtn.disabled = false;
                    confirmFlushBtn.innerHTML = '<i data-lucide="trash-2"></i> Yes, Flush Library';
                    lucide.createIcons();
                }, 1500);
            } else {
                throw new Error('Flush failed');
            }
        } catch (err) {
            confirmFlushBtn.innerHTML = '<i data-lucide="alert-circle"></i> Error';
            lucide.createIcons();
            setTimeout(() => {
                confirmFlushBtn.disabled = false;
                confirmFlushBtn.innerHTML = '<i data-lucide="trash-2"></i> Yes, Flush Library';
                lucide.createIcons();
            }, 2000);
        }
    });

    // --- Scanning Logic ---

    function showCompletedScanPanel(stats) {
        scanProgressPanel.classList.remove("hidden");
        isScanMinimized = false;
        libraryProgress.classList.add("hidden");
        
        scanPanelTitle.innerText = 'Scan Complete!';
        scanPanelStage.innerHTML = '<i data-lucide="check-circle"></i> Scan complete!';
        scanPanelProgressFill.style.width = '100%';
        scanPanelPercent.innerText = '100%';
        scanPanelPercent.className = 'scan-percent complete';
        scanPanelElapsed.innerText = formatDuration(stats.elapsed) + ' elapsed';
        scanPanelEta.innerText = 'Done in ' + formatDuration(stats.elapsed);
        scanPanelEta.className = 'scan-eta complete';
        scanPanelCurrent.innerText = `${stats.files || 0} / ${stats.files || 0} files`;
        scanPanelTotal.innerText = `${stats.songCount} songs indexed`;
        scanPanelFile.innerText = '';
        scanCompleteActions.classList.remove("hidden");
        
        lucide.createIcons();
    }

    function minimizeScanPanel() {
        scanProgressPanel.classList.add("hidden");
        isScanMinimized = true;
        const percent = scanPanelPercent.innerText;
        const isComplete = percent === '100%';
        
        if (isComplete) {
            const stats = JSON.parse(localStorage.getItem('lastScanStats') || '{}');
            if (stats.elapsed) {
                libraryProgress.innerText = formatDuration(stats.elapsed);
                libraryProgress.classList.remove("hidden");
            }
        } else if (percent !== '0%') {
            libraryProgress.innerText = percent;
            libraryProgress.classList.remove("hidden");
        }
    }

    function restoreScanPanel() {
        scanProgressPanel.classList.remove("hidden");
        isScanMinimized = false;
        libraryProgress.classList.add("hidden");
    }

    scanCloseBtn.addEventListener("click", () => {
        minimizeScanPanel();
    });

    dismissCompleteBtn.addEventListener("click", () => {
        scanProgressPanel.classList.add("hidden");
        isScanMinimized = false;
        scanCompleteActions.classList.add("hidden");
    });

    // Path History Management
    const PATH_HISTORY_KEY = 'scanPathHistory';
    const MAX_PATH_HISTORY = 5;
    
    function getPathHistory() {
        try {
            return JSON.parse(localStorage.getItem(PATH_HISTORY_KEY) || '[]');
        } catch {
            return [];
        }
    }
    
    function addPathToHistory(path) {
        if (!path) return;
        let history = getPathHistory();
        // Remove if already exists
        history = history.filter(p => p !== path);
        // Add to beginning
        history.unshift(path);
        // Keep only MAX_PATH_HISTORY items
        history = history.slice(0, MAX_PATH_HISTORY);
        localStorage.setItem(PATH_HISTORY_KEY, JSON.stringify(history));
    }
    
    function removePathFromHistory(path) {
        let history = getPathHistory();
        history = history.filter(p => p !== path);
        localStorage.setItem(PATH_HISTORY_KEY, JSON.stringify(history));
        renderPathHistory();
    }
    
    function clearPathHistory() {
        localStorage.removeItem(PATH_HISTORY_KEY);
        renderPathHistory();
    }
    
    // Path History UI Elements
    const pathHistoryBtn = document.getElementById("path-history-btn");
    const pathHistoryDropdown = document.getElementById("path-history-dropdown");
    const pathHistoryList = document.getElementById("path-history-list");
    const clearHistoryBtn = document.getElementById("clear-history-btn");
    
    function renderPathHistory() {
        const history = getPathHistory();
        if (history.length === 0) {
            pathHistoryList.innerHTML = '<div class="path-history-empty">No recent paths</div>';
            return;
        }
        
        pathHistoryList.innerHTML = history.map(path => `
            <div class="path-history-item" data-path="${path}">
                <i data-lucide="folder"></i>
                <span>${path}</span>
                <button class="remove-path" data-path="${path}" title="Remove from history">
                    <i data-lucide="x"></i>
                </button>
            </div>
        `).join('');
        
        lucide.createIcons();
        
        // Add click handlers
        pathHistoryList.querySelectorAll('.path-history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.remove-path')) return;
                const path = item.dataset.path;
                scanPathInput.value = path;
                pathHistoryDropdown.classList.add('hidden');
                pathHistoryBtn.classList.remove('active');
            });
        });
        
        pathHistoryList.querySelectorAll('.remove-path').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                removePathFromHistory(btn.dataset.path);
            });
        });
    }
    
    // Toggle path history dropdown
    if (pathHistoryBtn) {
        pathHistoryBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = pathHistoryDropdown.classList.contains('hidden');
            pathHistoryDropdown.classList.toggle('hidden', !isHidden);
            pathHistoryBtn.classList.toggle('active', isHidden);
            if (isHidden) renderPathHistory();
        });
    }
    
    // Clear history button
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', clearPathHistory);
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.path-input-container')) {
            pathHistoryDropdown.classList.add('hidden');
            pathHistoryBtn.classList.remove('active');
        }
    });
    
    // Indexed Folders Loading
    async function loadIndexedFolders() {
        const foldersList = document.getElementById('indexed-folders-list');
        if (!foldersList) return;
        
        try {
            const res = await fetch("/scan/folders");
            const data = await res.json();
            
            if (data.folders && data.folders.length > 0) {
                foldersList.innerHTML = data.folders.map(folder => `
                    <div class="indexed-folder-item">
                        <i data-lucide="folder-check"></i>
                        <div class="indexed-folder-info">
                            <div class="indexed-folder-path">${folder.path}</div>
                            <div class="indexed-folder-meta">
                                ${folder.song_count} songs • Last scan: ${folder.last_scan_formatted}
                            </div>
                        </div>
                    </div>
                `).join('');
                lucide.createIcons();
            } else {
                foldersList.innerHTML = '<p class="no-folders">No folders indexed yet</p>';
            }
        } catch (err) {
            console.error("Failed to load indexed folders:", err);
            foldersList.innerHTML = '<p class="no-folders">Failed to load folders</p>';
        }
    }
    
    scanBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        console.log("Scan button clicked");
        scanModal.classList.remove("hidden");
        scanModal.classList.add("visible");
        scanPathInput.focus();
        renderPathHistory();
        loadIndexedFolders();
    });
    
    // Debug: ensure elements exist
    console.log("Scan button:", scanBtn);
    console.log("Scan modal:", scanModal);

    cancelScanBtn.addEventListener("click", () => {
        scanModal.classList.add("hidden");
        scanModal.classList.remove("visible");
    });

    confirmScanBtn.addEventListener("click", async () => {
        const path = scanPathInput.value.trim();
        if (!path) return;

        confirmScanBtn.disabled = true;
        confirmScanBtn.innerHTML = '<i data-lucide="loader-2" class="loading"></i> Starting...';
        lucide.createIcons();

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
                // Close modal and show progress on main page
                scanModal.classList.add("hidden");
                scanModal.classList.remove("visible");
                scanProgressPanel.classList.remove("hidden");
                isScanMinimized = false;
                addPathToHistory(path); // Save to history
                scanPathInput.value = ''; // Clear input
                libraryProgress.classList.add("hidden");
                startPollingScan();
            } else {
                const err = await res.json();
                confirmScanBtn.innerHTML = '<i data-lucide="alert-circle"></i> Error';
                lucide.createIcons();
                setTimeout(() => {
                    confirmScanBtn.disabled = false;
                    confirmScanBtn.innerHTML = '<i data-lucide="search"></i> Start Scan';
                    lucide.createIcons();
                }, 2000);
            }
        } catch (err) {
            confirmScanBtn.innerHTML = '<i data-lucide="alert-circle"></i> Network Error';
            lucide.createIcons();
            setTimeout(() => {
                confirmScanBtn.disabled = false;
                confirmScanBtn.innerHTML = '<i data-lucide="search"></i> Start Scan';
                lucide.createIcons();
            }, 2000);
        }
    });

    // Allow Enter key to start scan
    scanPathInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            confirmScanBtn.click();
        }
    });

    function startPollingScan() {
        if (scanInterval) clearInterval(scanInterval);
        scanInterval = setInterval(checkScanStatus, 1000);
    }

    function formatDuration(seconds) {
        if (!seconds || seconds < 0) return '--:--';
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        if (hours > 0) {
            return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    async function checkScanStatus() {
        try {
            const res = await fetch("/scan/status");
            const status = await res.json();
            
            // Show panel if not minimized and scan is active
            if ((status.is_scanning || status.stage !== 'idle') && !isScanMinimized) {
                scanProgressPanel.classList.remove("hidden");
            }
            
            // Update stage with icon
            const stageConfig = {
                'scanning': { text: 'Scanning files', icon: 'folder-search' },
                'embedding': { text: 'Building embeddings', icon: 'brain' },
                'clap': { text: 'Computing audio features', icon: 'music' },
                'complete': { text: 'Scan complete!', icon: 'check-circle' },
                'idle': { text: 'Ready', icon: 'check' }
            };
            const stageInfo = stageConfig[status.stage] || { text: status.stage, icon: 'loader' };
            scanPanelStage.innerHTML = `<i data-lucide="${stageInfo.icon}"></i> ${stageInfo.text}`;
            
            // Update progress bar
            const percent = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;
            scanPanelProgressFill.style.width = percent + '%';
            scanPanelPercent.innerText = percent + '%';
            scanPanelPercent.className = 'scan-percent' + (percent >= 100 ? ' complete' : '');
            
            // Update minimized progress indicator
            if (isScanMinimized && percent > 0) {
                libraryProgress.innerText = percent + '%';
                libraryProgress.classList.remove("hidden");
            }
            
            // Update current file
            scanPanelFile.innerText = status.current_file || '';
            
            // Update counts
            scanPanelCurrent.innerText = `${status.current} / ${status.total} files`;
            scanPanelTotal.innerText = `${status.indexed_songs} songs indexed`;
            
            // Update timer and ETA
            scanPanelElapsed.innerText = formatDuration(status.elapsed_seconds) + ' elapsed';
            
            if (status.eta_seconds !== undefined && status.eta_seconds !== null && status.is_scanning) {
                scanPanelEta.innerText = 'ETA: ' + formatDuration(status.eta_seconds);
                scanPanelEta.className = 'scan-eta';
                scanPanelTitle.innerText = 'Scanning Library';
                scanCompleteActions.classList.add("hidden");
            } else if (!status.is_scanning && status.stage === 'complete') {
                scanPanelEta.innerText = 'Done in ' + formatDuration(status.elapsed_seconds);
                scanPanelEta.className = 'scan-eta complete';
                scanPanelTitle.innerText = 'Scan Complete!';
                scanCompleteActions.classList.remove("hidden");
                
                // Save scan stats
                lastScanStats = {
                    songCount: status.indexed_songs,
                    elapsed: status.elapsed_seconds,
                    files: status.total,
                    timestamp: Date.now()
                };
                localStorage.setItem('lastScanStats', JSON.stringify(lastScanStats));
                updateLibraryButton();
                
                // Auto-minimize after 3 seconds
                setTimeout(() => {
                    if (!isScanMinimized && status.stage === 'complete') {
                        minimizeScanPanel();
                    }
                }, 3000);
            } else if (status.is_scanning && status.current > 0) {
                scanPanelEta.innerText = 'ETA: calculating...';
                scanPanelEta.className = 'scan-eta';
                scanPanelTitle.innerText = 'Scanning Library';
                scanCompleteActions.classList.add("hidden");
            } else {
                scanPanelEta.innerText = 'ETA: --:--';
                scanPanelEta.className = 'scan-eta';
                scanCompleteActions.classList.add("hidden");
            }
            
            lucide.createIcons();
            
            if (!status.is_scanning) {
                if (scanInterval) {
                    clearInterval(scanInterval);
                    scanInterval = null;
                }
                confirmScanBtn.disabled = false;
            }
        } catch (err) {
            console.error("Poll error", err);
        }
    }

    // Initialize library button state
    updateLibraryButton();
    
    // Check for existing scan on page load
    checkScanStatus();

    // --- Helpers ---

    function formatTime(seconds) {
        const min = Math.floor(seconds / 60);
        const sec = Math.floor(seconds % 60);
        return `${min}:${sec < 10 ? '0' : ''}${sec}`;
    }
});
