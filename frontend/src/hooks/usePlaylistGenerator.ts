import { useState, useCallback } from 'react'
import type { Song } from '@/types'

interface GenerateState {
  isGenerating: boolean
  results: Song[]
  query: string
  error: string | null
}

export function usePlaylistGenerator() {
  const [state, setState] = useState<GenerateState>({
    isGenerating: false,
    results: [],
    query: '',
    error: null,
  })

  const generatePlaylist = useCallback(async (prompt: string, limit = 20) => {
    setState(prev => ({ ...prev, isGenerating: true, error: null, query: prompt }))

    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, limit }),
      })

      if (!res.ok) {
        throw new Error('Failed to generate playlist')
      }

      const results = await res.json()
      setState(prev => ({ ...prev, results, isGenerating: false }))
      return results
    } catch (e) {
      setState(prev => ({ 
        ...prev, 
        isGenerating: false, 
        error: e instanceof Error ? e.message : 'Unknown error' 
      }))
      return []
    }
  }, [])

  const clearResults = useCallback(() => {
    setState({
      isGenerating: false,
      results: [],
      query: '',
      error: null,
    })
  }, [])

  return {
    ...state,
    generatePlaylist,
    clearResults,
  }
}