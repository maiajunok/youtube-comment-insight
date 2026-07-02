<script setup lang="ts">
import type { VideoInfo, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'

const props = defineProps<{ video: VideoInfo; lang: Lang }>()

const fmt = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K'     :
  String(n)
</script>

<template>
  <div class="rounded-xl border flex flex-col gap-4 h-full"
    style="background: var(--card); border-color: var(--border); padding: var(--card-padding)">

    <!-- Thumbnail -->
    <div class="rounded-lg overflow-hidden aspect-video bg-slate-800/60 relative">
      <img
        :src="video.thumbnailUrl"
        :alt="video.title"
        class="w-full h-full object-cover"
        @error="($event.target as HTMLImageElement).style.opacity = '0'"
      />
      <!-- 영상 길이 배지 -->
      <div class="absolute bottom-2 right-2 px-1.5 py-0.5 rounded text-[10px] font-bold"
        style="background: rgba(0,0,0,0.75); color: #fff">
        18:42
      </div>
      <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent pointer-events-none"></div>
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
      <div class="flex rounded-sm overflow-hidden h-2">
        <div :style="`width: ${video.languageRatio.ko}%; background: var(--accent)`"></div>
        <div :style="`width: ${video.languageRatio.en}%; background: var(--positive)`"></div>
        <div :style="`width: ${video.languageRatio.other}%; background: var(--neutral)`"></div>
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
