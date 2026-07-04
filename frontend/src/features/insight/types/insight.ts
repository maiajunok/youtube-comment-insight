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

export type CommentGraphNode = {
  id: string
  text: string
  likeCount: number
  sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'
  topic: string
  // UMAP으로 미리 투영해둔 좌표 — force-directed 시뮬레이션 대신 이 위치에 고정해서
  // 실제 임베딩 공간의 이웃 구조를 그대로 보여줌. 이 필드가 없으면(옛 캐시) 물리 시뮬레이션으로 폴백.
  // x2d/y2d는 3d 좌표를 눌러 찍은 게 아니라 2D로 독립적으로 다시 투영한 값(2D 화면 표시용)
  x?: number
  y?: number
  z?: number
  x2d?: number
  y2d?: number
}

export type CommentGraphLink = {
  source: string
  target: string
  similarity: number
}

export type CommentGraphData = {
  nodes: CommentGraphNode[]
  links: CommentGraphLink[]
}

export type VideoGraphNode = {
  id: string
  title: string
  thumbnailUrl: string
  commentCount: number
  sentiment: SentimentRatio
  topics: string[]
  hasGraph: boolean
  x?: number
  y?: number
  z?: number
  x2d?: number
  y2d?: number
}

export type VideoGraphLink = {
  source: string
  target: string
  similarity: number
}

export type VideoGraphData = {
  nodes: VideoGraphNode[]
  links: VideoGraphLink[]
}
