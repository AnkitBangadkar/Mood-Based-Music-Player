import { useEffect, useMemo, useState } from 'react'
import { useLibraryStore } from '@/store/libraryStore'
import { usePlayerStore } from '@/store/playerStore'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { 
  Search, 
  Play, 
  Music, 
  Disc3, 
  User, 
  Clock,
  Library,
  ChevronDown,
  Activity
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Song } from '@/types'

function formatTime(seconds: number): string {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

function TrackRow({ song, index, isActive, onPlay }: { 
  song: Song
  index: number
  isActive: boolean
  onPlay: () => void
}) {
  const energy = song.energy != null ? Math.round(song.energy * 100) : null

  return (
    <div 
      className={cn(
        "flex items-center gap-4 p-3 rounded-xl transition-all duration-200 cursor-pointer group",
        isActive 
          ? "bg-primary/10 ring-1 ring-primary/30" 
          : "hover:bg-muted/60"
      )}
      onClick={onPlay}
    >
      {/* Number / Playing Indicator */}
      <div className="w-8 text-center flex-shrink-0">
        {isActive ? (
          <div className="flex items-end justify-center gap-0.5 h-4">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="w-1 bg-primary rounded-full visualizer-bar"
                style={{ animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
        ) : (
          <span className="text-sm text-muted-foreground group-hover:text-foreground">
            {index + 1}
          </span>
        )}
      </div>

      {/* Album Art */}
      <div className={cn(
        "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-all",
        isActive 
          ? "bg-gradient-to-br from-amber-500 to-orange-500" 
          : "bg-muted group-hover:bg-amber-500/20"
      )}>
        {isActive ? (
          <Disc3 className="w-5 h-5 text-white animate-spin-slow" />
        ) : (
          <Music className="w-5 h-5 text-muted-foreground group-hover:text-amber-500" />
        )}
      </div>

      {/* Track Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={cn(
            "font-medium truncate",
            isActive ? "text-primary" : "group-hover:text-foreground"
          )}>
            {song.title}
          </p>
          {song.has_lyrics && (
            <Badge variant="secondary" className="text-[10px] h-4 px-1.5 bg-muted/50">
              Lyrics
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground truncate">{song.artist}</p>
      </div>

      {/* Album */}
      <div className="hidden md:block flex-1 min-w-0">
        <p className="text-sm text-muted-foreground truncate">{song.album}</p>
      </div>

      {/* Features */}
      <div className="hidden sm:flex items-center gap-4 text-sm">
        {energy !== null && (
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Activity className="w-3.5 h-3.5" />
            <span className="tabular-nums">{energy}%</span>
          </div>
        )}
        <div className="flex items-center gap-1.5 text-muted-foreground w-16 justify-end">
          <Clock className="w-3.5 h-3.5" />
          <span className="tabular-nums">{formatTime(song.duration || 0)}</span>
        </div>
      </div>

      {/* Play Button */}
      <Button 
        variant="ghost" 
        size="icon" 
        className={cn(
          "h-8 w-8 rounded-full flex-shrink-0 transition-all",
          isActive 
            ? "opacity-100 bg-primary text-primary-foreground" 
            : "opacity-0 group-hover:opacity-100 bg-muted"
        )}
        onClick={(e) => {
          e.stopPropagation()
          onPlay()
        }}
      >
        <Play className="w-4 h-4 ml-0.5" />
      </Button>
    </div>
  )
}

export function LibraryBrowser() {
  const { 
    songs, 
    searchQuery, 
    sortBy, 
    setSearchQuery, 
    setSortBy, 
    fetchSongs,
  } = useLibraryStore()
  const { queue, currentIndex, loadSong } = usePlayerStore()
  const [isLoading, setIsLoading] = useState(true)
  const [isSearchFocused, setIsSearchFocused] = useState(false)

  useEffect(() => {
    const load = async () => {
      await fetchSongs()
      setIsLoading(false)
    }
    load()
  }, [fetchSongs])

  const filteredSongs = useMemo(() => {
    let result = [...songs]
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(s => 
        (s.title || '').toLowerCase().includes(query) ||
        (s.artist || '').toLowerCase().includes(query) ||
        (s.album || '').toLowerCase().includes(query) ||
        (s.genre || '').toLowerCase().includes(query)
      )
    }
    
    // Apply sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return (a.title || '').localeCompare(b.title || '')
        case 'artist':
          return (a.artist || '').localeCompare(b.artist || '')
        case 'album':
          return (a.album || '').localeCompare(b.album || '')
        case 'recent':
          return b.id - a.id
        default:
          return 0
      }
    })
    
    return result
  }, [songs, searchQuery, sortBy])

  const handlePlaySong = (song: Song) => {
    loadSong(song, true)
  }

  const getCurrentSongId = () => {
    if (queue.length === 0) return null
    return queue[currentIndex]?.id
  }

  const currentSongId = getCurrentSongId()

  const sortOptions = [
    { value: 'title', label: 'Title', icon: Music },
    { value: 'artist', label: 'Artist', icon: User },
    { value: 'album', label: 'Album', icon: Disc3 },
    { value: 'recent', label: 'Recently Added', icon: Clock },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Library className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Your Library</h2>
                <p className="text-xs text-muted-foreground">
                  {songs.length.toLocaleString()} tracks
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className={cn(
              "relative flex-1 transition-all duration-300",
              isSearchFocused && "scale-[1.01]"
            )}>
              <Search className={cn(
                "absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors",
                isSearchFocused ? "text-primary" : "text-muted-foreground"
              )} />
              <Input
                placeholder="Search songs, artists, albums..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                className="pl-11 pr-4 py-2.5 rounded-xl bg-muted/50 border-0 focus-visible:ring-2 focus-visible:ring-primary/30"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="outline" 
                  className="gap-2 rounded-xl px-4"
                >
                  {sortOptions.find(o => o.value === sortBy)?.icon && (
                    <span className="text-muted-foreground">
                      {(() => {
                        const Icon = sortOptions.find(o => o.value === sortBy)?.icon
                        return Icon ? <Icon className="w-4 h-4" /> : null
                      })()}
                    </span>
                  )}
                  <span>Sort</span>
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {sortOptions.map((option) => (
                  <DropdownMenuItem 
                    key={option.value}
                    onClick={() => setSortBy(option.value as any)}
                    className={cn(
                      "gap-2 cursor-pointer",
                      sortBy === option.value && "bg-primary/10 text-primary"
                    )}
                  >
                    <option.icon className="w-4 h-4" />
                    {option.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Track List */}
      <ScrollArea className="flex-1 p-4">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center animate-pulse mb-4">
              <Disc3 className="w-6 h-6 text-white animate-spin" />
            </div>
            <p className="text-muted-foreground">Loading your library...</p>
          </div>
        ) : filteredSongs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <div className="w-20 h-20 rounded-3xl bg-muted flex items-center justify-center mb-5">
              {searchQuery ? (
                <Search className="w-10 h-10 text-muted-foreground" />
              ) : (
                <Music className="w-10 h-10 text-muted-foreground" />
              )}
            </div>
            <h3 className="text-xl font-semibold mb-2">
              {searchQuery ? 'No songs found' : 'Your library is empty'}
            </h3>
            <p className="text-muted-foreground max-w-sm">
              {searchQuery 
                ? 'Try a different search term or check your spelling'
                : 'Scan a music folder to get started with your collection'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredSongs.map((song, index) => (
              <TrackRow
                key={song.id}
                song={song}
                index={index}
                isActive={currentSongId === song.id}
                onPlay={() => handlePlaySong(song)}
              />
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
