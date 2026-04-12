import { useState, useEffect } from 'react'
import { Sidebar } from '@/components/Sidebar'
import { AudioPlayer } from '@/features/player/AudioPlayer'
import { PlaylistGenerator } from '@/features/generator/PlaylistGenerator'
import { LibraryBrowser } from '@/features/library/LibraryBrowser'
import { ScanView } from '@/features/scan/ScanView'
import { FlushView } from '@/features/scan/FlushView'
import { useAudio } from '@/hooks/useAudio'
import { useLibraryStore } from '@/store/libraryStore'
import { Toaster } from 'sonner'

type View = 'discover' | 'library' | 'scan' | 'flush'

export default function App() {
  const [currentView, setCurrentView] = useState<View>('discover')
  const audioRef = useAudio()
  const { fetchStats } = useLibraryStore()

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [fetchStats])

  const renderView = () => {
    switch (currentView) {
      case 'discover':
        return <PlaylistGenerator />
      case 'library':
        return <LibraryBrowser />
      case 'scan':
        return <ScanView />
      case 'flush':
        return <FlushView />
      default:
        return <PlaylistGenerator />
    }
  }

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentView={currentView} onViewChange={setCurrentView} />
        <main className="flex-1 overflow-hidden pb-28">
          {renderView()}
        </main>
      </div>
      <AudioPlayer />
      <audio ref={audioRef} />
      <Toaster 
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            color: 'hsl(var(--foreground))',
          },
        }}
      />
    </div>
  )
}
