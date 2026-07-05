<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TimelinePoint, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'

// 등빈도 버킷 단위(원본)가 아니라 30분 창 단위로 이미 묶인 시간 그룹 — 댓글이 몰리는 구간엔
// 원본 버킷이 몇 초~몇 분 간격으로 수십 개씩 쏟아져서, 버킷 그대로 칩을 만들면 "같은 시간"처럼
// 보이는 칩이 수십 개 생긴다(ReactionTimeline.vue의 burstDayGroups.windows 참고)
type SiblingWindow = {
  key: string; direction: TimelinePoint['direction']; timeLabel: string
  kind: 'SENTIMENT' | 'VOLUME' | 'BOTH'
}

const props = defineProps<{
  point: TimelinePoint
  label: string
  lang: Lang
  siblingWindows?: SiblingWindow[]
  activeWindowKey?: string | null
  showAll?: boolean
}>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'select-time', key: string): void; (e: 'select-all'): void }>()

const M = computed(() => messages[props.lang])

type Filter = 'all' | 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'
const filter = ref<Filter>('all')
watch(() => props.point, () => { filter.value = 'all' })

const filteredComments = computed(() => {
  const all = props.point.topComments ?? []
  return filter.value === 'all' ? all : all.filter(c => c.sentiment === filter.value)
})

const LOCALE_MAP2: Record<Lang, string> = { ko: 'ko-KR', en: 'en-US', zh: 'zh-CN', ja: 'ja-JP' }

const absoluteDate = computed(() => {
  if (!props.point.bucketStart) return ''
  const d = new Date(props.point.bucketStart)
  return d.toLocaleString(LOCALE_MAP2[props.lang], {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
})

// 구간이 "그 하루 전체"가 아니라 등빈도로 잘린 슬라이스라는 걸 명확히 보여주기 위한 종료 시각 표시
const dateRangeEnd = computed(() => {
  if (!props.point.bucketEnd) return ''
  const start = props.point.bucketStart ? new Date(props.point.bucketStart) : null
  const end = new Date(props.point.bucketEnd)
  const sameDay = start && start.toDateString() === end.toDateString()
  return end.toLocaleString(LOCALE_MAP2[props.lang], sameDay
    ? { hour: '2-digit', minute: '2-digit' }
    : { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
})

const DAYS_SINCE_UPLOAD_LABEL: Record<Lang, (n: number) => string> = {
  ko: n => `업로드 ${n}일째`,
  en: n => `Day ${n} since upload`,
  zh: n => `上传后第 ${n} 天`,
  ja: n => `アップロード${n}日目`,
}

const daysSinceUploadLabel = computed(() => {
  if (props.point.elapsedSeconds == null) return ''
  // 프리미어 대기실 댓글 등 업로드 공식 시각보다 먼저 달린 댓글은 음수가 될 수 있음 → 0으로 클램프
  const days = Math.floor(Math.max(props.point.elapsedSeconds, 0) / 86400)
  return DAYS_SINCE_UPLOAD_LABEL[props.lang](days)
})

// 감정 급변(POSITIVE_SPIKE/NEGATIVE_SPIKE)과 댓글량 급증(volume-only, direction 없음)을
// 구분해서 보여줌 — "전체" 병합 뷰는 그 날 가장 극단적인 포인트를 대표로 쓰므로 감정/볼륨
// 어느 쪽이든 대표가 될 수 있음(ReactionTimeline.vue의 severity 비교 참고)
const burstEyebrow = computed(() => {
  if (props.point.direction === 'POSITIVE_SPIKE') return M.value.positiveSpike
  if (props.point.direction === 'NEGATIVE_SPIKE') return M.value.negativeSpike
  if (props.point.isVolumeBurst) return M.value.volumeSpike
  return ''
})
const burstZScore = computed(() => props.point.isBurst ? props.point.zScore : props.point.volumeZScore)
// 색상 의미 고정: 감정 급변=주황(anomaly), 댓글량 급증(단독)=보라(volume-burst) — 감정 급변이
// 같이 있으면(direction 존재) 그쪽을 우선해서 amber로 표시(라벨 우선순위와 동일하게 맞춤)
const burstEyebrowColor = computed(() =>
  props.point.direction ? 'var(--anomaly)' : props.point.isVolumeBurst ? 'var(--volume-burst)' : 'var(--anomaly)'
)

const sentimentColor = (s: string) => {
  if (s === 'POSITIVE') return 'var(--positive)'
  if (s === 'NEGATIVE') return 'var(--negative)'
  return 'var(--neutral)'
}
const sentimentLabel = (s: string) => {
  if (s === 'POSITIVE') return M.value.positive
  if (s === 'NEGATIVE') return M.value.negative
  return M.value.neutral
}
</script>

<template>
  <div class="drawer-backdrop" @click="emit('close')" />

  <div class="drawer">
    <div class="drawer-header">
      <div class="header-text">
        <p class="header-eyebrow" :style="{ color: burstEyebrowColor }">
          {{ burstEyebrow }}
          <span class="z-badge">z={{ burstZScore?.toFixed(2) }}</span>
        </p>
        <h3 class="header-title">{{ absoluteDate || label }}<span v-if="dateRangeEnd" class="header-range"> ~ {{ dateRangeEnd }}</span></h3>
        <p class="header-days">{{ daysSinceUploadLabel }}</p>
        <div class="header-counts">
          <span><i class="dot" style="background: var(--positive)"/>{{ point.positive }}</span>
          <span><i class="dot" style="background: var(--neutral)"/>{{ point.neutral }}</span>
          <span><i class="dot" style="background: var(--negative)"/>{{ point.negative }}</span>
        </div>
      </div>
      <button @click="emit('close')" class="close-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- 같은 날 이상치가 여러 번이면, 창을 닫지 않고 바로 다른 시간대(30분 단위)로(또는 전체
         합쳐서) 전환 -->
    <div v-if="siblingWindows && siblingWindows.length > 1" class="time-row">
      <button class="time-pill" :class="{ active: showAll }" @click="emit('select-all')">
        {{ M.filterAll }}
      </button>
      <button
        v-for="w in siblingWindows"
        :key="w.key"
        class="time-pill"
        :class="{ active: !showAll && w.key === activeWindowKey }"
        @click="emit('select-time', w.key)"
      >
        <i class="dot" :style="{ background: w.direction === 'NEGATIVE_SPIKE' ? 'var(--negative)' : w.direction === 'POSITIVE_SPIKE' ? 'var(--positive)' : 'var(--volume-burst)' }" />
        {{ w.timeLabel }}
      </button>
    </div>

    <!-- 감정 필터 탭 -->
    <div class="filter-row">
      <button
        v-for="[key, label, count] in [
          ['all', M.filterAll, point.positive + point.neutral + point.negative],
          ['POSITIVE', M.positive, point.positive],
          ['NEUTRAL', M.neutral, point.neutral],
          ['NEGATIVE', M.negative, point.negative],
        ]"
        :key="key"
        @click="filter = key as Filter"
        class="filter-tab"
        :class="{ active: filter === key }"
      >
        {{ label }}
        <span class="tab-badge" :class="{ 'badge-active': filter === key }">{{ count }}</span>
      </button>
    </div>

    <div class="comment-list">
      <p v-if="!filteredComments.length" class="state-msg">{{ M.noCommentsFound }}</p>
      <div v-else v-for="(c, i) in filteredComments" :key="i" class="comment-card">
        <div class="sentiment-bar" :style="`background: ${sentimentColor(c.sentiment)}`" />
        <div class="comment-body">
          <div class="comment-meta">
            <span
              class="sentiment-pill"
              :style="`background: ${sentimentColor(c.sentiment)}1f; color: ${sentimentColor(c.sentiment)}`"
            >{{ sentimentLabel(c.sentiment) }}</span>
            <div class="likes">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {{ c.likeCount.toLocaleString() }}
            </div>
          </div>
          <p class="comment-text">{{ c.text }}</p>
        </div>
      </div>
    </div>

    <div class="footer-bar">
      {{ M.totalCommentsFooter.replace('{n}', String(point.positive + point.neutral + point.negative)) }}
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/assets/variables' as *;

.drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(8, 6, 16, 0.55);
  backdrop-filter: blur(2px);
  animation: drawer-fade-in 0.2s ease-out;
}
@keyframes drawer-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.drawer {
  position: fixed;
  right: 0;
  top: 0;
  height: 100vh;
  z-index: 50;
  width: 500px;
  display: flex;
  flex-direction: column;
  background: var(--card);
  border-left: 0.5px solid var(--border);
  box-shadow: -24px 0 60px rgba(0, 0, 0, 0.35);
  animation: drawer-slide-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes drawer-slide-in {
  from { transform: translateX(24px); opacity: 0; }
  to   { transform: translateX(0); opacity: 1; }
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  gap: $space-md;
  padding: 28px 28px 20px;
  border-bottom: 0.5px solid var(--border);
  flex-shrink: 0;
}
.header-text { flex: 1; min-width: 0; }
.header-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  /* color는 burstEyebrowColor로 인라인 바인딩(감정 급변=주황 / 댓글량 급증=보라) */
  margin-bottom: 6px;
}
.z-badge {
  font-size: 10px;
  font-weight: 500;
  color: var(--subtext);
}
.header-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.4;
  letter-spacing: -.01em;
  margin-bottom: 3px;
}
.header-range {
  font-size: 13px;
  font-weight: 500;
  color: var(--subtext);
}
.header-days {
  font-size: 12px;
  color: var(--subtext);
  margin-bottom: 10px;
}
.header-counts {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--subtext);

  span { display: flex; align-items: center; gap: 5px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
}

.close-btn {
  @include icon-button;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  color: var(--subtext);

  &:hover { color: var(--text); border-color: rgb(from var(--accent) r g b / 0.35); }
}

.time-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 28px;
  flex-shrink: 0;
  border-bottom: 0.5px solid var(--border);
}
.time-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-family);
  white-space: nowrap;
  cursor: pointer;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  transition: background 0.15s, color 0.15s, border-color 0.15s;

  .dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
}
.time-pill:hover:not(.active) { color: var(--text); background: var(--card-hover); }
.time-pill.active {
  border-color: var(--anomaly);
  background: rgb(255 222 89 / 0.1);
  color: var(--text);
  font-weight: 600;
}

.filter-row {
  display: flex;
  gap: 8px;
  padding: 16px 28px;
  flex-shrink: 0;
  border-bottom: 0.5px solid var(--border);
}
.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-family);
  cursor: pointer;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.filter-tab:hover:not(.active) {
  color: var(--text);
  background: var(--card-hover);
}
.filter-tab.active {
  background: rgb(from var(--accent) r g b / 0.12);
  border-color: rgb(from var(--accent) r g b / 0.35);
  color: var(--accent);
  font-weight: 600;
}
.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  background: var(--card-hover);
  color: var(--dim);
  border: 0.5px solid var(--border);
  line-height: 1;
}
.tab-badge.badge-active {
  background: rgb(from var(--accent) r g b / 0.18);
  color: var(--accent);
  border-color: transparent;
}

.comment-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 28px 28px;
  display: flex;
  flex-direction: column;
  gap: $space-md;

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
}

.state-msg {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
  font-size: 13px;
  text-align: center;
  color: var(--subtext);
}

.comment-card {
  display: flex;
  gap: $space-md;
  border-radius: 14px;
  padding: 16px 18px;
  background: var(--card-hover);
  border: 0.5px solid var(--border);
  transition: border-color $transition-fast;

  &:hover { border-color: rgb(from var(--accent) r g b / 0.25); }
}

.sentiment-bar {
  margin-top: 2px;
  flex-shrink: 0;
  width: 3px;
  border-radius: 999px;
  align-self: stretch;
}

.comment-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: $space-sm;
}

.sentiment-pill {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
}

.comment-text {
  font-size: 13px;
  color: var(--text);
  line-height: 1.7;
  font-weight: 500;
  white-space: pre-wrap;
}

.likes {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--dim);
  margin-left: auto;
}

.footer-bar {
  flex-shrink: 0;
  padding: 16px 28px;
  border-top: 0.5px solid var(--border);
  font-size: 11px;
  color: var(--dim);
  background: var(--card-hover);
}

@media (max-width: 768px) {
  .drawer { width: 100%; }
  .drawer-header { padding: 20px 18px 16px; }
  .filter-row { padding: 12px 18px; overflow-x: auto; }
  .comment-list { padding: 16px 18px 20px; }
}
</style>
