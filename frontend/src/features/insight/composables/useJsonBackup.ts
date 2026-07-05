import type { CommentGraphData, InsightData } from '@/features/insight/types/insight'

// 사용자가 자기 PC에 백업해두고 나중에 다시 업로드하는 용도의 파일 포맷 — 서버에는 아무것도
// 전송되지 않음(insightApi 호출 없이 순수 클라이언트 사이드 다운로드/파싱). schemaVersion은
// 나중에 포맷이 바뀌어도 옛날 파일을 계속 읽을 수 있게 하기 위한 최소한의 안전장치.
export type ReactionAnalysisBackup = {
  schemaVersion: 1
  exportedAt: string
  videoId: string
  videoUrl: string
  data: InsightData
  graph: CommentGraphData | null
}

export function buildBackup(data: InsightData, graph: CommentGraphData | null): ReactionAnalysisBackup {
  const videoId = data.video.videoId
  return {
    schemaVersion: 1,
    exportedAt: new Date().toISOString(),
    videoId,
    videoUrl: `https://www.youtube.com/watch?v=${videoId}`,
    data,
    graph,
  }
}

export function downloadBackup(backup: ReactionAnalysisBackup) {
  const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${backup.videoId}_reaction-analysis.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 형식이 안 맞는 파일(다른 JSON, 손상된 파일 등)을 조용히 걸러내기 위한 최소 검증 —
// data.video.videoId와 data.topics 배열만 있으면 나머지(그래프, exportedAt 등)는 없어도
// 복원 가능한 정도로 관대하게 봄
export function parseBackup(raw: string): ReactionAnalysisBackup | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  const obj = parsed as Partial<ReactionAnalysisBackup> | null
  const data = obj?.data
  if (!data || typeof data !== 'object') return null
  if (!data.video?.videoId || !Array.isArray(data.topics)) return null
  // 토픽 배열 자체는 있어도 각 항목이 기대하는 필드(mentionCount, sentiment)를 안 갖췄으면
  // 히스토리 목록 렌더링(감정 비율 계산)에서 죽을 수 있으므로 여기서 미리 걸러냄
  const topicsValid = data.topics.every(t =>
    t && typeof t.mentionCount === 'number' &&
    t.sentiment && typeof t.sentiment.positive === 'number' && typeof t.sentiment.negative === 'number',
  )
  if (!topicsValid) return null

  return {
    schemaVersion: 1,
    exportedAt: obj?.exportedAt ?? new Date().toISOString(),
    videoId: data.video.videoId,
    videoUrl: obj?.videoUrl ?? `https://www.youtube.com/watch?v=${data.video.videoId}`,
    data,
    graph: obj?.graph ?? null,
  }
}
