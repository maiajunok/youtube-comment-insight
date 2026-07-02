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
      <span class="footer-copyright">© 2026 FindComments</span>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-top: auto;
  padding-top: 14px;
  padding-right: 4px;
  border-top: 0.5px solid var(--border);
  width: 100%;
}

.footer-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.footer-brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.footer-logo { font-size: 11px; font-weight: 700; color: var(--text); }
.footer-tagline { font-size: 10px; color: var(--dim); }

.footer-desc {
  font-size: 10px;
  color: var(--subtext);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer-side {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.footer-disclaimer {
  font-size: 10px;
  color: var(--dim);
  white-space: nowrap;
}

.footer-copyright { font-size: 10px; color: var(--dim); white-space: nowrap; }

@media (max-width: 768px) {
  .app-footer {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 4px;
    padding-top: 16px;
  }
  /* 브랜드명/설명은 상단 바에 이미 나오므로 모바일 히어로 하단에서는 생략 */
  .footer-main { display: none; }
  .footer-side { align-items: center; }
  .footer-disclaimer { white-space: normal; }
}
</style>
