<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TimelinePoint, Lang } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'
import BurstCommentsDrawer from './BurstCommentsDrawer.vue'

const props = defineProps<{ data: TimelinePoint[]; lang: Lang }>()

const TOOLTIP_WIDTH = 220 // min-width 근사치, 오른쪽 넘침 판단용

// 차트 두 개(다이버징 차트 / 순감정 차트)가 각자 독립된 호버 상태를 가짐 — 공용 팩토리
function useChartHover() {
  const hoveredIdx = ref<number | null>(null)
  const mouseX = ref(0)
  const mouseY = ref(0)
  const wrapWidth = ref(0)

  function onMouseMove(e: MouseEvent) {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    mouseX.value = e.clientX - rect.left
    mouseY.value = e.clientY - rect.top
    wrapWidth.value = rect.width
  }

  // 오른쪽으로 붙이면 카드 밖으로 넘치는 구간(그래프 오른쪽 끝 근처)에서는 왼쪽으로 뒤집음
  const tooltipLeft = computed(() => {
    const overflowsRight = mouseX.value + 14 + TOOLTIP_WIDTH > wrapWidth.value
    return overflowsRight ? mouseX.value - TOOLTIP_WIDTH - 14 : mouseX.value + 14
  })

  return { hoveredIdx, mouseX, mouseY, wrapWidth, onMouseMove, tooltipLeft }
}

const chart1 = useChartHover() // 다이버징(긍정/부정) 차트
const chart2 = useChartHover() // 순감정 + 밴드 차트

const expandedBurstIdx = ref<number | null>(null)
const showAllForDay = ref(false)
function openBurstDetail(i: number) {
  expandedBurstIdx.value = i
  showAllForDay.value = false
}

const burstHoverIdx = ref<number | null>(null)

// '3시간 후' / '3 hours later' / '3小时后' / '3時間後' — 등빈도 구간의 x축 라벨
const ELAPSED_UNITS: Record<Lang, { minute: string; hour: string; day: string; week: string; month: string; year: string; suffix: string; prefix?: string }> = {
  ko: { minute: '분', hour: '시간', day: '일', week: '주', month: '개월', year: '년', suffix: ' 후' },
  en: { minute: 'm', hour: 'h', day: 'd', week: 'w', month: 'mo', year: 'y', suffix: ' later', prefix: '' },
  zh: { minute: '分钟', hour: '小时', day: '天', week: '周', month: '个月', year: '年', suffix: '后' },
  ja: { minute: '分', hour: '時間', day: '日', week: '週', month: 'ヶ月', year: '年', suffix: '後' },
}

const NOW_LABEL: Record<Lang, string> = { ko: '현재', en: 'Now', zh: '现在', ja: '現在' }

function formatElapsed(seconds: number | null | undefined, lang: Lang): string {
  if (seconds == null) return ''
  const u = ELAPSED_UNITS[lang]
  // 프리미어 대기실 댓글 등으로 공식 업로드 시각보다 먼저 달린 댓글은 음수가 될 수 있음 —
  // "-50분 후" 같은 이상한 표시 대신 0으로 클램프
  const clamped = Math.max(seconds, 0)
  const hours = clamped / 3600
  if (hours < 1) return `${Math.round(clamped / 60)}${u.minute}${u.suffix}`
  if (hours < 24) return `${Math.round(hours)}${u.hour}${u.suffix}`
  const days = hours / 24
  if (days < 14) return `${Math.round(days)}${u.day}${u.suffix}`
  if (days < 60) return `${Math.round(days / 7)}${u.week}${u.suffix}`
  if (days < 730) return `${Math.round(days / 30)}${u.month}${u.suffix}`
  return `${Math.round(days / 365)}${u.year}${u.suffix}`
}

// 마지막 포인트(가장 최근 댓글 구간)는 "N년 후" 같은 어색한 절대 경과값 대신
// 그냥 "현재"로 고정 — 보는 사람이 감 잡기 훨씬 쉬움
const pointLabels = computed(() =>
  props.data.map((d, i) => {
    if (d.label) return d.label
    if (i === props.data.length - 1) return NOW_LABEL[props.lang]
    return formatElapsed(d.elapsedSeconds, props.lang)
  })
)

const DAYS_SINCE_UPLOAD_LABEL: Record<Lang, (n: number) => string> = {
  ko: n => `업로드 ${n}일째`,
  en: n => `Day ${n} since upload`,
  zh: n => `上传后第 ${n} 天`,
  ja: n => `アップロード${n}日目`,
}
const LOCALE_MAP: Record<Lang, string> = { ko: 'ko-KR', en: 'en-US', zh: 'zh-CN', ja: 'ja-JP' }

// 그래프 아래 요약 리스트용 — 이상치 구간을 날짜별로 묶고, 같은 날 여러 번이면
// 펼쳤을 때 시간대별로 보여줌 (등빈도 버킷 특성상 같은 날 여러 버킷이 이상치로
// 잡히는 경우가 많아, 목록에서는 날짜 단위로 정리하는 게 덜 산만함)
type BurstTimeEntry = { index: number; direction: TimelinePoint['direction']; timeLabel: string }
type BurstDayGroup = { dateKey: string; dateLabel: string; direction: TimelinePoint['direction']; times: BurstTimeEntry[] }

const burstDayGroups = computed(() => {
  const groups = new Map<string, BurstDayGroup>()

  props.data.forEach((d, i) => {
    if (!d.isBurst || !d.bucketStart) return
    const dt = new Date(d.bucketStart)
    const dateKey = `${dt.getFullYear()}-${dt.getMonth()}-${dt.getDate()}`
    const timeLabel = dt.toLocaleTimeString(LOCALE_MAP[props.lang], { hour: '2-digit', minute: '2-digit' })

    let group = groups.get(dateKey)
    if (!group) {
      const dateLabel = dt.toLocaleDateString(LOCALE_MAP[props.lang], { year: 'numeric', month: '2-digit', day: '2-digit' })
      group = { dateKey, dateLabel, direction: d.direction, times: [] }
      groups.set(dateKey, group)
    }
    group.times.push({ index: i, direction: d.direction, timeLabel })
  })

  return [...groups.values()]
})

// 날짜 pill은 항상 그 날의 첫 이상치를 열고, 같은 날 여러 건이면 드로어 안에서
// 시간대를 전환함(따로 뜨는 드랍다운 없이 오른쪽 드로어 안에서 바로 처리)
function openDay(group: BurstDayGroup) {
  openBurstDetail(group.times[0].index)
}

const activeDayGroup = computed(() => {
  if (expandedBurstIdx.value == null) return null
  return burstDayGroups.value.find(g => g.times.some(t => t.index === expandedBurstIdx.value)) ?? null
})

// "전체" 선택 시 그 날의 모든 이상치 시간대를 하나로 합친 가상의 포인트를 만들어 드로어에 넘김 —
// 긍정/중립/부정은 합산, 대표 댓글은 전부 모아 좋아요순 재정렬. direction/zScore는 그 날 중
// 가장 극단적인(절대값이 큰) 시간대의 값을 대표로 씀(합산이 의미 없는 값이라)
const drawerPoint = computed<TimelinePoint | null>(() => {
  if (expandedBurstIdx.value == null) return null
  const base = props.data[expandedBurstIdx.value]
  if (!showAllForDay.value || !activeDayGroup.value) return base ?? null

  const points = activeDayGroup.value.times
    .map(t => props.data[t.index])
    .filter((p): p is TimelinePoint => !!p)
  if (!points.length) return base ?? null

  const mostExtreme = points.reduce((best, p) => Math.abs(p.zScore ?? 0) > Math.abs(best.zScore ?? 0) ? p : best)

  return {
    ...mostExtreme,
    positive: points.reduce((s, p) => s + p.positive, 0),
    neutral: points.reduce((s, p) => s + p.neutral, 0),
    negative: points.reduce((s, p) => s + p.negative, 0),
    topComments: points.flatMap(p => p.topComments ?? []).sort((a, b) => b.likeCount - a.likeCount),
    bucketStart: points[0]!.bucketStart,
    bucketEnd: points[points.length - 1]!.bucketEnd ?? points[points.length - 1]!.bucketStart,
  }
})
const drawerLabel = computed(() =>
  showAllForDay.value ? (activeDayGroup.value?.dateLabel ?? '') : (pointLabels.value[expandedBurstIdx.value ?? -1] ?? '')
)

// SVG 좌표계 상수
const W  = 1300
const H  = 320
const PL = 60
const PR = 40
const PT = 50
const PB = 50

const cW = W - PL - PR    // 1200
const cH = H - PT - PB    // 210

const n = computed(() => props.data.length)

// 막대(1번 차트)는 인덱스 균등 간격 — 막대는 불연속적인 표시라 시간 비례로 배치하면
// 뜸한 구간에 빈 칸이 생겨 "그 사이 댓글은 어디갔지"라는 착시를 줌. 균등 배치하면
// 항상 나란히 붙어있어서 그런 오해가 없음 (실제 시간 정보는 x축 라벨로 전달)
const xsIndex = computed(() =>
  props.data.map((_, i) => PL + (i / Math.max(n.value - 1, 1)) * cW)
)

// 선(2번 차트)은 실제 경과 시간에 비례해서 배치 — 선은 연속된 궤적이라 뜸한 구간도
// 자연스럽게 이어져 보이고, 오히려 언제 반응이 몰렸는지가 시각적으로 드러나서 더 유용함.
// elapsedSeconds가 없는 데이터(업로드 시각 파싱 실패 등)면 균등 간격으로 폴백
const timeScale = computed(() => {
  const hasElapsed = props.data.every(d => d.elapsedSeconds != null)
  if (!hasElapsed || n.value < 2) return null
  const values = props.data.map(d => d.elapsedSeconds as number)
  const min = values[0]
  const max = values[values.length - 1]
  return { min, span: Math.max(max - min, 1) }
})

const xsTime = computed(() => {
  const scale = timeScale.value
  if (!scale) return xsIndex.value
  return props.data.map(d => PL + (((d.elapsedSeconds as number) - scale.min) / scale.span) * cW)
})

// x축 라벨: 최소 픽셀 간격을 못 채우거나 직전에 찍힌 라벨과 텍스트가 같으면 건너뜀
// (등빈도 구간이 촘촘히 몰린 구간에서 "9시간 후"가 나란히 반복 찍히는 걸 방지)
const MIN_LABEL_GAP = 70
function computeVisibleLabels(xsArr: number[]): Set<number> {
  const visible = new Set<number>()
  let lastX = -Infinity
  let lastLabel = ''
  const lastIdx = n.value - 1
  props.data.forEach((_, i) => {
    const x = xsArr[i]
    const label = pointLabels.value[i]
    const isLast = i === lastIdx
    if (isLast || (x - lastX >= MIN_LABEL_GAP && label !== lastLabel)) {
      visible.add(i)
      lastX = x
      lastLabel = label
    }
  })
  return visible
}
const visibleLabelIndicesIndex = computed(() => computeVisibleLabels(xsIndex.value))
const visibleLabelIndicesTime = computed(() => computeVisibleLabels(xsTime.value))

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

// ── 순감정(net sentiment) 라인 + 볼린저 밴드 스타일 이상치 시각화 ──
// 백엔드 z-score 이상탐지(평균 ± Z_THRESHOLD*표준편차)와 같은 기준을 그대로 그래프에 그림.
// 긍정/부정 두 선을 따로 보여주는 대신, "지금 여론이 좋은지 나쁜지"를 하나의 선으로 압축하고,
// 그 선이 밴드를 벗어나는 지점 = 이상치라는 걸 클릭 없이도 바로 눈으로 알 수 있게 함.
const Z_THRESHOLD = 1.5

const netValues = computed(() => props.data.map(d => d.netSentiment ?? 0))

const netStats = computed(() => {
  const vals = netValues.value
  if (!vals.length) return { mean: 0, std: 0 }
  const mean = vals.reduce((a, b) => a + b, 0) / vals.length
  // 백엔드(pandas .std())는 표본표준편차(n-1로 나눔)를 쓰므로 여기도 똑같이 맞춤 —
  // 안 맞추면 버킷 수가 적을 때(20~30개) 밴드 폭이 달라져서 실제 isBurst 판정과 그래프가 어긋남
  const denom = Math.max(vals.length - 1, 1)
  const variance = vals.reduce((a, b) => a + (b - mean) ** 2, 0) / denom
  return { mean, std: Math.sqrt(variance) }
})

const netRange = computed(() => {
  const { mean, std } = netStats.value
  const bandTop = mean + Z_THRESHOLD * std
  const bandBottom = mean - Z_THRESHOLD * std
  const dataMin = Math.min(...netValues.value, bandBottom)
  const dataMax = Math.max(...netValues.value, bandTop)
  const pad = Math.max((dataMax - dataMin) * 0.18, 0.05)
  return { min: dataMin - pad, max: dataMax + pad }
})

function netY(v: number): number {
  const { min, max } = netRange.value
  const span = Math.max(max - min, 0.001)
  return PT + (1 - (v - min) / span) * cH
}

const netPoints = computed(() => xsTime.value.map((x, i) => ({ x, y: netY(netValues.value[i]) })))
const netLine = computed(() => smoothPath(netPoints.value))

const bandTopY = computed(() => netY(netStats.value.mean + Z_THRESHOLD * netStats.value.std))
const bandBottomY = computed(() => netY(netStats.value.mean - Z_THRESHOLD * netStats.value.std))
const meanY = computed(() => netY(netStats.value.mean))
const bandAreaPath = computed(() => {
  const top = xsTime.value.map(x => ({ x, y: bandTopY.value }))
  const bottom = xsTime.value.map(x => ({ x, y: bandBottomY.value }))
  return areaPath(top, bottom)
})

// y축 눈금 (순감정 점수, -1~1 범위 중 실제 데이터 범위만)
const yTicksNet = computed(() => {
  const { min, max } = netRange.value
  const step = (max - min) / 4
  return [1, 2, 3].map(i => ({
    label: (min + step * i).toFixed(2),
    y: netY(min + step * i),
  }))
})

// ── 원래 있던 긍정/부정 다이버징 차트 (비전공자용 직관적 뷰, 그대로 복원) ──
// 0선을 정중앙에 고정하고 좌우 대칭 스케일을 쓰면, 부정 값이 긍정보다 훨씬 작을 때
// 아래쪽 절반이 텅 비게 됨. 대신 긍정/부정 각각의 실제 최댓값 비율로 0선 위치를 옮기고
// 스케일도 따로 둬서, 안 쓰는 공간을 잘라내고 그래프 자체를 크게 씀
const NICE_STEPS = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]
function niceCeil(v: number): number {
  if (v <= 0) return 10
  const padded = v * 1.1
  const magnitude = Math.pow(10, Math.floor(Math.log10(padded)))
  const normalized = padded / magnitude
  const niceNormalized = NICE_STEPS.find(s => s >= normalized) ?? 10
  return niceNormalized * magnitude
}
function formatAxisValue(v: number): string {
  return v >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${Math.round(v)}`
}

const scalePos = computed(() => niceCeil(Math.max(...props.data.map(d => d.positive), 1)))
const scaleNeg = computed(() => niceCeil(Math.max(...props.data.map(d => d.negative), 1)))

// 0선 위치 — 긍정/부정 스케일 비율대로 배분 (최소 25%는 항상 확보해서 한쪽이 안 사라지게 함)
const zeroY = computed(() => {
  const total = scalePos.value + scaleNeg.value
  const posRatio = Math.min(Math.max(scalePos.value / total, 0.25), 0.75)
  return PT + cH * posRatio
})

const yPos = (v: number) => zeroY.value - (v / scalePos.value) * (zeroY.value - PT)
const yNeg = (v: number) => zeroY.value + (v / scaleNeg.value) * ((H - PB) - zeroY.value)

const posPoints = computed(() => xsIndex.value.map((x, i) => ({ x, y: yPos(props.data[i].positive) })))
const negPoints = computed(() => xsIndex.value.map((x, i) => ({ x, y: yNeg(props.data[i].negative) })))
const zeroLinePoints = computed(() => xsIndex.value.map(x => ({ x, y: zeroY.value })))

const posLine = computed(() => smoothPath(posPoints.value))
const negLine = computed(() => smoothPath(negPoints.value))
const posArea = computed(() => areaPath(posPoints.value, zeroLinePoints.value))
const negArea = computed(() => areaPath(zeroLinePoints.value, negPoints.value))

const yTicksPos = computed(() => {
  const step = scalePos.value / 4
  return [1, 2, 3, 4].map(i => ({ label: formatAxisValue(step * i), y: yPos(step * i) }))
})
const yTicksNeg = computed(() => {
  const step = scaleNeg.value / 4
  return [1, 2, 3, 4].map(i => ({ label: formatAxisValue(step * i), y: yNeg(step * i) }))
})

const M = computed(() => messages[props.lang])
</script>

<template>
  <div class="rounded-xl border" style="background: var(--card); border-color: var(--border); padding: var(--card-padding)">

    <!-- ══════════════ 차트 1: 긍정/부정 다이버징 (직관적 개요) ══════════════ -->
    <div class="flex items-start justify-between mb-5">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-[14px] font-bold" style="color: var(--text)">
            {{ M.sentimentTrend }}
          </h2>
          <span class="text-[10px] uppercase tracking-wide" style="color: var(--subtext); opacity: 0.5">
            ({{ M.reactionFlow }})
          </span>
        </div>
        <p class="text-[10px] mt-1 italic" style="color: var(--subtext)">{{ M.reactionSub }}</p>
      </div>
    </div>

    <div style="position: relative" @mousemove="chart1.onMouseMove">
      <Transition name="tt-fade">
      <div
        v-if="chart1.hoveredIdx.value != null"
        class="chart-tooltip"
        :style="{ left: chart1.tooltipLeft.value + 'px', top: chart1.mouseY.value - 10 + 'px' }"
      >
        <div class="tt-label">{{ pointLabels[chart1.hoveredIdx.value] }}</div>
        <div class="tt-row">
          <span class="tt-dot pos" />
          <span class="tt-key">{{ M.positive }}</span>
          <span class="tt-val">{{ data[chart1.hoveredIdx.value].positive.toLocaleString() }}</span>
        </div>
        <div class="tt-row">
          <span class="tt-dot neu" />
          <span class="tt-key">{{ M.neutral }}</span>
          <span class="tt-val">{{ data[chart1.hoveredIdx.value].neutral.toLocaleString() }}</span>
        </div>
        <div class="tt-row">
          <span class="tt-dot neg" />
          <span class="tt-key">{{ M.negative }}</span>
          <span class="tt-val">{{ data[chart1.hoveredIdx.value].negative.toLocaleString() }}</span>
        </div>
      </div>
      </Transition>

      <svg :viewBox="`0 0 ${W} ${H}`" style="width: 100%; height: auto" preserveAspectRatio="xMidYMid meet"
        @mouseleave="chart1.hoveredIdx.value = null; burstHoverIdx = null">
        <defs>
          <linearGradient id="grad-pos" x1="0" :y1="PT" x2="0" :y2="zeroY" gradientUnits="userSpaceOnUse">
            <stop offset="0%"   stop-color="var(--positive)" stop-opacity="0.32"/>
            <stop offset="100%" stop-color="var(--positive)" stop-opacity="0"/>
          </linearGradient>
          <linearGradient id="grad-neg" x1="0" :y1="H - PB" x2="0" :y2="zeroY" gradientUnits="userSpaceOnUse">
            <stop offset="0%"   stop-color="var(--negative)" stop-opacity="0.32"/>
            <stop offset="100%" stop-color="var(--negative)" stop-opacity="0"/>
          </linearGradient>
        </defs>

        <g v-for="tick in yTicksPos" :key="`pos-${tick.label}`">
          <line :x1="PL" :y1="tick.y" :x2="W - PR" :y2="tick.y" stroke="var(--divider-line)" stroke-width="1"/>
          <text :x="PL - 8" :y="tick.y + 4" text-anchor="end" font-size="12" fill="var(--dim)">{{ tick.label }}</text>
        </g>
        <g v-for="tick in yTicksNeg" :key="`neg-${tick.label}`">
          <line :x1="PL" :y1="tick.y" :x2="W - PR" :y2="tick.y" stroke="var(--divider-line)" stroke-width="1"/>
          <text :x="PL - 8" :y="tick.y + 4" text-anchor="end" font-size="12" fill="var(--dim)">-{{ tick.label }}</text>
        </g>

        <!-- 부드러운 선 + 면적: 긍정은 0선 위로, 부정은 0선 아래로 -->
        <path :d="posArea" fill="url(#grad-pos)"/>
        <path :d="negArea" fill="url(#grad-neg)"/>
        <path :d="posLine" fill="none" stroke="var(--positive)" stroke-width="2" stroke-opacity="0.8" stroke-linecap="round" stroke-linejoin="round"/>
        <path :d="negLine" fill="none" stroke="var(--negative)" stroke-width="2" stroke-opacity="0.8" stroke-linecap="round" stroke-linejoin="round"/>

        <circle v-for="(pt, i) in posPoints" :key="`pdot-${i}`" :cx="pt.x" :cy="pt.y" r="3.5" fill="var(--card)" stroke="var(--positive)" stroke-width="1.5"/>
        <circle v-for="(pt, i) in negPoints" :key="`ndot-${i}`" :cx="pt.x" :cy="pt.y" r="3" fill="var(--card)" stroke="var(--negative)" stroke-width="1.5"/>

        <line :x1="PL" :y1="zeroY" :x2="W - PR" :y2="zeroY" stroke="var(--outline-stroke)" stroke-width="1.5"/>
        <text :x="PL - 8" :y="zeroY + 4" text-anchor="end" font-size="12" fill="var(--dim)">0</text>

        <text v-for="(point, i) in data" v-show="visibleLabelIndicesIndex.has(i)" :key="`x-${i}`"
          :x="xsIndex[i]" :y="H - 14" text-anchor="middle" font-size="13" fill="var(--dim)">{{ pointLabels[i] }}</text>

        <line v-show="chart1.hoveredIdx.value != null" class="hover-guide"
          :x1="chart1.hoveredIdx.value != null ? xsIndex[chart1.hoveredIdx.value] : 0" :y1="PT"
          :x2="chart1.hoveredIdx.value != null ? xsIndex[chart1.hoveredIdx.value] : 0" :y2="H - 8"
          stroke="var(--outline-stroke)" stroke-width="1" stroke-dasharray="5 4"/>

        <!-- 이상치 지점은 긍정/부정 포인트를 직접 이어서 "이 격차로 이상치를 계산했다"는 걸 보여줌 —
             기본은 회색으로 은은하게, 이상치 요약 리스트를 hover하면 그 지점만 금색으로 강조 -->
        <g v-for="(point, i) in data" v-show="point.isBurst" :key="`burst1-${i}`" class="burst-marker"
          :class="{ 'burst-hover': burstHoverIdx === i }" style="cursor: pointer"
          @click="openBurstDetail(i)" @mouseenter="burstHoverIdx = i" @mouseleave="burstHoverIdx = null">
          <rect :x="xsIndex[i] - 8" :y="PT" width="16" :height="H - PT - PB" fill="transparent"/>
          <line :x1="xsIndex[i]" :y1="posPoints[i].y" :x2="xsIndex[i]" :y2="negPoints[i].y"
            :stroke="burstHoverIdx === i ? 'var(--anomaly)' : 'var(--subtext)'"
            :stroke-opacity="burstHoverIdx === i ? 1 : burstHoverIdx != null ? 0.35 : 0.6"
            :stroke-width="burstHoverIdx === i ? 2.5 : 1.5"
            stroke-linecap="round" class="burst-line"/>
        </g>

        <rect v-for="(point, i) in data" :key="`hit-${i}`"
          :x="i === 0 ? 0 : (xsIndex[i - 1] + xsIndex[i]) / 2"
          :width="i === 0 ? (xsIndex[0] + xsIndex[1]) / 2 : i === n - 1 ? W - (xsIndex[n - 2] + xsIndex[n - 1]) / 2 : (xsIndex[i + 1] - xsIndex[i - 1]) / 2"
          y="0" :height="H - PB + 10" fill="transparent" :style="{ cursor: point.isBurst ? 'pointer' : 'crosshair' }"
          @mouseenter="chart1.hoveredIdx.value = i; burstHoverIdx = point.isBurst ? i : null"
          @click="point.isBurst && openBurstDetail(i)"/>
      </svg>
    </div>

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

    <!-- ══════════════ 차트 2: 순감정 + 볼린저 밴드 (z-score 방법론 시각화) ══════════════ -->
    <div class="flex items-start justify-between mb-5"
      style="border-top: 0.5px solid var(--border); margin-top: var(--card-padding); padding-top: var(--card-padding)">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-[14px] font-bold" style="color: var(--text)">
            {{ M.netSentimentTrend }}
          </h2>
          <span class="text-[10px] uppercase tracking-wide" style="color: var(--subtext); opacity: 0.5">
            ({{ M.netSentimentAnomalyLabel }})
          </span>
        </div>
        <p class="text-[10px] mt-1 italic" style="color: var(--subtext)">{{ M.netSentimentSub }}</p>
      </div>
    </div>

    <div style="position: relative" @mousemove="chart2.onMouseMove">
      <Transition name="tt-fade">
      <div
        v-if="chart2.hoveredIdx.value != null"
        class="chart-tooltip"
        :style="{ left: chart2.tooltipLeft.value + 'px', top: chart2.mouseY.value - 10 + 'px' }"
      >
        <div class="tt-label">{{ pointLabels[chart2.hoveredIdx.value] }}</div>
        <div class="tt-row">
          <span class="tt-key">{{ M.netSentimentLabel }}</span>
          <span class="tt-val">{{ data[chart2.hoveredIdx.value].netSentiment?.toFixed(2) }}</span>
        </div>
        <div class="tt-row">
          <span class="tt-dot pos" />
          <span class="tt-key">{{ M.positive }}</span>
          <span class="tt-val">{{ data[chart2.hoveredIdx.value].positive.toLocaleString() }}</span>
        </div>
        <div class="tt-row">
          <span class="tt-dot neu" />
          <span class="tt-key">{{ M.neutral }}</span>
          <span class="tt-val">{{ data[chart2.hoveredIdx.value].neutral.toLocaleString() }}</span>
        </div>
        <div class="tt-row">
          <span class="tt-dot neg" />
          <span class="tt-key">{{ M.negative }}</span>
          <span class="tt-val">{{ data[chart2.hoveredIdx.value].negative.toLocaleString() }}</span>
        </div>
        <div v-if="data[chart2.hoveredIdx.value].isBurst" class="tt-burst">
          {{ data[chart2.hoveredIdx.value].direction === 'POSITIVE_SPIKE' ? M.positiveSpike : M.negativeSpike }}
          <span class="tt-z">(z={{ data[chart2.hoveredIdx.value].zScore?.toFixed(2) }})</span>
          <div class="tt-click-hint">{{ M.clickHint }}</div>
        </div>
      </div>
      </Transition>

      <svg :viewBox="`0 0 ${W} ${H}`" style="width: 100%; height: auto" preserveAspectRatio="xMidYMid meet"
        @mouseleave="chart2.hoveredIdx.value = null; burstHoverIdx = null">
        <g v-for="tick in yTicksNet" :key="tick.label">
          <line :x1="PL" :y1="tick.y" :x2="W - PR" :y2="tick.y" stroke="var(--divider-line)" stroke-width="1"/>
          <text :x="PL - 8" :y="tick.y + 4" text-anchor="end" font-size="12" fill="var(--dim)">{{ tick.label }}</text>
        </g>

        <path :d="bandAreaPath" fill="var(--subtext)" opacity="0.12"/>
        <line :x1="PL" :y1="meanY" :x2="W - PR" :y2="meanY" stroke="var(--outline-stroke)" stroke-width="1" stroke-dasharray="3 3"/>

        <path :d="netLine" fill="none" stroke="var(--net-line)" stroke-width="2.5" stroke-opacity="0.9" stroke-linecap="round" stroke-linejoin="round"/>

        <circle v-for="(pt, i) in netPoints" :key="`ndot2-${i}`" :cx="pt.x" :cy="pt.y" r="3.5"
          fill="var(--card)" :stroke="data[i].isBurst ? 'var(--anomaly)' : 'var(--net-line)'" stroke-width="1.5"/>

        <g v-for="(point, i) in data" v-show="point.isBurst" :key="`burst2-${i}`" class="burst-marker"
          :class="{ 'burst-hover': burstHoverIdx === i }" style="cursor: pointer"
          @click="openBurstDetail(i)" @mouseenter="burstHoverIdx = i" @mouseleave="burstHoverIdx = null">
          <rect :x="xsTime[i] - 8" :y="PT" width="16" :height="H - PT - PB" fill="transparent"/>
          <line :x1="xsTime[i]" :y1="netPoints[i].y" :x2="xsTime[i]" :y2="meanY"
            :stroke="burstHoverIdx === i ? 'var(--anomaly)' : 'var(--subtext)'"
            :stroke-opacity="burstHoverIdx === i ? 1 : burstHoverIdx != null ? 0.35 : 0.6"
            :stroke-width="burstHoverIdx === i ? 2.5 : 1.5"
            stroke-linecap="round" class="burst-line"/>
        </g>

        <text v-for="(point, i) in data" v-show="visibleLabelIndicesTime.has(i)" :key="`x2-${i}`"
          :x="xsTime[i]" :y="H - 14" text-anchor="middle" font-size="13" fill="var(--dim)">{{ pointLabels[i] }}</text>

        <line v-show="chart2.hoveredIdx.value != null" class="hover-guide"
          :x1="chart2.hoveredIdx.value != null ? xsTime[chart2.hoveredIdx.value] : 0" :y1="PT"
          :x2="chart2.hoveredIdx.value != null ? xsTime[chart2.hoveredIdx.value] : 0" :y2="H - 8"
          stroke="var(--outline-stroke)" stroke-width="1" stroke-dasharray="5 4"/>

        <rect v-for="(point, i) in data" :key="`hit2-${i}`"
          :x="i === 0 ? 0 : (xsTime[i - 1] + xsTime[i]) / 2"
          :width="i === 0 ? (xsTime[0] + xsTime[1]) / 2 : i === n - 1 ? W - (xsTime[n - 2] + xsTime[n - 1]) / 2 : (xsTime[i + 1] - xsTime[i - 1]) / 2"
          y="0" :height="H - PB + 10" fill="transparent" :style="{ cursor: point.isBurst ? 'pointer' : 'crosshair' }"
          @mouseenter="chart2.hoveredIdx.value = i; burstHoverIdx = point.isBurst ? i : null"
          @click="point.isBurst && openBurstDetail(i)"/>
      </svg>
    </div>

    <div class="flex items-center gap-5 mt-1 text-[11px]" style="color: var(--subtext)">
      <span class="flex items-center gap-1.5">
        <span class="w-5 h-0.5 inline-block rounded-full" style="background: var(--net-line)"></span>
        {{ M.netSentimentLabel }}
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-5 h-2.5 inline-block rounded-sm" style="background: var(--subtext); opacity: 0.25"></span>
        {{ M.normalRangeLabel }}
      </span>
      <span v-if="data.some(d => d.isBurst)" class="flex items-center gap-1.5">
        <span class="w-5 h-0.5 inline-block rounded-full" style="background: var(--anomaly)"></span>
        {{ M.anomalyDetected }}
      </span>
    </div>

    <!-- 이상치 요약 리스트 — 날짜별로 묶고, 같은 날 여러 건이면 드로어 안에서 시간대 전환 -->
    <div v-if="burstDayGroups.length" class="burst-summary">
      <p class="burst-summary-title">{{ M.anomalyDetected }} {{ burstDayGroups.length }}건</p>
      <button
        v-for="group in burstDayGroups"
        :key="group.dateKey"
        class="burst-summary-item"
        :class="{ 'burst-summary-item-active': group.times.some(t => t.index === expandedBurstIdx) || (group.times.length === 1 && burstHoverIdx === group.times[0].index) }"
        @click="openDay(group)"
        @mouseenter="burstHoverIdx = group.times[0].index"
        @mouseleave="burstHoverIdx = null"
      >
        <span class="burst-dot" :style="{ background: group.direction === 'NEGATIVE_SPIKE' ? 'var(--negative)' : 'var(--positive)' }"></span>
        <span class="burst-date">{{ group.dateLabel }}</span>
      </button>
    </div>

  </div>

  <BurstCommentsDrawer
    v-if="drawerPoint"
    :point="drawerPoint"
    :label="drawerLabel"
    :lang="lang"
    :sibling-times="activeDayGroup?.times"
    :active-index="showAllForDay ? null : expandedBurstIdx"
    :show-all="showAllForDay"
    @select-time="showAllForDay = false; expandedBurstIdx = $event"
    @select-all="showAllForDay = true"
    @close="expandedBurstIdx = null; showAllForDay = false"
  />
</template>

<style scoped>
.burst-summary {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 0.5px solid var(--border);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.burst-summary-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--subtext);
  margin-right: 4px;
}
.burst-summary-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 0.5px solid var(--border);
  background: var(--card-hover);
  font-size: 11px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.burst-summary-item:hover,
.burst-summary-item-active {
  border-color: var(--anomaly);
  background: rgb(255 222 89 / 0.1);
}
.burst-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.burst-date {
  font-weight: 600;
  color: var(--text);
}

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
  transition: left 0.1s ease-out, top 0.1s ease-out;
}
.tt-fade-enter-active, .tt-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.tt-fade-enter-from, .tt-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
.hover-guide {
  transition: x1 0.12s ease-out, x2 0.12s ease-out, opacity 0.12s ease-out;
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
.tt-burst {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 0.5px solid var(--border);
  font-size: 11.5px;
  font-weight: 700;
  color: var(--anomaly);
}
.tt-z { font-weight: 400; color: var(--subtext); }
.tt-click-hint {
  margin-top: 4px;
  font-size: 10.5px;
  font-weight: 400;
  color: var(--subtext);
}
.burst-line {
  transition: stroke-width 0.15s ease, stroke 0.15s ease, stroke-opacity 0.15s ease;
}
</style>
