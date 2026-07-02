export type Lang = 'ko' | 'en' | 'zh' | 'ja'

export type SentimentRatio = {
  positive: number
  neutral: number
  negative: number
}

export type Topic = {
  label: string
  labelEn?: string
  mentionCount: number
  sentiment: SentimentRatio
}

export type TimelinePoint = {
  label: string
  positive: number
  neutral: number
  negative: number
}

export type KeyInsight = {
  type: 'positive' | 'negative'
  topic: string
  comment: string
  commentEn?: string
  likes: number
}

export type VideoInfo = {
  videoId: string
  title: string
  channelTitle: string
  thumbnailUrl: string
  publishedAt: string
  viewCount: number
  likeCount: number
  analyzedComments: number
  languageRatio: { ko: number; en: number; other: number }
  weightedSentiment?: number
}

export type InsightData = {
  video: VideoInfo
  topics: Topic[]
  reactionTimeline: TimelinePoint[]
  keyInsights: KeyInsight[]
}

export type HistoryItem = {
  videoId: string
  title: string
  channelTitle: string
  thumbnailUrl: string
  publishedAt: string
  analyzedComments: number
  analyzedAt: string
  topTopics: string[]
  overallSentiment: { positive: number; negative: number }
}

export type TopicComment = {
  id: string
  authorName: string
  text: string
  likeCount: number
  publishedAt: string
  sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'
}
