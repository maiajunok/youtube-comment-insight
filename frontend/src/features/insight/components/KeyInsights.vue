<script setup lang="ts">
import { watch } from 'vue'
import type { KeyInsight, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'
import { insightApi } from '@/features/insight/api/insightApi'

const props = defineProps<{
  insights: KeyInsight[]
  lang: Lang
  languageRatio: { ko: number; en: number; other: number }
}>()

const fmt = (n: number) => n >= 1000 ? (n / 1000).toFixed(1) + 'K' : String(n)

const COMMENT_FIELD = { ko: null, en: 'commentEn', zh: 'commentZh', ja: 'commentJa' } as const

// 댓글이 이미 화면 언어와 같으면 번역 API를 호출하지 않는다 (BYOK 비용 절약)
async function fillComments() {
  const field = COMMENT_FIELD[props.lang]
  if (!field) return
  const missing = props.insights.filter(i => i.commentLang && i.commentLang !== props.lang && !i[field])
  if (!missing.length) return
  try {
    const translations = await insightApi.translateComments(missing.map(i => i.comment), props.lang)
    missing.forEach((i, idx) => { i[field] = translations[idx] || i.comment })
  } catch { /* 실패 시 원문 유지 */ }
}
watch(() => [props.insights, props.lang], fillComments, { immediate: true })

const getComment = (insight: KeyInsight) => {
  const field = COMMENT_FIELD[props.lang]
  return (field && insight[field]) || insight.comment
}
const isTranslated = (insight: KeyInsight) => getComment(insight) !== insight.comment

const getTopic = (insight: KeyInsight) => {
  if (props.lang === 'en') return insight.topicEn || insight.topic
  if (props.lang === 'zh') return insight.topicZh || insight.topic
  if (props.lang === 'ja') return insight.topicJa || insight.topic
  return insight.topic
}
</script>

<template>
  <div class="flex flex-col gap-4">

    <h2 class="text-[11px] font-bold uppercase tracking-widest" style="color: var(--subtext)">
      {{ messages[lang].keyInsights }}
    </h2>

    <!-- 댓글 카드 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div
        v-for="insight in insights"
        :key="insight.comment"
        class="rounded-xl border flex flex-col gap-3"
        :style="`background: var(--card); padding: var(--card-padding); border-color: ${
          insight.type === 'positive' ? 'rgb(from var(--positive) r g b / 0.3)' : 'rgb(from var(--negative) r g b / 0.3)'
        }`"
      >
        <div class="flex items-center justify-between">
          <span
            class="text-[11px] font-bold uppercase tracking-wider"
            :style="insight.type === 'positive' ? 'color: var(--positive)' : 'color: var(--negative)'"
          >
            {{ insight.type === 'positive' ? messages[lang].positiveLabel : messages[lang].negativeLabel }}
          </span>
          <span class="text-[11px] rounded-full border"
            style="color: var(--subtext); border-color: var(--border); padding: 3px 10px">
            {{ getTopic(insight) }}
          </span>
        </div>

        <p class="text-[14px] leading-relaxed" style="color: var(--text); line-height: 1.7; font-weight: 500;">
          {{ getComment(insight) }}
        </p>

        <p v-if="isTranslated(insight)" class="text-[11.5px] leading-relaxed" style="color: var(--dim); line-height: 1.6;">
          <span class="font-semibold uppercase tracking-wide" style="font-size: 9px; opacity: 0.8;">{{ messages[lang].originalCommentLabel }}</span>
          {{ insight.comment }}
        </p>

        <p class="text-[12px] font-medium" style="color: var(--subtext)">
          ♥ {{ fmt(insight.likes) }} {{ messages[lang].likesLabel }}
        </p>
      </div>
    </div>

    <!-- 언어 분포 -->
    <div class="rounded-xl border" style="background: var(--card); border-color: var(--border); padding: var(--card-padding)">
      <h3 class="text-[11px] font-bold uppercase tracking-widest mb-4" style="color: var(--subtext)">
        {{ messages[lang].langBreakdown }}
      </h3>
      <div class="grid grid-cols-3 gap-2 sm:gap-4 text-center">
        <div
          v-for="l in [
            { label: '한국어', pct: props.languageRatio.ko,    color: 'var(--accent)'   },
            { label: 'English', pct: props.languageRatio.en,    color: 'var(--positive)' },
            { label: 'Other',   pct: props.languageRatio.other, color: 'var(--neutral)'  },
          ]"
          :key="l.label"
          class="flex flex-col items-center gap-1"
        >
          <span class="text-3xl font-bold tabular-nums" :style="`color: ${l.color}`">{{ l.pct }}%</span>
          <span class="text-sm" style="color: var(--subtext)">{{ l.label }}</span>
        </div>
      </div>
    </div>

    <!-- 면책 문구 -->
    <p class="text-xs italic text-center pb-4" style="color: var(--subtext)">
      {{ messages[lang].disclaimer }}
    </p>

  </div>
</template>
