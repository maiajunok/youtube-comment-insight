<script setup lang="ts">
import type { Topic, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'
import { displayLabel } from '@/features/insight/composables/useLabelTranslation'

const props = defineProps<{ topics: Topic[]; lang: Lang }>()
const emit = defineEmits<{ (e: 'select-topic', label: string): void }>()

const fmt = (n: number) => n >= 1000 ? (n / 1000).toFixed(1) + 'K' : String(n)

const getLabel = (topic: Topic) => displayLabel(topic, props.lang)

// 표본(mentionCount)이 적은 토픽의 긍정/부정 %는 과신하기 쉬워서, Wilson score interval
// 기반 신뢰도(백엔드 analysis/topic.py에서 계산)를 배지 + 툴팁으로만 가볍게 보여줌
const CONFIDENCE_KEY = { LOW: 'confidenceLow', MEDIUM: 'confidenceMedium', HIGH: 'confidenceHigh' } as const
function confidenceLabel(topic: Topic): string {
  const level = topic.confidence?.positive.level
  return level ? messages[props.lang][CONFIDENCE_KEY[level]] : ''
}
function confidenceTooltip(topic: Topic): string {
  const c = topic.confidence
  if (!c) return ''
  return messages[props.lang].confidenceTooltip
    .replace('{n}', String(c.positive.sampleSize))
    .replace('{posLow}', String(c.positive.ciLow)).replace('{posHigh}', String(c.positive.ciHigh))
    .replace('{negLow}', String(c.negative.ciLow)).replace('{negHigh}', String(c.negative.ciHigh))
}
// LOW(해석 주의)=이상치와 같은 amber, MEDIUM(표본 적음)=중립 회색 — 감정(긍/부정) 색과
// 겹치지 않는 팔레트를 써서 "신뢰도"를 "감정"으로 착각하지 않게 함
const CONFIDENCE_COLOR = { LOW: 'var(--anomaly)', MEDIUM: 'var(--subtext)', HIGH: 'var(--subtext)' } as const
function confidenceBadgeStyle(topic: Topic) {
  const level = topic.confidence?.positive.level
  const color = level ? CONFIDENCE_COLOR[level] : 'var(--subtext)'
  return `color: ${color}; border-color: color-mix(in srgb, ${color} 45%, transparent)`
}
// 표본이 충분한(HIGH) 토픽까지 배지를 붙이면 화면이 다 배지투성이라 오히려 신호가 죽음 —
// "주의가 필요한" LOW/MEDIUM만 배지로 드러내고, HIGH는 배지 없이 title(hover)로만 CI 확인 가능
function showConfidenceBadge(topic: Topic): boolean {
  const level = topic.confidence?.positive.level
  return level === 'LOW' || level === 'MEDIUM'
}
</script>

<template>
  <div class="rounded-xl border flex flex-col h-full"
    style="background: var(--card); border-color: var(--border); padding: var(--card-padding)">

    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-[11px] font-bold uppercase tracking-widest" style="color: var(--subtext)">
        {{ messages[lang].topReactionTopics }}
      </h2>
      <span class="text-[11px] uppercase tracking-wider" style="color: var(--subtext)">
        {{ messages[lang].totalMentions }}
      </span>
    </div>

    <!-- Topic Rows -->
    <div class="flex-1 flex flex-col justify-start gap-3 md:justify-evenly md:gap-0">
      <div
        v-for="(topic, i) in topics"
        :key="topic.label"
        class="flex flex-wrap md:flex-nowrap items-center gap-x-3 gap-y-2 rounded-lg px-2 py-2 -mx-2 cursor-pointer transition-all group"
        style="hover:background: rgba(255,255,255,0.04)"
        @click="emit('select-topic', topic.label)"
      >
        <!-- 순위 -->
        <span
          class="text-sm font-bold w-4 text-right shrink-0 tabular-nums md:order-1"
          :style="i === 0 ? 'color: var(--accent)' : 'color: var(--subtext)'"
        >{{ i + 1 }}</span>

        <!-- 토픽명 + 비율 신뢰도 배지(표본 적음/해석 주의일 때만 — 신뢰도 높음은 배지 없이
             title(hover)로만 CI 확인) -->
        <span class="flex items-center gap-1.5 min-w-0 flex-1 md:w-44 md:flex-none md:order-2">
          <span
            class="text-[15px] font-medium min-w-0 leading-snug group-hover:underline truncate"
            style="color: var(--text)"
            :title="confidenceTooltip(topic)"
          >{{ getLabel(topic) }}</span>
          <span
            v-if="showConfidenceBadge(topic)"
            class="text-[9px] font-bold uppercase tracking-wide shrink-0 rounded-full border px-1.5 py-0.5 cursor-help"
            :style="confidenceBadgeStyle(topic)"
            :title="confidenceTooltip(topic)"
          >{{ confidenceLabel(topic) }}</span>
        </span>

        <!-- 언급 수 -->
        <span
          class="text-xs md:text-sm font-bold tabular-nums shrink-0 md:w-12 md:text-right md:order-4"
          :style="i === 0 ? 'color: var(--accent)' : 'color: var(--text)'"
        >{{ fmt(topic.mentionCount) }}</span>

        <!-- 화살표 -->
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          class="shrink-0 opacity-40 group-hover:opacity-100 transition-opacity md:order-5"
          style="color: var(--subtext)">
          <polyline points="9 18 15 12 9 6"/>
        </svg>

        <!-- Stacked Sentiment Bar -->
        <div
          class="w-full md:w-auto md:flex-1 flex rounded overflow-hidden h-[26px] text-[11px] font-bold leading-none md:order-3"
          :title="confidenceTooltip(topic)"
        >
          <div
            class="flex items-center justify-center text-white transition-all"
            :style="`flex: ${topic.sentiment.positive} 1 0%; background: var(--positive)`"
          >{{ topic.sentiment.positive >= 8 ? topic.sentiment.positive + '%' : '' }}</div>
          <div
            class="flex items-center justify-center transition-all"
            :style="`flex: ${topic.sentiment.neutral} 1 0%; background: var(--neutral); color: #94a3b8`"
          >{{ topic.sentiment.neutral >= 8 ? topic.sentiment.neutral + '%' : '' }}</div>
          <div
            class="flex items-center justify-center text-white transition-all"
            :style="`flex: ${topic.sentiment.negative} 1 0%; background: var(--negative)`"
          >{{ topic.sentiment.negative >= 8 ? topic.sentiment.negative + '%' : '' }}</div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-7 pt-7 mt-3 border-t text-[11px]"
      style="border-color: var(--border); color: var(--subtext)">
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-sm inline-block shrink-0" style="background: var(--positive)"></span>
        {{ messages[lang].positive }}
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-sm inline-block shrink-0" style="background: var(--neutral)"></span>
        {{ messages[lang].neutral }}
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-sm inline-block shrink-0" style="background: var(--negative)"></span>
        {{ messages[lang].negative }}
      </span>
      <span class="ml-auto text-[10px] opacity-60">{{ messages[lang].clickHint }}</span>
    </div>

  </div>
</template>
