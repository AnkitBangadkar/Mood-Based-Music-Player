import { useLibraryStore } from '@/store/libraryStore'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Compass, 
  Library, 
  FolderSearch, 
  Trash2, 
  Radio,
  Disc3,
  Loader2
} from 'lucide-react'

type View = 'discover' | 'library' | 'scan' | 'flush'

interface SidebarProps {
  currentView: View
  onViewChange: (view: View) => void
}

export function Sidebar({ currentView, onViewChange }: SidebarProps) {
  const { stats, isScanning } = useLibraryStore()

  const navItems = [
    { 
      id: 'discover' as View, 
      label: 'Discover', 
      icon: Compass,
      description: 'Generate playlists'
    },
    { 
      id: 'library' as View, 
      label: 'Library', 
      icon: Library, 
      badge: stats?.song_count,
      description: 'Browse your music'
    },
    { 
      id: 'scan' as View, 
      label: 'Scan', 
      icon: FolderSearch,
      description: 'Add music folders'
    },
    { 
      id: 'flush' as View, 
      label: 'Manage', 
      icon: Trash2,
      description: 'Clear data'
    },
  ]

  return (
    <aside className="w-64 h-full flex flex-col">
      {/* Brand */}
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/25">
            <Radio className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-xl leading-tight bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
              SoulSeek
            </h1>
            <p className="text-xs text-muted-foreground font-medium">Mood Discovery</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <Button
            key={item.id}
            variant="ghost"
            className={cn(
              'w-full justify-start gap-3 h-12 rounded-xl transition-all duration-200',
              currentView === item.id 
                ? 'bg-amber-500/10 text-amber-500' 
                : 'hover:bg-muted/50 text-muted-foreground hover:text-foreground'
            )}
            onClick={() => onViewChange(item.id)}
          >
            <div className={cn(
              "w-9 h-9 rounded-lg flex items-center justify-center transition-all",
              currentView === item.id 
                ? "bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-md" 
                : "bg-muted"
            )}>
              {item.id === 'scan' && isScanning ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <item.icon className="w-4 h-4" />
              )}
            </div>
            <div className="flex-1 text-left">
              <span className="font-medium">{item.label}</span>
            </div>
            {item.badge !== undefined && (
              <Badge 
                variant="secondary" 
                className="text-xs bg-muted"
              >
                {item.badge.toLocaleString()}
              </Badge>
            )}
          </Button>
        ))}
      </nav>

      {/* Status Card */}
      <div className="p-4">
        <div className={cn(
          "flex items-center gap-3 p-3 rounded-xl transition-all",
          isScanning 
            ? "bg-amber-500/10" 
            : stats && stats.song_count > 0 
              ? "bg-emerald-500/10" 
              : "bg-muted/50"
        )}>
          <div className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0",
            isScanning 
              ? "bg-amber-500 text-white" 
              : stats && stats.song_count > 0 
                ? "bg-emerald-500 text-white" 
                : "bg-muted"
          )}>
            {isScanning ? (
              <Disc3 className="w-5 h-5 animate-spin" />
            ) : (
              <Radio className="w-5 h-5" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate">
              {isScanning ? 'Scanning...' : 
               stats && stats.song_count > 0 ? 'Library Active' : 'Ready'}
            </p>
            <p className="text-xs text-muted-foreground">
              {stats && stats.song_count > 0 
                ? `${stats.song_count.toLocaleString()} tracks` 
                : 'Add music to start'}
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}
