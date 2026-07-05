import type { Lang } from '@/features/insight/types/insight'

export interface UIMessages {
  // 네비게이션
  navHome: string
  navHistory: string
  navCompare: string
  navNetwork: string
  navHowto: string
  navStats: string
  navSettings: string
  // VideoInfoCard
  uploadDate: string
  views: string
  likes: string
  analyzedComments: string
  languageRatio: string
  analysisNote: string
  analyzedAtLabel: string
  reAnalyze: string
  // TopReactionTopics
  topReactionTopics: string
  totalMentions: string
  positive: string
  neutral: string
  negative: string
  clickHint: string
  // ReactionTimeline
  sentimentTrend: string
  reactionSub: string
  byHour: string
  reactionFlow: string
  anomalyDetected: string
  positiveSpike: string
  negativeSpike: string
  netSentimentLabel: string
  normalRangeLabel: string
  netSentimentTrend: string
  netSentimentAnomalyLabel: string
  netSentimentSub: string
  // KeyInsights
  keyInsights: string
  positiveLabel: string
  negativeLabel: string
  likesLabel: string
  langBreakdown: string
  disclaimer: string
  // HomeView
  communityAnalysis: string
  urlPlaceholder: string
  analyzeBtn: string
  urlHint: string
  backToHistory: string
  newAnalysis: string
  moreInsights: string
  // HistoryView
  historyTitle: string
  historySub: string
  loading: string
  emptyHistory: string
  goAnalyze: string
  viewBtn: string
  deleteBtn: string
  sortDate: string
  sortPos: string
  sortNeg: string
  sortPub: string
  // 분석 지표
  sentimentScore: string
  sentimentScoreDesc: string
  commentRate: string
  commentRateDesc: string
  likeRate: string
  likeRateDesc: string
  controversy: string
  controversyDesc: string
  weightedSentiment: string
  weightedSentimentDesc: string
  // CompareView
  compareSub: string
  compareBtn: string
  comparing: string
  compareNone: string
  reselect: string
  sectionBasic: string
  sectionSentiment: string
  sectionTopics: string
  sectionCommonTopics: string
  sectionAnalysisMetrics: string
  sectionLangDist: string
  colTopic: string
  colCommon: string
  overallLabel: string
  colCommentCount: string
  // StatsView
  statsSub: string
  totalAnalyses: string
  totalComments: string
  totalTokens: string
  avgDuration: string
  minDuration: string
  maxDuration: string
  avgPer100: string
  videoRecords: string
  colVideo: string
  colDuration: string
  colPer100: string
  colDate: string
  noRecords: string
  backendError: string
  // HowToView
  howtoEyebrow: string
  howtoTitle: string
  howtoSub: string
  techStackLabel: string
  notesLabel: string
  // LoadingState
  loadingTitle: string
  loadingStep1Label: string
  loadingStep1Sub: string
  loadingStep2Label: string
  loadingStep2Sub: string
  loadingStep3Label: string
  loadingStep3Sub: string
  // 분석 대기열
  queueRemove: string
  queueAddBtn: string
  cancelAnalysisBtn: string
  confirmCancelAnalysisTitle: string
  confirmCancelAnalysisBody: string
  confirmCancelQueuedTitle: string
  confirmCancelQueuedBody: string
  // NetworkView (반응 지도)
  networkSub: string
  networkNoGraph: string
  networkReanalyzeBtn: string
  networkMethodTitle: string
  networkPipeline1Title: string
  networkPipeline1Sub: string
  networkPipeline2Title: string
  networkPipeline2Sub: string
  networkPipeline3Title: string
  networkPipeline3Sub: string
  networkPipeline4Title: string
  networkPipeline4Sub: string
  networkPipeline5Title: string
  networkPipeline5Sub: string
  networkEdgeCardTitle: string
  networkEdgeReasonComment: string
  networkEdgeReasonTopic: string
  networkEdgeReasonNoTopic: string
  networkThumbGoToHistory: string
  networkSortCluster: string
  networkSortComments: string
  networkSortPositive: string
  networkSortNegative: string
  networkSortNewest: string
  networkBack: string
  networkResetView: string
  networkLegendOverview: string
  networkLegendDetail: string
  networkPanelSimilarVideos: string
  networkPanelSimilarComments: string
  networkPanelViewCommentsBtn: string
  networkBackToList: string
  networkListVideos: string
  networkTopicSampleNote: string
  networkListUnavailable: string
  // SettingsView
  settingsTitle: string
  settingsSub: string
  byokNotice: string
  openaiKeyLabel: string
  openaiKeyHint: string
  youtubeKeyLabel: string
  youtubeKeyHint: string
  keyPlaceholder: string
  saveBtn: string
  savedToast: string
  clearBtn: string
  keyStoredLocally: string
  missingYoutubeKey: string
  missingOpenaiKey: string
  analysisFailed: string
  fieldSaved: string
  fieldDeleted: string
  currentlySaved: string
  notSaved: string
  // Missing-key modal
  keyModalTitle: string
  keyModalBody1: string
  keyModalBody2: string
  keyModalSettingsBtn: string
  keyModalHistoryBtn: string
  keyModalClose: string
  // TopicComments
  topicCommentsLabel: string
  filterAll: string
  anonymousAuthor: string
  noCommentsFound: string
  totalCommentsFooter: string
  commentsLoadFailed: string
  originalCommentLabel: string
  // Delete confirmation
  confirmDeleteTitle: string
  confirmDeleteBody: string
  confirmDeleteBtn: string
  cancelBtn: string
  deleteFailed: string
  // PDF Report
  reportBrandTagline: string
  reportGeneratedOn: string
  overallSentimentDistribution: string
  reportFooterNote: string
  // App footer
  footerDescription: string
  footerDisclaimer: string
}

export const messages: Record<Lang, UIMessages> = {
  ko: {
    navHome: '홈',
    navHistory: '분석 기록',
    navCompare: '영상 비교',
    navNetwork: '반응 지도',
    navHowto: '작동 방식',
    navStats: '분석 통계',
    navSettings: '설정',
    uploadDate: '업로드 일자',
    views: '조회수',
    likes: '좋아요',
    analyzedComments: '분석된 댓글',
    languageRatio: '언어 비율',
    analysisNote: '유튜브 공개 댓글 API 기반 분석',
    analyzedAtLabel: '분석일자',
    reAnalyze: '다시 분석하기',
    topReactionTopics: '상위 반응 토픽',
    totalMentions: '총 언급수',
    positive: '긍정',
    neutral: '중립',
    negative: '부정',
    clickHint: '클릭하면 댓글 보기',
    sentimentTrend: '감정 반응 트렌드',
    reactionSub: '업로드 후 시간대별 댓글 반응',
    byHour: '시간별',
    reactionFlow: '반응 흐름',
    anomalyDetected: '이상치 감지',
    positiveSpike: '긍정 급상승',
    negativeSpike: '부정 급상승',
    netSentimentLabel: '순 감정 점수',
    normalRangeLabel: '정상 범위',
    netSentimentTrend: '순감정 지수',
    netSentimentAnomalyLabel: '이상치 탐지',
    netSentimentSub: '평균 ± 표준편차를 벗어나면 이상치로 표시 (z-score 기반)',
    keyInsights: '주요 인사이트',
    positiveLabel: '↑ 긍정',
    negativeLabel: '↓ 부정',
    likesLabel: '좋아요',
    langBreakdown: '언어 분포',
    disclaimer: '이 분석은 유튜브 공개 API로 수집 가능한 댓글에 한합니다. 삭제·숨김·신고된 댓글은 포함되지 않습니다.',
    communityAnalysis: '커뮤니티 반응 분석',
    urlPlaceholder: 'YouTube URL을 붙여넣기 하세요...',
    analyzeBtn: '분석하기',
    urlHint: 'youtu.be/... 또는 youtube.com/watch?v=... 형식 지원',
    backToHistory: '분석 기록으로',
    newAnalysis: '새 분석',
    moreInsights: '↓ 더 많은 인사이트',
    historyTitle: '분석 기록',
    historySub: '그동안 분석한 영상들을 한곳에 모아뒀어요',
    loading: '불러오는 중...',
    emptyHistory: '아직 분석한 영상이 없습니다',
    goAnalyze: '지금 분석하러 가기',
    viewBtn: '보기',
    deleteBtn: '삭제',
    sortDate: '분석 최신순',
    sortPos: '긍정 높은순',
    sortNeg: '부정 높은순',
    sortPub: '영상 최신순',
    sentimentScore: '감정 점수',
    sentimentScoreDesc: '긍정% − 부정%',
    commentRate: '댓글 반응률',
    commentRateDesc: '댓글 ÷ 조회수',
    likeRate: '좋아요율',
    likeRateDesc: '좋아요 ÷ 조회수',
    controversy: '논쟁성',
    controversyDesc: '의견 분열 정도',
    weightedSentiment: '가중 감정',
    weightedSentimentDesc: '좋아요 가중 평균',
    compareSub: '분석된 영상 중 2~3개를 선택하세요',
    compareBtn: '비교하기',
    comparing: '로딩 중…',
    compareNone: '비교할 분석 기록이 없습니다.',
    reselect: '다시 선택',
    sectionBasic: '기본 정보',
    sectionSentiment: '감정 분포',
    sectionTopics: '상위 토픽',
    sectionCommonTopics: '공통 주제',
    sectionAnalysisMetrics: '분석 지표',
    sectionLangDist: '언어 분포',
    colTopic: '토픽',
    colCommon: '공통',
    overallLabel: '전체',
    colCommentCount: '분석 댓글',
    statsSub: '이 서버에서 분석된 모든 영상의 소요 시간 및 처리량 기록',
    totalAnalyses: '총 분석 횟수',
    totalComments: '총 분석 댓글',
    totalTokens: '총 사용 토큰',
    avgDuration: '평균 소요 시간',
    minDuration: '최단 소요 시간',
    maxDuration: '최장 소요 시간',
    avgPer100: '100댓글당 평균',
    videoRecords: '영상별 분석 기록',
    colVideo: '영상',
    colDuration: '소요 시간',
    colPer100: '100댓글당',
    colDate: '분석 날짜',
    noRecords: '아직 분석 기록이 없습니다.',
    backendError: '백엔드 서버에 연결할 수 없습니다.',
    howtoEyebrow: '시스템 아키텍처',
    howtoTitle: '어떻게 작동하나요?',
    howtoSub: 'YouTube URL 하나로 모든 댓글을 AI가 자동으로 분석합니다',
    techStackLabel: '기술 스택',
    notesLabel: '유의사항',
    loadingTitle: '분석 중입니다...',
    loadingStep1Label: '댓글 수집 중',
    loadingStep1Sub: 'YouTube API에서 댓글을 가져오는 중입니다',
    loadingStep2Label: '감정 분석 중',
    loadingStep2Sub: 'AI가 각 댓글의 감정을 판단합니다',
    loadingStep3Label: '토픽 분류 중',
    loadingStep3Sub: '주요 반응 토픽을 분류하고 집계합니다',
    queueRemove: '취소',
    queueAddBtn: '추가',
    cancelAnalysisBtn: '취소하기',
    confirmCancelAnalysisTitle: '분석을 취소할까요?',
    confirmCancelAnalysisBody: '지금 취소하면 진행 중이던 분석이 중단되고, 다시 보려면 처음부터 재분석해야 합니다.',
    confirmCancelQueuedTitle: '대기열에서 삭제할까요?',
    confirmCancelQueuedBody: '삭제하면 대기열에서 빠지고, 다시 분석하려면 URL을 다시 입력해야 합니다.',
    networkSub: '분석된 영상들을 반응(긍정·부정)에 따라 3D로 배치한 지도입니다. 영상을 클릭하면 그 안의 댓글 반응 지도로 들어갑니다',
    networkNoGraph: '이 영상은 반응 지도 데이터가 없습니다. 다시 분석해주세요.',
    networkReanalyzeBtn: '다시 분석하기',
    networkMethodTitle: '분석 파이프라인',
    networkPipeline1Title: '텍스트 정규화',
    networkPipeline1Sub: '같은 대상을 가리키는 여러 표현(별칭·줄임말 등)을 하나로 통일해요',
    networkPipeline2Title: 'Embedding',
    networkPipeline2Sub: '제목·토픽 또는 댓글 텍스트를 벡터로 변환해요',
    networkPipeline3Title: 'Cosine Similarity',
    networkPipeline3Sub: '벡터 간 각도로 얼마나 비슷한 반응인지 계산해요',
    networkPipeline4Title: '상호 k-NN Graph',
    networkPipeline4Sub: '서로를 이웃으로 꼽을 때만 선으로 연결해요',
    networkPipeline5Title: 'UMAP',
    networkPipeline5Sub: '가까운 벡터끼리 가깝게, 2차원 지도 위에 배치해요',
    networkEdgeCardTitle: '연결 분석',
    networkEdgeReasonComment: '두 댓글이 의미적으로 비슷해서, 서로가 서로를 가장 가까운 이웃으로 골라 연결됐어요.',
    networkEdgeReasonTopic: '공통 토픽({topics})을 다루고 반응 패턴도 비슷해서 연결됐어요.',
    networkEdgeReasonNoTopic: '다루는 토픽은 다르지만, 제목·감정 반응의 패턴이 비슷해서 연결됐어요.',
    networkThumbGoToHistory: '분석 기록 보기',
    networkSortCluster: '지도 그룹순',
    networkSortComments: '댓글 많은 순',
    networkSortPositive: '긍정률 높은 순',
    networkSortNegative: '부정률 높은 순',
    networkSortNewest: '최신순',
    networkBack: '전체 지도로',
    networkResetView: '보기 초기화',
    networkLegendOverview: '원 = 영상 · 크기 = 댓글 수 · 색 = 비슷한 반응 그룹 · 선 = 비슷한 반응',
    networkLegendDetail: '원 = 댓글 · 크기 = 좋아요 수 · 색 = 토픽 · 선 = 의미 유사도',
    networkPanelSimilarVideos: '비슷한 반응의 영상',
    networkPanelSimilarComments: '비슷한 댓글',
    networkPanelViewCommentsBtn: '댓글 반응 지도 보기',
    networkBackToList: '목록으로',
    networkListVideos: '분석된 영상',
    networkTopicSampleNote: '그래프 가독성과 임베딩 비용 때문에 토픽당 좋아요 상위 30개 댓글만 표시돼요(감정·토픽 분석 자체는 전체 댓글 기준)',
    networkListUnavailable: '댓글 반응 지도 없음',
    settingsTitle: '설정',
    settingsSub: '새 영상을 분석하려면 본인의 API 키가 필요합니다',
    byokNotice: '이 사이트는 방문자가 직접 발급받은 API 키로 새 영상을 분석합니다. 키는 브라우저(localStorage)에만 저장되며, 분석 요청 시 헤더로만 전송되고 서버에 저장되지 않습니다. 키 없이도 기존에 분석된 영상 기록·통계·비교는 자유롭게 볼 수 있습니다.',
    openaiKeyLabel: 'OpenAI API 키',
    openaiKeyHint: 'platform.openai.com/api-keys 에서 발급',
    youtubeKeyLabel: 'YouTube Data API 키',
    youtubeKeyHint: 'Google Cloud Console에서 YouTube Data API v3 사용 설정 후 발급',
    keyPlaceholder: '키를 입력하세요',
    saveBtn: '저장',
    savedToast: '저장되었습니다',
    clearBtn: '삭제',
    keyStoredLocally: '이 브라우저에만 저장됩니다',
    missingYoutubeKey: 'YouTube API 키가 필요합니다. 설정 페이지에서 본인의 키를 입력해주세요.',
    missingOpenaiKey: 'OpenAI API 키가 필요합니다. 설정 페이지에서 본인의 키를 입력해주세요.',
    analysisFailed: '분석 중 오류가 발생했습니다.',
    fieldSaved: '저장됨',
    fieldDeleted: '삭제됨',
    currentlySaved: '이 브라우저에 저장되어 있음',
    notSaved: '저장된 키 없음',
    keyModalTitle: 'API 키가 필요해요',
    keyModalBody1: '새 영상을 분석하려면 본인의 YouTube Data API 키와 OpenAI API 키(유료)가 필요합니다. 설정 페이지에서 입력하면 이 브라우저에만 저장됩니다.',
    keyModalBody2: '키가 없어도 이미 분석된 영상의 기록·통계·비교는 자유롭게 볼 수 있어요.',
    keyModalSettingsBtn: '설정으로 이동',
    keyModalHistoryBtn: '분석 기록 보기',
    keyModalClose: '닫기',
    topicCommentsLabel: '토픽 댓글',
    filterAll: '전체',
    anonymousAuthor: '익명',
    noCommentsFound: '해당 댓글이 없습니다',
    totalCommentsFooter: '총 {n}개 댓글 · 좋아요 순 정렬',
    commentsLoadFailed: '댓글을 불러오지 못했습니다.',
    originalCommentLabel: '원문',
    confirmDeleteTitle: '분석 기록을 삭제할까요?',
    confirmDeleteBody: '삭제하면 캐시된 분석 결과가 서버에서 완전히 지워지고 되돌릴 수 없습니다. 다시 보려면 처음부터 재분석해야 합니다.',
    confirmDeleteBtn: '삭제',
    cancelBtn: '취소',
    deleteFailed: '삭제에 실패했습니다.',
    reportBrandTagline: 'Community Reaction Analysis',
    reportGeneratedOn: '생성일',
    overallSentimentDistribution: '전체 감정 분포',
    reportFooterNote: '유튜브 공개 댓글 API 기반 분석',
    footerDescription: '유튜브 댓글을 AI로 분석해 감정과 반응을 한눈에 보여주는 대시보드입니다. 서초구청 × T1 e스포츠 개발자 아카데미 과정에서 제작했습니다.',
    footerDisclaimer: '현재 분석 결과의 정확도는 검증되지 않았습니다. GPT 기반 분류이므로 실제와 다를 수 있습니다.',
  },

  en: {
    navHome: 'Home',
    navHistory: 'History',
    navCompare: 'Compare',
    navNetwork: 'Reaction Map',
    navHowto: 'How It Works',
    navStats: 'Stats',
    navSettings: 'Settings',
    uploadDate: 'Upload Date',
    views: 'Views',
    likes: 'Likes',
    analyzedComments: 'Analyzed Comments',
    languageRatio: 'Language Ratio',
    analysisNote: 'Based on public YouTube comments available via API',
    analyzedAtLabel: 'Analyzed At',
    reAnalyze: 'Re-analyze',
    topReactionTopics: 'Top Reaction Topics',
    totalMentions: 'Total Mentions',
    positive: 'Positive',
    neutral: 'Neutral',
    negative: 'Negative',
    clickHint: 'Click to view comments',
    sentimentTrend: 'Sentiment Trend',
    reactionSub: 'Based on comment publish time after upload',
    byHour: 'By Hour',
    reactionFlow: 'Reaction Flow',
    anomalyDetected: 'Anomaly Detected',
    positiveSpike: 'Positive Spike',
    negativeSpike: 'Negative Spike',
    netSentimentLabel: 'Net Sentiment',
    normalRangeLabel: 'Normal Range',
    netSentimentTrend: 'Net Sentiment Index',
    netSentimentAnomalyLabel: 'Anomaly Detection',
    netSentimentSub: 'Flagged as anomaly when it moves outside mean ± std dev (z-score based)',
    keyInsights: 'Key Insights',
    positiveLabel: '↑ Positive',
    negativeLabel: '↓ Negative',
    likesLabel: 'likes',
    langBreakdown: 'Language Breakdown',
    disclaimer: 'This analysis is based on public YouTube comments available via API. Deleted, hidden, or moderated comments are not included.',
    communityAnalysis: 'Community Reaction Analysis',
    urlPlaceholder: 'Paste a YouTube URL...',
    analyzeBtn: 'Analyze',
    urlHint: 'Supports youtu.be/... or youtube.com/watch?v=... format',
    backToHistory: 'Back to History',
    newAnalysis: 'New Analysis',
    moreInsights: '↓ More Insights',
    historyTitle: 'Analysis History',
    historySub: 'Video analysis results saved in server cache',
    loading: 'Loading...',
    emptyHistory: 'No analyzed videos yet',
    goAnalyze: 'Start Analyzing',
    viewBtn: 'View',
    deleteBtn: 'Delete',
    sortDate: 'Newest Analysis',
    sortPos: 'Most Positive',
    sortNeg: 'Most Negative',
    sortPub: 'Newest Video',
    sentimentScore: 'Sentiment Score',
    sentimentScoreDesc: 'positive% − negative%',
    commentRate: 'Comment Rate',
    commentRateDesc: 'comments ÷ views',
    likeRate: 'Like Rate',
    likeRateDesc: 'likes ÷ views',
    controversy: 'Controversy',
    controversyDesc: 'opinion divide degree',
    weightedSentiment: 'Weighted Sentiment',
    weightedSentimentDesc: 'like-weighted average',
    compareSub: 'Select 2–3 videos from your analysis history',
    compareBtn: 'Compare',
    comparing: 'Loading…',
    compareNone: 'No analysis records to compare.',
    reselect: 'Re-select',
    sectionBasic: 'Basic Info',
    sectionSentiment: 'Sentiment Distribution',
    sectionTopics: 'Top Topics',
    sectionCommonTopics: 'Common Topics',
    sectionAnalysisMetrics: 'Analysis Metrics',
    sectionLangDist: 'Language Distribution',
    colTopic: 'Topics',
    colCommon: 'Common',
    overallLabel: 'Overall',
    colCommentCount: 'Comments',
    statsSub: 'Duration and throughput records for all analyzed videos on this server',
    totalAnalyses: 'Total Analyses',
    totalComments: 'Total Comments',
    totalTokens: 'Total Tokens',
    avgDuration: 'Avg Duration',
    minDuration: 'Min Duration',
    maxDuration: 'Max Duration',
    avgPer100: 'Avg per 100 comments',
    videoRecords: 'Per-Video Records',
    colVideo: 'Video',
    colDuration: 'Duration',
    colPer100: 'per 100',
    colDate: 'Analysis Date',
    noRecords: 'No analysis records yet.',
    backendError: 'Cannot connect to backend server.',
    howtoEyebrow: 'System Architecture',
    howtoTitle: 'How does it work?',
    howtoSub: 'AI automatically analyzes all comments from a single YouTube URL',
    techStackLabel: 'Tech Stack',
    notesLabel: 'Notes',
    loadingTitle: 'Analyzing...',
    loadingStep1Label: 'Collecting Comments',
    loadingStep1Sub: 'Fetching comments from the YouTube API',
    loadingStep2Label: 'Analyzing Sentiment',
    loadingStep2Sub: 'AI is judging the sentiment of each comment',
    loadingStep3Label: 'Classifying Topics',
    loadingStep3Sub: 'Grouping and tallying the main reaction topics',
    queueRemove: 'Cancel',
    queueAddBtn: 'Add',
    cancelAnalysisBtn: 'Cancel analysis',
    confirmCancelAnalysisTitle: 'Cancel this analysis?',
    confirmCancelAnalysisBody: 'Cancelling now stops the analysis in progress — you\'ll need to start over from scratch to see it again.',
    confirmCancelQueuedTitle: 'Remove from the queue?',
    confirmCancelQueuedBody: 'Removing it drops it from the queue — you\'ll need to re-enter the URL to analyze it again.',
    networkSub: 'A 3D map of your analyzed videos positioned by reaction (positive/negative). Click a video to enter its comment reaction map',
    networkNoGraph: 'This video has no reaction map data. Please re-analyze it.',
    networkReanalyzeBtn: 'Re-analyze',
    networkMethodTitle: 'Analysis Pipeline',
    networkPipeline1Title: 'Text normalization',
    networkPipeline1Sub: 'Merges different ways of referring to the same thing (aliases, abbreviations) into one form',
    networkPipeline2Title: 'Embedding',
    networkPipeline2Sub: 'Converts titles/topics or comment text into vectors',
    networkPipeline3Title: 'Cosine Similarity',
    networkPipeline3Sub: 'Measures how similar the reactions are by vector angle',
    networkPipeline4Title: 'Mutual k-NN Graph',
    networkPipeline4Sub: 'Only connects nodes that pick each other as neighbors',
    networkPipeline5Title: 'UMAP',
    networkPipeline5Sub: 'Projects nearby vectors to nearby points on a 2D map',
    networkEdgeCardTitle: 'Connection analysis',
    networkEdgeReasonComment: 'These two comments are semantically similar, and each picked the other as a nearest neighbor.',
    networkEdgeReasonTopic: 'They share the topic(s) {topics} and have a similar reaction pattern.',
    networkEdgeReasonNoTopic: 'They don\'t share a topic, but the title/sentiment pattern is similar enough to connect them.',
    networkThumbGoToHistory: 'View analysis record',
    networkSortCluster: 'Map group order',
    networkSortComments: 'Most comments',
    networkSortPositive: 'Highest positive %',
    networkSortNegative: 'Highest negative %',
    networkSortNewest: 'Newest',
    networkBack: 'Back to overview',
    networkResetView: 'Reset view',
    networkLegendOverview: 'circle = video · size = comment count · color = similar-reaction group · line = similar reaction',
    networkLegendDetail: 'circle = comment · size = like count · color = topic · line = semantic similarity',
    networkPanelSimilarVideos: 'Similar-reaction videos',
    networkPanelSimilarComments: 'Similar comments',
    networkPanelViewCommentsBtn: 'View Comment Reaction Map',
    networkBackToList: 'Back to list',
    networkListVideos: 'Analyzed videos',
    networkTopicSampleNote: 'Only the top 30 most-liked comments per topic are shown here for graph readability and embedding cost (sentiment/topic analysis itself still covers all comments)',
    networkListUnavailable: 'No comment map yet',
    settingsTitle: 'Settings',
    settingsSub: 'Bring your own API keys to analyze new videos',
    byokNotice: 'This site uses your own API keys to analyze new videos. Keys are stored only in your browser (localStorage), sent solely as request headers, and never stored on the server. Existing analysis history, stats, and comparisons remain viewable without any key.',
    openaiKeyLabel: 'OpenAI API Key',
    openaiKeyHint: 'Get one at platform.openai.com/api-keys',
    youtubeKeyLabel: 'YouTube Data API Key',
    youtubeKeyHint: 'Enable YouTube Data API v3 in Google Cloud Console to get one',
    keyPlaceholder: 'Enter your key',
    saveBtn: 'Save',
    savedToast: 'Saved',
    clearBtn: 'Clear',
    keyStoredLocally: 'Stored only in this browser',
    missingYoutubeKey: 'A YouTube API key is required. Please enter your own key on the Settings page.',
    missingOpenaiKey: 'An OpenAI API key is required. Please enter your own key on the Settings page.',
    analysisFailed: 'An error occurred during analysis.',
    fieldSaved: 'Saved',
    fieldDeleted: 'Deleted',
    currentlySaved: 'Saved in this browser',
    notSaved: 'No key saved',
    keyModalTitle: 'API Keys Required',
    keyModalBody1: 'Analyzing a new video requires your own YouTube Data API key and OpenAI API key (paid). Enter them on the Settings page — they\'re stored only in this browser.',
    keyModalBody2: 'You can still freely browse existing analysis history, stats, and comparisons without any key.',
    keyModalSettingsBtn: 'Go to Settings',
    keyModalHistoryBtn: 'View History',
    keyModalClose: 'Close',
    topicCommentsLabel: 'Topic Comments',
    filterAll: 'All',
    anonymousAuthor: 'Anonymous',
    noCommentsFound: 'No comments found',
    totalCommentsFooter: '{n} comments total · sorted by likes',
    commentsLoadFailed: 'Failed to load comments.',
    originalCommentLabel: 'Original',
    confirmDeleteTitle: 'Delete this analysis?',
    confirmDeleteBody: 'This permanently removes the cached analysis from the server and cannot be undone. You\'ll need to re-analyze from scratch to see it again.',
    confirmDeleteBtn: 'Delete',
    cancelBtn: 'Cancel',
    deleteFailed: 'Failed to delete.',
    reportBrandTagline: 'Community Reaction Analysis',
    reportGeneratedOn: 'Generated',
    overallSentimentDistribution: 'Overall Sentiment Distribution',
    reportFooterNote: 'Based on public YouTube comments via API',
    footerDescription: 'An AI-powered dashboard that analyzes YouTube comments to surface sentiment and reactions at a glance. Built during the Seocho e-Sports Developer Academy (Seocho District Office × T1 Esports).',
    footerDisclaimer: 'The accuracy of current analysis results has not been independently validated. Since classification is GPT-based, it may differ from the ground truth.',
  },

  zh: {
    navHome: '首页',
    navHistory: '分析记录',
    navCompare: '视频对比',
    navNetwork: '反应地图',
    navHowto: '使用说明',
    navStats: '分析统计',
    navSettings: '设置',
    uploadDate: '上传日期',
    views: '浏览量',
    likes: '点赞数',
    analyzedComments: '分析评论数',
    languageRatio: '语言比例',
    analysisNote: '基于YouTube公开评论API分析',
    analyzedAtLabel: '分析日期',
    reAnalyze: '重新分析',
    topReactionTopics: '热门反应话题',
    totalMentions: '总提及数',
    positive: '正面',
    neutral: '中立',
    negative: '负面',
    clickHint: '点击查看评论',
    sentimentTrend: '情感反应趋势',
    reactionSub: '按上传后时间段的评论反应',
    byHour: '按小时',
    reactionFlow: '反应流',
    anomalyDetected: '检测到异常',
    positiveSpike: '正面反应激增',
    negativeSpike: '负面反应激增',
    netSentimentLabel: '净情感分数',
    normalRangeLabel: '正常范围',
    netSentimentTrend: '净情感指数',
    netSentimentAnomalyLabel: '异常检测',
    netSentimentSub: '超出平均值 ± 标准差范围时标记为异常（基于z-score）',
    keyInsights: '主要洞察',
    positiveLabel: '↑ 正面',
    negativeLabel: '↓ 负面',
    likesLabel: '点赞',
    langBreakdown: '语言分布',
    disclaimer: '本分析仅基于YouTube公开API可获取的评论。已删除、隐藏或举报的评论不包含在内。',
    communityAnalysis: '社区反应分析',
    urlPlaceholder: '粘贴YouTube链接...',
    analyzeBtn: '分析',
    urlHint: '支持 youtu.be/... 或 youtube.com/watch?v=... 格式',
    backToHistory: '返回记录',
    newAnalysis: '新分析',
    moreInsights: '↓ 更多洞察',
    historyTitle: '分析记录',
    historySub: '保存在服务器缓存中的视频分析结果',
    loading: '加载中...',
    emptyHistory: '还没有分析过的视频',
    goAnalyze: '开始分析',
    viewBtn: '查看',
    deleteBtn: '删除',
    sortDate: '最新分析',
    sortPos: '正面最高',
    sortNeg: '负面最高',
    sortPub: '最新视频',
    sentimentScore: '情感分数',
    sentimentScoreDesc: '正面% − 负面%',
    commentRate: '评论互动率',
    commentRateDesc: '评论 ÷ 浏览量',
    likeRate: '点赞率',
    likeRateDesc: '点赞 ÷ 浏览量',
    controversy: '争议度',
    controversyDesc: '意见分歧程度',
    weightedSentiment: '加权情感',
    weightedSentimentDesc: '点赞加权平均',
    compareSub: '从分析历史中选择2~3个视频',
    compareBtn: '对比',
    comparing: '加载中…',
    compareNone: '没有可对比的分析记录。',
    reselect: '重新选择',
    sectionBasic: '基本信息',
    sectionSentiment: '情感分布',
    sectionTopics: '热门话题',
    sectionCommonTopics: '共同话题',
    sectionAnalysisMetrics: '分析指标',
    sectionLangDist: '语言分布',
    colTopic: '话题',
    colCommon: '共同',
    overallLabel: '整体',
    colCommentCount: '分析评论',
    statsSub: '本服务器上所有分析视频的耗时及处理量记录',
    totalAnalyses: '总分析次数',
    totalComments: '总分析评论',
    totalTokens: '总使用Token',
    avgDuration: '平均耗时',
    minDuration: '最短耗时',
    maxDuration: '最长耗时',
    avgPer100: '每100条平均',
    videoRecords: '按视频分析记录',
    colVideo: '视频',
    colDuration: '耗时',
    colPer100: '每100条',
    colDate: '分析日期',
    noRecords: '暂无分析记录。',
    backendError: '无法连接到后端服务器。',
    howtoEyebrow: '系统架构',
    howtoTitle: '如何运作？',
    howtoSub: '通过单个YouTube链接，AI自动分析所有评论',
    techStackLabel: '技术栈',
    notesLabel: '注意事项',
    loadingTitle: '正在分析...',
    loadingStep1Label: '正在收集评论',
    loadingStep1Sub: '正在通过YouTube API获取评论',
    loadingStep2Label: '正在分析情感',
    loadingStep2Sub: 'AI正在判断每条评论的情感',
    loadingStep3Label: '正在分类话题',
    loadingStep3Sub: '正在分类并汇总主要反应话题',
    queueRemove: '取消',
    queueAddBtn: '添加',
    cancelAnalysisBtn: '取消',
    confirmCancelAnalysisTitle: '要取消这次分析吗？',
    confirmCancelAnalysisBody: '现在取消会中断正在进行的分析，之后需要重新从头分析才能再次查看。',
    confirmCancelQueuedTitle: '要从队列中删除吗？',
    confirmCancelQueuedBody: '删除后将从队列中移除，需要重新输入链接才能再次分析。',
    networkSub: '按反应（正面/负面）分布的已分析视频3D地图。点击视频可进入该视频的评论反应地图',
    networkNoGraph: '该视频没有反应地图数据，请重新分析。',
    networkReanalyzeBtn: '重新分析',
    networkMethodTitle: '分析流程',
    networkPipeline1Title: '文本归一化',
    networkPipeline1Sub: '把指代同一对象的不同说法（别名、缩写等）统一成一种表达',
    networkPipeline2Title: 'Embedding',
    networkPipeline2Sub: '把标题·话题或评论文本转换成向量',
    networkPipeline3Title: 'Cosine Similarity',
    networkPipeline3Sub: '通过向量夹角计算反应的相似程度',
    networkPipeline4Title: '互为最近邻图（Mutual k-NN）',
    networkPipeline4Sub: '只有双方互选为邻居时才连接',
    networkPipeline5Title: 'UMAP',
    networkPipeline5Sub: '把嵌入空间中相近的点投影到2D地图上相近的位置',
    networkEdgeCardTitle: '连接分析',
    networkEdgeReasonComment: '这两条评论在语义上很相似，彼此都把对方选为最近邻。',
    networkEdgeReasonTopic: '两者都涉及话题（{topics}），且反应模式相似。',
    networkEdgeReasonNoTopic: '虽然话题不同，但标题和情感反应的模式相似，因此被连接。',
    networkThumbGoToHistory: '查看分析记录',
    networkSortCluster: '按地图分组',
    networkSortComments: '评论最多',
    networkSortPositive: '积极率最高',
    networkSortNegative: '消极率最高',
    networkSortNewest: '最新',
    networkBack: '返回总览',
    networkResetView: '重置视图',
    networkLegendOverview: '圆圈 = 视频 · 大小 = 评论数 · 颜色 = 反应相似分组 · 连线 = 反应相似',
    networkLegendDetail: '圆圈 = 评论 · 大小 = 点赞数 · 颜色 = 话题 · 连线 = 语义相似度',
    networkPanelSimilarVideos: '反应相似的视频',
    networkPanelSimilarComments: '相似评论',
    networkPanelViewCommentsBtn: '查看评论反应地图',
    networkBackToList: '返回列表',
    networkListVideos: '已分析视频',
    networkTopicSampleNote: '出于图表可读性和嵌入成本考虑，每个话题只显示点赞数最高的30条评论（情感·话题分析本身仍基于全部评论）',
    networkListUnavailable: '尚未生成评论地图',
    settingsTitle: '设置',
    settingsSub: '分析新视频需要您自己的API密钥',
    byokNotice: '本站使用您自己的API密钥来分析新视频。密钥仅保存在您的浏览器（localStorage）中，仅通过请求头发送，不会保存在服务器上。无需密钥即可查看已有的分析记录、统计和对比。',
    openaiKeyLabel: 'OpenAI API 密钥',
    openaiKeyHint: '在 platform.openai.com/api-keys 获取',
    youtubeKeyLabel: 'YouTube Data API 密钥',
    youtubeKeyHint: '在 Google Cloud Console 启用 YouTube Data API v3 后获取',
    keyPlaceholder: '请输入密钥',
    saveBtn: '保存',
    savedToast: '已保存',
    clearBtn: '删除',
    keyStoredLocally: '仅保存在此浏览器中',
    missingYoutubeKey: '需要YouTube API密钥。请在设置页面输入您自己的密钥。',
    missingOpenaiKey: '需要OpenAI API密钥。请在设置页面输入您自己的密钥。',
    analysisFailed: '分析过程中发生错误。',
    fieldSaved: '已保存',
    fieldDeleted: '已删除',
    currentlySaved: '已保存在此浏览器中',
    notSaved: '未保存密钥',
    keyModalTitle: '需要API密钥',
    keyModalBody1: '分析新视频需要您自己的YouTube Data API密钥和OpenAI API密钥（付费）。在设置页面输入后，仅保存在此浏览器中。',
    keyModalBody2: '即使没有密钥，您仍可以自由查看已有视频的分析记录、统计和对比。',
    keyModalSettingsBtn: '前往设置',
    keyModalHistoryBtn: '查看分析记录',
    keyModalClose: '关闭',
    topicCommentsLabel: '话题评论',
    filterAll: '全部',
    anonymousAuthor: '匿名',
    noCommentsFound: '没有相关评论',
    totalCommentsFooter: '共 {n} 条评论 · 按点赞数排序',
    commentsLoadFailed: '无法加载评论。',
    originalCommentLabel: '原文',
    confirmDeleteTitle: '要删除此分析记录吗？',
    confirmDeleteBody: '删除后，服务器上缓存的分析结果将被永久清除且无法恢复。如需再次查看，需要重新分析。',
    confirmDeleteBtn: '删除',
    cancelBtn: '取消',
    deleteFailed: '删除失败。',
    reportBrandTagline: 'Community Reaction Analysis',
    reportGeneratedOn: '生成日期',
    overallSentimentDistribution: '整体情感分布',
    reportFooterNote: '基于YouTube公开评论API的分析',
    footerDescription: '一个用AI分析YouTube评论、一目了然展示情感与反应的仪表盘。制作于首尔瑞草区电竞开发者学院（瑞草区厅 × T1 Esports）课程期间。',
    footerDisclaimer: '当前分析结果的准确性尚未经过独立验证。由于是基于GPT的分类，可能与实际情况有所出入。',
  },

  ja: {
    navHome: 'ホーム',
    navHistory: '分析履歴',
    navCompare: '動画比較',
    navNetwork: 'リアクションマップ',
    navHowto: '使い方',
    navStats: '分析統計',
    navSettings: '設定',
    uploadDate: 'アップロード日',
    views: '再生回数',
    likes: 'いいね数',
    analyzedComments: '分析コメント数',
    languageRatio: '言語比率',
    analysisNote: 'YouTube公開コメントAPIに基づく分析',
    analyzedAtLabel: '分析日',
    reAnalyze: '再分析する',
    topReactionTopics: 'トップ反応トピック',
    totalMentions: '総言及数',
    positive: 'ポジティブ',
    neutral: 'ニュートラル',
    negative: 'ネガティブ',
    clickHint: 'クリックしてコメントを表示',
    sentimentTrend: '感情反応トレンド',
    reactionSub: 'アップロード後の時間帯別コメント反応',
    byHour: '時間別',
    reactionFlow: '反応フロー',
    anomalyDetected: '異常検知',
    positiveSpike: 'ポジティブ急増',
    negativeSpike: 'ネガティブ急増',
    netSentimentLabel: '純感情スコア',
    normalRangeLabel: '通常範囲',
    netSentimentTrend: '純感情指数',
    netSentimentAnomalyLabel: '異常検知',
    netSentimentSub: '平均 ± 標準偏差の範囲を外れると異常として表示（z-score基準）',
    keyInsights: '主要インサイト',
    positiveLabel: '↑ ポジティブ',
    negativeLabel: '↓ ネガティブ',
    likesLabel: 'いいね',
    langBreakdown: '言語分布',
    disclaimer: 'この分析はYouTube公開APIで取得可能なコメントに限ります。削除・非表示・通報されたコメントは含まれません。',
    communityAnalysis: 'コミュニティ反応分析',
    urlPlaceholder: 'YouTube URLを貼り付けてください...',
    analyzeBtn: '分析する',
    urlHint: 'youtu.be/... または youtube.com/watch?v=... 形式対応',
    backToHistory: '履歴に戻る',
    newAnalysis: '新規分析',
    moreInsights: '↓ さらなるインサイト',
    historyTitle: '分析履歴',
    historySub: 'サーバーキャッシュに保存された動画分析結果',
    loading: '読み込み中...',
    emptyHistory: 'まだ分析した動画はありません',
    goAnalyze: '今すぐ分析する',
    viewBtn: '表示',
    deleteBtn: '削除',
    sortDate: '最新の分析',
    sortPos: 'ポジティブ高順',
    sortNeg: 'ネガティブ高順',
    sortPub: '最新動画',
    sentimentScore: '感情スコア',
    sentimentScoreDesc: 'ポジティブ% − ネガティブ%',
    commentRate: 'コメント反応率',
    commentRateDesc: 'コメント ÷ 再生回数',
    likeRate: 'いいね率',
    likeRateDesc: 'いいね ÷ 再生回数',
    controversy: '議論性',
    controversyDesc: '意見の分裂度',
    weightedSentiment: '加重感情',
    weightedSentimentDesc: 'いいね加重平均',
    compareSub: '分析済み動画から2~3件を選択してください',
    compareBtn: '比較する',
    comparing: '読み込み中…',
    compareNone: '比較できる分析記録がありません。',
    reselect: '再選択',
    sectionBasic: '基本情報',
    sectionSentiment: '感情分布',
    sectionTopics: '上位トピック',
    sectionCommonTopics: '共通トピック',
    sectionAnalysisMetrics: '分析指標',
    sectionLangDist: '言語分布',
    colTopic: 'トピック',
    colCommon: '共通',
    overallLabel: '全体',
    colCommentCount: '分析コメント',
    statsSub: 'このサーバーで分析されたすべての動画の処理時間・処理量の記録',
    totalAnalyses: '総分析回数',
    totalComments: '総分析コメント',
    totalTokens: '総使用トークン',
    avgDuration: '平均所要時間',
    minDuration: '最短所要時間',
    maxDuration: '最長所要時間',
    avgPer100: '100件あたり平均',
    videoRecords: '動画別分析記録',
    colVideo: '動画',
    colDuration: '所要時間',
    colPer100: '100件あたり',
    colDate: '分析日',
    noRecords: 'まだ分析記録はありません。',
    backendError: 'バックエンドサーバーに接続できません。',
    howtoEyebrow: 'システムアーキテクチャ',
    howtoTitle: 'どのように動作しますか？',
    howtoSub: '1つのYouTube URLからAIがすべてのコメントを自動分析します',
    techStackLabel: '技術スタック',
    notesLabel: '注意事項',
    loadingTitle: '分析中です...',
    loadingStep1Label: 'コメント収集中',
    loadingStep1Sub: 'YouTube APIからコメントを取得しています',
    loadingStep2Label: '感情分析中',
    loadingStep2Sub: 'AIが各コメントの感情を判定しています',
    loadingStep3Label: 'トピック分類中',
    loadingStep3Sub: '主要な反応トピックを分類・集計しています',
    queueRemove: 'キャンセル',
    queueAddBtn: '追加',
    cancelAnalysisBtn: 'キャンセルする',
    confirmCancelAnalysisTitle: '分析をキャンセルしますか？',
    confirmCancelAnalysisBody: '今キャンセルすると進行中の分析が中断され、再度見るには最初からやり直す必要があります。',
    confirmCancelQueuedTitle: '待ち行列から削除しますか？',
    confirmCancelQueuedBody: '削除すると待ち行列から外れ、再度分析するにはURLを入力し直す必要があります。',
    networkSub: '分析済みの動画を反応（ポジティブ／ネガティブ）で配置した3Dマップです。動画をクリックするとそのコメント反応マップに入ります',
    networkNoGraph: 'この動画にはリアクションマップのデータがありません。再分析してください。',
    networkReanalyzeBtn: '再分析する',
    networkMethodTitle: '分析パイプライン',
    networkPipeline1Title: 'テキスト正規化',
    networkPipeline1Sub: '同じ対象を指す様々な表現（別名・略称など）を一つにまとめる',
    networkPipeline2Title: 'Embedding',
    networkPipeline2Sub: 'タイトル・トピックやコメントのテキストをベクトルに変換',
    networkPipeline3Title: 'Cosine Similarity',
    networkPipeline3Sub: 'ベクトルの角度で反応の類似度を計算',
    networkPipeline4Title: '相互k-NNグラフ',
    networkPipeline4Sub: 'お互いを隣人として選んだ場合だけ線でつなぐ',
    networkPipeline5Title: 'UMAP',
    networkPipeline5Sub: '埋め込み空間で近いものを2Dマップ上でも近くに配置',
    networkEdgeCardTitle: '接続分析',
    networkEdgeReasonComment: 'この2つのコメントは意味的に似ていて、お互いを最も近い隣人として選んでいます。',
    networkEdgeReasonTopic: '共通トピック（{topics}）を扱っていて、反応パターンも似ています。',
    networkEdgeReasonNoTopic: '扱うトピックは違いますが、タイトルや感情反応のパターンが似ているためつながっています。',
    networkThumbGoToHistory: '分析記録を見る',
    networkSortCluster: 'マップのグループ順',
    networkSortComments: 'コメントが多い順',
    networkSortPositive: 'ポジティブ率が高い順',
    networkSortNegative: 'ネガティブ率が高い順',
    networkSortNewest: '新しい順',
    networkBack: '全体マップへ',
    networkResetView: '表示をリセット',
    networkLegendOverview: '円 = 動画 · 大きさ = コメント数 · 色 = 反応が似たグループ · 線 = 反応の類似度',
    networkLegendDetail: '円 = コメント · 大きさ = 高評価数 · 色 = トピック · 線 = 意味的類似度',
    networkPanelSimilarVideos: '反応が似ている動画',
    networkPanelSimilarComments: '似ているコメント',
    networkPanelViewCommentsBtn: 'コメント反応マップを見る',
    networkBackToList: 'リストに戻る',
    networkListVideos: '分析済み動画',
    networkTopicSampleNote: 'グラフの見やすさと埋め込みコストのため、トピックごとに高評価上位30件のコメントのみ表示しています（感情・トピック分析自体は全コメントが対象）',
    networkListUnavailable: 'コメントマップ未生成',
    settingsTitle: '設定',
    settingsSub: '新しい動画を分析するにはご自身のAPIキーが必要です',
    byokNotice: '当サイトでは、訪問者ご自身が取得したAPIキーで新しい動画を分析します。キーはブラウザ（localStorage）にのみ保存され、分析リクエスト時にヘッダーとしてのみ送信され、サーバーには保存されません。キーがなくても既存の分析履歴・統計・比較は自由に閲覧できます。',
    openaiKeyLabel: 'OpenAI APIキー',
    openaiKeyHint: 'platform.openai.com/api-keys で取得',
    youtubeKeyLabel: 'YouTube Data APIキー',
    youtubeKeyHint: 'Google Cloud ConsoleでYouTube Data API v3を有効化して取得',
    keyPlaceholder: 'キーを入力してください',
    saveBtn: '保存',
    savedToast: '保存しました',
    clearBtn: '削除',
    keyStoredLocally: 'このブラウザにのみ保存されます',
    missingYoutubeKey: 'YouTube APIキーが必要です。設定ページでご自身のキーを入力してください。',
    missingOpenaiKey: 'OpenAI APIキーが必要です。設定ページでご自身のキーを入力してください。',
    analysisFailed: '分析中にエラーが発生しました。',
    fieldSaved: '保存済み',
    fieldDeleted: '削除済み',
    currentlySaved: 'このブラウザに保存されています',
    notSaved: '保存されたキーはありません',
    keyModalTitle: 'APIキーが必要です',
    keyModalBody1: '新しい動画を分析するには、ご自身のYouTube Data APIキーとOpenAI APIキー（有料）が必要です。設定ページで入力すると、このブラウザにのみ保存されます。',
    keyModalBody2: 'キーがなくても、既存の動画の分析履歴・統計・比較は自由に閲覧できます。',
    keyModalSettingsBtn: '設定へ移動',
    keyModalHistoryBtn: '分析履歴を見る',
    keyModalClose: '閉じる',
    topicCommentsLabel: 'トピックコメント',
    filterAll: 'すべて',
    anonymousAuthor: '匿名',
    noCommentsFound: '該当するコメントがありません',
    totalCommentsFooter: '合計 {n} 件のコメント · いいね順',
    commentsLoadFailed: 'コメントを読み込めませんでした。',
    originalCommentLabel: '原文',
    confirmDeleteTitle: 'この分析記録を削除しますか？',
    confirmDeleteBody: '削除すると、サーバーにキャッシュされた分析結果が完全に削除され、元に戻せません。再度見るには最初から再分析が必要です。',
    confirmDeleteBtn: '削除',
    cancelBtn: 'キャンセル',
    deleteFailed: '削除に失敗しました。',
    reportBrandTagline: 'Community Reaction Analysis',
    reportGeneratedOn: '生成日',
    overallSentimentDistribution: '全体の感情分布',
    reportFooterNote: 'YouTube公開コメントAPIに基づく分析',
    footerDescription: 'YouTubeコメントをAIで分析し、感情と反応を一目で見せるダッシュボードです。瑞草eスポーツ開発者アカデミー（瑞草区庁 × T1 Esports）の課程で制作しました。',
    footerDisclaimer: '現在の分析結果の正確性はまだ検証されていません。GPTベースの分類のため、実際とは異なる場合があります。',
  },
}
