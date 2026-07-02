<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { messages } from '@/locales/messages'
import { storeToRefs } from 'pinia'
import { insightApi } from '@/features/insight/api/insightApi'
import { useHistory } from '@/features/insight/composables/useHistory'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { useAnalysisStore } from '@/features/insight/stores/analysis'
import { useRouter } from 'vue-router'
import VideoInfoCard     from '@/features/insight/components/VideoInfoCard.vue'
import TopReactionTopics from '@/features/insight/components/TopReactionTopics.vue'
import ReactionTimeline  from '@/features/insight/components/ReactionTimeline.vue'
import KeyInsights       from '@/features/insight/components/KeyInsights.vue'
import LoadingState      from '@/features/insight/components/LoadingState.vue'
import TopicComments     from '@/features/insight/components/TopicComments.vue'

const router        = useRouter()
const settings      = useSettingsStore()
const analysisStore = useAnalysisStore()

const url           = ref('')
const isFocused     = ref(false)
const selectedTopic = ref<string | null>(null)

// 분석 상태는 store에서 직접 읽음 — storeToRefs로 반응성 보장
const { result: data, isAnalyzing: isLoading, loadingStep, loadingProgress, analysisError: error, resultSource } =
  storeToRefs(analysisStore)

async function fillEnglishLabels() {
  if (!data.value) return
  const missing = data.value.topics.filter(t => !t.labelEn)
  if (!missing.length) return
  try {
    const translations = await insightApi.translateLabels(missing.map(t => t.label))
    missing.forEach((t, i) => { t.labelEn = translations[i] || t.label })
  } catch { /* 실패 시 한국어 유지 */ }
}

watch(() => settings.lang, (lang) => {
  if (lang === 'en') fillEnglishLabels()
})

watch(data, (d) => {
  if (d && settings.lang === 'en') fillEnglishLabels()
})

const fmtNum = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K'     :
  String(n)

const overallSentiment = computed(() => {
  if (!data.value) return { positive: 0, neutral: 0, negative: 0 }
  let pos = 0, neu = 0, neg = 0, total = 0
  data.value.topics.forEach(t => {
    pos += t.sentiment.positive * t.mentionCount
    neu += t.sentiment.neutral * t.mentionCount
    neg += t.sentiment.negative * t.mentionCount
    total += t.mentionCount
  })
  if (!total) return { positive: 0, neutral: 0, negative: 0 }
  return {
    positive: Math.round(pos / total),
    neutral:  Math.round(neu / total),
    negative: Math.round(neg / total),
  }
})

function analyze() {
  if (!url.value.trim() || analysisStore.isAnalyzing) return
  selectedTopic.value = null
  analysisStore.startAnalysis(url.value.trim(), (videoId, d) => {
    useHistory().save(videoId, d)
  })
}

function goBack() {
  if (resultSource.value === 'history') {
    analysisStore.clearResult()
    router.push({ name: 'history' })
  } else {
    analysisStore.clearResult()
    url.value = ''
    selectedTopic.value = null
  }
}

const backLabel = computed(() =>
  resultSource.value === 'history'
    ? messages[settings.lang].backToHistory
    : messages[settings.lang].newAnalysis
)

function exportPDF() { window.print() }

// ── 분석 지표 ──
const sentimentScore = computed(() => {
  const s = overallSentiment.value
  return s.positive - s.negative
})
const commentRate = computed(() => {
  if (!data.value?.video.viewCount) return null
  return (data.value.video.analyzedComments / data.value.video.viewCount * 100).toFixed(2)
})
const likeRate = computed(() => {
  if (!data.value?.video.viewCount) return null
  return (data.value.video.likeCount / data.value.video.viewCount * 100).toFixed(2)
})
const controversyScore = computed(() => {
  const s = overallSentiment.value
  return Math.min(s.positive, s.negative) * 2
})
</script>

<template>
  <!-- 히어로 상태 -->
  <div v-if="!data && !isLoading" class="home-view">
    <div class="eyebrow">{{ messages[settings.lang].communityAnalysis }}</div>

    <h1 class="big-word">
      ANALYZE<br>
      <span>YOUR</span>
    </h1>
    <p class="sub-line">community.</p>

    <div class="search-wrap" :class="{ focused: isFocused }">
      <svg class="yt-icon" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
        <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8zM9.75 15.5v-7l6.25 3.5-6.25 3.5z"/>
      </svg>
      <input
        v-model="url"
        type="text"
        :placeholder="messages[settings.lang].urlPlaceholder"
        class="url-input"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @keyup.enter="analyze"
        autofocus
      />
      <button class="btn-go" @click="analyze" :disabled="!url.trim()">
        {{ messages[settings.lang].analyzeBtn }}
      </button>
    </div>

    <p v-if="error" class="url-error">{{ error }}</p>
    <p v-else class="url-hint">{{ messages[settings.lang].urlHint }}</p>

    <div class="platform-chips">
      <span class="chip active">
        <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
          <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8zM9.75 15.5v-7l6.25 3.5-6.25 3.5z"/>
        </svg>
        YouTube
        <span class="chip-live">{{ settings.lang === 'en' ? '● Live' : '● 지원중' }}</span>
      </span>
      <span class="chip soon">
        <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
        </svg>
        Reddit
        <span class="chip-badge">{{ settings.lang === 'en' ? 'Soon' : '준비중' }}</span>
      </span>
      <span class="chip soon">
        <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.19 8.19 0 0 0 4.79 1.52V6.75a4.85 4.85 0 0 1-1.02-.06z"/>
        </svg>
        TikTok
        <span class="chip-badge">{{ settings.lang === 'en' ? 'Coming Soon' : '출시 예정' }}</span>
      </span>
    </div>
  </div>

  <!-- 로딩 상태 (data 없을 때만) -->
  <div v-else-if="isLoading && !data" class="home-view loading-mode">
    <LoadingState :step="loadingStep" :progress="loadingProgress" />
  </div>

  <!-- 대시보드 (data 있으면 분석 중이어도 표시) -->
  <div v-else-if="data" class="home-view dashboard-mode">
    <div class="dash-topbar">
      <button class="back-btn" @click="goBack">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        {{ backLabel }}
      </button>

      <!-- 분석기록에서 열었을 때만 PDF 내보내기 표시 -->
      <button v-if="resultSource === 'history'" class="export-btn" @click="exportPDF">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="8 17 12 21 16 17"/>
          <line x1="12" y1="12" x2="12" y2="21"/>
          <path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"/>
        </svg>
        Export PDF
      </button>
    </div>

    <div class="dash-grid">
      <div class="dash-col-1">
        <VideoInfoCard :video="data.video" :lang="settings.lang" />
      </div>
      <div class="dash-col-2">
        <TopReactionTopics
          :topics="data.topics"
          :lang="settings.lang"
          @select-topic="selectedTopic = $event"
        />
      </div>
    </div>

    <!-- 분석 지표 카드 행 -->
    <div class="metrics-row">
      <div class="metric-card">
        <span class="metric-label">{{ messages[settings.lang].sentimentScore }}</span>
        <span class="metric-value" :class="sentimentScore > 0 ? 'mval-pos' : sentimentScore < 0 ? 'mval-neg' : ''">
          {{ sentimentScore > 0 ? '+' : '' }}{{ sentimentScore }}
        </span>
        <span class="metric-desc">{{ messages[settings.lang].sentimentScoreDesc }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ messages[settings.lang].commentRate }}</span>
        <span class="metric-value">{{ commentRate !== null ? commentRate + '%' : '—' }}</span>
        <span class="metric-desc">{{ messages[settings.lang].commentRateDesc }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ messages[settings.lang].likeRate }}</span>
        <span class="metric-value">{{ likeRate !== null ? likeRate + '%' : '—' }}</span>
        <span class="metric-desc">{{ messages[settings.lang].likeRateDesc }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ messages[settings.lang].controversy }}</span>
        <span class="metric-value">{{ controversyScore }}</span>
        <span class="metric-desc">{{ messages[settings.lang].controversyDesc }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ messages[settings.lang].weightedSentiment }}</span>
        <span class="metric-value" :class="(data.video.weightedSentiment ?? 0) > 0 ? 'mval-pos' : (data.video.weightedSentiment ?? 0) < 0 ? 'mval-neg' : ''">
          <template v-if="data.video.weightedSentiment !== undefined">
            {{ data.video.weightedSentiment > 0 ? '+' : '' }}{{ data.video.weightedSentiment }}
          </template>
          <template v-else>—</template>
        </span>
        <span class="metric-desc">{{ messages[settings.lang].weightedSentimentDesc }}</span>
      </div>
    </div>

    <ReactionTimeline :data="data.reactionTimeline" :lang="settings.lang" />

    <div class="dash-divider">
      <div class="line" /><span>{{ messages[settings.lang].moreInsights }}</span><div class="line" />
    </div>

    <KeyInsights
      :insights="data.keyInsights"
      :lang="settings.lang"
      :language-ratio="data.video.languageRatio"
    />
  </div>

  <!-- Print 보고서 (화면에는 숨겨져 있고 인쇄 시에만 표시) -->
  <div v-if="data" class="print-report">
    <div class="rpt-page">

      <div class="rpt-header">
        <img :src="data.video.thumbnailUrl" class="rpt-thumb" />
        <div class="rpt-header-info">
          <div class="rpt-brand">미정 · Community Reaction Analysis</div>
          <h1 class="rpt-title">{{ data.video.title }}</h1>
          <div class="rpt-channel">{{ data.video.channelTitle }}</div>
        </div>
        <div class="rpt-meta">
          <div>업로드 {{ data.video.publishedAt.slice(0, 10) }}</div>
          <div>생성일 {{ new Date().toLocaleDateString('ko-KR') }}</div>
        </div>
      </div>

      <div class="rpt-stats-row">
        <div class="rpt-stat"><span class="rpt-stat-val">{{ fmtNum(data.video.viewCount) }}</span><span class="rpt-stat-lbl">조회수</span></div>
        <div class="rpt-stat"><span class="rpt-stat-val">{{ fmtNum(data.video.likeCount) }}</span><span class="rpt-stat-lbl">좋아요</span></div>
        <div class="rpt-stat"><span class="rpt-stat-val">{{ fmtNum(data.video.analyzedComments) }}</span><span class="rpt-stat-lbl">분석 댓글</span></div>
        <div class="rpt-stat"><span class="rpt-stat-val">{{ data.video.languageRatio.ko }}%</span><span class="rpt-stat-lbl">한국어 비율</span></div>
      </div>

      <div class="rpt-section">
        <h2 class="rpt-sec-title">전체 감정 분포</h2>
        <div class="rpt-sent-bar">
          <div class="rpt-bar-pos" :style="`width:${overallSentiment.positive}%`"></div>
          <div class="rpt-bar-neu" :style="`width:${overallSentiment.neutral}%`"></div>
          <div class="rpt-bar-neg" :style="`width:${overallSentiment.negative}%`"></div>
        </div>
        <div class="rpt-sent-labels">
          <span class="rpt-pos-txt">긍정 {{ overallSentiment.positive }}%</span>
          <span class="rpt-neu-txt">중립 {{ overallSentiment.neutral }}%</span>
          <span class="rpt-neg-txt">부정 {{ overallSentiment.negative }}%</span>
        </div>
      </div>

      <div class="rpt-section">
        <h2 class="rpt-sec-title">상위 반응 토픽</h2>
        <div class="rpt-topics">
          <div v-for="(t, i) in data.topics" :key="t.label" class="rpt-topic-row">
            <span class="rpt-topic-num">{{ i + 1 }}</span>
            <span class="rpt-topic-name">{{ t.label }}</span>
            <div class="rpt-topic-bar">
              <div :style="`width:${t.sentiment.positive}%; background:#22c55e`"></div>
              <div :style="`width:${t.sentiment.neutral}%; background:#94a3b8`"></div>
              <div :style="`width:${t.sentiment.negative}%; background:#f43f5e`"></div>
            </div>
            <span class="rpt-topic-pcts">긍정 {{ t.sentiment.positive }}% · 부정 {{ t.sentiment.negative }}%</span>
            <span class="rpt-topic-count">{{ t.mentionCount }}건</span>
          </div>
        </div>
      </div>

      <div class="rpt-section">
        <h2 class="rpt-sec-title">주요 인사이트</h2>
        <div class="rpt-insights">
          <div v-for="ins in data.keyInsights" :key="ins.comment"
            class="rpt-insight" :class="ins.type">
            <div class="rpt-ins-meta">
              <span class="rpt-ins-badge">{{ ins.type === 'positive' ? '↑ 긍정' : '↓ 부정' }}</span>
              <span class="rpt-ins-topic">{{ ins.topic }}</span>
              <span class="rpt-ins-likes">♥ {{ fmtNum(ins.likes) }}</span>
            </div>
            <p class="rpt-ins-text">"{{ ins.comment }}"</p>
          </div>
        </div>
      </div>

      <div class="rpt-footer">
        <span>언어 분포 — 한국어 {{ data.video.languageRatio.ko }}%  ·  English {{ data.video.languageRatio.en }}%  ·  Other {{ data.video.languageRatio.other }}%</span>
        <span>유튜브 공개 댓글 API 기반 분석 · 미정 Analytics</span>
      </div>

    </div>
  </div>

  <!-- 토픽 댓글 드로어 -->
  <TopicComments
    v-if="selectedTopic && data"
    :video-id="data.video.videoId"
    :topic="selectedTopic"
    @close="selectedTopic = null"
  />
</template>

<style>
/* ── Print Report (항상 숨김 — 화면 그대로 출력) ── */
.print-report { display: none !important; }

.rpt-page {
  font-family: 'Inter', 'Apple SD Gothic Neo', sans-serif;
  color: #1a1a2e;
  padding: 14mm 16mm;
  max-width: 180mm;
  margin: 0 auto;
  font-size: 10pt;
  line-height: 1.5;
}

.rpt-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  border-bottom: 2px solid #7b5ef8;
  padding-bottom: 10px;
  margin-bottom: 12px;
}
.rpt-thumb {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}
.rpt-header-info { flex: 1; min-width: 0; }
.rpt-brand { font-size: 8pt; color: #7b5ef8; font-weight: 600; letter-spacing: .08em; margin-bottom: 4px; }
.rpt-title { font-size: 14pt; font-weight: 700; color: #1a1a2e; margin: 0 0 3px; line-height: 1.3; }
.rpt-channel { font-size: 9pt; color: #666680; }
.rpt-meta { text-align: right; font-size: 8pt; color: #999aaa; line-height: 1.8; flex-shrink: 0; margin-left: 4px; white-space: nowrap; }

.rpt-stats-row {
  display: flex;
  gap: 0;
  margin-bottom: 14px;
  border: 1px solid #e0e0eb;
  border-radius: 6px;
  overflow: hidden;
}
.rpt-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  border-right: 1px solid #e0e0eb;
}
.rpt-stat:last-child { border-right: none; }
.rpt-stat-val { font-size: 14pt; font-weight: 700; color: #1a1a2e; }
.rpt-stat-lbl { font-size: 7pt; color: #999aaa; margin-top: 1px; }

.rpt-section { margin-bottom: 14px; }
.rpt-sec-title {
  font-size: 8pt; font-weight: 700;
  text-transform: uppercase; letter-spacing: .1em;
  color: #666680; margin: 0 0 6px;
  padding-bottom: 3px; border-bottom: 0.5px solid #e0e0eb;
}

.rpt-sent-bar { display: flex; height: 10px; border-radius: 4px; overflow: hidden; margin-bottom: 4px; }
.rpt-bar-pos { background: #22c55e; }
.rpt-bar-neu { background: #94a3b8; }
.rpt-bar-neg { background: #f43f5e; }
.rpt-sent-labels { display: flex; gap: 14px; font-size: 8pt; }
.rpt-pos-txt { color: #16a34a; font-weight: 600; }
.rpt-neu-txt { color: #64748b; font-weight: 600; }
.rpt-neg-txt { color: #dc2626; font-weight: 600; }

.rpt-topics { display: flex; flex-direction: column; gap: 5px; }
.rpt-topic-row {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 8px; background: #f8f8fc;
  border-radius: 4px; border: 0.5px solid #e0e0eb;
}
.rpt-topic-num { font-size: 9pt; font-weight: 700; color: #7b5ef8; width: 12px; flex-shrink: 0; }
.rpt-topic-name { font-size: 9pt; font-weight: 600; color: #1a1a2e; width: 80px; flex-shrink: 0; }
.rpt-topic-bar { flex: 1; display: flex; height: 6px; border-radius: 2px; overflow: hidden; }
.rpt-topic-bar div { height: 100%; }
.rpt-topic-pcts { font-size: 7pt; color: #666680; white-space: nowrap; width: 90px; flex-shrink: 0; }
.rpt-topic-count { font-size: 9pt; font-weight: 700; color: #1a1a2e; width: 30px; text-align: right; flex-shrink: 0; }

.rpt-insights { display: flex; flex-direction: column; gap: 6px; }
.rpt-insight {
  padding: 7px 10px; border-radius: 4px; border-left: 3px solid;
}
.rpt-insight.positive { background: #f0fdf4; border-left-color: #22c55e; }
.rpt-insight.negative { background: #fff1f2; border-left-color: #f43f5e; }
.rpt-ins-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
.rpt-ins-badge { font-size: 7pt; font-weight: 700; }
.rpt-insight.positive .rpt-ins-badge { color: #16a34a; }
.rpt-insight.negative .rpt-ins-badge { color: #dc2626; }
.rpt-ins-topic { font-size: 7pt; color: #666680; }
.rpt-ins-likes { font-size: 7pt; color: #999aaa; margin-left: auto; }
.rpt-ins-text { font-size: 9pt; color: #1a1a2e; margin: 0; line-height: 1.5; }

.rpt-footer {
  margin-top: 14px; padding-top: 6px;
  border-top: 0.5px solid #e0e0eb;
  display: flex; justify-content: space-between;
  font-size: 7pt; color: #999aaa;
}
</style>

<style scoped>
/* ── 공통 래퍼 ── */
.home-view {
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 44px 52px;
  overflow: hidden;
}

.loading-mode {
  justify-content: center;
  align-items: center;
}

.dashboard-mode {
  justify-content: flex-start;
  overflow-y: auto;
  padding: 28px 32px;
  gap: var(--gap);
}

/* ── 히어로 ── */
.eyebrow {
  font-size: 11px;
  letter-spacing: .14em;
  color: var(--accent);
  font-weight: 600;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  opacity: 0.75;
}
.eyebrow::before {
  content: '';
  display: block;
  width: 20px; height: 1px;
  background: var(--accent);
}

.big-word {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(72px, 10vw, 118px);
  line-height: .88;
  color: var(--text);
  letter-spacing: -.01em;
  margin-bottom: 2px;
}
.big-word span {
  color: transparent;
  -webkit-text-stroke: 2px var(--outline-stroke);
}

.sub-line {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(32px, 4vw, 48px);
  line-height: 1.1;
  color: var(--accent);
  margin-bottom: 28px;
}

.search-wrap {
  display: flex;
  align-items: center;
  background: var(--search-bg);
  border: 0.5px solid var(--search-border);
  border-radius: var(--radius);
  padding: 6px 6px 6px 18px;
  max-width: 520px;
  margin-bottom: 10px;
  transition: border-color .2s;
  position: relative; z-index: 1;
}
.search-wrap.focused { border-color: rgba(123, 94, 248, 0.5); }

.yt-icon { color: #e03; flex-shrink: 0; margin-right: 10px; }

.url-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  padding: 10px 0;
}
.url-input::placeholder { color: var(--dim); }

.btn-go {
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  border: none;
  padding: 11px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
  transition: opacity .15s;
}
.btn-go:disabled { opacity: .4; cursor: not-allowed; }

.url-hint  { font-size: 12px; color: var(--dim); margin-bottom: 32px; position: relative; z-index: 1; }
.url-error { font-size: 12px; color: var(--negative); margin-bottom: 32px; position: relative; z-index: 1; }

.platform-chips { display: flex; gap: 10px; flex-wrap: wrap; position: relative; z-index: 1; }
.chip {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px;
  color: var(--chip-color);
  border: 0.5px solid var(--chip-border);
  background: transparent;
  padding: 5px 12px;
  border-radius: 20px;
}
.chip.active { color: var(--chip-active); border-color: var(--chip-active-bd); }
.chip.soon   { color: var(--dim); }
.chip-live   { color: var(--positive); font-size: 10px; }
.chip-badge  {
  font-size: 9px;
  background: rgba(123, 94, 248, 0.15);
  color: var(--accent);
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

/* 로딩 중 취소 버튼 */
.analyzing-back {
  position: absolute;
  top: 24px; left: 24px;
}

/* ── 대시보드 ── */
.dash-topbar { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.back-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px;
  color: var(--dim);
  background: transparent;
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 5px 12px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: color .15s;
}
.back-btn:hover { color: var(--subtext); }
.export-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px;
  color: var(--accent);
  background: rgba(123, 94, 248, 0.08);
  border: 0.5px solid rgba(123, 94, 248, 0.35);
  border-radius: 8px;
  padding: 5px 12px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: background .15s, border-color .15s;
  margin-left: auto;
}
.export-btn:hover { background: rgba(123, 94, 248, 0.14); border-color: rgba(123, 94, 248, 0.55); }

.dash-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--gap);
}
.dash-col-1 { min-width: 0; }
.dash-col-2 { min-width: 0; }

.dash-divider {
  display: flex; align-items: center; gap: 14px;
  font-size: 10px;
  letter-spacing: .1em;
  color: var(--dim);
}
.dash-divider .line { flex: 1; height: 0.5px; background: var(--divider-line); }

/* ── 분석 지표 카드 ── */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--gap);
}
.metric-card {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.metric-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--subtext);
}
.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  line-height: 1.3;
}
.mval-pos { color: var(--positive); }
.mval-neg { color: var(--negative); }
.metric-desc {
  font-size: 10px;
  color: var(--dim);
}
</style>
