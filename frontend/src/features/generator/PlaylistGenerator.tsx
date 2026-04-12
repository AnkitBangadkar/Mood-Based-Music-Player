import { useState } from 'react'
import { usePlaylistGenerator } from '@/hooks/usePlaylistGenerator'
import { usePlayerStore } from '@/store/playerStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Zap, 
  Play, 
  Clock,
  Heart,
  Activity, 
  Sparkles,
  Music,
  Disc3,
  Radio,
  Wind,
  Flame,
  CloudRain,
  Sun,
  Moon,
  Coffee
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Song } from '@/types'

function formatTime(seconds: number): string {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

function getScoreColor(score?: number): string {
  if (!score) return 'bg-muted text-muted-foreground'
  if (score >= 70) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
  if (score >= 50) return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
  if (score >= 35) return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
  return 'bg-red-500/20 text-red-400 border-red-500/30'
}

const moodSuggestions = [
  { text: 'happy but not energetic', icon: Sun, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  { text: 'sad rainy day', icon: CloudRain, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { text: 'chill lofi', icon: Coffee, color: 'text-amber-600', bg: 'bg-amber-600/10' },
  { text: 'hype workout', icon: Flame, color: 'text-red-500', bg: 'bg-red-500/10' },
  { text: 'romantic evening', icon: Moon, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  { text: 'peaceful breeze', icon: Wind, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
]

function TrackCard({ song, index: _index, isActive, onClick }: { 
  song: Song
  index: number
  isActive: boolean
  onClick: () => void
}) {
  const energy = song.energy != null ? Math.round(song.energy * 100) : null
  const valence = song.valence != null ? Math.round((song.valence + 1) * 50) : null

  return (
    <Card 
      className={cn(
        "cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-lg group border-0 shadow-md",
        isActive ? "ring-2 ring-primary bg-primary/5" : "hover:bg-card/80"
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Album Art Placeholder */}
          <div className={cn(
            "w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300",
            isActive 
              ? "bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg shadow-amber-500/25" 
              : "bg-gradient-to-br from-muted to-muted/50 group-hover:from-amber-500/20 group-hover:to-orange-500/20"
          )}>
            {isActive ? (
              <Disc3 className="w-7 h-7 text-white animate-spin-slow" />
            ) : (
              <Music className="w-6 h-6 text-muted-foreground group-hover:text-amber-500 transition-colors" />
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h4 className={cn(
                  "font-semibold truncate transition-colors",
                  isActive ? "text-primary" : "group-hover:text-foreground"
                )}>
                  {song.title}
                </h4>
                <p className="text-sm text-muted-foreground truncate">{song.artist}</p>
              </div>
              {song.score && (
                <Badge variant="outline" className={cn("flex-shrink-0 text-xs", getScoreColor(song.score))}>
                  {song.score.toFixed(0)}%
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
              {energy !== null && (
                <div className="flex items-center gap-1.5 bg-muted/50 px-2 py-1 rounded-full">
                  <Activity className="w-3 h-3" />
                  <span>Energy {energy}%</span>
                </div>
              )}
              {valence !== null && (
                <div className="flex items-center gap-1.5 bg-muted/50 px-2 py-1 rounded-full">
                  <Heart className="w-3 h-3" />
                  <span>Mood {valence}%</span>
                </div>
              )}
              <div className="flex items-center gap-1.5 bg-muted/50 px-2 py-1 rounded-full">
                <Clock className="w-3 h-3" />
                <span>{formatTime(song.duration || 0)}</span>
              </div>
            </div>
          </div>
          
          {/* Play Button */}
          <div className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300",
            isActive 
              ? "bg-primary text-primary-foreground scale-100" 
              : "bg-muted text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:scale-100 scale-90"
          )}>
            <Play className="w-5 h-5 ml-0.5" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function EmptyState({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6">
      <h3 className="text-3xl font-bold mb-3 text-amber-500">
        Discover Your Mood
      </h3>
      <p className="text-muted-foreground max-w-md mb-8 text-base leading-relaxed">
        Describe how you&apos;re feeling and let AI craft the perfect playlist for your moment.
      </p>
      
      {/* Mood Suggestions */}
      <div className="flex gap-3 flex-wrap justify-center max-w-2xl">
        {moodSuggestions.map((suggestion) => (
          <button
            key={suggestion.text}
            onClick={() => onSuggestionClick(suggestion.text)}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-full transition-all duration-300 hover:scale-105",
              "border border-border/50 hover:border-primary/50",
              "bg-card/50 hover:bg-card shadow-sm hover:shadow-md"
            )}
          >
            <suggestion.icon className={cn("w-4 h-4", suggestion.color)} />
            <span className="text-sm font-medium">{suggestion.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export function PlaylistGenerator() {
  const [prompt, setPrompt] = useState('')
  const { isGenerating, results, query, generatePlaylist, clearResults } = usePlaylistGenerator()
  const { queue, currentIndex, setQueue, playSongAtIndex } = usePlayerStore()
  const [isInputFocused, setIsInputFocused] = useState(false)

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    const songs = await generatePlaylist(prompt)
    if (songs.length > 0) {
      setQueue(songs, 0)
    }
  }

  const handlePlayTrack = (index: number) => {
    if (queue !== results) {
      setQueue(results, index)
    } else {
      playSongAtIndex(index)
    }
  }

  const showEmptyState = results.length === 0 && !isGenerating && !query

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Generate Playlist</h2>
              <p className="text-xs text-muted-foreground">AI-powered mood matching</p>
            </div>
          </div>
          
          <div className={cn(
            "flex gap-3 p-1.5 rounded-2xl transition-all duration-300",
            isInputFocused ? "bg-card shadow-lg ring-2 ring-primary/20" : "bg-muted/50"
          )}>
            <div className="relative flex-1">
              <Radio className={cn(
                "absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 transition-colors",
                isInputFocused ? "text-primary" : "text-muted-foreground"
              )} />
              <Input
                placeholder="Describe a mood... (e.g., 'rainy day melancholy')"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                onFocus={() => setIsInputFocused(true)}
                onBlur={() => setIsInputFocused(false)}
                className="flex-1 border-0 bg-transparent pl-12 pr-4 py-3 text-base placeholder:text-muted-foreground/70 focus-visible:ring-0 focus-visible:ring-offset-0"
              />
            </div>
            <Button 
              onClick={handleGenerate} 
              disabled={isGenerating || !prompt.trim()}
              className="gap-2 px-6 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-lg shadow-amber-500/25 transition-all hover:shadow-amber-500/40 hover:scale-[1.02]"
            >
              {isGenerating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Generate</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-6">
        {showEmptyState ? (
          <EmptyState onSuggestionClick={setPrompt} />
        ) : (
          <div className="max-w-4xl mx-auto">
            {query && (
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold">&ldquo;{query}&rdquo;</h3>
                  <p className="text-sm text-muted-foreground mt-1">{results.length} tracks matched your mood</p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={clearResults}
                  className="rounded-full px-4"
                >
                  Clear Results
                </Button>
              </div>
            )}
            
            <div className="grid gap-3">
              {results.map((song, index) => (
                <TrackCard
                  key={song.id}
                  song={song}
                  index={index}
                  isActive={queue === results && currentIndex === index}
                  onClick={() => handlePlayTrack(index)}
                />
              ))}
            </div>
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
