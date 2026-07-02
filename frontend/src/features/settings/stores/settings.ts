import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Lang } from '@/features/insight/types/insight'

type Theme = 'dark' | 'light'

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<Theme>((localStorage.getItem('theme') as Theme) || 'dark')
  const lang  = ref<Lang>((localStorage.getItem('lang') as Lang) || 'ko')

  const openaiKey  = ref(localStorage.getItem('openai_key')  || '')
  const youtubeKey = ref(localStorage.getItem('youtube_key') || '')

  function applyTheme(t: Theme) {
    document.documentElement.setAttribute('data-theme', t)
  }
  applyTheme(theme.value)

  watch(theme, (t) => {
    applyTheme(t)
    localStorage.setItem('theme', t)
  })

  watch(lang, (l) => {
    localStorage.setItem('lang', l)
  })

  watch(openaiKey, (k) => {
    if (k) localStorage.setItem('openai_key', k)
    else localStorage.removeItem('openai_key')
  })

  watch(youtubeKey, (k) => {
    if (k) localStorage.setItem('youtube_key', k)
    else localStorage.removeItem('youtube_key')
  })

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return { theme, lang, openaiKey, youtubeKey, toggleTheme }
})
