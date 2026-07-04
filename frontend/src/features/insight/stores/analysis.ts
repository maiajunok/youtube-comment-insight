import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { InsightData } from '@/features/insight/types/insight'
import { API_BASE_URL } from '@/shared/api/client'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

// 백엔드 호출 없이 URL만으로 썸네일을 바로 보여주기 위한 최소한의 video id 추출
// (backend/youtube.py의 extract_video_id와 동일한 패턴만 커버)
function extractVideoId(url: string): string | null {
  try {
    const u = new URL(url)
    if (u.hostname === 'youtu.be' || u.hostname === 'www.youtu.be') {
      return u.pathname.slice(1).split('/')[0] || null
    }
    if (u.hostname.includes('youtube.com')) {
      if (u.pathname === '/watch') return u.searchParams.get('v')
      const m = u.pathname.match(/^\/shorts\/([^/?]+)/)
      if (m) return m[1]
    }
  } catch { /* invalid URL */ }
  return null
}

export type QueueItem = {
  url: string
  videoId: string | null
  onSave?: (videoId: string, data: InsightData) => void
}

export const useAnalysisStore = defineStore('analysis', () => {
  const isAnalyzing     = ref(false)
  const loadingStep     = ref('')
  const loadingProgress = ref(0)
  const result          = ref<InsightData | null>(null)
  const analysisError   = ref('')
  const missingKeyModal = ref<'youtube' | 'openai' | null>(null)
  const resultSource    = ref<'analysis' | 'history' | null>(null)
  const justFinished    = ref(false)
  const pendingVideoId  = ref<string | null>(null)

  // 분석 대기열 — 하나 분석 중일 때 추가로 제출된 URL은 각자의 onSave와 함께 여기 쌓였다가
  // 순서대로 자동 실행됨(항목마다 콜백을 따로 들고 있어야 서로 안 섞임)
  const queue = ref<QueueItem[]>([])

  // 현재 진행 중인 fetch를 취소할 수 있게 참조를 들고 있음(반응형일 필요 없음)
  let currentAbort: AbortController | null = null

  function submit(url: string, onSave?: (videoId: string, data: InsightData) => void) {
    if (isAnalyzing.value) {
      queue.value.push({ url, videoId: extractVideoId(url), onSave })
    } else {
      startAnalysis(url, onSave)
    }
  }

  function removeFromQueue(index: number) {
    queue.value.splice(index, 1)
  }

  function cancelCurrent() {
    currentAbort?.abort()
  }

  async function startAnalysis(
    url: string,
    onSave?: (videoId: string, data: InsightData) => void,
  ) {
    isAnalyzing.value     = true
    loadingStep.value     = ''
    loadingProgress.value = 0
    result.value          = null
    analysisError.value   = ''
    missingKeyModal.value = null
    pendingVideoId.value  = extractVideoId(url)

    const settings = useSettingsStore()
    const openaiKey  = localStorage.getItem('openai_key')  ?? ''
    const youtubeKey = localStorage.getItem('youtube_key') ?? ''

    const controller = new AbortController()
    currentAbort = controller

    try {
      const res = await fetch(`${API_BASE_URL}/insight`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(openaiKey  ? { 'X-OpenAI-Key':  openaiKey }  : {}),
          ...(youtubeKey ? { 'X-YouTube-Key': youtubeKey } : {}),
        },
        body: JSON.stringify({ url }),
        signal: controller.signal,
      })

      if (!res.ok || !res.body) throw new Error(messages[settings.lang].analysisFailed)

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer    = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() ?? ''

        for (const event of events) {
          const dataLine = event.split('\n').find(l => l.startsWith('data: '))
          if (!dataLine) continue
          try {
            const msg = JSON.parse(dataLine.slice(6))
            if (msg.step === 'done') {
              result.value       = msg.data
              resultSource.value = 'analysis'
              justFinished.value = true
              const videoId = msg.data?.video?.videoId
              if (videoId && onSave) onSave(videoId, msg.data)
            } else if (msg.step === 'error') {
              const M = messages[settings.lang]
              if (msg.code === 'MISSING_YOUTUBE_KEY') {
                missingKeyModal.value = 'youtube'
                analysisError.value   = M.missingYoutubeKey
              } else if (msg.code === 'MISSING_OPENAI_KEY') {
                missingKeyModal.value = 'openai'
                analysisError.value   = M.missingOpenaiKey
              } else {
                analysisError.value = msg.detail ?? M.analysisFailed
              }
            } else {
              loadingStep.value     = msg.step
              loadingProgress.value = msg.progress ?? 0
            }
          } catch { /* skip malformed SSE chunk */ }
        }
      }
    } catch (e: any) {
      // 사용자가 직접 취소한 경우엔 에러로 취급하지 않음
      if (e?.name !== 'AbortError') {
        analysisError.value = e?.message ?? messages[settings.lang].analysisFailed
      }
    } finally {
      if (currentAbort === controller) currentAbort = null
      isAnalyzing.value     = false
      loadingStep.value     = ''
      loadingProgress.value = 0
      pendingVideoId.value  = null

      // 대기열에 남은 게 있으면 이어서 자동 실행
      if (queue.value.length) {
        const next = queue.value.shift()!
        startAnalysis(next.url, next.onSave)
      }
    }
  }

  function setResult(data: InsightData) {
    result.value        = data
    resultSource.value  = 'history'
    analysisError.value = ''
  }

  function clearResult() {
    result.value        = null
    resultSource.value  = null
    analysisError.value = ''
    justFinished.value  = false
  }

  function closeMissingKeyModal() {
    missingKeyModal.value = null
  }

  return {
    isAnalyzing,
    loadingStep,
    loadingProgress,
    result,
    analysisError,
    missingKeyModal,
    resultSource,
    justFinished,
    pendingVideoId,
    queue,
    submit,
    removeFromQueue,
    cancelCurrent,
    startAnalysis,
    setResult,
    clearResult,
    closeMissingKeyModal,
  }
})
