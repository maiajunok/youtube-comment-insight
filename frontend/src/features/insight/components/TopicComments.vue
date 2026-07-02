<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { insightApi } from '@/features/insight/api/insightApi'
import type { TopicComment } from '@/features/insight/types/insight'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

const props = defineProps<{ videoId: string; topic: string; displayTopic?: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])

type Filter = 'all' | 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'

const comments = ref<TopicComment[]>([])
const counts = ref({ POSITIVE: 0, NEUTRAL: 0, NEGATIVE: 0 })
const total = ref(0)
const filter = ref<Filter>('all')
const isLoading = ref(false)
const error = ref('')

const load = async (sentiment: Filter) => {
  isLoading.value = true
  error.value = ''
  try {
    const res = await insightApi.getTopicComments(props.videoId, props.topic, sentiment)
    comments.value = res.comments
    total.value = res.total
    if (sentiment === 'all') counts.value = res.counts as any
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? M.value.commentsLoadFailed
    comments.value = []
  } finally {
    isLoading.value = false
  }
}

watch(filter, (val) => load(val))
watch(() => props.topic, () => { filter.value = 'all'; load('all') }, { immediate: true })

const fmtDate = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

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
  <!-- backdrop -->
  <div class="drawer-backdrop" @click="emit('close')" />

  <!-- drawer -->
  <div class="drawer">
    <!-- 헤더 -->
    <div class="drawer-header">
      <div class="header-text">
        <p class="header-eyebrow">{{ M.topicCommentsLabel }}</p>
        <h3 class="header-title">{{ displayTopic || topic }}</h3>
      </div>
      <button @click="emit('close')" class="close-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- 감정 필터 탭 -->
    <div class="filter-row">
      <button
        v-for="[key, label, count] in [
          ['all', M.filterAll, counts.POSITIVE + counts.NEUTRAL + counts.NEGATIVE],
          ['POSITIVE', M.positive, counts.POSITIVE],
          ['NEUTRAL', M.neutral, counts.NEUTRAL],
          ['NEGATIVE', M.negative, counts.NEGATIVE],
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

    <!-- 댓글 목록 -->
    <div class="comment-list">

      <div v-if="isLoading" class="state-msg">
        <p>{{ M.loading }}</p>
      </div>

      <p v-else-if="error" class="state-msg error">{{ error }}</p>

      <p v-else-if="!comments.length" class="state-msg">
        {{ M.noCommentsFound }}
      </p>

      <div v-else v-for="c in comments" :key="c.id" class="comment-card">
        <!-- 감정 인디케이터 -->
        <div class="sentiment-bar" :style="`background: ${sentimentColor(c.sentiment)}`" />

        <div class="comment-body">
          <!-- 메타 -->
          <div class="comment-meta">
            <span class="author">{{ c.authorName || M.anonymousAuthor }}</span>
            <span class="date">{{ fmtDate(c.publishedAt) }}</span>
            <span
              class="sentiment-pill"
              :style="`background: ${sentimentColor(c.sentiment)}1f; color: ${sentimentColor(c.sentiment)}`"
            >{{ sentimentLabel(c.sentiment) }}</span>
          </div>

          <!-- 텍스트 -->
          <p class="comment-text">{{ c.text }}</p>

          <!-- 좋아요 -->
          <div v-if="c.likeCount > 0" class="likes">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            {{ c.likeCount.toLocaleString() }}
          </div>
        </div>
      </div>

    </div>

    <!-- 푸터 -->
    <div class="footer-bar">
      {{ M.totalCommentsFooter.replace('{n}', total.toLocaleString()) }}
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
  font-size: 10px;
  letter-spacing: .14em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--accent);
  opacity: 0.75;
  margin-bottom: 6px;
}
.header-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.4;
  letter-spacing: -.01em;
}

.close-btn {
  @include icon-button;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  color: var(--subtext);

  &:hover { color: var(--text); border-color: rgb(from var(--accent) r g b / 0.35); }
}

.filter-row {
  display: flex;
  gap: 8px;
  padding: 16px 28px;
  flex-shrink: 0;
  border-bottom: 0.5px solid var(--border);
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

  &.error { color: #f87171; }
}

.comment-card {
  display: flex;
  gap: $space-md;
  border-radius: 14px;
  padding: 16px 18px;
  background: var(--card-hover);
  border: 0.5px solid var(--border);
  transition: border-color $transition-fast, transform $transition-fast;

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
  flex-wrap: wrap;

  .author { font-size: 12px; font-weight: 600; color: var(--text); }
  .date   { font-size: 11px; color: var(--dim); }
}

.sentiment-pill {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  margin-left: auto;
}

.comment-text {
  font-size: 13px;
  color: var(--text);
  line-height: 1.7;
  font-weight: 500;
}

.likes {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--dim);
}

.footer-bar {
  flex-shrink: 0;
  padding: 16px 28px;
  border-top: 0.5px solid var(--border);
  font-size: 11px;
  color: var(--dim);
  background: var(--card-hover);
}
.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
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

@media (max-width: 768px) {
  .drawer { width: 100%; }
  .drawer-header { padding: 20px 18px 16px; }
  .filter-row { padding: 12px 18px; overflow-x: auto; }
  .comment-list { padding: 16px 18px 20px; }
}
</style>
