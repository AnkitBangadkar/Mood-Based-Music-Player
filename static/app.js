document.addEventListener('DOMContentLoaded', () => {
    // State
    let queue = [];
    let currentIndex = 0;
    let isPlaying = false;
    let isShuffling = false;
    let isRepeating = false;
    let scanInterval = null;
    let libraryStats = null;
    let currentBrowsePath = '/';
    let asyncLyrics = true;
    let allLibrarySongs = [];
    let libraryFilter = '';
    let librarySortBy = 'title';
    let selectedScanPath = '';
    let isStatusExpanded = false;
    let statusUpdateInterval = null;

    // DOM Elements
    const audioPlayer = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const shuffleBtn = document.getElementById('shuffle-btn');
    const repeatBtn = document.getElementById('repeat-btn');
    const progressBar = document.getElementById('progress-bar');
    const progressFill = document.getElementById('progress-fill');
    const volumeBar = document.getElementById('volume-bar');
    const volumeFill = document.getElementById('volume-fill');
    const currentTimeEl = document.getElementById('current-time');
    const durationEl = document.getElementById('duration');
    const playerTitle = document.getElementById('player-title');
    const playerArtist = document.getElementById('player-artist');
    const promptInput = document.getElementById('prompt-input');
    const generateBtn = document.getElementById('generate-btn');
    const heroState = document.getElementById('hero-state');
    const resultsSection = document.getElementById('results-section');
    const trackGrid = document.getElementById('track-grid');
    const resultsTitle = document.getElementById('results-title');
    const resultsCount = document.getElementById('results-count');
    const navLibraryCount = document.getElementById('nav-library-count');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const statusMeta = document.getElementById('status-meta');
    const statusCard = document.getElementById('status-card');
    const statusDetails = document.getElementById('status-details');
    const statusChevron = document.getElementById('status-chevron');
    const scanProgressSection = document.getElementById('scan-progress-section');
    const foldersSection = document.getElementById('folders-section');
    const scannedFoldersList = document.getElementById('scanned-folders-list');
    const audioProgressBar = document.getElementById('audio-progress-bar');
    const audioProgressText = document.getElementById('audio-progress-text');
    const audioTime = document.getElementById('audio-time');
    const lyricsProgressBar = document.getElementById('lyrics-progress-bar');
    const lyricsProgressText = document.getElementById('lyrics-progress-text');
    const lyricsTime = document.getElementById('lyrics-time');
    const navDiscover = document.getElementById('nav-discover');
    const navLibrary = document.getElementById('nav-library');
    const navScan = document.getElementById('nav-scan');
    const navSettings = document.getElementById('nav-settings');
    const heroScanBtn = document.getElementById('hero-scan-btn');
    const libraryView = document.getElementById('library-view');
    const libraryList = document.getElementById('library-list');
    const librarySearchInput = document.getElementById('library-search-input');
    const librarySort = document.getElementById('library-sort');
    const libraryTotalCount = document.getElementById('library-total-count');
    const scanModal = document.getElementById('scan-modal');
    const settingsModal = document.getElementById('settings-modal');
    const scanPathInput = document.getElementById('scan-path-input');
    const confirmScanBtn = document.getElementById('confirm-scan-btn');
    const cancelScanBtn = document.getElementById('cancel-scan-btn');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const nativeFolderPicker = document.getElementById('native-folder-picker');
    const browseFolderBtn = document.getElementById('browse-folder-btn');
    const selectedFolderPath = document.getElementById('selected-folder-path');
    const recentFoldersList = document.getElementById('recent-folders-list');
    const asyncToggle = document.getElementById('async-toggle');
    const flushAllBtn = document.getElementById('flush-all-btn');
    const flushClapBtn = document.getElementById('flush-clap-btn');
    const flushTextBtn = document.getElementById('flush-text-btn');

    function refreshIcons() {
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    function formatDuration(seconds) {
        if (!seconds) return '--:--';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        return `${m}:${s.toString().padStart(2,'0')}`;
    }

    function scoreClass(score) {
        if (!score) return 'unknown';
        if (score >= 60) return 'high';
        if (score >= 35) return 'medium';
        return 'low';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --- Library Stats ---

    async function fetchLibraryStats() {
        try {
            const res = await fetch('/library/stats');
            if (res.ok) {
                libraryStats = await res.json();
                updateStatus();
            }
        } catch (e) {
            console.error('Failed to fetch stats:', e);
        }
    }

    function updateStatus() {
        const count = libraryStats?.song_count || 0;
        navLibraryCount.textContent = count;

        if (count > 0) {
            statusDot.classList.remove('idle');
            statusDot.classList.add('active');
            statusText.textContent = 'Library Active';
            statusMeta.textContent = `${count} tracks indexed`;
            heroState.classList.add('hidden');
        } else {
            statusDot.classList.remove('active');
            statusDot.classList.add('idle');
            statusText.textContent = 'Ready';
            statusMeta.textContent = 'No tracks indexed';
            heroState.classList.remove('hidden');
            resultsSection.classList.add('hidden');
        }
    }

    // --- Status Card ---

    statusCard.addEventListener('click', () => {
        isStatusExpanded = !isStatusExpanded;
        statusCard.classList.toggle('expanded', isStatusExpanded);
        statusDetails.classList.toggle('hidden', !isStatusExpanded);

        if (isStatusExpanded) {
            loadStatusDetails();
            // Start polling for updates while expanded
            if (!statusUpdateInterval) {
                statusUpdateInterval = setInterval(loadStatusDetails, 1000);
            }
        } else {
            // Stop polling when collapsed
            if (statusUpdateInterval) {
                clearInterval(statusUpdateInterval);
                statusUpdateInterval = null;
            }
        }
    });

    async function loadStatusDetails() {
        try {
            const res = await fetch('/scan/progress');
            const data = await res.json();

            const isScanning = data.is_scanning || data.lyrics.is_running;

            if (isScanning) {
                // Show progress bars
                scanProgressSection.classList.remove('hidden');
                foldersSection.classList.add('hidden');

                // Update audio progress
                const audioPct = data.audio.total > 0 ? (data.audio.processed / data.audio.total) * 100 : 0;
                audioProgressBar.style.width = audioPct + '%';
                audioProgressText.textContent = `${data.audio.processed}/${data.audio.total}`;
                audioTime.textContent = data.audio.elapsed_seconds > 0 ?
                    formatDuration(data.audio.elapsed_seconds) : '--';

                // Update lyrics progress
                const lyricsPct = data.lyrics.total > 0 ? (data.lyrics.processed / data.lyrics.total) * 100 : 0;
                lyricsProgressBar.style.width = lyricsPct + '%';
                lyricsProgressText.textContent = `${data.lyrics.processed}/${data.lyrics.total} (${data.lyrics.found} found)`;
                lyricsTime.textContent = data.lyrics.elapsed_seconds > 0 ?
                    formatDuration(data.lyrics.elapsed_seconds) : '--';
            } else {
                // Show folders list
                scanProgressSection.classList.add('hidden');
                foldersSection.classList.remove('hidden');
                renderScannedFolders(data.folders);
            }
        } catch (e) {
            console.error('Failed to load status details:', e);
        }
    }

    function renderScannedFolders(folders) {
        if (!folders || folders.length === 0) {
            scannedFoldersList.innerHTML = '<div style="padding: 0.5rem; color: var(--text-dim); font-size: 0.75rem; font-style: italic;">No folders scanned</div>';
            return;
        }

        scannedFoldersList.innerHTML = folders.map(f => `
            <div class="scanned-folder-item">
                <i data-lucide="folder" style="width: 14px; height: 14px; color: var(--accent);"></i>
                <span class="folder-path-text">${escapeHtml(f.path)}</span>
                <span class="folder-count">${f.song_count}</span>
                <button class="remove-folder-btn" data-path="${escapeHtml(f.path)}" title="Remove folder and delete songs">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        `).join('');

        // Add remove handlers
        scannedFoldersList.querySelectorAll('.remove-folder-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const path = btn.dataset.path;
                if (confirm(`Delete all songs from ${path}?\n\nThis will remove the songs from your library.`)) {
                    try {
                        await fetch(`/library/flush`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ folder: path })
                        });
                        loadStatusDetails();
                        fetchLibraryStats();
                    } catch (err) {
                        console.error('Failed to remove folder:', err);
                    }
                }
            });
        });

        refreshIcons();
    }

    // --- Audio Player ---

    function loadSong(index, autoPlay = true) {
        if (index < 0 || index >= queue.length) return;
        currentIndex = index;
        const song = queue[currentIndex];
        
        audioPlayer.src = `/audio/${song.id}`;
        audioPlayer.load();
        
        playerTitle.textContent = song.title || 'Unknown';
        playerArtist.textContent = song.artist || 'Unknown';
        
        // Update active card
        document.querySelectorAll('.track-card').forEach((card, i) => {
            card.classList.toggle('active', i === currentIndex);
        });
        
        if (autoPlay) playSong();
        updatePlayButton();
    }

    function playSong() {
        audioPlayer.play().then(() => {
            isPlaying = true;
            updatePlayButton();
            updateVisualizerState();
        }).catch(console.error);
    }

    function pauseSong() {
        audioPlayer.pause();
        isPlaying = false;
        updatePlayButton();
        updateVisualizerState();
    }

    function updateVisualizerState() {
        const visualizerBars = document.getElementById('visualizer-bars');
        if (visualizerBars) {
            visualizerBars.classList.toggle('paused', !isPlaying);
        }
    }

    function togglePlay() {
        if (queue.length === 0) return;
        if (isPlaying) pauseSong();
        else playSong();
    }

    function updatePlayButton() {
        const icon = isPlaying ? 'pause' : 'play';
        const label = isPlaying ? 'Pause' : 'Play';
        playPauseBtn.innerHTML = `<i data-lucide="${icon}"></i>`;
        playPauseBtn.title = label;
        playPauseBtn.setAttribute('aria-label', label);
        refreshIcons();
    }

    function nextSong() {
        if (queue.length === 0) return;
        let next = currentIndex + 1;
        if (next >= queue.length) next = 0;
        loadSong(next);
    }

    function prevSong() {
        if (queue.length === 0) return;
        let prev = currentIndex - 1;
        if (prev < 0) prev = queue.length - 1;
        loadSong(prev);
    }

    // Player Events
    audioPlayer.addEventListener('timeupdate', () => {
        const pct = audioPlayer.duration ? (audioPlayer.currentTime / audioPlayer.duration) * 100 : 0;
        progressFill.style.width = pct + '%';
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
        durationEl.textContent = formatTime(audioPlayer.duration);
    });

    audioPlayer.addEventListener('ended', () => {
        if (isRepeating) playSong();
        else nextSong();
    });

    // Progress/Volume Drag
    let isDraggingProgress = false;
    let isDraggingVolume = false;

    progressBar.addEventListener('mousedown', (e) => {
        isDraggingProgress = true;
        updateProgress(e);
    });

    volumeBar.addEventListener('mousedown', (e) => {
        isDraggingVolume = true;
        updateVolume(e);
    });

    document.addEventListener('mousemove', (e) => {
        if (isDraggingProgress) updateProgress(e);
        if (isDraggingVolume) updateVolume(e);
    });

    document.addEventListener('mouseup', () => {
        isDraggingProgress = false;
        isDraggingVolume = false;
    });

    function updateProgress(e) {
        const rect = progressBar.getBoundingClientRect();
        const pct = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
        progressFill.style.width = pct + '%';
        if (audioPlayer.duration) {
            audioPlayer.currentTime = (pct / 100) * audioPlayer.duration;
        }
    }

    function updateVolume(e) {
        const rect = volumeBar.getBoundingClientRect();
        const pct = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
        volumeFill.style.width = pct + '%';
        audioPlayer.volume = pct / 100;
    }

    playPauseBtn.addEventListener('click', togglePlay);
    nextBtn.addEventListener('click', nextSong);
    prevBtn.addEventListener('click', prevSong);
    
    shuffleBtn.addEventListener('click', () => {
        isShuffling = !isShuffling;
        shuffleBtn.classList.toggle('active', isShuffling);
    });
    
    repeatBtn.addEventListener('click', () => {
        isRepeating = !isRepeating;
        repeatBtn.classList.toggle('active', isRepeating);
    });

    // Keyboard
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
        if (e.code === 'ArrowRight') nextSong();
        if (e.code === 'ArrowLeft') prevSong();
    });

    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') generateBtn.click();
    });

    // --- Generate Playlist ---

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i><span>Generating...</span>';
        statusDot.classList.add('processing');
        statusText.textContent = 'Analyzing...';
        refreshIcons();

        try {
            const res = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, limit: 20 })
            });

            if (!res.ok) throw new Error('Generation failed');
            
            queue = await res.json();
            currentIndex = 0;

            heroState.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            resultsTitle.textContent = `"${escapeHtml(prompt)}"`;
            resultsCount.textContent = `${queue.length} tracks`;

            renderTrackGrid();

            if (queue.length > 0) {
                loadSong(0, false);
                statusDot.classList.remove('processing');
                statusDot.classList.add('active');
                statusText.textContent = 'Library Active';
            }
        } catch (err) {
            console.error(err);
            statusText.textContent = 'Error';
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i data-lucide="zap"></i><span>Generate</span>';
            refreshIcons();
        }
    });

    function renderTrackGrid() {
        trackGrid.innerHTML = '';
        
        queue.forEach((song, index) => {
            const card = document.createElement('div');
            card.className = 'track-card';
            if (index === currentIndex) card.classList.add('active');
            
            const energy = song.energy !== null ? Math.round(song.energy * 100) : null;
            const valence = song.valence !== null ? Math.round((song.valence + 1) * 50) : null;
            const sc = scoreClass(song.score);
            
            card.innerHTML = `
                <div class="track-card-header">
                    <div class="track-number">${index + 1}</div>
                    <div class="track-info">
                        <div class="track-title">${escapeHtml(song.title || 'Unknown')}</div>
                        <div class="track-artist">${escapeHtml(song.artist || 'Unknown')}</div>
                    </div>
                    <div class="track-score score-${sc}">${song.score ? song.score.toFixed(0) + '%' : '--'}</div>
                </div>
                <div class="track-features">
                    ${energy !== null ? `
                        <div class="feature-mini">
                            <i data-lucide="zap"></i>
                            <span>Energy ${energy}%</span>
                        </div>
                    ` : ''}
                    ${valence !== null ? `
                        <div class="feature-mini">
                            <i data-lucide="heart"></i>
                            <span>Mood ${valence}%</span>
                        </div>
                    ` : ''}
                    <div class="feature-mini">
                        <i data-lucide="clock"></i>
                        <span>${formatTime(song.duration)}</span>
                    </div>
                </div>
            `;
            
            card.addEventListener('click', () => loadSong(index));
            trackGrid.appendChild(card);
        });
        
            refreshIcons();
    }

    // --- Library View ---

    function showView(viewName) {
        // Hide all views
        heroState.classList.add('hidden');
        resultsSection.classList.add('hidden');
        libraryView.classList.add('hidden');
        
        // Remove active from all nav items
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        
        // Show selected view
        switch(viewName) {
            case 'discover':
                navDiscover.classList.add('active');
                if (queue.length > 0) {
                    resultsSection.classList.remove('hidden');
                } else if (libraryStats && libraryStats.song_count > 0) {
                    heroState.classList.remove('hidden');
                } else {
                    heroState.classList.remove('hidden');
                }
                break;
            case 'library':
                navLibrary.classList.add('active');
                libraryView.classList.remove('hidden');
                loadLibrary();
                break;
        }
    }

    navDiscover.addEventListener('click', () => showView('discover'));
    navLibrary.addEventListener('click', () => showView('library'));

    async function loadLibrary() {
        try {
            const res = await fetch('/songs?limit=500');
            if (res.ok) {
                allLibrarySongs = await res.json();
                libraryTotalCount.textContent = `${allLibrarySongs.length} tracks`;
                renderLibrary();
            }
        } catch (e) {
            console.error('Failed to load library:', e);
        }
    }

    function renderLibrary() {
        let songs = [...allLibrarySongs];
        
        // Apply search filter
        if (libraryFilter) {
            const filter = libraryFilter.toLowerCase();
            songs = songs.filter(s => 
                (s.title || '').toLowerCase().includes(filter) ||
                (s.artist || '').toLowerCase().includes(filter) ||
                (s.album || '').toLowerCase().includes(filter)
            );
        }
        
        // Apply sort
        songs.sort((a, b) => {
            switch(librarySortBy) {
                case 'title':
                    return (a.title || '').localeCompare(b.title || '');
                case 'artist':
                    return (a.artist || '').localeCompare(b.artist || '');
                case 'album':
                    return (a.album || '').localeCompare(b.album || '');
                case 'recent':
                    return b.id - a.id; // Assuming higher ID = more recent
                default:
                    return 0;
            }
        });
        
        libraryList.innerHTML = '';
        
        if (songs.length === 0) {
            libraryList.innerHTML = '<div style="text-align: center; padding: 3rem; color: var(--text-muted);">No songs found</div>';
            return;
        }
        
        songs.forEach((song, index) => {
            const item = document.createElement('div');
            item.className = 'library-item';
            if (queue.length > 0 && queue[currentIndex] && queue[currentIndex].id === song.id) {
                item.classList.add('active');
            }
            
            const energy = song.energy !== null ? Math.round(song.energy * 100) : null;
            const valence = song.valence !== null ? Math.round((song.valence + 1) * 50) : null;
            
            item.innerHTML = `
                <div class="library-item-number">${index + 1}</div>
                <div class="library-item-info">
                    <div class="library-item-title">${escapeHtml(song.title || 'Unknown')}</div>
                    <div class="library-item-artist">${escapeHtml(song.artist || 'Unknown')}</div>
                </div>
                <div class="library-item-album">${escapeHtml(song.album || '')}</div>
                <div class="library-item-features">
                    ${energy !== null ? `
                        <div class="library-item-feature">
                            <i data-lucide="zap"></i>
                            <span>${energy}%</span>
                        </div>
                    ` : ''}
                    ${valence !== null ? `
                        <div class="library-item-feature">
                            <i data-lucide="heart"></i>
                            <span>${valence}%</span>
                        </div>
                    ` : ''}
                </div>
                <div class="library-item-duration">${formatTime(song.duration)}</div>
            `;
            
            item.addEventListener('click', () => {
                // Add to queue and play
                queue = [song];
                currentIndex = 0;
                loadSong(0);
                renderLibrary(); // Update active state
            });
            
            libraryList.appendChild(item);
        });
        
        refreshIcons();
    }

    // Library search
    librarySearchInput.addEventListener('input', (e) => {
        libraryFilter = e.target.value;
        renderLibrary();
    });

    // Library sort
    librarySort.addEventListener('change', (e) => {
        librarySortBy = e.target.value;
        renderLibrary();
    });

    // --- Modals ---

    navScan.addEventListener('click', () => {
        scanModal.classList.remove('hidden');
        scanModal.classList.add('visible');
        loadRecentFolders();
        scanPathInput.focus();
    });

    heroScanBtn.addEventListener('click', () => {
        scanModal.classList.remove('hidden');
        scanModal.classList.add('visible');
        loadRecentFolders();
        scanPathInput.focus();
    });

    navSettings.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
        settingsModal.classList.add('visible');
    });

    cancelScanBtn.addEventListener('click', closeScanModal);
    closeSettingsBtn.addEventListener('click', closeSettingsModal);

    function closeScanModal() {
        scanModal.classList.add('hidden');
        scanModal.classList.remove('visible');
    }

    function closeSettingsModal() {
        settingsModal.classList.add('hidden');
        settingsModal.classList.remove('visible');
    }

    // Toggle switch
    asyncToggle.addEventListener('click', () => {
        asyncToggle.classList.toggle('active');
        asyncLyrics = asyncToggle.classList.contains('active');
    });

    // --- File Picker ---

    function loadRecentFolders() {
        const recent = JSON.parse(localStorage.getItem('recentFolders') || '[]');
        renderRecentFolders(recent);
    }

    function saveRecentFolder(path) {
        let recent = JSON.parse(localStorage.getItem('recentFolders') || '[]');
        recent = [path, ...recent.filter(p => p !== path)].slice(0, 5);
        localStorage.setItem('recentFolders', JSON.stringify(recent));
    }

    function renderRecentFolders(folders) {
        if (folders.length === 0) {
            recentFoldersList.innerHTML = '<div style="padding: 0.5rem; color: var(--text-dim); font-size: 0.8125rem; font-style: italic;">No recent folders</div>';
            return;
        }
        
        recentFoldersList.innerHTML = folders.map(path => `
            <div class="recent-item" data-path="${escapeHtml(path)}">
                <i data-lucide="folder-clock"></i>
                <span class="recent-path">${escapeHtml(path)}</span>
            </div>
        `).join('');
        
        // Add click handlers
        recentFoldersList.querySelectorAll('.recent-item').forEach(item => {
            item.addEventListener('click', () => {
                const path = item.dataset.path;
                selectedScanPath = path;
                scanPathInput.value = path;
                selectedFolderPath.textContent = path;
                selectedFolderPath.classList.add('has-path');
            });
        });
        
        refreshIcons();
    }

    // Native file picker
    browseFolderBtn.addEventListener('click', () => {
        nativeFolderPicker.click();
    });

    nativeFolderPicker.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            // Get folder path from first file
            const file = e.target.files[0];
            let folderPath = '';
            
            // Try to extract path from webkitRelativePath
            if (file.webkitRelativePath) {
                const parts = file.webkitRelativePath.split('/');
                parts.pop(); // Remove filename
                folderPath = parts.join('/');
            }
            
            // Fallback: use the name as folder name
            if (!folderPath && file.name) {
                folderPath = file.name;
            }
            
            if (folderPath) {
                selectedScanPath = folderPath;
                scanPathInput.value = folderPath;
                selectedFolderPath.textContent = folderPath;
                selectedFolderPath.classList.add('has-path');
                saveRecentFolder(folderPath);
                loadRecentFolders();
            }
        }
        // Reset input so same folder can be selected again
        nativeFolderPicker.value = '';
    });

    // Manual path input
    scanPathInput.addEventListener('input', (e) => {
        const path = e.target.value.trim();
        selectedScanPath = path;
        selectedFolderPath.textContent = path || 'No folder selected';
        if (path) {
            selectedFolderPath.classList.add('has-path');
        } else {
            selectedFolderPath.classList.remove('has-path');
        }
    });

    // --- Scanning ---

    confirmScanBtn.addEventListener('click', async () => {
        const path = selectedScanPath || scanPathInput.value.trim();
        if (!path) return;

        confirmScanBtn.disabled = true;
        confirmScanBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i><span>Starting...</span>';
        refreshIcons();

        try {
            const res = await fetch('/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path,
                    enable_audio: true,
                    enable_lyrics: true,
                    enable_async_lyrics: asyncLyrics
                })
            });

            if (res.ok) {
                closeScanModal();
                statusDot.classList.add('processing');
                statusText.textContent = 'Scanning...';
                pollScanStatus();
            }
        } catch (e) {
            console.error(e);
        } finally {
            confirmScanBtn.disabled = false;
            confirmScanBtn.innerHTML = '<i data-lucide="search"></i><span>Start Scan</span>';
        }
    });

    async function pollScanStatus() {
        if (scanInterval) clearInterval(scanInterval);
        scanInterval = setInterval(async () => {
            try {
                const res = await fetch('/scan/status');
                const status = await res.json();
                
                if (status.is_scanning) {
                    const pct = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;
                    statusMeta.textContent = `Scanning: ${pct}% (${status.indexed_songs} tracks)`;
                } else if (status.stage === 'complete') {
                    clearInterval(scanInterval);
                    statusDot.classList.remove('processing');
                    statusDot.classList.add('active');
                    statusText.textContent = 'Library Active';
                    fetchLibraryStats();
                }
            } catch (e) {
                console.error(e);
            }
        }, 1000);
    }

    // --- Flush Operations ---

    flushAllBtn.addEventListener('click', async () => {
        if (!confirm('Delete all tracks? This cannot be undone.')) return;
        try {
            await fetch('/library/flush', { method: 'POST' });
            fetchLibraryStats();
            queue = [];
            renderTrackGrid();
            closeSettingsModal();
        } catch (e) {
            console.error(e);
        }
    });

    flushClapBtn.addEventListener('click', async () => {
        if (!confirm('Clear CLAP embeddings?')) return;
        try {
            await fetch('/library/flush', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rescan_clap: true })
            });
            closeSettingsModal();
        } catch (e) {
            console.error(e);
        }
    });

    flushTextBtn.addEventListener('click', async () => {
        if (!confirm('Clear text embeddings?')) return;
        try {
            await fetch('/library/flush', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rescan_embeddings: true })
            });
            closeSettingsModal();
        } catch (e) {
            console.error(e);
        }
    });

    // --- Init ---
    fetchLibraryStats();
    volumeFill.style.width = '80%';
    updateVisualizerState(); // Initialize visualizer in paused state
    loadRecentFolders(); // Load recent folders

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (statusUpdateInterval) {
            clearInterval(statusUpdateInterval);
        }
        if (scanInterval) {
            clearInterval(scanInterval);
        }
    });
});