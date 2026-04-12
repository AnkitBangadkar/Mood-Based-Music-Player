import { create } from 'zustand'
import type { LibraryStats, ScanStatus, ScanProgress, ScannedFolder, Song } from '@/types'

interface LibraryState {
  // Stats
  stats: LibraryStats | null
  
  // Scan state
  scanStatus: ScanStatus | null
  scanProgress: ScanProgress | null
  isScanning: boolean
  
  // Library data
  songs: Song[]
  folders: ScannedFolder[]
  
  // Filters
  searchQuery: string
  sortBy: 'title' | 'artist' | 'album' | 'recent'
  
  // Actions
  setStats: (stats: LibraryStats) => void
  setScanStatus: (status: ScanStatus | null) => void
  setScanProgress: (progress: ScanProgress | null) => void
  setIsScanning: (isScanning: boolean) => void
  setSongs: (songs: Song[]) => void
  setFolders: (folders: ScannedFolder[]) => void
  setSearchQuery: (query: string) => void
  setSortBy: (sortBy: 'title' | 'artist' | 'album' | 'recent') => void
  
  // Async actions
  fetchStats: () => Promise<void>
  fetchSongs: (limit?: number) => Promise<void>
  fetchScanStatus: () => Promise<void>
  startScan: (path: string, options?: { enableAudio?: boolean; enableLyrics?: boolean; enableAsyncLyrics?: boolean }) => Promise<void>
  removeFolder: (path: string) => Promise<void>
}

const API_BASE = '' // Empty since we're serving from same origin

export const useLibraryStore = create<LibraryState>((set, get) => ({
  // Initial state
  stats: null,
  scanStatus: null,
  scanProgress: null,
  isScanning: false,
  songs: [],
  folders: [],
  searchQuery: '',
  sortBy: 'title',

  // Actions
  setStats: (stats) => set({ stats }),
  setScanStatus: (status) => set({ scanStatus: status }),
  setScanProgress: (progress) => set({ scanProgress: progress }),
  setIsScanning: (isScanning) => set({ isScanning }),
  setSongs: (songs) => set({ songs }),
  setFolders: (folders) => set({ folders }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSortBy: (sortBy) => set({ sortBy }),

  // Async actions
  fetchStats: async () => {
    try {
      const res = await fetch(`${API_BASE}/library/stats`)
      if (res.ok) {
        const stats = await res.json()
        set({ stats })
      }
    } catch (e) {
      console.error('Failed to fetch stats:', e)
    }
  },

  fetchSongs: async (limit = 500) => {
    try {
      const res = await fetch(`${API_BASE}/songs?limit=${limit}`)
      if (res.ok) {
        const songs = await res.json()
        set({ songs })
      }
    } catch (e) {
      console.error('Failed to fetch songs:', e)
    }
  },

  fetchScanStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/scan/progress`)
      if (res.ok) {
        const progress = await res.json()
        set({ 
          scanProgress: progress,
          isScanning: progress.is_scanning || progress.lyrics?.is_running
        })
      }
    } catch (e) {
      console.error('Failed to fetch scan status:', e)
    }
  },

  startScan: async (path, options = {}) => {
    try {
      const res = await fetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path,
          enable_audio: options.enableAudio ?? true,
          enable_lyrics: options.enableLyrics ?? true,
          enable_async_lyrics: options.enableAsyncLyrics ?? true,
        }),
      })
      
      if (res.ok) {
        set({ isScanning: true })
      }
    } catch (e) {
      console.error('Failed to start scan:', e)
    }
  },

  removeFolder: async (path) => {
    try {
      const res = await fetch(`${API_BASE}/library/flush`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder: path }),
      })
      
      if (res.ok) {
        // Refresh stats and songs
        get().fetchStats()
        get().fetchSongs()
      }
    } catch (e) {
      console.error('Failed to remove folder:', e)
    }
  },
}))