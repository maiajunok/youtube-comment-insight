import type { Lang } from '@/features/insight/types/insight'

export interface HowtoStep {
  tag: string
  color: string
  title: string
  desc: string
  details: string[]
  future: string | null
}

export interface HowtoTech {
  role: string
  name: string
}

export interface HowtoNote {
  title: string
  desc: string
}

export interface HowtoContent {
  steps: HowtoStep[]
  techStack: HowtoTech[]
  notes: HowtoNote[]
}

export const howtoContent: Record<Lang, HowtoContent> = {
  ko: {
    steps: [
      {
        tag: 'YouTube Data API v3',
        color: '#ef4444',
        title: '댓글 전체 수집',
        desc: '입력된 YouTube URL에서 영상 ID를 추출하고, YouTube Data API를 통해 페이지네이션으로 해당 영상의 전체 댓글을 수집합니다. 댓글 수에 상한선 없이 모두 가져옵니다.',
        details: ['제한 없음 (전체 수집)', '100개씩 페이지네이션', '본문·작성자·좋아요·날짜 포함'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini (현재)',
        color: '#22c55e',
        title: '감정 분석',
        desc: '수집된 댓글을 50개씩 배치로 묶어 GPT-4o-mini에 전송합니다. 각 댓글을 긍정 / 중립 / 부정으로 분류합니다. 현재는 방문자 본인의 OpenAI API 키(BYOK)로 GPT API를 호출하며, 추후 통계 기반 모델로 전환 예정입니다.',
        details: ['배치 크기: 50개', '3-class 분류', '한국어·영어 모두 처리'],
        future: '향후 VADER, 한국어 KoBERT 등 전용 감정 분석 모델로 교체 예정',
      },
      {
        tag: 'GPT-4o-mini + Embeddings (현재)',
        color: '#c850ff',
        title: '토픽 분류',
        desc: '좋아요 상위 300개 댓글을 GPT에 전달해 대표 토픽 5개를 추출합니다. 나머지 전체 댓글은 text-embedding-3-small로 벡터화 후 코사인 유사도로 가장 가까운 토픽에 배정합니다. 현재 GPT 의존도가 높으며, 추후 LDA 등 통계 기반 방법론으로 개선 예정입니다.',
        details: ['좋아요 상위 300개로 토픽 추출', 'text-embedding-3-small', '코사인 유사도 배정'],
        future: '향후 LDA (Latent Dirichlet Allocation) 등 비지도 토픽 모델링으로 전환 예정',
      },
      {
        tag: 'FastAPI · JSON Cache',
        color: '#f59e0b',
        title: '집계 및 캐싱',
        desc: '토픽별 감정 비율, 시간대별 반응 추이, 언어 분포, 대표 댓글을 집계합니다. 결과는 서버에 JSON 파일로 캐싱되어 동일 영상 재분석 시 API 없이 즉시 반환합니다.',
        details: ['서버 JSON 캐시', '즉시 재로딩', '언어 감지(langdetect)'],
        future: null,
      },
      {
        tag: 'Vue 3 · SSE',
        color: '#3b82f6',
        title: '실시간 대시보드',
        desc: '분석 중 Server-Sent Events(SSE)로 단계별 진행 상황을 실시간 스트리밍합니다. 완료 후 토픽 차트, 타임라인, 언어 분포, 토픽별 전체 댓글 조회를 제공합니다.',
        details: ['SSE 실시간 스트리밍', '토픽 클릭 → 댓글 드로어', '분석 기록 저장'],
        future: null,
      },
    ],
    techStack: [
      { role: 'Frontend',      name: 'Vue 3 + TypeScript' },
      { role: 'Styling',       name: 'Tailwind CSS v4' },
      { role: 'Backend',       name: 'Python FastAPI' },
      { role: 'LLM (현재)',    name: 'OpenAI GPT-4o-mini' },
      { role: 'Embeddings',    name: 'text-embedding-3-small' },
      { role: 'Data Source',   name: 'YouTube Data API v3' },
      { role: 'Caching',       name: 'JSON File Cache' },
      { role: 'Streaming',     name: 'Server-Sent Events' },
      { role: '예정 (토픽)',   name: 'LDA / NMF' },
      { role: '예정 (감정)',   name: 'KoBERT / VADER' },
    ],
    notes: [
      {
        title: 'API 키 정책 (BYOK)',
        desc: '새 영상 분석에는 방문자 본인의 OpenAI · YouTube API 키가 필요합니다(설정 페이지에서 입력, 브라우저에만 저장). 키가 없어도 기존 분석 기록·통계·비교는 자유롭게 볼 수 있습니다.',
      },
      {
        title: '분석 시간',
        desc: '댓글이 많을수록 수집·분석 시간이 늘어납니다. 동일 영상은 캐시에서 즉시 로드됩니다.',
      },
      {
        title: 'API 비용',
        desc: 'GPT-4o-mini와 임베딩 API는 유료입니다. 댓글 수에 비례해 비용이 발생합니다.',
      },
      {
        title: '결과 검증 미완료',
        desc: '현재 분석 결과의 정확성은 아직 검증되지 않았습니다. GPT 기반 분류이므로 실제와 다를 수 있습니다.',
      },
      {
        title: '알고리즘 개선 예정',
        desc: 'GPT API 의존도를 낮추고 LDA, KoBERT 등 전통적·딥러닝 기반 모델로 단계적 전환 예정입니다.',
      },
    ],
  },

  en: {
    steps: [
      {
        tag: 'YouTube Data API v3',
        color: '#ef4444',
        title: 'Collect All Comments',
        desc: 'Extracts the video ID from the given YouTube URL and paginates through the YouTube Data API to collect every comment on the video, with no upper limit.',
        details: ['No limit (full collection)', 'Paginated 100 at a time', 'Includes text, author, likes, date'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini (current)',
        color: '#22c55e',
        title: 'Sentiment Analysis',
        desc: 'Collected comments are batched 50 at a time and sent to GPT-4o-mini, which classifies each as Positive / Neutral / Negative. This currently calls the GPT API using the visitor\'s own OpenAI API key (BYOK), with a move to a statistical model planned for the future.',
        details: ['Batch size: 50', '3-class classification', 'Handles both Korean and English'],
        future: 'Planned migration to dedicated sentiment models such as VADER or Korean KoBERT',
      },
      {
        tag: 'GPT-4o-mini + Embeddings (current)',
        color: '#c850ff',
        title: 'Topic Classification',
        desc: 'The top 300 comments by likes are sent to GPT to extract 5 representative topics. The remaining comments are vectorized with text-embedding-3-small and assigned to the closest topic by cosine similarity. Currently relies heavily on GPT, with a move to statistical methods such as LDA planned.',
        details: ['Top 300 by likes for topic extraction', 'text-embedding-3-small', 'Cosine similarity assignment'],
        future: 'Planned migration to unsupervised topic modeling such as LDA (Latent Dirichlet Allocation)',
      },
      {
        tag: 'FastAPI · JSON Cache',
        color: '#f59e0b',
        title: 'Aggregation & Caching',
        desc: 'Aggregates sentiment ratio per topic, reaction trend over time, language distribution, and representative comments. Results are cached as a JSON file on the server, so re-analyzing the same video returns instantly with no API calls.',
        details: ['Server-side JSON cache', 'Instant reload', 'Language detection (langdetect)'],
        future: null,
      },
      {
        tag: 'Vue 3 · SSE',
        color: '#3b82f6',
        title: 'Real-time Dashboard',
        desc: 'Streams step-by-step progress in real time via Server-Sent Events (SSE) during analysis. Once complete, it provides topic charts, a timeline, language distribution, and per-topic comment browsing.',
        details: ['Real-time SSE streaming', 'Click a topic → comment drawer', 'Analysis history saved'],
        future: null,
      },
    ],
    techStack: [
      { role: 'Frontend',        name: 'Vue 3 + TypeScript' },
      { role: 'Styling',         name: 'Tailwind CSS v4' },
      { role: 'Backend',         name: 'Python FastAPI' },
      { role: 'LLM (current)',   name: 'OpenAI GPT-4o-mini' },
      { role: 'Embeddings',      name: 'text-embedding-3-small' },
      { role: 'Data Source',     name: 'YouTube Data API v3' },
      { role: 'Caching',         name: 'JSON File Cache' },
      { role: 'Streaming',       name: 'Server-Sent Events' },
      { role: 'Planned (topic)', name: 'LDA / NMF' },
      { role: 'Planned (sent.)', name: 'KoBERT / VADER' },
    ],
    notes: [
      {
        title: 'API Key Policy (BYOK)',
        desc: 'Analyzing a new video requires your own OpenAI and YouTube API keys (entered on the Settings page, stored only in your browser). Existing analysis history, stats, and comparisons remain viewable without any key.',
      },
      {
        title: 'Analysis Time',
        desc: 'More comments mean longer collection and analysis time. The same video loads instantly from cache on repeat visits.',
      },
      {
        title: 'API Cost',
        desc: 'GPT-4o-mini and the embeddings API are paid services. Cost scales with the number of comments.',
      },
      {
        title: 'Results Not Yet Validated',
        desc: 'The accuracy of current analysis results has not been formally validated. Since classification is GPT-based, it may differ from ground truth.',
      },
      {
        title: 'Planned Algorithm Improvements',
        desc: 'Plans are underway to reduce reliance on the GPT API and gradually move to traditional and deep-learning-based models such as LDA and KoBERT.',
      },
    ],
  },

  zh: {
    steps: [
      {
        tag: 'YouTube Data API v3',
        color: '#ef4444',
        title: '收集全部评论',
        desc: '从输入的YouTube链接中提取视频ID，并通过YouTube Data API分页收集该视频的全部评论，评论数量没有上限。',
        details: ['无数量限制（全部收集）', '每次分页100条', '包含正文·作者·点赞·日期'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini（当前）',
        color: '#22c55e',
        title: '情感分析',
        desc: '收集到的评论以50条为一批发送给GPT-4o-mini，将每条评论分类为正面/中立/负面。目前使用访客自己的OpenAI API密钥（BYOK）调用GPT API，未来计划转为基于统计的模型。',
        details: ['批次大小：50条', '三分类', '同时处理韩语和英语'],
        future: '未来计划替换为VADER、韩语KoBERT等专用情感分析模型',
      },
      {
        tag: 'GPT-4o-mini + Embeddings（当前）',
        color: '#c850ff',
        title: '话题分类',
        desc: '将点赞数最高的300条评论提交给GPT，提取5个代表性话题。其余评论通过text-embedding-3-small向量化后，按余弦相似度分配到最接近的话题。目前对GPT依赖度较高，未来计划改进为LDA等统计方法。',
        details: ['点赞前300条用于话题提取', 'text-embedding-3-small', '余弦相似度分配'],
        future: '未来计划转向LDA（潜在狄利克雷分配）等无监督话题建模',
      },
      {
        tag: 'FastAPI · JSON Cache',
        color: '#f59e0b',
        title: '汇总与缓存',
        desc: '汇总各话题的情感比例、按时间段的反应趋势、语言分布及代表性评论。结果以JSON文件形式缓存在服务器上，同一视频再次分析时无需调用API即可立即返回。',
        details: ['服务器JSON缓存', '即时重新加载', '语言检测（langdetect）'],
        future: null,
      },
      {
        tag: 'Vue 3 · SSE',
        color: '#3b82f6',
        title: '实时仪表盘',
        desc: '分析过程中通过Server-Sent Events（SSE）实时流式传输各阶段进度。完成后提供话题图表、时间线、语言分布以及按话题查看全部评论的功能。',
        details: ['SSE实时流式传输', '点击话题→评论抽屉', '保存分析记录'],
        future: null,
      },
    ],
    techStack: [
      { role: '前端',       name: 'Vue 3 + TypeScript' },
      { role: '样式',       name: 'Tailwind CSS v4' },
      { role: '后端',       name: 'Python FastAPI' },
      { role: 'LLM（当前）', name: 'OpenAI GPT-4o-mini' },
      { role: '向量嵌入',    name: 'text-embedding-3-small' },
      { role: '数据来源',    name: 'YouTube Data API v3' },
      { role: '缓存',       name: 'JSON文件缓存' },
      { role: '流式传输',    name: 'Server-Sent Events' },
      { role: '计划中（话题）', name: 'LDA / NMF' },
      { role: '计划中（情感）', name: 'KoBERT / VADER' },
    ],
    notes: [
      {
        title: 'API密钥政策（BYOK）',
        desc: '分析新视频需要您自己的OpenAI和YouTube API密钥（在设置页面输入，仅保存在浏览器中）。无需密钥即可查看已有的分析记录、统计和对比。',
      },
      {
        title: '分析时间',
        desc: '评论越多，收集和分析所需时间越长。同一视频再次访问时会从缓存中立即加载。',
      },
      {
        title: 'API费用',
        desc: 'GPT-4o-mini和嵌入API为付费服务，费用与评论数量成正比。',
      },
      {
        title: '结果尚未验证',
        desc: '当前分析结果的准确性尚未经过正式验证。由于是基于GPT的分类，可能与实际情况有所出入。',
      },
      {
        title: '算法改进计划',
        desc: '计划降低对GPT API的依赖，逐步转向LDA、KoBERT等传统及深度学习模型。',
      },
    ],
  },

  ja: {
    steps: [
      {
        tag: 'YouTube Data API v3',
        color: '#ef4444',
        title: 'コメント全件収集',
        desc: '入力されたYouTube URLから動画IDを抽出し、YouTube Data APIでページネーションしながら該当動画の全コメントを収集します。コメント数に上限はありません。',
        details: ['上限なし（全件収集）', '100件ずつページネーション', '本文・投稿者・いいね・日付を含む'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini（現在）',
        color: '#22c55e',
        title: '感情分析',
        desc: '収集したコメントを50件ずつバッチ化してGPT-4o-miniに送信します。各コメントをポジティブ／ニュートラル／ネガティブに分類します。現在は訪問者自身のOpenAI APIキー（BYOK）でGPT APIを呼び出しており、将来的には統計ベースのモデルへの移行を予定しています。',
        details: ['バッチサイズ：50件', '3クラス分類', '韓国語・英語の両方に対応'],
        future: '今後、VADERや韓国語KoBERTなど専用の感情分析モデルへの置き換えを予定',
      },
      {
        tag: 'GPT-4o-mini + Embeddings（現在）',
        color: '#c850ff',
        title: 'トピック分類',
        desc: 'いいね数上位300件のコメントをGPTに渡し、代表的なトピックを5つ抽出します。残りの全コメントはtext-embedding-3-smallでベクトル化し、コサイン類似度で最も近いトピックに割り当てます。現在はGPTへの依存度が高く、今後LDAなど統計ベースの手法への改善を予定しています。',
        details: ['いいね上位300件でトピック抽出', 'text-embedding-3-small', 'コサイン類似度による割り当て'],
        future: '今後、LDA（潜在ディリクレ配分法）などの教師なしトピックモデリングへの移行を予定',
      },
      {
        tag: 'FastAPI · JSON Cache',
        color: '#f59e0b',
        title: '集計とキャッシュ',
        desc: 'トピックごとの感情比率、時間帯別の反応推移、言語分布、代表コメントを集計します。結果はサーバーにJSONファイルとしてキャッシュされ、同じ動画を再分析する際はAPIを呼ばずに即座に返します。',
        details: ['サーバーJSONキャッシュ', '即時再読み込み', '言語検出（langdetect）'],
        future: null,
      },
      {
        tag: 'Vue 3 · SSE',
        color: '#3b82f6',
        title: 'リアルタイムダッシュボード',
        desc: '分析中はServer-Sent Events（SSE）で段階ごとの進捗をリアルタイムにストリーミングします。完了後はトピックチャート、タイムライン、言語分布、トピック別の全コメント閲覧を提供します。',
        details: ['SSEリアルタイムストリーミング', 'トピックをクリック→コメントドロワー', '分析履歴の保存'],
        future: null,
      },
    ],
    techStack: [
      { role: 'フロントエンド',   name: 'Vue 3 + TypeScript' },
      { role: 'スタイリング',     name: 'Tailwind CSS v4' },
      { role: 'バックエンド',     name: 'Python FastAPI' },
      { role: 'LLM（現在）',      name: 'OpenAI GPT-4o-mini' },
      { role: 'Embeddings',      name: 'text-embedding-3-small' },
      { role: 'データソース',     name: 'YouTube Data API v3' },
      { role: 'キャッシュ',       name: 'JSONファイルキャッシュ' },
      { role: 'ストリーミング',   name: 'Server-Sent Events' },
      { role: '予定（トピック）', name: 'LDA / NMF' },
      { role: '予定（感情）',     name: 'KoBERT / VADER' },
    ],
    notes: [
      {
        title: 'APIキーポリシー（BYOK）',
        desc: '新しい動画の分析にはご自身のOpenAI・YouTube APIキーが必要です（設定ページで入力、ブラウザにのみ保存）。キーがなくても既存の分析履歴・統計・比較は自由に閲覧できます。',
      },
      {
        title: '分析時間',
        desc: 'コメントが多いほど収集・分析時間が長くなります。同じ動画はキャッシュから即座に読み込まれます。',
      },
      {
        title: 'APIコスト',
        desc: 'GPT-4o-miniと埋め込みAPIは有料です。コメント数に比例してコストが発生します。',
      },
      {
        title: '結果の検証は未完了',
        desc: '現在の分析結果の正確性はまだ検証されていません。GPTベースの分類のため、実際とは異なる場合があります。',
      },
      {
        title: 'アルゴリズム改善予定',
        desc: 'GPT APIへの依存度を下げ、LDAやKoBERTなど従来型・深層学習ベースのモデルへ段階的に移行する予定です。',
      },
    ],
  },
}
