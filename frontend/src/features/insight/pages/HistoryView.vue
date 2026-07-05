<script setup lang="ts">
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { insightApi } from '@/features/insight/api/insightApi'
import { useAnalysisStore } from '@/features/insight/stores/analysis'
import { useSettingsStore } from '@/features/settings/stores/settings'
import type { HistoryItem } from '@/features/insight/types/insight'
import { messages } from '@/locales/messages'
import { fillTopicLabels, displayLabel } from '@/features/insight/composables/useLabelTranslation'
import { useHistory, type HistoryEntry } from '@/features/insight/composables/useHistory'
import { parseBackup } from '@/features/insight/composables/useJsonBackup'

const router        = useRouter()
const analysisStore = useAnalysisStore()
const settings      = useSettingsStore()

type DisplayItem = HistoryItem & { importedOnly?: boolean }

const items = ref<HistoryItem[]>([])
const isLoading = ref(true)
const error = ref('')

// 백엔드 분석 기록과 별개로, 사용자가 JSON으로 업로드해 이 브라우저에만 저장된 항목 —
// 같은 videoId가 백엔드에도 이미 있으면 굳이 중복으로 보여줄 필요 없어서 그 경우엔 숨김
const localEntries = ref<HistoryEntry[]>(useHistory().getAll())
// 이 함수가 던지면 computed 전체가 깨져서 히스토리 화면이 통째로 안 보이게 됨 — 손상되거나
// 형식이 안 맞는 로컬 항목 하나 때문에 나머지 정상 항목까지 다 안 보이면 안 되므로,
// 문제 있는 항목은 null을 반환해 조용히 건너뛰고 나머지는 그대로 보여줌
function entryToDisplayItem(e: HistoryEntry): DisplayItem | null {
  try {
    const topics = e.data.topics ?? []
    const total = topics.reduce((sum, t) => sum + (t.mentionCount ?? 0), 0) || 1
    const positive = Math.round(topics.reduce((sum, t) => sum + (t.sentiment?.positive ?? 0) * (t.mentionCount ?? 0), 0) / total)
    const negative = Math.round(topics.reduce((sum, t) => sum + (t.sentiment?.negative ?? 0) * (t.mentionCount ?? 0), 0) / total)
    if (!e.data.video?.videoId) return null
    return {
      videoId: e.videoId,
      title: e.data.video.title ?? e.videoId,
      channelTitle: e.data.video.channelTitle ?? '',
      thumbnailUrl: e.data.video.thumbnailUrl ?? '',
      publishedAt: e.data.video.publishedAt ?? '',
      analyzedComments: e.data.video.analyzedComments ?? 0,
      analyzedAt: e.data.analyzedAt ?? e.savedAt,
      topTopics: topics.slice(0, 3),
      overallSentiment: { positive, negative },
      importedOnly: true,
    }
  } catch {
    return null
  }
}
const localOnlyItems = computed<DisplayItem[]>(() => {
  const backendIds = new Set(items.value.map(i => i.videoId))
  return localEntries.value
    .filter(e => e.importedOnly && !backendIds.has(e.videoId))
    .map(entryToDisplayItem)
    .filter((i): i is DisplayItem => i !== null)
})
const allItems = computed<DisplayItem[]>(() => [...items.value, ...localOnlyItems.value])

const importInput = ref<HTMLInputElement | null>(null)
function triggerImport() { importInput.value?.click() }

async function onImportFiles(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length) return
  for (const file of Array.from(files)) {
    try {
      const backup = parseBackup(await file.text())
      if (!backup) { error.value = M.value.importJsonError; continue }
      useHistory().save(backup.videoId, backup.data, backup.graph, true)
    } catch {
      error.value = M.value.importJsonError
    }
  }
  localEntries.value = useHistory().getAll()
  ;(e.target as HTMLInputElement).value = '' // 같은 파일을 다시 선택해도 change가 또 발생하게
}

type SortKey = 'date' | 'positive' | 'negative' | 'published'
const sortKey = ref<SortKey>('date')

const M = computed(() => messages[settings.lang])

const fmtComments = (n: string) => {
  const l = settings.lang
  if (l === 'en') return `${n} comments`
  if (l === 'zh') return `${n} 条评论`
  if (l === 'ja') return `${n} 件のコメント`
  return `댓글 ${n}개`
}

const SORT_OPTIONS = computed(() => [
  { key: 'date'      as SortKey, label: M.value.sortDate },
  { key: 'positive'  as SortKey, label: M.value.sortPos  },
  { key: 'negative'  as SortKey, label: M.value.sortNeg  },
  { key: 'published' as SortKey, label: M.value.sortPub  },
])

const dropdownOpen = ref(false)

function onClickOutside(e: MouseEvent) {
  const el = document.querySelector('.sort-dropdown')
  if (el && !el.contains(e.target as Node)) dropdownOpen.value = false
}
onMounted(() => document.addEventListener('mousedown', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutside))

const sortedItems = computed(() => {
  const arr = [...allItems.value]
  if (sortKey.value === 'positive')  return arr.sort((a, b) => b.overallSentiment.positive  - a.overallSentiment.positive)
  if (sortKey.value === 'negative')  return arr.sort((a, b) => b.overallSentiment.negative  - a.overallSentiment.negative)
  if (sortKey.value === 'published') return arr.sort((a, b) => b.publishedAt.localeCompare(a.publishedAt))
  return arr.sort((a, b) => b.analyzedAt.localeCompare(a.analyzedAt))
})

onMounted(async () => {
  try {
    items.value = await insightApi.getHistory()
    fillTopicLabels(allItems.value.flatMap(i => i.topTopics), settings.lang)
  } catch {
    error.value = '기록을 불러오지 못했습니다. 백엔드 서버가 실행 중인지 확인해주세요.'
  } finally {
    isLoading.value = false
  }
})

watch(() => settings.lang, (lang) => {
  fillTopicLabels(allItems.value.flatMap(i => i.topTopics), lang)
})

const fmtDate = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}  ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const fmtNum = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M' :
  n >= 1_000     ? (n / 1_000).toFixed(1) + 'K'     :
  String(n)

const onView = async (item: DisplayItem) => {
  // 로컬로 가져온 항목은 서버에 실제로 존재하지 않으므로 재요청하지 않고 저장된 데이터를 그대로 씀
  if (item.importedOnly) {
    const entry = localEntries.value.find(e => e.videoId === item.videoId)
    if (entry) {
      analysisStore.setResult(entry.data)
      // id를 남겨둬야 새로고침 시 HomeView가 로컬 저장소에서 같은 항목을 다시 찾을 수 있음
      await router.push({ name: 'history-view', query: { id: item.videoId } })
    }
    return
  }
  try {
    const data = await insightApi.getByVideoId(item.videoId)
    analysisStore.setResult(data)
    // videoId를 쿼리에 남겨서 새로고침해도 같은 영상을 다시 불러올 수 있게 함
    await router.push({ name: 'history-view', query: { id: item.videoId } })
  } catch (e) {
    console.error('[onView]', e)
    error.value = '영상 데이터를 불러오지 못했습니다.'
  }
}

const pendingDeleteId = ref<string | null>(null)

function requestDelete(videoId: string) {
  pendingDeleteId.value = videoId
}

async function confirmDelete() {
  const videoId = pendingDeleteId.value
  if (!videoId) return
  pendingDeleteId.value = null
  const localItem = localOnlyItems.value.find(i => i.videoId === videoId)
  if (localItem) {
    useHistory().remove(videoId)
    localEntries.value = useHistory().getAll()
    return
  }
  try {
    await insightApi.deleteCache(videoId)
    items.value = items.value.filter(i => i.videoId !== videoId)
  } catch {
    error.value = M.value.deleteFailed
  }
}
</script>

<template>
  <div class="history-wrap overflow-y-auto flex-1" style="position:relative;z-index:2; display:flex; flex-direction:column;">

    <!-- 헤더 -->
    <div class="history-header" style="display:flex; align-items:flex-end; justify-content:space-between;">
      <div>
        <h1 style="font-size:18px; font-weight:700; color:var(--text); letter-spacing:-.02em;">{{ M.historyTitle }}</h1>
        <p style="font-size:13px; color:var(--subtext); margin-top:4px;">
          {{ M.historySub }}
        </p>
      </div>

      <div style="display:flex; align-items:center; gap:8px;">
        <!-- JSON 불러오기 — 서버 호출 없이 이 브라우저(localStorage)에만 저장됨.
             여러 파일을 한 번에 선택할 수 있음 -->
        <input ref="importInput" type="file" accept=".json,application/json" multiple hidden @change="onImportFiles" />
        <button class="sort-trigger" @click="triggerImport">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <path d="M12 11v6M9.5 14.5 12 17l2.5-2.5"/>
          </svg>
          {{ M.importJsonBtn }}
        </button>

        <!-- 정렬 드롭다운 -->
        <div class="sort-dropdown">
          <button class="sort-trigger" @click="dropdownOpen = !dropdownOpen">
            {{ SORT_OPTIONS.find(o => o.key === sortKey)?.label }}
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
              :style="{ transform: dropdownOpen ? 'rotate(180deg)' : 'none', transition: 'transform .18s' }">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          <div v-if="dropdownOpen" class="sort-menu">
            <button
              v-for="opt in SORT_OPTIONS"
              :key="opt.key"
              class="sort-option"
              :class="{ active: sortKey === opt.key }"
              @click="sortKey = opt.key; dropdownOpen = false"
            >
              <span class="sort-option-dot" v-if="sortKey === opt.key" />
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="history-body">

    <p v-if="error" class="text-sm" style="color: #f87171">{{ error }}</p>

    <!-- 로딩 -->
    <div v-if="isLoading" class="flex items-center justify-center py-32">
      <p class="text-sm" style="color: var(--subtext)">{{ M.loading }}</p>
    </div>

    <!-- 빈 상태 -->
    <div v-else-if="!allItems.length" class="flex flex-col items-center justify-center py-32 gap-3">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
        style="color: var(--subtext)">
        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
      </svg>
      <p class="text-sm" style="color: var(--subtext)">{{ M.emptyHistory }}</p>
      <button @click="router.push({ name: 'home' })"
        class="mt-2 text-sm px-4 py-2 rounded-lg font-semibold"
        style="background: var(--accent); color: var(--cta-text)">
        {{ M.goAnalyze }}
      </button>
    </div>

    <!-- 카드 그리드 -->
    <div v-else class="grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">
      <div
        v-for="item in sortedItems"
        :key="item.videoId"
        class="rounded-xl border flex flex-col overflow-hidden"
        style="background: var(--card); border-color: var(--border)"
      >
        <!-- 썸네일 -->
        <div class="aspect-video bg-slate-800/60 overflow-hidden shrink-0" style="position:relative;">
          <img
            :src="item.thumbnailUrl"
            :alt="item.title"
            class="w-full h-full object-cover"
            @error="($event.target as HTMLImageElement).style.opacity = '0'"
          />
          <!-- 백엔드에 없고 이 브라우저에 업로드해서만 있는 항목임을 표시 -->
          <span v-if="item.importedOnly" class="imported-badge">{{ M.importedBadge }}</span>
        </div>

        <div class="flex flex-col gap-3 flex-1" style="padding: 18px 20px 16px;">

          <!-- 제목 + 채널 -->
          <div>
            <p class="text-[14px] font-semibold line-clamp-2" style="color: var(--text); line-height: 1.6; min-height: 44.8px;">
              {{ item.title }}
            </p>
            <p class="text-[13px] mt-1.5 font-medium" style="color: var(--subtext)">{{ item.channelTitle }}</p>
          </div>

          <!-- 분석 날짜 + 댓글 수 -->
          <div class="flex items-center justify-between text-[12px] font-medium" style="color: var(--subtext); margin-top: auto;">
            <span>{{ fmtDate(item.analyzedAt) }}</span>
            <span>{{ fmtComments(fmtNum(item.analyzedComments)) }}</span>
          </div>

          <!-- 전체 감정 미니바 -->
          <div>
            <div class="flex rounded overflow-hidden h-[6px]">
              <div :style="`width: ${item.overallSentiment.positive}%; background: var(--positive)`"></div>
              <div :style="`width: ${100 - item.overallSentiment.positive - item.overallSentiment.negative}%; background: var(--neutral)`"></div>
              <div :style="`width: ${item.overallSentiment.negative}%; background: var(--negative)`"></div>
            </div>
            <div class="flex justify-between mt-2 text-[11px] font-medium">
              <span style="color: var(--positive)">{{ M.positive }} {{ item.overallSentiment.positive }}%</span>
              <span style="color: var(--negative)">{{ M.negative }} {{ item.overallSentiment.negative }}%</span>
            </div>
          </div>

          <!-- 상위 토픽 -->
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="topic in item.topTopics"
              :key="topic.label"
              class="topic-pill"
            >{{ displayLabel(topic, settings.lang) }}</span>
          </div>

        </div>

        <!-- 버튼 (카드 하단에 고정) -->
        <div class="card-footer">
          <button
            @click="onView(item)"
            class="view-btn flex-1 py-2 rounded-lg text-[13px] font-semibold cursor-pointer"
          >{{ M.viewBtn }}</button>
          <button
            @click="requestDelete(item.videoId)"
            class="delete-btn"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14H6L5 6"/>
              <path d="M10 11v6M14 11v6"/>
            </svg>
            {{ M.deleteBtn }}
          </button>
        </div>
      </div>
    </div>

    </div>

    <!-- 삭제 확인 모달 -->
    <div v-if="pendingDeleteId" class="confirm-overlay" @click.self="pendingDeleteId = null">
      <div class="confirm-modal">
        <div class="confirm-icon-badge">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14H6L5 6"/>
            <path d="M10 11v6M14 11v6"/>
          </svg>
        </div>
        <h3 class="confirm-title">{{ M.confirmDeleteTitle }}</h3>
        <p class="confirm-body">{{ M.confirmDeleteBody }}</p>
        <div class="confirm-actions">
          <button class="confirm-btn cancel" @click="pendingDeleteId = null">{{ M.cancelBtn }}</button>
          <button class="confirm-btn danger" @click="confirmDelete">{{ M.confirmDeleteBtn }}</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.sort-dropdown {
  position: relative;
  flex-shrink: 0;
}
.sort-trigger {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-family);
  padding: 6px 12px;
  border-radius: 8px;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  cursor: pointer;
  transition: border-color .15s, color .15s, background .15s;
  white-space: nowrap;
}
.sort-trigger:hover { background: var(--card-hover); }
.view-btn {
  background: transparent;
  border: 0.5px solid var(--border);
  color: var(--text);
  transition: border-color .15s, background .15s;
}
.view-btn:hover { border-color: rgb(from var(--accent) r g b / 0.4); background: rgb(from var(--accent) r g b / 0.06); }

.sort-trigger:hover {
  color: var(--text);
  border-color: rgb(from var(--accent) r g b / 0.4);
}
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
.sort-option:hover {
  background: rgb(from var(--accent) r g b / 0.07);
  color: var(--text);
}
.sort-option.active {
  color: var(--accent);
  font-weight: 600;
}
.sort-option-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}

.card-footer {
  display: flex;
  gap: 8px;
  padding: 12px 20px 16px;
}

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

.imported-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  backdrop-filter: blur(4px);
}

.delete-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-family);
  cursor: pointer;
  border: 0.5px solid rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.06);
  color: #f87171;
  transition: background 0.15s, border-color 0.15s;
}
.delete-btn:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.5);
}

/* ── 삭제 확인 모달 ── */
.confirm-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: radial-gradient(circle at 50% 40%, rgba(244,63,94,0.08), rgba(8, 6, 16, 0.72) 60%);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
  animation: confirm-fade-in 0.2s ease-out;
}
@keyframes confirm-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.confirm-modal {
  background: var(--card);
  border: 0.5px solid rgba(244, 63, 94, 0.25);
  border-radius: 20px;
  padding: 32px 32px 28px;
  max-width: 400px;
  width: 100%;
  display: flex; flex-direction: column; align-items: flex-start;
  box-shadow: 0 24px 70px rgba(0,0,0,0.45), 0 0 60px rgba(244,63,94,0.08);
  animation: confirm-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes confirm-pop {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.confirm-icon-badge {
  width: 46px; height: 46px;
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  background: var(--negative);
  box-shadow: 0 8px 22px rgba(225,29,72,0.35), 0 0 0 1px rgba(255,255,255,0.08) inset;
  margin-bottom: 16px;
}
.confirm-title { font-size: 17px; font-weight: 700; color: var(--text); margin-bottom: 8px; letter-spacing: -.01em; }
.confirm-body { font-size: 13px; color: var(--subtext); line-height: 1.65; }
.confirm-actions { display: flex; gap: 10px; margin-top: 22px; width: 100%; }
.confirm-btn {
  flex: 1;
  font-size: 13px; font-weight: 600;
  padding: 11px 16px; border-radius: 10px;
  border: 0.5px solid var(--border);
  cursor: pointer; font-family: var(--font-family);
  transition: transform 0.15s, box-shadow 0.15s;
}
.confirm-btn:hover { transform: translateY(-1px); }
.confirm-btn.cancel { background: var(--card-hover); color: var(--subtext); }
.confirm-btn.danger {
  background: var(--negative);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 6px 18px rgba(225,29,72,0.3);
}
.confirm-btn.danger:hover { opacity: 0.88; box-shadow: 0 8px 22px rgba(225,29,72,0.42); }

.history-header {
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

.history-body {
  padding: 24px 40px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

@media (max-width: 768px) {
  .history-wrap { padding-top: 112px; }
  .history-header {
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    padding: 16px 16px 14px;
    background: color-mix(in srgb, var(--bg) 65%, transparent);
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    flex-wrap: wrap;
    align-items: flex-start !important;
    gap: 10px;
  }
  .history-body { padding: 18px 16px 32px; gap: 18px; }
}
</style>
