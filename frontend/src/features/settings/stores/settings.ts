import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Lang } from '@/features/insight/types/insight'

type Theme = 'dark' | 'light'

// html lang은 BCP-47 표준 태그를 써야 함 — 특히 중국어는 이 프로젝트가 쓰는 표기(zh)가
// 간체(Simplified)라서 'zh-CN'으로 명시해야 브라우저가 번체용 폰트를 섞어 고르지 않음
const HTML_LANG: Record<Lang, string> = { ko: 'ko', en: 'en', zh: 'zh-CN', ja: 'ja' }

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

  // data-locale은 CSS(assets/style.css의 언어별 --font-family)가 참조하고,
  // lang은 브라우저가 CJK 글리프의 기본 폴백 폰트를 고를 때 참조함 — 이 둘을 안 맞춰주면
  // 같은 한자라도 문서 언어를 뭘로 보느냐에 따라 다른 시스템 폰트로 렌더링될 수 있음
  function applyLocale(l: Lang) {
    document.documentElement.lang = HTML_LANG[l]
    document.documentElement.setAttribute('data-locale', l)
  }
  applyLocale(lang.value)

  watch(lang, (l) => {
    applyLocale(l)
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
