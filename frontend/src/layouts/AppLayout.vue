<template>
  <div class="shell">
    <!-- 사이드바 -->
    <aside class="sidebar" ref="sidebarRef" :class="{ 'mobile-open': mobileNavOpen }">
      <div class="logo">
        <span class="logo-text">FindComments</span>
      </div>

      <nav>
        <div
          class="nav-item"
          :class="{ active: route.name === 'home' }"
          @click="goHome(); closeMobileNav()"
        >
          <IconHome class="nav-icon" />
          {{ messages[settings.lang].navHome }}
          <span v-if="analysisStore.isAnalyzing" class="analyzing-dot" />
        </div>
      </nav>

      <div class="nav-divider" />
      <div class="nav-section">{{ settings.lang === 'ko' ? '분석' : 'Analysis' }}</div>
      <nav>
        <div
          v-for="item in analysisNav"
          :key="item.name"
          class="nav-item"
          :class="{ active: route.name === item.name || (item.name === 'history' && route.name === 'history-view') }"
          @click="router.push({ name: item.name }); closeMobileNav()"
        >
          <component :is="item.icon" class="nav-icon" />
          {{ messages[settings.lang][item.msgKey as keyof typeof messages['ko']] }}
          <!-- 분석 완료 인디케이터 (분석 기록) -->
          <span v-if="item.name === 'history' && analysisStore.justFinished" class="done-dot" />
        </div>
      </nav>

      <div class="nav-divider" />
      <div class="nav-section">{{ settings.lang === 'ko' ? '정보' : 'Info' }}</div>
      <div
        class="nav-item"
        :class="{ active: route.name === 'howto' }"
        @click="router.push({ name: 'howto' }); closeMobileNav()"
      >
        <IconFileDescription class="nav-icon" />
        {{ messages[settings.lang].navHowto }}
      </div>
      <div
        class="nav-item"
        :class="{ active: route.name === 'stats' }"
        @click="router.push({ name: 'stats' }); closeMobileNav()"
      >
        <IconActivity class="nav-icon" />
        {{ messages[settings.lang].navStats }}
      </div>

      <div class="nav-bottom">
        <a
          href="https://github.com/maiajunok/youtube-comment-insight"
          target="_blank"
          rel="noopener"
          class="nav-item github-link"
          @click="closeMobileNav()"
        >
          <IconBrandGithub class="nav-icon" />
          maiajunok
        </a>
        <div
          class="nav-item"
          :class="{ active: route.name === 'settings' }"
          @click="router.push({ name: 'settings' }); closeMobileNav()"
        >
          <IconSettings class="nav-icon" />
          {{ messages[settings.lang].navSettings }}
        </div>
      </div>
    </aside>

    <!-- 모바일 메뉴 배경 오버레이 -->
    <div v-if="mobileNavOpen" class="mobile-nav-backdrop" @click="closeMobileNav" />

    <!-- 메인 영역 -->
    <main class="main">
      <template v-if="route.name === 'home'">
        <div class="orb orb-1" />
        <div class="orb orb-2" />
        <div class="orb orb-3" />
      </template>

      <!-- 상단 바 -->
      <header class="topbar">
        <button class="hamburger-btn" ref="hamburgerRef" @click="toggleMobileNav" :aria-expanded="mobileNavOpen">
          <svg v-if="!mobileNavOpen" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
        <span class="tb-title">{{ topbarTitle }}</span>
        <div class="tb-right">
          <div class="lang-dropdown" ref="langDropdownRef">
            <button class="lang-trigger" ref="langTriggerRef" @click="toggleLang">
              {{ LANG_OPTIONS.find(o => o.value === settings.lang)?.label }}
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                :style="{ transform: langOpen ? 'rotate(180deg)' : 'none', transition: 'transform .18s' }">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            <teleport to="body">
              <div v-if="langOpen" class="lang-menu" ref="langMenuRef"
                :style="{ top: menuPos.top + 'px', left: menuPos.left + 'px' }">
                <button
                  v-for="opt in LANG_OPTIONS"
                  :key="opt.value"
                  class="lang-option"
                  :class="{ active: settings.lang === opt.value }"
                  @click="settings.lang = opt.value as any; langOpen = false"
                >
                  <span class="lang-dot" v-if="settings.lang === opt.value" />
                  {{ opt.label }}
                </button>
              </div>
            </teleport>
          </div>
          <button class="tb-btn theme-btn" @click="settings.toggleTheme" :title="settings.theme === 'dark' ? '라이트 모드' : '다크 모드'">
            <svg v-if="settings.theme === 'dark'" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="4"/>
              <line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/>
              <line x1="4.93" y1="4.93" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.07" y2="19.07"/>
              <line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/>
              <line x1="4.93" y1="19.07" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.07" y2="4.93"/>
            </svg>
            <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
        </div>
      </header>

      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  IconHome, IconClock, IconLayoutColumns, IconChartDots3,
  IconSettings, IconFileDescription, IconActivity, IconBrandGithub,
} from '@tabler/icons-vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { useAnalysisStore } from '@/features/insight/stores/analysis'
import { messages } from '@/locales/messages'

const router       = useRouter()
const route        = useRoute()
const settings     = useSettingsStore()
const analysisStore = useAnalysisStore()

function goHome() {
  // 표시 중인 결과(result)와 백그라운드 분석 진행 상태(isAnalyzing)는 서로 무관함 —
  // 다른 영상이 분석 중이어도 지금 보고 있는 결과 화면은 항상 지워져야 홈으로 돌아감
  analysisStore.clearResult()
  router.push({ name: 'home' })
}

const mobileNavOpen = ref(false)
const sidebarRef = ref<HTMLElement | null>(null)
const hamburgerRef = ref<HTMLElement | null>(null)

// 드로어가 열려 있는 동안 그 뒤의 페이지(반응 지도 등)가 같이 스크롤되면 드로어 위에서
// 스크롤하려 했는데 배경이 움직이는 것처럼 느껴짐 — 열려 있을 때만 body 스크롤을 잠그고,
// 드로어 내부(overflow-y: auto)는 그대로 자체 스크롤되게 둠
watch(mobileNavOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})
onBeforeUnmount(() => { document.body.style.overflow = '' })

function toggleMobileNav() { mobileNavOpen.value = !mobileNavOpen.value }
function closeMobileNav() { mobileNavOpen.value = false }

function onClickOutsideMobileNav(e: MouseEvent) {
  const t = e.target as Node
  const insideSidebar = sidebarRef.value?.contains(t)
  const insideHamburger = hamburgerRef.value?.contains(t)
  if (!insideSidebar && !insideHamburger) closeMobileNav()
}
onMounted(() => document.addEventListener('mousedown', onClickOutsideMobileNav))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutsideMobileNav))

const langOpen = ref(false)
const langDropdownRef = ref<HTMLElement | null>(null)
const langTriggerRef = ref<HTMLElement | null>(null)
const langMenuRef = ref<HTMLElement | null>(null)
const menuPos = ref({ top: 0, left: 0 })

const LANG_OPTIONS = [
  { value: 'ko', label: '한국어' },
  { value: 'en', label: 'English' },
  { value: 'zh', label: '中文' },
  { value: 'ja', label: '日本語' },
]

function toggleLang() {
  if (!langOpen.value && langTriggerRef.value) {
    const rect = langTriggerRef.value.getBoundingClientRect()
    menuPos.value = {
      top: rect.bottom + 6,
      left: rect.right - 110,
    }
  }
  langOpen.value = !langOpen.value
}

function onClickOutsideLang(e: MouseEvent) {
  const t = e.target as Node
  const insideTrigger = langDropdownRef.value?.contains(t)
  const insideMenu = langMenuRef.value?.contains(t)
  if (!insideTrigger && !insideMenu) {
    langOpen.value = false
  }
}
onMounted(() => document.addEventListener('mousedown', onClickOutsideLang))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutsideLang))


// 분석 기록 화면을 실제로 보면 "완료" 표시를 지움 (타이머가 아니라 확인 시점 기준)
watch(() => route.name, (name) => {
  if (name === 'history' || name === 'history-view') analysisStore.justFinished = false
})

const analysisNav = [
  { name: 'history', msgKey: 'navHistory', icon: IconClock },
  { name: 'compare', msgKey: 'navCompare', icon: IconLayoutColumns },
  { name: 'network', msgKey: 'navNetwork', icon: IconChartDots3 },
]

const topbarTitle = computed(() => {
  const m = messages[settings.lang]
  const map: Record<string, string> = {
    home:           'Community Reaction Dashboard',
    history:        m.navHistory,
    stats:          m.navStats,
    'history-view': 'Community Reaction Dashboard',
    compare:        m.navCompare,
    network:        m.navNetwork,
    howto:          m.navHowto,
    settings:       m.navSettings,
  }
  return map[route.name as string] ?? ''
})
</script>
