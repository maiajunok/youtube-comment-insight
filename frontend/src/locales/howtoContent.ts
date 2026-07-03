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
        desc: '수집된 댓글을 50개씩 배치로 묶어 GPT-4o-mini에 전송합니다. 각 댓글을 긍정 / 중립 / 부정으로 분류합니다. 현재는 방문자 본인의 OpenAI API 키(BYOK)로 GPT API를 호출합니다.',
        details: ['배치 크기: 50개', '3-class 분류', '한국어·영어 모두 처리'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini + Embeddings (현재)',
        color: '#c850ff',
        title: '토픽 분류',
        desc: '좋아요 상위 300개 댓글을 GPT에 전달해 대표 토픽 5개를 추출합니다. 나머지 전체 댓글은 text-embedding-3-small로 벡터화 후 코사인 유사도로 가장 가까운 토픽에 배정합니다. K-means·DBSCAN 등 비지도 클러스터링으로 대체를 실험했으나 어휘·문장부호 패턴 위주로 묶여 의미 있는 토픽 분리에는 실패해, 현재 방식(GPT + 임베딩 유사도)을 유지하고 있습니다.',
        details: ['좋아요 상위 300개로 토픽 추출', 'text-embedding-3-small', '코사인 유사도 배정'],
        future: null,
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
        tag: 'pandas · Z-score',
        color: '#eab308',
        title: '이상치 탐지 (반응 트렌드)',
        desc: '댓글을 등빈도 구간(구간당 약 40개)으로 나눕니다. 구간마다 댓글 감정을 긍정=+1, 중립=0, 부정=−1로 바꿔서 평균을 낸 값이 "순감정 점수"입니다(예: 40개 중 긍정 25·중립 10·부정 5 → (25×1 + 10×0 + 5×−1)/40 = 0.5). 영상 전체 구간의 평균·표준편차 대비 이 구간의 z-score가 임계값(1.5)을 넘으면 이상치로 표시합니다. 금융권 이상거래탐지(FDS)·볼린저 밴드와 같은 통계 기법이며, AI 호출 없이 이미 분류된 감정 데이터만으로 순수 통계 계산만 추가로 수행합니다.',
        details: ['순감정 점수 = (긍정×1 + 중립×0 + 부정×−1) / 댓글 수', '등빈도 구간화 (구간당 ~40개)', 'z-score = (구간 평균 − 전체 평균) / 표준편차'],
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
      { role: '이상치 탐지',   name: 'Z-score (pandas)' },
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
        title: '분류 방식에 대한 결정',
        desc: '토픽 분류는 비지도 클러스터링(K-means/DBSCAN)을 실험해봤으나 의미 있는 분리에 실패해 현재 GPT 방식을 유지합니다. 감정·토픽 분류는 GPT에 맡기고, 그 위에 순수 통계 기반 이상치 탐지(Z-score)를 얹는 구조로 설계했습니다.',
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
        desc: 'Collected comments are batched 50 at a time and sent to GPT-4o-mini, which classifies each as Positive / Neutral / Negative. This currently calls the GPT API using the visitor\'s own OpenAI API key (BYOK).',
        details: ['Batch size: 50', '3-class classification', 'Handles both Korean and English'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini + Embeddings (current)',
        color: '#c850ff',
        title: 'Topic Classification',
        desc: 'The top 300 comments by likes are sent to GPT to extract 5 representative topics. The remaining comments are vectorized with text-embedding-3-small and assigned to the closest topic by cosine similarity. Unsupervised clustering (K-means/DBSCAN) was tested as a replacement, but it grouped comments by surface lexical/punctuation patterns rather than meaningful topics, so the current approach (GPT + embedding similarity) was kept.',
        details: ['Top 300 by likes for topic extraction', 'text-embedding-3-small', 'Cosine similarity assignment'],
        future: null,
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
        tag: 'pandas · Z-score',
        color: '#eab308',
        title: 'Anomaly Detection (Reaction Trend)',
        desc: 'Comments are grouped into equal-frequency buckets (~40 comments each). Each comment\'s sentiment is mapped to Positive=+1, Neutral=0, Negative=−1, and averaged to get the "net sentiment score" (e.g., 25 positive, 10 neutral, 5 negative out of 40 → (25×1 + 10×0 + 5×−1)/40 = 0.5). Buckets whose z-score against the video\'s own mean/std exceeds a threshold (1.5) are flagged as anomalies — the same statistical technique used in financial fraud detection (FDS) and Bollinger Bands. This is a pure statistical computation on already-classified sentiment data, with no additional AI calls.',
        details: ['Net sentiment = (positive×1 + neutral×0 + negative×−1) / count', 'Equal-frequency bucketing (~40/bucket)', 'z-score = (bucket mean − overall mean) / std dev'],
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
      { role: 'Anomaly Detection', name: 'Z-score (pandas)' },
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
        title: 'Decision on Classification Approach',
        desc: 'Unsupervised clustering (K-means/DBSCAN) was tested for topic classification, but failed to produce meaningful separation, so the current GPT-based approach was kept. Sentiment and topic classification are both left to GPT — the actual statistical analysis layer (Z-score anomaly detection) is built on top of those labels.',
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
        desc: '收集到的评论以50条为一批发送给GPT-4o-mini，将每条评论分类为正面/中立/负面。目前使用访客自己的OpenAI API密钥（BYOK）调用GPT API。',
        details: ['批次大小：50条', '三分类', '同时处理韩语和英语'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini + Embeddings（当前）',
        color: '#c850ff',
        title: '话题分类',
        desc: '将点赞数最高的300条评论提交给GPT，提取5个代表性话题。其余评论通过text-embedding-3-small向量化后，按余弦相似度分配到最接近的话题。曾尝试用K-means、DBSCAN等无监督聚类替代，但结果只是按词汇、标点等表层模式聚类，未能形成有意义的话题划分，因此保留了目前的方式（GPT+向量相似度）。',
        details: ['点赞前300条用于话题提取', 'text-embedding-3-small', '余弦相似度分配'],
        future: null,
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
        tag: 'pandas · Z-score',
        color: '#eab308',
        title: '异常检测（反应趋势）',
        desc: '将评论按等频区间（每区间约40条）分组。将每条评论的情感映射为 正面=+1、中立=0、负面=−1，取平均值得到"净情感分数"（例如40条中正面25·中立10·负面5 → (25×1 + 10×0 + 5×−1)/40 = 0.5）。相对于该视频整体均值/标准差的z-score超过阈值（1.5）的区间将被标记为异常——与金融欺诈检测（FDS）、布林带使用的统计方法相同。这只是在已分类的情感数据上进行纯统计计算，无需额外调用AI。',
        details: ['净情感分数 = (正面×1 + 中立×0 + 负面×−1) / 评论数', '等频分箱（每箱约40条）', 'z-score = (区间均值 − 整体均值) / 标准差'],
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
      { role: '异常检测',    name: 'Z-score (pandas)' },
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
        title: '分类方式的决定',
        desc: '话题分类曾尝试无监督聚类（K-means/DBSCAN），但未能形成有意义的划分，因此保留了当前基于GPT的方式。情感与话题分类都交给GPT处理，在这些标签之上再叠加纯统计的异常检测（Z-score）。',
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
        desc: '収集したコメントを50件ずつバッチ化してGPT-4o-miniに送信します。各コメントをポジティブ／ニュートラル／ネガティブに分類します。現在は訪問者自身のOpenAI APIキー（BYOK）でGPT APIを呼び出しています。',
        details: ['バッチサイズ：50件', '3クラス分類', '韓国語・英語の両方に対応'],
        future: null,
      },
      {
        tag: 'GPT-4o-mini + Embeddings（現在）',
        color: '#c850ff',
        title: 'トピック分類',
        desc: 'いいね数上位300件のコメントをGPTに渡し、代表的なトピックを5つ抽出します。残りの全コメントはtext-embedding-3-smallでベクトル化し、コサイン類似度で最も近いトピックに割り当てます。K-means・DBSCANなどの教師なしクラスタリングへの置き換えを試しましたが、語彙や句読点パターン中心にまとまるだけで意味のあるトピック分離はできず、現在の方式（GPT+埋め込み類似度）を維持しています。',
        details: ['いいね上位300件でトピック抽出', 'text-embedding-3-small', 'コサイン類似度による割り当て'],
        future: null,
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
        tag: 'pandas · Z-score',
        color: '#eab308',
        title: '異常検知（反応トレンド）',
        desc: 'コメントを等頻度区間（区間あたり約40件）に分けます。各コメントの感情をポジティブ=+1、ニュートラル=0、ネガティブ=−1に変換して平均した値が「純感情スコア」です（例:40件中ポジティブ25・ニュートラル10・ネガティブ5 → (25×1 + 10×0 + 5×−1)/40 = 0.5）。動画全体の平均・標準偏差に対するz-scoreが閾値（1.5）を超える区間を異常として表示します。金融機関の不正取引検知（FDS）やボリンジャーバンドと同じ統計手法で、既に分類済みの感情データに対して追加のAI呼び出しなしに純粋な統計計算のみを行います。',
        details: ['純感情スコア = (ポジティブ×1 + ニュートラル×0 + ネガティブ×−1) / 件数', '等頻度区間化（区間あたり約40件）', 'z-score = (区間平均 − 全体平均) / 標準偏差'],
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
      { role: '異常検知',        name: 'Z-score (pandas)' },
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
        title: '分類方式に関する判断',
        desc: 'トピック分類は教師なしクラスタリング（K-means/DBSCAN）を試しましたが、意味のある分離はできず、現行のGPT方式を維持しています。感情・トピック分類はどちらもGPTに任せ、そのラベルの上に純粋な統計的異常検知（Z-score）を重ねる構成にしています。',
      },
    ],
  },
}
