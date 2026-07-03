<script setup lang="ts">
import { computed } from 'vue'
import type { VideoInfo, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'

const props = defineProps<{
  video: VideoInfo
  lang: Lang
  analyzedAt?: string
  showReanalyze?: boolean
  reanalyzing?: boolean
}>()
const emit = defineEmits<{ (e: 'reanalyze'): void }>()

const fmt = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K'     :
  String(n)

const youtubeUrl = computed(() => `https://www.youtube.com/watch?v=${props.video.videoId}`)

const analyzedAtFmt = computed(() => {
  if (!props.analyzedAt) return ''
  const d = new Date(props.analyzedAt)
  return d.toLocaleString(props.lang === 'ko' ? 'ko-KR' : props.lang === 'zh' ? 'zh-CN' : props.lang === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
})
</script>

<template>
  <div class="rounded-xl border flex flex-col gap-4 h-full"
    style="background: var(--card); border-color: var(--border); padding: var(--card-padding)">

    <!-- Thumbnail -->
    <a
      :href="youtubeUrl"
      target="_blank"
      rel="noopener"
      class="rounded-lg overflow-hidden aspect-video bg-slate-800/60 relative block group"
    >
      <img
        :src="video.thumbnailUrl"
        :alt="video.title"
        class="w-full h-full object-cover transition-transform duration-300 ease-out group-hover:scale-[1.04]"
        @error="($event.target as HTMLImageElement).style.opacity = '0'"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-black/55 via-black/0 to-black/5 transition-opacity duration-300 pointer-events-none"></div>

      <!-- 영상 길이 배지 -->
      <div class="absolute bottom-2 right-2 px-1.5 py-0.5 rounded text-[10px] font-bold"
        style="background: rgba(0,0,0,0.75); color: #fff">
        18:42
      </div>

      <!-- 중앙 재생 버튼 (글래스모피즘, 호버 시 등장) -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div
          class="flex items-center justify-center w-12 h-12 rounded-full scale-75 opacity-0 group-hover:scale-100 group-hover:opacity-100 transition-all duration-300 ease-out"
          style="background: rgba(255,255,255,0.14); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.35); box-shadow: 0 4px 20px rgba(0,0,0,0.35);"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff" style="margin-left: 2px">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>

      <!-- 유튜브에서 보기 칩 (좌하단, 호버 시 등장) -->
      <div
        class="absolute bottom-2 left-2 flex items-center gap-1.5 px-3 py-2 rounded-full text-[11px] font-semibold opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 ease-out"
        style="background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); color: #fff; border: 0.5px solid rgba(255,255,255,0.18)"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="#ff3b30">
          <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8zM9.75 15.5v-7l6.25 3.5-6.25 3.5z"/>
        </svg>
        {{ lang === 'en' ? 'Watch on YouTube' : '유튜브에서 보기' }}
      </div>
    </a>

    <p class="flex items-center gap-1 text-[11px] -mt-4" style="color: var(--dim)">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" class="shrink-0"><path d="M8 5v14l11-7z"/></svg>
      {{ lang === 'en' ? 'Click the thumbnail to watch on YouTube' : '썸네일을 클릭하면 유튜브 영상으로 이동해요' }}
    </p>

    <!-- 분석일자 + 다시 분석하기 (제목 위 작은 메타 정보) -->
    <div v-if="analyzedAt" class="flex items-center justify-between text-[11px]" style="color: var(--dim)">
      <span>{{ messages[lang].analyzedAtLabel }} · {{ analyzedAtFmt }}</span>
      <button
        v-if="showReanalyze"
        class="reanalyze-btn"
        :disabled="reanalyzing"
        @click="emit('reanalyze')"
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: reanalyzing }">
          <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        {{ messages[lang].reAnalyze }}
      </button>
    </div>

    <!-- Title & Channel -->
    <div class="flex flex-col gap-2.5">
      <p class="text-base font-semibold leading-snug line-clamp-2" style="color: var(--text); line-height: 1.6;">
        {{ video.title }}
      </p>
      <div class="flex items-center gap-1.5 text-[13px]" style="color: var(--subtext)">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
        {{ video.channelTitle }}
      </div>
    </div>

    <!-- Stats -->
    <div class="flex flex-col gap-3">
      <div
        v-for="stat in [
          { label: messages[lang].uploadDate,        value: video.publishedAt,           icon: 'calendar' },
          { label: messages[lang].views,             value: fmt(video.viewCount),        icon: 'eye'      },
          { label: messages[lang].likes,             value: fmt(video.likeCount),        icon: 'heart'    },
          { label: messages[lang].analyzedComments,  value: fmt(video.analyzedComments), icon: 'chat'     },
        ]"
        :key="stat.label"
        class="flex items-center justify-between text-[13px]"
      >
        <span class="flex items-center gap-1.5" style="color: var(--subtext)">
          <!-- calendar -->
          <svg v-if="stat.icon === 'calendar'" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <!-- eye -->
          <svg v-else-if="stat.icon === 'eye'" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          <!-- heart -->
          <svg v-else-if="stat.icon === 'heart'" width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          <!-- chat -->
          <svg v-else-if="stat.icon === 'chat'" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          {{ stat.label }}
        </span>
        <span class="font-semibold tabular-nums" style="color: var(--text)">{{ stat.value }}</span>
      </div>
    </div>

    <!-- Language Ratio -->
    <div>
      <p class="text-[11px] font-semibold uppercase tracking-widest mb-2" style="color: var(--subtext)">
        {{ messages[lang].languageRatio }}
      </p>
      <div class="flex rounded-full overflow-hidden h-2">
        <div :style="`flex: ${video.languageRatio.ko} 1 0%; background: var(--accent)`"></div>
        <div :style="`flex: ${video.languageRatio.en} 1 0%; background: var(--positive)`"></div>
        <div :style="`flex: ${video.languageRatio.other} 1 0%; background: var(--neutral)`"></div>
      </div>
      <div class="flex gap-4 mt-2 text-[11px]" style="color: var(--subtext)">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full inline-block shrink-0" style="background: var(--accent)"></span>
          {{ lang === 'en' ? 'Korean' : '한국어' }} {{ video.languageRatio.ko }}%
        </span>
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full inline-block shrink-0" style="background: var(--positive)"></span>
          English {{ video.languageRatio.en }}%
        </span>
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full inline-block shrink-0" style="background: var(--neutral)"></span>
          Other {{ video.languageRatio.other }}%
        </span>
      </div>
    </div>

    <!-- Note -->
    <p class="text-[11px] italic mt-auto" style="color: var(--subtext)">
      {{ messages[lang].analysisNote }}
    </p>

  </div>
</template>

<style scoped>
.reanalyze-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.reanalyze-btn:hover:not(:disabled) {
  color: var(--accent);
  border-color: rgb(from var(--accent) r g b / 0.35);
  background: rgb(from var(--accent) r g b / 0.08);
}
.reanalyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>
