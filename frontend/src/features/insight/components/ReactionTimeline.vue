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
// 선택된 30분 창(BurstWindow.key) — showAllForDay가 false일 때만 의미 있음
const activeWindowKey = ref<string | null>(null)
// 어떤 경로로 열든(요약 pill, 차트 마커 직접 클릭) 처음엔 그 날의 "전체"를 합친 뷰로 시작 —
// 특정 시간대가 먼저 선택돼 있으면 지금 보이는 게 그 구간 전체인지 일부인지 헷갈림.
// 시간 칩은 사용자가 직접 눌렀을 때만(select-time 이벤트) 특정 시간창으로 좁혀짐
function openBurstDetail(i: number) {
  expandedBurstIdx.value = i
  showAllForDay.value = true
  activeWindowKey.value = null
}

const burstHoverIdx = ref<number | null>(null)

// 감정 급변(isBurst)과 댓글량 급증(isVolumeBurst)은 서로 독립적인 신호라 화면에서도 분리해서
// 다뤄야 함 — 마커 표시 여부/클릭 판정은 "둘 중 하나라도" 기준, 색과 라벨은 어떤 종류인지에 따라 갈림
// data[i] 형태의 인덱스 접근은 noUncheckedIndexedAccess 때문에 TimelinePoint | undefined로
// 잡혀서, 이 헬퍼들은 v-for 변수(항상 확정)와 인덱스 접근(undefined 가능) 양쪽에서 다 불려도
// 되게 매개변수를 옵셔널로 받음
function isAnyBurst(d?: TimelinePoint): boolean {
  return !!(d?.isBurst || d?.isVolumeBurst)
}
type BurstKind = 'SENTIMENT' | 'VOLUME' | 'BOTH'
function burstKind(d: TimelinePoint): BurstKind {
  if (d.isBurst && d.isVolumeBurst) return 'BOTH'
  return d.isVolumeBurst ? 'VOLUME' : 'SENTIMENT'
}
function burstLabel(d?: TimelinePoint): string {
  if (d?.direction === 'POSITIVE_SPIKE') return M.value.positiveSpike
  if (d?.direction === 'NEGATIVE_SPIKE') return M.value.negativeSpike
  if (d?.isVolumeBurst) return M.value.volumeSpike
  return ''
}
function burstZScore(d?: TimelinePoint): number | undefined {
  return d?.isBurst ? d.zScore : d?.volumeZScore
}
// 색상 의미를 고정: 초록=긍정, 빨강=부정, 주황(anomaly)=감정 급변, 보라(volume-burst)=댓글량
// 이벤트 — 댓글량 급증이 빨강/주황 계열로 보이면 "부정 반응"이나 "감정 이상치"로 착각하기
// 쉬워서 별도 색 채널로 분리함. 감정 급변이 우선순위 높은 신호라 둘 다 있으면 amber를 메인으로
// 쓰고, 보라는 보조 점/링으로만 얹음(hasBothBursts 참고)
function hasBothBursts(d?: TimelinePoint): boolean {
  return !!(d?.isBurst && d?.isVolumeBurst)
}
// 순감정 라인 위 상시 표시되는 작은 점 테두리색
function burstDotStroke(d?: TimelinePoint): string {
  if (d?.isBurst) return 'var(--anomaly)'
  if (d?.isVolumeBurst) return 'var(--volume-burst)'
  return 'var(--net-line)'
}
// 마커(세로 가이드라인) 색 — 호버 중이면 항상 강조색, 아니면 종류별 색(감정 급변이 있으면
// 보라와 겹쳐도 amber 우선 — 보라는 별도 보조 점으로 표시하므로 선 색 자체는 단순하게 둠)
function burstLineColor(d?: TimelinePoint, i?: number): string {
  if (burstHoverIdx.value === i) return 'var(--anomaly)'
  if (d?.isBurst) return 'var(--anomaly)'
  if (d?.isVolumeBurst) return 'var(--volume-burst)'
  return 'var(--subtext)'
}

// '3시간 후' / '3 hours later' / '3小时后' / '3時間後' — 등빈도 구간의 x축 라벨
const ELAPSED_UNITS: Record<Lang, { minute: string; hour: string; day: string; week: string; month: string; year: string; suffix: string; prefix?: string }> = {
  ko: { minute: '분', hour: '시간', day: '일', week: '주', month: '개월', year: '년', suffix: ' 후' },
  en: { minute: 'm', hour: 'h', day: 'd', week: 'w', month: 'mo', year: 'y', suffix: ' later', prefix: '' },
  zh: { minute: '分钟', hour: '小时', day: '天', week: '周', month: '个月', year: '年', suffix: '后' },
  ja: { minute: '分', hour: '時間', day: '日', week: '週', month: 'ヶ月', year: '年', suffix: '後' },
}

const NOW_LABEL: Record<Lang, string> = { ko: '현재', en: 'Now', zh: '现在', ja: '現在' }

// 값+단위만("3시간", "13개월") — 접미사("후"/"later") 없이, 이벤트 카드의 "업로드 후 {t}" 같은
// 다른 접두/접미 표현에도 재사용하기 위해 formatElapsed에서 분리
function elapsedValueUnit(seconds: number | null | undefined, lang: Lang): string | null {
  if (seconds == null) return null
  const u = ELAPSED_UNITS[lang]
  // 프리미어 대기실 댓글 등으로 공식 업로드 시각보다 먼저 달린 댓글은 음수가 될 수 있음 —
  // "-50분" 같은 이상한 표시 대신 0으로 클램프
  const clamped = Math.max(seconds, 0)
  const hours = clamped / 3600
  if (hours < 1) return `${Math.round(clamped / 60)}${u.minute}`
  if (hours < 24) return `${Math.round(hours)}${u.hour}`
  const days = hours / 24
  if (days < 14) return `${Math.round(days)}${u.day}`
  if (days < 60) return `${Math.round(days / 7)}${u.week}`
  if (days < 730) return `${Math.round(days / 30)}${u.month}`
  return `${Math.round(days / 365)}${u.year}`
}
function formatElapsed(seconds: number | null | undefined, lang: Lang): string {
  const vu = elapsedValueUnit(seconds, lang)
  return vu == null ? '' : `${vu}${ELAPSED_UNITS[lang].suffix}`
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
type BurstTimeEntry = {
  index: number; direction: TimelinePoint['direction']; timeLabel: string; kind: BurstKind
  severity: number; minuteOfDay: number
}
// 댓글이 폭주하는 구간(예: 업로드 직후)은 등빈도 버킷 하나가 몇 초~몇 분짜리라, 같은 날 안에서도
// 버킷 단위로 다 보여주면 "오후 9:00"이 수십 개씩 찍히는 등 사실상 구분이 안 되는 시간 칩이
// 쏟아진다. 그래서 드로어의 시간 칩은 버킷 단위가 아니라 30분 창(window) 단위로 한 번 더
// 묶어서 보여주고, 실제 병합(댓글 목록)도 그 창에 속한 버킷 전체를 대상으로 함
const BURST_WINDOW_MINUTES = 30
type BurstWindow = {
  key: string; timeLabel: string; indices: number[]; direction: TimelinePoint['direction']; kind: BurstKind
}
type BurstDayGroup = {
  dateKey: string; dateLabel: string; direction: TimelinePoint['direction']
  hasVolumeBurst: boolean; hasSentimentBurst: boolean; severity: number
  times: BurstTimeEntry[]; windows: BurstWindow[]
}

const burstDayGroups = computed(() => {
  const groups = new Map<string, { dateKey: string; dateLabel: string; times: BurstTimeEntry[] }>()

  props.data.forEach((d, i) => {
    if (!isAnyBurst(d) || !d.bucketStart) return
    const dt = new Date(d.bucketStart)
    const dateKey = `${dt.getFullYear()}-${dt.getMonth()}-${dt.getDate()}`
    const timeLabel = dt.toLocaleTimeString(LOCALE_MAP[props.lang], { hour: '2-digit', minute: '2-digit' })

    let group = groups.get(dateKey)
    if (!group) {
      const dateLabel = dt.toLocaleDateString(LOCALE_MAP[props.lang], { year: 'numeric', month: '2-digit', day: '2-digit' })
      group = { dateKey, dateLabel, times: [] }
      groups.set(dateKey, group)
    }
    group.times.push({
      index: i, direction: d.direction, timeLabel, kind: burstKind(d),
      severity: Math.max(Math.abs(d.zScore ?? 0), Math.abs(d.volumeZScore ?? 0)),
      minuteOfDay: dt.getHours() * 60 + dt.getMinutes(),
    })
  })

  // 그룹 대표값은 "그 날의 첫 이상치"가 아니라 "그 날 전체"를 훑어서 계산 — 첫 항목이
  // 우연히 volume-only여도 그 날 나중에 감정 급변이 있었으면 direction/hasSentimentBurst에
  // 반영되어야 pill 색·요약 카운트가 정확함
  const result: BurstDayGroup[] = [...groups.values()].map(g => {
    // 1단계: 30분 창 단위로 원본 버킷의 index만 모음
    const windowBuckets = new Map<string, { key: string; timeLabel: string; times: BurstTimeEntry[] }>()
    for (const t of g.times) {
      const windowStart = Math.floor(t.minuteOfDay / BURST_WINDOW_MINUTES) * BURST_WINDOW_MINUTES
      const key = String(windowStart)
      let wb = windowBuckets.get(key)
      if (!wb) {
        const timeLabel = new Date(0, 0, 0, Math.floor(windowStart / 60), windowStart % 60)
          .toLocaleTimeString(LOCALE_MAP[props.lang], { hour: '2-digit', minute: '2-digit' })
        wb = { key, timeLabel, times: [] }
        windowBuckets.set(key, wb)
      }
      wb.times.push(t)
    }
    // 2단계: 날짜 그룹과 동일한 우선순위 규칙(부정 > 긍정 > null, BOTH > 단일 종류)으로
    // 창 대표 방향/종류를 계산 — 로직을 두 곳에 다르게 두지 않고 그대로 재사용
    const windows: BurstWindow[] = [...windowBuckets.values()].map(wb => ({
      key: wb.key,
      timeLabel: wb.timeLabel,
      indices: wb.times.map(t => t.index),
      direction: wb.times.find(t => t.direction === 'NEGATIVE_SPIKE')?.direction
        ?? wb.times.find(t => t.direction === 'POSITIVE_SPIKE')?.direction
        ?? null,
      kind: wb.times.some(t => t.kind === 'BOTH') || (wb.times.some(t => t.kind === 'SENTIMENT') && wb.times.some(t => t.kind === 'VOLUME'))
        ? 'BOTH'
        : wb.times.some(t => t.kind === 'VOLUME') ? 'VOLUME' : 'SENTIMENT',
    }))

    return {
      dateKey: g.dateKey,
      dateLabel: g.dateLabel,
      direction: g.times.find(t => t.direction === 'NEGATIVE_SPIKE')?.direction
        ?? g.times.find(t => t.direction === 'POSITIVE_SPIKE')?.direction
        ?? null,
      hasVolumeBurst: g.times.some(t => t.kind !== 'SENTIMENT'),
      hasSentimentBurst: g.times.some(t => t.kind !== 'VOLUME'),
      severity: Math.max(...g.times.map(t => t.severity)),
      times: g.times,
      windows,
    }
  })

  // 중요도(그 날 가장 극단적인 z-score) 높은 순 — 기본 노출 개수도, "더보기"로 펼치는
  // 나머지도 이 순서를 그대로 이어감(날짜순으로 되돌리지 않아 목록이 한 기준으로 일관됨)
  result.sort((a, b) => b.severity - a.severity)
  return result
})

// 감정 급변과 댓글량 급증이 겹치면 감정 쪽으로 집계(다른 곳과 동일한 우선순위)해서
// 두 카운트를 더하면 정확히 전체 건수가 되게 함(중복 집계 없음)
const burstCounts = computed(() => {
  const groups = burstDayGroups.value
  const sentiment = groups.filter(g => g.hasSentimentBurst).length
  const volumeOnly = groups.filter(g => !g.hasSentimentBurst && g.hasVolumeBurst).length
  return { sentiment, volumeOnly }
})
// 숫자만 던지면 안 와닿아서, 어떤 조합이든 사람이 바로 읽을 수 있는 한 문장으로 요약
const burstSummarySentence = computed(() => {
  const { sentiment, volumeOnly } = burstCounts.value
  if (sentiment > 0 && volumeOnly > 0) {
    return M.value.burstSummaryBoth.replace('{v}', String(volumeOnly)).replace('{s}', String(sentiment))
  }
  if (volumeOnly > 0) return M.value.burstSummaryVolumeOnly.replace('{n}', String(volumeOnly))
  return M.value.burstSummarySentimentOnly.replace('{n}', String(sentiment))
})

// 업로드 후 이 기간 안의 이상치는 댓글 표본이 작아 흔들리기 쉬우므로, 개별 카드로 나열하는
// 대신 하나의 "주의해서 보라"는 caveat 카드로 묶는다 — 그 이후(late)는 방향/종류별로 각각
// 독립된 카드가 되어 "언제·어느 방향·왜 흥미로운지"가 카드 하나로 바로 읽히게 함
const EARLY_PERIOD_SECONDS = 7 * 24 * 3600 // 7일

type BurstEventType = 'EARLY' | 'POSITIVE' | 'NEGATIVE' | 'VOLUME' | 'BOTH'
type BurstEvent = {
  type: BurstEventType; dayGroups: BurstDayGroup[]; severity: number; elapsedSeconds: number | null
}

function firstElapsedSeconds(g: BurstDayGroup): number | null {
  return props.data[g.times[0]!.index]?.elapsedSeconds ?? null
}

const burstEvents = computed<BurstEvent[]>(() => {
  const groups = burstDayGroups.value // 이미 severity 내림차순
  const early: BurstDayGroup[] = []
  const late: BurstDayGroup[] = []
  for (const g of groups) {
    const elapsed = firstElapsedSeconds(g)
    if (elapsed != null && elapsed < EARLY_PERIOD_SECONDS) early.push(g)
    else late.push(g)
  }

  const events: BurstEvent[] = late.map(g => {
    const type: BurstEventType =
      g.hasSentimentBurst && g.hasVolumeBurst ? 'BOTH'
      : !g.hasSentimentBurst && g.hasVolumeBurst ? 'VOLUME'
      : g.direction === 'POSITIVE_SPIKE' ? 'POSITIVE'
      : 'NEGATIVE'
    return { type, dayGroups: [g], severity: g.severity, elapsedSeconds: firstElapsedSeconds(g) }
  })

  // 업로드 직후 caveat 카드는 항상 맨 뒤 — 이 카드는 "주의해서 볼 것"이라, 흥미로운(late)
  // 이벤트보다 먼저 눈에 띄면 우선순위가 뒤집힘
  if (early.length) {
    events.push({
      type: 'EARLY',
      dayGroups: early,
      severity: Math.max(...early.map(g => g.severity)),
      elapsedSeconds: Math.min(...early.map(g => firstElapsedSeconds(g) ?? Infinity)),
    })
  }
  return events
})

// 이상치가 많은 영상에서는 카드가 다 펼쳐지면 다시 복잡해지므로, late 이벤트만 상위 6개로
// 제한하고 나머지는 "+N개 더보기"로 접어둠(caveat 카드는 항상 노출, 개수 제한 대상 아님)
const BURST_EVENTS_VISIBLE = 6
const burstEventsExpanded = ref(false)
const lateBurstEvents = computed(() => burstEvents.value.filter(e => e.type !== 'EARLY'))
const earlyBurstEvent = computed(() => burstEvents.value.find(e => e.type === 'EARLY') ?? null)
const visibleBurstEvents = computed(() => {
  const late = burstEventsExpanded.value ? lateBurstEvents.value : lateBurstEvents.value.slice(0, BURST_EVENTS_VISIBLE)
  return earlyBurstEvent.value ? [...late, earlyBurstEvent.value] : late
})
const hiddenBurstEventCount = computed(() => Math.max(lateBurstEvents.value.length - BURST_EVENTS_VISIBLE, 0))

function eventTypeLabel(event: BurstEvent): string {
  if (event.type === 'EARLY') return M.value.burstEventTypeEarly
  if (event.type === 'POSITIVE') return M.value.positiveSpike
  if (event.type === 'NEGATIVE') return M.value.negativeSpike
  if (event.type === 'VOLUME') return M.value.volumeSpike
  return M.value.burstEventTypeBoth
}
function eventInterpretation(event: BurstEvent): string {
  if (event.type === 'EARLY') {
    const hasVolume = event.dayGroups.some(g => g.hasVolumeBurst)
    return hasVolume ? `${M.value.burstEarlyCaveat} ${M.value.burstEarlyVolumeNote}` : M.value.burstEarlyCaveat
  }
  if (event.type === 'POSITIVE') return M.value.burstPositiveInterpretation
  if (event.type === 'NEGATIVE') return `${M.value.burstNegativeInterpretation} ${M.value.burstNegativeLateNote}`
  if (event.type === 'VOLUME') return M.value.burstVolumeInterpretation
  return M.value.burstBothInterpretation
}
function eventColor(event: BurstEvent): string {
  if (event.type === 'POSITIVE') return 'var(--positive)'
  if (event.type === 'NEGATIVE') return 'var(--negative)'
  if (event.type === 'VOLUME') return 'var(--volume-burst)'
  if (event.type === 'BOTH') return 'var(--anomaly)'
  return 'var(--subtext)'
}
function eventDateLabel(event: BurstEvent): string {
  return event.dayGroups.map(g => g.dateLabel).join(' · ')
}
function eventElapsedLabel(event: BurstEvent): string {
  const vu = elapsedValueUnit(event.elapsedSeconds === Infinity ? null : event.elapsedSeconds, props.lang)
  return vu == null ? '' : M.value.burstUploadElapsedPrefix.replace('{t}', vu)
}
// 이벤트 카드 클릭/버튼 — dayGroups[0]은 이미 severity로 정렬된 목록에서 뽑혔으므로
// 이 이벤트 안에서 가장 극단적인 날을 연다(EARLY처럼 날짜가 여럿이어도 동일)
function openEvent(event: BurstEvent) {
  openDay(event.dayGroups[0]!)
}

// 날짜 pill은 그 날의 첫 이상치를 앵커로 열되(openBurstDetail이 showAll=true로 시작하므로
// 실제 초기 화면은 그 날 전체를 합친 뷰), 같은 날 여러 건이면 드로어 안에서 시간대를 전환함
// (따로 뜨는 드랍다운 없이 오른쪽 드로어 안에서 바로 처리)
function openDay(group: BurstDayGroup) {
  openBurstDetail(group.times[0].index)
}

const activeDayGroup = computed(() => {
  if (expandedBurstIdx.value == null) return null
  return burstDayGroups.value.find(g => g.times.some(t => t.index === expandedBurstIdx.value)) ?? null
})

// 여러 버킷(하루 전체 또는 30분 창)을 하나의 가상 포인트로 합침 — 긍정/중립/부정은 합산,
// 대표 댓글은 전부 모아 좋아요순 재정렬. direction/zScore는 그중 가장 극단적인(절대값이 큰)
// 버킷의 값을 대표로 씀(합산이 의미 없는 값이라). "전체 날짜" 병합과 "창 하나" 병합에 동일하게 씀
function mergePoints(indices: number[]): TimelinePoint | null {
  const points = indices.map(i => props.data[i]).filter((p): p is TimelinePoint => !!p)
  if (!points.length) return null

  const severity = (p: TimelinePoint) => Math.max(Math.abs(p.zScore ?? 0), Math.abs(p.volumeZScore ?? 0))
  const mostExtreme = points.reduce((best, p) => severity(p) > severity(best) ? p : best)

  return {
    ...mostExtreme,
    positive: points.reduce((s, p) => s + p.positive, 0),
    neutral: points.reduce((s, p) => s + p.neutral, 0),
    negative: points.reduce((s, p) => s + p.negative, 0),
    topComments: points.flatMap(p => p.topComments ?? []).sort((a, b) => b.likeCount - a.likeCount),
    bucketStart: points[0]!.bucketStart,
    bucketEnd: points[points.length - 1]!.bucketEnd ?? points[points.length - 1]!.bucketStart,
  }
}

const activeWindow = computed(() => {
  if (!activeDayGroup.value || activeWindowKey.value == null) return null
  return activeDayGroup.value.windows.find(w => w.key === activeWindowKey.value) ?? null
})

const drawerPoint = computed<TimelinePoint | null>(() => {
  if (expandedBurstIdx.value == null) return null
  const base = props.data[expandedBurstIdx.value]
  if (!activeDayGroup.value) return base ?? null

  if (showAllForDay.value) {
    return mergePoints(activeDayGroup.value.times.map(t => t.index)) ?? base ?? null
  }
  if (activeWindow.value) {
    return mergePoints(activeWindow.value.indices) ?? base ?? null
  }
  return base ?? null
})
const drawerLabel = computed(() => {
  if (showAllForDay.value) return activeDayGroup.value?.dateLabel ?? ''
  if (activeWindow.value) return `${activeDayGroup.value?.dateLabel ?? ''} ${activeWindow.value.timeLabel}`.trim()
  return pointLabels.value[expandedBurstIdx.value ?? -1] ?? ''
})

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
             기본은 회색(중립)/주황(감정 급변)/보라(댓글량 급증)로 은은하게, 이상치 요약 리스트를
             hover하면 그 지점만 금색으로 강조. 감정 급변과 댓글량 급증이 겹치면 선 색은 amber를
             메인으로 쓰고, 보라 점을 선 위쪽에 별도로 얹어서 두 신호를 섞지 않고 분리해서 보여줌 -->
        <g v-for="(point, i) in data" v-show="isAnyBurst(point)" :key="`burst1-${i}`" class="burst-marker"
          :class="{ 'burst-hover': burstHoverIdx === i }" style="cursor: pointer"
          @click="openBurstDetail(i)" @mouseenter="burstHoverIdx = i" @mouseleave="burstHoverIdx = null">
          <rect :x="xsIndex[i] - 8" :y="PT" width="16" :height="H - PT - PB" fill="transparent"/>
          <line :x1="xsIndex[i]" :y1="posPoints[i].y" :x2="xsIndex[i]" :y2="negPoints[i].y"
            :stroke="burstLineColor(point, i)"
            :stroke-opacity="burstHoverIdx === i ? 1 : burstHoverIdx != null ? 0.35 : 0.6"
            :stroke-width="burstHoverIdx === i ? 2.5 : 1.5"
            stroke-linecap="round" class="burst-line"/>
          <circle v-if="hasBothBursts(point)" :cx="xsIndex[i]" :cy="PT + 5" r="3" fill="var(--volume-burst)"/>
        </g>

        <rect v-for="(point, i) in data" :key="`hit-${i}`"
          :x="i === 0 ? 0 : (xsIndex[i - 1] + xsIndex[i]) / 2"
          :width="i === 0 ? (xsIndex[0] + xsIndex[1]) / 2 : i === n - 1 ? W - (xsIndex[n - 2] + xsIndex[n - 1]) / 2 : (xsIndex[i + 1] - xsIndex[i - 1]) / 2"
          y="0" :height="H - PB + 10" fill="transparent" :style="{ cursor: isAnyBurst(point) ? 'pointer' : 'crosshair' }"
          @mouseenter="chart1.hoveredIdx.value = i; burstHoverIdx = isAnyBurst(point) ? i : null"
          @click="isAnyBurst(point) && openBurstDetail(i)"/>
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
        <div v-if="isAnyBurst(data[chart2.hoveredIdx.value])" class="tt-burst" :style="{ color: burstDotStroke(data[chart2.hoveredIdx.value]) }">
          {{ burstLabel(data[chart2.hoveredIdx.value]) }}
          <span class="tt-z">(z={{ burstZScore(data[chart2.hoveredIdx.value])?.toFixed(2) }})</span>
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

        <!-- 감정 급변 + 댓글량 급증이 같은 버킷에 겹치면, 점 색을 섞는 대신 amber 점 밖에
             보라 링을 하나 더 둘러서 두 신호를 분리해서 보여줌 -->
        <template v-for="(pt, i) in netPoints" :key="`ndot2-${i}`">
          <circle v-if="hasBothBursts(data[i])" :cx="pt.x" :cy="pt.y" r="6"
            fill="none" stroke="var(--volume-burst)" stroke-width="1.5" opacity="0.85"/>
          <circle :cx="pt.x" :cy="pt.y" r="3.5" fill="var(--card)" :stroke="burstDotStroke(data[i])" stroke-width="1.5"/>
        </template>

        <g v-for="(point, i) in data" v-show="isAnyBurst(point)" :key="`burst2-${i}`" class="burst-marker"
          :class="{ 'burst-hover': burstHoverIdx === i }" style="cursor: pointer"
          @click="openBurstDetail(i)" @mouseenter="burstHoverIdx = i" @mouseleave="burstHoverIdx = null">
          <rect :x="xsTime[i] - 8" :y="PT" width="16" :height="H - PT - PB" fill="transparent"/>
          <line :x1="xsTime[i]" :y1="netPoints[i].y" :x2="xsTime[i]" :y2="meanY"
            :stroke="burstLineColor(point, i)"
            :stroke-opacity="burstHoverIdx === i ? 1 : burstHoverIdx != null ? 0.35 : 0.6"
            :stroke-width="burstHoverIdx === i ? 2.5 : 1.5"
            stroke-linecap="round" class="burst-line"/>
          <circle v-if="hasBothBursts(point)" :cx="xsTime[i]" :cy="PT + 5" r="3" fill="var(--volume-burst)"/>
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
          y="0" :height="H - PB + 10" fill="transparent" :style="{ cursor: isAnyBurst(point) ? 'pointer' : 'crosshair' }"
          @mouseenter="chart2.hoveredIdx.value = i; burstHoverIdx = isAnyBurst(point) ? i : null"
          @click="isAnyBurst(point) && openBurstDetail(i)"/>
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
      <span v-if="data.some(d => d.isVolumeBurst)" class="flex items-center gap-1.5">
        <span class="w-5 h-0.5 inline-block rounded-full" style="background: var(--volume-burst)"></span>
        {{ M.volumeSpike }}
      </span>
    </div>

    <!-- 이상치 이벤트 해석 블록 — 날짜를 그냥 나열하지 않고, "언제 · 어느 방향 · 왜 흥미로운지"가
         카드 하나로 바로 읽히게 의미 단위로 묶어서 보여줌. 업로드 직후 caveat 카드는 항상 맨 뒤 -->
    <div v-if="burstDayGroups.length" class="burst-events">
      <div class="burst-events-header">
        <p class="burst-events-title">
          {{ M.burstEventsHeading }} {{ burstDayGroups.length }}건
          <span class="burst-events-breakdown">
            · {{ M.sentimentBurstLabel }} {{ burstCounts.sentiment }} · {{ M.volumeSpike }} {{ burstCounts.volumeOnly }}
          </span>
        </p>
        <p class="burst-events-summary">{{ burstSummarySentence }}</p>
      </div>

      <div
        v-for="(event, i) in visibleBurstEvents"
        :key="i"
        class="burst-event-card"
        :class="{ 'burst-event-card--early': event.type === 'EARLY' }"
        :style="{ borderLeftColor: eventColor(event) }"
      >
        <div class="burst-event-head">
          <span class="burst-event-type" :style="{ color: eventColor(event) }">{{ eventTypeLabel(event) }}</span>
          <span v-if="event.severity" class="burst-event-z">z={{ event.severity.toFixed(2) }}</span>
        </div>
        <p class="burst-event-meta">
          {{ eventDateLabel(event) }}<template v-if="eventElapsedLabel(event)"> · {{ eventElapsedLabel(event) }}</template>
        </p>
        <p class="burst-event-desc">{{ eventInterpretation(event) }}</p>
        <button class="burst-event-btn" @click="openEvent(event)">{{ M.burstViewCommentsBtn }}</button>
      </div>

      <button v-if="!burstEventsExpanded && hiddenBurstEventCount > 0" class="burst-summary-more" @click="burstEventsExpanded = true">
        {{ M.burstShowMore.replace('{n}', String(hiddenBurstEventCount)) }}
      </button>
      <button v-else-if="burstEventsExpanded && hiddenBurstEventCount > 0" class="burst-summary-more" @click="burstEventsExpanded = false">
        {{ M.burstShowLess }}
      </button>
    </div>

  </div>

  <BurstCommentsDrawer
    v-if="drawerPoint"
    :point="drawerPoint"
    :label="drawerLabel"
    :lang="lang"
    :sibling-windows="activeDayGroup?.windows"
    :active-window-key="showAllForDay ? null : activeWindowKey"
    :show-all="showAllForDay"
    @select-time="showAllForDay = false; activeWindowKey = $event"
    @select-all="showAllForDay = true; activeWindowKey = null"
    @close="expandedBurstIdx = null; showAllForDay = false; activeWindowKey = null"
  />
</template>

<style scoped>
.burst-events {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 0.5px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.burst-events-header { margin-bottom: 2px; }
.burst-events-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--subtext);
}
.burst-events-breakdown {
  font-weight: 500;
  opacity: 0.75;
}
.burst-events-summary {
  font-size: 12.5px;
  color: var(--text);
  margin-top: 4px;
  line-height: 1.5;
}
.burst-summary-more {
  align-self: flex-start;
  padding: 4px 10px;
  border-radius: 999px;
  border: 0.5px dashed var(--border);
  background: transparent;
  color: var(--subtext);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.burst-summary-more:hover {
  color: var(--text);
  background: var(--card-hover);
  border-color: var(--subtext);
}

/* 이상치 이벤트 카드 — 타입 색이 왼쪽 테두리로 드러나고, 업로드 직후 caveat 카드는
   점선 테두리 + 톤다운된 텍스트로 "주의해서 볼 것"임을 구분함 */
.burst-event-card {
  border-left: 3px solid transparent;
  border-radius: 10px;
  background: var(--card-hover);
  border-top: 0.5px solid var(--border);
  border-right: 0.5px solid var(--border);
  border-bottom: 0.5px solid var(--border);
  padding: 12px 14px;
}
.burst-event-card--early {
  border-left-style: dashed;
  opacity: 0.85;
}
.burst-event-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}
.burst-event-type {
  font-size: 12.5px;
  font-weight: 700;
}
.burst-event-z {
  font-size: 10px;
  color: var(--dim);
  flex-shrink: 0;
}
.burst-event-meta {
  font-size: 11px;
  color: var(--subtext);
  margin-top: 3px;
}
.burst-event-desc {
  font-size: 12px;
  color: var(--text);
  line-height: 1.5;
  margin-top: 6px;
}
.burst-event-btn {
  margin-top: 8px;
  padding: 4px 12px;
  border-radius: 8px;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.burst-event-btn:hover {
  color: var(--text);
  background: var(--card-hover);
  border-color: rgb(from var(--accent) r g b / 0.4);
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
  /* color는 burstDotStroke로 인라인 바인딩(감정 급변=주황 / 댓글량 급증=보라) */
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
