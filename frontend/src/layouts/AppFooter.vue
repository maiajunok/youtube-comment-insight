<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])
</script>

<template>
  <footer class="app-footer">
    <div class="footer-main">
      <div class="footer-brand">
        <span class="footer-logo">FindComments</span>
        <span class="footer-tagline">Community Reaction Analysis</span>
      </div>
      <p class="footer-desc">{{ M.footerDescription }}</p>
    </div>

    <div class="footer-side">
      <p class="footer-disclaimer">{{ M.footerDisclaimer }}</p>
      <div class="footer-bottom">
        <span class="footer-copyright">© 2026 FindComments</span>
        <a
          href="https://github.com/maiajunok/youtube-comment-insight"
          target="_blank"
          rel="noopener"
          class="footer-gh"
          title="GitHub"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.57.1.78-.25.78-.55v-1.94c-3.2.7-3.88-1.54-3.88-1.54-.52-1.33-1.28-1.68-1.28-1.68-1.04-.72.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.75 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.11 3.04.74.81 1.18 1.83 1.18 3.09 0 4.41-2.69 5.38-5.25 5.67.41.36.78 1.05.78 2.12v3.14c0 .3.2.66.79.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/>
          </svg>
          github.com/maiajunok
        </a>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 40px;
  margin-top: 40px;
  padding-top: 24px;
  padding-right: 4px;
  border-top: 0.5px solid var(--border);
  width: 100%;
}

.footer-main { flex: 1; min-width: 0; }

.footer-brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}
.footer-logo { font-size: 14px; font-weight: 700; color: var(--text); }
.footer-tagline { font-size: 11px; color: var(--dim); }

.footer-desc {
  font-size: 12px;
  color: var(--subtext);
  line-height: 1.6;
  max-width: 420px;
}

.footer-side {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  text-align: right;
}

.footer-disclaimer {
  font-size: 11px;
  color: var(--dim);
  line-height: 1.6;
  max-width: 340px;
}

.footer-bottom {
  display: flex;
  align-items: center;
  gap: 14px;
}
.footer-copyright { font-size: 11px; color: var(--dim); white-space: nowrap; }

.footer-gh {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--subtext);
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.15s;
}
.footer-gh:hover { color: var(--accent); }
</style>
