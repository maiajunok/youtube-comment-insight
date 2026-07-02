import type { InsightData, HistoryItem, TopicComment } from '@/features/insight/types/insight'
import { httpClient as instance } from '@/shared/api/client'

export const insightApi = {
  async getInsight(url?: string): Promise<InsightData> {
    const { data } = await instance.post<InsightData>('/insight', { url })
    return data
  },
  async getHistory(): Promise<HistoryItem[]> {
    const { data } = await instance.get<HistoryItem[]>('/history')
    return data
  },
  async getByVideoId(videoId: string): Promise<InsightData> {
    const { data } = await instance.get<InsightData>(`/history/${videoId}`)
    return data
  },
  async deleteCache(videoId: string): Promise<void> {
    await instance.post(`/refresh/${videoId}`)
  },
  async getStats(): Promise<{
    totalAnalyses: number
    totalComments: number
    totalTokens: number
    totalCostUsd: number
    avgDuration: number | null
    minDuration: number | null
    maxDuration: number | null
    records: {
      videoId: string
      title: string
      analyzedComments: number
      analyzedAt: string
      duration: number | null
      totalTokens: number | null
      estimatedCostUsd: number | null
    }[]
  }> {
    const { data } = await instance.get('/stats')
    return data
  },
  async translateLabels(labels: string[], targetLang: string = 'en'): Promise<string[]> {
    const { data } = await instance.post<{ translations: string[] }>('/translate-labels', { labels, target_lang: targetLang })
    return data.translations
  },
  async translateComments(texts: string[], targetLang: string = 'en'): Promise<string[]> {
    const { data } = await instance.post<{ translations: string[] }>('/translate-comments', { texts, target_lang: targetLang })
    return data.translations
  },
  async getTopicComments(
    videoId: string,
    topic: string,
    sentiment = 'all',
  ): Promise<{ comments: TopicComment[]; total: number; counts: Record<string, number> }> {
    const { data } = await instance.get(`/comments/${videoId}`, {
      params: { topic, sentiment },
    })
    return data
  },
}
