<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TimelinePoint, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'

const props = defineProps<{ data: TimelinePoint[]; lang: Lang }>()

const hoveredIdx = ref<number | null>(null)
const mouseX = ref(0)
const mouseY = ref(0)

function onMouseMove(e: MouseEvent) {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  mouseX.value = e.clientX - rect.left
  mouseY.value = e.clientY - rect.top
}

// SVG 좌표계 상수
const W  = 1300
const H  = 320
const PL = 60
const PR = 40
const PT = 50
const PB = 50

const cW = W - PL - PR    // 1200
const cH = H - PT - PB    // 210
const zeroY = PT + cH / 2 // 135 — 0 기준선 (가운데)

const n = computed(() => props.data.length)

// x 좌표
const xs = computed(() =>
  props.data.map((_, i) => PL + (i / (n.value - 1)) * cW)
)

// 긍정/부정 중 더 큰 값 기준으로 스케일 설정
const scale = computed(() => {
  const maxP = Math.max(...props.data.map(d => d.positive))
  const maxN = Math.max(...props.data.map(d => d.negative))
  return Math.ceil(Math.max(maxP, maxN) / 100) * 100
})

// value → SVG y 좌표
const yPos = (v: number) => zeroY - (v / scale.value) * (cH / 2)  // 위로↑
const yNeg = (v: number) => zeroY + (v / scale.value) * (cH / 2)  // 아래로↓

// 각 감정별 좌표 배열
const posPoints = computed(() =>
  xs.value.map((x, i) => ({ x, y: yPos(props.data[i].positive) }))
)
const negPoints = computed(() =>
  xs.value.map((x, i) => ({ x, y: yNeg(props.data[i].negative) }))
)
const zeroLine = computed(() =>
  xs.value.map(x => ({ x, y: zeroY }))
)

// 부드러운 베지어 곡선 path
function smoothPath(pts: { x: number; y: number }[]): string {
  if (!pts.length) return ''
  let d = `M ${pts[0].x},${pts[0].y}`
  for (let i = 1; i < pts.length; i++) {
    const cpx = (pts[i - 1].x + pts[i].x) / 2
    d += ` C ${cpx},${pts[i - 1].y} ${cpx},${pts[i].y} ${pts[i].x},${pts[i].y}`
  }
  return d
}

// 면적 경로: top 곡선 → bottom 역방향으로 닫기
function areaPath(
  top: { x: number; y: number }[],
  bottom: { x: number; y: number }[]
): string {
  if (!top.length) return ''
  let d = `M ${top[0].x},${top[0].y}`
  for (let i = 1; i < top.length; i++) {
    const cpx = (top[i - 1].x + top[i].x) / 2
    d += ` C ${cpx},${top[i - 1].y} ${cpx},${top[i].y} ${top[i].x},${top[i].y}`
  }
  const rev = [...bottom].reverse()
  d += ` L ${rev[0].x},${rev[0].y}`
  for (let i = 1; i < rev.length; i++) {
    const cpx = (rev[i - 1].x + rev[i].x) / 2
    d += ` C ${cpx},${rev[i - 1].y} ${cpx},${rev[i].y} ${rev[i].x},${rev[i].y}`
  }
  return d + ' Z'
}

// 긍정: posPoints 위 ~ zeroLine 아래, 부정: zeroLine 위 ~ negPoints 아래
const posArea = computed(() => areaPath(posPoints.value, zeroLine.value))
const negArea = computed(() => areaPath(zeroLine.value, negPoints.value))
const posLine = computed(() => smoothPath(posPoints.value))
const negLine = computed(() => smoothPath(negPoints.value))

// y축 눈금 (상단 4개)
const yTicks = computed(() => {
  const step = scale.value / 4
  return [1, 2, 3, 4].map(i => ({
    label: i === 4 ? `${(scale.value / 1000).toFixed(1)}k` : `${(step * i / 1000).toFixed(1)}k`,
    y: yPos(step * i),
  }))
})

const M = computed(() => messages[props.lang])
</script>

<template>
  <div class="rounded-xl border" style="background: var(--card); border-color: var(--border); padding: var(--card-padding)">

    <!-- Header -->
    <div class="flex items-start justify-between mb-5">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-[10px] font-bold uppercase tracking-widest" style="color: var(--subtext)">
            {{ M.sentimentTrend }}
          </h2>
          <span class="text-[10px] uppercase tracking-wide" style="color: var(--subtext); opacity: 0.5">
            ({{ M.reactionFlow }})
          </span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            style="color: var(--subtext); opacity: 0.4">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
        </div>
        <p class="text-[10px] mt-1 italic" style="color: var(--subtext)">{{ M.reactionSub }}</p>
      </div>

      <!-- By Hour 드롭다운 (placeholder) -->
      <button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[10px] cursor-pointer"
        style="border-color: var(--border); color: var(--subtext)">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        {{ M.byHour }}
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>
    </div>

    <!-- 차트 래퍼 (툴팁 포지셔닝용) -->
    <div style="position: relative" @mousemove="onMouseMove">

    <!-- 툴팁 (마우스 옆에 따라다님) -->
    <div
      v-if="hoveredIdx != null"
      class="chart-tooltip"
      :style="{ left: mouseX + 14 + 'px', top: mouseY - 10 + 'px' }"
    >
      <div class="tt-label">{{ data[hoveredIdx].label }}</div>
      <div class="tt-row">
        <span class="tt-dot pos" />
        <span class="tt-key">{{ M.positive }}</span>
        <span class="tt-val">{{ data[hoveredIdx].positive.toLocaleString() }}</span>
      </div>
      <div class="tt-row">
        <span class="tt-dot neu" />
        <span class="tt-key">{{ M.neutral }}</span>
        <span class="tt-val">{{ data[hoveredIdx].neutral.toLocaleString() }}</span>
      </div>
      <div class="tt-row">
        <span class="tt-dot neg" />
        <span class="tt-key">{{ M.negative }}</span>
        <span class="tt-val">{{ data[hoveredIdx].negative.toLocaleString() }}</span>
      </div>
    </div>

    <!-- SVG 양극 차트 -->
    <svg
      :viewBox="`0 0 ${W} ${H}`"
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      @mouseleave="hoveredIdx = null"
    >
      <defs>
        <!-- 긍정: 위에서 0선 방향으로 페이드 -->
        <linearGradient id="grad-pos" x1="0" y1="30" x2="0" y2="135" gradientUnits="userSpaceOnUse">
          <stop offset="0%"   stop-color="var(--positive)" stop-opacity="0.14"/>
          <stop offset="100%" stop-color="var(--positive)" stop-opacity="0"/>
        </linearGradient>
        <!-- 부정: 아래에서 0선 방향으로 페이드 -->
        <linearGradient id="grad-neg" x1="0" y1="240" x2="0" y2="135" gradientUnits="userSpaceOnUse">
          <stop offset="0%"   stop-color="var(--negative)" stop-opacity="0.14"/>
          <stop offset="100%" stop-color="var(--negative)" stop-opacity="0"/>
        </linearGradient>
      </defs>

      <!-- 상단 격자선 + y축 레이블 -->
      <g v-for="tick in yTicks" :key="tick.label">
        <line :x1="PL" :y1="tick.y" :x2="W - PR" :y2="tick.y"
          stroke="var(--divider-line)" stroke-width="1"/>
        <text :x="PL - 8" :y="tick.y + 4" text-anchor="end" font-size="12" fill="var(--dim)">
          {{ tick.label }}
        </text>
      </g>

      <!-- 0 기준선 (두껍게, 더 밝게) -->
      <line :x1="PL" :y1="zeroY" :x2="W - PR" :y2="zeroY"
        stroke="var(--outline-stroke)" stroke-width="1.5"/>
      <text :x="PL - 8" :y="zeroY + 4" text-anchor="end" font-size="12" fill="var(--dim)">0</text>

      <!-- 부정 레이블 -->
      <g v-for="tick in yTicks" :key="`neg-${tick.label}`">
        <line :x1="PL" :y1="zeroY + (zeroY - tick.y)" :x2="W - PR" :y2="zeroY + (zeroY - tick.y)"
          stroke="var(--divider-line)" stroke-width="1"/>
        <text :x="PL - 8" :y="zeroY + (zeroY - tick.y) + 4" text-anchor="end" font-size="12" fill="var(--dim)">
          -{{ tick.label }}
        </text>
      </g>

      <!-- 면적 채우기 -->
      <path :d="posArea" fill="url(#grad-pos)"/>
      <path :d="negArea" fill="url(#grad-neg)"/>

      <!-- 꺾은선 -->
      <path :d="posLine" fill="none" stroke="var(--positive)" stroke-width="2" stroke-opacity="0.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path :d="negLine" fill="none" stroke="var(--negative)" stroke-width="2" stroke-opacity="0.8" stroke-linecap="round" stroke-linejoin="round"/>

      <!-- 데이터 포인트 dot (긍정) -->
      <circle
        v-for="(pt, i) in posPoints"
        :key="`pdot-${i}`"
        :cx="pt.x" :cy="pt.y" r="3.5"
        fill="var(--card)" stroke="var(--positive)" stroke-width="1.5"
      />
      <!-- 데이터 포인트 dot (부정) -->
      <circle
        v-for="(pt, i) in negPoints"
        :key="`ndot-${i}`"
        :cx="pt.x" :cy="pt.y" r="3"
        fill="var(--card)" stroke="var(--negative)" stroke-width="1.5"
      />

      <!-- x축 레이블 -->
      <text
        v-for="(point, i) in data"
        :key="`x-${i}`"
        :x="xs[i]" :y="H - 14"
        text-anchor="middle"
        font-size="13"
        fill="var(--dim)"
      >{{ point.label }}</text>

      <!-- 호버 수직선 (x축 레이블까지) -->
      <line
        v-if="hoveredIdx != null"
        :x1="xs[hoveredIdx]" :y1="PT"
        :x2="xs[hoveredIdx]" :y2="H - 8"
        stroke="var(--outline-stroke)" stroke-width="1" stroke-dasharray="5 4"
      />

      <!-- 히트 영역 (투명 rect — 버킷별 클릭/호버 영역) -->
      <rect
        v-for="(_, i) in data"
        :key="`hit-${i}`"
        :x="i === 0 ? 0 : (xs[i - 1] + xs[i]) / 2"
        :width="i === 0
          ? (xs[0] + xs[1]) / 2
          : i === n - 1
            ? W - (xs[n - 2] + xs[n - 1]) / 2
            : (xs[i + 1] - xs[i - 1]) / 2"
        y="0" :height="H - PB + 10"
        fill="transparent"
        style="cursor: crosshair"
        @mouseenter="hoveredIdx = i"
      />

    </svg>
    </div><!-- 래퍼 끝 -->

    <!-- Legend -->
    <div class="flex items-center gap-5 mt-1 text-[11px]" style="color: var(--subtext)">
      <span class="flex items-center gap-1.5">
        <span class="w-5 h-0.5 inline-block rounded-full" style="background: var(--positive)"></span>
        {{ M.positive }}
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-5 h-0.5 inline-block rounded-full" style="background: var(--negative)"></span>
        {{ M.negative }}
      </span>
    </div>

  </div>
</template>

<style scoped>
.chart-tooltip {
  position: absolute;
  top: 8px;
  z-index: 10;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 10px 13px;
  pointer-events: none;
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  min-width: 130px;
}
.tt-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  letter-spacing: .04em;
}
.tt-row {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  padding: 2px 0;
}
.tt-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.tt-dot.pos { background: var(--positive); }
.tt-dot.neu { background: var(--neutral); }
.tt-dot.neg { background: var(--negative); }
.tt-key { color: var(--subtext); flex: 1; }
.tt-val { font-weight: 700; color: var(--text); }
</style>
