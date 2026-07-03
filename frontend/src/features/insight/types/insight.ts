export type Lang = 'ko' | 'en' | 'zh' | 'ja'

export type SentimentRatio = {
  positive: number
  neutral: number
  negative: number
}

export type Topic = {
  label: string
  labelEn?: string
  labelZh?: string
  labelJa?: string
  mentionCount: number
  sentiment: SentimentRatio
}

export type TopicLabel = {
  label: string
  labelEn?: string
  labelZh?: string
  labelJa?: string
}

export type TimelinePoint = {
  label?: string
  elapsedSeconds?: number | null
  bucketStart?: string
  bucketEnd?: string
  positive: number
  neutral: number
  negative: number
  netSentiment?: number
  zScore?: number
  isBurst?: boolean
  direction?: 'POSITIVE_SPIKE' | 'NEGATIVE_SPIKE' | null
  topComments?: { text: string; likeCount: number; sentiment: string }[]
}

export type KeyInsight = {
  type: 'positive' | 'negative'
  topic: string
  topicEn?: string
  topicZh?: string
  topicJa?: string
  comment: string
  commentLang?: 'ko' | 'en' | 'zh' | 'ja' | null
  commentEn?: string
  commentZh?: string
  commentJa?: string
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
  analyzedAt?: string
}

export type HistoryItem = {
  videoId: string
  title: string
  channelTitle: string
  thumbnailUrl: string
  publishedAt: string
  analyzedComments: number
  analyzedAt: string
  topTopics: TopicLabel[]
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
