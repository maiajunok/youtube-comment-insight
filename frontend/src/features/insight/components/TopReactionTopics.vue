<script setup lang="ts">
import type { Topic, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'
import { displayLabel } from '@/features/insight/composables/useLabelTranslation'

const props = defineProps<{ topics: Topic[]; lang: Lang }>()
const emit = defineEmits<{ (e: 'select-topic', label: string): void }>()

const fmt = (n: number) => n >= 1000 ? (n / 1000).toFixed(1) + 'K' : String(n)

const getLabel = (topic: Topic) => displayLabel(topic, props.lang)
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

        <!-- 토픽명 -->
        <span
          class="text-[15px] font-medium flex-1 min-w-0 md:w-40 md:flex-none leading-snug group-hover:underline truncate md:order-2"
          style="color: var(--text)"
        >{{ getLabel(topic) }}</span>

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
        <div class="w-full md:w-auto md:flex-1 flex rounded overflow-hidden h-[26px] text-[11px] font-bold leading-none md:order-3">
          <div
            class="flex items-center justify-center text-white transition-all"
            :style="`width: ${topic.sentiment.positive}%; background: var(--positive)`"
          >{{ topic.sentiment.positive >= 8 ? topic.sentiment.positive + '%' : '' }}</div>
          <div
            class="flex items-center justify-center transition-all"
            :style="`width: ${topic.sentiment.neutral}%; background: var(--neutral); color: #94a3b8`"
          >{{ topic.sentiment.neutral >= 8 ? topic.sentiment.neutral + '%' : '' }}</div>
          <div
            class="flex items-center justify-center text-white transition-all"
            :style="`width: ${topic.sentiment.negative}%; background: var(--negative)`"
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
