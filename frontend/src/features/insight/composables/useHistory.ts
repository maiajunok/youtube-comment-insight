import type { InsightData } from '@/features/insight/types/insight'

export type HistoryEntry = {
  videoId: string
  savedAt: string
  data: InsightData
}

const STORAGE_KEY = 'insight_history'

export function useHistory() {
  const getAll = (): HistoryEntry[] => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')
    } catch {
      return []
    }
  }

  const save = (videoId: string, data: InsightData) => {
    const entries = getAll().filter(e => e.videoId !== videoId)
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([{ videoId, savedAt: new Date().toISOString(), data }, ...entries]),
    )
  }

  const remove = (videoId: string) => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(getAll().filter(e => e.videoId !== videoId)),
    )
  }

  return { getAll, save, remove }
}
