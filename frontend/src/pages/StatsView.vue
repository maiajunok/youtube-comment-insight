<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { insightApi } from '@/features/insight/api/insightApi'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])

type Stats = Awaited<ReturnType<typeof insightApi.getStats>>
const stats = ref<Stats | null>(null)
const isLoading = ref(true)
const error = ref(false)

onMounted(async () => {
  try { stats.value = await insightApi.getStats() }
  catch { error.value = true }
  finally { isLoading.value = false }
})

const fmtNum = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K' : String(n)

const fmtDur = (s: number | null) => s != null ? s + 's' : '—'

const fmtDate = (iso: string) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}  ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const durBar = (dur: number | null, max: number | null) => {
  if (dur == null || !max) return 0
  return Math.round((dur / max) * 100)
}

// 댓글 100개당 처리 시간 (초)
const per100 = (dur: number | null, comments: number) => {
  if (dur == null || comments === 0) return null
  return (dur / comments * 100).toFixed(1)
}

const avgPer100 = computed(() => {
  if (!stats.value) return null
  const valid = stats.value.records.filter(r => r.duration != null && r.analyzedComments > 0)
  if (!valid.length) return null
  const sum = valid.reduce((acc, r) => acc + r.duration! / r.analyzedComments * 100, 0)
  return (sum / valid.length).toFixed(1)
})
</script>

<template>
  <div class="stats-page">

    <div class="stats-header">
      <p class="eyebrow">Usage Analytics</p>
      <h1 class="stats-title">{{ M.navStats }}</h1>
      <p class="stats-sub">{{ M.statsSub }}</p>
    </div>

    <!-- 로딩 -->
    <div v-if="isLoading" class="center-msg">{{ M.loading }}</div>
    <div v-else-if="error" class="center-msg" style="color:#f87171">{{ M.backendError }}</div>

    <template v-else-if="stats">

      <!-- 요약 카드 -->
      <div class="summary-cards">
        <div class="s-card accent">
          <span class="s-val">{{ stats.totalAnalyses }}</span>
          <span class="s-lbl">{{ M.totalAnalyses }}</span>
        </div>
        <div class="s-card">
          <span class="s-val">{{ fmtNum(stats.totalComments) }}</span>
          <span class="s-lbl">{{ M.totalComments }}</span>
        </div>
        <div class="s-card">
          <span class="s-val">{{ fmtNum(stats.totalTokens) }}</span>
          <span class="s-lbl">{{ M.totalTokens }}</span>
        </div>
        <div class="s-card">
          <span class="s-val">{{ fmtDur(stats.avgDuration) }}</span>
          <span class="s-lbl">{{ M.avgDuration }}</span>
        </div>
        <div class="s-card">
          <span class="s-val">{{ fmtDur(stats.minDuration) }}</span>
          <span class="s-lbl">{{ M.minDuration }}</span>
        </div>
        <div class="s-card">
          <span class="s-val">{{ fmtDur(stats.maxDuration) }}</span>
          <span class="s-lbl">{{ M.maxDuration }}</span>
        </div>
        <div class="s-card">
          <span class="s-val">{{ avgPer100 != null ? avgPer100 + 's' : '—' }}</span>
          <span class="s-lbl">{{ M.avgPer100 }}</span>
        </div>
      </div>

      <!-- 영상별 기록 -->
      <div v-if="stats.records.length">
        <p class="section-label">{{ M.videoRecords }}</p>
        <div class="records-table">
          <div class="rec-head">
            <span>{{ M.colVideo }}</span>
            <span class="align-right">{{ M.colCommentCount }}</span>
            <span>{{ M.colDuration }}</span>
            <span class="align-right">{{ M.colPer100 }}</span>
            <span>{{ M.colDate }}</span>
          </div>
          <div v-for="r in stats.records" :key="r.videoId" class="rec-row">
            <span class="rec-title">{{ r.title }}</span>
            <span class="rec-num align-right">{{ fmtNum(r.analyzedComments) }}</span>
            <span class="rec-dur-cell">
              <span class="rec-dur-val">{{ fmtDur(r.duration) }}</span>
              <div class="dur-track">
                <div class="dur-fill" :style="`width:${durBar(r.duration, stats!.maxDuration)}%`" />
              </div>
            </span>
            <span class="rec-per100 align-right">
              {{ per100(r.duration, r.analyzedComments) != null ? per100(r.duration, r.analyzedComments) + 's' : '—' }}
            </span>
            <span class="rec-date">{{ fmtDate(r.analyzedAt) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="center-msg">{{ M.noRecords }}</div>

    </template>

  </div>
</template>

<style scoped>
.stats-page {
  position: relative;
  z-index: 2;
  flex: 1;
  overflow-y: auto;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.stats-header { display: flex; flex-direction: column; gap: 8px; }
.eyebrow {
  font-size: 10px; letter-spacing: .14em; color: var(--accent);
  text-transform: uppercase; font-weight: 600; opacity: 0.7;
  display: flex; align-items: center; gap: 8px;
}
.eyebrow::before { content: ''; width: 20px; height: 1px; background: var(--accent); }
.stats-title { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.stats-sub   { font-size: 14px; color: var(--subtext); line-height: 1.6; }

.center-msg { font-size: 13px; color: var(--subtext); }

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 14px;
}
.s-card {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 20px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.s-card.accent { border-color: rgba(123,94,248,0.35); background: rgba(123,94,248,0.06); }
.s-val { font-size: 28px; font-weight: 700; color: var(--accent); letter-spacing: -.03em; line-height: 1; }
.s-lbl { font-size: 11px; color: var(--dim); text-transform: uppercase; letter-spacing: .07em; font-weight: 600; }

.section-label {
  font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--dim); font-weight: 600; margin-bottom: 14px;
}

.records-table {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.rec-head {
  display: grid;
  grid-template-columns: 1fr 80px 170px 100px 140px;
  padding: 10px 20px;
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .08em;
  color: var(--dim);
  background: var(--card-hover);
  border-bottom: 0.5px solid var(--border);
  gap: 16px;
}

.rec-row {
  display: grid;
  grid-template-columns: 1fr 80px 170px 100px 140px;
  padding: 13px 20px;
  border-bottom: 0.5px solid var(--border);
  align-items: center;
  transition: background .12s;
  gap: 16px;
}
.rec-row:last-child { border-bottom: none; }
.rec-row:hover { background: var(--card-hover); }

.rec-title {
  font-size: 13px; font-weight: 500; color: var(--text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  padding-right: 16px;
}
.rec-num { font-size: 13px; font-weight: 600; color: var(--text); }
.align-right { text-align: right; }

.rec-dur-cell { display: flex; flex-direction: column; gap: 5px; padding-right: 16px; }
.rec-dur-val  { font-size: 13px; font-weight: 700; color: var(--accent); }
.dur-track    { height: 3px; background: var(--border); border-radius: 99px; overflow: hidden; }
.dur-fill     { height: 100%; background: var(--accent); border-radius: 99px; opacity: 0.6; transition: width .3s; }

.rec-date    { font-size: 12px; color: var(--subtext); }
.rec-per100  { font-size: 13px; font-weight: 600; color: var(--subtext); }
</style>
