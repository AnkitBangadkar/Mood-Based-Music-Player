import { useState, useEffect } from 'react'
import { usePlayerStore } from '@/store/playerStore'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Shuffle, 
  Repeat, 
  Volume2, 
  VolumeX,
  Disc3,
  ListMusic,
  FileText
} from 'lucide-react'
import { cn } from '@/lib/utils'

function formatTime(seconds: number): string {
  if (!seconds || isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

function AnimatedEqualizer({ isPlaying }: { isPlaying: boolean }) {
  if (!isPlaying) return null
  
  return (
    <div className="flex items-end gap-0.5 h-4">
      {[...Array(4)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-primary rounded-full visualizer-bar"
          style={{ 
            animationDelay: `${i * 0.1}s`,
            animationPlayState: isPlaying ? 'running' : 'paused'
          }}
        />
      ))}
    </div>
  )
}

export function AudioPlayer() {
  const {
    queue,
    currentIndex,
    isPlaying,
    currentTime,
    duration,
    volume,
    isMuted,
    isShuffling,
    isRepeating,
    togglePlay,
    next,
    previous,
    seek,
    setVolume,
    toggleMute,
    toggleShuffle,
    toggleRepeat,
  } = usePlayerStore()

  const currentSong = queue[currentIndex]
  const progress = duration ? (currentTime / duration) * 100 : 0

  const [showLyrics, setShowLyrics] = useState(false)
  const [lyricsText, setLyricsText] = useState<string | null>(null)
  const [loadingLyrics, setLoadingLyrics] = useState(false)

  useEffect(() => {
    if (!currentSong?.id || !currentSong?.has_lyrics) {
      setLyricsText(null)
      return
    }
    setLyricsText(null)
  }, [currentSong?.id, currentSong?.has_lyrics])

  const fetchLyrics = async () => {
    if (!currentSong?.id) return
    setLoadingLyrics(true)
    try {
      const res = await fetch(`/lyrics/${currentSong.id}`)
      const data = await res.json()
      if (data.has_lyrics && data.lyrics) {
        setLyricsText(data.lyrics)
        setShowLyrics(true)
      }
    } catch (e) {
      console.error('Failed to fetch lyrics:', e)
    } finally {
      setLoadingLyrics(false)
    }
  }

  if (!currentSong) {
    return (
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
        <div className="glass-floating player-island rounded-2xl px-6 py-3 flex items-center gap-4 min-w-[400px]">
          <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
            <Disc3 className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">No Signal</p>
            <p className="text-xs text-muted-foreground">--</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-4xl px-4">
        <div className="glass-floating player-island rounded-3xl px-6 py-4 space-y-3">
          {/* Progress Bar - Full Width on Top */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-10 text-right tabular-nums shrink-0">
              {formatTime(currentTime)}
            </span>
            <Slider
              value={[progress]}
              max={100}
              step={0.1}
              className="flex-1"
              onValueChange={([value]) => seek((value / 100) * duration)}
            />
            <span className="text-xs text-muted-foreground w-10 tabular-nums shrink-0">
              {formatTime(duration)}
            </span>
          </div>

          {/* Controls Row */}
          <div className="flex items-center gap-4 min-w-0">
            {/* Album Art */}
            <div className={cn(
              "w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-500",
              isPlaying 
                ? "bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg shadow-amber-500/30" 
                : "bg-gradient-to-br from-muted to-muted/50"
            )}>
              {isPlaying ? (
                <Disc3 className="w-7 h-7 text-white animate-spin-slow" />
              ) : (
                <Disc3 className="w-7 h-7 text-muted-foreground" />
              )}
            </div>

            {/* Track Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 min-w-0">
                <p className="text-sm font-semibold truncate min-w-0">{currentSong.title}</p>
                <AnimatedEqualizer isPlaying={isPlaying} />
                {currentSong.has_lyrics && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-amber-500 shrink-0"
                    onClick={fetchLyrics}
                    disabled={loadingLyrics}
                  >
                    <FileText className="w-4 h-4" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground truncate">{currentSong.artist}</p>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-1 shrink-0">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-9 w-9 rounded-full transition-all",
                      isShuffling ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground"
                    )}
                    onClick={toggleShuffle}
                  >
                    <Shuffle className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Shuffle</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-9 w-9 rounded-full text-muted-foreground hover:text-foreground"
                    onClick={previous}
                  >
                    <SkipBack className="w-5 h-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Previous</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    size="icon" 
                    className="h-12 w-12 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-lg shadow-amber-500/30 transition-all hover:shadow-amber-500/50 hover:scale-105"
                    onClick={togglePlay}
                  >
                    {isPlaying ? (
                      <Pause className="w-5 h-5" />
                    ) : (
                      <Play className="w-5 h-5 ml-0.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{isPlaying ? 'Pause' : 'Play'}</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-9 w-9 rounded-full text-muted-foreground hover:text-foreground"
                    onClick={next}
                  >
                    <SkipForward className="w-5 h-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Next</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-9 w-9 rounded-full transition-all",
                      isRepeating ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground"
                    )}
                    onClick={toggleRepeat}
                  >
                    <Repeat className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Repeat</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {/* Volume */}
            <div className="hidden sm:flex items-center gap-2 shrink-0">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground"
                    onClick={toggleMute}
                  >
                    {isMuted || volume === 0 ? (
                      <VolumeX className="w-4 h-4" />
                    ) : (
                      <Volume2 className="w-4 h-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{isMuted ? 'Unmute' : 'Mute'}</p>
                </TooltipContent>
              </Tooltip>
              <Slider
                value={[isMuted ? 0 : volume * 100]}
                max={100}
                step={1}
                className="w-20"
                onValueChange={([value]) => setVolume(value / 100)}
              />
            </div>

            {/* Queue indicator */}
            <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-border/50 shrink-0">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full text-muted-foreground">
                    <ListMusic className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Queue ({queue.length})</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </div>

          {/* Mobile Progress Bar */}
          <div className="md:hidden flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-8 text-right tabular-nums">
              {formatTime(currentTime)}
            </span>
            <Slider
              value={[progress]}
              max={100}
              step={0.1}
              className="flex-1"
              onValueChange={([value]) => seek((value / 100) * duration)}
            />
            <span className="text-xs text-muted-foreground w-8 tabular-nums">
              {formatTime(duration)}
            </span>
          </div>
        </div>

        {/* Lyrics Dialog */}
        <Dialog open={showLyrics} onOpenChange={setShowLyrics}>
          <DialogContent className="max-w-lg max-h-[70vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle className="text-lg font-semibold">{currentSong.title}</DialogTitle>
              <p className="text-sm text-muted-foreground">{currentSong.artist}</p>
            </DialogHeader>
            <div className="flex-1 overflow-y-auto">
              {loadingLyrics ? (
                <p className="text-muted-foreground text-center py-8">Loading lyrics...</p>
              ) : lyricsText ? (
                <pre className="whitespace-pre-wrap text-sm leading-relaxed text-foreground font-sans">
                  {lyricsText}
                </pre>
              ) : (
                <p className="text-muted-foreground text-center py-8">No lyrics available</p>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </TooltipProvider>
  )
}
