<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])

const openaiInput  = ref(settings.openaiKey)
const youtubeInput = ref(settings.youtubeKey)
const savedFlash    = ref(false)

function save() {
  settings.openaiKey  = openaiInput.value.trim()
  settings.youtubeKey = youtubeInput.value.trim()
  savedFlash.value = true
  setTimeout(() => { savedFlash.value = false }, 2000)
}

function clearKeys() {
  openaiInput.value  = ''
  youtubeInput.value = ''
  settings.openaiKey  = ''
  settings.youtubeKey = ''
}

function mask(key: string) {
  if (key.length <= 8) return key
  return `${key.slice(0, 4)}${'•'.repeat(Math.min(key.length - 8, 20))}${key.slice(-4)}`
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
      <div class="field">
        <label class="field-label">{{ M.openaiKeyLabel }}</label>
        <input
          v-model="openaiInput"
          type="password"
          autocomplete="off"
          spellcheck="false"
          :placeholder="M.keyPlaceholder"
          class="key-input"
        />
        <span class="field-hint">{{ M.openaiKeyHint }}</span>
      </div>

      <div class="field">
        <label class="field-label">{{ M.youtubeKeyLabel }}</label>
        <input
          v-model="youtubeInput"
          type="password"
          autocomplete="off"
          spellcheck="false"
          :placeholder="M.keyPlaceholder"
          class="key-input"
        />
        <span class="field-hint">{{ M.youtubeKeyHint }}</span>
      </div>

      <div class="key-actions">
        <button class="save-btn" @click="save">{{ M.saveBtn }}</button>
        <button class="clear-btn" @click="clearKeys">{{ M.clearBtn }}</button>
        <span v-if="savedFlash" class="saved-toast">{{ M.savedToast }}</span>
      </div>

      <p class="stored-note">{{ M.keyStoredLocally }}</p>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  position: relative;
  z-index: 2;
  flex: 1;
  overflow-y: auto;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 560px;
}

.settings-header { display: flex; flex-direction: column; gap: 8px; }

.eyebrow {
  font-size: 10px; letter-spacing: .14em; color: var(--accent);
  text-transform: uppercase; font-weight: 600; opacity: 0.7;
  display: flex; align-items: center; gap: 8px;
}
.eyebrow::before { content: ''; width: 20px; height: 1px; background: var(--accent); }

.settings-title { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.settings-sub   { font-size: 14px; color: var(--subtext); line-height: 1.6; }

.notice-card {
  display: flex; gap: 12px; align-items: flex-start;
  background: rgba(123,94,248,0.07);
  border: 0.5px solid rgba(123,94,248,0.2);
  border-radius: var(--radius); padding: 16px 18px;
  color: var(--accent);
}
.notice-card p { font-size: 12.5px; line-height: 1.65; color: var(--subtext); }

.key-form {
  display: flex; flex-direction: column; gap: 20px;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}

.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 12px; font-weight: 600; color: var(--text); }
.key-input {
  background: var(--card-hover);
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  outline: none;
}
.key-input:focus { border-color: rgba(123,94,248,0.5); }
.key-input::placeholder { color: var(--dim); }
.field-hint { font-size: 11px; color: var(--dim); }

.key-actions { display: flex; align-items: center; gap: 10px; }
.save-btn {
  background: var(--accent);
  color: #fff;
  font-size: 13px; font-weight: 600;
  border: none; padding: 9px 20px; border-radius: 8px;
  cursor: pointer; font-family: 'Inter', sans-serif;
}
.clear-btn {
  background: transparent;
  color: var(--subtext);
  font-size: 13px;
  border: 0.5px solid var(--border); padding: 9px 16px; border-radius: 8px;
  cursor: pointer; font-family: 'Inter', sans-serif;
}
.saved-toast { font-size: 12px; color: var(--positive); font-weight: 600; }

.stored-note { font-size: 11px; color: var(--dim); }
</style>
