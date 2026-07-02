<template>
  <div class="howto">

    <div class="howto-header">
      <p class="eyebrow">{{ M.howtoEyebrow }}</p>
      <h1 class="howto-title">{{ M.howtoTitle }}</h1>
      <p class="howto-sub">{{ M.howtoSub }}</p>
    </div>

    <!-- 플로우 -->
    <div class="flow">
      <div v-for="(step, i) in steps" :key="i" class="flow-row">
        <div class="flow-step">
          <div class="step-num">{{ i + 1 }}</div>
          <div class="step-body">
            <div class="step-header">
              <span class="step-tag" :style="`background:${step.color}18;color:${step.color};border-color:${step.color}33`">
                {{ step.tag }}
              </span>
              <h3 class="step-title">{{ step.title }}</h3>
            </div>
            <p class="step-desc">{{ step.desc }}</p>
            <div v-if="step.details" class="step-details">
              <span v-for="d in step.details" :key="d" class="detail-chip">{{ d }}</span>
            </div>
            <div v-if="step.future" class="future-note">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ step.future }}
            </div>
          </div>
        </div>
        <div v-if="i < steps.length - 1" class="flow-arrow">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- 기술 스택 -->
    <div>
      <p class="section-label">{{ M.techStackLabel }}</p>
      <div class="tech-grid">
        <div v-for="t in techStack" :key="t.name" class="tech-card">
          <span class="tech-role">{{ t.role }}</span>
          <span class="tech-name">{{ t.name }}</span>
        </div>
      </div>
    </div>

    <!-- 유의사항 -->
    <div>
      <p class="section-label">{{ M.notesLabel }}</p>
      <div class="notes-grid">
        <div v-for="n in notes" :key="n.title" class="note-card">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#c850ff" stroke-width="2" style="flex-shrink:0;margin-top:2px">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div>
            <p class="note-title">{{ n.title }}</p>
            <p class="note-desc">{{ n.desc }}</p>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/features/settings/stores/settings'
import { messages } from '@/locales/messages'
import { howtoContent } from '@/locales/howtoContent'

const settings = useSettingsStore()
const M = computed(() => messages[settings.lang])
const C = computed(() => howtoContent[settings.lang])

const steps      = computed(() => C.value.steps)
const techStack   = computed(() => C.value.techStack)
const notes       = computed(() => C.value.notes)
</script>

<style scoped>
.howto {
  position: relative;
  z-index: 2;
  flex: 1;
  overflow-y: auto;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

.howto-header { display: flex; flex-direction: column; gap: 8px; }

.eyebrow {
  font-size: 10px; letter-spacing: .14em; color: var(--accent);
  text-transform: uppercase; font-weight: 600; opacity: 0.7;
  display: flex; align-items: center; gap: 8px;
}
.eyebrow::before { content: ''; width: 20px; height: 1px; background: var(--accent); }

.howto-title { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.howto-sub   { font-size: 14px; color: var(--subtext); line-height: 1.6; }

.flow { display: flex; flex-direction: column; }

.flow-step {
  display: flex; gap: 20px;
  background: var(--card-hover);
  border: 0.5px solid var(--border);
  border-radius: var(--radius); padding: 20px 24px;
}

.step-num {
  width: 32px; height: 32px; border-radius: 50%;
  background: rgb(from var(--accent) r g b / 0.12); border: 0.5px solid rgb(from var(--accent) r g b / 0.3);
  color: var(--accent); font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}

.step-body { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.step-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.step-tag {
  font-size: 10px; font-weight: 600;
  padding: 3px 9px; border-radius: 6px; border: 0.5px solid; white-space: nowrap;
}
.step-title { font-size: 15px; font-weight: 600; color: var(--text); }
.step-desc  { font-size: 13px; color: var(--subtext); line-height: 1.65; }

.step-details { display: flex; gap: 6px; flex-wrap: wrap; }
.detail-chip {
  font-size: 11px; color: var(--dim);
  background: var(--card-hover);
  border: 0.5px solid var(--border);
  padding: 3px 10px; border-radius: 20px;
}

.future-note {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 12px; color: var(--accent); line-height: 1.6; opacity: 0.8;
  background: rgb(from var(--accent) r g b / 0.07);
  border: 0.5px solid rgb(from var(--accent) r g b / 0.2);
  border-radius: 8px; padding: 10px 14px;
}

.flow-arrow {
  display: flex; justify-content: center; padding: 5px 0; color: var(--dim);
  opacity: 0.5;
}

.section-label {
  font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--dim); font-weight: 600; margin-bottom: 14px;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--gap);
}
.tech-card {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius); padding: 16px 18px;
  display: flex; flex-direction: column; gap: 5px;
}
.tech-role { font-size: 10px; color: var(--dim); text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }
.tech-name { font-size: 14px; font-weight: 600; color: var(--text); }

.notes-grid { display: flex; flex-direction: column; gap: var(--gap); }
.note-card {
  display: flex; gap: 14px; align-items: flex-start;
  background: rgb(from var(--accent) r g b / 0.05);
  border: 0.5px solid rgb(from var(--accent) r g b / 0.15);
  border-radius: var(--radius); padding: 16px 20px;
}
.note-title { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.note-desc  { font-size: 13px; color: var(--subtext); line-height: 1.65; }

@media (max-width: 768px) {
  .howto { padding: 24px 18px; gap: 32px; }
  .flow-step { padding: 16px 16px; gap: 14px; }
}
</style>
