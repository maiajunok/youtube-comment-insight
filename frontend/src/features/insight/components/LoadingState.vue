<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { useAnalysisStore } from '@/features/insight/stores/analysis'
import { useHistory } from '@/features/insight/composables/useHistory'
import { messages } from '@/locales/messages'

const props = defineProps<{ step: string; progress: number; videoId?: string | null }>()

const settings = useSettingsStore()
const analysisStore = useAnalysisStore()
const M = computed(() => messages[settings.lang])

const thumbnailUrl = computed(() =>
  props.videoId ? `https://i.ytimg.com/vi/${props.videoId}/hqdefault.jpg` : null
)
const thumbnailFailed = ref(false)
watch(() => props.videoId, () => { thumbnailFailed.value = false })

// 대기열은 최대 3개까지만 옆에 줄세워 미리보기, 그 이상은 "더보기" 드롭다운으로
const visibleQueue = computed(() => analysisStore.queue.slice(0, 3))
const overflowQueue = computed(() => analysisStore.queue.slice(3))
const queueMoreOpen = ref(false)

// 취소는 되돌릴 수 없으니(현재 분석은 재분석, 대기열은 다시 제출해야 함) 확인 모달을 거침 —
// 'current' = 지금 분석 중인 것, number = 대기열에서의 인덱스
const confirmTarget = ref<'current' | number | null>(null)

function confirmCancel() {
  if (confirmTarget.value === 'current') analysisStore.cancelCurrent()
  else if (typeof confirmTarget.value === 'number') analysisStore.removeFromQueue(confirmTarget.value)
  confirmTarget.value = null
}

// 분석 중 화면에서도 대기열에 영상을 더 추가할 수 있게 — 지금 분석 중인 썸네일 옆의
// 작은 + 버튼을 누르면 URL 입력창이 나타남
const showAddInput = ref(false)
const addUrl = ref('')
function submitAdd() {
  if (!addUrl.value.trim()) return
  analysisStore.submit(addUrl.value.trim(), (videoId, d) => useHistory().save(videoId, d))
  addUrl.value = ''
  showAddInput.value = false
}

const STEPS = computed(() => [
  { n: 1, label: M.value.loadingStep1Label, sub: M.value.loadingStep1Sub },
  { n: 2, label: M.value.loadingStep2Label, sub: M.value.loadingStep2Sub },
  { n: 3, label: M.value.loadingStep3Label, sub: M.value.loadingStep3Sub },
])
</script>

<template>
  <div class="flex flex-col items-center justify-center py-24 gap-10">

    <!-- 지금 분석 중인 영상(원래 크기 그대로) + 오른쪽에 대기열을 흐릿하게 줄세워 보여줌 -->
    <div class="thumb-row">
      <div class="cur-thumb">
        <img
          v-if="thumbnailUrl && !thumbnailFailed"
          :src="thumbnailUrl"
          alt=""
          class="cur-thumb-img"
          @error="thumbnailFailed = true"
        />
        <button class="thumb-x" :title="M.cancelAnalysisBtn" @click="confirmTarget = 'current'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="queue-sep" />

      <div class="queue-strip">
        <div v-for="(q, i) in visibleQueue" :key="i" class="q-thumb">
          <img
            v-if="q.videoId"
            :src="`https://i.ytimg.com/vi/${q.videoId}/hqdefault.jpg`"
            alt=""
            @error="($event.target as HTMLImageElement).style.opacity = '0'"
          />
          <button class="thumb-x" :title="M.queueRemove" @click="confirmTarget = i">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div v-if="overflowQueue.length" class="queue-more">
          <button class="queue-more-btn" @click="queueMoreOpen = !queueMoreOpen">
            +{{ overflowQueue.length }}
          </button>
          <Transition name="dropdown">
            <div v-if="queueMoreOpen" class="queue-more-panel">
              <div v-for="(q, i) in overflowQueue" :key="i" class="queue-more-item">
                <img
                  v-if="q.videoId"
                  :src="`https://i.ytimg.com/vi/${q.videoId}/hqdefault.jpg`"
                  alt=""
                  class="queue-more-thumb"
                  @error="($event.target as HTMLImageElement).style.opacity = '0'"
                />
                <span class="queue-more-url">{{ q.url }}</span>
                <button class="queue-more-cancel" @click="confirmTarget = i + 3">
                  {{ M.queueRemove }}
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <!-- 대기열 맨 끝에 있는 "+" 타일 — 큐가 비어 있어도 항상 보여서 "더 추가할 수 있다"는 게
             한눈에 보이게 함(대기열 항목들과 같은 톤의 점선 박스, "+N 더보기"와 같은 스타일) -->
        <button class="queue-add-btn" :title="M.queueAddBtn" @click="showAddInput = !showAddInput">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- + 버튼으로 여는 URL 추가 입력창 -->
    <Transition name="dropdown">
      <div v-if="showAddInput" class="add-row">
        <input
          v-model="addUrl"
          type="text"
          :placeholder="M.urlPlaceholder"
          class="add-input"
          autofocus
          @keyup.enter="submitAdd"
        />
        <button class="add-submit" :disabled="!addUrl.trim()" @click="submitAdd">{{ M.queueAddBtn }}</button>
      </div>
    </Transition>

    <!-- 상단 스피너 + 타이틀 -->
    <div class="flex flex-col items-center gap-4">
      <div class="w-10 h-10 rounded-full border-[3px] animate-spin"
        style="border-color: var(--border); border-top-color: var(--accent)" />
      <p class="text-sm font-medium" style="color: var(--subtext)">{{ M.loadingTitle }}</p>
    </div>

    <!-- 취소 확인 모달 (현재 분석 취소 / 대기열 삭제 공용) -->
    <div v-if="confirmTarget !== null" class="confirm-overlay" @click.self="confirmTarget = null">
      <div class="confirm-modal">
        <div class="confirm-icon-badge">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </div>
        <h3 class="confirm-title">
          {{ confirmTarget === 'current' ? M.confirmCancelAnalysisTitle : M.confirmCancelQueuedTitle }}
        </h3>
        <p class="confirm-body">
          {{ confirmTarget === 'current' ? M.confirmCancelAnalysisBody : M.confirmCancelQueuedBody }}
        </p>
        <div class="confirm-actions">
          <button class="confirm-btn cancel" @click="confirmTarget = null">{{ M.cancelBtn }}</button>
          <button class="confirm-btn danger" @click="confirmCancel">
            {{ confirmTarget === 'current' ? M.cancelAnalysisBtn : M.queueRemove }}
          </button>
        </div>
      </div>
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
          style="border-color: var(--border); border-top-color: var(--accent)" />

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

<style scoped>
.thumb-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

/* ── 지금 분석 중인 영상(중앙, 원색, 제일 크게) ── */
.cur-thumb {
  position: relative;
  width: 200px;
  flex-shrink: 0;
  transition: transform .15s;
}
.cur-thumb:hover { transform: scale(1.06); }
.cur-thumb-img {
  width: 200px;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 14px;
  border: 0.5px solid var(--border);
  display: block;
  transition: filter .15s;
}
.cur-thumb:hover .cur-thumb-img { filter: brightness(0.6); }

/* ── 구분선 ── */
.queue-sep {
  width: 0.5px;
  align-self: stretch;
  background: var(--border);
  flex-shrink: 0;
}

/* ── 대기열: 오른쪽에 회색조로 줄세움(지금 분석 중인 것과 비슷한 크기), hover하면 원색+확대 ── */
.queue-strip {
  display: flex;
  align-items: center;
  gap: 10px;
}
.q-thumb {
  position: relative;
  width: 116px;
  flex-shrink: 0;
  transition: transform .15s;
}
.q-thumb:hover { transform: scale(1.08); }
.q-thumb img {
  width: 116px;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 14px;
  border: 0.5px solid var(--border);
  display: block;
  filter: grayscale(0.85) brightness(0.85);
  opacity: 0.75;
  transition: filter .15s, opacity .15s;
}
.q-thumb:hover img {
  filter: grayscale(0) brightness(0.6);
  opacity: 1;
}

/* ── 썸네일 위 취소(X) — hover 시 썸네일 중앙에 크게 뜸 ── */
.thumb-x {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.7);
  transition: opacity .15s, transform .15s;
}
.cur-thumb:hover .thumb-x,
.q-thumb:hover .thumb-x { opacity: 1; transform: scale(1); }

/* ── + 버튼으로 여는 URL 추가 입력창 — 히어로 검색창과 같은 톤 ── */
.add-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 420px;
}
.add-input {
  flex: 1;
  min-width: 0;
  background: var(--search-bg);
  border: 0.5px solid var(--search-border);
  border-radius: var(--radius);
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text);
  outline: none;
  font-family: var(--font-family);
  transition: border-color .2s;
}
.add-input:focus { border-color: rgb(from var(--accent) r g b / 0.5); }
.add-input::placeholder { color: var(--dim); }
.add-submit {
  flex-shrink: 0;
  background: var(--accent);
  color: var(--cta-text);
  font-size: 13px;
  font-weight: 700;
  border: none;
  padding: 10px 20px;
  border-radius: var(--radius);
  cursor: pointer;
  font-family: var(--font-family);
  transition: opacity .15s;
}
.add-submit:hover:not(:disabled) { opacity: 0.88; }
.add-submit:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── 대기열 "+N 더보기" ── */
.queue-more {
  position: relative;
  flex-shrink: 0;
}
.queue-more-btn {
  width: 116px;
  height: calc(116px * 9 / 16);
  border-radius: 14px;
  border: 0.5px dashed var(--border);
  background: var(--search-bg);
  color: var(--subtext);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-family);
  transition: color .15s, border-color .15s;
}
.queue-more-btn:hover { color: var(--accent); border-color: rgb(from var(--accent) r g b / 0.4); }

/* ── 대기열 맨 끝의 "+" 추가 타일 — "+N 더보기"와 같은 톤(점선 박스)으로 일관되게 ── */
.queue-add-btn {
  width: 116px;
  height: calc(116px * 9 / 16);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 0.5px dashed var(--border);
  background: var(--search-bg);
  color: var(--subtext);
  cursor: pointer;
  transition: color .15s, border-color .15s, background .15s;
}
.queue-add-btn:hover {
  color: var(--accent);
  border-color: rgb(from var(--accent) r g b / 0.4);
  background: rgb(from var(--accent) r g b / 0.06);
}

.queue-more-panel {
  position: absolute;
  top: 0;
  left: calc(100% + 10px);
  z-index: 50;
  width: 220px;
  max-height: 260px;
  overflow-y: auto;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.queue-more-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 6px;
  border-radius: 6px;
}
.queue-more-item:hover { background: var(--card-hover); }
.queue-more-thumb {
  width: 40px;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}
.queue-more-url {
  flex: 1;
  min-width: 0;
  font-size: 11px;
  color: var(--subtext);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.queue-more-cancel {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  color: var(--negative);
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: var(--font-family);
}
.queue-more-cancel:hover { opacity: 0.75; }

.dropdown-enter-active, .dropdown-leave-active {
  transition: opacity .18s ease, transform .18s ease;
}
.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}
</style>
