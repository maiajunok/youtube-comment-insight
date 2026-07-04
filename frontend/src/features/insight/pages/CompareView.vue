<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { insightApi } from '@/features/insight/api/insightApi'
import type { HistoryItem, InsightData } from '@/features/insight/types/insight'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'
import { fillTopicLabels, displayLabel } from '@/features/insight/composables/useLabelTranslation'

const router = useRouter()
const route = useRoute()
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

  // 새로고침해도 비교 결과 화면이 유지되도록 URL의 ids로 다시 비교함
  const idsParam = route.query.ids
  if (typeof idsParam === 'string' && idsParam) {
    selected.value = idsParam.split(',').slice(0, 3)
    doCompare()
  }
})

// 사이드바에서 "영상 비교"를 다시 눌렀을 때(쿼리가 사라짐)도 선택 화면으로 돌아오게 함 —
// phase는 로컬 상태라 onMounted 이후엔 route 변화를 스스로 감지하지 못했음
watch(() => route.query.ids, (idsParam) => {
  if (typeof idsParam === 'string' && idsParam) {
    selected.value = idsParam.split(',').slice(0, 3)
    doCompare()
  } else if (phase.value === 'compare') {
    reset()
  }
})

const toggle = (id: string) => {
  const i = selected.value.indexOf(id)
  if (i !== -1) { selected.value.splice(i, 1) }
  else if (selected.value.length < 3) { selected.value.push(id) }
}

const isSelected = (id: string) => selected.value.includes(id)
const selIndex = (id: string) => selected.value.indexOf(id) + 1

const commonTopicLabels = ref<string[]>([])

// 비교 중(await) 다른 곳으로 나갔다가 돌아오면(reset 등) 뒤늦게 끝난 이전 요청이
// 화면을 다시 덮어써버리는 걸 막기 위한 토큰 — reset()에서도 증가시킴
let compareToken = 0

const doCompare = async () => {
  if (selected.value.length < 2) return
  const token = ++compareToken
  isComparing.value = true
  compareError.value = ''
  try {
    const results = await Promise.all(
      selected.value.map(id => insightApi.getByVideoId(id))
    )
    if (token !== compareToken) return
    comparisons.value = results
    await fillTopicLabels(comparisons.value.flatMap(d => d.topics), settings.lang)
    if (token !== compareToken) return
    phase.value = 'compare'
    router.replace({ query: { ids: selected.value.join(',') } })
    // 의미상 비슷한 토픽까지 묶어서 "공통 주제" 판별 (완전 일치 대신 임베딩 유사도)
    insightApi.getCommonTopics(comparisons.value.map(d => d.topics.map(t => t.label)))
      .then(labels => { if (token === compareToken) commonTopicLabels.value = labels })
      .catch(() => { if (token === compareToken) commonTopicLabels.value = [] })
  } catch {
    if (token === compareToken) compareError.value = '데이터를 불러오지 못했습니다.'
  } finally {
    if (token === compareToken) isComparing.value = false
  }
}

watch(() => settings.lang, (lang) => {
  if (comparisons.value.length) fillTopicLabels(comparisons.value.flatMap(d => d.topics), lang)
})

const reset = () => {
  compareToken++ // 이 시점 이후 뒤늦게 끝나는 doCompare()는 무시됨
  phase.value = 'select'
  comparisons.value = []
  commonTopicLabels.value = []
  headerCollapsed.value = false
  router.replace({ query: {} })
}

const onPageScroll = (e: Event) => {
  // 히스테리시스를 넉넉하게 둬서 경계값 근처에서 왔다갔다 하지 않게 함.
  // 애니메이션 없이 즉시 껐다 켜서(트랜지션 중 리플로우로 인한 떨림 방지) 썸네일을 통째로 뺌.
  const top = (e.target as HTMLElement).scrollTop
  if (top > 120) headerCollapsed.value = true
  else if (top < 20) headerCollapsed.value = false
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
  return commonTopicLabels.value
    .map(label => comparisons.value[0].topics.find(t => t.label === label))
    .filter((t): t is InsightData['topics'][number] => !!t)
})

const langRatio = (data: InsightData, key: string): number =>
  (data.video.languageRatio as Record<string, number>)[key] ?? 0

const fmtNum = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K'     :
  String(n)

const COL = ['#C0AB7E', '#22c55e', '#f59e0b']

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
  <div v-if="phase === 'select'" class="cpage cpage--select">

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
        <button v-if="selected.length" class="clear-sel-btn" @click="selected = []">
          {{ settings.lang === 'ko' ? '선택 해제' : settings.lang === 'zh' ? '取消选择' : settings.lang === 'ja' ? '選択解除' : 'Clear' }}
        </button>
        <p v-if="compareError" class="err-inline">{{ compareError }}</p>
        <button class="do-compare-btn" :disabled="selected.length < 2 || isComparing" @click="doCompare">
          <svg v-if="isComparing" class="spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          {{ isComparing ? M.comparing : M.compareBtn }}
        </button>
      </div>
    </div>

    <div class="cpage-body">
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
  </div>

  <!-- ── 비교 결과 ── -->
  <div v-else class="cpage cpage--select">

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
    <div class="cpage-body">
    <div class="ct-wrap">

      <!-- ── 영상 헤더 행 (sticky) ── -->
      <div class="ct-row ct-header-row">
        <div class="ct-corner" />
        <div v-for="(d, i) in comparisons" :key="d.video.videoId" class="ct-vh">
          <div class="ct-vh-accent" :style="`background:${COL[i]}`" />
          <div v-if="!headerCollapsed" class="ct-vh-thumb">
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

/* 선택 단계는 sticky 헤더가 부모 패딩을 완전히 덮어야 해서 패딩을 헤더/바디로 옮김 */
.cpage--select { padding: 0; gap: 0; }
.cpage-body {
  padding: 24px 40px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── 선택 헤더 ── */
.cpage-header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
  position: sticky;
  top: 0;
  padding: 36px 40px 16px;
  z-index: 100;
  isolation: isolate;
  background: color-mix(in srgb, var(--bg) 65%, transparent);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 0.5px solid var(--border);
}
.cpage-title { font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.cpage-sub { font-size: 13px; color: var(--subtext); margin-top: 4px; }
.header-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; margin-left: auto; }
.sel-pips { display: flex; align-items: center; gap: 6px; }
.sel-pip { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.sel-count-txt { font-size: 12px; color: var(--subtext); }
.clear-sel-btn {
  font-size: 12px;
  color: var(--subtext);
  background: transparent;
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 7px 12px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
  transition: color .15s, border-color .15s, background .15s;
}
.clear-sel-btn:hover { color: var(--text); background: var(--card-hover); }
.err-inline { font-size: 12px; color: #f87171; }
.err-msg { font-size: 13px; color: #f87171; }

.do-compare-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 9px 20px; border-radius: 8px;
  font-size: 13px; font-weight: 600; font-family: 'Inter', sans-serif;
  cursor: pointer;
  background: var(--accent);
  color: var(--cta-text); border: none;
  transition: opacity 0.15s;
}
.do-compare-btn:disabled { opacity: 0.35; cursor: default; }
.do-compare-btn:not(:disabled):hover { opacity: 0.88; }

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
.sel-card:hover:not(.sel-card--dim) { border-color: rgb(from var(--accent) r g b / 0.45); transform: translateY(-1px); }
.sel-card--on { border-color: var(--accent); box-shadow: 0 0 0 2px rgb(from var(--accent) r g b / 0.18); }
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
  position: absolute; inset: 0; background: rgb(from var(--accent) r g b / 0.38);
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
.res-nav {
  display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
  position: sticky;
  top: 0;
  padding: 36px 40px 16px;
  z-index: 100;
  isolation: isolate;
  background: color-mix(in srgb, var(--bg) 65%, transparent);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 0.5px solid var(--border);
}
.back-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--dim);
  background: var(--card); border: 0.5px solid var(--border);
  border-radius: 8px; padding: 7px 14px;
  cursor: pointer; font-family: 'Inter', sans-serif;
  transition: color 0.15s, border-color 0.15s;
}
.back-btn:hover { color: var(--accent); border-color: rgb(from var(--accent) r g b / 0.35); }
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
  top: 80px;
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

/* 썸네일: 고정 높이 (스크롤에 따라 크기가 변하지 않도록 — 떨림 방지) */
.ct-vh-thumb {
  overflow: hidden;
  background: rgba(0,0,0,0.12);
  height: 160px;
}
.ct-vh-thumb img { width: 100%; height: 100%; object-fit: contain; display: block; }

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
  background: rgb(from var(--accent) r g b / 0.08);
  color: var(--accent);
  border: 0.5px solid rgb(from var(--accent) r g b / 0.22);
  white-space: nowrap;
}

/* ── 언어 바 ── */
.lbar-row { display: flex; align-items: center; gap: 10px; width: 100%; }
.lbar-track { flex: 1; height: 5px; border-radius: 999px; background: var(--card-hover); overflow: hidden; }
.lbar-fill { height: 100%; border-radius: 999px; opacity: 0.85; transition: width 0.4s; }
.lbar-pct { font-size: 11px; color: var(--subtext); min-width: 30px; text-align: right; flex-shrink: 0; }

@media (max-width: 768px) {
  .cpage { padding: 20px 16px; }
  .cpage-header, .res-nav {
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    padding: 16px 16px 14px;
    background: color-mix(in srgb, var(--bg) 65%, transparent);
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  .cpage-body { padding: 18px 16px 32px; }
  .cpage--select { padding-top: 112px; }
  .ct-header-row { top: 60px; }
  .do-compare-btn { white-space: nowrap; }

  .ct-wrap { overflow-x: auto; }
  .ct-row, .ct-header-row { min-width: 460px; }
  .ct-corner, .ct-lbl { width: 90px; font-size: 12px; }
  .ct-vh-thumb { display: none; }
  .ct-vh-body { padding: 10px 10px; }
  .ct-vh-title { font-size: 11px; }
  .ct-vh-ch { font-size: 10px; }
}
</style>
