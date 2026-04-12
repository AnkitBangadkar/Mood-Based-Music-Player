import { create } from 'zustand'
import type { Song } from '@/types'

interface PlayerState {
  // Audio state
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
  isMuted: boolean
  isShuffling: boolean
  isRepeating: boolean
  
  // Queue
  queue: Song[]
  currentIndex: number
  
  // Audio element ref
  audioRef: HTMLAudioElement | null
  
  // Actions
  setAudioRef: (ref: HTMLAudioElement | null) => void
  setQueue: (songs: Song[], startIndex?: number) => void
  play: () => void
  pause: () => void
  togglePlay: () => void
  next: () => void
  previous: () => void
  seek: (time: number) => void
  setVolume: (volume: number) => void
  toggleMute: () => void
  toggleShuffle: () => void
  toggleRepeat: () => void
  playSongAtIndex: (index: number) => void
  loadSong: (song: Song, autoPlay?: boolean) => void
  setCurrentTime: (time: number) => void
  setDuration: (duration: number) => void
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  // Initial state
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  volume: 0.8,
  isMuted: false,
  isShuffling: false,
  isRepeating: false,
  queue: [],
  currentIndex: 0,
  audioRef: null,

  // Actions
  setAudioRef: (ref) => set({ audioRef: ref }),
  
  setQueue: (songs, startIndex = 0) => set({ 
    queue: songs, 
    currentIndex: startIndex,
    currentTime: 0 
  }),
  
  play: () => {
    const { audioRef } = get()
    if (audioRef) {
      audioRef.play()
      set({ isPlaying: true })
    }
  },
  
  pause: () => {
    const { audioRef } = get()
    if (audioRef) {
      audioRef.pause()
      set({ isPlaying: false })
    }
  },
  
  togglePlay: () => {
    const { isPlaying, play, pause } = get()
    if (isPlaying) {
      pause()
    } else {
      play()
    }
  },
  
  next: () => {
    const { queue, currentIndex, isShuffling } = get()
    if (queue.length === 0) return
    
    let nextIndex: number
    if (isShuffling) {
      nextIndex = Math.floor(Math.random() * queue.length)
    } else {
      nextIndex = currentIndex + 1
      if (nextIndex >= queue.length) nextIndex = 0
    }
    
    get().playSongAtIndex(nextIndex)
  },
  
  previous: () => {
    const { queue, currentIndex } = get()
    if (queue.length === 0) return
    
    let prevIndex = currentIndex - 1
    if (prevIndex < 0) prevIndex = queue.length - 1
    
    get().playSongAtIndex(prevIndex)
  },
  
  seek: (time) => {
    const { audioRef } = get()
    if (audioRef) {
      audioRef.currentTime = time
      set({ currentTime: time })
    }
  },
  
  setVolume: (volume) => {
    const { audioRef } = get()
    if (audioRef) {
      audioRef.volume = volume
      set({ volume, isMuted: volume === 0 })
    }
  },
  
  toggleMute: () => {
    const { audioRef, isMuted, volume } = get()
    if (audioRef) {
      if (isMuted) {
        audioRef.volume = volume || 0.8
        set({ isMuted: false })
      } else {
        audioRef.volume = 0
        set({ isMuted: true })
      }
    }
  },
  
  toggleShuffle: () => set((state) => ({ isShuffling: !state.isShuffling })),
  toggleRepeat: () => set((state) => ({ isRepeating: !state.isRepeating })),
  
  playSongAtIndex: (index) => {
    const { queue, audioRef } = get()
    if (index < 0 || index >= queue.length || !audioRef) return
    
    const song = queue[index]
    audioRef.src = `/audio/${song.id}`
    audioRef.load()
    set({ currentIndex: index, currentTime: 0 })
    
    audioRef.play().then(() => {
      set({ isPlaying: true })
    }).catch(console.error)
  },
  
  loadSong: (song, autoPlay = true) => {
    const { audioRef, queue } = get()
    if (!audioRef) return
    
    // Find song in queue or add it
    const existingIndex = queue.findIndex(s => s.id === song.id)
    
    if (existingIndex === -1) {
      set({ queue: [song], currentIndex: 0 })
    } else {
      set({ currentIndex: existingIndex })
    }
    
    audioRef.src = `/audio/${song.id}`
    audioRef.load()
    set({ currentTime: 0 })
    
    if (autoPlay) {
      audioRef.play().then(() => {
        set({ isPlaying: true })
      }).catch(console.error)
    }
  },
  
  setCurrentTime: (time) => set({ currentTime: time }),
  setDuration: (duration) => set({ duration }),
}))