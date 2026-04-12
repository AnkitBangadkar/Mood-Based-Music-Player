export interface Song {
  id: number
  title: string
  artist: string
  album: string
  genre: string
  filepath: string
  bpm?: number
  energy?: number
  valence?: number
  arousal?: number
  duration?: number
  has_lyrics?: boolean
  score?: number
  semantic_score?: number
  match_quality?: 'high' | 'medium' | 'low' | 'unknown'
}

export interface ScanStatus {
  is_scanning: boolean
  indexed_songs: number
  existing_songs: number
  current: number
  total: number
  current_file: string
  stage: string
  start_time?: number
  end_time?: number
  elapsed_seconds: number
  eta_seconds?: number
  errors: string[]
  lyrics_async: {
    is_running: boolean
    current: number
    total: number
    found: number
    not_found: number
    current_song: string
    stage: string
    elapsed_seconds: number
  }
}

export interface ScanProgress {
  is_scanning: boolean
  audio: {
    total: number
    processed: number
    indexed: number
    stage: string
    current_file: string
    elapsed_seconds: number
  }
  lyrics: {
    is_running: boolean
    total: number
    processed: number
    found: number
    not_found: number
    current_song: string
    stage: string
    elapsed_seconds: number
  }
  folders: ScannedFolder[]
}

export interface ScannedFolder {
  path: string
  song_count: number
  last_scan: string
}

export interface LibraryStats {
  song_count: number
  folder_count: number
  clap_count: number
  folders: ScannedFolder[]
  is_empty: boolean
}