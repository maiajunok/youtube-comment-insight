<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])

const openaiInput  = ref(settings.openaiKey)
const youtubeInput = ref(settings.youtubeKey)

type Flash = 'saved' | 'deleted' | null
const flash = reactive<{ openai: Flash; youtube: Flash }>({ openai: null, youtube: null })

function flashField(field: 'openai' | 'youtube', kind: Flash) {
  flash[field] = kind
  setTimeout(() => { if (flash[field] === kind) flash[field] = null }, 2000)
}

function saveOpenai() {
  settings.openaiKey = openaiInput.value.trim()
  flashField('openai', 'saved')
}
function deleteOpenai() {
  openaiInput.value = ''
  settings.openaiKey = ''
  flashField('openai', 'deleted')
}

function saveYoutube() {
  settings.youtubeKey = youtubeInput.value.trim()
  flashField('youtube', 'saved')
}
function deleteYoutube() {
  youtubeInput.value = ''
  settings.youtubeKey = ''
  flashField('youtube', 'deleted')
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <p class="eyebrow">API Keys</p>
      <h1 class="settings-title">{{ M.settingsTitle }}</h1>
      <p class="settings-sub">{{ M.settingsSub }}</p>
    </div>

    <div class="notice-card">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:2px">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      <p>{{ M.byokNotice }}</p>
    </div>

    <div class="key-form">
      <!-- OpenAI -->
      <div class="field">
        <div class="field-top">
          <label class="field-label">{{ M.openaiKeyLabel }}</label>
          <span class="field-status" :class="{ on: !!settings.openaiKey }">
            <span class="status-dot" />
            {{ settings.openaiKey ? M.currentlySaved : M.notSaved }}
          </span>
        </div>
        <div class="field-row">
          <input
            v-model="openaiInput"
            type="password"
            autocomplete="off"
            spellcheck="false"
            :placeholder="M.keyPlaceholder"
            class="key-input"
          />
          <button class="icon-btn save" :title="M.saveBtn" @click="saveOpenai">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </button>
          <button class="icon-btn delete" :title="M.clearBtn" :disabled="!settings.openaiKey && !openaiInput" @click="deleteOpenai">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
        <div class="field-bottom">
          <span class="field-hint">{{ M.openaiKeyHint }}</span>
          <transition name="fade">
            <span v-if="flash.openai" class="inline-flash" :class="flash.openai">
              {{ flash.openai === 'saved' ? M.fieldSaved : M.fieldDeleted }}
            </span>
          </transition>
        </div>
      </div>

      <!-- YouTube -->
      <div class="field">
        <div class="field-top">
          <label class="field-label">{{ M.youtubeKeyLabel }}</label>
          <span class="field-status" :class="{ on: !!settings.youtubeKey }">
            <span class="status-dot" />
            {{ settings.youtubeKey ? M.currentlySaved : M.notSaved }}
          </span>
        </div>
        <div class="field-row">
          <input
            v-model="youtubeInput"
            type="password"
            autocomplete="off"
            spellcheck="false"
            :placeholder="M.keyPlaceholder"
            class="key-input"
          />
          <button class="icon-btn save" :title="M.saveBtn" @click="saveYoutube">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </button>
          <button class="icon-btn delete" :title="M.clearBtn" :disabled="!settings.youtubeKey && !youtubeInput" @click="deleteYoutube">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
        <div class="field-bottom">
          <span class="field-hint">{{ M.youtubeKeyHint }}</span>
          <transition name="fade">
            <span v-if="flash.youtube" class="inline-flash" :class="flash.youtube">
              {{ flash.youtube === 'saved' ? M.fieldSaved : M.fieldDeleted }}
            </span>
          </transition>
        </div>
      </div>

      <p class="stored-note">{{ M.keyStoredLocally }}</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/assets/variables' as *;

.settings-page {
  position: relative;
  z-index: 2;
  flex: 1;
  overflow-y: auto;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  gap: $space-xl - 4px;
}

.settings-header {
  display: flex;
  flex-direction: column;
  gap: $space-sm;
}

.eyebrow {
  font-size: 10px;
  letter-spacing: .14em;
  color: var(--accent);
  text-transform: uppercase;
  font-weight: 600;
  opacity: 0.7;
  display: flex;
  align-items: center;
  gap: $space-sm;

  &::before {
    content: '';
    width: 20px;
    height: 1px;
    background: var(--accent);
  }
}

.settings-title { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.settings-sub   { font-size: 14px; color: var(--subtext); line-height: 1.6; }

.notice-card {
  display: flex;
  gap: $space-md;
  align-items: flex-start;
  background: rgba(123, 94, 248, 0.07);
  border: 0.5px solid rgba(123, 94, 248, 0.2);
  border-radius: var(--radius);
  padding: 16px 18px;
  color: var(--accent);

  p { font-size: 12.5px; line-height: 1.65; color: var(--subtext); }
}

.key-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: $space-lg 28px;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-sm;
}
.field-label { font-size: 12px; font-weight: 600; color: var(--text); }

.field-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  color: var(--dim);

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--dim);
  }

  &.on {
    color: var(--positive);
    .status-dot { background: var(--positive); }
  }
}

.field-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.key-input {
  flex: 1;
  background: var(--card-hover);
  border: 0.5px solid var(--border);
  border-radius: $radius-sm;
  padding: 10px $space-md;
  font-size: 13px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  outline: none;

  &:focus { border-color: rgba(123, 94, 248, 0.5); }
  &::placeholder { color: var(--dim); }
}

.icon-btn {
  @include icon-button;
  width: 34px;
  height: 34px;
  flex-shrink: 0;

  &.save {
    color: var(--positive);
    &:hover:not(:disabled) { background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.4); }
  }
  &.delete {
    color: var(--negative);
    &:hover:not(:disabled) { background: rgba(244, 63, 94, 0.12); border-color: rgba(244, 63, 94, 0.4); }
  }
}

.field-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-sm;
  min-height: 14px;
}
.field-hint { font-size: 11px; color: var(--dim); }

.inline-flash {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  @include fade-transition;

  &.saved   { color: var(--positive); }
  &.deleted { color: var(--negative); }
}

.stored-note { grid-column: 1 / -1; font-size: 11px; color: var(--dim); }
</style>
