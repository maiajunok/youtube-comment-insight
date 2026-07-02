import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { InsightData } from '@/features/insight/types/insight'
import { API_BASE_URL } from '@/shared/api/client'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

export const useAnalysisStore = defineStore('analysis', () => {
  const isAnalyzing     = ref(false)
  const loadingStep     = ref('')
  const loadingProgress = ref(0)
  const result          = ref<InsightData | null>(null)
  const analysisError   = ref('')
  const missingKeyModal = ref<'youtube' | 'openai' | null>(null)
  const resultSource    = ref<'analysis' | 'history' | null>(null)
  const justFinished    = ref(false)

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

    const settings = useSettingsStore()
    const openaiKey  = localStorage.getItem('openai_key')  ?? ''
    const youtubeKey = localStorage.getItem('youtube_key') ?? ''

    try {
      const res = await fetch(`${API_BASE_URL}/insight`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(openaiKey  ? { 'X-OpenAI-Key':  openaiKey }  : {}),
          ...(youtubeKey ? { 'X-YouTube-Key': youtubeKey } : {}),
        },
        body: JSON.stringify({ url }),
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
              setTimeout(() => { justFinished.value = false }, 6000)
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
      analysisError.value = e?.message ?? messages[settings.lang].analysisFailed
    } finally {
      isAnalyzing.value     = false
      loadingStep.value     = ''
      loadingProgress.value = 0
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
    startAnalysis,
    setResult,
    clearResult,
    closeMissingKeyModal,
  }
})
