import { useEffect, useRef } from 'react'
import { usePlayerStore } from '@/store/playerStore'

export function useAudio() {
  const audioRef = useRef<HTMLAudioElement>(null)
  const {
    setAudioRef,
    setCurrentTime,
    setDuration,
    isRepeating,
    next,
    pause,
  } = usePlayerStore()

  useEffect(() => {
    if (audioRef.current) {
      setAudioRef(audioRef.current)
    }

    return () => {
      setAudioRef(null)
    }
  }, [setAudioRef])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
    }

    const handleEnded = () => {
      if (isRepeating) {
        audio.currentTime = 0
        audio.play()
      } else {
        next()
      }
    }

    const handleError = (e: ErrorEvent) => {
      console.error('Audio error:', e)
      pause()
    }

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError as EventListener)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError as EventListener)
    }
  }, [setCurrentTime, setDuration, isRepeating, next, pause])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (e.code) {
        case 'Space':
          e.preventDefault()
          usePlayerStore.getState().togglePlay()
          break
        case 'ArrowRight':
          e.preventDefault()
          next()
          break
        case 'ArrowLeft':
          e.preventDefault()
          usePlayerStore.getState().previous()
          break
        case 'ArrowUp':
          e.preventDefault()
          {
            const { volume, setVolume } = usePlayerStore.getState()
            setVolume(Math.min(1, volume + 0.05))
          }
          break
        case 'ArrowDown':
          e.preventDefault()
          {
            const { volume, setVolume } = usePlayerStore.getState()
            setVolume(Math.max(0, volume - 0.05))
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [next])

  return audioRef
}