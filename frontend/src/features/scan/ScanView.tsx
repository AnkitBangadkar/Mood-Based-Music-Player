import { useState, useEffect, useRef, useCallback } from 'react'
import { useLibraryStore } from '@/store/libraryStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  FolderSearch,
  Folder,
  Trash2,
  Music,
  Loader2,
  CheckCircle2,
  Clock,
  HardDrive,
  UploadCloud,
  FileMusic,
  Mic2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ScannedFolder } from '@/types'

function formatDuration(seconds: number): string {
  if (!seconds) return '--:--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m ${s}s`
}

function FolderCard({ folder, onRemove }: { folder: ScannedFolder; onRemove: () => void }) {
  return (
    <Card className="group border-0 shadow-md hover:shadow-lg transition-all duration-300">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0">
            <Folder className="w-6 h-6 text-blue-500" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate text-sm" title={folder.path}>
              {folder.path}
            </p>
            <div className="flex items-center gap-3 mt-2">
              <Badge variant="secondary" className="text-xs bg-muted/50">
                <Music className="w-3 h-3 mr-1" />
                {folder.song_count} tracks
              </Badge>
              {folder.last_scan && (
                <span className="text-xs text-muted-foreground">
                  Last scan: {new Date(folder.last_scan).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="opacity-0 group-hover:opacity-100 transition-all h-8 w-8 rounded-full text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={onRemove}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function FolderPicker({ onSelect, onClose }: { onSelect: (path: string) => void; onClose: () => void }) {
  const [isDragging, setIsDragging] = useState(false)
  const [path, setPath] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const items = e.dataTransfer.items
    if (items && items.length > 0) {
      const item = items[0]
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry?.()
        if (entry) {
          // For security reasons, we can't get the full path from drag & drop
          // But we can get the name to show feedback
          setPath(`Dropped: ${entry.name} (type path manually or use browse)`)
        }
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      // Get the path from the first file
      const file = files[0]
      // Try to construct path from webkitRelativePath
      const relativePath = (file as any).webkitRelativePath
      if (relativePath) {
        const folderPath = relativePath.split('/')[0]
        setPath(folderPath)
      }
    }
  }

  const handleSubmit = () => {
    if (path.trim()) {
      onSelect(path.trim())
    }
  }

  return (
    <div className="space-y-5">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "drop-zone rounded-2xl p-8 text-center transition-all duration-300 cursor-pointer",
          isDragging ? "drag-over scale-[1.02]" : "bg-muted/30 hover:bg-muted/50"
        )}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          {...{ webkitdirectory: '' }}
          {...{ directory: '' }}
          className="hidden"
          onChange={handleFileSelect}
        />
        <div className={cn(
          "w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center transition-all duration-300",
          isDragging ? "bg-primary scale-110" : "bg-muted"
        )}>
          <UploadCloud className={cn(
            "w-8 h-8 transition-colors",
            isDragging ? "text-white" : "text-muted-foreground"
          )} />
        </div>
        <p className="font-medium mb-1">
          {isDragging ? 'Drop folder here' : 'Drag & drop a folder here'}
        </p>
        <p className="text-sm text-muted-foreground">
          or click to browse
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          (Note: Due to browser security, you may need to type the full path below)
        </p>
      </div>

      {/* Manual Path Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium flex items-center gap-2">
          <HardDrive className="w-4 h-4" />
          Folder Path
        </label>
        <Input
          placeholder="/home/user/Music"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Enter the absolute path to your music folder
        </p>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          disabled={!path.trim()}
          className="gap-2"
        >
          <FolderSearch className="w-4 h-4" />
          Start Scan
        </Button>
      </div>
    </div>
  )
}

function AudioProgressCard({ progress }: { progress: any }) {
  const percent = progress.total > 0 ? (progress.processed / progress.total) * 100 : 0
  
  return (
    <Card className="border-0 shadow-md bg-gradient-to-br from-amber-500/5 to-orange-500/5">
      <CardContent className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <FileMusic className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <h4 className="font-semibold">Audio Analysis</h4>
              <p className="text-xs text-muted-foreground">
                {progress.stage !== 'idle' ? progress.stage : 'Waiting...'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">{Math.round(percent)}%</p>
            <p className="text-xs text-muted-foreground">
              {progress.processed} / {progress.total}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <Progress value={percent} className="h-2" />
          {progress.current_file && (
            <p className="text-xs text-muted-foreground truncate">
              <span className="font-medium">Now processing:</span> {progress.current_file}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2">
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" />
            <span>Elapsed: {formatDuration(progress.elapsed_seconds)}</span>
          </div>
          <span>{progress.indexed} files indexed</span>
        </div>
      </CardContent>
    </Card>
  )
}

function LyricsProgressCard({ progress }: { progress: any }) {
  const percent = progress.total > 0 ? (progress.processed / progress.total) * 100 : 0
  
  return (
    <Card className="border-0 shadow-md bg-gradient-to-br from-blue-500/5 to-purple-500/5">
      <CardContent className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Mic2 className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <h4 className="font-semibold">Lyrics Fetch</h4>
              <p className="text-xs text-muted-foreground">
                {progress.stage !== 'idle' ? progress.stage : 'Waiting...'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">{Math.round(percent)}%</p>
            <p className="text-xs text-muted-foreground">
              {progress.processed} / {progress.total}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <Progress value={percent} className="h-2" />
          {progress.current_song && (
            <p className="text-xs text-muted-foreground truncate">
              <span className="font-medium">Searching:</span> {progress.current_song}
            </p>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3 pt-2 border-t border-border/50">
          <div className="text-center">
            <p className="text-lg font-bold text-green-500">{progress.found}</p>
            <p className="text-xs text-muted-foreground">Found</p>
          </div>
          <div className="text-center border-x border-border/50">
            <p className="text-lg font-bold text-red-500">{progress.not_found}</p>
            <p className="text-xs text-muted-foreground">Not Found</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold">{formatDuration(progress.elapsed_seconds)}</p>
            <p className="text-xs text-muted-foreground">Elapsed</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function ScanView() {
  const { 
    stats, 
    scanProgress, 
    isScanning, 
    folders,
    fetchStats, 
    fetchScanStatus,
    startScan,
    removeFolder,
  } = useLibraryStore()
  
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  useEffect(() => {
    let interval: NodeJS.Timeout
    
    if (isScanning) {
      interval = setInterval(() => {
        fetchScanStatus()
      }, 1000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isScanning, fetchScanStatus])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  const handleStartScan = async (path: string) => {
    await startScan(path)
    setIsDialogOpen(false)
  }

  const handleRemoveFolder = async (path: string) => {
    if (confirm(`Remove all songs from this folder?\n${path}`)) {
      await removeFolder(path)
    }
  }

  return (
    <div className="flex flex-col h-full p-6">
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
              <FolderSearch className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Scan Library</h2>
              <p className="text-sm text-muted-foreground">Add music folders to your collection</p>
            </div>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 rounded-full px-6 shadow-lg shadow-amber-500/20 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600">
                <UploadCloud className="w-4 h-4" />
                Add Folder
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <FolderSearch className="w-5 h-5 text-primary" />
                  Scan Music Folder
                </DialogTitle>
              </DialogHeader>
              <FolderPicker 
                onSelect={handleStartScan}
                onClose={() => setIsDialogOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="border-0 shadow-md">
            <CardContent className="p-5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                  <Music className="w-6 h-6 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Tracks</p>
                  <p className="text-2xl font-bold">{stats?.song_count?.toLocaleString() || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-md">
            <CardContent className="p-5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Analyzed</p>
                  <p className="text-2xl font-bold">{stats?.clap_count?.toLocaleString() || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-md">
            <CardContent className="p-5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center">
                  <Folder className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Folders</p>
                  <p className="text-2xl font-bold">{folders.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Scan Progress */}
        {isScanning && scanProgress && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <h3 className="font-semibold text-lg">Scanning in Progress</h3>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              <AudioProgressCard progress={scanProgress.audio} />
              {scanProgress.lyrics.is_running && (
                <LyricsProgressCard progress={scanProgress.lyrics} />
              )}
            </div>
          </div>
        )}

        {/* Folders List */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-muted-foreground" />
            Scanned Folders
          </h3>
          {folders.length === 0 ? (
            <Card className="border-0 shadow-md border-dashed border-2">
              <CardContent className="p-10 text-center">
                <div className="w-16 h-16 rounded-2xl bg-muted mx-auto mb-4 flex items-center justify-center">
                  <Folder className="w-8 h-8 text-muted-foreground" />
                </div>
                <h4 className="font-semibold text-lg mb-2">No folders scanned yet</h4>
                <p className="text-sm text-muted-foreground mb-5 max-w-sm mx-auto">
                  Add a music folder to start building your library. We&apos;ll analyze audio features and fetch lyrics.
                </p>
                <Button 
                  onClick={() => setIsDialogOpen(true)}
                  className="gap-2 rounded-full px-6"
                >
                  <UploadCloud className="w-4 h-4" />
                  Add Folder
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {folders.map((folder) => (
                <FolderCard
                  key={folder.path}
                  folder={folder}
                  onRemove={() => handleRemoveFolder(folder.path)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
