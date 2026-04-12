import { useState } from 'react'
import { useLibraryStore } from '@/store/libraryStore'
import { Card, CardContent } from '@/components/ui/card'
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { 
  Trash2, 
  FileAudio, 
  FileText, 
  AlertTriangle,
  Database,
  RotateCcw
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'

interface FlushOption {
  id: string
  title: string
  description: string
  icon: React.ElementType
  color: string
  bgColor: string
  warning: string
  endpoint?: string
  body?: object
}

export function FlushView() {
  const { fetchStats, fetchSongs } = useLibraryStore()
  const [isFlushing, setIsFlushing] = useState(false)

  const flushOptions: FlushOption[] = [
    {
      id: 'all',
      title: 'Flush Everything',
      description: 'Remove all songs, playlists, and analysis data from the library',
      icon: Database,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      warning: 'This will permanently delete all your library data. This action cannot be undone.',
    },
    {
      id: 'clap',
      title: 'Clear Audio Analysis',
      description: 'Remove CLAP embeddings and audio feature analysis only',
      icon: FileAudio,
      color: 'text-amber-500',
      bgColor: 'bg-amber-500/10',
      warning: 'This will remove all audio analysis data. You will need to rescan to regenerate it.',
      body: { rescan_clap: true }
    },
    {
      id: 'embeddings',
      title: 'Clear Text Embeddings',
      description: 'Remove BGE text embeddings and lyric analysis only',
      icon: FileText,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      warning: 'This will remove all text and lyric embeddings. You will need to rescan to regenerate them.',
      body: { rescan_embeddings: true }
    },
  ]

  const handleFlush = async (option: FlushOption) => {
    setIsFlushing(true)
    try {
      const res = await fetch('/library/flush', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(option.body || {}),
      })

      if (res.ok) {
        const data = await res.json()
        toast.success(data.message || 'Library flushed successfully')
        await fetchStats()
        await fetchSongs()
      } else {
        toast.error('Failed to flush library')
      }
    } catch (e) {
      toast.error('An error occurred while flushing')
    } finally {
      setIsFlushing(false)
    }
  }

  return (
    <div className="flex flex-col h-full p-6">
      <div className="max-w-3xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg shadow-red-500/20">
            <Trash2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Manage Library</h2>
            <p className="text-sm text-muted-foreground">Clear data and reset analysis</p>
          </div>
        </div>

        {/* Warning Card */}
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-500 mb-1">Warning</h3>
              <p className="text-sm text-muted-foreground">
                These actions are permanent and cannot be undone. Make sure you have backups of any important data before proceeding.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Flush Options */}
        <div className="space-y-3">
          {flushOptions.map((option) => (
            <AlertDialog key={option.id}>
              <AlertDialogTrigger asChild>
                <Card className="group cursor-pointer border-0 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.01]">
                  <CardContent className="p-5">
                    <div className="flex items-start gap-4">
                      <div className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-all",
                        option.bgColor
                      )}>
                        <option.icon className={cn("w-6 h-6", option.color)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-lg mb-1">{option.title}</h3>
                        <p className="text-sm text-muted-foreground">{option.description}</p>
                      </div>
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center group-hover:bg-red-500/10 group-hover:text-red-500 transition-colors">
                          <Trash2 className="w-5 h-5" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                    Are you sure?
                  </AlertDialogTitle>
                  <AlertDialogDescription className="space-y-3">
                    <p>{option.warning}</p>
                    {option.id === 'all' && (
                      <p className="font-semibold text-red-500">
                        This action cannot be undone!
                      </p>
                    )}
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => handleFlush(option)}
                    disabled={isFlushing}
                    className={cn(
                      "gap-2",
                      option.id === 'all' 
                        ? "bg-red-500 hover:bg-red-600" 
                        : "bg-amber-500 hover:bg-amber-600"
                    )}
                  >
                    {isFlushing ? (
                      <RotateCcw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                    {isFlushing ? 'Flushing...' : 'Yes, Flush'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          ))}
        </div>
      </div>
    </div>
  )
}
