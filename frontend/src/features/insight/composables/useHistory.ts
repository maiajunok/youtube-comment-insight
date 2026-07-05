import type { CommentGraphData, InsightData } from '@/features/insight/types/insight'

export type HistoryEntry = {
  videoId: string
  savedAt: string
  data: InsightData
  // JSON 백업 파일에서 가져온 항목에만 있음(백엔드 분석 직후 저장되는 항목은 그래프를
  // 따로 안 들고 다님 — NetworkView가 필요할 때 /api/graph에서 직접 받아오므로)
  graph?: CommentGraphData | null
  // 백엔드에 실제로 존재하지 않고 이 브라우저에만 있는 항목인지 — HistoryView가 이 값으로
  // "로컬" 배지를 붙이고, 조회 시 서버 재요청 대신 저장된 데이터를 그대로 씀
  importedOnly?: boolean
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

  const save = (videoId: string, data: InsightData, graph?: CommentGraphData | null, importedOnly = false) => {
    const entries = getAll().filter(e => e.videoId !== videoId)
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([{ videoId, savedAt: new Date().toISOString(), data, graph, importedOnly }, ...entries]),
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
