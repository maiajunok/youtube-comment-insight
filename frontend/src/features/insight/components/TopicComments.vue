<script setup lang="ts">
import { ref, watch } from 'vue'
import { insightApi } from '@/features/insight/api/insightApi'
import type { TopicComment } from '@/features/insight/types/insight'

const props = defineProps<{ videoId: string; topic: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

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
    error.value = e?.response?.data?.detail ?? '댓글을 불러오지 못했습니다.'
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
  if (s === 'POSITIVE') return '긍정'
  if (s === 'NEGATIVE') return '부정'
  return '중립'
}
</script>

<template>
  <!-- backdrop -->
  <div
    class="fixed inset-0 z-40"
    style="background: rgba(0,0,0,0.5)"
    @click="emit('close')"
  />

  <!-- drawer -->
  <div
    class="fixed right-0 top-0 h-screen z-50 flex flex-col border-l"
    style="width: 480px; background: var(--card); border-color: var(--border)"
  >
    <!-- 헤더 -->
    <div class="flex items-center gap-3 px-5 py-4 border-b shrink-0"
      style="border-color: var(--border)">
      <div class="flex-1 min-w-0">
        <p class="text-[11px] uppercase tracking-widest mb-0.5" style="color: var(--subtext)">토픽 댓글</p>
        <h3 class="text-base font-bold leading-snug" style="color: var(--text)">{{ topic }}</h3>
      </div>
      <button
        @click="emit('close')"
        class="w-8 h-8 rounded-lg flex items-center justify-center border transition-all"
        style="border-color: var(--border); color: var(--subtext)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- 감정 필터 탭 -->
    <div class="flex gap-1.5 px-5 py-3 shrink-0 border-b" style="border-color: var(--border)">
      <button
        v-for="[key, label, count] in [
          ['all', '전체', counts.POSITIVE + counts.NEUTRAL + counts.NEGATIVE],
          ['POSITIVE', '긍정', counts.POSITIVE],
          ['NEUTRAL', '중립', counts.NEUTRAL],
          ['NEGATIVE', '부정', counts.NEGATIVE],
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
    <div class="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-3">

      <div v-if="isLoading" class="flex-1 flex items-center justify-center py-16">
        <p class="text-sm" style="color: var(--subtext)">불러오는 중...</p>
      </div>

      <p v-else-if="error" class="text-sm py-4 text-center" style="color: #f87171">{{ error }}</p>

      <p v-else-if="!comments.length" class="text-sm py-8 text-center" style="color: var(--subtext)">
        해당 댓글이 없습니다
      </p>

      <div
        v-else
        v-for="c in comments"
        :key="c.id"
        class="flex gap-3 rounded-xl border"
        style="padding: var(--card-padding); background: var(--card-hover); border-color: var(--border)"
      >
        <!-- 감정 인디케이터 -->
        <div class="mt-1 shrink-0 w-1.5 rounded-full self-stretch"
          :style="`background: ${sentimentColor(c.sentiment)}`"
        />

        <div class="flex-1 min-w-0 flex flex-col gap-2.5">
          <!-- 메타 -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[12px] font-semibold" style="color: var(--text)">{{ c.authorName || '익명' }}</span>
            <span class="text-[11px]" style="color: var(--subtext)">{{ fmtDate(c.publishedAt) }}</span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full ml-auto"
              :style="`background: ${sentimentColor(c.sentiment)}22; color: ${sentimentColor(c.sentiment)}`"
            >{{ sentimentLabel(c.sentiment) }}</span>
          </div>

          <!-- 텍스트 -->
          <p class="text-[13px]" style="color: var(--text); line-height: 1.7; font-weight: 500;">{{ c.text }}</p>

          <!-- 좋아요 -->
          <div v-if="c.likeCount > 0" class="flex items-center gap-1 text-[11px]" style="color: var(--subtext)">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            {{ c.likeCount.toLocaleString() }}
          </div>
        </div>
      </div>

    </div>

    <!-- 푸터 -->
    <div class="px-5 py-3 border-t text-[11px] shrink-0" style="border-color: var(--border); color: var(--subtext)">
      총 {{ total.toLocaleString() }}개 댓글 · 좋아요 순 정렬
    </div>
  </div>
</template>

<style scoped>
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
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
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
  background: rgba(255, 255, 255, 0.22);
  color: rgba(255, 255, 255, 0.9);
  border-color: transparent;
}
</style>
