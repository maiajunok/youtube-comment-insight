<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { messages } from '@/locales/messages'
import { storeToRefs } from 'pinia'
import { useHistory } from '@/features/insight/composables/useHistory'
import { fillTopicLabels, displayLabel } from '@/features/insight/composables/useLabelTranslation'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { useAnalysisStore } from '@/features/insight/stores/analysis'
import { useRouter, useRoute } from 'vue-router'
import { insightApi } from '@/features/insight/api/insightApi'
import VideoInfoCard     from '@/features/insight/components/VideoInfoCard.vue'
import TopReactionTopics from '@/features/insight/components/TopReactionTopics.vue'
import ReactionTimeline  from '@/features/insight/components/ReactionTimeline.vue'
import KeyInsights       from '@/features/insight/components/KeyInsights.vue'
import LoadingState      from '@/features/insight/components/LoadingState.vue'
import TopicComments     from '@/features/insight/components/TopicComments.vue'
import AppFooter         from '@/layouts/AppFooter.vue'

const router        = useRouter()
const route         = useRoute()
const settings      = useSettingsStore()
const analysisStore = useAnalysisStore()

const url           = ref('')
const isFocused     = ref(false)
const selectedTopic = ref<string | null>(null)

// 분석 상태는 store에서 직접 읽음 — storeToRefs로 반응성 보장
const { result: data, isAnalyzing: isLoading, loadingStep, loadingProgress, analysisError: error, missingKeyModal, resultSource } =
  storeToRefs(analysisStore)

const selectedTopicDisplay = computed(() => {
  if (!selectedTopic.value || !data.value) return selectedTopic.value ?? undefined
  const t = data.value.topics.find(t => t.label === selectedTopic.value)
  return t ? displayLabel(t, settings.lang) : selectedTopic.value
})

function goToSettings() {
  analysisStore.closeMissingKeyModal()
  router.push({ name: 'settings' })
}
function goToHistory() {
  analysisStore.closeMissingKeyModal()
  router.push({ name: 'history' })
}

// 새로고침해도 히스토리에서 보던 영상이 유지되도록 URL의 id로 다시 불러옴
onMounted(async () => {
  const id = route.query.id
  if (route.name === 'history-view' && typeof id === 'string' && !data.value) {
    try {
      const result = await insightApi.getByVideoId(id)
      analysisStore.setResult(result)
    } catch {
      router.push({ name: 'history' })
    }
  }
})

watch(() => settings.lang, (lang) => {
  if (data.value) fillTopicLabels(data.value.topics, lang)
})

watch(data, (d) => {
  if (d) fillTopicLabels(d.topics, settings.lang)
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

// 다시 분석하기 — 캐시 삭제 후 같은 URL로 재분석. analysisStore가 전역 상태라
// 이 함수 실행 중에 다른 페이지로 이동해도 백그라운드에서 계속 진행됨
async function reAnalyze() {
  if (!data.value || analysisStore.isAnalyzing) return
  const videoId = data.value.video.videoId
  const rebuiltUrl = `https://www.youtube.com/watch?v=${videoId}`
  await insightApi.deleteCache(videoId)
  await analysisStore.startAnalysis(rebuiltUrl, (id, d) => {
    useHistory().save(id, d)
  })
  if (analysisStore.result) analysisStore.resultSource = 'history'
}

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

// ── PDF 리포트 ──
const donutGradient = computed(() => {
  const s = overallSentiment.value
  const posEnd = s.positive
  const neuEnd = s.positive + s.neutral
  return `conic-gradient(#16a34a 0% ${posEnd}%, #94a3b8 ${posEnd}% ${neuEnd}%, #dc2626 ${neuEnd}% 100%)`
})

const reportTopicLabel = (t: { label: string; labelEn?: string; labelZh?: string; labelJa?: string }) =>
  displayLabel(t, settings.lang)

const reportInsightTopic = (ins: { topic: string; topicEn?: string; topicZh?: string; topicJa?: string }) => {
  if (settings.lang === 'en') return ins.topicEn || ins.topic
  if (settings.lang === 'zh') return ins.topicZh || ins.topic
  if (settings.lang === 'ja') return ins.topicJa || ins.topic
  return ins.topic
}

const reportInsightComment = (ins: { comment: string; commentEn?: string; commentZh?: string; commentJa?: string }) => {
  if (settings.lang === 'en') return ins.commentEn || ins.comment
  if (settings.lang === 'zh') return ins.commentZh || ins.comment
  if (settings.lang === 'ja') return ins.commentJa || ins.comment
  return ins.comment
}
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

    <div class="search-row">
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
      </div>
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

    <AppFooter />
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

      <!-- 분석기록에서 열었을 때만 PDF 내보내기 표시 (다시 분석하기는 VideoInfoCard의 분석일자 옆에) -->
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
        <VideoInfoCard
          :video="data.video"
          :lang="settings.lang"
          :analyzed-at="data.analyzedAt"
          :show-reanalyze="resultSource === 'history'"
          :reanalyzing="analysisStore.isAnalyzing"
          @reanalyze="reAnalyze"
        />
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
      <div class="rpt-topbar" />

      <div class="rpt-header">
        <img :src="data.video.thumbnailUrl" class="rpt-thumb" />
        <div class="rpt-header-info">
          <div class="rpt-brand">FindComments · {{ messages[settings.lang].reportBrandTagline }}</div>
          <h1 class="rpt-title">{{ data.video.title }}</h1>
          <div class="rpt-channel">{{ data.video.channelTitle }}</div>
        </div>
        <div class="rpt-meta">
          <div>{{ messages[settings.lang].uploadDate }} {{ data.video.publishedAt.slice(0, 10) }}</div>
          <div>{{ messages[settings.lang].reportGeneratedOn }} {{ new Date().toLocaleDateString() }}</div>
        </div>
      </div>

      <div class="rpt-hero">
        <div class="rpt-donut-block">
          <div class="rpt-donut" :style="`background:${donutGradient}`">
            <div class="rpt-donut-hole">
              <span class="rpt-donut-score" :class="sentimentScore > 0 ? 'pos' : sentimentScore < 0 ? 'neg' : ''">{{ sentimentScore > 0 ? '+' : '' }}{{ sentimentScore }}</span>
              <span class="rpt-donut-score-lbl">{{ messages[settings.lang].sentimentScore }}</span>
            </div>
          </div>
          <div class="rpt-donut-legend">
            <div class="rpt-legend-row"><span class="rpt-dot pos" />{{ messages[settings.lang].positive }}<b>{{ overallSentiment.positive }}%</b></div>
            <div class="rpt-legend-row"><span class="rpt-dot neu" />{{ messages[settings.lang].neutral }}<b>{{ overallSentiment.neutral }}%</b></div>
            <div class="rpt-legend-row"><span class="rpt-dot neg" />{{ messages[settings.lang].negative }}<b>{{ overallSentiment.negative }}%</b></div>
          </div>
        </div>

        <div class="rpt-stats-grid">
          <div class="rpt-stat"><span class="rpt-stat-val">{{ fmtNum(data.video.viewCount) }}</span><span class="rpt-stat-lbl">{{ messages[settings.lang].views }}</span></div>
          <div class="rpt-stat"><span class="rpt-stat-val">{{ fmtNum(data.video.likeCount) }}</span><span class="rpt-stat-lbl">{{ messages[settings.lang].likes }}</span></div>
          <div class="rpt-stat"><span class="rpt-stat-val">{{ fmtNum(data.video.analyzedComments) }}</span><span class="rpt-stat-lbl">{{ messages[settings.lang].analyzedComments }}</span></div>
          <div class="rpt-stat"><span class="rpt-stat-val">{{ commentRate !== null ? commentRate + '%' : '—' }}</span><span class="rpt-stat-lbl">{{ messages[settings.lang].commentRate }}</span></div>
        </div>
      </div>

      <div class="rpt-section">
        <h2 class="rpt-sec-title">{{ messages[settings.lang].topReactionTopics }}</h2>
        <div class="rpt-topics">
          <div v-for="(t, i) in data.topics" :key="t.label" class="rpt-topic-row">
            <span class="rpt-topic-num">{{ i + 1 }}</span>
            <span class="rpt-topic-name">{{ reportTopicLabel(t) }}</span>
            <div class="rpt-topic-bar">
              <div :style="`width:${t.sentiment.positive}%; background:#16a34a`"></div>
              <div :style="`width:${t.sentiment.neutral}%; background:#94a3b8`"></div>
              <div :style="`width:${t.sentiment.negative}%; background:#dc2626`"></div>
            </div>
            <span class="rpt-topic-pcts">{{ messages[settings.lang].positive }} {{ t.sentiment.positive }}% · {{ messages[settings.lang].negative }} {{ t.sentiment.negative }}%</span>
            <span class="rpt-topic-count">{{ t.mentionCount }}</span>
          </div>
        </div>
      </div>

      <div class="rpt-section">
        <h2 class="rpt-sec-title">{{ messages[settings.lang].keyInsights }}</h2>
        <div class="rpt-insights">
          <div v-for="ins in data.keyInsights" :key="ins.comment"
            class="rpt-insight" :class="ins.type">
            <div class="rpt-ins-meta">
              <span class="rpt-ins-badge">{{ ins.type === 'positive' ? messages[settings.lang].positiveLabel : messages[settings.lang].negativeLabel }}</span>
              <span class="rpt-ins-topic">{{ reportInsightTopic(ins) }}</span>
              <span class="rpt-ins-likes">♥ {{ fmtNum(ins.likes) }}</span>
            </div>
            <p class="rpt-ins-text">"{{ reportInsightComment(ins) }}"</p>
          </div>
        </div>
      </div>

      <div class="rpt-section">
        <h2 class="rpt-sec-title">{{ messages[settings.lang].langBreakdown }}</h2>
        <div class="rpt-lang-grid">
          <div class="rpt-lang-stat">
            <span class="rpt-lang-val ko">{{ data.video.languageRatio.ko }}%</span>
            <span class="rpt-lang-lbl">한국어</span>
          </div>
          <div class="rpt-lang-stat">
            <span class="rpt-lang-val en">{{ data.video.languageRatio.en }}%</span>
            <span class="rpt-lang-lbl">English</span>
          </div>
          <div class="rpt-lang-stat">
            <span class="rpt-lang-val other">{{ data.video.languageRatio.other }}%</span>
            <span class="rpt-lang-lbl">Other</span>
          </div>
        </div>
      </div>

      <div class="rpt-footer">
        <span>{{ messages[settings.lang].reportFooterNote }}</span>
        <span>FindComments by github.com/maiajunok</span>
      </div>

    </div>
  </div>

  <!-- 토픽 댓글 드로어 -->
  <TopicComments
    v-if="selectedTopic && data"
    :video-id="data.video.videoId"
    :topic="selectedTopic"
    :display-topic="selectedTopicDisplay"
    @close="selectedTopic = null"
  />

  <!-- API 키 필요 모달 -->
  <div v-if="missingKeyModal" class="key-modal-overlay" @click.self="analysisStore.closeMissingKeyModal()">
    <div class="key-modal">
      <div class="key-modal-icon-badge">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8">
          <rect x="3" y="11" width="18" height="10" rx="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>
      <h2 class="key-modal-title">{{ messages[settings.lang].keyModalTitle }}</h2>
      <p class="key-modal-body">{{ messages[settings.lang].keyModalBody1 }}</p>
      <p class="key-modal-body dim">{{ messages[settings.lang].keyModalBody2 }}</p>
      <div class="key-modal-actions">
        <button class="key-modal-btn primary" @click="goToSettings">{{ messages[settings.lang].keyModalSettingsBtn }}</button>
        <button class="key-modal-btn" @click="goToHistory">{{ messages[settings.lang].keyModalHistoryBtn }}</button>
      </div>
      <button class="key-modal-close" @click="analysisStore.closeMissingKeyModal()">{{ messages[settings.lang].keyModalClose }}</button>
    </div>
  </div>
</template>

<style>
/* ── Print Report (화면에서는 숨김, 인쇄 시에만 App.vue의 @media print에서 표시) ── */
@media screen {
  .print-report { display: none; }
}

.rpt-page {
  position: relative;
  font-family: 'Inter', 'Apple SD Gothic Neo', sans-serif;
  color: #1a1a2e;
  background: #ffffff;
  padding: 12mm 16mm 14mm;
  max-width: 180mm;
  margin: 0 auto;
  font-size: 10pt;
  line-height: 1.5;
}

.rpt-topbar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: #E4002B;
}

.rpt-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  border-bottom: 1px solid #e0e0eb;
  padding-bottom: 12px;
  margin-bottom: 16px;
}
.rpt-thumb {
  width: 84px;
  height: 47px;
  object-fit: cover;
  border-radius: 5px;
  flex-shrink: 0;
  border: 0.5px solid #e0e0eb;
}
.rpt-header-info { flex: 1; min-width: 0; }
.rpt-brand { font-size: 8pt; color: #E4002B; font-weight: 700; letter-spacing: .08em; margin-bottom: 5px; }
.rpt-title { font-size: 14pt; font-weight: 700; color: #1a1a2e; margin: 0 0 3px; line-height: 1.3; }
.rpt-channel { font-size: 9pt; color: #666680; }
.rpt-meta { text-align: right; font-size: 8pt; color: #999aaa; line-height: 1.8; flex-shrink: 0; margin-left: 4px; white-space: nowrap; }

/* ── 히어로: 도넛 차트 + 통계 ── */
.rpt-hero {
  display: flex;
  gap: 20px;
  align-items: stretch;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e0e0eb;
}

.rpt-donut-block {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  padding-right: 20px;
  border-right: 1px solid #e0e0eb;
}
.rpt-donut {
  position: relative;
  width: 78px;
  height: 78px;
  border-radius: 50%;
  flex-shrink: 0;
}
.rpt-donut-hole {
  position: absolute;
  inset: 12px;
  background: #ffffff;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 0.5px #e0e0eb;
}
.rpt-donut-score { font-size: 13pt; font-weight: 800; color: #1a1a2e; line-height: 1; }
.rpt-donut-score.pos { color: #16a34a; }
.rpt-donut-score.neg { color: #dc2626; }
.rpt-donut-score-lbl { font-size: 6pt; color: #999aaa; text-transform: uppercase; letter-spacing: .06em; margin-top: 2px; }

.rpt-donut-legend { display: flex; flex-direction: column; gap: 5px; }
.rpt-legend-row {
  display: flex; align-items: center; gap: 6px;
  font-size: 8pt; color: #666680; white-space: nowrap;
}
.rpt-legend-row b { color: #1a1a2e; margin-left: auto; padding-left: 10px; }
.rpt-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.rpt-dot.pos { background: #16a34a; }
.rpt-dot.neu { background: #94a3b8; }
.rpt-dot.neg { background: #dc2626; }

.rpt-stats-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.rpt-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6px 4px;
}
.rpt-stat-val { font-size: 13pt; font-weight: 700; color: #1a1a2e; }
.rpt-stat-lbl { font-size: 7pt; color: #999aaa; margin-top: 2px; text-align: center; }

.rpt-section { margin-bottom: 12px; }
.rpt-sec-title {
  font-size: 8pt; font-weight: 700;
  text-transform: uppercase; letter-spacing: .1em;
  color: #666680; margin: 0 0 6px;
  padding-bottom: 3px; border-bottom: 0.5px solid #e0e0eb;
}

.rpt-topics { display: flex; flex-direction: column; }
.rpt-topic-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 2px;
  border-bottom: 0.5px solid #e0e0eb;
}
.rpt-topic-row:last-child { border-bottom: none; }
.rpt-topic-num { font-size: 9pt; font-weight: 700; color: #E4002B; width: 12px; flex-shrink: 0; }
.rpt-topic-name { font-size: 9pt; font-weight: 600; color: #1a1a2e; width: 80px; flex-shrink: 0; }
.rpt-topic-bar { flex: 1; display: flex; height: 6px; border-radius: 2px; overflow: hidden; }
.rpt-topic-bar div { height: 100%; }
.rpt-topic-pcts { font-size: 7pt; color: #666680; white-space: nowrap; width: 90px; flex-shrink: 0; }
.rpt-topic-count { font-size: 9pt; font-weight: 700; color: #1a1a2e; width: 30px; text-align: right; flex-shrink: 0; }

.rpt-insights {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 14px;
}
.rpt-insight {
  padding: 2px 0 2px 10px; border-left: 2px solid;
}
.rpt-insight.positive { border-left-color: #16a34a; }
.rpt-insight.negative { border-left-color: #dc2626; }
.rpt-ins-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
.rpt-ins-badge { font-size: 7pt; font-weight: 700; }
.rpt-insight.positive .rpt-ins-badge { color: #16a34a; }
.rpt-insight.negative .rpt-ins-badge { color: #dc2626; }
.rpt-ins-topic { font-size: 7pt; color: #666680; }
.rpt-ins-likes { font-size: 7pt; color: #999aaa; margin-left: auto; }
.rpt-ins-text { font-size: 8.5pt; color: #1a1a2e; margin: 0; line-height: 1.5; }

.rpt-lang-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  text-align: center;
}
.rpt-lang-stat { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.rpt-lang-val { font-size: 15pt; font-weight: 800; }
.rpt-lang-val.ko { color: #E4002B; }
.rpt-lang-val.en { color: #16a34a; }
.rpt-lang-val.other { color: #94a3b8; }
.rpt-lang-lbl { font-size: 7.5pt; color: #999aaa; }

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

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 620px;
  margin-bottom: 10px;
  position: relative; z-index: 1;
}

.search-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  background: var(--search-bg);
  border: 0.5px solid var(--search-border);
  border-radius: var(--radius);
  padding: 12px 16px;
  transition: border-color .2s;
}
.search-wrap.focused { border-color: rgb(from var(--accent) r g b / 0.5); }

.yt-icon { color: #e03; flex-shrink: 0; margin-right: 10px; }

.url-input {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
}
.url-input::placeholder { color: var(--dim); }

.btn-go {
  flex-shrink: 0;
  background: var(--accent);
  color: var(--cta-text);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .01em;
  border: none;
  padding: 13px 26px;
  border-radius: var(--radius);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
  transition: opacity .15s;
}
.btn-go:hover:not(:disabled) { opacity: 0.88; }
.btn-go:disabled { opacity: .4; cursor: not-allowed; box-shadow: none; }

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
  background: rgb(from var(--accent) r g b / 0.15);
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
  color: var(--text);
  background: transparent;
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 5px 12px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: background .15s, border-color .15s;
  margin-left: auto;
}
.export-btn:hover { background: rgb(from var(--accent) r g b / 0.06); border-color: rgb(from var(--accent) r g b / 0.4); }

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

/* ── API 키 필요 모달 ── */
.key-modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: radial-gradient(circle at 50% 40%, rgb(from var(--accent) r g b / 0.10), rgba(8, 6, 16, 0.72) 60%);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
  animation: key-modal-fade-in 0.2s ease-out;
}
@keyframes key-modal-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.key-modal {
  position: relative;
  background: linear-gradient(180deg, var(--card-hover) 0%, var(--card) 60%);
  border: 0.5px solid rgb(from var(--accent) r g b / 0.28);
  border-radius: 20px;
  padding: 36px 34px 30px;
  max-width: 430px;
  width: 100%;
  display: flex; flex-direction: column; align-items: flex-start; gap: 4px;
  box-shadow:
    0 24px 70px rgba(0,0,0,0.45),
    0 0 0 1px rgba(255,255,255,0.02) inset,
    0 0 60px rgb(from var(--accent) r g b / 0.10);
  animation: key-modal-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes key-modal-pop {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.key-modal-icon-badge {
  width: 52px; height: 52px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, color-mix(in srgb, var(--accent), white 35%) 0%, var(--accent) 55%, color-mix(in srgb, var(--accent), black 40%) 100%);
  box-shadow: 0 8px 24px rgb(from var(--accent) r g b / 0.45), 0 0 0 1px rgba(255,255,255,0.08) inset;
  margin-bottom: 18px;
}

.key-modal-title {
  font-size: 19px; font-weight: 700; color: var(--text);
  letter-spacing: -.01em;
  margin-bottom: 8px;
}
.key-modal-body { font-size: 13px; color: var(--subtext); line-height: 1.7; margin-bottom: 4px; }
.key-modal-body.dim { color: var(--dim); }

.key-modal-actions { display: flex; gap: 10px; margin-top: 22px; width: 100%; }
.key-modal-btn {
  flex: 1;
  font-size: 13px; font-weight: 600;
  border: 0.5px solid var(--border);
  background: var(--card-hover);
  color: var(--subtext);
  padding: 11px 16px; border-radius: 10px;
  cursor: pointer; font-family: 'Inter', sans-serif;
  transition: transform 0.15s, border-color 0.15s, background 0.15s, box-shadow 0.15s;
}
.key-modal-btn:hover { transform: translateY(-1px); border-color: rgba(192,171,126,0.45); }
.key-modal-btn.primary {
  background: var(--accent);
  border-color: transparent;
  color: var(--cta-text);
}
.key-modal-btn.primary:hover { opacity: 0.88; }

.key-modal-close {
  margin-top: 16px;
  font-size: 12px; color: var(--dim);
  background: transparent; border: none;
  cursor: pointer; font-family: 'Inter', sans-serif;
  align-self: center;
  width: 100%;
  text-align: center;
  transition: color 0.15s;
}
.key-modal-close:hover { color: var(--subtext); }

/* ── 모바일 ── */
@media (max-width: 768px) {
  .home-view { padding: 28px 20px; }
  .dashboard-mode { padding: 18px 16px; }

  .big-word { font-size: clamp(48px, 15vw, 72px); }
  .sub-line { font-size: clamp(24px, 7vw, 36px); margin-bottom: 20px; }

  .search-row { flex-direction: column; align-items: stretch; max-width: 100%; gap: 10px; }
  .search-wrap { padding: 12px 14px; }
  .btn-go { width: 100%; padding: 13px; }

  .dash-topbar { flex-wrap: wrap; gap: 8px; }
  .export-btn { margin-left: 0; }

  .dash-grid { grid-template-columns: 1fr; }

  .metrics-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
