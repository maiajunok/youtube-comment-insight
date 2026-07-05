<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { insightApi } from '@/features/insight/api/insightApi'
import type { CommentGraphData, CommentGraphNode, VideoGraphData, VideoGraphNode, InsightData, Topic } from '@/features/insight/types/insight'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { useAnalysisStore } from '@/features/insight/stores/analysis'
import { useHistory } from '@/features/insight/composables/useHistory'
import { messages } from '@/locales/messages'

const router = useRouter()
const route = useRoute()
const settings = useSettingsStore()
const analysisStore = useAnalysisStore()
const M = computed(() => messages[settings.lang])

// ── 1단계: 분석된 영상 전체를 감정 기준으로 클러스터링한 개요 지도 ──
const overviewData = ref<VideoGraphData | null>(null)
const isLoadingOverview = ref(true)
// 백엔드가 준 구체적 에러 메시지(있으면 그대로 노출 — 백엔드 응답이라 지금은 항상 한국어)와
// 응답 자체가 없는 일반 연결 실패를 구분해서 저장 — 후자를 처음부터 M.value로 문자열을
// "구워서" 저장하면 나중에 언어를 바꿔도 이미 표시된 에러 문구는 그대로 남아 화면 전체가
// 다른 언어인데 이 메시지만 예전 언어로 보이는 문제가 생김. computed로 매 렌더마다
// 현재 언어 기준으로 다시 계산해야 graphError(아래)처럼 언어 전환에 즉시 반응함
const overviewErrorDetail = ref('')
const overviewErrorGeneric = ref(false)
const overviewError = computed(() => overviewErrorDetail.value || (overviewErrorGeneric.value ? M.value.backendError : ''))

// ── 2단계: 영상 하나를 골랐을 때 그 안의 댓글 반응 지도 ──
// route.query.videoId를 유일한 출처로 둠 — selectVideo/backToOverview가 각자 로컬 상태를
// 따로 갱신하면 아래 watch와 타이밍이 어긋나 "클릭해도 안 바뀌는" 버그가 생기기 쉬움
const selectedVideoId = computed(() => {
  const v = route.query.videoId
  return typeof v === 'string' && v ? v : null
})
const selectedVideoTitle = ref('')
const selectedVideoThumbnail = ref('')
const graphData = ref<CommentGraphData | null>(null)
const isLoadingGraph = ref(false)
const graphError = ref<'' | '404' | 'other'>('')

// 2D SVG viewBox 계산용 컨테이너 실측 크기 참조(ResizeObserver) — 3D 렌더러는 더 이상 없음
const graphContainer = ref<HTMLElement | null>(null)

// 원색(비비드)이 사이트의 muted한 톤과 안 어울린다는 피드백 — 색상(파랑/분홍/주황/초록)은
// 그대로 두되 채도만 낮춰서 대시보드 톤에 맞춤. 강조는 이 색 자체를 바꾸는 대신 outline으로만 함.
// 라이트 테마 기준 톤은 다크 배경(#121110)에서 명도가 부족해 묻히므로 다크 테마에서 더 밝게 씀
// 카키/갈색 톤이 탁하다는 피드백 — blue/rose/green/orange/purple/teal로 색상은 서로 뚜렷이
// 구분되면서도 채도를 눌러 과하지 않게(사이트의 muted 톤 유지)
const TOPIC_PALETTE_LIGHT = ['#5B8DB8', '#C97B90', '#6FA97A', '#D68A3E', '#8B7FC9', '#4FA5A0']
const TOPIC_PALETTE_DARK = ['#7EB0DE', '#E0A0B4', '#8FCB9A', '#EDAD64', '#AFA3E8', '#6FC9C4']
const TOPIC_PALETTE = computed(() => settings.theme === 'dark' ? TOPIC_PALETTE_DARK : TOPIC_PALETTE_LIGHT)

// 실제로는 "100% 긍정"이나 "100% 부정" 영상은 거의 없어서, 이론상 -100~100 전체
// 범위로 색을 매핑하면 대부분 영상이 중간의 비슷한 색(누런 초록)에 몰려 구분이 잘 안 됨.
// 그래서 이론적 최댓값이 아니라 지금 분석된 영상들의 실제 점수 분포(min~max)를 0~120도
// 색상환에 꽉 채워서 매핑 — 컬러맵에서 흔히 쓰는 대비 스트레칭(contrast stretching)
const sentimentScoreRange = computed(() => {
  const nodes = overviewData.value?.nodes ?? []
  const scores = nodes.map(n => n.sentiment.positive - n.sentiment.negative)
  if (!scores.length) return { min: -100, max: 100 }
  const min = Math.min(...scores)
  const max = Math.max(...scores)
  return min === max ? { min: min - 1, max: max + 1 } : { min, max }
})

// 긍정-부정 점수를 빨강(부정)~초록(긍정) 색상으로 매핑(실제 분포 기준으로 대비 스트레칭됨).
// 이전엔 HSL 색상환을 그대로(빨강→노랑→초록) 돌려서 "기본 그래프 초록/빨강" 느낌이 강했음.
// 실제로 채도 낮춘 3개 고정색(부정/중립/긍정)만 정해두고 그 사이를 선형 보간하면 중간값이
// 애매한 갈색/누런빛으로 새지 않고 항상 이 3색 톤 안에서만 움직여서 훨씬 차분해 보임.
// 라이트 테마 기준으로 고른 톤을 다크 테마 배경(#121110, 거의 검정)에 그대로 쓰면 명도가
// 부족해 노드가 배경에 파묻혀 버림 — 같은 색상군을 유지하되 다크 테마에서만 더 밝은 버전을 씀
const sentimentPalette = computed(() => settings.theme === 'dark'
  ? { neg: '#D9827C', neu: '#D6C48C', pos: '#86C486' }
  : { neg: '#B64A4A', neu: '#B7A36A', pos: '#65A765' })
function mixHex(hexA: string, hexB: string, factor: number): string {
  const a = parseInt(hexA.replace('#', ''), 16), b = parseInt(hexB.replace('#', ''), 16)
  const mix = (shift: number) => Math.round(((a >> shift) & 255) + (((b >> shift) & 255) - ((a >> shift) & 255)) * factor)
  const toHex2 = (n: number) => n.toString(16).padStart(2, '0')
  return `#${toHex2(mix(16))}${toHex2(mix(8))}${toHex2(mix(0))}`
}
function sentimentColor(sentiment: { positive: number; negative: number }): string {
  const score = sentiment.positive - sentiment.negative
  const { min, max } = sentimentScoreRange.value
  const t = Math.min(Math.max((score - min) / (max - min), 0), 1)
  const { neg, neu, pos } = sentimentPalette.value
  return t < 0.5 ? mixHex(neg, neu, t / 0.5) : mixHex(neu, pos, (t - 0.5) / 0.5)
}

// 댓글 지도의 토픽↔색 배정 — 오른쪽 목록·범례가 항상 같은 매핑을 쓰도록 공유
const commentTopics = computed(() => graphData.value ? [...new Set(graphData.value.nodes.map(n => n.topic))] : [])
function topicColor(topic: string): string {
  const idx = commentTopics.value.indexOf(topic)
  return TOPIC_PALETTE.value[idx % TOPIC_PALETTE.value.length] ?? '#888'
}

// ── 옆 패널 — 기본은 지금 지도에 있는 노드 목록, 노드를 클릭하면 그 노드의 상세로 전환됨.
// (호버로 뜨는 방식은 그래프 폭이 바뀌면서 화면이 밀리는 문제가 있어 패널은 항상 마운트해두고
// 내용만 목록⇄상세로 바꿈. 선택된 노드는 3D 쪽에서 크기를 키워 "선택됨"을 표시) ──
type NeighborInfo = { id: string; label: string; similarity: number; commonTopics?: string[] }

const hoveredNodeId = ref<string | null>(null)
const selectedNodeId = ref<string | null>(null)

const panelVideo = ref<VideoGraphNode | null>(null)
const panelComment = ref<CommentGraphNode | null>(null)

const listNodes = computed<(VideoGraphNode | CommentGraphNode)[]>(() =>
  selectedVideoId.value ? (graphData.value?.nodes ?? []) : (overviewData.value?.nodes ?? [])
)
function listLabel(n: VideoGraphNode | CommentGraphNode): string {
  return selectedVideoId.value ? (n as CommentGraphNode).text : (n as VideoGraphNode).title
}

// 댓글 지도의 목록 모드 — 처음엔 댓글을 다 늘어놓지 않고 토픽 그룹만 보여주고,
// 그룹 하나를 고르면 그 토픽으로 분류된 댓글만 필터링해서 보여줌.
// 그래프 노드 수(topicGroups의 count)는 30개로 캡핑되어 다 똑같이 보이므로,
// 옆에 보여줄 개수는 전체 댓글 기준 실제 분류 개수(videoTopics의 mentionCount)를 씀
const selectedTopicFilter = ref<string | null>(null)
const videoTopics = ref<Topic[]>([])
const topicGroups = computed(() => {
  if (!graphData.value) return []
  const counts = new Map<string, number>()
  graphData.value.nodes.forEach(n => counts.set(n.topic, (counts.get(n.topic) ?? 0) + 1))
  const groups = commentTopics.value.map(t => ({
    topic: t,
    count: videoTopics.value.find(vt => vt.label === t)?.mentionCount ?? counts.get(t) ?? 0,
  }))
  // 단순 개수만 있으면 "목록"처럼 보이는데, 비중(%)까지 있으면 topic distribution처럼
  // 읽혀서 지도 옆 패널이 실제 분석 결과라는 느낌이 더 남
  const total = groups.reduce((sum, g) => sum + g.count, 0) || 1
  return groups.map(g => ({ ...g, pct: Math.round((g.count / total) * 100) }))
})
const filteredComments = computed<CommentGraphNode[]>(() =>
  graphData.value && selectedTopicFilter.value
    ? graphData.value.nodes.filter(n => n.topic === selectedTopicFilter.value)
    : []
)
// 댓글 상세 헤더의 카운트 뱃지 — topicGroups와 동일한 값(캡핑 안 된 실제 분류 개수)을 재사용
const panelCommentTopicCount = computed(() =>
  panelComment.value ? topicGroups.value.find(g => g.topic === panelComment.value!.topic)?.count ?? 0 : 0
)

const listItemEls = new Map<string, HTMLElement>()
function setListItemRef(id: string, el: unknown) {
  if (el instanceof HTMLElement) listItemEls.set(id, el)
  else listItemEls.delete(id)
}
// 노드를 호버하면 목록에서도 어떤 항목인지 바로 보이게 스크롤해서 보여줌(그래프 쪽 강조는
// emphasisScale/nodeFocusOpacity가 hoveredNodeId를 직접 참조하는 computed라 여기서 따로
// 갱신할 필요 없음)
watch(hoveredNodeId, (id) => {
  if (id) listItemEls.get(id)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
})

// 선택된 노드 하나만 확실히 커 보이게(호버·엣지끝은 그보다 작게) — 전에는 호버/선택/엣지끝이
// 다 똑같이 1.15배라 "내가 누른 게 어느 것인지" 비슷한 크기의 이웃들 사이에서 구분이 잘 안 됐음
function emphasisScale(id: string): number {
  if (id === selectedNodeId.value) return 1.35
  if (id === hoveredNodeId.value) return 1.1
  const e = selectedEdge.value
  if (e && (id === e.source || id === e.target)) return 1.2
  return 1
}

function isEdgeSelected(l: { source: string; target: string }): boolean {
  const e = selectedEdge.value
  return !!e && e.source === l.source && e.target === l.target
}

// ── Focus mode — 노드나 엣지를 클릭하면 관련 없는 나머지는 흐리게 죽여서
// "무엇과 무엇이 연결됐는지"가 화면 전체에서 바로 읽히게 함(호버만으로는 발동 안 하고,
// 클릭으로 선택이 확정됐을 때만 — 패널이 열려 있는 상태와 동일한 조건) ──
function nodeFocusOpacity(id: string): number {
  if (selectedNodeId.value) {
    if (id === selectedNodeId.value) return 1
    const links = selectedVideoId.value ? (graphData.value?.links ?? []) : (overviewData.value?.links ?? [])
    const isNeighbor = links.some(l =>
      (l.source === selectedNodeId.value && l.target === id) ||
      (l.target === selectedNodeId.value && l.source === id))
    return isNeighbor ? 1 : 0.25
  }
  if (selectedEdge.value) {
    return id === selectedEdge.value.source || id === selectedEdge.value.target ? 1 : 0.25
  }
  // 토픽 focus mode — 오른쪽에서 토픽 하나를 고르면(댓글 지도 전용) 그 토픽 댓글만
  // 또렷하게 남기고 나머지는 확 죽여서 "토픽 클러스터 지도"처럼 보이게 함
  if (selectedTopicFilter.value) {
    const node = graphData.value?.nodes.find(n => n.id === id)
    return node?.topic === selectedTopicFilter.value ? 1 : 0.18
  }
  return 1
}

function edgeFocusOpacity(l: { source: string; target: string }): number {
  if (selectedNodeId.value) {
    return l.source === selectedNodeId.value || l.target === selectedNodeId.value ? 1 : 0.12
  }
  if (selectedEdge.value) {
    return isEdgeSelected(l) ? 1 : 0.12
  }
  return 1
}

// 연결선 스타일 — 두 지도의 역할이 다름. 개요(영상 간) 지도는 edge 자체가 핵심 정보라
// 장식처럼 흐릿하면 안 되고, 기본 상태에서도 최소 0.35 불투명도/1.4px 두께를 보장함.
// 반대로 댓글 지도는 노드 수가 많아서 선을 다 그려두면 지저분해지고(토픽 클러스터를
// 보여주는 게 목적) — 그래서 댓글 지도는 기본 상태에서 선을 거의 숨기고, 호버/선택된
// 댓글의 연결만 (isEdgeFocused를 통해) 또렷하게 드러냄
function linkAlpha(similarity: number | undefined): number {
  if (selectedVideoId.value) return 0.06
  const raw = 1.85 * (similarity ?? 0) - 1.115
  return Math.min(0.6, Math.max(0.35, raw))
}
function linkWidth(similarity: number | undefined): number {
  if (selectedVideoId.value) return 1
  const norm = (linkAlpha(similarity) - 0.35) / (0.6 - 0.35)
  return 1.4 + norm * 0.6
}

// ── 2D 시각화 ────────────────────────────────────────────────────────────────
// 임베딩 유사도를 보여줄 때 실제로 흔히 쓰는 형태는 3D가 아니라 2D 스캐터/버블맵이다
// (BERTopic의 visualize_documents(), pyLDAvis, TensorBoard Embedding Projector 등
// 전부 2D). 2D는 SVG viewBox 하나로 "내용에 맞춰 펼치기"가 끝나서, 3D 카메라 관련
// 버그(초기 크기, 중앙 정렬, 흔들림)가 애초에 생길 여지가 없다 — zoomToFit도
// ResizeObserver도 필요 없이 뷰박스만 계산하면 항상 정확히 맞춰짐.
// 3D 버전(ForceGraph3D 기반 renderOverviewGraph/renderCommentGraph 등)은 나중에
// 다시 쓸 수도 있어서 코드는 그대로 남겨뒀고, 지금은 이 2D 경로만 실제로 호출됨.
// 데이터의 실제 가로세로 비율과 넓은 컨테이너의 비율이 다르면(예: 세로로 긴 데이터를
// 가로로 넓은 카드에 넣을 때) preserveAspectRatio="meet"가 남는 쪽을 그냥 빈 여백으로
// 남겨버려서 "이렇게 넓은데 왜 안 채우냐"는 느낌을 줌. 데이터를 늘리거나 찌그러뜨리지
// 않고(그러면 상대 거리가 왜곡됨), 부족한 축의 여백만 컨테이너 비율만큼 균등하게 더 줘서
// 렌더 영역을 실제로 채움 — 중심은 그대로 유지되므로 클러스터 배치 자체는 안 변함.
// 다만 컨테이너 비율을 100% 그대로 따라가면(예: 2.5:1처럼 아주 넓은 카드) 그 차이만큼
// 빈 여백이 늘어나 데이터가 오히려 더 작고 밀집돼 보이는 역효과가 남 — 그래서 목표 비율을
// 데이터 자체 비율의 ±60% 안으로 캡을 씌워서, 공간은 최대한 쓰되 밀도가 과하게 희석되지
// 않게 함(균등 스케일이라 클러스터 간 상대 거리·구조는 전혀 안 바뀜)
const containerAspect = ref(1.6)
function computeViewBox(nodes: { x2d?: number; y2d?: number }[], padding = 30): string {
  const pts = nodes.filter((n): n is { x2d: number; y2d: number } => n.x2d != null && n.y2d != null)
  if (!pts.length) return '-150 -150 300 300'
  const xs = pts.map(p => p.x2d), ys = pts.map(p => p.y2d)
  const minX = Math.min(...xs), maxX = Math.max(...xs)
  const minY = Math.min(...ys), maxY = Math.max(...ys)
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2
  let w = Math.max(maxX - minX, 1) + padding * 2
  let h = Math.max(maxY - minY, 1) + padding * 2
  const dataAspect = w / h
  const aspect = Math.min(Math.max(containerAspect.value, dataAspect / 1.6), dataAspect * 1.6)
  if (w / h < aspect) w = h * aspect
  else h = w / aspect
  return `${cx - w / 2} ${cy - h / 2} ${w} ${h}`
}

// 좋아요/댓글 수처럼 넓게 퍼진 값을 반지름으로 쓸 때, 이상치 하나가 화면을 다 잡아먹지
// 않도록 최소/최대를 clamp — sqrt 스케일 자체는 3D 버전의 nodeVal과 같은 원리.
// 예전 범위(5~28)는 화면에서 원이 "비눗방울"처럼 부풀어 보인다는 피드백이 있어서
// 최대치를 크게 줄이고(28→18) 최소치도 살짝 올려(5→7) 크기 편차를 좁혔음 —
// 댓글/좋아요 수 차이는 여전히 보이되, 큰 원 하나가 지도 전체를 지배하지 않게 함
function nodeRadius(count: number): number {
  return Math.min(18, Math.max(7, Math.sqrt(count + 1) * 0.71))
}

const overviewViewBox = computed(() => computeViewBox(overviewData.value?.nodes ?? []))
const commentViewBox = computed(() => computeViewBox(graphData.value?.nodes ?? []))

// 노드를 붙잡아 당겼다가 놓으면 원래(UMAP) 자리로 튕겨 돌아오는 상호작용 — 실제 위치는
// UMAP이 이미 확정했으니 계속 흔들리게 두진 않되(그건 이전에 "움직이지 마" 피드백이 있었음),
// 사용자가 직접 당길 때만 반응해서 "만질 수 있는 공간"이라는 느낌을 줌. 드래그 중인 노드가
// 있으면 그 노드의 좌표만 포인터 위치로 잠깐 덮어쓰고, 나머지는 항상 실제 좌표를 그대로 씀
const dragNode = ref<{ id: string; x: number; y: number } | null>(null)
// 잡아당긴 노드에 직접 연결된 이웃들도 스프링으로 이어진 것처럼 살짝 딸려오게 하는 보정값 —
// "선 하나로만 연결된 딱딱한 그래프"가 아니라 서로 당겨지는 네트워크처럼 느껴지게 함.
// 놓으면 이것도 비워지고, 이웃 노드는 (드래그 중이 아니므로) 기본 트랜지션을 타고 같이 튕겨 돌아감
const dragNeighborOffsets = ref<Map<string, { x: number; y: number }>>(new Map())

// 전체 지도를 옮기고(pan) 확대/축소(zoom)하는 카메라 상태 — 노드/엣지는 이 값 하나로 묶인
// <g transform>을 통해서만 화면에 그려지므로, 배경을 드래그하면 노드와 선이 항상 "한 덩어리"로
// 같이 움직인다(따로 노는 것처럼 보이는 문제가 여기서 생기지 않음). 노드 위 pointerdown은
// .stop으로 이 배경 pan 핸들러까지 전파되지 않게 막아서 "노드 드래그"와 "지도 이동"이 항상
// 분리됨 — 노드를 잡으면 그 노드만, 빈 공간을 잡으면 지도 전체가 움직임
const panX = ref(0)
const panY = ref(0)
const zoom = ref(1)
const sceneTransform = computed(() => `translate(${panX.value} ${panY.value}) scale(${zoom.value})`)
function resetView() {
  panX.value = 0
  panY.value = 0
  zoom.value = 1
}

function find(parent: Map<string, string>, x: string): string {
  let root = x
  while (parent.get(root) !== root) root = parent.get(root)!
  return root
}

// 노드들을 "서로 선으로 이어진 묶음(연결 요소)" 단위로 묶음 — 표준 union-find
function computeClusterRoots(nodeIds: string[], links: { source: string; target: string }[]): Map<string, string> {
  const parent = new Map<string, string>()
  for (const id of nodeIds) parent.set(id, id)
  for (const l of links) {
    if (!parent.has(l.source) || !parent.has(l.target)) continue
    const ra = find(parent, l.source), rb = find(parent, l.target)
    if (ra !== rb) parent.set(ra, rb)
  }
  const result = new Map<string, string>()
  for (const id of nodeIds) result.set(id, find(parent, id))
  return result
}

const clusterRoots = computed(() => {
  const isComment = !!selectedVideoId.value
  const nodes = isComment ? (graphData.value?.nodes ?? []) : (overviewData.value?.nodes ?? [])
  const links = isComment ? (graphData.value?.links ?? []) : (overviewData.value?.links ?? [])
  return computeClusterRoots(nodes.map(n => n.id), links)
})

// 개요 지도 전용 — 클러스터 크기(그룹이 클수록 먼저)와, 정렬에도 재사용할 연결 수(중심성)를
// 한 번에 계산해둠. 감정 정보는 이미 오른쪽 리스트/상세 패널에서 충분히 보여주고 있어서,
// 이 지도의 핵심 질문("어떤 영상들이 비슷한 반응 구조로 묶이는가")에 맞춰 색은 감정 대신
// 이 그룹(클러스터) 기준으로 씀 — 감정은 작은 보조 점(sentiment badge)으로만 남김
const overviewClusterInfo = computed(() => {
  const roots = clusterRoots.value
  const sizes = new Map<string, number>()
  const degree = new Map<string, number>()
  for (const n of overviewData.value?.nodes ?? []) {
    const r = roots.get(n.id) ?? n.id
    sizes.set(r, (sizes.get(r) ?? 0) + 1)
  }
  for (const l of overviewData.value?.links ?? []) {
    degree.set(l.source, (degree.get(l.source) ?? 0) + 1)
    degree.set(l.target, (degree.get(l.target) ?? 0) + 1)
  }
  // 팔레트 색은 2개 이상 묶인 진짜 그룹에만 배정 — 고립 노드까지 색을 배정하면 팔레트가
  // 금방 돌아가며 "묶여 있다"는 착각을 줌. 고립 노드는 무채색으로 남김
  const rankedRoots = [...sizes.entries()]
    .filter(([, size]) => size >= 2)
    .sort((a, b) => b[1] - a[1])
    .map(([root]) => root)
  const rank = new Map<string, number>()
  rankedRoots.forEach((root, i) => rank.set(root, i))
  return { sizes, degree, rank }
})

const CLUSTER_NEUTRAL_LIGHT = '#B7B2A9'
const CLUSTER_NEUTRAL_DARK = '#726C61'
function clusterColor(id: string): string {
  const root = clusterRoots.value.get(id) ?? id
  const { sizes, rank } = overviewClusterInfo.value
  if ((sizes.get(root) ?? 1) < 2) return settings.theme === 'dark' ? CLUSTER_NEUTRAL_DARK : CLUSTER_NEUTRAL_LIGHT
  const r = rank.get(root) ?? 0
  return TOPIC_PALETTE.value[r % TOPIC_PALETTE.value.length] ?? '#888'
}

// 대시보드는 값을 정확히 읽을 수 있어야 하므로, 드래그/스냅백 중이 아닌 노드는 항상
// UMAP이 확정한 좌표 그대로를 반환 — 좌표가 저절로 계속 움직이면 "지금 이 위치가 뭘
// 뜻하는지" 매 순간 달라 보여서 지도를 안정적인 공간으로 신뢰하기 어려워짐
function effectivePos(n: { id: string; x2d?: number; y2d?: number }): { x: number; y: number } | null {
  if (dragNode.value && dragNode.value.id === n.id) return { x: dragNode.value.x, y: dragNode.value.y }
  if (n.x2d == null || n.y2d == null) return null
  const off = dragNeighborOffsets.value.get(n.id)
  if (off) return { x: n.x2d + off.x, y: n.y2d + off.y }
  return { x: n.x2d, y: n.y2d }
}

// 화면 픽셀 좌표를 SVG 내부 좌표(viewBox 기준)로 정확히 변환 — viewBox와 실제 렌더 크기의
// 배율을 직접 계산하지 않고 getScreenCTM()의 역행렬을 쓰면 preserveAspectRatio로 생기는
// letterboxing까지 포함해 항상 정확함
const svgEl = ref<SVGSVGElement | null>(null)
function toSvgPoint(clientX: number, clientY: number): { x: number; y: number } | null {
  const svg = svgEl.value
  if (!svg) return null
  const ctm = svg.getScreenCTM()
  if (!ctm) return null
  const pt = svg.createSVGPoint()
  pt.x = clientX
  pt.y = clientY
  const p = pt.matrixTransform(ctm.inverse())
  return { x: p.x, y: p.y }
}

let dragStartPointer: { x: number; y: number } | null = null
let dragOrigin: { x: number; y: number } | null = null
let dragMoved = false
// 클릭과 드래그가 같은 pointerdown/up 시퀀스에서 시작되므로, 드래그가 실제로 있었으면
// 뒤이어 오는 click 이벤트(selectNode 호출)를 한 번 무시해서 "당겼는데 패널이 열리는" 걸 막음
let suppressNextClick = false

function startNodeDrag(nodeId: string, x2d: number, y2d: number, event: PointerEvent) {
  const p = toSvgPoint(event.clientX, event.clientY)
  if (!p) return
  dragStartPointer = p
  dragOrigin = { x: x2d, y: y2d }
  dragMoved = false
  dragNode.value = { id: nodeId, x: x2d, y: y2d }
  window.addEventListener('pointermove', onNodeDragMove)
  window.addEventListener('pointerup', endNodeDrag)
}

function onNodeDragMove(event: PointerEvent) {
  if (!dragNode.value || !dragStartPointer || !dragOrigin) return
  const p = toSvgPoint(event.clientX, event.clientY)
  if (!p) return
  const dx = p.x - dragStartPointer.x
  const dy = p.y - dragStartPointer.y
  if (Math.abs(dx) > 2 || Math.abs(dy) > 2) dragMoved = true
  const id = dragNode.value.id
  dragNode.value = { id, x: dragOrigin.x + dx, y: dragOrigin.y + dy }

  // 직접 연결된 이웃만 유사도에 비례해서 살짝 딸려오게(최대 35%) — 물리 시뮬레이션을
  // 새로 돌리는 대신, 지금 있는 링크 데이터로 그 느낌만 값싸게 흉내냄
  const links = selectedVideoId.value ? (graphData.value?.links ?? []) : (overviewData.value?.links ?? [])
  const offsets = new Map<string, { x: number; y: number }>()
  for (const l of links) {
    const otherId = l.source === id ? l.target : l.target === id ? l.source : null
    if (!otherId) continue
    const factor = Math.min(0.35, l.similarity * 0.4)
    offsets.set(otherId, { x: dx * factor, y: dy * factor })
  }
  dragNeighborOffsets.value = offsets
}

// 드래그가 끝난 직후 짧게만 cx/cy(및 대응하는 선의 x1/y1/x2/y2) 트랜지션을 걸어
// 원위치로 "튕겨" 돌아가 보이게 함 — 평소엔 이 트랜지션이 없어야 드래그 중 좌표 변경이
// 지연 없이 그대로 반영됨
const snappingIds = ref<Set<string>>(new Set())

function endNodeDrag() {
  window.removeEventListener('pointermove', onNodeDragMove)
  window.removeEventListener('pointerup', endNodeDrag)
  suppressNextClick = dragMoved
  if (dragNode.value) {
    snappingIds.value = new Set([dragNode.value.id, ...dragNeighborOffsets.value.keys()])
    setTimeout(() => { snappingIds.value = new Set() }, 550)
  }
  dragNode.value = null
  dragNeighborOffsets.value = new Map()
  dragStartPointer = null
  dragOrigin = null
}

// ── 배경(빈 공간) 드래그 = 지도 전체 이동(pan) ──
// 노드 위 pointerdown은 @pointerdown.stop으로 여기까지 전파되지 않으므로, 이 핸들러는
// 항상 "노드가 아닌 곳"을 잡았을 때만 실행된다 — Explore 모드(지도 이동)와 노드 드래그
// 모드가 이벤트 전파만으로 자연스럽게 분리됨
const isPanning = ref(false)
let panStartPointer: { x: number; y: number } | null = null
let panOrigin: { x: number; y: number } | null = null
let panMoved = false

function startBackgroundPan(event: PointerEvent) {
  const p = toSvgPoint(event.clientX, event.clientY)
  if (!p) return
  panStartPointer = p
  panOrigin = { x: panX.value, y: panY.value }
  panMoved = false
  isPanning.value = true
  window.addEventListener('pointermove', onBackgroundPanMove)
  window.addEventListener('pointerup', endBackgroundPan)
}

function onBackgroundPanMove(event: PointerEvent) {
  if (!panStartPointer || !panOrigin) return
  const p = toSvgPoint(event.clientX, event.clientY)
  if (!p) return
  const dx = p.x - panStartPointer.x
  const dy = p.y - panStartPointer.y
  if (Math.abs(dx) > 2 || Math.abs(dy) > 2) panMoved = true
  panX.value = panOrigin.x + dx
  panY.value = panOrigin.y + dy
}

function endBackgroundPan() {
  window.removeEventListener('pointermove', onBackgroundPanMove)
  window.removeEventListener('pointerup', endBackgroundPan)
  // 실제로 지도를 옮겼다면 뒤이어 오는 click(=closePanel)을 한 번 무시 —
  // 안 그러면 패널을 보며 지도를 옮기려 할 때마다 패널이 닫혀버림
  if (panMoved) suppressNextClick = true
  isPanning.value = false
  panStartPointer = null
  panOrigin = null
}

// 휠 확대/축소 — 커서 아래의 "월드" 좌표가 확대 후에도 같은 화면 위치에 남도록 pan을 보정
// (transform이 translate(pan) scale(zoom) 순서라 world*zoom+pan = 화면좌표라는 관계를 이용)
function onWheelZoom(event: WheelEvent) {
  event.preventDefault()
  const p = toSvgPoint(event.clientX, event.clientY)
  if (!p) return
  const factor = event.deltaY < 0 ? 1.15 : 1 / 1.15
  const nextZoom = Math.min(4, Math.max(0.5, zoom.value * factor))
  const worldX = (p.x - panX.value) / zoom.value
  const worldY = (p.y - panY.value) / zoom.value
  panX.value = p.x - worldX * nextZoom
  panY.value = p.y - worldY * nextZoom
  zoom.value = nextZoom
}

// 색은 항상 그대로 유지 — 강조는 색을 바꾸는 대신 크기(15%)와 테두리(템플릿에서
// selectedNodeId/hoveredNodeId 참조)로만 표현해서 기본 화면은 차분하게, 선택 시에만 또렷하게 함
const overviewNodePositions = computed(() =>
  (overviewData.value?.nodes ?? [])
    .map(n => ({ node: n, pos: effectivePos(n) }))
    .filter((p): p is { node: VideoGraphNode; pos: { x: number; y: number } } => p.pos != null)
    .map(({ node: n, pos }) => {
      const r = nodeRadius(n.commentCount ?? 0) * emphasisScale(n.id)
      return {
        node: n,
        x: pos.x,
        y: pos.y,
        r,
        color: clusterColor(n.id),
        // 감정은 메인 색에서 뺀 대신, 노드 모서리에 작은 보조 점으로 남겨둠(오른쪽 목록/
        // 상세 패널에 이미 자세히 있으니 여기선 참고용 신호 정도로만)
        badgeX: pos.x + r * 0.68,
        badgeY: pos.y - r * 0.68,
        badgeColor: sentimentColor(n.sentiment),
      }
    })
)

const commentNodePositions = computed(() =>
  (graphData.value?.nodes ?? [])
    .map(n => ({ node: n, pos: effectivePos(n) }))
    .filter((p): p is { node: CommentGraphNode; pos: { x: number; y: number } } => p.pos != null)
    .map(({ node: n, pos }) => ({
      node: n,
      x: pos.x,
      y: pos.y,
      r: nodeRadius(n.likeCount ?? 0) * emphasisScale(n.id),
      color: topicColor(n.topic),
    }))
)

type LinkPos = {
  key: string; source: string; target: string; similarity: number
  x1: number; y1: number; x2: number; y2: number; opacity: number; width: number
}

function resolveLinkPositions(
  nodes: { id: string; x2d?: number; y2d?: number }[],
  links: { source: string; target: string; similarity: number }[],
): LinkPos[] {
  const byId = new Map(nodes.map(n => [n.id, n]))
  const result: LinkPos[] = []
  for (const l of links) {
    const s = byId.get(l.source), t = byId.get(l.target)
    if (!s || !t) continue
    // effectivePos를 써야 드래그 중인 노드에 붙은 선이 손가락을 따라 함께 늘어남
    const sp = effectivePos(s), tp = effectivePos(t)
    if (!sp || !tp) continue
    result.push({
      key: `${l.source}-${l.target}`, source: l.source, target: l.target, similarity: l.similarity,
      x1: sp.x, y1: sp.y, x2: tp.x, y2: tp.y,
      opacity: linkAlpha(l.similarity), width: linkWidth(l.similarity),
    })
  }
  return result
}

const overviewLinkPositions = computed(() =>
  resolveLinkPositions(overviewData.value?.nodes ?? [], overviewData.value?.links ?? [])
)
const commentLinkPositions = computed(() =>
  resolveLinkPositions(graphData.value?.nodes ?? [], graphData.value?.links ?? [])
)

// 선을 클릭하기 전, 호버만 해도 살짝 진해지도록 — 실제 클릭 타겟인 두꺼운 히트 라인 쪽에서 갱신
const hoveredEdgeKey = ref<string | null>(null)
// 선택되거나 호버된 노드에 직접 연결된 선인지 — 이 경우엔 실제 유사도가 낮아 원래는 흐릴
// 선이어도 "왜 연결됐는지 보라"는 게 지금 목적이므로 강도를 유사도값과 무관하게 확실히
// 올려서 보여줌. 댓글 지도는 기본 선이 거의 안 보이므로(linkAlpha 0.06), 호버만으로도
// 연결이 드러나야 "이 댓글이 뭐랑 이어져 있는지" 클릭 없이 바로 확인할 수 있음
function isEdgeFocused(l: { source: string; target: string }): boolean {
  if (selectedNodeId.value) return l.source === selectedNodeId.value || l.target === selectedNodeId.value
  if (hoveredNodeId.value) return l.source === hoveredNodeId.value || l.target === hoveredNodeId.value
  if (selectedEdge.value) return isEdgeSelected(l)
  return false
}

// 클릭했을 때 선 색이 T1 red로 확 바뀌니 "안 어울린다"는 피드백 — T1 red는 노드 선택
// 표시(테두리)에만 남기고, 선은 색 자체를 바꾸지 않고 항상 같은 선 색 계열을 더 진하게만 씀.
// 포커스됐을 때도 유사도가 높을수록 더 진하게 남겨서, 여러 개가 한꺼번에 강조돼도
// 그중 어떤 연결이 더 강한지 여전히 구분됨
const EDGE_BASE_RGB = '201, 191, 174' // #C9BFAE — 배경(#f7f6f4 / #121110)과 확실히 구분되는 톤
function focusedEdgeAlpha(similarity: number): number {
  return Math.min(0.9, Math.max(0.75, 0.75 + similarity * 0.2))
}
function edgeStroke(l: LinkPos): string {
  if (isEdgeSelected(l)) return `rgba(${EDGE_BASE_RGB}, 0.9)`
  if (isEdgeFocused(l)) return `rgba(${EDGE_BASE_RGB}, ${focusedEdgeAlpha(l.similarity)})`
  const a = hoveredEdgeKey.value === l.key ? 0.85 : l.opacity
  return `rgba(${EDGE_BASE_RGB}, ${a})`
}
function edgeStrokeWidth(l: LinkPos): number {
  if (isEdgeSelected(l)) return 3
  if (isEdgeFocused(l)) return 2.2 + focusedEdgeAlpha(l.similarity) * 0.8
  return hoveredEdgeKey.value === l.key ? 2.6 : l.width
}

// 댓글 지도의 토픽 라벨 — 실제 2D 좌표 평균(centroid)에 SVG 텍스트로 띄움.
// centroid 그대로 쓰면 글자가 노드 뭉치 한가운데 겹쳐서 지저분해지므로 위로 살짝 띄움
// (3D 버전의 sprite y+55 오프셋과 같은 목적). 토픽이 많으면 라벨이 다 겹쳐 화면이
// 지저분해지므로, 노드 수가 가장 많은 상위 3개 토픽만 라벨을 보여줌
const commentTopicCentroids2D = computed(() => {
  const sums: Record<string, { x: number; y: number; n: number }> = {}
  for (const node of graphData.value?.nodes ?? []) {
    if (node.x2d == null) continue
    const s = sums[node.topic] ?? (sums[node.topic] = { x: 0, y: 0, n: 0 })
    s.x += node.x2d
    s.y += node.y2d ?? 0
    s.n += 1
  }
  return Object.entries(sums)
    .map(([topic, s]) => ({ topic, x: s.x / s.n, y: s.y / s.n - 22, n: s.n }))
    .sort((a, b) => b.n - a.n)
    .slice(0, 3)
})

// 연결된 영상 목록 — 그냥 유사도 %만 보여주면 "왜" 연결됐는지 알 수 없다는 피드백이 있어서,
// 공통 토픽을 함께 보여줘서 줄(엣지)을 따로 클릭하지 않아도 관계가 바로 읽히게 함
const videoNeighbors = computed<NeighborInfo[]>(() => {
  if (!panelVideo.value || !overviewData.value) return []
  const id = panelVideo.value.id
  const myTopics = panelVideo.value.topics
  return overviewData.value.links
    .filter(l => l.source === id || l.target === id)
    .map(l => {
      const otherId = l.source === id ? l.target : l.source
      const other = overviewData.value!.nodes.find(n => n.id === otherId)
      const commonTopics = other ? myTopics.filter(t => other.topics.includes(t)) : []
      return { id: otherId, label: other?.title ?? otherId, similarity: l.similarity, commonTopics }
    })
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, 5)
})

const commentNeighbors = computed<NeighborInfo[]>(() => {
  if (!panelComment.value || !graphData.value) return []
  const id = panelComment.value.id
  return graphData.value.links
    .filter(l => l.source === id || l.target === id)
    .map(l => {
      const otherId = l.source === id ? l.target : l.source
      const other = graphData.value!.nodes.find(n => n.id === otherId)
      return { id: otherId, label: other?.text ?? otherId, similarity: l.similarity }
    })
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, 5)
})

// 엣지(선) 클릭 시 "왜 연결됐는지" 보여주는 카드용 데이터 — 지금까지는 선이 그냥 장식처럼
// 보인다는 피드백이 있어서, 실제로 무슨 유사도 계산 결과인지 직접 확인할 수 있게 함
type EdgeInfo = {
  labelA: string
  labelB: string
  similarity: number
  isComment: boolean
  topicsA?: string[]
  topicsB?: string[]
  commonTopics?: string[]
}

const selectedEdgeInfo = computed<EdgeInfo | null>(() => {
  const e = selectedEdge.value
  if (!e) return null

  if (selectedVideoId.value) {
    const nodes = graphData.value?.nodes ?? []
    const a = nodes.find(n => n.id === e.source)
    const b = nodes.find(n => n.id === e.target)
    if (!a || !b) return null
    return { labelA: a.text, labelB: b.text, similarity: e.similarity, isComment: true }
  }

  const nodes = overviewData.value?.nodes ?? []
  const a = nodes.find(n => n.id === e.source)
  const b = nodes.find(n => n.id === e.target)
  if (!a || !b) return null
  const commonTopics = a.topics.filter(t => b.topics.includes(t))
  return {
    labelA: a.title, labelB: b.title, similarity: e.similarity, isComment: false,
    topicsA: a.topics, topicsB: b.topics, commonTopics,
  }
})

// "왜 연결됐는지" 한 문장 — 공통 토픽 유무에 따라 다른 문구를 씀. 엣지 클릭 카드와
// 옆 패널의 "비슷한 반응의 영상" 목록이 둘 다 이 로직을 그대로 재사용함
function neighborReasonText(commonTopics: string[] | undefined): string {
  if (commonTopics && commonTopics.length) {
    return M.value.networkEdgeReasonTopic.replace('{topics}', commonTopics.join(', '))
  }
  return M.value.networkEdgeReasonNoTopic
}

const edgeReasonText = computed(() => {
  const info = selectedEdgeInfo.value
  if (!info) return ''
  if (info.isComment) return M.value.networkEdgeReasonComment
  return neighborReasonText(info.commonTopics)
})

// 같은 노드를 여러 번 클릭해도 매번 다시 불러오지 않게 캐시
const videoDetailCache = new Map<string, InsightData>()

// 분석일자·토픽·인사이트는 패널에서 더 이상 안 보여주지만(영상 분석 페이지에 이미 있음),
// 댓글 반응 지도로 넘어갈 때 쓰는 실제 토픽 개수(videoTopics)를 위해 캐시는 미리 데워둠
async function openVideoPanel(node: VideoGraphNode) {
  panelComment.value = null
  panelVideo.value = node
  if (videoDetailCache.has(node.id)) return
  try {
    const detail = await insightApi.getByVideoId(node.id)
    videoDetailCache.set(node.id, detail)
  } catch { /* 댓글 반응 지도 진입 시 재시도됨 */ }
}

function openCommentPanel(node: CommentGraphNode) {
  panelVideo.value = null
  panelComment.value = node
}

// 패널을 닫고 노드/엣지 선택도 해제
function closePanel() {
  panelVideo.value = null
  panelComment.value = null
  selectedNodeId.value = null
  selectedEdge.value = null
}

// 노드를 클릭했을 때: 이미 선택된 노드를 다시 클릭하면 선택 해제(목록으로),
// 아니면 그 노드를 선택하고 패널을 상세로 전환
function selectNode(node: VideoGraphNode | CommentGraphNode, isComment: boolean) {
  if (suppressNextClick) {
    suppressNextClick = false
    return
  }
  if (selectedNodeId.value === node.id) {
    closePanel()
    return
  }
  panelVideo.value = null
  panelComment.value = null
  selectedEdge.value = null
  selectedNodeId.value = node.id
  if (isComment) openCommentPanel(node as CommentGraphNode)
  else openVideoPanel(node as VideoGraphNode)
}

// 선(엣지)을 클릭했을 때 — 노드 상세와 달리 목록을 가리지 않고, 목록 위에 작은
// "연결 분석" 카드로 얹음(패널이 이미 320px로 좁은데 엣지 정보는 훨씬 가벼우니
// 노드 클릭처럼 전체를 대체할 필요가 없음). 두 끝 노드는 emphasisScale/nodeFocusOpacity가
// selectedEdge를 직접 참조해서 함께 강조됨
type SelectedEdge = { source: string; target: string; similarity: number }
const selectedEdge = ref<SelectedEdge | null>(null)

function selectEdge(link: SelectedEdge) {
  if (selectedEdge.value && selectedEdge.value.source === link.source && selectedEdge.value.target === link.target) {
    closePanel()
    return
  }
  panelVideo.value = null
  panelComment.value = null
  selectedNodeId.value = null
  selectedEdge.value = link
}

function thumbUrl(videoId: string) {
  return `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`
}

function formatAnalyzedAt(iso?: string): string {
  if (!iso) return ''
  const loc = settings.lang === 'ko' ? 'ko-KR' : settings.lang === 'zh' ? 'zh-CN' : settings.lang === 'ja' ? 'ja-JP' : 'en-US'
  return new Date(iso).toLocaleString(loc, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// HistoryView.vue의 fmtComments와 같은 패턴 — 목록이 제목만 쭉 나열돼 있으면 "관리자
// 페이지 초안" 같다는 피드백이 있어서, 감정 점 + 댓글 수/긍정률 메타 한 줄을 덧붙임
function fmtComments(n: number): string {
  const s = n.toLocaleString()
  if (settings.lang === 'en') return `${s} comments`
  if (settings.lang === 'zh') return `${s} 条评论`
  if (settings.lang === 'ja') return `${s} 件のコメント`
  return `댓글 ${s}개`
}

// 개요 지도의 영상 중 댓글 반응 지도(2단계)가 아직 없는 것(옛날 분석분/생성 실패)을
// 목록에서 분리해서 보여주고, 그 자리에서 바로 재분석할 수 있게 함
const availableVideos = computed(() => (overviewData.value?.nodes ?? []).filter(n => n.hasGraph))
const unavailableVideos = computed(() => (overviewData.value?.nodes ?? []).filter(n => !n.hasGraph))

// 정렬 — 이 화면의 핵심은 감정 랭킹이 아니라 반응 네트워크라서, 기본값은 지도에서 같이
// 묶이는 유사도 그룹 순서로 둠(리스트가 지도 구조를 그대로 따라가게). 그룹은 큰 순서,
// 그룹 안에서는 댓글 수(반응 규모) 많은 순 → 연결 수(중심성) 많은 순으로 동률을 가름
type SortMode = 'cluster' | 'comments' | 'positive' | 'negative' | 'newest'
const sortMode = ref<SortMode>('cluster')
const sortDropdownOpen = ref(false)
function onSortClickOutside(e: MouseEvent) {
  const el = document.querySelector('.sort-dropdown')
  if (el && !el.contains(e.target as Node)) sortDropdownOpen.value = false
}
const SORT_OPTIONS = computed(() => [
  { key: 'cluster' as SortMode, label: M.value.networkSortCluster },
  { key: 'comments' as SortMode, label: M.value.networkSortComments },
  { key: 'positive' as SortMode, label: M.value.networkSortPositive },
  { key: 'negative' as SortMode, label: M.value.networkSortNegative },
  { key: 'newest' as SortMode, label: M.value.networkSortNewest },
])

const sortedAvailableVideos = computed(() => {
  const nodes = [...availableVideos.value]
  if (sortMode.value === 'newest') return nodes
  if (sortMode.value === 'comments') return nodes.sort((a, b) => (b.commentCount ?? 0) - (a.commentCount ?? 0))
  if (sortMode.value === 'positive') return nodes.sort((a, b) => b.sentiment.positive - a.sentiment.positive)
  if (sortMode.value === 'negative') return nodes.sort((a, b) => b.sentiment.negative - a.sentiment.negative)
  const roots = clusterRoots.value
  const { sizes, degree } = overviewClusterInfo.value
  return nodes.sort((a, b) => {
    const ra = roots.get(a.id) ?? a.id, rb = roots.get(b.id) ?? b.id
    const sizeDiff = (sizes.get(rb) ?? 1) - (sizes.get(ra) ?? 1)
    if (sizeDiff !== 0) return sizeDiff
    // 같은 크기의 서로 다른 그룹은 root id로 묶어서 서로 섞이지 않고 인접 배치되게 함
    if (ra !== rb) return ra.localeCompare(rb)
    const commentDiff = (b.commentCount ?? 0) - (a.commentCount ?? 0)
    if (commentDiff !== 0) return commentDiff
    return (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0)
  })
})

// 그룹순 정렬일 때, 목록에서 그룹이 바뀌는 경계마다 얇은 구분선을 넣어서 "여기까지 한
// 그룹"이라는 게 눈에 보이게 함 — 다른 정렬 모드에서는 그룹 개념이 없으니 항상 빈 Set
const videoGroupBreakIds = computed(() => {
  const breaks = new Set<string>()
  if (sortMode.value !== 'cluster') return breaks
  const roots = clusterRoots.value
  const list = sortedAvailableVideos.value
  for (let i = 1; i < list.length; i++) {
    const prevItem = list[i - 1], curItem = list[i]
    if (!prevItem || !curItem) continue
    const prevRoot = roots.get(prevItem.id) ?? prevItem.id
    const curRoot = roots.get(curItem.id) ?? curItem.id
    if (prevRoot !== curRoot) breaks.add(curItem.id)
  }
  return breaks
})

const legendLines = computed(() =>
  (selectedVideoId.value ? M.value.networkLegendDetail : M.value.networkLegendOverview).split(' · ')
)

// 산문 설명 박스 대신 실제 처리 단계를 순서대로 보여주는 파이프라인 스트립용 데이터
const pipelineSteps = computed(() => [
  { title: M.value.networkPipeline1Title, sub: M.value.networkPipeline1Sub },
  { title: M.value.networkPipeline2Title, sub: M.value.networkPipeline2Sub },
  { title: M.value.networkPipeline3Title, sub: M.value.networkPipeline3Sub },
  { title: M.value.networkPipeline4Title, sub: M.value.networkPipeline4Sub },
  { title: M.value.networkPipeline5Title, sub: M.value.networkPipeline5Sub },
])

async function loadOverview() {
  isLoadingOverview.value = true
  overviewErrorDetail.value = ''
  overviewErrorGeneric.value = false
  try {
    // 2D는 overviewData가 바뀌면 템플릿의 computed(overviewNodePositions 등)가 알아서
    // 다시 그리므로, 3D 때와 달리 별도의 명령형 렌더 호출이 필요 없음
    overviewData.value = await insightApi.getVideoGraph()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (detail) overviewErrorDetail.value = detail
    else overviewErrorGeneric.value = true
  } finally {
    isLoadingOverview.value = false
  }
}

// 썸네일 클릭 — 토픽/인사이트는 이미 영상 분석(히스토리) 페이지에 있으므로 여기서
// 중복해서 보여주는 대신, 클릭하면 바로 그 페이지로 이동시킴
function goToVideoAnalysis(videoId: string) {
  router.push({ name: 'history-view', query: { id: videoId } })
}

function selectVideo(videoId: string, title: string) {
  closePanel()
  selectedVideoTitle.value = title
  selectedVideoThumbnail.value = thumbUrl(videoId)
  router.replace({ query: { videoId } })
}

async function loadVideoGraph(videoId: string) {
  closePanel()
  selectedTopicFilter.value = null
  graphData.value = null
  videoTopics.value = []
  graphError.value = ''
  isLoadingGraph.value = true
  try {
    // 2D는 graphData가 바뀌면 computed(commentNodePositions 등)가 알아서 다시 그림
    graphData.value = await insightApi.getGraph(videoId)
  } catch (e: any) {
    graphError.value = e?.response?.status === 404 ? '404' : 'other'
  } finally {
    isLoadingGraph.value = false
  }

  // 토픽별 실제 분류 개수(mentionCount)는 그래프 캡핑과 무관한 값이라 별도로 가져옴 —
  // 실패해도 목록 자체는 이미 떴으니 조용히 무시(그러면 캡핑된 개수로 폴백됨)
  const cached = videoDetailCache.get(videoId)
  if (cached) {
    videoTopics.value = cached.topics
  } else {
    try {
      const detail = await insightApi.getByVideoId(videoId)
      videoDetailCache.set(videoId, detail)
      if (selectedVideoId.value === videoId) videoTopics.value = detail.topics
    } catch { /* 폴백: topicGroups가 캡핑된 개수를 씀 */ }
  }
}

function backToOverview() {
  closePanel()
  router.replace({ query: {} })
}

// selectedVideoId(= route.query.videoId)가 바뀔 때마다 여기서만 실제 로딩/렌더링을 함 —
// selectVideo/backToOverview는 라우터만 바꾸고, 이 watch가 유일하게 반응하게 해서
// "클릭해도 상태가 이미 같아서 아무 일도 안 일어나는" 경쟁 상태를 없앰
watch(selectedVideoId, (videoId) => {
  resetView()
  if (videoId) {
    loadVideoGraph(videoId)
  } else {
    closePanel()
  }
}, { immediate: true })

let containerResizeObserver: ResizeObserver | null = null

onMounted(async () => {
  await loadOverview()
  document.addEventListener('mousedown', onSortClickOutside)
  if (graphContainer.value) {
    containerResizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (!entry) return
      const { width, height } = entry.contentRect
      if (width > 0 && height > 0) containerAspect.value = width / height
    })
    containerResizeObserver.observe(graphContainer.value)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onNodeDragMove)
  window.removeEventListener('pointerup', endNodeDrag)
  window.removeEventListener('pointermove', onBackgroundPanMove)
  window.removeEventListener('pointerup', endBackgroundPan)
  document.removeEventListener('mousedown', onSortClickOutside)
  containerResizeObserver?.disconnect()
})

async function reanalyze(videoId: string) {
  const rebuiltUrl = `https://www.youtube.com/watch?v=${videoId}`
  await insightApi.deleteCache(videoId)
  analysisStore.submit(rebuiltUrl, (id, d) => useHistory().save(id, d))
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="net-page">
    <div class="cpage-header">
      <div class="header-title-row">
        <img v-if="selectedVideoId" :src="selectedVideoThumbnail" alt="" class="header-thumb" />
        <div>
          <p v-if="selectedVideoId" class="cpage-eyebrow">{{ M.navNetwork }}</p>
          <h1 class="cpage-title" :class="{ 'cpage-title--video': selectedVideoId }">
            {{ selectedVideoId ? selectedVideoTitle : M.navNetwork }}
          </h1>
          <p v-if="!selectedVideoId" class="cpage-sub">{{ M.networkSub }}</p>
        </div>
      </div>
      <div class="header-actions">
        <button v-if="selectedVideoId" class="back-btn" @click="backToOverview">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          {{ M.networkBack }}
        </button>
      </div>
    </div>

    <div class="cpage-body net-body">
      <!-- 개요(전체 영상) 로딩/에러 -->
      <p v-if="!selectedVideoId && isLoadingOverview" class="net-state">{{ M.loading }}</p>
      <p v-else-if="!selectedVideoId && overviewError" class="net-state net-state--error">{{ overviewError }}</p>
      <p v-else-if="!selectedVideoId && overviewData && overviewData.nodes.length === 0" class="net-state">{{ M.compareNone }}</p>

      <!-- 상세(댓글) 로딩/에러 -->
      <p v-else-if="selectedVideoId && isLoadingGraph" class="net-state">{{ M.loading }}</p>
      <div v-else-if="selectedVideoId && graphError === '404'" class="net-state net-state--error">
        <p>{{ M.networkNoGraph }}</p>
        <button class="net-reanalyze-btn" @click="reanalyze(selectedVideoId)">{{ M.networkReanalyzeBtn }}</button>
      </div>
      <p v-else-if="selectedVideoId && graphError === 'other'" class="net-state net-state--error">{{ M.backendError }}</p>

      <!-- 2D 그래프(개요/상세 공용) — SVG viewBox로 항상 내용에 맞춰 펼쳐지므로
           3D 때 겪었던 카메라/줌 관련 버그(초기 크기, 중앙 정렬)가 구조적으로 없음 -->
      <div v-show="!(isLoadingOverview || overviewError || isLoadingGraph || graphError)" class="net-graph-canvas-wrap">
        <div class="net-main-row">
          <div class="net-graph-canvas-inner" ref="graphContainer">
            <svg
              ref="svgEl"
              class="net-graph-canvas net-graph-svg"
              :class="{ 'net-graph-svg--panning': isPanning }"
              :viewBox="selectedVideoId ? commentViewBox : overviewViewBox"
              preserveAspectRatio="xMidYMid meet"
              @click="closePanel"
              @pointerdown="startBackgroundPan"
              @wheel="onWheelZoom"
            >
              <!-- 노드/엣지를 전부 이 <g> 하나로 묶어서 pan/zoom(sceneTransform) 값 하나만
                   바뀌면 지도 전체가 항상 한 덩어리로 같이 움직인다 — 배경을 드래그해도
                   노드와 선이 따로 노는 문제가 구조적으로 생기지 않음 -->
              <g :transform="sceneTransform">
              <template v-if="!selectedVideoId">
                <g
                  v-for="l in overviewLinkPositions" :key="l.key" class="net-svg-link"
                  :class="{ 'net-svg-link--snapping': snappingIds.has(l.source) || snappingIds.has(l.target) }"
                  :style="{ opacity: edgeFocusOpacity(l) }"
                  @click.stop="selectEdge(l)"
                >
                  <!-- 실제 눈에 보이는 얇은 선 -->
                  <line
                    :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
                    :stroke="edgeStroke(l)"
                    :stroke-width="edgeStrokeWidth(l)"
                  />
                  <!-- 클릭이 잘 되도록 눈에는 안 보이는 두꺼운 히트 영역(선 자체는 너무 얇아서 클릭하기 힘듦).
                       호버도 이 두꺼운 영역 기준으로 잡아야 가는 선 위에 정확히 커서를 올리지 않아도 반응함 -->
                  <line
                    :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2" stroke="transparent" stroke-width="14"
                    class="net-svg-link-hit"
                    @mouseenter="hoveredEdgeKey = l.key" @mouseleave="hoveredEdgeKey = null"
                  />
                </g>
                <circle
                  v-for="p in overviewNodePositions" :key="p.node.id"
                  :cx="p.x" :cy="p.y" :r="p.r" :fill="p.color"
                  :opacity="nodeFocusOpacity(p.node.id)"
                  :stroke="p.node.id === selectedNodeId ? 'var(--t1-red)' : (p.node.id === hoveredNodeId ? 'var(--text)' : undefined)"
                  :stroke-width="p.node.id === selectedNodeId ? 2.5 : (p.node.id === hoveredNodeId ? 1.5 : undefined)"
                  class="net-svg-node"
                  :class="{ 'net-svg-node--dragging': dragNode?.id === p.node.id, 'net-svg-node--snapping': snappingIds.has(p.node.id) }"
                  @mouseenter="hoveredNodeId = p.node.id" @mouseleave="hoveredNodeId = null"
                  @pointerdown.stop="startNodeDrag(p.node.id, p.x, p.y, $event)"
                  @click.stop="selectNode(p.node, false)"
                />
                <!-- 감정 보조 점 — 메인 색은 이제 클러스터를 나타내므로, 감정은 참고용으로만 작게 표시 -->
                <circle
                  v-for="p in overviewNodePositions" :key="`${p.node.id}-badge`"
                  :cx="p.badgeX" :cy="p.badgeY" r="3.2" :fill="p.badgeColor"
                  :opacity="nodeFocusOpacity(p.node.id)"
                  class="net-svg-sentiment-badge"
                />
              </template>
              <template v-else>
                <g
                  v-for="l in commentLinkPositions" :key="l.key" class="net-svg-link"
                  :class="{ 'net-svg-link--snapping': snappingIds.has(l.source) || snappingIds.has(l.target) }"
                  :style="{ opacity: edgeFocusOpacity(l) }"
                  @click.stop="selectEdge(l)"
                >
                  <!-- 댓글 지도는 기본적으로 선을 아예 숨김(토픽 클러스터 지도 느낌) — 흐릿하게
                       그려두면 "지워지다 만 실선"처럼 보인다는 피드백이 있어서, 낮은 opacity로
                       두는 대신 포커스(호버/선택)됐을 때만 실제로 그림 -->
                  <line
                    v-if="isEdgeFocused(l) || isEdgeSelected(l)"
                    :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
                    :stroke="edgeStroke(l)"
                    :stroke-width="edgeStrokeWidth(l)"
                  />
                  <line
                    :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2" stroke="transparent" stroke-width="14"
                    class="net-svg-link-hit"
                    @mouseenter="hoveredEdgeKey = l.key" @mouseleave="hoveredEdgeKey = null"
                  />
                </g>
                <circle
                  v-for="p in commentNodePositions" :key="p.node.id"
                  :cx="p.x" :cy="p.y" :r="p.r" :fill="p.color"
                  :opacity="nodeFocusOpacity(p.node.id)"
                  :stroke="p.node.id === selectedNodeId ? 'var(--t1-red)' : (p.node.id === hoveredNodeId ? 'var(--text)' : undefined)"
                  :stroke-width="p.node.id === selectedNodeId ? 2.5 : (p.node.id === hoveredNodeId ? 1.5 : undefined)"
                  class="net-svg-node"
                  :class="{ 'net-svg-node--dragging': dragNode?.id === p.node.id, 'net-svg-node--snapping': snappingIds.has(p.node.id) }"
                  @mouseenter="hoveredNodeId = p.node.id" @mouseleave="hoveredNodeId = null"
                  @pointerdown.stop="startNodeDrag(p.node.id, p.x, p.y, $event)"
                  @click.stop="selectNode(p.node, true)"
                />
                <text
                  v-for="c in commentTopicCentroids2D" :key="c.topic"
                  :x="c.x" :y="c.y" text-anchor="middle"
                  class="net-svg-label" :style="{ fill: topicColor(c.topic) }"
                >{{ c.topic }}</text>
              </template>
              </g>
            </svg>

            <!-- 지도를 옮기거나 확대/축소한 뒤에만 노출 — 원래 자동으로 맞춰진 상태(pan=0, zoom=1)로
                 되돌리는 용도라, 평소(건드리지 않았을 때)엔 화면을 어지럽히지 않게 숨김 -->
            <button v-if="panX !== 0 || panY !== 0 || zoom !== 1" class="net-reset-view-btn" @click="resetView">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="1 4 1 10 7 10"/>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
              </svg>
              {{ M.networkResetView }}
            </button>

            <!-- 범례 — 항상 보이는 고정 박스. 댓글 지도에선 토픽↔색 매핑도 같이 보여줌 -->
            <div class="net-legend-wrap">
              <div class="net-legend-panel">
                <!-- 그림(점/막대/스와치) 없이 텍스트만 세로로 나열 — 아이콘이 오히려 지저분해
                     보인다는 피드백 -->
                <p v-for="line in legendLines" :key="line" class="net-legend-text">{{ line }}</p>
              </div>
            </div>
          </div>

          <!-- 옆 패널 — 기본은 목록, 노드를 클릭하면 그 노드의 상세로 전환 (항상 마운트되어
               있어서 열고 닫아도 그래프 캔버스 폭이 바뀌지 않음) -->
          <div class="net-panel">
            <template v-if="!panelVideo && !panelComment">
              <!-- 엣지(선) 클릭 시 목록 위에 얹히는 "연결 분석" 카드 — 노드 클릭과 달리
                   목록을 대체하지 않고 그 위에 쌓임(정보량이 훨씬 가벼움) -->
              <!-- 닫기 버튼은 없앰 — 같은 선을 다시 클릭하거나 빈 공간을 클릭하면 어차피 닫힘 -->
              <div v-if="selectedEdgeInfo" class="net-edge-card">
                <p class="net-edge-card-title">{{ M.networkEdgeCardTitle }}</p>
                <p class="net-edge-card-pair">{{ selectedEdgeInfo.labelA }} ↔ {{ selectedEdgeInfo.labelB }}</p>
                <div class="net-edge-card-sim-row">
                  <span>Similarity</span>
                  <span class="net-edge-card-sim-value">{{ Math.round(selectedEdgeInfo.similarity * 100) }}%</span>
                </div>
                <div v-if="selectedEdgeInfo.commonTopics?.length" class="net-edge-card-topics">
                  <span v-for="t in selectedEdgeInfo.commonTopics" :key="t" class="topic-pill">{{ t }}</span>
                </div>
                <p class="net-edge-card-reason">{{ edgeReasonText }}</p>
              </div>

              <div class="net-list-header">
                <p class="net-list-title">
                  <button v-if="selectedVideoId && selectedTopicFilter" class="net-list-title-back" @click="selectedTopicFilter = null">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                  </button>
                  {{ selectedVideoId ? (selectedTopicFilter ?? M.topReactionTopics) : M.networkListVideos }}
                  <span class="net-list-count">{{ selectedVideoId ? (selectedTopicFilter ? filteredComments.length : topicGroups.length) : listNodes.length }}</span>
                </p>

                <!-- 정렬 — 이 화면의 핵심이 감정 랭킹이 아니라 반응 네트워크라서, 기본값은
                     지도에서 같이 묶이는 유사도 그룹 순서로 둠(리스트가 지도 구조를 그대로 따라가게) -->
                <div v-if="!selectedVideoId" class="sort-dropdown">
                  <button class="sort-trigger" @click="sortDropdownOpen = !sortDropdownOpen">
                    {{ SORT_OPTIONS.find(o => o.key === sortMode)?.label }}
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                      :style="{ transform: sortDropdownOpen ? 'rotate(180deg)' : 'none', transition: 'transform .18s' }">
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                  <div v-if="sortDropdownOpen" class="sort-menu">
                    <button
                      v-for="opt in SORT_OPTIONS"
                      :key="opt.key"
                      class="sort-option"
                      :class="{ active: sortMode === opt.key }"
                      @click="sortMode = opt.key; sortDropdownOpen = false"
                    >
                      <span class="sort-option-dot" v-if="sortMode === opt.key" />
                      {{ opt.label }}
                    </button>
                  </div>
                </div>
              </div>
              <p v-if="selectedVideoId && !selectedTopicFilter" class="net-list-note">{{ M.networkTopicSampleNote }}</p>
              <div class="net-list-scroll">
                <!-- 댓글 지도: 토픽 그룹 먼저 보여주고, 고르면 그 토픽 댓글만 필터링 -->
                <template v-if="selectedVideoId">
                  <template v-if="!selectedTopicFilter">
                    <button
                      v-for="g in topicGroups"
                      :key="g.topic"
                      class="net-list-item net-list-item--topic"
                      @click="selectedTopicFilter = selectedTopicFilter === g.topic ? null : g.topic"
                    >
                      <span class="net-list-item-row">
                        <span class="net-legend-dot" :style="{ background: topicColor(g.topic) }" />
                        <span class="net-list-item-label">{{ g.topic }}</span>
                        <span class="net-list-count">{{ g.count }} · {{ g.pct }}%</span>
                      </span>
                      <span class="net-list-item-bar">
                        <span class="net-list-item-bar-fill" :style="{ width: g.pct + '%', background: topicColor(g.topic) }" />
                      </span>
                    </button>
                  </template>
                  <template v-else>
                    <button
                      v-for="n in filteredComments"
                      :key="n.id"
                      :ref="(el) => setListItemRef(n.id, el)"
                      class="net-list-item"
                      :class="{ 'net-list-item--active': hoveredNodeId === n.id }"
                      @mouseenter="hoveredNodeId = n.id"
                      @mouseleave="hoveredNodeId = null"
                      @click="selectNode(n, true)"
                    >{{ n.text }}</button>
                  </template>
                </template>

                <!-- 영상 목록: 댓글 반응 지도가 있는 것 / 없는 것(옛날 분석·생성 실패)을 분리 -->
                <template v-else>
                  <template v-for="n in sortedAvailableVideos" :key="n.id">
                    <div v-if="videoGroupBreakIds.has(n.id)" class="net-list-group-break" />
                    <button
                      :ref="(el) => setListItemRef(n.id, el)"
                      class="net-list-item net-list-item--video"
                      :class="{ 'net-list-item--active': hoveredNodeId === n.id }"
                      @mouseenter="hoveredNodeId = n.id"
                      @mouseleave="hoveredNodeId = null"
                      @click="selectNode(n, false)"
                    >
                      <span class="net-list-item-dot" :style="{ background: clusterColor(n.id) }" />
                      <span class="net-list-item-body">
                        <span class="net-list-item-label">{{ listLabel(n) }}</span>
                        <span class="net-list-item-meta">{{ fmtComments(n.commentCount) }} · {{ M.positive }} {{ Math.round(n.sentiment.positive) }}%</span>
                      </span>
                    </button>
                  </template>

                  <template v-if="unavailableVideos.length">
                    <p class="net-list-divider">{{ M.networkListUnavailable }}</p>
                    <div
                      v-for="n in unavailableVideos"
                      :key="n.id"
                      :ref="(el) => setListItemRef(n.id, el)"
                      class="net-list-item net-list-item--unavailable"
                      :class="{ 'net-list-item--active': hoveredNodeId === n.id }"
                      @mouseenter="hoveredNodeId = n.id"
                      @mouseleave="hoveredNodeId = null"
                      @click="selectNode(n, false)"
                    >
                      <span class="net-list-item-label">{{ listLabel(n) }}</span>
                      <button class="net-list-reanalyze" @click.stop="reanalyze(n.id)">{{ M.networkReanalyzeBtn }}</button>
                    </div>
                  </template>
                </template>
              </div>
            </template>

            <!-- 뒤로가기 버튼은 없앴음 — 그래프 빈 공간을 클릭하면 어차피 closePanel이 호출돼서
                 목록으로 돌아가므로 굳이 중복된 버튼을 둘 필요가 없음 -->
            <template v-else-if="panelVideo">
              <div class="net-panel-scroll">
                <!-- 토픽/인사이트/분석일자는 이미 영상 분석 페이지에 있으므로 여기서 중복하지 않고,
                     썸네일을 누르면 바로 그 분석 페이지로 이동함 -->
                <button class="net-panel-header net-panel-header-btn" @click="goToVideoAnalysis(panelVideo.id)">
                  <div class="net-panel-thumb-wrap">
                    <img :src="thumbUrl(panelVideo.id)" alt="" class="net-panel-thumb-lg"
                      @error="($event.target as HTMLImageElement).style.opacity = '0'" />
                    <div class="net-panel-thumb-overlay">
                      <span class="net-panel-thumb-overlay-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                          <path d="M5 12h14M13 6l6 6-6 6"/>
                        </svg>
                        {{ M.networkThumbGoToHistory }}
                      </span>
                    </div>
                  </div>
                  <p class="net-panel-title">{{ panelVideo.title }}</p>
                </button>

                <button class="net-panel-cta" @click="selectVideo(panelVideo.id, panelVideo.title)">
                  {{ M.networkPanelViewCommentsBtn }}
                </button>

                <!-- 이 지도의 핵심 — 이 영상이 다른 영상과 왜/얼마나 비슷한 반응을 보였는지.
                     엣지를 따로 클릭하지 않아도 관계가 바로 이해되게 유사도%와 이유 문장을 함께 보여줌 -->
                <div v-if="videoNeighbors.length" class="net-panel-section net-panel-section--highlight">
                  <p class="net-panel-section-title">{{ M.networkPanelSimilarVideos }}</p>
                  <button v-for="nb in videoNeighbors" :key="nb.id" class="net-panel-neighbor net-panel-neighbor--rich" @click="selectVideo(nb.id, nb.label)">
                    <div class="net-panel-neighbor-row">
                      <span class="net-panel-neighbor-label">{{ nb.label }}</span>
                      <span class="net-panel-neighbor-sim">{{ Math.round(nb.similarity * 100) }}%</span>
                    </div>
                    <p class="net-panel-neighbor-reason">{{ neighborReasonText(nb.commonTopics) }}</p>
                  </button>
                </div>
              </div>
            </template>

            <template v-else-if="panelComment">
              <!-- 댓글 지도는 노드가 빽빽해서 빈 공간을 찾아 클릭하기 어려울 수 있으니(영상 지도와
                   달리) 여기는 뒤로가기를 남겨둠 — 목록 화면(.net-list-title)과 동일한 헤더 구조로 맞춰서
                   "목록으로 가는 버튼"이 아니라 "지금 보고 있는 토픽 제목"처럼 보이게 함 -->
              <p class="net-list-title">
                <button class="net-list-title-back" @click="closePanel">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                </button>
                {{ panelComment.topic }}
                <span class="net-list-count">{{ panelCommentTopicCount }}</span>
              </p>

              <div class="net-panel-scroll">
                <p class="net-panel-comment-text">{{ panelComment.text }}</p>
                <div class="net-panel-stats">
                  <span>{{ M.likesLabel }}</span>
                  <span class="net-panel-stat-value">{{ panelComment.likeCount }}</span>
                </div>

                <div v-if="commentNeighbors.length" class="net-panel-section net-panel-section--highlight">
                  <p class="net-panel-section-title">{{ M.networkPanelSimilarComments }}</p>
                  <div v-for="nb in commentNeighbors" :key="nb.id" class="net-panel-neighbor">
                    <span class="net-panel-neighbor-label">{{ nb.label }}</span>
                    <span class="net-panel-neighbor-sim">{{ Math.round(nb.similarity * 100) }}%</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 카드 5개를 나열하는 느낌 대신, 번호 붙인 한 줄짜리 얇은 프로세스 바로 정리 —
             설명(sub)은 늘 보이지 않고 title 툴팁(호버)으로만 확인 가능 -->
        <div class="net-pipeline">
          <span class="net-pipeline-title">{{ M.networkMethodTitle }}</span>
          <div class="net-pipeline-strip">
            <template v-for="(step, i) in pipelineSteps" :key="step.title">
              <span class="net-pipeline-step" :title="step.sub">
                <span class="net-pipeline-step-num">{{ String(i + 1).padStart(2, '0') }}</span>
                {{ step.title }}
              </span>
              <svg v-if="i < pipelineSteps.length - 1" class="net-pipeline-arrow" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 6 15 12 9 18"/>
              </svg>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.net-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

.cpage-header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
  position: sticky;
  top: 0;
  padding: 36px 40px 16px;
  z-index: 100;
  isolation: isolate;
  background: color-mix(in srgb, var(--bg) 65%, transparent);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 0.5px solid var(--border);
}
.cpage-title { font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.cpage-title--video {
  font-size: 16px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.cpage-eyebrow {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 3px;
}
.cpage-sub { font-size: 13px; color: var(--subtext); margin-top: 4px; }
.header-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; margin-left: auto; }

.header-title-row { display: flex; align-items: center; gap: 12px; }
.header-thumb {
  width: 64px;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 8px;
  border: 0.5px solid var(--border);
  flex-shrink: 0;
}

.back-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 600;
  color: var(--subtext);
  background: transparent;
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  font-family: var(--font-family);
  transition: color .15s, border-color .15s, background .15s;
}
.back-btn:hover { color: var(--text); background: var(--card-hover); }

.cpage-body {
  padding: 24px 40px 40px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.net-body { gap: 12px; }

.net-state {
  margin: auto;
  font-size: 13px;
  color: var(--subtext);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.net-state--error { color: var(--negative); }

.net-reanalyze-btn {
  background: var(--accent);
  color: var(--cta-text);
  font-size: 12px;
  font-weight: 700;
  border: none;
  padding: 10px 20px;
  border-radius: var(--radius);
  cursor: pointer;
}
.net-reanalyze-btn:hover { opacity: 0.88; }

.net-graph-canvas-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.net-main-row {
  flex: 1;
  min-height: 420px;
  display: flex;
  gap: 16px;
}

.net-graph-canvas-inner {
  position: relative;
  flex: 1;
  min-width: 0;
}

.net-graph-canvas {
  position: absolute;
  inset: 0;
  border-radius: var(--radius);
  border: 0.5px solid var(--border);
  overflow: hidden;
}
.net-graph-svg {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
  touch-action: none;
}
.net-graph-svg--panning { cursor: grabbing; }
.net-svg-node {
  cursor: grab;
  /* 아주 얇은 흰 테두리 — 무채색 배경 위에서 노드 하나하나의 경계를 또렷하게 잡아줘서
     "그냥 색칠된 점"이 아니라 값싼 유리질감 없이도 입체감 있는 마커처럼 보이게 함 */
  stroke: rgba(255, 255, 255, 0.65);
  stroke-width: 0.75;
  transition: r .15s ease, fill .15s ease, stroke .15s ease, stroke-width .15s ease, opacity .2s ease;
}
.net-svg-node--dragging { cursor: grabbing; }
/* 드래그를 놓은 직후에만 짧게 cx/cy에 스프링 트랜지션을 걸어 원위치로 튕겨 돌아가 보이게 함.
   평소엔 이 트랜지션이 없어야 드래그 중 좌표 변경이 지연 없이 그대로 반영됨 */
.net-svg-node--snapping {
  transition: r .15s ease, fill .15s ease, stroke .15s ease, stroke-width .15s ease, opacity .2s ease,
              cx .5s cubic-bezier(.34, 1.56, .64, 1), cy .5s cubic-bezier(.34, 1.56, .64, 1);
}
.net-svg-sentiment-badge { stroke: var(--bg); stroke-width: 1.2; pointer-events: none; }
.net-svg-link line { transition: stroke .12s ease, stroke-width .12s ease; }
/* 노드를 놓은 직후에만 선의 양 끝(x1/y1/x2/y2)에도 같은 스프링 트랜지션을 걸어서,
   원(노드)은 튕겨 돌아가는데 거기 붙은 선만 순간이동하는 것처럼 보이는 어긋남을 없앰.
   평소엔 이 트랜지션이 없어야 드래그 중 선이 손가락을 지연 없이 그대로 따라옴 */
.net-svg-link--snapping line {
  transition: stroke .12s ease, stroke-width .12s ease,
              x1 .5s cubic-bezier(.34, 1.56, .64, 1), y1 .5s cubic-bezier(.34, 1.56, .64, 1),
              x2 .5s cubic-bezier(.34, 1.56, .64, 1), y2 .5s cubic-bezier(.34, 1.56, .64, 1);
}
.net-svg-link-hit { cursor: pointer; }
.net-svg-label {
  font-size: 10px;
  font-weight: 600;
  font-family: var(--font-family);
  paint-order: stroke;
  stroke: var(--bg);
  stroke-width: 6px;
  stroke-linejoin: round;
  stroke-opacity: 0.9;
  pointer-events: none;
}

/* ── 범례 — 토글 없이 항상 떠 있는 고정 박스 ── */
.net-legend-wrap {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
}
/* 아이콘(점/막대/스와치)이 오히려 지저분해 보인다는 피드백 — 그림 없이 텍스트만
   세로로 나열하는 작은 캡션 박스로 정리 */
.net-legend-panel {
  background: var(--search-bg);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.net-legend-text {
  font-size: 10.5px;
  color: var(--subtext);
  line-height: 1.4;
  white-space: nowrap;
}
.net-legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* 지도를 옮기거나 확대/축소했을 때만 나타나는 초기화 버튼 — 범례 반대편(우상단)에 둬서
   겹치지 않게 함 */
.net-reset-view-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--search-bg);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 11.5px;
  color: var(--subtext);
  cursor: pointer;
  transition: color .15s, border-color .15s;
}
.net-reset-view-btn:hover { color: var(--text); border-color: var(--text); }

/* ── 옆 패널 — 목록/상세 공용. 항상 마운트되어 있어서 열고 닫혀도 그래프 폭이 안 변함 ── */
.net-panel {
  position: relative;
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 12px;
  border: 0.5px solid var(--border);
  background: var(--card);
  overflow: hidden;
}
.net-panel-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
}
.net-panel-header { display: flex; flex-direction: column; gap: 10px; }
.net-panel-header-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-align: left;
  font-family: var(--font-family);
}
.net-panel-header-btn:hover .net-panel-title { color: var(--accent); }
/* 유튜브로 넘어갈 때(VideoInfoCard의 "유튜브에서 보기")와 같은 시각 언어 —
   살짝 확대 + 회색 오버레이 + 가운데 라벨로 "눌러서 다른 곳으로 이동한다"는 걸 알려줌 */
.net-panel-thumb-wrap { position: relative; overflow: hidden; border-radius: 8px; }
.net-panel-header-btn:hover .net-panel-thumb-lg { transform: scale(1.045); }
.net-panel-thumb-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0);
  opacity: 0;
  transition: opacity .25s ease, background .25s ease;
}
.net-panel-header-btn:hover .net-panel-thumb-overlay {
  opacity: 1;
  background: rgba(0, 0, 0, 0.42);
}
.net-panel-thumb-overlay-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #fff;
  font-size: 11.5px;
  font-weight: 700;
  padding: 7px 13px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.35);
  border: 0.5px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(6px);
  transform: translateY(4px);
  transition: transform .25s ease;
}
.net-panel-header-btn:hover .net-panel-thumb-overlay-label { transform: translateY(0); }
.net-panel-thumb-lg {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 8px;
  border: 0.5px solid var(--border);
  transition: transform .3s ease;
}
.net-panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── 목록 모드(기본) — 지금 지도에 있는 노드들을 제목만 나열 ── */
.net-list-header { flex-shrink: 0; display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.net-list-title {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  padding: 14px 14px 10px;
}
.net-list-header .sort-dropdown { margin: 10px 10px 0 0; }
/* HistoryView.vue의 정렬 드롭다운과 같은 패턴 — 이 화면에서만 쓰므로 그대로 복사해둠 */
.sort-dropdown { position: relative; flex-shrink: 0; }
.sort-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  font-family: var(--font-family);
  padding: 5px 10px;
  border-radius: 8px;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  cursor: pointer;
  transition: border-color .15s, color .15s, background .15s;
  white-space: nowrap;
}
.sort-trigger:hover { color: var(--text); background: var(--card-hover); border-color: rgb(from var(--accent) r g b / 0.4); }
.sort-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 130px;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  z-index: 50;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.sort-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-family);
  color: var(--subtext);
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background .12s, color .12s;
}
.sort-option:hover { background: rgb(from var(--accent) r g b / 0.07); color: var(--text); }
.sort-option.active { color: var(--accent); font-weight: 600; }
.sort-option-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
.net-list-count {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--subtext);
  background: var(--card-hover);
  border-radius: 999px;
  padding: 1px 7px;
}
.net-list-title-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  border: none;
  background: var(--card-hover);
  color: var(--subtext);
  cursor: pointer;
  flex-shrink: 0;
  transition: color .15s, background .15s;
}
.net-list-title-back:hover { color: var(--text); }
.net-list-note {
  font-size: 10.5px;
  color: var(--subtext);
  line-height: 1.5;
  padding: 0 14px 10px;
}
.net-list-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 0 8px 10px;
}
.net-list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 8px;
  border-radius: 8px;
  font-size: 12.5px;
  color: var(--subtext);
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
  font-family: var(--font-family);
  line-height: 1.5;
  transition: background .12s, color .12s;
}
.net-list-item:hover, .net-list-item--active { background: var(--card-hover); color: var(--text); }
.net-list-item--unavailable { cursor: default; }
.net-list-item-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}
/* 제목만 쭉 나열된 raw text 목록이라는 피드백 — 감정 점 + 댓글수/긍정률 메타 한 줄을 더해서
   "분석 결과 목록"처럼 보이게 함 */
.net-list-item--video { align-items: flex-start; padding: 9px 8px; }
.net-list-item-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.net-list-item-body { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.net-list-item-meta { font-size: 10.5px; color: var(--subtext); opacity: 0.75; }
/* 토픽 그룹 — 개수만 있으면 그냥 목록 같아서, 비중(%)과 작은 막대를 더해 topic
   distribution처럼 보이게 함 */
.net-list-item--topic { flex-direction: column; align-items: stretch; gap: 6px; }
.net-list-item-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.net-list-item-bar { display: block; height: 4px; border-radius: 999px; background: var(--card-hover); overflow: hidden; }
.net-list-item-bar-fill { display: block; height: 100%; border-radius: 999px; }
.net-list-reanalyze {
  flex-shrink: 0;
  font-size: 10.5px;
  font-weight: 600;
  padding: 4px 9px;
  border-radius: 999px;
  border: 0.5px solid var(--border);
  background: var(--card);
  color: var(--subtext);
  cursor: pointer;
  font-family: var(--font-family);
  transition: color .15s, border-color .15s, background .15s;
}
.net-list-reanalyze:hover { color: var(--accent); border-color: rgb(from var(--accent) r g b / 0.4); background: rgb(from var(--accent) r g b / 0.08); }
.net-list-divider {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--subtext);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin: 10px 8px 4px;
  padding-top: 10px;
  border-top: 0.5px solid var(--border);
}
/* 그룹순 정렬일 때 그룹 경계마다 넣는 얇은 구분선 — 목록이 지도의 클러스터 구조를
   따라간다는 걸 시각적으로 보여줌 */
.net-list-group-break { height: 0.5px; background: var(--border); margin: 6px 8px; }

/* ── 스크롤바 — 기본 OS 스크롤바(위아래 화살표 버튼 포함)가 촌스러워서 얇은 커스텀으로 교체 ── */
.net-list-scroll, .net-panel-scroll {
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.net-list-scroll::-webkit-scrollbar, .net-panel-scroll::-webkit-scrollbar { width: 6px; }
.net-list-scroll::-webkit-scrollbar-button, .net-panel-scroll::-webkit-scrollbar-button { display: none; height: 0; width: 0; }
.net-list-scroll::-webkit-scrollbar-track, .net-panel-scroll::-webkit-scrollbar-track { background: transparent; }
.net-list-scroll::-webkit-scrollbar-thumb, .net-panel-scroll::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 999px;
}
.net-list-scroll::-webkit-scrollbar-thumb:hover, .net-panel-scroll::-webkit-scrollbar-thumb:hover { background: var(--subtext); }
.net-panel-comment-text {
  font-size: 13px;
  color: var(--text);
  line-height: 1.6;
}
.net-panel-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--subtext);
}
.net-panel-stat-value { font-weight: 600; color: var(--text); }

.net-panel-section { display: flex; flex-direction: column; gap: 6px; }
.net-panel-section--highlight {
  padding: 10px;
  border-radius: 10px;
  background: var(--search-bg);
  border: 0.5px solid var(--border);
}
.net-panel-section-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--subtext);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.net-panel-neighbor {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border-radius: 8px;
  background: transparent;
  border: none;
  font-family: var(--font-family);
  text-align: left;
  cursor: pointer;
  transition: background .12s;
}
/* 관계 이유(공통 토픽)까지 함께 보여주는 풍부한 버전 — 세로로 두 줄(제목+% / 토픽 pill) */
.net-panel-neighbor--rich { flex-direction: column; align-items: stretch; gap: 4px; }
.net-panel-neighbor-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.net-panel-neighbor-reason { font-size: 11px; color: var(--subtext); line-height: 1.45; }
button.net-panel-neighbor:hover { background: var(--card-hover); }
.net-panel-neighbor-label {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.net-panel-neighbor-sim { flex-shrink: 0; font-size: 11px; font-weight: 600; color: var(--accent); }

.net-panel-cta {
  background: var(--accent);
  color: var(--cta-text);
  font-size: 12px;
  font-weight: 700;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
}
.net-panel-cta:hover { opacity: 0.88; }

.topic-pill {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgb(from var(--accent) r g b / 0.08);
  color: var(--accent);
  border: 0.5px solid rgb(from var(--accent) r g b / 0.22);
  white-space: nowrap;
  letter-spacing: 0.01em;
}
/* ── 카드 5개짜리 "과제 발표 슬라이드" 느낌을 없애고, 번호 붙은 얇은 한 줄 프로세스 바로 —
   설명은 항상 보이지 않고 title 속성(네이티브 툴팁)으로만 필요할 때 확인하게 함.
   그래프/선택 분석 다음으로 낮은 우선순위라 서체도 legend와 비슷한 caption 톤으로 낮춤 ── */
.net-pipeline {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 12px;
  border-top: 0.5px solid var(--border);
}
.net-pipeline-title {
  flex-shrink: 0;
  font-size: 9.5px;
  font-weight: 700;
  color: var(--dim);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}
.net-pipeline-strip {
  display: flex;
  align-items: center;
  gap: 5px;
  overflow-x: auto;
  min-width: 0;
}
.net-pipeline-step {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--subtext);
  white-space: nowrap;
  cursor: default;
}
.net-pipeline-step-num { font-size: 9px; font-weight: 700; color: var(--dim); }
.net-pipeline-arrow { flex-shrink: 0; color: var(--dim); opacity: 0.7; }

/* ── 엣지(선) 클릭 시 목록 위에 얹히는 "연결 분석" 카드 ── */
.net-edge-card {
  flex-shrink: 0;
  margin: 12px 12px 0;
  padding: 12px;
  border-radius: 10px;
  background: var(--search-bg);
  border: 0.5px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.net-edge-card-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--subtext);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.net-edge-card-pair {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.net-edge-card-sim-row { display: flex; align-items: center; justify-content: space-between; font-size: 11.5px; color: var(--subtext); }
.net-edge-card-sim-value { font-weight: 700; color: var(--accent); font-size: 13px; }
.net-edge-card-topics { display: flex; flex-wrap: wrap; gap: 6px; }
.net-edge-card-reason { font-size: 11.5px; color: var(--subtext); line-height: 1.5; }

@media (max-width: 768px) {
  .net-page { padding-top: 112px; }
  .cpage-header {
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    padding: 16px 16px 14px;
    background: color-mix(in srgb, var(--bg) 65%, transparent);
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  .cpage-body { padding: 18px 16px 32px; }

  /* 데스크톱은 "지도+목록을 한 화면에 맞추기"가 목표라 flex:1로 뷰포트 높이를 나눠 쓰지만,
     모바일 폭에서는 그 둘을 나란히 두면 둘 다 못 쓸 만큼 좁아짐 — 세로로 쌓고(지도 먼저,
     목록 아래) 페이지 전체가 자연스럽게 스크롤되게 함. 목록 내부의 자체 스크롤(overflow-y:auto)도
     같이 켜져 있으면 "페이지 스크롤 vs 목록 안 스크롤"이 손가락 위치에 따라 헷갈리므로,
     모바일에서는 목록 스크롤을 꺼서 스크롤 표면을 페이지 하나로 통일함 */
  .net-graph-canvas-wrap { flex: none; gap: 14px; }
  .net-main-row {
    flex: none;
    flex-direction: column;
    min-height: 0;
    gap: 14px;
  }
  .net-graph-canvas-inner {
    flex: none;
    width: 100%;
    height: min(56vh, 400px);
    min-height: 260px;
  }
  .net-panel {
    width: 100%;
    flex: none;
    max-height: none;
    overflow: visible;
  }
  .net-panel-scroll, .net-list-scroll {
    flex: none;
    overflow-y: visible;
  }

  /* 좁은 지도 위에서 범례가 노드를 가리지 않도록 훨씬 작고 압축된 캡션으로 */
  .net-legend-wrap { top: 8px; left: 8px; }
  .net-legend-panel { padding: 5px 8px; gap: 2px; }
  .net-legend-text { font-size: 9px; }
  .net-reset-view-btn { top: 8px; right: 8px; padding: 5px 8px; font-size: 10.5px; gap: 4px; }

  /* 파이프라인 바 — 라벨을 줄이고 여백을 좁혀서 좁은 화면에서 답답해 보이지 않게 함.
     가로 스텝 목록 자체는 이미 overflow-x:auto라 페이지 세로 스크롤과 안 부딪힘 */
  .net-pipeline { padding: 6px 10px; gap: 8px; }
  .net-pipeline-title { font-size: 8.5px; }
  .net-pipeline-step { font-size: 10px; }
}
</style>
