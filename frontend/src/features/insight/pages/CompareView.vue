<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { insightApi } from '@/features/insight/api/insightApi'
import type { HistoryItem, InsightData } from '@/features/insight/types/insight'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'
import { fillTopicLabels, displayLabel } from '@/features/insight/composables/useLabelTranslation'

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])

const history = ref<HistoryItem[]>([])
const isLoadingHistory = ref(true)
const historyError = ref('')
const selected = ref<string[]>([])
const comparisons = ref<InsightData[]>([])
const isComparing = ref(false)
const compareError = ref('')
const phase = ref<'select' | 'compare'>('select')
const headerCollapsed = ref(false)

onMounted(async () => {
  try {
    history.value = await insightApi.getHistory()
  } catch {
    historyError.value = '기록을 불러오지 못했습니다.'
  } finally {
    isLoadingHistory.value = false
  }
})

const toggle = (id: string) => {
  const i = selected.value.indexOf(id)
  if (i !== -1) { selected.value.splice(i, 1) }
  else if (selected.value.length < 3) { selected.value.push(id) }
}

const isSelected = (id: string) => selected.value.includes(id)
const selIndex = (id: string) => selected.value.indexOf(id) + 1

const doCompare = async () => {
  if (selected.value.length < 2) return
  isComparing.value = true
  compareError.value = ''
  try {
    comparisons.value = await Promise.all(
      selected.value.map(id => insightApi.getByVideoId(id))
    )
    await fillTopicLabels(comparisons.value.flatMap(d => d.topics), settings.lang)
    phase.value = 'compare'
  } catch {
    compareError.value = '데이터를 불러오지 못했습니다.'
  } finally {
    isComparing.value = false
  }
}

watch(() => settings.lang, (lang) => {
  if (comparisons.value.length) fillTopicLabels(comparisons.value.flatMap(d => d.topics), lang)
})

const reset = () => {
  phase.value = 'select'
  comparisons.value = []
  headerCollapsed.value = false
}

const onPageScroll = (e: Event) => {
  headerCollapsed.value = (e.target as HTMLElement).scrollTop > 60
}

const overallSentiment = (data: InsightData) => {
  let pos = 0, neu = 0, neg = 0, total = 0
  data.topics.forEach(t => {
    pos += t.sentiment.positive * t.mentionCount
    neu += t.sentiment.neutral * t.mentionCount
    neg += t.sentiment.negative * t.mentionCount
    total += t.mentionCount
  })
  if (!total) return { positive: 0, neutral: 0, negative: 0 }
  return {
    positive: Math.round(pos / total),
    neutral: Math.round(neu / total),
    negative: Math.round(neg / total),
  }
}

const commonTopics = computed(() => {
  if (comparisons.value.length < 2) return []
  const sets = comparisons.value.map(d => new Set(d.topics.map(t => t.label)))
  const commonLabels = [...sets[0]].filter(label => sets.slice(1).every(s => s.has(label)))
  return commonLabels.map(label => comparisons.value[0].topics.find(t => t.label === label)!)
})

const langRatio = (data: InsightData, key: string): number =>
  (data.video.languageRatio as Record<string, number>)[key] ?? 0

const fmtNum = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K'     :
  String(n)

const COL = ['#7b5ef8', '#22c55e', '#f59e0b']

const cCommentRate = (d: InsightData) => {
  if (!d.video.viewCount) return '—'
  return (d.video.analyzedComments / d.video.viewCount * 100).toFixed(2) + '%'
}
const cLikeRate = (d: InsightData) => {
  if (!d.video.viewCount) return '—'
  return (d.video.likeCount / d.video.viewCount * 100).toFixed(2) + '%'
}
const cSentimentScore = (d: InsightData) => overallSentiment(d).positive - overallSentiment(d).negative
const cControversyScore = (d: InsightData) => {
  const s = overallSentiment(d)
  return Math.min(s.positive, s.negative) * 2
}
</script>

<template>
  <!-- ── 선택 단계 ── -->
  <div v-if="phase === 'select'" class="cpage">

    <div class="cpage-header">
      <div>
        <h1 class="cpage-title">{{ M.navCompare }}</h1>
        <p class="cpage-sub">{{ M.compareSub }}</p>
      </div>
      <div class="header-actions">
        <div v-if="selected.length" class="sel-pips">
          <span v-for="(_, i) in selected" :key="i" class="sel-pip" :style="`background:${COL[i]}`" />
          <span class="sel-count-txt">{{ settings.lang === 'ko' ? `${selected.length}개 선택됨` : settings.lang === 'zh' ? `已选${selected.length}个` : settings.lang === 'ja' ? `${selected.length}件選択中` : `${selected.length} selected` }}</span>
        </div>
        <p v-if="compareError" class="err-inline">{{ compareError }}</p>
        <button class="do-compare-btn" :disabled="selected.length < 2 || isComparing" @click="doCompare">
          <svg v-if="isComparing" class="spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          {{ isComparing ? M.comparing : M.compareBtn }}
        </button>
      </div>
    </div>

    <p v-if="historyError" class="err-msg">{{ historyError }}</p>

    <div v-if="isLoadingHistory" class="state-center"><p>{{ M.loading }}</p></div>

    <div v-else-if="!history.length" class="state-center">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:var(--subtext)">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
      </svg>
      <p>{{ M.compareNone }}</p>
    </div>

    <div v-else class="sel-grid">
      <div
        v-for="item in history"
        :key="item.videoId"
        class="sel-card"
        :class="{
          'sel-card--on': isSelected(item.videoId),
          'sel-card--dim': !isSelected(item.videoId) && selected.length >= 3
        }"
        @click="toggle(item.videoId)"
      >
        <div v-if="isSelected(item.videoId)" class="sel-badge" :style="`background:${COL[selIndex(item.videoId)-1]}`">
          {{ selIndex(item.videoId) }}
        </div>
        <div class="sc-thumb">
          <img :src="item.thumbnailUrl" :alt="item.title"
            @error="($event.target as HTMLImageElement).style.opacity='0'" />
          <div v-if="isSelected(item.videoId)" class="sc-overlay">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
        </div>
        <div class="sc-body">
          <p class="sc-title">{{ item.title }}</p>
          <p class="sc-channel">{{ item.channelTitle }}</p>
          <div class="sc-stats">
            <span>{{ M.colCommentCount }} {{ fmtNum(item.analyzedComments) }}</span>
            <span>·</span>
            <span style="color:var(--positive)">{{ M.positive }} {{ item.overallSentiment.positive }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── 비교 결과 ── -->
  <div v-else class="cpage" @scroll="onPageScroll">

    <div class="res-nav">
      <button class="back-btn" @click="reset">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        {{ M.reselect }}
      </button>
      <div class="legend">
        <div v-for="(d, i) in comparisons" :key="d.video.videoId" class="legend-item">
          <span class="legend-dot" :style="`background:${COL[i]}`" />
          <span class="legend-label">{{ d.video.channelTitle }}</span>
        </div>
      </div>
    </div>

    <!-- 비교 테이블 -->
    <div class="ct-wrap">

      <!-- ── 영상 헤더 행 (sticky) ── -->
      <div class="ct-row ct-header-row" :class="{ 'ct-header-row--collapsed': headerCollapsed }">
        <div class="ct-corner" />
        <div v-for="(d, i) in comparisons" :key="d.video.videoId" class="ct-vh">
          <div class="ct-vh-accent" :style="`background:${COL[i]}`" />
          <div class="ct-vh-thumb">
            <img :src="d.video.thumbnailUrl" :alt="d.video.title"
              @error="($event.target as HTMLImageElement).style.opacity='0'" />
          </div>
          <div class="ct-vh-body">
            <p class="ct-vh-title">{{ d.video.title }}</p>
            <p class="ct-vh-ch">{{ d.video.channelTitle }}</p>
          </div>
        </div>
      </div>

      <!-- ── 기본 정보 ── -->
      <div class="ct-sec">{{ M.sectionBasic }}</div>

      <div class="ct-row">
        <div class="ct-lbl">{{ M.views }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          {{ fmtNum(d.video.viewCount) }}
        </div>
      </div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.likes }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          {{ fmtNum(d.video.likeCount) }}
        </div>
      </div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.colCommentCount }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          {{ fmtNum(d.video.analyzedComments) }}
        </div>
      </div>

      <!-- ── 분석 지표 ── -->
      <div class="ct-sec">{{ settings.lang === 'ko' ? '분석 지표' : settings.lang === 'ja' ? '分析指標' : settings.lang === 'zh' ? '分析指标' : 'Analysis Metrics' }}</div>

      <div class="ct-row">
        <div class="ct-lbl">{{ M.commentRate }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          {{ cCommentRate(d) }}
        </div>
      </div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.likeRate }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          {{ cLikeRate(d) }}
        </div>
      </div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.sentimentScore }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          <span :style="cSentimentScore(d) > 0 ? 'color:var(--positive);font-weight:700' : cSentimentScore(d) < 0 ? 'color:var(--negative);font-weight:700' : ''">
            {{ cSentimentScore(d) > 0 ? '+' : '' }}{{ cSentimentScore(d) }}
          </span>
        </div>
      </div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.controversy }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          {{ cControversyScore(d) }}
        </div>
      </div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.weightedSentiment }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell">
          <span v-if="d.video.weightedSentiment !== undefined"
            :style="d.video.weightedSentiment > 0 ? 'color:var(--positive);font-weight:700' : d.video.weightedSentiment < 0 ? 'color:var(--negative);font-weight:700' : ''">
            {{ d.video.weightedSentiment > 0 ? '+' : '' }}{{ d.video.weightedSentiment }}
          </span>
          <span v-else style="color:var(--dim)">—</span>
        </div>
      </div>

      <!-- ── 감정 분포 ── -->
      <div class="ct-sec">{{ M.sectionSentiment }}</div>

      <div class="ct-row">
        <div class="ct-lbl">{{ M.overallLabel }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell ct-cell--col">
          <div class="sent-bar">
            <div class="sb-pos" :style="`width:${overallSentiment(d).positive}%`" />
            <div class="sb-neu" :style="`width:${overallSentiment(d).neutral}%`" />
            <div class="sb-neg" :style="`width:${overallSentiment(d).negative}%`" />
          </div>
          <div class="sent-nums">
            <span class="sn-pos">{{ M.positive }} {{ overallSentiment(d).positive }}%</span>
            <span class="sn-neu">{{ M.neutral }} {{ overallSentiment(d).neutral }}%</span>
            <span class="sn-neg">{{ M.negative }} {{ overallSentiment(d).negative }}%</span>
          </div>
        </div>
      </div>

      <!-- ── 상위 토픽 ── -->
      <div class="ct-sec">{{ M.sectionTopics }}</div>
      <div class="ct-row">
        <div class="ct-lbl">{{ M.colTopic }}</div>
        <div v-for="d in comparisons" :key="d.video.videoId" class="ct-cell ct-cell--col" style="align-items:flex-start">
          <div class="topic-pills">
            <span v-for="t in d.topics.slice(0, 5)" :key="t.label" class="topic-pill-sm">
              {{ displayLabel(t, settings.lang) }}
            </span>
          </div>
        </div>
      </div>

      <!-- ── 공통 주제 (있을 때만) ── -->
      <template v-if="commonTopics.length">
        <div class="ct-sec">{{ M.sectionCommonTopics }}</div>
        <div class="ct-row">
          <div class="ct-lbl">{{ M.colCommon }}</div>
          <div class="ct-cell" style="flex:1; flex-wrap:wrap; gap:6px; align-items:center;">
            <span v-for="t in commonTopics" :key="t.label" class="topic-pill-sm">{{ displayLabel(t, settings.lang) }}</span>
          </div>
        </div>
      </template>

      <!-- ── 언어 분포 ── -->
      <div class="ct-sec">{{ M.sectionLangDist }}</div>

      <div v-for="[key, lbl] in [['ko','한국어 / Korean'],['en','English'],['other','Other']]" :key="key" class="ct-row">
        <div class="ct-lbl">{{ lbl }}</div>
        <div v-for="(d, i) in comparisons" :key="d.video.videoId" class="ct-cell">
          <div class="lbar-row">
            <div class="lbar-track">
              <div class="lbar-fill" :style="`width:${langRatio(d, key)}%;background:${COL[i]}`" />
            </div>
            <span class="lbar-pct">{{ langRatio(d, key) }}%</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* ── 공통 페이지 컨테이너 ── */
.cpage {
  position: relative;
  z-index: 2;
  flex: 1;
  overflow-y: auto;
  padding: 36px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── 선택 헤더 ── */
.cpage-header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.cpage-title { font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.cpage-sub { font-size: 13px; color: var(--subtext); margin-top: 4px; }
.header-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.sel-pips { display: flex; align-items: center; gap: 6px; }
.sel-pip { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.sel-count-txt { font-size: 12px; color: var(--subtext); }
.err-inline { font-size: 12px; color: #f87171; }
.err-msg { font-size: 13px; color: #f87171; }

.do-compare-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 9px 20px; border-radius: 8px;
  font-size: 13px; font-weight: 600; font-family: 'Inter', sans-serif;
  cursor: pointer; background: var(--accent); color: #fff; border: none;
  transition: opacity 0.15s;
}
.do-compare-btn:disabled { opacity: 0.35; cursor: default; }
.do-compare-btn:not(:disabled):hover { opacity: 0.85; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.8s linear infinite; }

/* ── 빈 상태 ── */
.state-center {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 12px; padding: 80px 0;
  font-size: 13px; color: var(--subtext); text-align: center;
}

/* ── 선택 그리드 ── */
.sel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--gap);
}
.sel-card {
  position: relative;
  border-radius: var(--radius); border: 0.5px solid var(--border);
  background: var(--card); overflow: hidden; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.12s;
  user-select: none;
}
.sel-card:hover:not(.sel-card--dim) { border-color: rgba(123,94,248,0.45); transform: translateY(-1px); }
.sel-card--on { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(123,94,248,0.18); }
.sel-card--dim { opacity: 0.38; cursor: default; pointer-events: none; }

.sel-badge {
  position: absolute; top: 8px; right: 8px; z-index: 3;
  width: 22px; height: 22px; border-radius: 50%;
  color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.sc-thumb { position: relative; aspect-ratio: 16/9; background: rgba(0,0,0,0.18); overflow: hidden; }
.sc-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.sc-overlay {
  position: absolute; inset: 0; background: rgba(123,94,248,0.38);
  display: flex; align-items: center; justify-content: center;
}
.sc-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
.sc-title {
  font-size: 13px; font-weight: 500; color: var(--text);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5;
}
.sc-channel { font-size: 11px; color: var(--subtext); }
.sc-stats { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--dim); margin-top: 4px; }

/* ── 비교 결과 내비 ── */
.res-nav { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.back-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--dim);
  background: var(--card); border: 0.5px solid var(--border);
  border-radius: 8px; padding: 7px 14px;
  cursor: pointer; font-family: 'Inter', sans-serif;
  transition: color 0.15s, border-color 0.15s;
}
.back-btn:hover { color: var(--accent); border-color: rgba(123,94,248,0.35); }
.legend { display: flex; align-items: center; gap: 18px; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
.legend-label { font-size: 12px; color: var(--subtext); }

/* ──────────────────────────────────────────
   비교 테이블
   행(row) 기반 레이아웃:
   [지표 레이블] [영상1] [영상2] [영상3?]
────────────────────────────────────────── */
.ct-wrap {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  overflow: clip;
}

/* 기본 행 */
.ct-row {
  display: flex;
  border-bottom: 0.5px solid var(--border);
}
.ct-row:last-child { border-bottom: none; }

/* sticky 영상 헤더 행 */
.ct-header-row {
  position: sticky;
  top: 0;
  z-index: 5;
  background: var(--card);
  border-bottom: 0.5px solid var(--border) !important;
}

/* 왼쪽 상단 코너 */
.ct-corner {
  width: 140px; flex-shrink: 0;
  background: var(--card-hover);
  border-right: 0.5px solid var(--border);
}

/* 영상 헤더 셀 */
.ct-vh {
  flex: 1; display: flex; flex-direction: column;
  border-right: 0.5px solid var(--border); overflow: hidden;
}
.ct-vh:last-child { border-right: none; }
.ct-vh-accent { height: 3px; flex-shrink: 0; }

/* 썸네일: 스크롤 시 접힘 */
.ct-vh-thumb {
  overflow: hidden;
  background: rgba(0,0,0,0.12);
  max-height: 300px;
  opacity: 1;
  transition: max-height 0.3s ease, opacity 0.25s ease;
}
.ct-vh-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; aspect-ratio: 16/9; }
.ct-header-row--collapsed .ct-vh-thumb {
  max-height: 0;
  opacity: 0;
}

.ct-vh-body { padding: 12px 14px; }
.ct-vh-title {
  font-size: 12px; font-weight: 600; color: var(--text); line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.ct-vh-ch { font-size: 11px; color: var(--subtext); margin-top: 3px; }

/* 섹션 구분 헤더 */
.ct-sec {
  padding: 8px 16px;
  font-size: 10px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
  color: var(--dim);
  background: var(--card-hover);
  border-bottom: 0.5px solid var(--border);
  border-top: 0.5px solid var(--border);
}

/* 지표 레이블 셀 */
.ct-lbl {
  width: 140px; flex-shrink: 0;
  padding: 14px 16px;
  font-size: 12px; font-weight: 500; color: var(--subtext);
  background: var(--card-hover);
  border-right: 0.5px solid var(--border);
  display: flex; align-items: center;
}

/* 데이터 셀 */
.ct-cell {
  flex: 1;
  padding: 14px 16px;
  font-size: 13px; font-weight: 500; color: var(--text);
  border-right: 0.5px solid var(--border);
  display: flex; align-items: center;
}
.ct-cell:last-child { border-right: none; }
.ct-cell--col { flex-direction: column; align-items: stretch; justify-content: center; gap: 7px; }

/* ── 감정 바 ── */
.sent-bar { display: flex; height: 7px; border-radius: 999px; overflow: hidden; }
.sb-pos { background: var(--positive); transition: width 0.35s; }
.sb-neu { background: var(--neutral); transition: width 0.35s; }
.sb-neg { background: var(--negative); transition: width 0.35s; }
.sent-nums { display: flex; gap: 10px; font-size: 11px; font-weight: 500; flex-wrap: wrap; }
.sn-pos { color: var(--positive); }
.sn-neu { color: var(--neutral); }
.sn-neg { color: var(--negative); }

/* ── 토픽 pills ── */
.topic-pills { display: flex; flex-wrap: wrap; gap: 5px; }
.topic-pill-sm {
  font-size: 11px; font-weight: 500;
  padding: 3px 9px; border-radius: 999px;
  background: rgba(123, 94, 248, 0.08);
  color: var(--accent);
  border: 0.5px solid rgba(123, 94, 248, 0.22);
  white-space: nowrap;
}

/* ── 언어 바 ── */
.lbar-row { display: flex; align-items: center; gap: 10px; width: 100%; }
.lbar-track { flex: 1; height: 5px; border-radius: 999px; background: var(--card-hover); overflow: hidden; }
.lbar-fill { height: 100%; border-radius: 999px; opacity: 0.85; transition: width 0.4s; }
.lbar-pct { font-size: 11px; color: var(--subtext); min-width: 30px; text-align: right; flex-shrink: 0; }
</style>
