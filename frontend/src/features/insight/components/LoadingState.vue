<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

defineProps<{ step: string; progress: number }>()

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])

const STEPS = computed(() => [
  { n: 1, label: M.value.loadingStep1Label, sub: M.value.loadingStep1Sub },
  { n: 2, label: M.value.loadingStep2Label, sub: M.value.loadingStep2Sub },
  { n: 3, label: M.value.loadingStep3Label, sub: M.value.loadingStep3Sub },
])
</script>

<template>
  <div class="flex flex-col items-center justify-center py-24 gap-10">

    <!-- 상단 스피너 + 타이틀 -->
    <div class="flex flex-col items-center gap-4">
      <div class="w-10 h-10 rounded-full border-[3px] animate-spin"
        style="border-color: rgba(67,97,238,0.2); border-top-color: var(--accent)" />
      <p class="text-sm font-medium" style="color: var(--subtext)">{{ M.loadingTitle }}</p>
    </div>

    <!-- 단계 리스트 -->
    <div class="flex flex-col gap-5 w-64">
      <div v-for="s in STEPS" :key="s.n" class="flex items-start gap-3">

        <!-- 상태 아이콘 -->
        <!-- 완료 -->
        <div v-if="progress > s.n"
          class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5"
          style="background: var(--positive)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>

        <!-- 진행 중 -->
        <div v-else-if="progress === s.n"
          class="w-6 h-6 rounded-full border-2 animate-spin shrink-0 mt-0.5"
          style="border-color: rgba(67,97,238,0.25); border-top-color: var(--accent)" />

        <!-- 대기 -->
        <div v-else
          class="w-6 h-6 rounded-full border-2 shrink-0 mt-0.5"
          style="border-color: var(--border)" />

        <!-- 텍스트 -->
        <div class="flex flex-col gap-0.5">
          <p class="text-[14px] font-medium transition-all"
            :style="progress === s.n
              ? 'color: var(--text)'
              : progress > s.n
                ? 'color: var(--subtext)'
                : 'color: var(--border)'">
            {{ s.label }}
          </p>
          <p v-if="progress === s.n" class="text-[11px]" style="color: var(--subtext)">
            {{ s.sub }}
          </p>
        </div>

      </div>
    </div>

    <!-- 프로그레스 바 -->
    <div class="w-64 h-1 rounded-full overflow-hidden" style="background: var(--border)">
      <div
        class="h-full rounded-full transition-all duration-700"
        style="background: var(--accent)"
        :style="{ width: `${Math.round((progress / 3) * 100)}%` }"
      />
    </div>

  </div>
</template>
